from . import action
from ..api import CTX, list_devices, get, put

def _pick_switch(net_id):
    devs = list_devices(net_id)
    sw = [d for d in devs if d.get("model","").startswith(("MS","C9"))]
    if not sw:
        print("No switches found.")
        return None
    for i, d in enumerate(sw, 1):
        print(f" {i}) {d.get('name') or d['serial']} [{d.get('model')}]")
    sel = input("Choose switch: ").strip()
    if sel.isdigit() and 1 <= int(sel) <= len(sw):
        return sw[int(sel)-1]
    return None

from . import action
from ..api import CTX, list_devices, get, put

def _pick_switch(net_id):
    devs = list_devices(net_id)
    sw = [d for d in devs if d.get("model","").startswith(("MS","C9"))]  # MS or Meraki-Catalyst
    if not sw:
        print("No switches found.")
        return None
    for i, d in enumerate(sw, 1):
        print(f" {i}) {d.get('name') or d['serial']} [{d.get('model')}]")
    sel = input("Choose switch: ").strip()
    if sel.isdigit() and 1 <= int(sel) <= len(sw):
        return sw[int(sel)-1]
    return None

def _clean(s: str) -> str:
    return str(s or "").replace("\n", " ").replace("\r", " ").replace("\t", " ")

def _fit(s: str, width: int) -> str:
    s = _clean(s)
    if len(s) <= width:
        return s
    # keep width (including ellipsis)
    return s[: max(0, width - 1)] + "…"

@action("switch ports", "List ports on a switch (interactive)")
def switch_ports(_args):
    net_id = CTX.net_id()
    if not net_id:
        print("No network set. Run: setup or use net <id|name>")
        return
    sw = _pick_switch(net_id)
    if not sw:
        return
    serial = sw["serial"]
    ports = get(f"/devices/{serial}/switch/ports") or []

    # Wider, fixed widths + clipping for readability
    NAME_W = 28  # increase if you have a very wide terminal
    print(f"\nPorts for {sw.get('name') or serial}:\n")
    print(f"{'Port':>4}  {'Name':<{NAME_W}} {'Enabled':<7} {'Type':<6} {'VLAN':>5} {'Voice':>5} Allowed")
    for p in ports:
        port    = str(p.get("portId", ""))
        name    = _fit(p.get("name") or "", NAME_W)
        enabled = "True" if p.get("enabled") else "False"
        ptype   = p.get("type", "")
        vlan    = str(p.get("vlan") or "-")
        voice   = str(p.get("voiceVlan") or "-")
        allowed = p.get("allowedVlans") if ptype == "trunk" else "-"
        allowed = _fit(str(allowed or "-"), 32)  # clip long VLAN lists

        print(f"{port:>4}  {name:<{NAME_W}} {enabled:<7} {ptype:<6} {vlan:>5} {voice:>5} {allowed}")
    print()


@action("switch set", "Configure a switch port (interactive)")
def switch_set(_args):
    net_id = CTX.net_id()
    if not net_id:
        print("No network set. Run: setup or use net <id|name>")
        return
    sw = _pick_switch(net_id)
    if not sw: return
    serial = sw["serial"]

    port = input("Port number (e.g., 1): ").strip()
    ptype = input("Type [access/trunk] (blank=keep): ").strip()
    vlan = input("Access VLAN (blank=keep): ").strip()
    voice = input("Voice VLAN (blank=keep): ").strip()
    allowed = input("Allowed VLANs (trunk) e.g. '10,20,30' or 'all' (blank=keep): ").strip()
    name = input("Port name (blank=keep): ").strip()
    enabled = input("Enabled? [y/n/blank=keep]: ").strip().lower()

    body = {}
    if ptype in ("access","trunk"): body["type"] = ptype
    if vlan.isdigit(): body["vlan"] = int(vlan)
    if voice.isdigit(): body["voiceVlan"] = int(voice)
    if allowed: body["allowedVlans"] = allowed
    if name: body["name"] = name
    if enabled in ("y","n"): body["enabled"] = (enabled == "y")

    if not body:
        print("Nothing to change.")
        return

    print("\nPlanned update:")
    for k,v in body.items(): print(f" - {k}: {v}")
    if input("Apply? [y/N]: ").strip().lower() != "y":
        print("Aborted.")
        return

    res = put(f"/devices/{serial}/switch/ports/{port}", json_body=body)
    print("Updated:", res)
