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

# ---- Kubernetes (kind) ------------------------------------------------------
kind-up:
    kind create cluster --name incident-pulse --config deploy/kind/kind-config.yaml
    docker build -t incident-pulse:local .
    kind load docker-image incident-pulse:local --name incident-pulse
    helm upgrade --install incident-pulse deploy/helm/incident-pulse -f deploy/helm/incident-pulse/values-kind.yaml --wait --timeout 5m
    helm test incident-pulse --logs

kind-smoke:
    docker run --rm -v "${PWD}/loadtest:/scripts" -e BASE_URL=http://host.docker.internal:8080 grafana/k6:2.3.0 run /scripts/smoke.js

kind-down:
    kind delete cluster --name incident-pulse

# ---- Security scans ---------------------------------------------------------
scan-secrets:
    docker run --rm -v "${PWD}:/repo" zricethezav/gitleaks:v8.30.1 git /repo --redact --no-banner -v

scan-config:
    docker run --rm -v "${PWD}:/src" aquasec/trivy:0.76.1 config --severity HIGH,CRITICAL /src/Dockerfile
    docker run --rm -v "${PWD}:/src" aquasec/trivy:0.76.1 config --severity HIGH,CRITICAL /src/deploy/helm

scan-image:
    docker build -t incident-pulse:scan .
    docker run --rm -v //var/run/docker.sock:/var/run/docker.sock aquasec/trivy:0.76.1 image --severity HIGH,CRITICAL incident-pulse:scan
