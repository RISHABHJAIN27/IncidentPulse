# Failure mode analysis

What can break in Incident Pulse, what users would see, how we find out, and what protects against it. "Verified by" points to the test or experiment that proves the row is true. Rows marked **open** are known gaps with a proposed fix.

| # | Component | Failure mode | User impact | Detection | Mitigation | Verified by |
|---|---|---|---|---|---|---|
| 1 | App replica | Crash, OOM kill or task replacement | None if another replica is up: the load balancer fails over, with a brief latency blip | `IncidentPulseReplicaDown` (ticket) | Two replicas behind the load balancer; `restart: unless-stopped` locally, ECS service scheduler on AWS | `chaos/replica-loss.json` |
| 2 | App tier | All replicas down | Full outage | `IncidentPulseAllReplicasDown` (page) | ECS replaces tasks; spread tasks across AZs | `slo.test.yml` |
| 3 | DynamoDB | Brownout: connections open, nothing answers | **Before:** requests hung for up to a minute on boto3 default timeouts. **Now:** fail in about 15 s with a 500 | `AvailabilityBudgetBurnFast` and `LatencyBudgetBurnFast` (page) | Bounded boto3 timeouts and retries (`app/database.py`: 2 s connect, 5 s read, 3 attempts) | `chaos/dynamodb-brownout.json` |
| 4 | DynamoDB | Throttling | 500s on writes or scans | Availability burn alerts | On-demand capacity; boto3 standard retry mode with backoff | Runbook `dynamodb-errors.md` |
| 5 | Health checks | `/health` stays green while DynamoDB is unreachable, so traffic keeps going to tasks that cannot serve | Errors look "healthy" to the ALB | `/ready` now reports 503 when DynamoDB is unreachable | Liveness (`/health`) and readiness (`/ready`) are now separate. Keep the ECS container check on `/health` so a database outage does not cause a restart storm. Point the ALB target group at `/ready`; the ALB fails open when every target is unhealthy | `tests/test_observability.py` |
| 6 | Status page | Shares fate with its own database: during a DynamoDB outage the incident about the outage cannot be posted | Status page cannot announce the incident | Triage agent logs failed publishes | Triage agent keeps the note and retries publishing every 30 s | `triage/tests/test_agent.py`. **Open:** a static fallback page (S3) for full outages |
| 7 | Deploys | Code regression ships | 5xx or latency spike | Fast-burn pages within minutes | CI gate: unit tests, `promtool test rules` and a k6 smoke test against the SLOs on every PR. **Open:** enable the ECS deployment circuit breaker with automatic rollback | `.github/workflows/reliability.yml` |
| 8 | Data growth | `/status` and `/incidents` scan the whole table, so latency grows with incident count | Slowly rising latency | `LatencyBudgetBurnSlow` (ticket) | **Open:** add a GSI on `status` and query instead of scan; paginate `/incidents` | `loadtest/stress.js` shows where it breaks |
| 9 | Capacity (AWS) | `desired_count = 1` in `terraform/modules/ecs`: one task crash is a full outage | Outage until ECS starts a new task (about 1 to 2 min) | `AllReplicasDown` (page) | **Open:** run 2 tasks across AZs (roughly doubles Fargate cost) | Local lab runs 2 replicas |
| 10 | Telemetry | OTel Collector or Jaeger down | None; traces are dropped, requests unaffected | Missing traces in Jaeger | Batch exporter drops spans rather than blocking requests | Accepted risk |
| 11 | Triage agent | Ollama (LLM) unavailable | Triage notes fall back to runbook-only text | `fallback_used: true` in each triage result | Rule-based fallback built from the retrieved runbook | `triage/tests/test_agent.py` |
| 12 | Triage agent | LLM suggests a destructive or invented action | Wrong guidance during an incident | Guardrail rejects the draft (logged, traced in LangFuse) | Guardrails: no destructive commands, must cite a retrieved runbook, severity must be valid; one retry, then fallback | `triage/tests/test_guardrails.py`, `evals/promptfooconfig.yaml` |
| 13 | App thread pool | DynamoDB hangs, blocked requests fill the request thread pool, and synchronous `/health` and `/metrics` stop answering | The ALB would mark healthy tasks dead and ECS would restart them in a loop; Prometheus could not scrape, so the SLO error ratio read 0% while every request failed and only a misleading `ReplicaDown` fired | Found by the brownout experiment | `/health` and `/metrics` are async handlers on the event loop, independent of the request thread pool | `chaos/dynamodb-brownout.json`, `tests/test_observability.py` |

## How to use this

- Before a risky change, check which rows it touches.
- After an incident, add or update a row in the postmortem.
- Each **open** item is a backlog ticket, prioritized by the error budget policy in `docs/slo.md`.
