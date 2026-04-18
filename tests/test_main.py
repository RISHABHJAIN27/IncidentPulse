import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from unittest.mock import patch, MagicMock
from datetime import datetime
from fastapi.testclient import TestClient

# Patch the startup database call BEFORE creating TestClient.
# This stops tests from needing a real DynamoDB connection.
with patch("app.database.create_table_if_not_exists"):
    from app.main import app

from app.models import Incident, SeverityLevel, IncidentStatus

client = TestClient(app)

# A reusable fake incident with known, fixed values
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
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


# ---------------------------------------------------------------------------
# POST /incidents
# ---------------------------------------------------------------------------

def test_create_incident_success():
    with patch("app.main.database.create_incident", return_value=FAKE_INCIDENT):
        response = client.post("/incidents", json={
            "title": "Payment gateway is down",
            "severity": "critical",
        })

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Payment gateway is down"
    assert data["severity"] == "critical"
    assert data["status"] == "investigating"
    assert data["id"] == "test-id-123"


def test_create_incident_missing_title():
    response = client.post("/incidents", json={
        "severity": "critical",
    })
    assert response.status_code == 422


def test_create_incident_invalid_severity():
    response = client.post("/incidents", json={
        "title": "Something broke",
        "severity": "banana",
    })
    assert response.status_code == 422


def test_create_incident_missing_both_fields():
    response = client.post("/incidents", json={})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /incidents
# ---------------------------------------------------------------------------

def test_list_incidents_returns_all():
    with patch("app.main.database.get_all_incidents", return_value=[FAKE_INCIDENT]):
        response = client.get("/incidents")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Payment gateway is down"


def test_list_incidents_empty():
    with patch("app.main.database.get_all_incidents", return_value=[]):
        response = client.get("/incidents")

    assert response.status_code == 200
    assert response.json() == []


def test_list_incidents_with_status_filter():
    with patch("app.main.database.get_all_incidents", return_value=[]) as mock:
        response = client.get("/incidents?status=resolved")

    assert response.status_code == 200
    mock.assert_called_once_with(status_filter="resolved")


# ---------------------------------------------------------------------------
# GET /incidents/{incident_id}
# ---------------------------------------------------------------------------

def test_get_incident_found():
    with patch("app.main.database.get_incident", return_value=FAKE_INCIDENT):
        response = client.get("/incidents/test-id-123")

    assert response.status_code == 200
    assert response.json()["id"] == "test-id-123"


def test_get_incident_not_found():
    with patch("app.main.database.get_incident", return_value=None):
        response = client.get("/incidents/does-not-exist")

    assert response.status_code == 404
    assert response.json()["detail"] == "Incident not found"


# ---------------------------------------------------------------------------
# PATCH /incidents/{incident_id}
# ---------------------------------------------------------------------------

def test_update_incident_success():
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
    with patch("app.main.database.update_incident", return_value=None):
        response = client.patch("/incidents/does-not-exist", json={
            "status": "resolved",
        })

    assert response.status_code == 404
    assert response.json()["detail"] == "Incident not found"


def test_update_incident_invalid_status():
    response = client.patch("/incidents/test-id-123", json={
        "status": "banana",
    })
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /status
# ---------------------------------------------------------------------------

def test_system_status_operational():
    with patch("app.main.database.get_all_incidents", return_value=[]):
        response = client.get("/status")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert data["active_incidents"] == 0
    assert data["message"] == "All systems normal"


def test_system_status_major_outage_critical():
    with patch("app.main.database.get_all_incidents", return_value=[FAKE_INCIDENT]):
        response = client.get("/status")

    data = response.json()
    assert data["status"] == "major_outage"
    assert data["active_incidents"] == 1


def test_system_status_degraded():
    medium_incident = FAKE_INCIDENT.model_copy(
        update={"severity": SeverityLevel.medium}
    )

    with patch("app.main.database.get_all_incidents", return_value=[medium_incident]):
        response = client.get("/status")

    data = response.json()
    assert data["status"] == "degraded"
    assert data["active_incidents"] == 1


def test_system_status_excludes_resolved():
    resolved_incident = FAKE_INCIDENT.model_copy(
        update={"status": IncidentStatus.resolved}
    )

    with patch("app.main.database.get_all_incidents", return_value=[resolved_incident]):
        response = client.get("/status")

    data = response.json()
    assert data["status"] == "operational"
    assert data["active_incidents"] == 0