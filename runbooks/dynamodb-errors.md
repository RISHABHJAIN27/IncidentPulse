# Runbook: DynamoDB errors, timeouts or throttling

Alerts: usually surfaces as `IncidentPulseAvailabilityBudgetBurnFast` or `IncidentPulseLatencyBudgetBurnFast`

## Symptoms
- `GET /ready` returns 503 with `dynamodb_unreachable` while `GET /health` still returns 200.
- App logs show botocore `ReadTimeoutError`, `EndpointConnectionError` or `ProvisionedThroughputExceededException`.
- Requests fail after about 15 seconds: 5 second read timeout, 3 attempts.

## Likely causes
- DynamoDB Local container stopped, paused or out of memory (local lab).
- Network path to DynamoDB broken: NAT gateway, VPC endpoint or security group change (AWS).
- Throttling during a traffic spike, or an AWS regional DynamoDB event.
- IAM change removed the task role's DynamoDB permissions (errors are `AccessDeniedException`, not timeouts).

## First steps
1. Confirm the database is the problem: `curl http://localhost:8080/ready`.
2. Local: `docker compose ps dynamodb-local`; if it is paused or stopped, `docker compose unpause dynamodb-local` or `docker compose up -d dynamodb-local`.
3. AWS: `aws dynamodb describe-table --table-name incidents` to confirm the table is ACTIVE, and check the AWS Health Dashboard for DynamoDB events.
4. Check the error type in the logs: throttling, access denied and timeouts each have different fixes.
5. Once DynamoDB answers again, confirm `/ready` returns 200 on every replica and the error ratio drops in Grafana.

## Escalation
- If AWS reports a regional DynamoDB event, post a status update and wait for AWS rather than changing infrastructure mid-incident.

## Related alerts
Availability and latency burn alerts fire together during a DynamoDB brownout.
