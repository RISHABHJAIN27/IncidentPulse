from fastapi import FastAPI, HTTPException
from app.models import Incident, IncidentCreate, IncidentUpdate

app = FastAPI(
    title="Incident Pulse",
    description="Real-Time Incident Status Page API",
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

@app.on_event("startup")
def startup():
    # We'll wire up the real database here in the next step.
    # For now this just confirms the app booted cleanly.

    # Deserialise config
    # Inject dependencies from the config to DB
    # initialise DB

    print("Environment:", os.getenv("ENVIRONMENT"))
    print("Incident Pulse is up and running.")


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
    # data is automatically validated by Pydantic against IncidentCreate model.
    # If title or severity is missing, FastAPI rejects the request before we
    # even get here.
    incident = Incident(title=data.title, severity=data.severity)
    # TODO: save to database in next step
    return incident


@app.get("/incidents")
def list_incidents(status: str = None):
    # 'status' is an optional query parameter — e.g. /incidents?status=resolved
    # If not provided it defaults to None and we return everything.
    # TODO: fetch from database in next step
    return []


@app.get("/incidents/{incident_id}")
def get_incident(incident_id: str):
    # incident_id is pulled from the URL path automatically by FastAPI.
    # TODO: fetch from database in next step
    # Returning 404 when an incident isn't found is the correct HTTP behaviour.
    raise HTTPException(status_code=404, detail="Incident not found")


@app.patch("/incidents/{incident_id}")
def update_incident(incident_id: str, data: IncidentUpdate):
    # Only the status field can be updated — IncidentUpdate enforces this.
    # TODO: update in database in next step
    raise HTTPException(status_code=404, detail="Incident not found")


# ---------------------------------------------------------------------------
# Status summary
# ---------------------------------------------------------------------------

@app.get("/status")
def system_status():
    # Returns a high-level summary of system health.
    # A real status page (like statuspage.io) shows something like this.
    # TODO: calculate from real incidents in next step
    return {
        "status": "operational",
        "active_incidents": 0,
        "message": "All systems normal",
    }