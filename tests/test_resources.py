import httpx
from prometheus_client import CollectorRegistry, generate_latest

from pve_exporter.client import PveClient
from pve_exporter.collectors.resources import ResourceCollector

def make_client(handler):
    client = PveClient(host="pve.test", token_id="test@pve!t", token_secret="x")
    client._http._transport = httpx.MockTransport(handler)
    return client

def scrape(client):
    collector_registry = CollectorRegistry()
    collector = ResourceCollector(client)
    collector_registry.register(collector)
    return generate_latest(collector_registry).decode("utf-8")

# Happy path
def test_happy_path(caplog):
    data = {"id": "qemu/100", "type": "qemu", "node": "pve", "status": "running"}
    client = make_client(lambda request: httpx.Response(200, json={"data": [data]}))
    output = scrape(client)
    assert "pve_exporter_scrape_success 1.0" in output
    assert "pve_up{id=\"qemu/100\"}" in output
    assert output.count("pve_up{") == 1

# Failure cases for the resource collector
def test_401_reports_scrape_failure(caplog):
    client = make_client(lambda request: httpx.Response(401))
    output = scrape(client)
    assert "pve_exporter_scrape_success 0.0" in output
    assert "401" in caplog.text

def test_500_reports_scrape_failure(caplog):
    client = make_client(lambda request: httpx.Response(500))
    output = scrape(client)
    assert "pve_exporter_scrape_success 0.0" in output
    assert "500" in caplog.text

def test_timeout_failure(caplog):
    def handler(request):
        raise httpx.ReadTimeout("Timed out", request=request)
    client = make_client(handler)
    output = scrape(client)
    assert "pve_exporter_scrape_success 0.0" in output
    assert "ReadTimeout occurred" in caplog.text

def test_connection_error_failure(caplog):
    def handler(request):
        raise httpx.ConnectError("Connection error", request=request)
    client = make_client(handler)
    output = scrape(client)
    assert "pve_exporter_scrape_success 0.0" in output
    assert "Connect error occurred" in caplog.text

def test_html_body_failure(caplog):
    client = make_client(lambda request: httpx.Response(200, content="<html></html>"))
    output = scrape(client)
    assert "pve_exporter_scrape_success 0.0" in output
    assert "Proxmox request failed: JSONDecode error" in caplog.text

def test_data_key_error(caplog):
    client = make_client(lambda request: httpx.Response(200, json={"errors": "x"}))
    output = scrape(client)
    assert "pve_exporter_scrape_success 0.0" in output
    assert "Proxmox request failed: Key error ('data')" in caplog.text

def test_data_null_error(caplog):
    client = make_client(lambda request: httpx.Response(200, json={"data": None}))
    output = scrape(client)
    assert "pve_exporter_scrape_success 0.0" in output
    assert "Proxmox request failed: Value error (Expected a list of resources)" in caplog.text

def test_data_dict_error(caplog):
    client = make_client(lambda request: httpx.Response(200, json={"data": {"a": 1}}))
    output = scrape(client)
    assert "pve_exporter_scrape_success 0.0" in output
    assert "Proxmox request failed: Value error (Expected a list of resources)" in caplog.text

def test_skip_missing_id(caplog):
    data = {"id": "qemu/100", "type": "qemu", "node": "pve", "status": "running"}
    bad_data = {"type": "qemu", "node": "pve", "status": "running"}
    client = make_client(lambda request: httpx.Response(200, json={"data": [data, bad_data]}))
    output = scrape(client)
    assert "pve_exporter_scrape_success 1.0" in output
    assert "pve_up{id=\"qemu/100\"}" in output
    assert output.count("pve_up{") == 1

def test_skip_empty_id(caplog):
    data = {"id": "qemu/100", "type": "qemu", "node": "pve", "status": "running"}
    bad_data = {"id": "", "type": "qemu", "node": "pve", "status": "running"}
    client = make_client(lambda request: httpx.Response(200, json={"data": [data, bad_data]}))
    output = scrape(client)
    assert "pve_exporter_scrape_success 1.0" in output
    assert "pve_up{id=\"qemu/100\"}" in output
    assert output.count("pve_up{") == 1

def test_skip_missing_type(caplog):
    data = {"id": "qemu/100", "type": "qemu", "node": "pve", "status": "running"}
    bad_data = {"id": "qemu/101", "node": "pve", "status": "running"}
    client = make_client(lambda request: httpx.Response(200, json={"data": [data, bad_data]}))
    output = scrape(client)
    assert "pve_exporter_scrape_success 1.0" in output
    assert "pve_up{id=\"qemu/100\"}" in output
    assert output.count("pve_up{") == 1

def test_skip_missing_node(caplog):
    data = {"id": "qemu/100", "type": "qemu", "node": "pve", "status": "running"}
    bad_data = {"id": "qemu/101", "type": "qemu", "status": "running"}
    client = make_client(lambda request: httpx.Response(200, json={"data": [data, bad_data]}))
    output = scrape(client)
    assert "pve_exporter_scrape_success 1.0" in output
    assert "pve_up{id=\"qemu/100\"}" in output
    assert output.count("pve_up{") == 1

def test_skip_non_dict_entry(caplog):
    data = {"id": "qemu/100", "type": "qemu", "node": "pve", "status": "running"}
    bad_data = ["test"]
    client = make_client(lambda request: httpx.Response(200, json={"data": [data, bad_data]}))
    output = scrape(client)
    assert "pve_exporter_scrape_success 1.0" in output
    assert "pve_up{id=\"qemu/100\"}" in output
    assert output.count("pve_up{") == 1