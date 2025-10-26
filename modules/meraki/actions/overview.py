# modules/meraki/actions/overview.py
from typing import List, Dict, Any, Tuple
import sys

from ..api import CTX

# ---------- tiny utils ----------
def _safe(v, default: str = "-") -> str:
    if v is None:
        return default
    s = str(v).strip()
    return s if s else default

def _pad(s: str, w: int) -> str:
    return f"{_safe(s):<{w}}"

def _status_word(st: Dict[str, Any]) -> str:
    s = (st or {}).get("status") or (st or {}).get("connectionStatus")
    if not s: return "unknown"
    s = str(s).lower()
    if s in ("online","up","connected"):      return "online"
    if s in ("alerting","degraded"):          return "alerting"
    if s in ("offline","down","disconnected"):return "offline"
    return s

def _family_from_model(model: str) -> str:
    m = (model or "").upper()
    if m.startswith(("MX","Z")): return "appliance"
    if m.startswith("MS"):       return "switch"
    if m.startswith(("MR","CW")):return "wireless"
    if m.startswith("MV"):       return "camera"
    if m.startswith("MT"):       return "sensor"
    if m.startswith(("MG")):     return "cellular"
    return "other"

def _merge_status_by_serial(statuses: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for s in statuses or []:
        serial = s.get("serial") or s.get("deviceSerial")
        if serial: out[serial] = s
    return out

def _uplink_summary(st: Dict[str, Any]) -> str:
    if not st: return "-"
    ups = st.get("uplinks")
    if isinstance(ups, list) and ups:
        parts = []
        for u in ups:
            iface=_safe(u.get("interface")).lower()
            status=_safe(u.get("status"))
            pub=_safe(u.get("publicIp"))
            parts.append(f"{iface}:{status}@{pub}" if pub != "-" else f"{iface}:{status}")
        return ", ".join(parts) if parts else "-"
    uplink = st.get("uplink") or st.get("wan1", {})
    if isinstance(uplink, dict) and uplink:
        iface  = _safe(uplink.get("interface"), "wan")
        status = _safe(uplink.get("status"))
        pub    = _safe(uplink.get("publicIp"))
        return f"{iface}:{status}@{pub}" if pub != "-" else f"{iface}:{status}"
    return "-"

# ---------- API helpers (no params signature assumptions) ----------
def _api_get_once(path: str):
    from .. import api as _api
    if hasattr(_api, "api_get"):
        try: return _api.api_get(path)
        except TypeError:
            return _api.api_get(path=path)  # type: ignore
    if hasattr(_api, "get"):
        try: return _api.get(path)
        except TypeError:
            return _api.get(path=path)  # type: ignore
    if hasattr(_api, "request"):
        try: return _api.request("GET", path)
        except TypeError:
            return _api.request(method="GET", path=path)  # type: ignore
    raise RuntimeError("No compatible API GET helper found in ..api")

def _try_paths(paths: List[str]):
    for p in paths:
        for candidate in (p.lstrip("/"), "/" + p.lstrip("/")):
            try:
                return _api_get_once(candidate)
            except Exception as e:
                msg = str(e).lower()
                if "404" in msg or "not found" in msg:
                    continue
                raise
    return None

def _fetch_devices_for_net(net_id: str, org_id: str):
    return _try_paths([
        f"networks/{net_id}/devices",
        f"organizations/{org_id}/devices?networkIds[]={net_id}" if org_id else "",
    ]) or []

def _fetch_statuses_for_net(net_id: str, org_id: str):
    return _try_paths([
        f"networks/{net_id}/devices/statuses",
        f"organizations/{org_id}/devices/statuses?networkIds[]={net_id}" if org_id else "",
    ]) or []

# ---------- ACTION ----------
def run(args: List[str]) -> None:
    """
    overview
        Quick network snapshot (org/net header, counts, breakdown, table)
        with None-safe formatting and resilient API paths.
    """
    net_id = CTX.net_id()
    if not net_id:
        print("No network selected. Use: use net <name>")
        return

    org_id   = CTX.org_id()
    org_name = CTX.org_name() or "-"
    net_name = CTX.net_name() or "-"

    try:
        devices  = _fetch_devices_for_net(net_id, org_id or "")
        statuses = _fetch_statuses_for_net(net_id, org_id or "")
    except Exception as e:
        print(f"Meraki API error: {e}")
        return

    # normalize possible error blobs
    if isinstance(devices, dict) and devices.get("errors"):
        print(f"Meraki API error devices: {devices.get('errors')}")
        devices = []
    if isinstance(statuses, dict) and statuses.get("errors"):
        print(f"Meraki API error statuses: {statuses.get('errors')}")
        statuses = []

    st_by_sn = _merge_status_by_serial(statuses if isinstance(statuses, list) else [])

    total = 0; online = alerting = offline = 0
    fam_counts: Dict[str,int] = {}
    rows: List[Tuple[str,str,str,str,str,str]] = []

    for d in (devices or []):
        if not isinstance(d, dict): continue
        total += 1
        serial = d.get("serial") or d.get("deviceSerial") or "-"
        name   = d.get("name") or d.get("mac") or "-"
        model  = d.get("model") or "-"
        lan_ip = d.get("lanIp")
        st     = st_by_sn.get(serial, {})
        s_word = _status_word(st)

        if s_word == "online": online += 1
        elif s_word == "alerting": alerting += 1
        elif s_word == "offline": offline += 1

        fam = _family_from_model(model)
        fam_counts[fam] = fam_counts.get(fam, 0) + 1

        rows.append((_safe(model), _safe(serial), _safe(name),
                     _safe(s_word), _safe(lan_ip), _safe(_uplink_summary(st))))

    # header
    print("\n=== Network Overview ===")
    print(f"  Org : {_safe(org_name)}")
    print(f"  Net : {_safe(net_name)}")
    print(f"  Devices: {total:<4} | Online: {online:<4}  Alerting: {alerting:<4}  Offline: {offline:<4}")

    parts = []
    for k in ("appliance","switch","wireless","camera","sensor","cellular","other"):
        if fam_counts.get(k): parts.append(f"{k}:{fam_counts[k]}")
    print("  Breakdown: " + (", ".join(parts) if parts else "-"))
    print()

    # simple widths (safe & readable)
    w_model, w_serial, w_name, w_status, w_lan, w_up = 8, 14, 24, 9, 15, 26
    hdr = (_pad("Model", w_model) + _pad("Serial", w_serial) + _pad("Name", w_name) +
           _pad("Status", w_status) + _pad("LAN IP", w_lan) + _pad("Public/Uplink", w_up))
    print(hdr); print("-" * len(hdr))
    rows.sort(key=lambda r: (r[0], r[2]))
    for r in rows:
        print(_pad(r[0], w_model) + _pad(r[1], w_serial) + _pad(r[2], w_name) +
              _pad(r[3], w_status) + _pad(r[4], w_lan) + _pad(r[5], w_up))
    print()

# ---------- FORCE REGISTRATION into the live actions package ----------
META = {
    "desc": "Quick network snapshot: org/net header, device counts, breakdown, device table.",
    "cat": "Network",
    "aliases": []
}

def _force_register():
    # Get the *live* actions package object the console imported
    pkg = sys.modules.get(__package__)  # e.g. "modules.meraki.actions"
    if not pkg:
        return
    # 1) REGISTRY dict (what console uses to dispatch)
    reg = getattr(pkg, "REGISTRY", None)
    if isinstance(reg, dict):
        reg["overview"] = run
    else:
        setattr(pkg, "REGISTRY", {"overview": run})

    # 2) If package tracks metadata for help()
    meta_map = getattr(pkg, "ACTION_META", None)
    if isinstance(meta_map, dict):
        meta_map["overview"] = META
    else:
        # Some codebases expose list_actions() reading ACTIONS / ACTION_META
        setattr(pkg, "ACTION_META", {"overview": META})

    # 3) Common alternates used by some scanners
    acts = getattr(pkg, "ACTIONS", None)
    if isinstance(acts, dict):
        acts["overview"] = {"func": run, **META}
    else:
        setattr(pkg, "ACTIONS", {"overview": {"func": run, **META}})

    # 4) Helper functions, if present
    try:
        add_action = getattr(pkg, "add_action", None)
        if callable(add_action):
            add_action("overview", run, META)  # harmless if duplicates ignored
    except Exception:
        pass
    try:
        register_action = getattr(pkg, "register_action", None)
        if callable(register_action):
            register_action("overview", run, **META)
    except Exception:
        pass

_force_register()
