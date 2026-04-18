import boto3
from boto3.dynamodb.conditions import Attr
from datetime import datetime

from app.models import Incident, IncidentCreate, IncidentUpdate
from app.config import ENVIRONMENT, TABLE_NAME
from time import perf_counter


def init_dynamodb():
    # Called ONCE at startup — creates and returns the boto3 resource.
    # The result is stored in app.state and reused for every request.
    if ENVIRONMENT == "local":
        return boto3.resource(
            "dynamodb",
            region_name="us-east-1",
            endpoint_url="http://localhost:8001",
            aws_access_key_id="local",
            aws_secret_access_key="local",
        )
    return boto3.resource("dynamodb")


def create_table_if_not_exists(dynamodb):
    # This only runs locally — in production, Terraform creates the table.
    if ENVIRONMENT != "local":
        return

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


def create_incident(table, data: IncidentCreate) -> Incident:
    # Build the full incident — id, status, timestamps are auto generated
    t0 = perf_counter()
    incident = Incident(title=data.title, severity=data.severity)
    t1 = perf_counter()


    table.put_item(Item={
        "id": incident.id,
        "title": incident.title,
        "severity": incident.severity.value,
        "status": incident.status.value,
        "created_at": incident.created_at.isoformat(),
        "updated_at": incident.updated_at.isoformat(),
    })
    t2 = perf_counter()


    print(
        "[timing] create_incident "
        f"model={(t1 - t0)*1000:.2f}ms "
        f"put_item={(t2 - t1)*1000:.2f}ms "
        f"total={(t2 - t0)*1000:.2f}ms"
    )

    return incident


def get_all_incidents(table, status_filter: str = None) -> list[Incident]:
    # If a status filter is passed, only return matching incidents
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


def get_incident(table, incident_id: str) -> Incident | None:
    response = table.get_item(Key={"id": incident_id})
    item = response.get("Item")

    if not item:
        return None

    return _item_to_incident(item)


def update_incident(table, incident_id: str, data: IncidentUpdate) -> Incident | None:
    # Make sure the incident actually exists before trying to update
    existing = get_incident(table, incident_id)
    if not existing:
        return None

    now = datetime.utcnow()

    table.update_item(
        Key={"id": incident_id},
        UpdateExpression="SET #s = :status, updated_at = :updated_at",
        # 'status' is a reserved word in DynamoDB so we use an alias #s
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
    # Small helper to convert raw DynamoDB data into an Incident object.
    # Both get_all_incidents and get_incident need this — so we write it once.
    return Incident(
        id=item["id"],
        title=item["title"],
        severity=item["severity"],
        status=item["status"],
        created_at=datetime.fromisoformat(item["created_at"]),
        updated_at=datetime.fromisoformat(item["updated_at"]),
    )