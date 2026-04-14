# Project: Incident Pulse — Real-Time Incident Status Page API

## Why This Project?

You've spent ~5 years managing incidents. Now you build the tool that powers one. **Incident Pulse** is a lightweight status page API where teams can log incidents, track their status, and view system health — deployed on AWS with full CI/CD, IaC, monitoring, and alerting. It's simple enough to build with basic Python, but touches every infrastructure skill that SRE/Cloud/Platform Engineering roles care about.

---

## What You'll Have When Done

- A working Python API running on AWS (publicly accessible)
- Infrastructure defined entirely in code (Terraform)
- Automated CI/CD pipeline (build → test → deploy)
- CloudWatch dashboards tracking health, errors, and latency
- An architecture diagram you can put on your resume and talk about in interviews

---

## Tech Stack

| Layer | Tool |
|-------|------|
| App | Python 3.12, FastAPI |
| Database | Amazon DynamoDB (serverless, no DB management overhead) |
| Containerization | Docker |
| Compute | AWS ECS Fargate (serverless containers) |
| Networking | Application Load Balancer, VPC, Security Groups |
| IaC | Terraform |
| CI/CD | GitHub Actions |
| Monitoring | Amazon CloudWatch |
| Registry | Amazon ECR (Elastic Container Registry) |
| Security | IAM roles, Secrets Manager |

---

## Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌────────────────────────────┐
│   GitHub     │────▶│GitHub Actions│────▶│  Amazon ECR                │
│   (Code)     │     │  (CI/CD)     │     │  (Container Image)         │
└─────────────┘     └──────────────┘     └────────────┬───────────────┘
                                                      │
                                                      ▼
┌─────────────┐     ┌──────────────┐     ┌────────────────────────────┐
│  End Users   │────▶│     ALB      │────▶│  ECS Fargate               │
│  (Browser/   │     │ (Load        │     │  (Running Docker Container)│
│   curl)      │     │  Balancer)   │     └────────────┬───────────────┘
└─────────────┘     └──────────────┘                   │
                                                       ▼
                                          ┌────────────────────────────┐
                                          │  DynamoDB                  │
                                          │  (Incident Records)        │
                                          └────────────────────────────┘

         CloudWatch ◀── Logs, Metrics, Alarms from all components
