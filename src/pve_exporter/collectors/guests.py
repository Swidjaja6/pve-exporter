import httpx
from prometheus_client.core import GaugeMetricFamily

LABELS = ["node", "vmid", "name", "type"]


class GuestCollector:
    def __init__(self, client):
        self.client = client

    def collect(self):
        success = GaugeMetricFamily(
            "pve_exporter_guests_scrape_success", "Prints 1 if the Proxmox API call succeeded"
        )
        try:
            guests = self.client.guests()
        except httpx.HTTPError:
            success.add_metric([], 0)
            yield success
            return

        up = GaugeMetricFamily("pve_guest_up", "1 if the guest is running", labels=LABELS)
        cpu = GaugeMetricFamily("pve_guest_cpu_usage_ratio", "CPU usage (0-1)", labels=LABELS)
        mem = GaugeMetricFamily("pve_guest_memory_used_bytes", "Memory in use", labels=LABELS)
        mem_max = GaugeMetricFamily("pve_guest_memory_max_bytes", "Memory allocated", labels=LABELS)

        for g in guests:
            labels = [g["node"], str(g["vmid"]), g.get("name", ""), g["type"]]
            up.add_metric(labels, 1.0 if g["status"] == "running" else 0.0)
            cpu.add_metric(labels, g.get("cpu", 0.0))
            mem.add_metric(labels, g.get("mem", 0))
            mem_max.add_metric(labels, g.get("maxmem", 0))

        success.add_metric([], 1)
        yield from (up, cpu, mem, mem_max, success)