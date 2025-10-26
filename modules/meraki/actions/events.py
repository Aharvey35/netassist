# modules/meraki/actions/events.py
from . import action
from ..api import CTX, CFG, get
from colorama import Fore, Style

try:
    from ..utils import save_json, pull_flag, stamp
except Exception:
    def save_json(*a, **k): pass
    def pull_flag(args, flag): return (False, None, args)
    def stamp(p, e): return f"{p}.{e}"


@action("events", "List recent network events", cat="Network")
def events(args):
    """
    events
    events --days 1
    events --mins 60
    events switch
    events switch stp
    events switch port_status
    events mx
    events mx vpn
    events mr

    Show recent network events.
    Options:
      --mins N        Limit to last N minutes (overrides --days).
      --days N        Limit to last N days (default 1).
      switch          Filter to switch-related events.
      mx              Filter to MX (appliance) events.
      mx vpn          Filter to MX VPN connectivity events.
      mr              Filter to wireless AP events.
      stp             Further filter (with switch) to STP events.
      port_status     Further filter (with switch) to port status events.
    """

    nid = CTX.net_id() or CFG.get("default_network_id")
    if not nid:
        print("Select a network first."); return

    jflag, jname, args = pull_flag(args, "--json")

    # --- timespan ---
    mins, days = None, 1
    if "--mins" in args:
        try:
            mins = int(args[args.index("--mins")+1])
        except Exception: pass
    if "--days" in args:
        try:
            days = int(args[args.index("--days")+1])
        except Exception: pass

    timespan = (mins*60) if mins else (days*86400)

    # --- productType ---
    productType = "appliance"
    eventTypes  = []

    if "switch" in args or "sw" in args:
        productType = "switch"
        if "stp" in args: eventTypes.append("stp")
        if "port_status" in args: eventTypes.append("port_status")
    elif "mx" in args:
        productType = "appliance"
        if "vpn" in args: eventTypes.append("vpn_connectivity")
    elif "mr" in args:
        productType = "wireless"

    # --- request loop with pagination ---
    params = {"productType": productType, "timespan": timespan, "perPage": 100}
    rows, page = [], 1
    while True:
        try:
            resp = get(f"/networks/{nid}/events", params=params) or {}
        except Exception as e:
            print(f"Meraki API error: {e}"); return

        # normalize result
        batch = resp.get("events") if isinstance(resp, dict) else resp
        if not batch: break

        rows.extend(batch)
        if len(batch) < params["perPage"]: break  # no next page
        page += 1
        if isinstance(batch[-1], dict) and "eventId" in batch[-1]:
            params["startingAfter"] = batch[-1]["eventId"]
        else:
            break

    # --- results ---
    if not rows:
        print(f"No events found (productType={productType}, timespan={timespan//3600}h).")
        return

    print(Fore.CYAN + f"\nEvents (last {timespan//3600}h, {productType})\n" + Style.RESET_ALL)
    print(Fore.LIGHTBLUE_EX + f"{'Time':19} {'Type':20} {'Device':18} {'Client/Details':30}" + Style.RESET_ALL)

    for ev in rows[:200]:
        when = (ev.get("occurredAt","-").replace("T"," ").replace("Z",""))[:19]
        et   = (ev.get("eventType") or "-")[:20]
        dev  = (ev.get("deviceName") or ev.get("deviceSerial") or "-")[:18]
        cl   = (ev.get("clientDescription") or ev.get("clientMac") or str(ev.get("details")) or "-")
        cl   = str(cl)[:30]
        print(f"{when:19} {et:20} {dev:18} {cl:30}")

    print(f"\nTotal events: {len(rows)}\n")

    if jflag:
        save_json(rows, jname or stamp("events","json"))
