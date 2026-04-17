from dotenv import load_dotenv
import os

# Load all variables from .env file into the environment.
# This runs once when the app starts.
load_dotenv()

# Now read them — these are the only settings your app needs to know about.
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
TABLE_NAME = os.getenv("TABLE_NAME", "incidents")