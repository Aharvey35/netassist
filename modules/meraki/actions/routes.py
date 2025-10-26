# modules/meraki/actions/routes.py
from typing import List, Dict, Any, Tuple, Set
import sys

from ..api import CTX

# ---------- utils ----------
def _safe(v, default: str = "-") -> str:
    if v is None:
        return default
    s = str(v).strip()
    return s if s else default

def _pad(s: str, w: int) -> str:
    return f"{_safe(s):<{w}}"

def _api_get_once(path: str):
    from .. import api as _api
    if hasattr(_api, "api_get"):
        try: return _api.api_get(path)
        except TypeError: return _api.api_get(path=path)  # type: ignore
    if hasattr(_api, "get"):
        try: return _api.get(path)
        except TypeError: return _api.get(path=path)  # type: ignore
    if hasattr(_api, "request"):
        try: return _api.request("GET", path)
        except TypeError: return _api.request(method="GET", path=path)  # type: ignore
    raise RuntimeError("No compatible API GET helper found in ..api")

def _try_paths(paths: List[str]):
    for p in paths:
        if not p:
            continue
        for cand in (p.lstrip("/"), "/" + p.lstrip("/")):
            try:
                return _api_get_once(cand)
            except Exception as e:
                msg = str(e).lower()
                if "404" in msg or "not found" in msg:
                    continue
                raise
    return None

def _list_network_devices(net_id: str) -> List[Dict[str, Any]]:
    devs = _try_paths([f"networks/{net_id}/devices"]) or []
    return devs if isinstance(devs, list) else []

def _list_switch_stacks(net_id: str) -> List[Dict[str, Any]]:
    stacks = _try_paths([f"networks/{net_id}/switch/stacks"]) or []
    return stacks if isinstance(stacks, list) else []

def _is_switch_model(model: str) -> bool:
    m = (model or "").upper()
    return m.startswith("MS") or m.startswith("C93") or m.startswith("C94") or m.startswith("C95") or m.startswith("C96")

# ---------- fetchers ----------
# MX routes (unchanged)
def _fetch_appliance_routes(net_id: str, org_id: str):
    return _try_paths([
        f"networks/{net_id}/appliance/staticRoutes",
        f"organizations/{org_id}/appliance/staticRoutes?networkIds[]={net_id}" if org_id else "",
    ]) or []

# MS routes — try network, stack, then device
def _fetch_switch_routes_network(net_id: str, org_id: str):
    return _try_paths([
        f"networks/{net_id}/switch/routing/staticRoutes",
        f"organizations/{org_id}/switch/routing/staticRoutes?networkIds[]={net_id}" if org_id else "",
    ]) or []

def _fetch_switch_routes_stack(net_id: str, stack_id: str):
    return _try_paths([
        f"networks/{net_id}/switch/stacks/{stack_id}/routing/staticRoutes",
    ]) or []

def _fetch_switch_routes_device(serial: str):
    return _try_paths([
        f"devices/{serial}/switch/routing/staticRoutes",
    ]) or []

# ---------- flags ----------
def _parse_flags(args: List[str]):
    flags = {"mx": False, "switch": False}
    for a in list(args):
        if a == "--mx": flags["mx"] = True; args.remove(a)
        elif a == "--switch": flags["switch"] = True; args.remove(a)
    return flags

