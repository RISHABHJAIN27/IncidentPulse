# Built from the repo root so the runbooks can be copied in:
#   docker build -f triage/Dockerfile -t incident-pulse-triage .
FROM python:3.12-slim

WORKDIR /app

COPY triage/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY triage/triage_agent ./triage_agent
COPY runbooks ./runbooks

ENV RUNBOOK_DIR=/app/runbooks
EXPOSE 8090

CMD ["uvicorn", "triage_agent.server:app", "--host", "0.0.0.0", "--port", "8090"]
