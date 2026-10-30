# Runbook: app replica down

Alerts: `IncidentPulseReplicaDown` (ticket), `IncidentPulseAllReplicasDown` (page)

## Symptoms
- Prometheus cannot scrape one replica (`up == 0`). With one replica down, users are served by the others with less headroom.
- With all replicas down, the API is fully unavailable and the load balancer returns 502.

## Likely causes
- The container crashed: an unhandled startup error, or out of memory.
- A deploy shipped an image that does not start (bad config, missing dependency).
- The host or Fargate task was stopped or replaced.

## First steps
1. Check container state: `docker compose ps` locally, or `aws ecs describe-services --cluster incident-pulse-cluster --services incident-pulse-service` on AWS (look at runningCount and recent events).
2. Read the last logs of the stopped replica: `docker compose logs --tail 100 app-1`, or the stopped task's reason in the ECS console.
3. If it was an out-of-memory kill, raise the task memory and investigate the cause after recovery.
4. If a new image fails to start, roll back (`deploy-rollback.md`).
5. Restart a single failed replica: `docker compose up -d app-1` locally. On AWS the ECS service starts a replacement task automatically.

## Escalation
- `IncidentPulseAllReplicasDown` is a full outage: page immediately and post a status update.

## Related alerts
Availability burn alerts if the remaining replicas cannot absorb the traffic.
