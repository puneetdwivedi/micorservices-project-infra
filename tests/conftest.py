import pytest
from moto import mock_aws

from utils.services.s3_manager import S3Manager


@pytest.fixture
def aws_credentials(monkeypatch):
	monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
	monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
	monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
	monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-south-1")


@pytest.fixture
def s3_manager(aws_credentials):
	with mock_aws():
		yield S3Manager("testing", "testing", region="ap-south-1")
