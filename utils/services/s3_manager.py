import json
import logging

import boto3

from utils.logging_config import SUCCESS_LEVEL

logger = logging.getLogger(__name__)


class S3Manager:
	def __init__(self, access_key, secret_key, region="ap-south-1"):
		"""
		Initializes the S3Manager with AWS credentials and creates an S3 client.

		:param access_key: AWS Access Key ID
		:param secret_key: AWS Secret Access Key
		:param region: AWS region name (default is 'ap-south-1')
		"""
		self.__session = boto3.session.Session(
			aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region
		)
		self.s3 = self.__session.client("s3")

	def get_buckets(self):
		"""Returns a list of all S3 bucket names."""
		try:
			response = self.s3.list_buckets()
			buckets = [bucket["Name"] for bucket in response["Buckets"]]
			return buckets
		except Exception as e:
			logger.error("Error fetching S3 buckets: %s", e)
			return []

	def create_bucket(self, bucket_name):
		try:
			location = {"LocationConstraint": self.s3.meta.region_name}
			self.s3.create_bucket(
				Bucket=bucket_name,
				CreateBucketConfiguration=location,
			)
			logger.log(SUCCESS_LEVEL, "S3 bucket created successfully: %s", bucket_name)
			return True
		except Exception as e:
			if "BucketAlreadyOwnedByYou" in str(e):
				logger.info("S3 bucket already exists: %s", bucket_name)
			else:
				logger.error("Error creating S3 bucket %s: %s", bucket_name, e)
			return False

	def upload_file(self, file_path, bucket_name, object_key, extra_args=None):
		"""
		Uploads a file from local storage to the specified S3 bucket.

		:param file_path: Path to the local file
		:param bucket_name: Target S3 bucket
		:param object_key: Optional S3 object key (defaults to file name)
		"""
		try:
			self.s3.upload_file(
				file_path,
				bucket_name,
				object_key,
				ExtraArgs=extra_args or {},
			)
			logger.log(SUCCESS_LEVEL, "Synchronized %s in S3 bucket %s", object_key, bucket_name)
			return True
		except Exception as e:
			logger.error("Error synchronizing S3 object %s: %s", object_key, e)
			return False

	def sync_file(self, file_path, bucket_name, object_key, extra_args=None):
		"""Synchronize one local file with an S3 object."""
		return self.upload_file(file_path, bucket_name, object_key, extra_args)

	def list_object_keys(self, bucket_name, prefix=""):
		"""Return all object keys under a bucket prefix."""
		try:
			paginator = self.s3.get_paginator("list_objects_v2")
			return [
				item["Key"]
				for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix)
				for item in page.get("Contents", [])
			]
		except Exception as e:
			logger.error("Error listing S3 objects under %s: %s", prefix, e)
			return []

	def delete_object(self, bucket_name, object_key):
		"""Delete one S3 object."""
		try:
			self.s3.delete_object(Bucket=bucket_name, Key=object_key)
			logger.info("Deleted S3 object %s from %s", object_key, bucket_name)
			return True
		except Exception as e:
			logger.error("Error deleting S3 object %s: %s", object_key, e)
			return False

	def empty_bucket(self, bucket_name):
		"""Delete every object version and delete marker from a bucket."""
		try:
			paginator = self.s3.get_paginator("list_object_versions")
			for page in paginator.paginate(Bucket=bucket_name):
				objects = [
					{"Key": item["Key"], "VersionId": item["VersionId"]}
					for item in page.get("Versions", []) + page.get("DeleteMarkers", [])
				]
				if objects:
					self.s3.delete_objects(Bucket=bucket_name, Delete={"Objects": objects})
			logger.info("Emptied S3 bucket %s", bucket_name)
			return True
		except Exception as e:
			logger.error("Error emptying S3 bucket %s: %s", bucket_name, e)
			return False

	def delete_bucket(self, bucket_name):
		"""Delete an empty S3 bucket."""
		try:
			self.s3.delete_bucket(Bucket=bucket_name)
			logger.log(SUCCESS_LEVEL, "S3 bucket deleted successfully: %s", bucket_name)
			return True
		except Exception as e:
			logger.error("Error deleting S3 bucket %s: %s", bucket_name, e)
			return False

	def add_public_read_object_policy(self, bucket_name, object_key):

		# Define the bucket policy
		bucket_policy = {
			"Version": "2012-10-17",
			"Statement": [
				{
					"Sid": "AllowPublicRead",
					"Effect": "Allow",
					"Action": "s3:GetObject",
					"Resource": f"arn:aws:s3:::{bucket_name}/{object_key}",
					"Principal": "*",
				}
			],
		}

		# Convert the policy to JSON string format
		policy_string = json.dumps(bucket_policy)

		try:
			# Attach the policy to the bucket
			self.s3.put_bucket_policy(Bucket=bucket_name, Policy=policy_string)
			return True
		except Exception as e:
			logger.error("Error adding bucket policy to %s: %s", bucket_name, e)

	def disable_public_access_block(self, bucket_name):
		try:
			self.s3.put_public_access_block(
				Bucket=bucket_name,
				PublicAccessBlockConfiguration={
					"BlockPublicAcls": False,  # Allow public ACLs
					"IgnorePublicAcls": False,  # Allow public ACLs
					"BlockPublicPolicy": False,  # Allow public policies
					"RestrictPublicBuckets": False,  # Allow unrestricted public access
				},
			)
		except Exception as e:
			logger.error("Error setting public access block for %s: %s", bucket_name, e)
