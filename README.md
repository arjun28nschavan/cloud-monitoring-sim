# Cloud Infrastructure Monitoring and Deployment Simulation

A self-contained, Docker-based simulation of a production environment: an app deployment with
full observability (metrics + logs), synthetic load generation, intentional fault injection, and
a basic Python-based anomaly detection script.

## Architecture

```
load generator -> app -> (node-exporter, promtail) -> (prometheus, loki) -> grafana
                                                                          -> exported CSV -> anomaly detection script
```

- **app** — Flask API exposing `/work` (simulated business logic), `/metrics` (Prometheus format),
  and `/chaos/*` endpoints to deliberately inject latency or errors.
- **prometheus** — scrapes metrics from the app and node-exporter every 5s.
- **node-exporter** — host-level metrics (CPU, memory, disk).
- **loki + promtail** — log aggregation; promtail tails container logs and ships them to Loki.
- **grafana** — dashboards over both Prometheus and Loki, auto-provisioned on startup.

## Prerequisites

- Docker and Docker Compose installed
- Ports 3000, 3100, 5000, 9090, 9100 free on your machine

## Setup

```bash
git clone <your-repo-url>
cd cloud-monitoring-sim
docker compose up -d --build
```

Check everything is running:

```bash
docker compose ps
```

## Accessing the stack

| Service     | URL                              | Notes                         |
|-------------|-----------------------------------|--------------------------------|
| App         | http://localhost:5000             | `/`, `/work`, `/health`        |
| Prometheus  | http://localhost:9090             | Query metrics, check targets   |
| Grafana     | http://localhost:3000             | login: `admin` / `admin`       |
| Loki        | http://localhost:3100/ready       | API only, view via Grafana     |

The "App overview" dashboard in Grafana is pre-loaded with request rate, error rate, p95 latency,
host CPU, and a live log panel.

## Generating traffic

```bash
# simple load loop
while true; do curl -s http://localhost:5000/work > /dev/null; sleep 0.2; done
```

Or use a proper load tool like `locust` or `hey` for higher, more realistic volume.

## Simulated incident scenarios

These are the kinds of scenarios worth writing up in your CV/portfolio as "troubleshooting"
evidence — each one is reproducible on demand using the chaos endpoints.

**1. Latency spike**
```bash
curl http://localhost:5000/chaos/slow/on
```
Watch the p95 latency panel in Grafana climb. Revert with `chaos/slow/off`.

**2. Elevated error rate**
```bash
curl http://localhost:5000/chaos/errors/0.3
```
30% of `/work` requests now return 500. Watch the error rate panel and cross-reference with the
log panel to see the corresponding `ERROR` log lines. Revert with `chaos/errors/0.0`.

**3. Container crash / recovery**
```bash
docker kill app
```
Because `app` has `restart: unless-stopped`, Compose restarts it automatically. Observe the gap
in the request rate graph and confirm recovery time from the metrics.

**4. Resource exhaustion**
```bash
docker run --rm -it polinux/stress stress --cpu 4 --timeout 60s
```
Observe host CPU usage spike in the "Host CPU usage" panel.

For each scenario, document: what you saw in the dashboard, what you saw in the logs, and what
the fix/mitigation would be in a real environment. This writeup is the actual deliverable for
your CV — the dashboards are just the evidence.

## Basic anomaly detection

Export a Prometheus range query to CSV and run a simple z-score/rolling-average detector over it
(see `analysis/anomaly_detection.py` if you've added one) to flag periods where latency or error
rate deviated significantly from baseline — this satisfies the "explored anomaly detection
concepts" part of the project without needing a full ML pipeline.

## Tearing down

```bash
docker compose down -v
```

## Skills demonstrated

- Docker & Docker Compose multi-service orchestration
- Prometheus metrics instrumentation (custom app metrics via `prometheus_client`)
- Grafana dashboard design and provisioning-as-code
- Log aggregation with Loki/Promtail
- Fault injection and incident troubleshooting
- Basic statistical anomaly detection in Python

## Screenshots

### Normal traffic
![Normal traffic](screenshots\normal_traffic.png)

### Latency spike (chaos/slow/on)
![Latency spike](screenshots\latency_spike.png)

### Error rate spike (chaos/errors/0.3)
![Error rate](screenshots\error-rate.png)

### Container crash and recovery
![Crash recovery](screenshots\crash-recovery.png)