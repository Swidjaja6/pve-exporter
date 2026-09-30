# metrics_basic.py

# Basic Prometheus metrics setup for Python
from prometheus_client import Counter, Gauge, Histogram, Summary
from prometheus_client import start_http_server, REGISTRY
import time

# Counter: tracks cumulative values that only increase
# Use for: request counts, error counts, processed items
requests_total = Counter(
    'app_requests_total',  # Metric name (must be unique)
    'Total number of requests processed',  # Help text
    ['method', 'endpoint', 'status']  # Label names for dimensions
)

# Gauge: tracks values that can go up or down
# Use for: queue sizes, active connections, temperature
active_connections = Gauge(
    'app_active_connections',
    'Number of currently active connections'
)

# Histogram: tracks distribution of values in buckets
# Use for: request latency, response sizes
request_latency = Histogram(
    'app_request_latency_seconds',
    'Request latency in seconds',
    ['endpoint'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Summary: tracks distribution with count and sum
# Use when: you need average duration or size, but not percentiles
request_duration = Summary(
    'app_request_duration_seconds',
    'Request duration in seconds',
    ['method']
)

def process_request(method: str, endpoint: str):
    """Simulate request processing with metrics"""
    # Track active connections
    active_connections.inc()  # Increment gauge

    start_time = time.time()

    try:
        # Simulate work
        time.sleep(0.1)

        # Increment counter with labels
        requests_total.labels(
            method=method,
            endpoint=endpoint,
            status='200'
        ).inc()

    except Exception as e:
        requests_total.labels(
            method=method,
            endpoint=endpoint,
            status='500'
        ).inc()
        raise

    finally:
        # Always decrement active connections
        active_connections.dec()

        # Record latency
        duration = time.time() - start_time
        request_latency.labels(endpoint=endpoint).observe(duration)
        request_duration.labels(method=method).observe(duration)

if __name__ == '__main__':
    # Start metrics server on port 8000
    start_http_server(8000)
    print("Metrics available at http://localhost:8000/metrics")

    # Keep running
    while True:
        process_request('GET', '/api/users')
        time.sleep(1)