import boto3
from boto3.dynamodb.conditions import Attr
from datetime import datetime

from app.models import Incident, IncidentCreate, IncidentUpdate
from app.config import (
    ENVIRONMENT,
    TABLE_NAME,
    AWS_REGION,
    DYNAMODB_ENDPOINT,
    DYNAMODB_LOCAL_KEY,
    DYNAMODB_LOCAL_SECRET,
)


def _get_dynamodb_resource():
    # Single place that creates the boto3 connection.
    # Every function that needs DynamoDB calls this instead of
    # duplicating the connection code.
    if ENVIRONMENT == "local":
        return boto3.resource(
            "dynamodb",
            region_name=AWS_REGION,
            endpoint_url=DYNAMODB_ENDPOINT,
            aws_access_key_id=DYNAMODB_LOCAL_KEY,
            aws_secret_access_key=DYNAMODB_LOCAL_SECRET,
        )
    return boto3.resource("dynamodb", region_name=AWS_REGION)


def get_dynamodb_table():
    return _get_dynamodb_resource().Table(TABLE_NAME)


def create_table_if_not_exists():
    # This only runs locally — in production, Terraform creates the table.
    if ENVIRONMENT != "local":
        return

    dynamodb = _get_dynamodb_resource()

    existing = [t.name for t in dynamodb.tables.all()]
    if TABLE_NAME in existing:
        return

    dynamodb.create_table(
        TableName=TABLE_NAME,
        KeySchema=[
            {"AttributeName": "id", "KeyType": "HASH"}
        ],
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    print(f"Table '{TABLE_NAME}' created.")


def create_incident(data: IncidentCreate) -> Incident:
    table = get_dynamodb_table()

    incident = Incident(title=data.title, severity=data.severity)

    table.put_item(Item={
        "id": incident.id,
        "title": incident.title,
        "severity": incident.severity.value,
        "status": incident.status.value,
        "created_at": incident.created_at.isoformat(),
        "updated_at": incident.updated_at.isoformat(),
    })

    return incident


def get_all_incidents(status_filter: str = None) -> list[Incident]:
    table = get_dynamodb_table()

    if status_filter:
        response = table.scan(
            FilterExpression=Attr("status").eq(status_filter)
        )
    else:
        response = table.scan()

    incidents = []
    for item in response.get("Items", []):
        incidents.append(_item_to_incident(item))

    return incidents


def get_incident(incident_id: str) -> Incident | None:
    table = get_dynamodb_table()

    response = table.get_item(Key={"id": incident_id})
    item = response.get("Item")

    if not item:
        return None

    return _item_to_incident(item)


def update_incident(incident_id: str, data: IncidentUpdate) -> Incident | None:
    table = get_dynamodb_table()

    existing = get_incident(incident_id)
    if not existing:
        return None

    now = datetime.utcnow()

    table.update_item(
        Key={"id": incident_id},
        UpdateExpression="SET #s = :status, updated_at = :updated_at",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":status": data.status.value,
            ":updated_at": now.isoformat(),
        },
    )

    existing.status = data.status
    existing.updated_at = now
    return existing


def _item_to_incident(item: dict) -> Incident:
    return Incident(
        id=item["id"],
        title=item["title"],
        severity=item["severity"],
        status=item["status"],
        created_at=datetime.fromisoformat(item["created_at"]),
        updated_at=datetime.fromisoformat(item["updated_at"]),
    )