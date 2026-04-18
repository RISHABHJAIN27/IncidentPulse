from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from app.models import Incident, IncidentCreate, IncidentUpdate
from app import database


# ---------------------------------------------------------------------------
# Lifespan — runs setup on startup, cleanup on shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once when the app starts
    database.create_table_if_not_exists()
    print("Incident Pulse is up and running.")

    yield   # app is running here, serving requests

    # Runs once when the app shuts down
    print("Incident Pulse is shutting down.")


app = FastAPI(
    title="Incident Pulse",
    description="Real-Time Incident Status Page API",
    version="1.0.0",
    lifespan=lifespan,
)


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
def create_incident(data: IncidentCreate):
    incident = database.create_incident(data)
    return incident


@app.get("/incidents")
def list_incidents(status: str = None):
    incidents = database.get_all_incidents(status_filter=status)
    return incidents


@app.get("/incidents/{incident_id}")
def get_incident(incident_id: str):
    incident = database.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@app.patch("/incidents/{incident_id}")
def update_incident(incident_id: str, data: IncidentUpdate):
    incident = database.update_incident(incident_id, data)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


# ---------------------------------------------------------------------------
# Status summary
# ---------------------------------------------------------------------------

@app.get("/status")
def system_status():
    all_incidents = database.get_all_incidents()

    active = [i for i in all_incidents if i.status != "resolved"]
    active_count = len(active)
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