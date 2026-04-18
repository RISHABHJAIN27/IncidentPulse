import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from datetime import datetime

from app.main import app
from app.models import Incident, SeverityLevel, IncidentStatus



# Create a fake browser that talks directly to our FastAPI app
client = TestClient(app)

# A reusable fake incident with known, fixed values.
# Using fixed values means we always know exactly what to expect in responses.
FAKE_INCIDENT = Incident(
    id="test-id-123",
    title="Payment gateway is down",
    severity=SeverityLevel.critical,
    status=IncidentStatus.investigating,
    created_at=datetime(2024, 1, 15, 10, 30, 0),
    updated_at=datetime(2024, 1, 15, 10, 30, 0),
)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def test_health_check():
    # No database involved — just checks the server is alive
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


# ---------------------------------------------------------------------------
# POST /incidents — create a new incident
# ---------------------------------------------------------------------------

def test_create_incident_success():
    # Mock the database so we don't touch real DynamoDB during tests
    with patch("app.main.database.create_incident", return_value=FAKE_INCIDENT):
        response = client.post("/incidents", json={
            "title": "Payment gateway is down",
            "severity": "critical",
        })

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Payment gateway is down"
    assert data["severity"] == "critical"
    assert data["status"] == "investigating"   # always starts as investigating
    assert data["id"] == "test-id-123"


def test_create_incident_missing_title():
    # Pydantic should reject this before it even reaches our code
    response = client.post("/incidents", json={
        "severity": "critical",
    })

    assert response.status_code == 422   # Unprocessable Entity


def test_create_incident_invalid_severity():
    # "banana" is not in our SeverityLevel enum
    response = client.post("/incidents", json={
        "title": "Something broke",
        "severity": "banana",
    })

    assert response.status_code == 422


def test_create_incident_missing_both_fields():
    # Sending completely empty body
    response = client.post("/incidents", json={})

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /incidents — list all incidents
# ---------------------------------------------------------------------------

def test_list_incidents_returns_all():
    with patch("app.main.database.get_all_incidents", return_value=[FAKE_INCIDENT]):
        response = client.get("/incidents")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Payment gateway is down"


def test_list_incidents_empty():
    # When no incidents exist — should return empty list, not an error
    with patch("app.main.database.get_all_incidents", return_value=[]):
        response = client.get("/incidents")

    assert response.status_code == 200
    assert response.json() == []


def test_list_incidents_with_status_filter():
    # Make sure the filter gets passed through to the database function
    with patch("app.main.database.get_all_incidents", return_value=[]) as mock:
        response = client.get("/incidents?status=resolved")

    assert response.status_code == 200
    mock.assert_called_once_with(status_filter="resolved")


# ---------------------------------------------------------------------------
# GET /incidents/{incident_id} — get one specific incident
# ---------------------------------------------------------------------------

def test_get_incident_found():
    with patch("app.main.database.get_incident", return_value=FAKE_INCIDENT):
        response = client.get("/incidents/test-id-123")

    assert response.status_code == 200
    assert response.json()["id"] == "test-id-123"
    assert response.json()["title"] == "Payment gateway is down"


def test_get_incident_not_found():
    # When database returns None — endpoint should respond with 404
    with patch("app.main.database.get_incident", return_value=None):
        response = client.get("/incidents/does-not-exist")

    assert response.status_code == 404
    assert response.json()["detail"] == "Incident not found"


# ---------------------------------------------------------------------------
# PATCH /incidents/{incident_id} — update an incident's status
# ---------------------------------------------------------------------------

def test_update_incident_success():
    # Create an updated version of our fake incident with resolved status
    updated_incident = FAKE_INCIDENT.model_copy(
        update={"status": IncidentStatus.resolved}
    )

    with patch("app.main.database.update_incident", return_value=updated_incident):
        response = client.patch("/incidents/test-id-123", json={
            "status": "resolved",
        })

    assert response.status_code == 200
    assert response.json()["status"] == "resolved"


def test_update_incident_not_found():
    # When database returns None — endpoint should respond with 404
    with patch("app.main.database.update_incident", return_value=None):
        response = client.patch("/incidents/does-not-exist", json={
            "status": "resolved",
        })

    assert response.status_code == 404
    assert response.json()["detail"] == "Incident not found"


def test_update_incident_invalid_status():
    # "banana" is not a valid IncidentStatus value
    response = client.patch("/incidents/test-id-123", json={
        "status": "banana",
    })

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /status — system health summary
# ---------------------------------------------------------------------------

def test_system_status_operational():
    # No active incidents — system should be operational
    with patch("app.main.database.get_all_incidents", return_value=[]):
        response = client.get("/status")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert data["active_incidents"] == 0
    assert data["message"] == "All systems normal"


def test_system_status_major_outage_critical():
    # One critical active incident — should trigger major outage
    with patch("app.main.database.get_all_incidents", return_value=[FAKE_INCIDENT]):
        response = client.get("/status")

    data = response.json()
    assert data["status"] == "major_outage"
    assert data["active_incidents"] == 1


def test_system_status_degraded():
    # One medium severity incident — should be degraded, not major outage
    medium_incident = FAKE_INCIDENT.model_copy(
        update={"severity": SeverityLevel.medium}
    )

    with patch("app.main.database.get_all_incidents", return_value=[medium_incident]):
        response = client.get("/status")

    data = response.json()
    assert data["status"] == "degraded"
    assert data["active_incidents"] == 1


def test_system_status_excludes_resolved():
    # Resolved incidents should NOT count towards active_incidents
    resolved_incident = FAKE_INCIDENT.model_copy(
        update={"status": IncidentStatus.resolved}
    )

    with patch("app.main.database.get_all_incidents", return_value=[resolved_incident]):
        response = client.get("/status")

    data = response.json()
    assert data["status"] == "operational"
    assert data["active_incidents"] == 0