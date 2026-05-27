# Demo Payment API 💳

A simulated payment microservice with **real Sentry error monitoring**. Built to demonstrate the [DevOps Incident Investigator](https://github.com/khadirullah/devops-incident-investigator) with live production errors.

## What This Does

This is a small Flask app that simulates a real payment microservice:

- ✅ **Healthy endpoints** — `/api/health`, `/api/payments` always work fine
- 🔴 **Error triggers** — Click buttons or hit endpoints to generate **real errors in Sentry**
- 📊 **Sentry integration** — Every triggered error is captured with full stack traces, tags, and context
- 🌐 **Web UI** — Beautiful dark-themed dashboard with buttons to trigger each error

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/khadirullah/demo-payment-api.git
cd demo-payment-api
pip install -r requirements.txt
```

### 2. Configure Sentry

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and paste your Sentry DSN
# Get your DSN from: Sentry → Project Settings → Client Keys (DSN)
nano .env
```

Your `.env` file should look like:
```
SENTRY_DSN=https://your-key@your-org.ingest.sentry.io/your-project-id
```

### 3. Run

```bash
python3 app.py
```

Open **http://localhost:5001** in your browser.

> **Note:** The app auto-loads the `.env` file — no need to `source .env` or `export` anything.

## Endpoints

### Healthy (Always Work)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Web UI with trigger buttons |
| `GET` | `/api/health` | Health check — returns `{"status": "healthy"}` |
| `GET` | `/api/payments` | Mock payments list — 5 sample payments |

### Error Triggers (Send Real Errors to Sentry)

| Endpoint | Error Type | Severity | What It Simulates |
|----------|-----------|----------|-------------------|
| `/trigger/db-connection` | `ConnectionError` | 🔴 Critical | PostgreSQL max connections reached |
| `/trigger/timeout` | `TimeoutError` | 🟠 High | Payment API request timeout (30s) |
| `/trigger/oom` | `MemoryError` | 🔴 Critical | OOM kill — worker exceeded 2GB limit |
| `/trigger/redis` | `ConnectionError` | 🔴 Critical | Redis cluster node unreachable |
| `/trigger/config` | `ValueError` | 🟡 Medium | Missing env var `DB_HOST` in config |
| `/trigger/disk` | `OSError` | 🟠 High | Disk space at 95% capacity |
| `/trigger/ssl` | `ConnectionError` | 🔴 Critical | SSL certificate expired |
| `/trigger/k8s-crash` | `RuntimeError` | 🔴 Critical | K8s pod CrashLoopBackOff |
| `/trigger/all` | All above | Mixed | Fires all 8 errors at once |

## How It Works

```
You click a trigger button
        ↓
Flask endpoint raises the error
        ↓
sentry_sdk.capture_exception() sends it to Sentry
        ↓
Error appears in Sentry dashboard with:
  - Full stack trace
  - Service tags (payment-api, cache-layer, etc.)
  - Host info (web-server-01, k8s-node-02, etc.)
  - Severity level (critical, high, medium)
  - Extra context (connection counts, memory usage, etc.)
        ↓
DevOps Incident Investigator detects it via Coral SQL
        ↓
AI analyzes root cause and suggests fixes
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SENTRY_DSN` | Yes | Your Sentry project DSN for error capture |

## Used With

This app is designed to work with the **DevOps Incident Investigator**:

```bash
# Run this demo app (port 5001)
python3 app.py

# In another terminal, run the Investigator pointing at this repo
python3 investigator.py --query correlation \
  --owner khadirullah --repo demo-payment-api \
  --sentry-project YOUR_SENTRY_PROJECT_ID
```

The Investigator will correlate:
- **GitHub PRs** merged in this repo → with
- **Sentry errors** triggered by this app → plus
- **Slack messages** from your `#incidents` channel

## Built For

[Pirates of the Coral-bean hackathon](https://wemakedevs.org/hackathons/coral) 🏴‍☠️ — Powered by [Coral SQL](https://withcoral.com)
