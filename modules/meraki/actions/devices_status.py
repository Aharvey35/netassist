# modules/meraki/actions/devices_status.py
from . import action
from ..api import CTX, get

@action("devices status", "List device status for the current network")
def devices_status(_args):
    org_id = CTX.org_id(); net_id = CTX.net_id()
    if not (org_id and net_id):
        print("Select an org/network first: use 'org select' and 'net select'")
        return

    params = {"networkIds[]": [net_id], "perPage": 1000}
    data = get(f"/organizations/{org_id}/devices/statuses", params=params) or []
    # Endpoint may return either a list or an object (future-proof)
    rows = data.get("devices", data) if isinstance(data, dict) else data

    if not rows:
        print("No devices found.")
        return

    print(f"\nDevices in network {CTX.net_name()}:")
    print(f"{'Model':8}  {'Serial':16}  {'Name':28}  {'Status':9}  {'LAN IP':15}  {'Public IP':15}  Last Heard")
    for r in rows:
        model = r.get("model","-")
        serial = r.get("serial","-")
        name = (r.get("name") or r.get("productType") or "-")[:28]
        status = r.get("status","-")
        lan = r.get("lanIp","-")
        pub = r.get("publicIp","-")
        last = r.get("lastReportedAt","-")
        print(f"{model:8}  {serial:16}  {name:28}  {status:9}  {lan:15}  {pub:15}  {last}")
    print()
