import logging

import boto3

from utils.constants import AWS_DEFAULT_REGION
from utils.logging_config import SUCCESS_LEVEL

logger = logging.getLogger(__name__)


class CloudFormationClient:
	def __init__(self, access_key, secret_key, region=AWS_DEFAULT_REGION):
		self.__session = boto3.session.Session(
			aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region
		)
		self.cf_client = self.__session.client("cloudformation")

	def get_cf_client(self):
		return self.cf_client


class CloudFormationStack:
	def __init__(self, stack_name, template_url, parameters, cf_client):
		self.stack_name = stack_name
		self.template_url = template_url
		self.parameters = parameters
		self.cf_client = cf_client

	def __create_stack(self):
		"""Create a CloudFormation Stack"""
		logger.info("Creating stack %s with template %s", self.stack_name, self.template_url)
		response = self.cf_client.create_stack(
			StackName=self.stack_name,
			TemplateURL=self.template_url,
			Parameters=self.parameters,
			Capabilities=["CAPABILITY_NAMED_IAM"],
			OnFailure="DELETE",
		)
		logger.debug("Stack creation response for %s: %s", self.stack_name, response)
		return response

	def __update_stack(self):
		"""Update an existing CloudFormation Stack"""
		logger.info("Updating stack %s with template %s", self.stack_name, self.template_url)
		response = self.cf_client.update_stack(
			StackName=self.stack_name,
			TemplateURL=self.template_url,
			Parameters=self.parameters,
			Capabilities=["CAPABILITY_NAMED_IAM"],
		)
		logger.debug("Stack update response for %s: %s", self.stack_name, response)
		return response

	def deploy(self):
		"""Deploys the stack by first checking if it exists and either creates or updates"""
		try:
			logger.info("Initiating deployment of stack %s", self.stack_name)
			self.__create_stack()
			logger.log(SUCCESS_LEVEL, "Stack created successfully: %s", self.stack_name)

		except Exception as e:
			if "AlreadyExistsException" in str(e):
				logger.info("Stack already exists: %s", self.stack_name)
				try:
					# update the stack
					logger.info("Updating stack: %s", self.stack_name)
					self.__update_stack()
					logger.log(SUCCESS_LEVEL, "Stack updated successfully: %s", self.stack_name)
				except Exception as update_err:
					if "No updates are to be performed" in str(update_err):
						logger.info("No updates are required for stack: %s", self.stack_name)
					else:
						logger.error("Error updating stack %s: %s", self.stack_name, update_err)
			else:
				logger.error("Error creating stack %s: %s", self.stack_name, e)

	def delete(self):
		"""Delete the stack and wait until CloudFormation confirms its removal."""
		logger.info("Deleting stack %s", self.stack_name)
		self.cf_client.delete_stack(StackName=self.stack_name)
		self.cf_client.get_waiter("stack_delete_complete").wait(StackName=self.stack_name)
		logger.log(SUCCESS_LEVEL, "Stack deleted successfully: %s", self.stack_name)
