from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from scripts import Build


def test_build_syncs_prefixed_infrastructure_and_lambda_archive(s3_manager):
	with TemporaryDirectory() as temporary_directory:
		project_root = Path(temporary_directory)
		(project_root / "infra" / "stacks").mkdir(parents=True)
		(project_root / "infra" / "templates").mkdir()
		(project_root / "infra" / "lambdas" / "orders").mkdir(parents=True)
		(project_root / "infra" / "stacks" / "infra.yml").write_text("stack")
		(project_root / "infra" / "templates" / "network.yml").write_text("network")
		(project_root / "infra" / "lambdas" / "orders" / "handler.py").write_text("handler")
		s3_manager.create_bucket("test-bucket")
		s3_manager.s3.put_object(
			Bucket="test-bucket",
			Key="demo/lambdas/func2.zip",
			Body=b"stale archive",
		)
		s3_manager.s3.put_object(Bucket="test-bucket", Key="demo/stacks/old.yml", Body=b"old stack")
		s3_manager.s3.put_object(
			Bucket="test-bucket", Key="demo/templates/old.yml", Body=b"old template"
		)
		synced_keys = Build(
			project_root=project_root,
			bucket_name="test-bucket",
			project_name_prefix="demo",
			s3_manager=s3_manager,
		).build()

		assert synced_keys == [
			"demo/stacks/infra.yml",
			"demo/templates/network.yml",
			"demo/lambdas/orders.zip",
		]
		assert s3_manager.s3.head_bucket(Bucket="test-bucket")
		response = s3_manager.s3.get_object(Bucket="test-bucket", Key="demo/lambdas/orders.zip")
		with ZipFile(BytesIO(response["Body"].read())) as archive:
			assert archive.namelist() == ["handler.py"]
			assert archive.read("handler.py") == b"handler"
		assert (
			s3_manager.s3.list_objects_v2(Bucket="test-bucket", Prefix="demo/lambdas/func2").get(
				"Contents"
			)
			is None
		)
		assert (
			s3_manager.s3.list_objects_v2(Bucket="test-bucket", Prefix="demo/stacks/old").get(
				"Contents"
			)
			is None
		)
		assert (
			s3_manager.s3.list_objects_v2(Bucket="test-bucket", Prefix="demo/templates/old").get(
				"Contents"
			)
			is None
		)
