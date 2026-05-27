#!/usr/bin/env python3
"""
Demo Payment API — A small Flask app with intentional error triggers.

This app simulates a payment microservice that:
- Runs perfectly fine on normal endpoints (health, payments list)
- Has "trigger" endpoints that generate REAL errors sent to Sentry
- Has a web UI with buttons to trigger each error type

Usage:
    source ../.env  # or set SENTRY_DSN env var
    pip install flask sentry-sdk
    python3 app.py
"""

import os
import sys
import time
import random
import sentry_sdk
from flask import Flask, jsonify, request, render_template

# ─── Sentry Setup ────────────────────────────────────────────────────────────

# Auto-load .env file if it exists (so you don't need to `source .env` manually)
_env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_env_file):
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())

DSN = os.environ.get("SENTRY_DSN", "")

if DSN:
    sentry_sdk.init(
        dsn=DSN,
        traces_sample_rate=1.0,
        environment="production",
        release="payment-api@1.2.0",
        send_default_pii=True,
    )
    print(f"✅ Sentry initialized: {DSN[:50]}...")
else:
    print("⚠️  SENTRY_DSN not set. Errors won't be sent to Sentry.")
    print("   Run: export SENTRY_DSN=https://your-key@sentry.io/project-id")

# ─── Flask App ───────────────────────────────────────────────────────────────

app = Flask(__name__)

# Simulated data
MOCK_PAYMENTS = [
    {"id": "PAY-001", "amount": 99.99, "currency": "USD", "status": "completed", "customer": "alice@example.com"},
    {"id": "PAY-002", "amount": 249.00, "currency": "USD", "status": "completed", "customer": "bob@example.com"},
    {"id": "PAY-003", "amount": 15.50, "currency": "EUR", "status": "pending", "customer": "carol@example.com"},
    {"id": "PAY-004", "amount": 1200.00, "currency": "USD", "status": "completed", "customer": "dave@example.com"},
    {"id": "PAY-005", "amount": 75.00, "currency": "GBP", "status": "refunded", "customer": "eve@example.com"},
]

# ─── Healthy Endpoints (Always Work) ────────────────────────────────────────

@app.route("/")
def index():
    """Serve the trigger UI."""
    return render_template("index.html")


@app.route("/api/health")
def health():
    """Health check — always returns OK."""
    return jsonify({"status": "healthy", "service": "payment-api", "version": "1.2.0", "uptime": "3d 14h 22m"})


@app.route("/api/payments")
def list_payments():
    """List mock payments — always works."""
    return jsonify({"data": MOCK_PAYMENTS, "total": len(MOCK_PAYMENTS)})


# ─── Error Trigger Endpoints ────────────────────────────────────────────────

def _send_error(err_class, message, tags, context=None):
    """Capture an error explicitly and send to Sentry, return JSON response."""
    with sentry_sdk.new_scope() as scope:
        for k, v in tags.items():
            scope.set_tag(k, v)
        if context:
            for ctx_name, ctx_data in context.items():
                scope.set_context(ctx_name, ctx_data)
        try:
            raise err_class(message)
        except Exception:
            event_id = sentry_sdk.capture_exception()
    sentry_sdk.flush(timeout=3)
    return jsonify({
        "error": err_class.__name__,
        "message": message,
        "event_id": str(event_id),
        "status": "error_sent_to_sentry",
        "note": "This error was captured by Sentry! Check your dashboard."
    }), 500


@app.route("/trigger/db-connection")
def trigger_db_error():
    """Simulate database connection failure."""
    return _send_error(
        ConnectionError,
        "Connection refused to postgres-primary:5432 — max connections reached (100/100)",
        {"service": "payment-api", "host": "web-server-01", "severity": "critical"},
        {"database": {"host": "postgres-primary:5432", "active_connections": 100, "max_connections": 100, "pool_exhausted": True}},
    )


@app.route("/trigger/timeout")
def trigger_timeout():
    """Simulate API request timeout."""
    return _send_error(
        TimeoutError,
        "Request timeout after 30000ms on /api/v2/payments/process",
        {"service": "payment-api", "host": "web-server-02", "severity": "high"},
        {"request": {"endpoint": "/api/v2/payments/process", "method": "POST", "timeout_ms": 30000}},
    )


@app.route("/trigger/oom")
def trigger_oom():
    """Simulate OOM kill."""
    return _send_error(
        MemoryError,
        "OOM killed: worker-3 exceeded 2GB memory limit during batch processing",
        {"service": "batch-processor", "host": "worker-03", "severity": "critical"},
        {"memory": {"limit_mb": 2048, "used_mb": 2150, "process": "batch-processor"}},
    )


@app.route("/trigger/redis")
def trigger_redis():
    """Simulate Redis cluster failure."""
    return _send_error(
        ConnectionError,
        "Redis cluster node redis-03:6379 unreachable — failover triggered",
        {"service": "cache-layer", "host": "web-server-01", "severity": "critical"},
        {"redis": {"node": "redis-03:6379", "cluster_size": 3, "healthy_nodes": 2}},
    )


