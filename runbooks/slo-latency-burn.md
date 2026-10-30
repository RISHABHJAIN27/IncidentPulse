# Runbook: latency error budget burn

Alerts: `IncidentPulseLatencyBudgetBurnFast` (page), `IncidentPulseLatencyBudgetBurnSlow` (ticket)

## Symptoms
- More than 5% of requests take longer than 300 ms. p95 latency in Grafana is above the 300 ms threshold line.

## Likely causes
- DynamoDB responding slowly: each call can wait up to the 5 second read timeout and retry (`dynamodb-errors.md`).
- Table scans growing: `/status` and `/incidents` scan the whole table, so latency rises as incidents accumulate. This shows as a slow burn rather than a sudden spike.
- Too few replicas for the traffic level; CPU-bound replicas queue requests.

## First steps
1. In Grafana, check "Latency percentiles" and "Requests per second by route" to find which route is slow and whether traffic rose.
2. Open slow traces in Jaeger (service `incident-pulse`, min duration 300ms) and compare time in the DynamoDB span with time in the app.
3. If DynamoDB spans dominate, follow `dynamodb-errors.md`.
4. If traffic rose, add capacity: increase the ECS service desired count, or start more replicas locally.
5. If scans are the cause, count items with `aws dynamodb describe-table --table-name incidents` and plan the GSI change in `docs/failure-mode-analysis.md`.

## Escalation
- Page the on-call engineer if p95 stays above 1 second for 15 minutes.

## Related alerts
`IncidentPulseAvailabilityBudgetBurnFast` when slow requests start timing out.
