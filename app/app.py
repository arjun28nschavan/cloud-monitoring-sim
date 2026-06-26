import time
import random
import logging
from flask import Flask, jsonify, request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# --- Logging setup (Promtail will pick these up from stdout) ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s level=%(levelname)s msg="%(message)s"'
)
log = logging.getLogger("app")

# --- Prometheus metrics ---
REQUEST_COUNT = Counter(
    "app_requests_total", "Total HTTP requests", ["endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "app_request_latency_seconds", "Request latency in seconds", ["endpoint"]
)

# Toggle this via /chaos/* endpoints to simulate problems on demand
STATE = {"slow": False, "error_rate": 0.0}


@app.route("/")
def home():
    start = time.time()
    log.info("Handled request to /")
    REQUEST_COUNT.labels(endpoint="/", status="200").inc()
    REQUEST_LATENCY.labels(endpoint="/").observe(time.time() - start)
    return jsonify({"message": "Cloud monitoring sim app is running"})


@app.route("/work")
def work():
    """Simulated endpoint that does 'real' work - latency varies, can fail."""
    start = time.time()
    endpoint = "/work"

    # Simulated slow downstream call (e.g. DB query)
    base_delay = random.uniform(0.05, 0.2)
    if STATE["slow"]:
        base_delay += random.uniform(1.0, 3.0)
    time.sleep(base_delay)

    # Simulated random failure
    if random.random() < STATE["error_rate"]:
        log.error(f"Failed to process /work request, delay={base_delay:.2f}s")
        REQUEST_COUNT.labels(endpoint=endpoint, status="500").inc()
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(time.time() - start)
        return jsonify({"error": "internal server error"}), 500

    log.info(f"Processed /work request in {base_delay:.2f}s")
    REQUEST_COUNT.labels(endpoint=endpoint, status="200").inc()
    REQUEST_LATENCY.labels(endpoint=endpoint).observe(time.time() - start)
    return jsonify({"status": "ok", "delay": round(base_delay, 2)})


@app.route("/health")
def health():
    return jsonify({"status": "healthy"})


@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


# --- Chaos endpoints: use these to simulate incidents for your CV demo ---
@app.route("/chaos/slow/<state>")
def chaos_slow(state):
    STATE["slow"] = state.lower() == "on"
    log.warning(f"Chaos: slow mode set to {STATE['slow']}")
    return jsonify({"slow": STATE["slow"]})


@app.route("/chaos/errors/<float:rate>")
def chaos_errors(rate):
    STATE["error_rate"] = max(0.0, min(1.0, rate))
    log.warning(f"Chaos: error_rate set to {STATE['error_rate']}")
    return jsonify({"error_rate": STATE["error_rate"]})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
