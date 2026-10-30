import pytest

from triage_agent.alerts import Alert
from triage_agent.config import load_settings
from triage_agent.knowledge import RunbookRetriever, load_runbooks

RB = "https://github.com/RISHABHJAIN27/IncidentPulse/blob/main/runbooks"


@pytest.fixture(scope="session")
def chunks():
    return load_runbooks(load_settings().runbook_dir)


@pytest.fixture
def retriever(chunks):
    return RunbookRetriever(chunks)  # keyword only: no Ollama in tests


@pytest.fixture
def page_alert():
    return Alert(
        status="firing",
        fingerprint="abc123",
        labels={"alertname": "IncidentPulseAvailabilityBudgetBurnFast", "severity": "page",
                "slo": "availability", "service": "incident-pulse"},
        annotations={"summary": "Incident Pulse is burning its availability error budget fast",
                     "description": "At this rate the 30-day availability error budget runs out in under 2 days.",
                     "runbook_url": f"{RB}/slo-availability-burn.md"},
    )


@pytest.fixture
def good_note():
    return {
        "severity": "high",
        "title": "Elevated API errors",
        "likely_cause": "DynamoDB is timing out.",
        "first_steps": ["Check /ready", "Read recent app logs"],
        "runbook": "slo-availability-burn.md",
        "confidence": "medium",
    }
