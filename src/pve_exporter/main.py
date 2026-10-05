import os
import time
import logging
import sys

from prometheus_client import start_http_server
from prometheus_client.core import REGISTRY

from pve_exporter.client import PveClient
from pve_exporter.collectors.resources import ResourceCollector

log = logging.getLogger("pve_exporter")

def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    log.info("Starting PVE exporter")
    required = ["PVE_HOST", "PVE_TOKEN_ID", "PVE_TOKEN_SECRET"]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        log.error(f"Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)

    raw_ssl = os.getenv("PVE_VERIFY_SSL", "true").strip().lower()
    if raw_ssl not in ("true", "false"):
        log.error("PVE_VERIFY_SSL environment variable must be 'true' or 'false', got %s", raw_ssl)
        sys.exit(1)
        
    try:
        port_string = os.getenv("EXPORTER_PORT", "9800")
        port = int(port_string)
        if port <= 0 or port > 65535:
            log.error("Port number must be between 1 and 65535, got %s", port)
            sys.exit(1)
    except ValueError:
        log.error("Invalid port number specified in EXPORTER_PORT, got %s", port_string)
        sys.exit(1)

    client = PveClient(
        host=os.getenv("PVE_HOST"),
        token_id=os.getenv("PVE_TOKEN_ID"),
        token_secret=os.getenv("PVE_TOKEN_SECRET"),
        verify_ssl = raw_ssl == "true"
    ) 
    
    REGISTRY.register(ResourceCollector(client))
    start_http_server(port)
    log.info(f"Serving metrics on http://localhost:{port}/metrics")
    while True:
        time.sleep(60)