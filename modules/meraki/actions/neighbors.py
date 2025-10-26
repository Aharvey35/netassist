# modules/meraki/actions/neighbors.py
from . import action
from ..api import CTX, get
from colorama import Fore, Style

@action("neighbors", "Show LLDP/CDP neighbors (serial | --pick | --all)", cat="Inventory & Topology")
def neighbors(args):
    net_id = CTX.net_id()
    if not net_id:
        print("Select a network first."); return

    # Parse args
    mode = "pick" if ("--pick" in args) else ("all" if ("--all" in args) else "auto")
    serial = next((a for a in args if a not in ("--pick","--all")), None)

    # Load devices and choose targets
    devs = get(f"/networks/{net_id}/devices") or []
    switches = [d for d in devs if str(d.get("model","")).startswith(("MS","C9"))]

    if serial:
        targets = [d for d in switches if d.get("serial") == serial]
        if not targets:
            print("No matching switch serial in this network."); return
    elif mode == "all":
        targets = switches
    else:
        # --pick or auto-pick first with a small menu
        if mode == "auto" and switches:
            targets = [sorted(switches, key=lambda d: (not d.get("name"), d.get("name","~")))[0]]
        else:
            for i, d in enumerate(switches, 1):
                print(f" {i}) {d.get('name') or d.get('serial')} [{d.get('model')}]")
            sel = input("Choose switch: ").strip()
            if not sel.isdigit() or not (1 <= int(sel) <= len(switches)):
                print("Canceled."); return
            targets = [switches[int(sel)-1]]

    for sw in targets:
        ser = sw.get("serial"); name = sw.get("name") or ser
        nbrs = get(f"/devices/{ser}/lldpCdp") or {}
        ports = (nbrs.get("ports") or {}) if isinstance(nbrs, dict) else {}

        print(Fore.CYAN + f"\nNeighbors for {name} ({ser}):" + Style.RESET_ALL)
        if not ports:
            print("  No LLDP/CDP neighbors reported."); continue

        for port, info in ports.items():
            l = info.get("lldp", {}); c = info.get("cdp", {})
            peer = l.get("systemName") or c.get("deviceId") or "-"
            mgmt = l.get("managementAddress") or c.get("managementAddress") or ""
            pid  = l.get("portId") or c.get("portId") or ""
            print(f"  {Fore.GREEN}{port:>4}{Style.RESET_ALL}  {peer}  {pid}  {mgmt}")
    print()
