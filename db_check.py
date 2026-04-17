# save as dynamo_healthcheck.py
import boto3
from botocore.exceptions import ClientError

TABLE = "HealthCheckTable"

dynamodb = boto3.client(
    "dynamodb",
    endpoint_url="http://localhost:8001",
    region_name="us-east-1",
    aws_access_key_id="dummy",
    aws_secret_access_key="dummy",
)

def ensure_table():
    existing = dynamodb.list_tables()["TableNames"]
    if TABLE not in existing:
        dynamodb.create_table(
            TableName=TABLE,
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            BillingMode="PAY_PER_REQUEST",
        )
        waiter = dynamodb.get_waiter("table_exists")
        waiter.wait(TableName=TABLE)

def run_check():
    ensure_table()
    dynamodb.put_item(
        TableName=TABLE,
        Item={"id": {"S": "1"}, "status": {"S": "ok"}},
    )
    item = dynamodb.get_item(
        TableName=TABLE,
        Key={"id": {"S": "1"}},
    ).get("Item")
    print("DynamoDB local OK:", item)

if __name__ == "__main__":
    run_check()