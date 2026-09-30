import os
import time

from prometheus_client import start_http_server
from prometheus_client.core import REGISTRY

from pve_exporter.client import PveClient
from pve_exporter.collectors.guests import GuestCollector


def main() -> None:
    client = PveClient(
        host=os.getenv("PVE_HOST"),
        token_id=os.getenv("PVE_TOKEN_ID"),
        token_secret=os.getenv("PVE_TOKEN_SECRET"),
        verify_ssl=os.getenv("PVE_VERIFY_SSL", "true").lower() == "true",
    )
    REGISTRY.register(GuestCollector(client))

    port = int(os.getenv("EXPORTER_PORT", "9800"))
    start_http_server(port)
    print(f"Serving metrics on http://localhost:{port}/metrics")
    while True:
        time.sleep(60)