# Demo Payment API 💳

A simulated payment microservice with **real Sentry error monitoring**. Built to demonstrate the [DevOps Incident Investigator](https://github.com/khadirullah/devops-incident-investigator) with live production errors.

## What This Does

- ✅ **Healthy endpoints** — `/api/health`, `/api/payments` always work
- 🔴 **Error triggers** — Click buttons or hit endpoints to generate real Sentry errors
- 📊 **Sentry integration** — Every triggered error is captured with full stack traces, tags, and context

## Quick Start

```bash
# Set your Sentry DSN
export SENTRY_DSN=https://your-key@your-org.ingest.sentry.io/project-id

# Install dependencies
pip install -r requirements.txt

# Run
python3 app.py
# Open http://localhost:5001
```

## Error Triggers

| Endpoint | Error | Severity |
|----------|-------|----------|
| `/trigger/db-connection` | PostgreSQL max connections | Critical |
| `/trigger/timeout` | API request timeout 30s | High |
| `/trigger/oom` | OOM kill 2GB limit | Critical |
| `/trigger/redis` | Redis node unreachable | Critical |
| `/trigger/config` | Missing env var | Medium |
| `/trigger/disk` | Disk at 95% capacity | High |
| `/trigger/ssl` | SSL certificate expired | Critical |
| `/trigger/k8s-crash` | K8s CrashLoopBackOff | Critical |
| `/trigger/all` | All 8 errors at once | Mixed |

## Built For

[Pirates of the Coral-bean hackathon](https://wemakedevs.org/hackathons/coral) 🏴‍☠️
