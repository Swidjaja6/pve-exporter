import logging

import httpx
from prometheus_client.core import GaugeMetricFamily

LABELS = ["id"]

VALUE_METRICS = {
    # API field: (metric name, help text)
    "cpu":    ("pve_cpu_usage_ratio", "CPU usage (0-1)"),
    "maxcpu": ("pve_cpu_usage_limit", "Number of available CPUs"),
    "mem": ("pve_memory_usage_bytes", "Memory in use"),
    "maxmem": ("pve_memory_size_bytes", "Memory allocated"),
    "disk": ("pve_disk_usage_bytes", "Disk usage in bytes"),
    "maxdisk": ("pve_disk_size_bytes", "Disk size in bytes"),
    "netin": ("pve_network_receive_bytes", "Network receive in bytes"),
    "netout": ("pve_network_transmit_bytes", "Network transmit in bytes"),
    "diskread": ("pve_disk_read_bytes", "Disk read in bytes"),
    "diskwrite": ("pve_disk_write_bytes", "Disk write in bytes"),
}

UP_STATUS = {
    "qemu" : "running",
    "lxc" : "running",
    "node" : "online",
    "storage" : "available"
}

INFO_METRICS = {
    "pve_guest_info": ("pve_guest_info", "Information about the Proxmox guest", ["id", "node", "name", "type"]),
    "pve_node_info": ("pve_node_info", "Information about the Proxmox node", ["id", "name", "level"]),
    "pve_storage_info": ("pve_storage_info", "Information about the Proxmox storage", ["id", "node", "storage", "plugintype", "content"])
}

log = logging.getLogger("pve_exporter")

class ResourceCollector:
    def __init__(self, client):
        self.client = client

    def collect(self):
        success = GaugeMetricFamily(
            "pve_exporter_scrape_success", "Prints 1 if the Proxmox API call succeeded, else 0"
        )
        try:
            resources = self.client.resources()
        except httpx.HTTPStatusError as e:
            log.error("HTTP status error occurred: %s", e)
            success.add_metric([], 0)
            yield success
            return
        except httpx.ConnectError as e:
            log.error("Connection error occurred: %s", e)
            success.add_metric([], 0)
            yield success
            return
        except httpx.HTTPError as e:
            log.error("HTTP error occurred: %s", e)
            success.add_metric([], 0)
            yield success
            return

        families = {
            field: GaugeMetricFamily(name, help_text, labels=LABELS)
            for field, (name, help_text) in VALUE_METRICS.items()
        }

        families_2 = {
            field: GaugeMetricFamily(name, help_text, labels=labels)
            for field, (name, help_text, labels) in INFO_METRICS.items()
        }

        pve_up = GaugeMetricFamily("pve_up", "1 if the resource is up, 0 otherwise", labels=LABELS)

        for g in resources:
            if g["type"] not in UP_STATUS:
                continue
            labels = [g["id"]]
            pve_up.add_metric(labels, 1.0 if g["status"] == UP_STATUS.get(g["type"], "") else 0.0)
            for field, family in families.items():
                if field in g:
                    family.add_metric(labels, g[field])
            if g["type"] == "node":
                families_2["pve_node_info"].add_metric([g["id"], g["node"], g.get("level", "")], 1)
            elif g["type"] in ("qemu", "lxc"):
                families_2["pve_guest_info"].add_metric([g["id"], g["node"], g.get("name", ""), g["type"]], 1)
            elif g["type"] == "storage":
                families_2["pve_storage_info"].add_metric([g["id"], g["node"], g.get("storage", ""), g.get("plugintype", ""), g.get("content", "")], 1)
        success.add_metric([], 1)
        yield from (*families.values(), *families_2.values(), pve_up, success)