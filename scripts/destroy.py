import logging
from pathlib import Path

from utils.constants import (
	AWS_ACCESS_KEY,
	AWS_DEFAULT_REGION,
	AWS_SECRET_KEY,
	PDW_S3_BUCKET_SANDBOX_PROJECT_PARTIALS,
)
from utils.logging_config import SUCCESS_LEVEL, configure_logging
from utils.services import S3Manager
from utils.services.cft import CloudFormationClient, CloudFormationStack

logger = logging.getLogger(__name__)


class Destroy:
	"""Delete CloudFormation stacks and the infrastructure artifact bucket."""

	def __init__(
		self,
		project_root: Path | None = None,
		stack_names=None,
		bucket_name=PDW_S3_BUCKET_SANDBOX_PROJECT_PARTIALS,
		cloudformation_client=None,
		s3_manager=None,
	):
		self.stacks_directory = (
			(project_root or Path(__file__).resolve().parents[1]) / "infra" / "stacks"
		)
		self.stack_names = stack_names
		self.bucket_name = bucket_name
		self.cloudformation_client = (
			cloudformation_client
			or CloudFormationClient(
				AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_DEFAULT_REGION
			).get_cf_client()
		)
		self.s3_manager = s3_manager or S3Manager(
			AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_DEFAULT_REGION
		)

	def __get_stacks(self):
		"""Return stack objects in reverse deployment order."""
		if self.stack_names is None:
			stack_names = [
				f"pdw-stack-{stack_file.stem}"
				for stack_file in sorted(
					(path for path in self.stacks_directory.glob("*.yml") if path.is_file()),
					reverse=True,
				)
			]
		else:
			stack_names = list(self.stack_names)
		return [
			CloudFormationStack(stack_name, "", [], self.cloudformation_client)
			for stack_name in stack_names
		]

	def destroy(self):
		"""Delete stacks first, then empty and delete the artifact bucket."""
		logger.info("Starting infrastructure destruction")
		for stack in self.__get_stacks():
			stack.delete()

		if not self.s3_manager.empty_bucket(self.bucket_name):
			raise RuntimeError(f"Unable to empty S3 bucket: {self.bucket_name}")
		if not self.s3_manager.delete_bucket(self.bucket_name):
			raise RuntimeError(f"Unable to delete S3 bucket: {self.bucket_name}")
		logger.log(SUCCESS_LEVEL, "Infrastructure destruction completed")


def main():
	configure_logging()
	Destroy().destroy()


if __name__ == "__main__":
	main()
