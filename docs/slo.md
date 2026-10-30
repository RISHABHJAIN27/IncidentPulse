# Incident Pulse SLOs

Incident Pulse is a status page API: when something else is down, people come here to find out. So it has to be up and fast during other teams' worst moments. These SLOs define "good enough" and tell us when reliability work must take priority over features.

## Service level indicators

Both SLIs are measured at the app from `http_requests_total` and `http_request_duration_seconds` (see `app/observability.py`). Health and readiness probes (`/health`, `/ready`) are excluded because they are not user traffic.

| SLI | Good event | Valid event |
|---|---|---|
| Availability | Response is not a 5xx | Any request except probes |
| Latency | Response completes in under 300 ms | Any request except probes |

4xx responses count as good for availability: a 404 for an unknown incident ID is the API working correctly.

## Objectives

Window: rolling 30 days.

| SLO | Target | Error budget | Budget in requests (at 1M requests / 30 days) |
|---|---|---|---|
| Availability | 99.5% | 0.5% | 5,000 failed requests |
| Latency | 95% under 300 ms | 5% | 50,000 slow requests |

## Alerting: multi-window, multi-burn-rate

Burn rate is how fast the budget is being spent: 1x spends exactly the 30-day budget in 30 days, 14.4x spends it in about 2 days. Each alert needs both a long and a short window to be over threshold. The long window proves the problem is significant, and the short window proves it is still happening, so alerts clear soon after recovery. The thresholds follow the Google SRE Workbook.

| Alert | Burn rate | Long / short window | Budget spent before firing | Severity |
|---|---|---|---|---|
| `*BudgetBurnFast` | 14.4x | 1h / 5m | 2% | page |
| `*BudgetBurnFast` | 6x | 6h / 30m | 5% | page |
| `*BudgetBurnSlow` | 3x | 1d / 2h | 10% | ticket |
| `*BudgetBurnSlow` | 1x | 3d / 6h | 10% | ticket |

Also: `IncidentPulseReplicaDown` (ticket) and `IncidentPulseAllReplicasDown` (page). Alertmanager inhibits a ticket while a page for the same SLO is firing.

Rules: `observability/prometheus/rules/slo.yml`. Unit tests: `observability/prometheus/tests/slo.test.yml`, run with `promtool test rules` in CI on every pull request.

## Error budget policy

| Budget left (30 days) | What happens |
|---|---|
| More than 50% | Ship normally. Use spare budget for chaos experiments and risky migrations. |
| 25 to 50% | Every deploy needs a rollback plan. Review the top error sources weekly. |
| Under 25% | Feature releases pause. Reliability fixes from postmortems come first. |
| Exhausted | Only fixes and security patches ship until the 30-day SLI is back above target. |

## Where to see it

Grafana dashboard **Incident Pulse - SLOs** (`observability/grafana/dashboards/incident-pulse-slo.json`): SLI vs target, budget remaining, burn rate, latency percentiles, firing alerts.
