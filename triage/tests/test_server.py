import httpx
from fastapi.testclient import TestClient

from triage_agent import server
from triage_agent.graph import build_graph
from triage_agent.publisher import IncidentPublisher


class DownLLM:
    def invoke(self, messages, config=None):
        raise ConnectionError("ollama is down")


def webhook(status, fingerprint="fp-1"):
    return {
        "version": "4",
        "status": status,
        "alerts": [{
            "status": status,
            "fingerprint": fingerprint,
            "labels": {"alertname": "IncidentPulseReplicaDown", "severity": "ticket", "instance": "app-1:8000"},
            "annotations": {"summary": "An Incident Pulse replica is not responding to scrapes",
                            "runbook_url": "https://example.com/runbooks/replica-down.md"},
        }],
    }


def test_alertmanager_webhook_opens_then_resolves_one_incident(monkeypatch):
    calls = []

    def handler(request):
        calls.append(request.method)
        if request.method == "POST":
            return httpx.Response(201, json={"id": "inc-42"})
        return httpx.Response(200, json={"id": "inc-42", "status": "resolved"})

    publisher = IncidentPublisher("http://status", httpx.Client(base_url="http://status", transport=httpx.MockTransport(handler)))
    monkeypatch.setattr(server, "publisher", publisher)
    monkeypatch.setattr(server, "agent", build_graph(DownLLM(), server.retriever, publisher))
    client = TestClient(server.app)

    first = client.post("/alerts", json=webhook("firing"))
    repeat = client.post("/alerts", json=webhook("firing"))  # Alertmanager re-sends while firing
    resolved = client.post("/alerts", json=webhook("resolved"))

    assert first.json()["accepted"] == [{"alertname": "IncidentPulseReplicaDown", "action": "triage"}]
    assert repeat.json()["accepted"] == []
    assert resolved.json()["accepted"][0]["action"] == "resolve"
    assert calls == ["POST", "PATCH"]

    latest = client.get("/triage/history").json()[0]
    assert latest["incident_id"] == "inc-42"
    assert latest["note"]["runbook"] == "replica-down.md"
    assert latest["fallback_used"] is True


def test_manual_triage_is_a_dry_run_by_default(monkeypatch):
    monkeypatch.setattr(server, "agent", build_graph(DownLLM(), server.retriever, None))
    client = TestClient(server.app)
    result = client.post("/triage", json=webhook("firing", "fp-2")["alerts"][0]).json()
    assert result["published"] is False
    assert result["note"]["severity"] == "medium"
