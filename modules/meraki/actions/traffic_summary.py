# modules/meraki/actions/traffic_summary.py
from . import action
from ..api import CTX, CFG, get, list_networks
from colorama import Fore, Style

try:
    from ..utils import save_json, save_csv, pull_flag, stamp
except Exception:
    def save_json(*a, **k): pass
    def save_csv(*a, **k): pass
    def pull_flag(args, flag): return (False, None, args)
    def stamp(p, e): return f"{p}.{e}"

def _resolve_net(org_id, val):
    if not val: return CTX.net_id()
    if val.startswith("N_") or val.count("-")==4: return val
    try:
        nets = list_networks(org_id) or []
        m = next((n for n in nets if (n.get("name") or "").lower()==val.lower()), None)
        return m.get("id") if m else None
    except Exception:
        return None

@action("traffic summary", "Application traffic mix", cat="Network")
def traffic_summary(args):
    """
    traffic summary
    traffic summary --hours 24
    traffic summary --net <name|id>
    traffic summary --json | --csv
    """
    org_id = CTX.org_id() or CFG.get("default_org_id")
    if not org_id:
        print("Select an org first."); return
    nid = CTX.net_id() or CFG.get("default_network_id")

    jflag, jname, args = pull_flag(args, "--json")
    cflag, cname, args = pull_flag(args, "--csv")

    hours, netarg = 24, None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--hours" and i+1 < len(args):
            hours = max(1, int(args[i+1])); i += 2
        elif a == "--net" and i+1 < len(args):
            netarg = args[i+1]; i += 2
        else:
            i += 1

    nid = _resolve_net(org_id, netarg) or nid
    if not nid:
        print("Select a network first."); return

    params = {"timespan": hours*3600, "perPage": 300}
    try:
        data = get(f"/networks/{nid}/traffic", params=params) or []
    except Exception as e:
        if "perPage" in str(e):
            params.pop("perPage", None)
            data = get(f"/networks/{nid}/traffic", params=params) or []
        else:
            print(f"Meraki API error: {e}"); return

    rows = data if isinstance(data, list) else (data.get("items") or [])
    if not rows:
        print("No traffic data."); return

    print(Fore.CYAN + f"\nTraffic Summary (last {hours}h)\n" + Style.RESET_ALL)
    print(Fore.LIGHTBLUE_EX + f"{'Application/Category':34} {'Clients':7} {'Recv MB':9} {'Sent MB':9}" + Style.RESET_ALL)
    out = []
    for r in rows[:300]:
        app = (r.get("application") or r.get("applicationCategory") or "-")[:34]
        clients = int(r.get("numClients") or r.get("clients", 0))
        recv = float(r.get("recv", 0)) / (1024*1024)
        sent = float(r.get("sent", 0)) / (1024*1024)
        print(f"{app:34} {clients:7d} {recv:9.1f} {sent:9.1f}")
        out.append({"app":app,"clients":clients,"recvMB":round(recv,1),"sentMB":round(sent,1)})
    print()

    if jflag: save_json(rows, jname or stamp("traffic-summary","json"))
    if cflag: save_csv(out, ["app","clients","recvMB","sentMB"], cname or stamp("traffic-summary","csv"))
