from scripts import Destroy


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
