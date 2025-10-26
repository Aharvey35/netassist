# modules/meraki/actions/svis.py
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
    return m.startswith("MS") or m.startswith("C93") or m.startswith("C94") or m.startswith("C95") or m.startswith("C96")  # Catalyst 9K families

# ---------- fetchers ----------
def _fetch_svis_network(net_id: str, org_id: str):
    return _try_paths([
        f"networks/{net_id}/switch/routing/interfaces",
        f"organizations/{org_id}/switch/routing/interfaces?networkIds[]={net_id}" if org_id else "",
    ]) or []

def _fetch_svis_stack(net_id: str, stack_id: str):
    return _try_paths([
        f"networks/{net_id}/switch/stacks/{stack_id}/routing/interfaces",
    ]) or []

def _fetch_svis_device(serial: str):
    return _try_paths([
        f"devices/{serial}/switch/routing/interfaces",
    ]) or []

# ---------- flags ----------
def _parse_flags(args: List[str]):
    flags = {"orgwide": False, "net": None}
    for a in list(args):
        if a in ("--orgwide","--wholeorg"):
            flags["orgwide"] = True; args.remove(a)
        elif a.startswith("--net="):
            flags["net"] = a.split("=",1)[1].strip(); args.remove(a)
    return flags

def _list_networks(org_id: str) -> List[Dict[str, Any]]:
    nets = _try_paths([f"organizations/{org_id}/networks?perPage=1000"]) or []
    return nets if isinstance(nets, list) else []

def _find_net(nets: List[Dict[str, Any]], q: str):
    ql = q.lower()
    for n in nets:
        if str(n.get("id","")).lower() == ql or str(n.get("name","")).lower() == ql:
            return n
    for n in nets:
        if ql in str(n.get("name","")).lower():
            return n
    return None

