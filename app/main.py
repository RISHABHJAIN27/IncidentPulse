from fastapi import FastAPI, HTTPException, Depends
from app.models import Incident, IncidentCreate, IncidentUpdate
from app.config import TABLE_NAME
from app import database
from time import perf_counter
import os

app = FastAPI(
    title="Incident Pulse",
    description="Real-Time Incident Status Page API",
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# Startup — runs once when the app boots up
# ---------------------------------------------------------------------------

@app.on_event("startup")
def startup():
    # Create the DynamoDB resource ONCE and store it in app.state.
    # Every request will reuse this same object — no recreating per request.
    dynamodb = database.init_dynamodb()
    app.state.table = dynamodb.Table(TABLE_NAME)

    # Create the local table if it doesn't exist yet.
    database.create_table_if_not_exists(dynamodb)
    print("Incident Pulse is up and running.")


# ---------------------------------------------------------------------------
# Dependency — provides the shared table to every endpoint that needs it
# ---------------------------------------------------------------------------

def get_table():
    # FastAPI calls this automatically for any endpoint that uses Depends(get_table).
    # It simply returns the shared table object from app.state.
    return app.state.table


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
def health_check():
    return {"status": "healthy"}


# ---------------------------------------------------------------------------
# Incidents
# ---------------------------------------------------------------------------

@app.post("/incidents", status_code=201)
def create_incident(data: IncidentCreate, table=Depends(get_table)):
    t0 = perf_counter()
    incident = database.create_incident(table, data)
    t1 = perf_counter()

    print(f"[timing] POST /incidents total={(t1 - t0)*1000:.2f}ms")
    return incident


@app.get("/incidents")
def list_incidents(status: str = None, table=Depends(get_table)):
    incidents = database.get_all_incidents(table, status_filter=status)
    return incidents


@app.get("/incidents/{incident_id}")
def get_incident(incident_id: str, table=Depends(get_table)):
    incident = database.get_incident(table, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@app.patch("/incidents/{incident_id}")
def update_incident(incident_id: str, data: IncidentUpdate, table=Depends(get_table)):
    incident = database.update_incident(table, incident_id, data)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


# ---------------------------------------------------------------------------
# Status summary
# ---------------------------------------------------------------------------

@app.get("/status")
def system_status(table=Depends(get_table)):
    all_incidents = database.get_all_incidents(table)

    # Count only incidents that are not yet resolved
    active = [i for i in all_incidents if i.status != "resolved"]
    active_count = len(active)

    # If any active incident is critical — that's a major outage
    has_critical = any(i.severity == "critical" for i in active)

    if active_count == 0:
        overall = "operational"
        message = "All systems normal"
    elif has_critical or active_count >= 3:
        overall = "major_outage"
        message = f"{active_count} active incident(s) — major outage"
    else:
        overall = "degraded"
        message = f"{active_count} active incident(s) — degraded performance"

    return {
        "status": overall,
        "active_incidents": active_count,
        "message": message,
    }