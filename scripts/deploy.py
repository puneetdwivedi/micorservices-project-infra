import json
import logging
from pathlib import Path

from utils.constants import (
	AWS_ACCESS_KEY,
	AWS_DEFAULT_REGION,
	AWS_SECRET_KEY,
	PDW_S3_BUCKET_SANDBOX_PROJECT_PARTIALS,
	PROJECT_NAME_PREFIX,
)
from utils.logging_config import SUCCESS_LEVEL
from utils.services.cft import CloudFormationClient, CloudFormationStack

logger = logging.getLogger(__name__)


class Deploy:
	"""Deploy CloudFormation stack templates from the stacks directory in order."""

	def __init__(
		self,
		project_root: Path | None = None,
		bucket_name: str = PDW_S3_BUCKET_SANDBOX_PROJECT_PARTIALS,
		project_name_prefix: str = PROJECT_NAME_PREFIX,
		cloudformation_client=None,
		waiter_delay: int = 30,
	):
		self.project_root = project_root or Path(__file__).resolve().parents[1]
		self.stacks_directory = self.project_root / "infra" / "stacks"
		self.configuration_file = (
			self.stacks_directory / "configuration" / "parsed" / "configuration.json"
		)
		self.bucket_name = bucket_name
		self.project_name_prefix = project_name_prefix.strip("/")
		self.waiter_delay = waiter_delay
		self.cloudformation_client = (
			cloudformation_client
			or CloudFormationClient(
				AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_DEFAULT_REGION
			).get_cf_client()
		)

	def __get_stacks(self):
		"""Build stack objects in deterministic filename order."""
		with self.configuration_file.open(encoding="utf-8") as configuration_file:
			configuration = json.load(configuration_file)
		stack_files = sorted(path for path in self.stacks_directory.glob("*.yml") if path.is_file())
		stacks = []
		for stack_file in stack_files:
			stack_name = self._stack_name(stack_file)
			stacks.append(
				CloudFormationStack(
					stack_name,
					self._template_url(stack_file),
					self._parameters(configuration.get(stack_name, {})),
					self.cloudformation_client,
				)
			)
		return stacks

	def deploy(self):
		"""Deploy every discovered stack and wait before deploying the next one."""
		stacks = self.__get_stacks()
		logger.info("Deploying %d CloudFormation stacks", len(stacks))
		for stack in stacks:
			stack.deploy(waiter_delay=self.waiter_delay)
		logger.log(SUCCESS_LEVEL, "Deployed %d CloudFormation stacks", len(stacks))

	def _stack_name(self, stack_file):
		return f"pdw-stack-{stack_file.stem}"

	def _template_url(self, stack_file):
		object_key = f"{self.project_name_prefix}/stacks/{stack_file.name}"
		return f"https://{self.bucket_name}.s3.{AWS_DEFAULT_REGION}.amazonaws.com/{object_key}"

	def _parameters(self, parameter_values):
		return [
			{
				"ParameterKey": parameter_key,
				"ParameterValue": parameter_value,
			}
			for parameter_key, parameter_value in parameter_values.items()
		]
