# Runbook: availability error budget burn

Alerts: `IncidentPulseAvailabilityBudgetBurnFast` (page), `IncidentPulseAvailabilityBudgetBurnSlow` (ticket)

## Symptoms
- More than 0.5% of API requests return 5xx. A fast burn means over 7.2% for the last hour, which uses the 30-day budget in about two days.
- Grafana "Incident Pulse - SLOs": the error ratio is above the budget line and the burn rate is above 6x.

## Likely causes
- DynamoDB unreachable, slow or throttling: requests time out and return 500. This is the most common cause; see `dynamodb-errors.md`.
- A bad deploy introduced an exception in a handler; check whether errors started right after a release (`deploy-rollback.md`).
- One or more replicas crash-looping, so the remaining ones are overloaded (`replica-down.md`).

## First steps
1. Open Grafana "Incident Pulse - SLOs" and check "Responses by status code" and "Requests per second by route" to see which route is failing.
2. Check readiness: `curl http://localhost:8080/ready`. A 503 with `dynamodb_unreachable` points to the database.
3. Read recent app errors: `docker compose logs --since 15m app-1 app-2` locally, or `aws logs tail /ecs/incident-pulse --since 15m` on AWS.
4. Open a slow or failed request in Jaeger (service `incident-pulse`) and check whether the time is spent in the DynamoDB span.
5. If errors began with a deploy, roll back first and investigate after (`deploy-rollback.md`).

## Escalation
- Page the on-call engineer if the fast-burn alert has been firing for 15 minutes without a clear cause.
- Post a status update every 30 minutes while the budget is burning.

## Related alerts
`IncidentPulseLatencyBudgetBurnFast` often fires at the same time when DynamoDB is slow.
