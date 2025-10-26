# modules/meraki/api.py
import os, time, json, yaml
from pathlib import Path
from typing import Any, Dict, Iterable, Optional
import requests

CONFIG_FILE = Path("data/meraki.yaml")
BASE_URL = "https://api.meraki.com/api/v1"

DEFAULT_CFG = {
    "api_key": "",
    "default_org_id": "",
    "default_org_name": "",
    "default_network_id": "",
    "default_network_name": "",
}

class MerakiConfig:
    def __init__(self):
        self.path = CONFIG_FILE
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._write(DEFAULT_CFG)
        self._cfg = yaml.safe_load(self.path.read_text()) or DEFAULT_CFG.copy()

    def _write(self, data: Dict[str, Any]):
        self.path.write_text(yaml.dump(data, sort_keys=False))

    def get(self, k, default=None):
        return self._cfg.get(k, default)

    def set(self, k, v):
        self._cfg[k] = v
        self._write(self._cfg)

    def as_dict(self): return dict(self._cfg)

CFG = MerakiConfig()

# --- Session (runtime) context for quick switching ---
class MerakiContext:
    """
    Ephemeral 'current selection' for this NetAssist session.
    Falls back to CFG defaults if not set.
    """
    def __init__(self):
        self._org_id = None
        self._org_name = None
        self._net_id = None
        self._net_name = None

    # Getters with fallback to defaults
    def org_id(self):
        return self._org_id or CFG.get("default_org_id")
    def org_name(self):
        return self._org_name or CFG.get("default_org_name")

    def net_id(self):
        """
        If an org override is active for this session, DO NOT fall back
        to the default network (which may belong to another org).
        Force the user to pick a network for the current org.
        """
        if self._org_id is not None:   # org is overridden in-session
            return self._net_id        # may be None → caller should prompt
        return self._net_id or CFG.get("default_network_id")

    def net_name(self):
        if self._org_id is not None:
            return self._net_name
        return self._net_name or CFG.get("default_network_name")

    # Handy flags for UIs/prompts
    def has_org_override(self): return self._org_id is not None
    def has_net_override(self): return self._net_id is not None

    # Setters
    def set_org(self, org_id, org_name=None, *, clear_net=True):
        self._org_id = org_id
        self._org_name = org_name
        if clear_net:
            self._net_id = None
            self._net_name = None

    def set_net(self, net_id, net_name=None):
        self._net_id = net_id
        self._net_name = net_name

    # Resets session to defaults (does not change defaults)
    def reset(self):
        self._org_id = self._org_name = self._net_id = self._net_name = None

CTX = MerakiContext()

def resolve_org(key: str):
    """Return (id, name) by id or case-insensitive name match."""
    key_l = key.strip().lower()
    for o in list_organizations():
        if key_l == str(o.get("id","")).lower() or key_l == str(o.get("name","")).lower():
            return o.get("id"), o.get("name")
    return None, None

def resolve_net(org_id: str, key: str):
    """Return (id, name) by id or case-insensitive name within org."""
    key_l = key.strip().lower()
    for n in list_networks(org_id):
        if key_l == str(n.get("id","")).lower() or key_l == str(n.get("name","")).lower():
            return n.get("id"), n.get("name")
    return None, None


def _auth_headers() -> Dict[str, str]:
    key = CFG.get("api_key", "") or os.getenv("MERAKI_DASHBOARD_API_KEY", "")
    if not key:
        raise RuntimeError("Meraki API key not set. Run: meraki -> Setup API key")
    return {"X-Cisco-Meraki-API-Key": key, "Content-Type": "application/json"}

def _handle_rate_limit(resp: requests.Response):
    # Honor Meraki's rate limit headers if present
    try:
        remain = int(resp.headers.get("X-Rate-Limit-Remaining", "1"))
        if remain <= 0:
            reset = int(resp.headers.get("X-Rate-Limit-Reset", "1"))
            time.sleep(max(1, reset))
    except Exception:
        pass

def _request(method: str, path: str, *, params=None, json_body=None, timeout=30):
    url = f"{BASE_URL}{path}"
    for attempt in range(3):
        resp = requests.request(
            method, url, headers=_auth_headers(), params=params, json=json_body, timeout=timeout
        )
        _handle_rate_limit(resp)
        if resp.status_code in (200, 201):
            if resp.headers.get("Content-Type","").startswith("application/json"):
                return resp.json()
            return resp.text
        if resp.status_code == 429:
            # backoff
            time.sleep(1 + attempt)
            continue
        if 500 <= resp.status_code < 600:
            time.sleep(1 + attempt)
            continue
        # other errors
        try:
            err = resp.json()
        except Exception:
            err = {"error": resp.text}
        raise RuntimeError(f"Meraki API error {resp.status_code}: {err}")
    raise RuntimeError("Meraki API error: retried too many times")

def get(path: str, **kw):  return _request("GET", path, **kw)
def post(path: str, **kw): return _request("POST", path, **kw)
def put(path: str, **kw):  return _request("PUT", path, **kw)
def delete(path: str, **kw):return _request("DELETE", path, **kw)

def paginate(path: str, *, params=None) -> Iterable[Dict[str, Any]]:
    # Simple keyset pagination using perPage+startingAfter when Meraki supports it
    params = dict(params or {})
    params.setdefault("perPage", 1000)
    starting_after = None
    while True:
        if starting_after:
            params["startingAfter"] = starting_after
        page = get(path, params=params)
        if not isinstance(page, list):
            yield from ([] if page is None else [page])
            break
        if not page:
            break
        for item in page:
            yield item
        # If list shorter than perPage, we likely exhausted
        if len(page) < params["perPage"]:
            break
        starting_after = page[-1].get("id") or page[-1].get("serial") or page[-1].get("name")

# Convenience helpers
def list_organizations():
    return list(paginate("/organizations"))

def list_networks(org_id: str):
    return list(paginate(f"/organizations/{org_id}/networks"))

def list_devices(network_id: str):
    return list(paginate(f"/networks/{network_id}/devices"))
