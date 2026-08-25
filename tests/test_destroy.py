from botocore.exceptions import ClientError

from scripts import Destroy
from utils.services.cft import CloudFormationStack


def test_destroy_discovers_stacks_in_reverse_order(tmp_path):
	stacks_directory = tmp_path / "infra" / "stacks"
	stacks_directory.mkdir(parents=True)
	(stacks_directory / "01-network.yml").write_text("network")
	(stacks_directory / "02-services.yml").write_text("services")

	events = []
	Destroy(
		project_root=tmp_path,
		cloudformation_client=FakeCloudFormationClient(events),
		s3_manager=FakeS3Manager(events),
	).destroy()

	assert events[:4] == [
		("delete_stack", "pdw-stack-02-services"),
		("wait", "pdw-stack-02-services"),
		("delete_stack", "pdw-stack-01-network"),
		("wait", "pdw-stack-01-network"),
	]


class FakeWaiter:
	def __init__(self, events):
		self.events = events

	def wait(self, **kwargs):
		self.events.append(("wait", kwargs["StackName"]))


class FakeCloudFormationClient:
	def __init__(self, events):
		self.events = events

	def delete_stack(self, **kwargs):
		self.events.append(("delete_stack", kwargs["StackName"]))

	def get_waiter(self, waiter_name):
		assert waiter_name == "stack_delete_complete"
		return FakeWaiter(self.events)


class FakeS3Manager:
	def __init__(self, events):
		self.events = events

	def empty_bucket(self, bucket_name):
		self.events.append(("empty_bucket", bucket_name))
		return True

	def delete_bucket(self, bucket_name):
		self.events.append(("delete_bucket", bucket_name))
		return True


def test_destroy_deletes_stacks_before_emptying_and_deleting_bucket():
	events = []

	Destroy(
		stack_names=("stack-one", "stack-two"),
		bucket_name="artifact-bucket",
		cloudformation_client=FakeCloudFormationClient(events),
		s3_manager=FakeS3Manager(events),
	).destroy()

	assert events == [
		("delete_stack", "stack-one"),
		("wait", "stack-one"),
		("delete_stack", "stack-two"),
		("wait", "stack-two"),
		("empty_bucket", "artifact-bucket"),
		("delete_bucket", "artifact-bucket"),
	]


def test_s3_manager_empty_and_delete_bucket(s3_manager):
	s3_manager.create_bucket("artifact-bucket")
	s3_manager.s3.put_object(Bucket="artifact-bucket", Key="artifact.txt", Body=b"artifact")

	assert s3_manager.empty_bucket("artifact-bucket")
	assert s3_manager.s3.list_objects_v2(Bucket="artifact-bucket").get("Contents") is None
	assert s3_manager.delete_bucket("artifact-bucket")


def test_s3_manager_skips_missing_bucket(s3_manager):
	assert s3_manager.empty_bucket("missing-bucket")
	assert s3_manager.delete_bucket("missing-bucket")


def test_stack_delete_skips_missing_stack():
	client = FailingCloudFormationClient("ValidationError", "Stack does not exist")

	CloudFormationStack("missing-stack", "", [], client).delete()


def test_stack_delete_raises_real_delete_failure():
	client = FailingCloudFormationClient("AccessDenied", "Delete failed")

	try:
		CloudFormationStack("failed-stack", "", [], client).delete()
	except ClientError as error:
		assert error.response["Error"]["Code"] == "AccessDenied"
	else:
		raise AssertionError("Expected stack deletion failure to be raised")


class FailingCloudFormationClient:
	def __init__(self, error_code, message):
		self.error = ClientError({"Error": {"Code": error_code, "Message": message}}, "DeleteStack")

	def delete_stack(self, **kwargs):
		raise self.error
