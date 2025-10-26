# modules/meraki/actions/l3_inventory.py
from typing import Any, Dict, List, Tuple

# Use your existing API + utils
from ..api import CFG, CTX, get, list_devices  # list_devices is in api.py
from ..utils import save_json, save_csv, pull_flag

# Import the central registry/decorator used by your console
try:
    from . import REGISTRY as ACTIONS_REG, list_actions as ACTIONS_META, action as ACTION_DECORATOR
except Exception:
    ACTIONS_REG = {}            # fallback (won’t be used by your console)
    ACTIONS_META = lambda: {}   # fallback
    ACTION_DECORATOR = None

# --------------------------
# Helpers
# --------------------------

def _need_net_id() -> str:
    net_id = None
    try:
        net_id = CTX.net_id()
    except Exception:
        pass
    net_id = net_id or CFG.get("default_network_id")
    if not net_id:
        raise RuntimeError("No network selected. Run: use org <name>  →  use net <name>")
    return net_id

def _api_get(path: str, params: Dict[str, Any] = None) -> Any:
    """
    Wrap your get() to include the path in any thrown error.
    api.get() returns the JSON (or text) or raises RuntimeError for non-2xx.
    """
    try:
        return get(path, params=params or {})
    except Exception as e:
        raise RuntimeError(f"GET {path} failed: {e}") from e

def _is_switch(device: Dict[str, Any]) -> bool:
    model = (device.get("model") or "").upper()
    prod  = (device.get("productType") or "").lower()
    return model.startswith("MS") or prod == "switch"

def _print_table(rows: List[Dict[str, Any]], headers: List[Tuple[str, str]]) -> None:
    if not rows:
        print("No data.")
        return
    widths = [len(t) for _, t in headers]
    for r in rows:
        for i, (k, _) in enumerate(headers):
            v = r.get(k, "")
            widths[i] = max(widths[i], len("" if v is None else str(v)))
    print("  ".join(t.ljust(widths[i]) for i, (_, t) in enumerate(headers)))
    print("  ".join("-" * widths[i] for i in range(len(headers))))
    for r in rows:
        print("  ".join(str(r.get(k, "") or "").ljust(widths[i]) for i, (k, _) in enumerate(headers)))

# --------------------------
# Data collection
# --------------------------

def _stack_list(network_id: str) -> List[Dict[str, Any]]:
    # v1: GET /networks/{networkId}/switch/stacks
    try:
        return _api_get(f"/networks/{network_id}/switch/stacks") or []
    except Exception:
        return []

def _stack_interfaces(network_id: str, stack_id: str) -> List[Dict[str, Any]]:
    # v1: GET /networks/{networkId}/switch/stacks/{stackId}/routing/interfaces
    try:
        return _api_get(f"/networks/{network_id}/switch/stacks/{stack_id}/routing/interfaces") or []
    except Exception:
        return []

def _stack_static_routes(network_id: str, stack_id: str) -> List[Dict[str, Any]]:
    # v1: GET /networks/{networkId}/switch/stacks/{stackId}/routing/staticRoutes
    try:
        return _api_get(f"/networks/{network_id}/switch/stacks/{stack_id}/routing/staticRoutes") or []
    except Exception:
        return []

def _device_interfaces(serial: str) -> List[Dict[str, Any]]:
    # v1: GET /devices/{serial}/switch/routing/interfaces
    try:
        return _api_get(f"/devices/{serial}/switch/routing/interfaces") or []
    except Exception:
        return []

def _device_static_routes(serial: str) -> List[Dict[str, Any]]:
    # v1: GET /devices/{serial}/switch/routing/staticRoutes
    try:
        return _api_get(f"/devices/{serial}/switch/routing/staticRoutes") or []
    except Exception:
        return []

def _mx_static_routes(network_id: str) -> List[Dict[str, Any]]:
    # v1: GET /networks/{networkId}/appliance/staticRoutes
    try:
        return _api_get(f"/networks/{network_id}/appliance/staticRoutes") or []
    except Exception:
        return []

def _gather_svis(network_id: str) -> List[Dict[str, Any]]:
    devices = list_devices(network_id)
    stacks  = _stack_list(network_id)

    name_by_serial = {d.get("serial"): (d.get("name") or d.get("mac") or d.get("serial")) for d in devices}
    ms_serials = {d.get("serial") for d in devices if _is_switch(d)}
    stack_serials = {ser for s in stacks for ser in (s.get("serials") or [])}

    rows: List[Dict[str, Any]] = []

    # Stack-level SVIs
    for s in stacks:
        sid = s.get("id")
        for itf in _stack_interfaces(network_id, sid):
            itf = dict(itf)
            itf["_scope"] = "stack"
            itf["_stackId"] = sid
            ser = itf.get("serial")
            if ser in name_by_serial:
                itf["_deviceName"] = name_by_serial[ser]
            rows.append(itf)

    # Standalone switches SVIs
    for ser in sorted(ms_serials - stack_serials):
        for itf in _device_interfaces(ser):
            itf = dict(itf)
            itf["_scope"] = "device"
            itf["_serial"] = ser
            itf["_deviceName"] = name_by_serial.get(ser, ser)
            rows.append(itf)

    return rows

