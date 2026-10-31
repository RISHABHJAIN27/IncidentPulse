# Running Incident Pulse on Kubernetes

The Helm chart in `deploy/helm/incident-pulse` runs the API on any Kubernetes
cluster. CI deploys it to a 3-node [kind](https://kind.sigs.k8s.io/) cluster on
every pull request and deletes a pod during a k6 load test to prove the service
heals itself without breaking its SLOs.

## Quick start (local, free)

Needs Docker, [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation),
`kubectl` and [Helm](https://helm.sh/docs/intro/install/).

```bash
just kind-up      # 3-node cluster, build + load image, helm install, helm test
just kind-smoke   # k6 smoke test against http://localhost:8080
just kind-down
```

Without `just`:

```bash
kind create cluster --name incident-pulse --config deploy/kind/kind-config.yaml
docker build -t incident-pulse:local .
kind load docker-image incident-pulse:local --name incident-pulse
helm upgrade --install incident-pulse deploy/helm/incident-pulse \
  -f deploy/helm/incident-pulse/values-kind.yaml --wait
helm test incident-pulse --logs
```

API docs: http://localhost:8080/docs (NodePort 30080 is mapped to localhost:8080).

## Things to try

| Exercise | Command | What you should see |
|---|---|---|
| Self-healing | `kubectl delete pod -l app.kubernetes.io/name=incident-pulse --wait=false` while `just kind-smoke` runs | New pods replace the old ones; k6 SLO thresholds still pass |
| Readiness vs liveness | `kubectl scale deploy/incident-pulse-dynamodb --replicas=0` | App pods go **NotReady** (`/ready` fails) but are **not restarted** (`/health` still passes). Scale back to 1 and they return |
| Node drain + PDB | `kubectl drain incident-pulse-worker --ignore-daemonsets` | The PDB keeps at least 1 replica up while pods move |
| Zero-downtime rollout | `helm upgrade ... --set podAnnotations.rev=2` during a load test | `maxUnavailable: 0` + preStop sleep: no failed requests |
| Rollback | `helm history incident-pulse` then `helm rollback incident-pulse 1` | Previous revision restored |

## What the chart does, and why

| Setting | Why |
|---|---|
| Liveness `/health`, readiness `/ready` | A database outage takes pods out of the Service instead of restart-looping them (see failure-mode-analysis.md) |
| `maxUnavailable: 0`, `preStop` sleep 5 s | Rollouts and pod deletions do not drop in-flight requests |
| PodDisruptionBudget `minAvailable: 1` | Node drains and cluster upgrades cannot take every replica down |
| Topology spread across nodes | One node failure does not take the service down |
| HPA 2–6 replicas on CPU | Scales with load; 5-minute scale-down window to avoid flapping (off on kind: no metrics-server) |
| Non-root UID 10001, read-only root FS, all capabilities dropped, seccomp `RuntimeDefault` | Hardened pod; passes Trivy's Kubernetes checks with no HIGH/CRITICAL findings |
| No service account token mounted | The app never calls the Kubernetes API |
| `values-eks.yaml`: IRSA role annotation | On EKS the pod gets AWS credentials from an IAM role, so no static keys exist in the cluster |
| Config checksum annotation | Changing configuration rolls the pods automatically |

## Security scanning

`.github/workflows/security.yml` runs on every PR and weekly:

- **Gitleaks** scans the whole git history for secrets. Known false positives (a fake key in a guardrail test) are listed by fingerprint in `.gitleaksignore`.
- **Trivy config** fails on HIGH/CRITICAL misconfigurations in the Dockerfile and Helm chart.
- **Trivy image** reports HIGH/CRITICAL CVEs in the image and fails on fixable CRITICAL ones.

Run them locally with `just scan-secrets`, `just scan-config` and `just scan-image`.

`.gitlab-ci.yml` shows the same test → security → build → deploy pipeline on GitLab.
