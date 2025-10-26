from . import action
from ..api import CTX, get

@action("client find", "Find client by MAC/IP (current network)")
def client_find(_args):
    net_id = CTX.net_id()
    if not net_id:
        print("No network set. Run: setup or use net <id|name>")
        return
    q = input("Enter MAC or IP: ").strip()
    res = get(f"/networks/{net_id}/clients", params={"perPage": 1000})
    matches = []
    for c in (res or []):
        if not isinstance(c, dict):
            continue
        if q.lower() in (str(c.get("mac","")).lower(), str(c.get("ip","")).lower()):
            matches.append(c)
    if not matches:
        print("No match found in recent clients.")
        return
    for m in matches:
        print(f"{m.get('description') or m.get('dhcpHostname') or '-'}  {m.get('mac')}  {m.get('ip')}  {m.get('switchport') or m.get('ssid') or '-'}")