def _gather_switch_routes(network_id: str) -> List[Dict[str, Any]]:
    devices = list_devices(network_id)
    stacks  = _stack_list(network_id)

    name_by_serial = {d.get("serial"): (d.get("name") or d.get("mac") or d.get("serial")) for d in devices}
    ms_serials = {d.get("serial") for d in devices if _is_switch(d)}
    stack_serials = {ser for s in stacks for ser in (s.get("serials") or [])}

    rows: List[Dict[str, Any]] = []

    # Stack routes
    for s in stacks:
        sid = s.get("id")
        for r in _stack_static_routes(network_id, sid):
            rr = dict(r)
            rr["_scope"] = "stack"
            rr["_stackId"] = sid
            rows.append(rr)

    # Device routes
    for ser in sorted(ms_serials - stack_serials):
        for r in _device_static_routes(ser):
            rr = dict(r)
            rr["_scope"] = "device"
            rr["_serial"] = ser
            rr["_deviceName"] = name_by_serial.get(ser, ser)
            rows.append(rr)

    return rows

# --------------------------
# Actions (implementations)
# --------------------------

def l3_overview(args: List[str] = None) -> None:
    """
    l3 overview
      Quick counts + small preview of SVIs and static routes (Switch + MX).
      Flags:
        --json              write exports/l3-overview.json
        --csv <prefix.csv>  write three CSVs with the given prefix
    """
    args = args or []
    net_id = _need_net_id()

    svis = _gather_svis(net_id)
    sw   = _gather_switch_routes(net_id)
    mx   = _mx_static_routes(net_id)

    print(f"Layer-3 Overview  (network: {getattr(CTX,'net_name',lambda:None)() or net_id})")
    print(f"  SVIs            : {len(svis)}")
    print(f"  Switch routes   : {len(sw)}")
    print(f"  MX routes       : {len(mx)}\n")

    prev_svis = [{
        "scope": r.get("_scope"),
        "where": r.get("_stackId") or r.get("_deviceName") or r.get("_serial"),
        "name":  r.get("name"),
        "vlan":  r.get("vlanId"),
        "subnet": r.get("subnet"),
        "ip":     r.get("interfaceIp"),
    } for r in svis[:10]]
    if prev_svis:
        print("SVIs (first 10):")
        _print_table(prev_svis, [
            ("scope","Scope"),("where","Device/Stack"),("name","Name"),
            ("vlan","VLAN"),("subnet","Subnet"),("ip","IP"),
        ])
        print()

    prev_routes = [{
        "scope": r.get("_scope","appliance"),
        "where": r.get("_stackId") or r.get("_deviceName") or r.get("_serial") or "MX",
        "name":  r.get("name"),
        "subnet": r.get("subnet"),
        "nextHop": r.get("nextHopIp") or r.get("gatewayIp") or r.get("nextHop") or "",
    } for r in (sw + mx)[:10]]
    if prev_routes:
        print("Static Routes (first 10):")
        _print_table(prev_routes, [
            ("scope","Scope"),("where","Device/Stack"),("name","Name"),("subnet","Subnet"),("nextHop","Next Hop"),
        ])
        print()

    want_json, jname, _ = pull_flag(args, "--json")
    want_csv,  cname, _ = pull_flag(args, "--csv")
    if want_json:
        save_json({
            "networkId": net_id, "svis": svis,
            "switchStaticRoutes": sw, "applianceStaticRoutes": mx
        }, jname or "l3-overview.json")
        print("Wrote exports/l3-overview.json")
    if want_csv:
        prefix = (cname or "l3-overview.csv").rstrip(".csv")
        save_csv(svis,                f"{prefix}_svis.csv")
        save_csv(sw,                  f"{prefix}_routes_switch.csv")
        save_csv(mx,                  f"{prefix}_routes_mx.csv")
        print(f"Wrote CSVs with prefix: {prefix}_*.csv")

