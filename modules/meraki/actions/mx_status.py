from . import action
from ..api import CTX, get

@action("mx status", "Show MX uplinks for current network")
def mx_status(_args):
    org_id = CTX.org_id()
    net_id = CTX.net_id()
    if not org_id:
        print("No org set. Run: setup or use org <id|name>")
        return
    if not net_id:
        print("No network set. Run: setup or use net <id|name>")
        return

    # Use org-level endpoint and filter by current network
    # Docs: /organizations/{organizationId}/appliance/uplink/statuses
    rows = get(
        f"/organizations/{org_id}/appliance/uplink/statuses",
        params={"networkIds[]": [net_id], "perPage": 1000},
    ) or []

    if not rows:
        print("No MX/Z uplink data returned for this network.")
        return

    # Print uplinks grouped by device
    for r in rows:
        serial = r.get("serial", "-")
        model = r.get("model", "-")
        name = r.get("networkId", net_id)
        print(f"\n{model} ({serial})")
        for u in r.get("uplinks", []) or []:
            iface = u.get("interface")
            status = u.get("status")
            ip = u.get("ip")
            pub = u.get("publicIp")
            gw = u.get("gateway")
            print(f" {iface:<6} {status:<12} ip={ip} gw={gw} public={pub}")
    print()
