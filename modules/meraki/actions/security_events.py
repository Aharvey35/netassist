# modules/meraki/actions/security_events.py
from . import action
from ..api import CTX, CFG, get
from colorama import Fore, Style

try:
    from ..utils import save_json, pull_flag, stamp
except Exception:
    def save_json(*a, **k): pass
    def pull_flag(args, flag): return (False, None, args)
    def stamp(p, e): return f"{p}.{e}"

@action("security events", "Recent MX security events", cat="Network")
def security_events(args):
    """
    security events
    security events --mins 60
    security events --json
    """
    nid = CTX.net_id() or CFG.get("default_network_id")
    if not nid:
        print("Select a network first."); return

    jflag, jname, args = pull_flag(args, "--json")
    mins = 60
    if args and args[0] == "--mins" and len(args) > 1:
        try: mins = max(1, int(args[1]))
        except Exception: pass

    params = {"t0": None, "timespan": mins*60, "perPage": 300}
    try:
        rows = get(f"/networks/{nid}/appliance/security/events", params=params) or []
    except Exception as e:
        if "perPage" in str(e):
            params.pop("perPage", None)
            rows = get(f"/networks/{nid}/appliance/security/events", params=params) or []
        else:
            print(f"Meraki API error: {e}"); return

    events = rows if isinstance(rows, list) else (rows.get("events") or rows.get("items") or [])
    if not events:
        print("No security events in window."); return

    print(Fore.CYAN + f"\nSecurity Events (last {mins} min)\n" + Style.RESET_ALL)
    print(Fore.LIGHTBLUE_EX + f"{'When':19} {'Src → Dst':40} {'Sig/Rule':24}" + Style.RESET_ALL)
    for ev in events[:400]:
        when = (ev.get("occurredAt","-").replace("T"," ").replace("Z",""))[:19]
        src  = ev.get("srcIp") or ev.get("clientIp") or "-"
        dst  = ev.get("dstIp") or ev.get("destinationIp") or "-"
        sig  = ev.get("signature") or ev.get("ruleId") or ev.get("rule") or "-"
        print(f"{when:19} {(src+' → '+dst)[:40]:40} {sig[:24]:24}")
    print()

    if jflag: save_json(events, jname or stamp("security-events","json"))