# ---------- action ----------
def run(args: List[str]) -> None:
    """
    svis [--orgwide|--wholeorg] [--net=<name|id>]
        List MS/Catalyst Layer-3 switch interfaces (SVIs).
        Tries network-, stack-, and device-scoped endpoints to cover MS & C9K.
    """
    flags = _parse_flags(args)
    org_id   = CTX.org_id() or ""
    org_name = CTX.org_name() or "-"
    cur_net_id = CTX.net_id()
    cur_net_name = CTX.net_name() or "-"

    targets: List[Dict[str, Any]] = []
    if flags["orgwide"]:
        if not org_id:
            print("No org selected. Use: use org <name>"); return
        targets = _list_networks(org_id)
    elif flags["net"]:
        if not org_id:
            print("No org selected. Use: use org <name>"); return
        hit = _find_net(_list_networks(org_id), flags["net"])
        if not hit:
            print(f"Network not found: {flags['net']}"); return
        targets = [hit]
    else:
        if not cur_net_id:
            print("No network selected. Use: use net <name>"); return
        targets = [{"id": cur_net_id, "name": cur_net_name}]

    all_rows: List[Tuple[str,str,str,str,str,str]] = []
    total = 0
    seen: Set[Tuple[str,str,str]] = set()  # (netId, vlanId, ip) to dedupe

    for n in targets:
        nid = n.get("id"); nname = n.get("name") or "-"
        if not nid: continue

        # 1) network-scoped
        data = _fetch_svis_network(nid, org_id)
        if isinstance(data, list):
            for itf in data:
                vlan   = _safe(itf.get("vlanId"))
                name   = _safe(itf.get("name"))
                ip     = _safe(itf.get("interfaceIp") or itf.get("ip"))
                subnet = _safe(itf.get("subnet"))
                mcast  = _safe(itf.get("multicastRouting"))
                ospf   = _safe((itf.get("ospf") or {}).get("enabled"))
                key = (nid, vlan, ip)
                if key in seen: continue
                seen.add(key)
                all_rows.append((_safe(nname), vlan, name, ip, subnet, f"{mcast} {ospf}".strip()))
                total += 1

        # 2) stack-scoped (if any stacks)
        stacks = _list_switch_stacks(nid)
        for st in stacks:
            sid = st.get("id")
            if not sid: continue
            sdata = _fetch_svis_stack(nid, sid)
            if isinstance(sdata, list):
                for itf in sdata:
                    vlan   = _safe(itf.get("vlanId"))
                    name   = _safe(itf.get("name"))
                    ip     = _safe(itf.get("interfaceIp") or itf.get("ip"))
                    subnet = _safe(itf.get("subnet"))
                    mcast  = _safe(itf.get("multicastRouting"))
                    ospf   = _safe((itf.get("ospf") or {}).get("enabled"))
                    key = (nid, vlan, ip)
                    if key in seen: continue
                    seen.add(key)
                    all_rows.append((_safe(nname), vlan, name, ip, subnet, f"{mcast} {ospf}".strip()))
                    total += 1

        # 3) device-scoped (for MS and Catalyst C9K)
        devs = _list_network_devices(nid)
        for d in devs:
            if not isinstance(d, dict): continue
            if not _is_switch_model(d.get("model","")): continue
            serial = d.get("serial"); 
            if not serial: continue
            ddata = _fetch_svis_device(serial)
            if isinstance(ddata, list):
                for itf in ddata:
                    vlan   = _safe(itf.get("vlanId"))
                    name   = _safe(itf.get("name"))
                    ip     = _safe(itf.get("interfaceIp") or itf.get("ip"))
                    subnet = _safe(itf.get("subnet"))
                    mcast  = _safe(itf.get("multicastRouting"))
                    ospf   = _safe((itf.get("ospf") or {}).get("enabled"))
                    key = (nid, vlan, ip)
                    if key in seen: continue
                    seen.add(key)
                    all_rows.append((_safe(nname), vlan, name, ip, subnet, f"{mcast} {ospf}".strip()))
                    total += 1

    # Render
    multi_net = len({r[0] for r in all_rows}) > 1
    print("\n=== Switch SVIs (MS/Catalyst L3 Interfaces) ===")
    print(f"  Org : {org_name}")
    if multi_net:
        print("  Nets: multiple")
    else:
        print(f"  Net : {targets[0].get('name', cur_net_name)}" if targets else f"  Net : {cur_net_name}")
    print(f"  Count: {total}\n")

    if not all_rows:
        print("(none)\n"); return

    if multi_net:
        w = dict(net=20, vlan=6, name=24, ip=16, subnet=18, extras=12)
        hdr = (_pad("Network", w["net"]) + _pad("VLAN", w["vlan"]) + _pad("Name", w["name"]) +
               _pad("Interface IP", w["ip"]) + _pad("Subnet", w["subnet"]) + _pad("Multicast/OSPF", w["extras"]))
    else:
        w = dict(vlan=6, name=24, ip=16, subnet=18, extras=12)
        hdr = (_pad("VLAN", w["vlan"]) + _pad("Name", w["name"]) + _pad("Interface IP", w["ip"]) +
               _pad("Subnet", w["subnet"]) + _pad("Multicast/OSPF", w["extras"]))
    print(hdr); print("-" * len(hdr))

    all_rows.sort(key=lambda r: (r[0], int(r[1]) if str(r[1]).isdigit() else 9999, r[2]))
    for row in all_rows:
        if multi_net:
            net, vlan, name, ip, subnet, extra = row
            line = (_pad(net, w["net"]) + _pad(vlan, w["vlan"]) + _pad(name, w["name"]) +
                    _pad(ip, w["ip"]) + _pad(subnet, w["subnet"]) + _pad(extra, w["extras"]))
        else:
            _, vlan, name, ip, subnet, extra = row
            line = (_pad(vlan, w["vlan"]) + _pad(name, w["name"]) + _pad(ip, w["ip"]) +
                    _pad(subnet, w["subnet"]) + _pad(extra, w["extras"]))
        print(line)
    print()

# ---------- force registration ----------
META = {
    "desc": "List MS/Catalyst L3 switch interfaces (SVIs). Tries network/stack/device endpoints. Flags: --orgwide/--wholeorg, --net=<name|id>",
    "cat": "Network",
    "aliases": ["switch svis","switch l3","svi list"]
}

def _force_register():
    pkg = sys.modules.get(__package__)  # modules.meraki.actions
    if not pkg: return
    reg = getattr(pkg, "REGISTRY", None)
    if isinstance(reg, dict): reg["svis"] = run
    else: setattr(pkg, "REGISTRY", {"svis": run})
    meta = getattr(pkg, "ACTION_META", None)
    if isinstance(meta, dict): meta["svis"] = META
    else: setattr(pkg, "ACTION_META", {"svis": META})
    acts = getattr(pkg, "ACTIONS", None)
    if isinstance(acts, dict): acts["svis"] = {"func": run, **META}
    else: setattr(pkg, "ACTIONS", {"svis": {"func": run, **META}})
    try:
        pkg.REGISTRY["switch svis"] = run
        pkg.REGISTRY["switch l3"]   = run
        pkg.REGISTRY["svi list"]    = run
    except Exception:
        pass

_force_register()
