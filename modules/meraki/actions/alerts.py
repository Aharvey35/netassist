# modules/meraki/actions/alerts.py
from . import action
from ..api import CTX, CFG, get, list_networks
from ..utils import save_json, save_csv, pull_flag, stamp
from colorama import Fore, Style
import time

@action("alerts", "Recent alert-like events", cat="Network")
def alerts(args):
    """
    Usage:
      alerts --mins 60
      alerts --net <name|id>
      alerts --json | --csv
    """
    org_id = CTX.org_id() or CFG.get("default_org_id")
    if not org_id:
        print("Select an org first."); return

    # Flags
    jflag, jname, args = pull_flag(args, "--json")
    cflag, cname, args = pull_flag(args, "--csv")

    mins = 60
    net_filter = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--mins" and i+1 < len(args):
            mins = int(args[i+1]); i += 2
        elif a == "--net" and i+1 < len(args):
            net_filter = args[i+1]; i += 2
        else:
            i += 1

    params = {"t0": int(time.time()) - mins*60, "perPage": 300, "sortOrder":"descending"}
    # If a network name/id passed, resolve name→id
    if net_filter:
        nid = net_filter
        if not (nid.startswith("N_") or nid.count("-") == 4):  # crude id test; else try by name
            try:
                nets = list_networks(org_id)
                match = next((n for n in nets if (n.get("name") or "").lower() == net_filter.lower()), None)
                if match: nid = match.get("id")
            except Exception:
                pass
        params["networkIds[]"] = [nid]

    try:
        data = get(f"/organizations/{org_id}/events", params=params) or []
    except Exception as e:
        # Older orgs may enforce perPage; retry w/o
        if "perPage" in str(e):
            params.pop("perPage", None)
            data = get(f"/organizations/{org_id}/events", params=params) or []
        else:
            print(f"Meraki API error: {e}"); return

    # Normalize
    events = data if isinstance(data, list) else (data.get("events") or data.get("items") or [])
    if not events:
        print("No recent events."); return

    # Heuristic: “alert-like” = type contains 'alert' OR severity field equals 'critical|warning|error'
    def is_alert(ev):
        typ = (ev.get("type") or "").lower()
        sev = (ev.get("severity") or "").lower()
        return ("alert" in typ) or (sev in ("critical","warning","error"))

    alerts = [e for e in events if is_alert(e)]
    if not alerts:
        print("No alert-like events in window."); return

    print(Fore.CYAN + f"\nAlerts (last {mins} min):\n" + Style.RESET_ALL)
    print(Fore.LIGHTBLUE_EX + f"{'When':19} {'Network':24} {'Type':28} {'Device/Client':24}" + Style.RESET_ALL)
    rows = []
    for ev in alerts[:400]:
        when = (ev.get("occurredAt","-").replace("T"," ").replace("Z",""))[:19]
        net  = (ev.get("networkName") or "-")[:24]
        typ  = (ev.get("type") or "-")[:28]
        dev  = (ev.get("deviceName") or ev.get("deviceSerial") or ev.get("clientName") or ev.get("clientMac") or "-")[:24]
        sev  = (ev.get("severity") or "").lower()
        color = Fore.RED if sev == "critical" else (Fore.YELLOW if sev in ("warning","error") else Style.RESET_ALL)
        print(f"{when:19} {net:24} {color}{typ:28}{Style.RESET_ALL} {dev:24}")
        rows.append({"occurredAt": when, "network": net, "type": typ, "deviceOrClient": dev, "severity": sev})

    print()
    if jflag:
        save_json(alerts, jname or stamp("alerts", "json"))
    if cflag:
        save_csv(rows, ["occurredAt","network","type","deviceOrClient","severity"], cname or stamp("alerts", "csv"))
