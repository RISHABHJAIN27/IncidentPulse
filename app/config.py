from dotenv import load_dotenv
import os

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
TABLE_NAME = os.getenv("TABLE_NAME", "incidents")

# DynamoDB connection settings
# When running locally, these point to DynamoDB Local in Docker.
# In production, endpoint is not needed — boto3 connects to real AWS.
DYNAMODB_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT", "http://localhost:8001")
DYNAMODB_LOCAL_KEY = os.getenv("DYNAMODB_LOCAL_KEY", "local")
DYNAMODB_LOCAL_SECRET = os.getenv("DYNAMODB_LOCAL_SECRET", "local")