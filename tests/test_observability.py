import inspect
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

with patch("app.database.create_table_if_not_exists"):
    from app.main import app

from app.observability import REQUESTS

client = TestClient(app)


def _count(route, status_code, method="GET"):
    return REQUESTS.labels(method, route, status_code)._value.get()


# ---------------------------------------------------------------------------
# /metrics
# ---------------------------------------------------------------------------

def test_metrics_endpoint_exposes_sli_series():
    client.get("/health")
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "http_requests_total" in response.text
    assert "http_request_duration_seconds_bucket" in response.text
    # 0.3s must be a bucket boundary: it is the latency SLO threshold.
    assert 'le="0.3"' in response.text


def test_metrics_use_route_template_not_raw_path():
    before = _count("/incidents/{incident_id}", "404")
    with patch("app.main.database.get_incident", return_value=None):
        client.get("/incidents/some-random-id-1")
        client.get("/incidents/some-random-id-2")

    assert _count("/incidents/{incident_id}", "404") == before + 2
    assert "some-random-id" not in client.get("/metrics").text


def test_server_errors_are_counted_as_500():
    before = _count("/incidents", "500")
    failing_client = TestClient(app, raise_server_exceptions=False)
    with patch("app.main.database.get_all_incidents", side_effect=RuntimeError("dynamodb down")):
        response = failing_client.get("/incidents")

    assert response.status_code == 500
    assert _count("/incidents", "500") == before + 1


def test_metrics_endpoint_is_not_counted():
    before = _count("/metrics", "200")
    client.get("/metrics")
    assert _count("/metrics", "200") == before


# ---------------------------------------------------------------------------
# /ready
# ---------------------------------------------------------------------------

def test_ready_when_dynamodb_reachable():
    with patch("app.main.database.check_ready", return_value=True):
        response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_not_ready_when_dynamodb_unreachable():
    with patch("app.main.database.check_ready", return_value=False):
        response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["reason"] == "dynamodb_unreachable"


def test_health_does_not_depend_on_dynamodb():
    with patch("app.main.database.check_ready", side_effect=AssertionError("must not be called")):
        response = client.get("/health")
    assert response.status_code == 200


def test_liveness_and_metrics_do_not_wait_for_the_request_thread_pool():
    # Sync handlers share one thread pool with the DynamoDB calls. In the brownout
    # experiment that pool filled up, /health timed out and /metrics could not be
    # scraped, so the SLO alerts went blind. These two must stay async.
    endpoints = {route.path: route.endpoint for route in app.routes if hasattr(route, "endpoint")}
    assert inspect.iscoroutinefunction(endpoints["/health"])
    assert inspect.iscoroutinefunction(endpoints["/metrics"])


# check_ready after DynamoDB Local restarts (in-memory: the table is gone)
def _not_found():
    from botocore.exceptions import ClientError
    return ClientError({"Error": {"Code": "ResourceNotFoundException", "Message": "gone"}}, "DescribeTable")


def test_ready_recreates_missing_table_locally():
    from app import database
    resource = MagicMock()
    resource.meta.client.describe_table.side_effect = _not_found()
    with patch.object(database, "ENVIRONMENT", "local"), \
         patch.object(database, "_get_dynamodb_resource", return_value=resource), \
         patch.object(database, "create_table_if_not_exists") as create:
        assert database.check_ready() is True
    create.assert_called_once()


def test_missing_table_in_production_is_not_ready():
    from app import database
    resource = MagicMock()
    resource.meta.client.describe_table.side_effect = _not_found()
    with patch.object(database, "ENVIRONMENT", "production"), \
         patch.object(database, "_get_dynamodb_resource", return_value=resource), \
         patch.object(database, "create_table_if_not_exists") as create:
        assert database.check_ready() is False
    create.assert_not_called()
