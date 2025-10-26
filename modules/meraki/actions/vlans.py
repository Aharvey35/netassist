from . import action
from ..api import CTX, get, post

@action("vlan list", "List appliance VLANs (current network)")
def vlan_list(_args):
    net_id = CTX.net_id()
    if not net_id:
        print("No network set. Run: setup or use net <id|name>")
        return
    vlans = get(f"/networks/{net_id}/appliance/vlans") or []
    print(f"\nVLANs for {net_id}:\n")
    print(f"{'ID':<8} {'Name':<20} {'Subnet':<18} {'Appliance IP'}")
    for v in vlans:
        print(f"{v.get('id'):<8} {v.get('name',''):<20} {v.get('subnet',''):<18} {v.get('applianceIp','')}")
    print()

@action("vlan add", "Create an appliance VLAN in current network")
def vlan_add(_args):
    net_id = CTX.net_id()
    if not net_id:
        print("No network set. Run: setup or use net <id|name>")
        return
    vid = input("VLAN ID: ").strip()
    name = input("Name: ").strip()
    subnet = input("Subnet (CIDR): ").strip()
    gw = input("Appliance IP (in subnet): ").strip()

    body = {"id": vid, "name": name, "subnet": subnet, "applianceIp": gw}
    res = post(f"/networks/{net_id}/appliance/vlans", json_body=body)
    print("Created:", res)
