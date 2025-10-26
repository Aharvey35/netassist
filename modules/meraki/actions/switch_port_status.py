# modules/meraki/actions/switch_port_status.py
from . import action
from ..api import CTX, get

def _pick_switch(net_id, preferred_serial=None):
    devs = get(f"/networks/{net_id}/devices") or []
    sw = [d for d in devs if (d.get("model","").startswith("MS") or d.get("model","").startswith("C9"))]
    if preferred_serial:
        for d in sw:
            if d.get("serial") == preferred_serial:
                return d
    if not sw:
        return None
    # Prefer a named/core switch if present
    sw.sort(key=lambda d: (not d.get("name"), d.get("name","~"), d.get("serial","~")))
    return sw[0]

@action(
    "switch port status",
    "Show live port status/PoE/clients for a switch (optional: serial)",
    cat="Switching",
    aliases=["switch ports status", "switch status"]
)
def switch_port_status(args):
    net_id = CTX.net_id()
    if not net_id:
        print("Select a network first.")
        return

    serial = args[0] if args else None
    sw = _pick_switch(net_id, serial)
    if not sw:
        print("No switches found in this network.")
        return

    serial = sw.get("serial")
    name = sw.get("name") or serial
    ports = get(f"/devices/{serial}/switch/ports/statuses", params={"timespan": 24*3600}) or []

    print(f"\nSwitch: {name} ({serial})  Ports: {len(ports)}")
    print(f"{'Port':>4}  {'Status':12} {'Speed':8} {'Duplex':6} {'PoE':3} {'Clients':7}  {'CDP/LLDP peer':30}")
    for p in ports:
        port = str(p.get("portId","?"))
        status = p.get("status","-")
        speed  = p.get("speed","")
        duplex = p.get("duplex","")
        poe    = "Y" if (p.get("poe") or {}).get("isAllocated") else ""
        ccnt   = p.get("clientCount",0)
        # Prefer LLDP, fall back to CDP
        nbr = p.get("lldp") or p.get("cdp") or {}
        peer = nbr.get("systemName") or nbr.get("deviceId") or ""
        peer_port = nbr.get("portId") or ""
        peer_s = f"{peer} {peer_port}".strip()
        print(f"{port:>4}  {status:12} {speed:8} {duplex:6} {poe:3} {ccnt!s:7}  {peer_s[:30]}")
    print()