def l3_svis(args: List[str] = None) -> None:
    """
    l3 svis
      List switch L3 interfaces (SVIs) across stacks + standalone switches.
      Flags:
        --json            write exports/svis.json
        --csv <file.csv>  write CSV
    """
    args = args or []
    net_id = _need_net_id()
    svis = _gather_svis(net_id)
    rows = [{
        "scope": r.get("_scope"),
        "deviceOrStack": r.get("_deviceName") or r.get("_serial") or r.get("_stackId"),
        "name": r.get("name"),
        "mode": r.get("mode"),
        "vlanId": r.get("vlanId"),
        "subnet": r.get("subnet"),
        "ip": r.get("interfaceIp"),
        "defaultGw": r.get("defaultGateway"),
    } for r in svis]
    print(f"L3 SVIs for {getattr(CTX,'net_name',lambda:None)() or net_id} (total {len(rows)})")
    _print_table(rows, [
        ("scope","Scope"),("deviceOrStack","Device/Stack"),("name","Name"),
        ("mode","Mode"),("vlanId","VLAN"),("subnet","Subnet"),("ip","IP"),("defaultGw","Default GW"),
    ])
    want_json, jname, _ = pull_flag(args, "--json")
    want_csv,  cname, _ = pull_flag(args, "--csv")
    if want_json:
        save_json(svis, jname or "svis.json"); print("Wrote exports/svis.json")
    if want_csv:
        save_csv(svis, cname or "svis.csv");   print(f"Wrote exports/{cname or 'svis.csv'}")

def l3_routes(args: List[str] = None) -> None:
    """
    l3 routes
      List static routes on Switch (stack + standalone) and MX.
      Flags:
        --json            write exports/routes.json
        --csv <file.csv>  write CSV
    """
    args = args or []
    net_id = _need_net_id()
    sw = _gather_switch_routes(net_id)
    mx = _mx_static_routes(net_id)
    merged = []
    for r in sw:
        merged.append({
            "scope": "switch_" + r.get("_scope","device"),
            "where": r.get("_deviceName") or r.get("_serial") or r.get("_stackId"),
            "name": r.get("name"),
            "subnet": r.get("subnet"),
            "nextHop": r.get("nextHopIp") or r.get("gatewayIp") or r.get("nextHop") or "",
            "id": r.get("staticRouteId") or r.get("id"),
        })
    for r in mx:
        merged.append({
            "scope": "appliance",
            "where": "MX",
            "name": r.get("name"),
            "subnet": r.get("subnet"),
            "nextHop": r.get("nextHopIp") or r.get("gatewayIp") or r.get("nextHop") or "",
            "id": r.get("id") or r.get("staticRouteId"),
        })
    print(f"Static Routes for {getattr(CTX,'net_name',lambda:None)() or net_id} (total {len(merged)})")
    _print_table(merged, [
        ("scope","Scope"),("where","Device/Stack"),("name","Name"),
        ("subnet","Subnet"),("nextHop","Next Hop"),("id","ID"),
    ])
    want_json, jname, _ = pull_flag(args, "--json")
    want_csv,  cname, _ = pull_flag(args, "--csv")
    if want_json:
        save_json({"switch": sw, "appliance": mx}, jname or "routes.json"); print("Wrote exports/routes.json")
    if want_csv:
        save_csv(merged, cname or "routes.csv"); print(f"Wrote exports/{cname or 'routes.csv'}")

# --------------------------
# Registration (both styles)
# --------------------------

def _register(name: str, desc: str, fn, cat: str = "Org & Admin", aliases: List[str] = None):
    """Register into your console’s global registry & metadata."""
    aliases = aliases or []
    # Decorator-style (if available)
    if ACTION_DECORATOR:
        ACTION_DECORATOR(name=name, desc=desc, cat=cat, aliases=aliases)(fn)
    # Direct registry (always do this too)
    if ACTIONS_REG is not None:
        ACTIONS_REG[name] = fn
        for a in aliases:
            ACTIONS_REG[a] = fn
    # Metadata for help menus
    try:
        acts = ACTIONS_META()
        acts[name] = {"desc": desc, "cat": cat, "aliases": aliases}
        for a in aliases:
            acts[a] = {"desc": f"(alias) {desc}", "cat": cat, "aliases": []}
    except Exception:
        pass

_register("l3 overview", "Counts + preview of SVIs and static routes.", l3_overview,
          cat="Org & Admin", aliases=["l3","l3 summary","overview"])
_register("l3 svis",     "List switch L3 interfaces (SVIs) for the selected network.", l3_svis,
          cat="Org & Admin", aliases=[])
_register("l3 routes",   "List static routes in one view (Switch + MX).", l3_routes,
          cat="Org & Admin", aliases=["l3 route","l3 staticroute","routes","route","staticroute"])