```

---

## Project Phases

### Phase 1 — Build the Python App (Local)

> **Goal:** A working API on your laptop that you can hit with curl or Postman.

- [ ] Set up project structure (`app/`, `tests/`, `requirements.txt`, `Dockerfile`)
- [ ] Initialize FastAPI app with health check endpoint (`GET /health`)
- [ ] Create incident data model (id, title, severity, status, created_at, updated_at)
- [ ] Build core API endpoints:
  - `POST /incidents` — create a new incident
  - `GET /incidents` — list all incidents (with optional status filter)
  - `GET /incidents/{id}` — get single incident details
  - `PATCH /incidents/{id}` — update incident status (investigating → identified → monitoring → resolved)
  - `GET /status` — system status summary (how many active incidents, overall health)
- [ ] Connect to DynamoDB using boto3 (use DynamoDB Local for development)
- [ ] Write unit tests using pytest (aim for core endpoint coverage)
- [ ] Test everything locally, confirm all endpoints work

**Deliverable:** A Python API that runs locally and passes all tests.

---

### Phase 2 — Containerize the App

> **Goal:** Your app runs inside a Docker container, identical to how it will run in production.

- [ ] Write a `Dockerfile` (Python base image, install deps, expose port, run with uvicorn)
- [ ] Create `.dockerignore` to exclude unnecessary files
- [ ] Build the Docker image locally and run it
- [ ] Verify all endpoints work inside the container
- [ ] Test that the container can connect to DynamoDB Local (via Docker networking)

**Deliverable:** A Docker image that runs your API identically to bare Python.

---

### Phase 3 — Design the AWS Architecture

> **Goal:** A clear architecture diagram and resource list before you write any Terraform.

- [ ] Define VPC layout:
  - 1 VPC
  - 2 public subnets (for ALB) across 2 AZs
  - 2 private subnets (for ECS tasks) across 2 AZs
  - NAT Gateway for outbound internet from private subnets
- [ ] Define security groups:
  - ALB SG: allow inbound 80/443 from internet
  - ECS SG: allow inbound from ALB SG only
- [ ] Define IAM:
  - ECS task execution role (pull from ECR, write to CloudWatch Logs)
  - ECS task role (read/write to DynamoDB)
- [ ] Define ECS service:
  - Fargate launch type
  - Desired count: 2 (for availability)
  - ALB target group with health check on `/health`
- [ ] Define DynamoDB table:
  - Table name: `incidents`
  - Partition key: `id` (String)
  - On-demand billing mode (no capacity planning needed)
- [ ] Draw final architecture diagram (use draw.io, Excalidraw, or Lucidchart)
- [ ] Document estimated monthly cost (Fargate, DynamoDB, ALB, NAT, CloudWatch)

**Deliverable:** Architecture diagram + resource specification document.

---

### Phase 4 — Build Infrastructure with Terraform

> **Goal:** Every AWS resource is created and destroyed via `terraform apply` and `terraform destroy`. No clicking in the console.

- [ ] Set up Terraform project structure:
  ```
  terraform/
  ├── main.tf
  ├── variables.tf
  ├── outputs.tf
  ├── provider.tf
  ├── modules/
  │   ├── networking/     (VPC, subnets, NAT, IGW)
  │   ├── ecs/            (cluster, service, task definition)
  │   ├── alb/            (load balancer, target group, listener)
  │   ├── dynamodb/       (table)
  │   ├── iam/            (roles, policies)
  │   ├── ecr/            (container registry)
  │   └── monitoring/     (CloudWatch dashboards, alarms)
  ```
- [ ] Configure S3 backend for Terraform state (with DynamoDB state locking)
- [ ] Write networking module (VPC, subnets, route tables, NAT, IGW)
- [ ] Write IAM module (task execution role, task role with DynamoDB access)
- [ ] Write ECR module (repository for Docker images)
- [ ] Write DynamoDB module (incidents table)
- [ ] Write ALB module (load balancer, target group, health check)
- [ ] Write ECS module (cluster, task definition, service, auto-scaling)
- [ ] Write monitoring module (placeholder — detailed in Phase 6)
- [ ] Run `terraform plan` — review every resource
- [ ] Run `terraform apply` — deploy full infrastructure
- [ ] Push Docker image to ECR manually (one-time, to validate)
- [ ] Verify app is accessible via ALB DNS name
- [ ] Test all endpoints against the live deployment
- [ ] Run `terraform destroy` and re-apply to confirm idempotency

**Deliverable:** Fully reproducible AWS infrastructure from code. One command to create, one to destroy.

---

### Phase 5 — Build CI/CD Pipeline (GitHub Actions)

> **Goal:** Push code to GitHub → tests run → image builds → deploys to AWS. No manual steps.

- [ ] Create GitHub repository for the project
- [ ] Set up GitHub Actions workflow file (`.github/workflows/deploy.yml`)
- [ ] **Stage 1 — Lint & Test:**
  - Run `flake8` or `ruff` for linting
  - Run `pytest` for unit tests
  - Fail the pipeline if any test fails
- [ ] **Stage 2 — Build & Push:**
  - Build Docker image
  - Tag with commit SHA (not `latest` — for traceability)
  - Authenticate to ECR
  - Push image to ECR
- [ ] **Stage 3 — Deploy:**
  - Update ECS task definition with new image tag
  - Force new deployment on ECS service
  - Wait for service stability (health check passes)
- [ ] **Stage 4 — Audit & Notify:**
  - Log deployment metadata (commit SHA, timestamp, deployer) to a deployment log
  - Send notification on success/failure (GitHub Actions summary or Slack webhook)
- [ ] Store AWS credentials as GitHub Secrets (never in code)
- [ ] Set up branch protection: require passing CI before merge to `main`
- [ ] Test full pipeline: push a code change → watch it flow through all stages → verify live

**Deliverable:** Fully automated pipeline. Every merge to main triggers build, test, and deploy.

---

### Phase 6 — Monitoring, Dashboards & Alerting (CloudWatch)

> **Goal:** A single CloudWatch dashboard that tells you if the app is healthy, and alarms that wake you up when it isn't.

- [ ] **Application Metrics:**
  - Add structured JSON logging to FastAPI (request method, path, status code, latency)
  - Create CloudWatch Log Group for ECS container logs
  - Create Metric Filters to extract:
    - Request count by status code (2xx, 4xx, 5xx)
    - Average response latency
    - Error rate (5xx / total requests)
- [ ] **Infrastructure Metrics (built-in):**
  - ECS: CPU utilization, memory utilization, running task count
  - ALB: request count, target response time, healthy host count, HTTP 5xx count
  - DynamoDB: consumed read/write capacity, throttled requests, latency
- [ ] **CloudWatch Dashboard:**
  - Create a single dashboard with widgets for:
    - API request volume (time series)
    - Error rate (time series)
    - Response latency P50 / P95 / P99 (time series)
    - ECS CPU & memory utilization (time series)
    - ALB healthy host count (number)
    - DynamoDB read/write latency (time series)
    - Active incidents count (custom metric from app)
- [ ] **CloudWatch Alarms:**
  - Error rate > 5% for 3 consecutive minutes → ALARM
  - Response latency P99 > 2 seconds for 5 minutes → ALARM
  - ECS running task count < 2 → ALARM (container crashed)
  - ALB healthy host count < 1 → ALARM (full outage)
  - DynamoDB throttled requests > 0 → WARNING
- [ ] **Alarm Actions:**
  - Create SNS topic for alerts
  - Subscribe your email to the SNS topic
  - Connect alarms to SNS for notifications
- [ ] Define all dashboard and alarm resources in Terraform (monitoring module from Phase 4)
- [ ] Deploy monitoring with `terraform apply`
- [ ] Trigger a test alarm (intentionally crash a container or send bad requests) to verify alerting

**Deliverable:** A live CloudWatch dashboard and working alerting pipeline, all defined in Terraform.

---

### Phase 7 — Documentation & Portfolio Packaging

> **Goal:** Make this project presentable to a hiring manager in under 2 minutes.

- [ ] Write a clear `README.md` for the GitHub repo:
  - Project overview (what it does, why it exists)
  - Architecture diagram (embed image)
  - Tech stack table
  - How to run locally
  - How to deploy (Terraform + GitHub Actions)
  - Monitoring screenshot
- [ ] Add the architecture diagram to your resume / portfolio
- [ ] Write a short blog post or LinkedIn article walking through the project (optional but high impact)
- [ ] Prepare a 3-minute verbal walkthrough for interviews:
  - "I built a status page API, containerized it, deployed it on ECS Fargate using Terraform, set up CI/CD with GitHub Actions, and built CloudWatch dashboards for observability."
- [ ] Clean up code: remove dead code, add docstrings to key functions, ensure consistent formatting

**Deliverable:** A portfolio-ready project with a polished README and interview talking points.

---

## Suggested Timeline

| Week | Phase | Focus |
|------|-------|-------|
| Week 1-2 | Phase 1 | Build the Python API locally |
| Week 2 (end) | Phase 2 | Containerize with Docker |
| Week 3 | Phase 3 | Design architecture (on paper / diagram tool) |
| Week 3-5 | Phase 4 | Write and deploy Terraform |
| Week 5-6 | Phase 5 | Build CI/CD pipeline |
| Week 6-7 | Phase 6 | Monitoring, dashboards, alerting |
| Week 7-8 | Phase 7 | Documentation and polish |

**Total estimated time: 6-8 weeks** (assuming ~3-4 hours/day of focused work)

---

## Skills You'll Be Able to Claim After This Project

| Skill | Evidence |
|-------|----------|
| Python (FastAPI) | Working API with tests |
| Docker | Containerized application |
| AWS (ECS, DynamoDB, ALB, VPC, IAM, ECR, CloudWatch) | Live deployment |
| Terraform | All infrastructure as code, modular |
| CI/CD (GitHub Actions) | Automated build → test → deploy |
| Observability | CloudWatch dashboards + alerting |
| Architecture Design | Documented architecture diagram |
| SRE Practices | Health checks, monitoring, alerting, incident data model |

---

## Cost Estimate (Keep It Cheap)

| Resource | Estimated Monthly Cost |
|----------|----------------------|
| ECS Fargate (2 small tasks) | ~$15-25 |
| ALB | ~$16 + data |
| NAT Gateway | ~$32 + data |
| DynamoDB (on-demand, low traffic) | ~$1-2 |
| ECR | < $1 |
| CloudWatch | ~$3-5 |
| S3 (Terraform state) | < $1 |
| **Total** | **~$70-80/month** |

> **Tip:** Run `terraform destroy` when you're not actively working on it. Spin it back up with `terraform apply` when you need it. This can cut costs to under $20/month during development.

---

## One Rule

**No clicking in the AWS Console to create resources.** If it exists in AWS, it exists in your Terraform. The only exception is the initial S3 bucket and DynamoDB table for Terraform state backend (bootstrap resources).

---
