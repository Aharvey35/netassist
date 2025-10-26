# modules/meraki/actions/api_usage.py
from . import action
from ..api import CTX, CFG, get
from colorama import Fore, Style

try:
    from ..utils import save_json, pull_flag, stamp
except Exception:
    def save_json(*a, **k): pass
    def pull_flag(args, flag): return (False, None, args)
    def stamp(p, e): return f"{p}.{e}"

@action("api usage", "Org API request overview", cat="General")
def api_usage(args):
    """
    api usage
    api usage --hours 24
    api usage --json
    """
    org_id = CTX.org_id() or CFG.get("default_org_id")
    if not org_id:
        print("Select an org first."); return

    jflag, jname, args = pull_flag(args, "--json")
    hours = 24
    if args and args[0] == "--hours" and len(args) > 1:
        try: hours = max(1, int(args[1]))
        except Exception: pass

    params = {"timespan": hours*3600}
    try:
        data = get(f"/organizations/{org_id}/apiRequests/overview", params=params) or {}
    except Exception as e:
        print(f"Meraki API error: {e}"); return

    totals = data.get("responseCodeCounts") or {}
    users  = data.get("userAgents") or []
    paths  = data.get("paths") or []

    print(Fore.CYAN + f"\nAPI Usage (last {hours}h)\n" + Style.RESET_ALL)
    if totals:
        ok = int(totals.get("200", 0))
        rate = data.get("rateLimitHitCount", 0)
        print(f"  200 OK      : {ok}")
        for k in ("429","4xx","5xx"):
            v = totals.get(k) or totals.get(k.upper())
            if v: print(f"  {k:<10}: {v}")
        print(f"  rate-limit hits: {rate}")
    if users:
        print(Fore.LIGHTBLUE_EX + "\nTop User-Agents:" + Style.RESET_ALL)
        for u in users[:10]:
            print(f"  - {u.get('userAgent','?')[:50]}  ({u.get('count',0)})")
    if paths:
        print(Fore.LIGHTBLUE_EX + "\nTop Endpoints:" + Style.RESET_ALL)
        for p in paths[:10]:
            print(f"  - {p.get('path','?')[:60]}  ({p.get('count',0)})")
    print()

    if jflag: save_json(data, jname or stamp("api-usage","json"))
