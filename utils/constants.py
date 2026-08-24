import os

from dotenv import load_dotenv

# loading env variables
load_dotenv()


# env variables
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "ap-south-1")


# constants
PDW_S3_BUCKET_SANDBOX_PROJECT_PARTIALS = "pdw-s3-bucket-sandbox-project-partials"
PDW_STACK_SANDBOX_CORE_INFRA = "pdw-stack-sandbox-core-infra"
PROJECT_NAME_PREFIX = "microservices-project-infra"
