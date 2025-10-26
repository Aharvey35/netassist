from . import action
from ..api import CTX, get, put

@action("wifi ssids", "List SSIDs (current network)")
def wifi_ssids(_args):
    net_id = CTX.net_id()
    if not net_id:
        print("No network set. Run: setup or use net <id|name>")
        return
    ssids = get(f"/networks/{net_id}/wireless/ssids") or []
    print(f"\n{'#':<3} {'Name':<28} {'Enabled'}")
    for s in ssids:
        print(f"{s.get('number'):<3} {s.get('name',''):<28} {s.get('enabled')}")
    print()

@action("wifi toggle", "Enable/disable an SSID (current network)")
def wifi_toggle(_args):
    net_id = CTX.net_id()
    if not net_id:
        print("No network set. Run: setup or use net <id|name>")
        return
    sid = input("SSID number (0-14): ").strip()
    on = input("Enable? [y/n]: ").strip().lower() == "y"
    res = put(f"/networks/{net_id}/wireless/ssids/{sid}", json_body={"enabled": on})
    print("Updated:", res)
