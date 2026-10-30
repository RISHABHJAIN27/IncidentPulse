"""HTTP front door for the triage agent.

POST /alerts          Alertmanager webhook: triage new alerts, resolve incidents for resolved ones
POST /triage          Triage one alert on demand (dry run by default), returns the note
GET  /triage/history  Last 50 triage results
GET  /health
"""

import asyncio
import logging
import threading
import time
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import BackgroundTasks, FastAPI

from .alerts import Alert, AlertmanagerWebhook
from .config import load_settings
from .graph import build_graph
from .knowledge import RunbookRetriever, load_runbooks
from .llm import flush_langfuse, langfuse_callbacks, make_embeddings_factory, make_llm
from .publisher import IncidentPublisher

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("triage_agent")

settings = load_settings()
chunks = load_runbooks(settings.runbook_dir)
retriever = RunbookRetriever(chunks, make_embeddings_factory(settings))
publisher = IncidentPublisher(settings.incidentpulse_url)
agent = build_graph(make_llm(settings), retriever, publisher, settings.max_attempts)
callbacks = langfuse_callbacks(settings)

history: deque = deque(maxlen=50)
_in_progress: set[str] = set()
_in_progress_lock = threading.Lock()


def run_triage(alert: Alert, publish: bool) -> dict:
    started = time.perf_counter()
    state = agent.invoke(
        {"alert": alert, "publish": publish},
        config={
            "callbacks": callbacks,
            "run_name": f"triage {alert.name}",
            "metadata": {"alertname": alert.name, "severity": alert.severity_label},
        },
    )
    result = {
        "at": datetime.now(timezone.utc).isoformat(),
        "alertname": alert.name,
        "alert_key": alert.key,
        "note": state["note"],
        "fallback_used": state["fallback_used"],
        "attempts": state["attempts"],
        "rejected_drafts": [v for v in state.get("violation_log", []) if v],
        "retrieval": retriever.last_mode,
        "context_runbooks": sorted({c.source for c in state["context"]}),
        "incident_id": state.get("incident_id"),
        "published": state.get("published", False),
        "duration_ms": round((time.perf_counter() - started) * 1000),
    }
    history.appendleft(result)
    log.info("triaged %s: severity=%s fallback=%s published=%s",
             alert.name, result["note"]["severity"], result["fallback_used"], result["published"])
    return result


def _triage_in_background(alert: Alert) -> None:
    try:
        run_triage(alert, publish=True)
    except Exception:
        log.exception("triage failed for %s", alert.name)
    finally:
        with _in_progress_lock:
            _in_progress.discard(alert.key)


async def _retry_loop() -> None:
    while True:
        await asyncio.sleep(30)
        if publisher.pending_count():
            await asyncio.to_thread(publisher.retry_pending)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_retry_loop())
    log.info("triage agent ready: %d runbook sections, model %s", len(chunks), settings.ollama_model)
    yield
    task.cancel()
    flush_langfuse(settings)


app = FastAPI(title="Incident Pulse triage agent", version="1.0.0", lifespan=lifespan)


@app.post("/alerts")
def receive_alerts(payload: AlertmanagerWebhook, background: BackgroundTasks):
    accepted = []
    for alert in payload.alerts:
        if alert.status == "resolved":
            background.add_task(publisher.resolve, alert.key)
            accepted.append({"alertname": alert.name, "action": "resolve"})
            continue
        with _in_progress_lock:
            if alert.key in _in_progress or publisher.known(alert.key):
                continue  # Alertmanager re-sends firing alerts; one incident per alert
            _in_progress.add(alert.key)
        background.add_task(_triage_in_background, alert)
        accepted.append({"alertname": alert.name, "action": "triage"})
    return {"accepted": accepted}


@app.post("/triage")
def triage_one(alert: Alert, publish: bool = False):
    return run_triage(alert, publish=publish)


@app.get("/triage/history")
def triage_history():
    return list(history)


@app.get("/health")
def health():
    return {"status": "healthy", "pending_publishes": publisher.pending_count()}
