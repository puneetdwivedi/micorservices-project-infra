import logging

from utils.constants import (
	AWS_ACCESS_KEY,
	AWS_DEFAULT_REGION,
	AWS_SECRET_KEY,
	PDW_S3_BUCKET_SANDBOX_PROJECT_PARTIALS,
	PDW_STACK_SANDBOX_CORE_INFRA,
)
from utils.logging_config import SUCCESS_LEVEL
from utils.services import S3Manager
from utils.services.cft import CloudFormationClient, CloudFormationStack

logger = logging.getLogger(__name__)


class Destroy:
	"""Delete CloudFormation stacks and the infrastructure artifact bucket."""

	def __init__(
		self,
		stack_names=(PDW_STACK_SANDBOX_CORE_INFRA,),
		bucket_name=PDW_S3_BUCKET_SANDBOX_PROJECT_PARTIALS,
		cloudformation_client=None,
		s3_manager=None,
	):
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

	def destroy(self):
		"""Delete stacks first, then empty and delete the artifact bucket."""
		logger.info("Starting infrastructure destruction")
		for stack_name in self.stack_names:
			CloudFormationStack(stack_name, "", [], self.cloudformation_client).delete()

		if not self.s3_manager.empty_bucket(self.bucket_name):
			raise RuntimeError(f"Unable to empty S3 bucket: {self.bucket_name}")
		if not self.s3_manager.delete_bucket(self.bucket_name):
			raise RuntimeError(f"Unable to delete S3 bucket: {self.bucket_name}")
		logger.log(SUCCESS_LEVEL, "Infrastructure destruction completed")


def main():
	Destroy().destroy()


if __name__ == "__main__":
	main()
