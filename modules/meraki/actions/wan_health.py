# modules/meraki/actions/wan_health.py
from . import action
from ..api import CTX, CFG, get, list_networks
from ..utils import save_json, save_csv, pull_flag, stamp
from colorama import Fore, Style

@action("wan health", "WAN uplink snapshot", cat="Network")
def wan_health(args):
    """
    Usage:
      wan health                → org-wide snapshot
      wan health --net <id|name>  → specific network
      wan health --only ok|offline|degraded
      wan health --json | --csv
    """
    org_id = CTX.org_id() or CFG.get("default_org_id")
    if not org_id:
        print("Select an org first."); return

    # Flags
    jflag, jname, args = pull_flag(args, "--json")
    cflag, cname, args = pull_flag(args, "--csv")

    # Filters
    only = None
    nid  = CTX.net_id()  # default to current network if set
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--only" and i+1 < len(args):
            only = args[i+1].lower(); i += 2
        elif a == "--net" and i+1 < len(args):
            nid = args[i+1]; i += 2
        else:
            i += 1

    # Resolve net name to id if needed
    if nid and not (nid.startswith("N_") or nid.count("-") == 4):
        try:
            nets = list_networks(org_id)
            match = next((n for n in nets if (n.get("name") or "").lower() == str(nid).lower()), None)
            if match: nid = match.get("id")
        except Exception:
            pass

    params = {"perPage": 300}
    if nid:
        params["networkIds[]"] = [nid]

    try:
        rows = get(f"/organizations/{org_id}/appliance/uplink/statuses", params=params) or []
    except Exception as e:
        if "perPage" in str(e):
            params.pop("perPage", None)
            rows = get(f"/organizations/{org_id}/appliance/uplink/statuses", params=params) or []
        else:
            print(f"Meraki API error: {e}"); return

    # Normalize list
    items = rows if isinstance(rows, list) else (rows.get("items") or rows.get("uplinks") or [])
    if not items:
        print("No uplink data."); return

    def derive_state(uplinks):
        """
        ok       : at least one 'active' / 'ready'
        degraded : none active, but at least one 'connecting'/'failed'/'not connected'
        offline  : empty / all 'not connected'
        """
        states = [ (u.get("status") or "").lower() for u in (uplinks or []) ]
        if any(s in ("active","ready") for s in states):
            return "ok"
        if not states or all(s == "not connected" for s in states):
            return "offline"
        return "degraded"

    # Build flat rows
    flat = []
    for d in items:
        net  = d.get("networkName") or "-"
        ser  = d.get("serial") or "-"
        mdl  = d.get("model") or "-"
        upls = d.get("uplinks") or []
        state = derive_state(upls)
        if only and state != only:
            continue
        for u in upls or [{"interface":"-","status":"not connected"}]:
            flat.append({
                "network": net, "serial": ser, "model": mdl,
                "iface": u.get("interface","-"),
                "status": u.get("status","-"),
                "publicIp": u.get("publicIp","-"),
                "ip": u.get("ip","-"),
                "gateway": u.get("gateway","-"),
                "overall": state
            })

    if not flat:
        print("No uplinks match filter."); return

    # Print
    scope = f"net:{nid}" if nid else "org"
    print(Fore.CYAN + f"\nWAN Health ({scope})\n" + Style.RESET_ALL)
    print(Fore.LIGHTBLUE_EX + f"{'Network':24} {'Serial':14} {'Model':8} {'If':3} {'Status':12} {'Public IP':15} {'Overall':8}" + Style.RESET_ALL)
    for r in flat[:600]:
        st = (r['status'] or "-").lower()
        ov = r['overall']
        c_status  = (Fore.GREEN if st in ("active","ready") else (Fore.YELLOW if st in ("connecting","failed") else Fore.RED))
        c_overall = (Fore.GREEN if ov == "ok" else (Fore.YELLOW if ov == "degraded" else Fore.RED))
        print(f"{(r['network'] or '-')[:24]:24} {(r['serial'] or '-')[:14]:14} {(r['model'] or '-')[:8]:8} "
              f"{(r['iface'] or '-')[:3]:3} {c_status}{st:<12}{Style.RESET_ALL} {(r['publicIp'] or '-')[:15]:15} {c_overall}{ov:<8}{Style.RESET_ALL}")
    print()

    # Exports
    if jflag:
        save_json(flat, jname or stamp("wan-health", "json"))
    if cflag:
        save_csv(flat, ["network","serial","model","iface","status","publicIp","ip","gateway","overall"],
                 cname or stamp("wan-health", "csv"))