@app.route("/trigger/config")
def trigger_config():
    """Simulate missing configuration."""
    return _send_error(
        ValueError,
        "Invalid configuration: missing required env var DB_HOST in deployment config",
        {"service": "config-loader", "host": "web-server-03", "severity": "medium"},
    )


@app.route("/trigger/disk")
def trigger_disk():
    """Simulate disk space critical."""
    return _send_error(
        OSError,
        "Disk space critical: /var/lib/docker at 95% capacity on build-server-01",
        {"service": "docker-daemon", "host": "build-server-01", "severity": "high"},
        {"disk": {"mount": "/var/lib/docker", "usage_percent": 95, "available_gb": 2.3}},
    )


@app.route("/trigger/ssl")
def trigger_ssl():
    """Simulate SSL certificate expiry."""
    return _send_error(
        ConnectionError,
        "SSL certificate expired for api.internal.company.com — all HTTPS requests failing",
        {"service": "api-gateway", "host": "gateway-01", "severity": "critical"},
    )


@app.route("/trigger/k8s-crash")
def trigger_k8s():
    """Simulate Kubernetes CrashLoopBackOff."""
    return _send_error(
        RuntimeError,
        "Kubernetes pod CrashLoopBackOff: payment-api-7d4f8b6c9-x2k4m restarted 5 times in 10 minutes",
        {"service": "payment-api", "host": "k8s-node-02", "severity": "critical"},
        {"kubernetes": {"pod": "payment-api-7d4f8b6c9-x2k4m", "restart_count": 5, "namespace": "production"}},
    )


@app.route("/trigger/all")
def trigger_all():
    """Fire all errors in sequence (doesn't crash — captures manually)."""
    errors_sent = []
    error_list = [
        (ConnectionError, "Connection refused to postgres-primary:5432 — max connections reached (100/100)",
         {"service": "payment-api", "severity": "critical"}),
        (TimeoutError, "Request timeout after 30000ms on /api/v2/payments/process",
         {"service": "payment-api", "severity": "high"}),
        (MemoryError, "OOM killed: worker-3 exceeded 2GB memory limit",
         {"service": "batch-processor", "severity": "critical"}),
        (ConnectionError, "Redis cluster node redis-03:6379 unreachable",
         {"service": "cache-layer", "severity": "critical"}),
        (ValueError, "Missing required env var DB_HOST in deployment config",
         {"service": "config-loader", "severity": "medium"}),
        (OSError, "Disk space critical: /var/lib/docker at 95%",
         {"service": "docker-daemon", "severity": "high"}),
        (ConnectionError, "SSL certificate expired for api.internal.company.com",
         {"service": "api-gateway", "severity": "critical"}),
        (RuntimeError, "Kubernetes pod CrashLoopBackOff: payment-api-7d4f8b6c9-x2k4m",
         {"service": "payment-api", "severity": "critical"}),
    ]

    for err_class, msg, tags in error_list:
        try:
            with sentry_sdk.new_scope() as scope:
                for k, v in tags.items():
                    scope.set_tag(k, v)
                try:
                    raise err_class(msg)
                except Exception:
                    event_id = sentry_sdk.capture_exception()
                    errors_sent.append({"error": err_class.__name__, "message": msg, "event_id": str(event_id)})
            time.sleep(0.3)
        except Exception as e:
            errors_sent.append({"error": err_class.__name__, "message": msg, "failed": str(e)})

    sentry_sdk.flush(timeout=5)
    return jsonify({
        "status": "all_errors_triggered",
        "count": len(errors_sent),
        "errors": errors_sent,
        "note": "Check Sentry dashboard in 1-2 minutes to see all errors"
    })


# ─── Error Handler (returns JSON instead of HTML error page) ────────────────

@app.errorhandler(Exception)
def handle_error(e):
    """Catch all errors, let Sentry capture them, return JSON."""
    sentry_sdk.flush(timeout=2)
    return jsonify({
        "error": type(e).__name__,
        "message": str(e),
        "status": "error_sent_to_sentry",
        "note": "This error was captured by Sentry! Check your dashboard."
    }), 500


# ─── HTML Template ──────────────────────────────────────────────────────────

# Templates are served via Flask's render_template from the templates/ directory


# ─── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║  💳  Demo Payment API — Error Trigger Service               ║
║                                                              ║
║  Dashboard:  http://localhost:5001                            ║
║  Health:     http://localhost:5001/api/health                 ║
║  Payments:   http://localhost:5001/api/payments               ║
║  Trigger UI: http://localhost:5001                            ║
║                                                              ║
║  Sentry: """ + ("✅ Connected" if DSN else "❌ Not configured") + """                                  ║
╚══════════════════════════════════════════════════════════════╝
""")
    app.run(host="0.0.0.0", port=5001, debug=False)
