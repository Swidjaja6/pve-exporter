import httpx

# Start connection to Proxmox API

class PveClient:
    def __init__(self, host: str, token_id: str, token_secret: str, verify_ssl: bool = True):
        self._http = httpx.Client(
            base_url=f"https://{host}:8006/api2/json",
            headers={"Authorization": f"PVEAPIToken={token_id}={token_secret}"},
            verify=verify_ssl,
            timeout=10.0,
        )

    # Each API call is wrapped with [data], it's extracted here first
    def _get(self, path: str, **params) -> list[dict]: 
        resp = self._http.get(path, params=params)
        resp.raise_for_status()
        return resp.json()["data"]
    
    # Gets all resources in the cluster
    def resources(self) -> list[dict]:
            return self._get("/cluster/resources")
    