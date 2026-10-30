# Runbook: roll back a bad deploy

Alerts: any burn alert that starts within minutes of a release

## Symptoms
- Error rate or latency jumps right after the GitHub Actions deploy job finishes.
- New errors in the logs that did not exist before the release.

## Likely causes
- A code change raises an exception on a common path.
- A new dependency or configuration value is missing in the deployed environment.

## First steps
1. Confirm the timing: compare the alert start time with the last successful run of the deploy workflow in GitHub Actions.
2. Roll back by redeploying the previous image: revert the commit on `main` and let the pipeline redeploy, or point the ECS service at the previous task definition revision with `aws ecs update-service --cluster incident-pulse-cluster --service incident-pulse-service --task-definition <previous-revision>`.
3. Watch the burn rate in Grafana return below 1x.
4. Open a ticket with the failing commit and add a test that would have caught it.

## Escalation
- If rollback does not restore the SLO, treat it as a new incident and follow `slo-availability-burn.md`.

## Related alerts
`IncidentPulseReplicaDown` if the new image fails to start at all.
