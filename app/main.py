from fastapi import FastAPI

app = FastAPI(
    title="Incident Pulse",
    description="Real-time incident status page API",
    version="0.1.0",
)

@app.get("/health")
def health_check(): 
    return {"status": "healthy"}
