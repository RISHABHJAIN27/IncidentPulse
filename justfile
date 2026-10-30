set shell := ["powershell.exe", "-NoLogo", "-Command"]

run:
    python -m uvicorn app.main:app --reload

activate-venv:
    .\venv\Scripts\activate

run-dynamodb:
    docker run -d --name dynamodb-local -p 8001:8000 amazon/dynamodb-local

# ---- Reliability lab ------------------------------------------------------
up:
    docker compose up -d --build

up-langfuse:
    docker compose -f docker-compose.yml -f observability/langfuse/docker-compose.langfuse.yml up -d --build

down:
    docker compose -f docker-compose.yml -f observability/langfuse/docker-compose.langfuse.yml down

smoke:
    docker compose run --rm --no-deps k6 run /scripts/smoke.js

load:
    docker compose run --rm --no-deps k6 run /scripts/load.js

stress:
    docker compose run --rm --no-deps k6 run /scripts/stress.js

chaos-replica:
    chaos run chaos/replica-loss.json

chaos-dynamodb:
    chaos run chaos/dynamodb-brownout.json

test-rules:
    docker run --rm -v "${PWD}/observability/prometheus:/p" --entrypoint promtool prom/prometheus:v3.15.1 test rules /p/tests/slo.test.yml

eval:
    npx promptfoo@latest eval -c evals/promptfooconfig.yaml