# ---------- action ----------
def run(args: List[str]) -> None:
    """
    routes [--mx] [--switch]
        Show static routes on the selected network.
        Tries MS routes via network/stack/device to cover MS & Catalyst C9K.
    """
    flags = _parse_flags(args)
    net_id = CTX.net_id()
    if not net_id:
        print("No network selected. Use: use net <name>"); return

    org_id   = CTX.org_id() or ""
    org_name = CTX.org_name() or "-"
    net_name = CTX.net_name() or "-"

    only_mx = flags["mx"] and not flags["switch"]
    only_sw = flags["switch"] and not flags["mx"]

    # MX
    mx_routes = []
    if not only_sw:
        data_mx = _fetch_appliance_routes(net_id, org_id)
        if isinstance(data_mx, dict) and data_mx.get("errors"):
            print(f"Meraki API (MX routes) error: {data_mx.get('errors')}")
        elif isinstance(data_mx, list):
            mx_routes = data_mx

    # MS — network, stacks, devices
    sw_routes: List[Dict[str, Any]] = []
    if not only_mx:
        # 1) network-level
        data_sw = _fetch_switch_routes_network(net_id, org_id)
        if isinstance(data_sw, list):
            sw_routes.extend(data_sw)

        # 2) stack-level
        stacks = _list_switch_stacks(net_id)
        for st in stacks:
            sid = st.get("id")
            if not sid: continue
            sdata = _fetch_switch_routes_stack(net_id, sid)
            if isinstance(sdata, list):
                sw_routes.extend(sdata)

        # 3) device-level
        devs = _list_network_devices(net_id)
        for d in devs:
            if not isinstance(d, dict): continue
            if not _is_switch_model(d.get("model","")): continue
            serial = d.get("serial"); 
            if not serial: continue
            ddata = _fetch_switch_routes_device(serial)
            if isinstance(ddata, list):
                sw_routes.extend(ddata)

    # -------- render --------
    print("\n=== Static Routes ===")
    print(f"  Org : {org_name}")
    print(f"  Net : {net_name}")

    # MX table
    if not only_sw:
        print("\n-- MX (Appliance) --")
        if not mx_routes:
            print("  (none)")
        else:
            w = dict(name=24, subnet=20, nh=16, active=8, advertise=10)
            hdr = (_pad("Name", w["name"]) + _pad("Subnet", w["subnet"]) +
                   _pad("Next Hop", w["nh"]) + _pad("Active", w["active"]) +
                   _pad("Advertise", w["advertise"]))
            print(hdr); print("-" * len(hdr))
            for r in mx_routes:
                name  = _safe(r.get("name"))
                subnet= _safe(r.get("subnet"))
                nh    = _safe(r.get("nextHopIp") or r.get("gatewayIp"))
                active= _safe(r.get("active"))
                adv   = _safe(r.get("advertiseViaVpn") or r.get("advertiseViaOspf"))
                line = (_pad(name, w["name"]) + _pad(subnet, w["subnet"]) +
                        _pad(nh, w["nh"]) + _pad(active, w["active"]) +
                        _pad(adv, w["advertise"]))
                print(line)

    # MS table
    if not only_mx:
        print("\n-- MS (Switch/Catalyst) --")
        if not sw_routes:
            print("  (none)")
        else:
            w = dict(name=24, subnet=20, nh=16, active=8, ospf=8)
            hdr = (_pad("Name", w["name"]) + _pad("Subnet", w["subnet"]) +
                   _pad("Next Hop", w["nh"]) + _pad("Active", w["active"]) +
                   _pad("OSPF", w["ospf"]))
            print(hdr); print("-" * len(hdr))
            for r in sw_routes:
                name  = _safe(r.get("name"))
                subnet= _safe(r.get("subnet"))
                nh    = _safe(r.get("nextHopIp") or r.get("gatewayIp"))
                active= _safe(r.get("active"))
                ospf  = _safe(r.get("advertiseViaOspf") or (r.get("ospf") or {}).get("enabled"))
                line = (_pad(name, w["name"]) + _pad(subnet, w["subnet"]) +
                        _pad(nh, w["nh"]) + _pad(active, w["active"]) +
                        _pad(ospf, w["ospf"]))
                print(line)
    print()

# ---------- force registration ----------
META = {
    "desc": "Show static routes on MX and MS/Catalyst. Tries network/stack/device endpoints. Flags: --mx, --switch",
    "cat": "Network",
    "aliases": ["route list","static routes","show routes"]
}

def _force_register():
    pkg = sys.modules.get(__package__)  # modules.meraki.actions
    if not pkg: return
    reg = getattr(pkg, "REGISTRY", None)
    if isinstance(reg, dict): reg["routes"] = run
    else: setattr(pkg, "REGISTRY", {"routes": run})
    meta = getattr(pkg, "ACTION_META", None)
    if isinstance(meta, dict): meta["routes"] = META
    else: setattr(pkg, "ACTION_META", {"routes": META})
    acts = getattr(pkg, "ACTIONS", None)
    if isinstance(acts, dict): acts["routes"] = {"func": run, **META}
    else: setattr(pkg, "ACTIONS", {"routes": {"func": run, **META}})
    try:
        pkg.REGISTRY["route list"]   = run
        pkg.REGISTRY["static routes"]= run
        pkg.REGISTRY["show routes"]  = run
    except Exception:
        pass

_force_register()
