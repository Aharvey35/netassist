# modules/meraki/actions/client_top.py
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

@action("clients top", "Top clients by usage", cat="Network")
def clients_top(args):
    """
    clients top
    clients top --hours 24 --top 15
    clients top --net <name|id>
    clients top --json | --csv
    """
    org_id = CTX.org_id() or CFG.get("default_org_id")
    if not org_id:
        print("Select an org first."); return
    nid = CTX.net_id() or CFG.get("default_network_id")

    # flags
    jflag, jname, args = pull_flag(args, "--json")
    cflag, cname, args = pull_flag(args, "--csv")

    hours, topn, netarg = 24, 10, None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--hours" and i+1 < len(args):
            hours = max(1, int(args[i+1])); i += 2
        elif a == "--top" and i+1 < len(args):
            topn = max(1, int(args[i+1])); i += 2
        elif a == "--net" and i+1 < len(args):
            netarg = args[i+1]; i += 2
        else:
            i += 1

    nid = _resolve_net(org_id, netarg) or nid
    if not nid:
        print("Select a network first."); return

    params = {"perPage": 300, "timespan": hours*3600}
    try:
        rows = get(f"/networks/{nid}/clients", params=params) or []
    except Exception as e:
        if "perPage" in str(e):
            params.pop("perPage", None)
            rows = get(f"/networks/{nid}/clients", params=params) or []
        else:
            print(f"Meraki API error: {e}"); return

    if not isinstance(rows, list) or not rows:
        print("No clients in window."); return

    # usage structure: {"sent": bytes, "recv": bytes}
    def total_bytes(c):
        u = c.get("usage") or {}
        return float(u.get("sent",0)) + float(u.get("recv",0))

    rows.sort(key=total_bytes, reverse=True)
    top = rows[:topn]

    print(Fore.CYAN + f"\nTop {topn} Clients (last {hours}h)\n" + Style.RESET_ALL)
    print(Fore.LIGHTBLUE_EX + f"{'Client':24} {'IP/MAC':20} {'Usage (MB)':12} {'Device':18}" + Style.RESET_ALL)
    out = []
    for c in top:
        name = (c.get("description") or c.get("dhcpHostname") or c.get("mdnsName") or "-")[:24]
        ident = (c.get("ip") or c.get("mac") or "-")[:20]
        u = c.get("usage") or {}
        mb = (float(u.get("sent",0))+float(u.get("recv",0)))/ (1024*1024)
        dev = (c.get("recentDeviceName") or c.get("switchport") or "-")[:18]
        print(f"{name:24} {ident:20} {mb:12.1f} {dev:18}")
        out.append({"client":name,"ipOrMac":ident,"usageMB":round(mb,1),"device":dev})

    print()
    if jflag: save_json(top, jname or stamp("clients-top","json"))
    if cflag: save_csv(out, ["client","ipOrMac","usageMB","device"], cname or stamp("clients-top","csv"))
