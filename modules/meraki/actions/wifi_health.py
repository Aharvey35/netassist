# modules/meraki/actions/wifi_health.py
from . import action
from ..api import CTX, get

@action("wifi health", "Wi-Fi connection success vs failures over the last N hours (default 24)")
def wifi_health(args):
    net_id = CTX.net_id()
    if not net_id:
        print("Select a network first.")
        return
    hours = int(args[0]) if (args and args[0].isdigit()) else 24
    timespan = min(max(hours,1), 168) * 3600  # API cap 7 days
    stats = get(f"/networks/{net_id}/wireless/connectionStats", params={"timespan": timespan}) or {}
    print(f"\nWireless connection stats (last {hours}h):")
    print(f"  Assoc failures : {stats.get('assoc',0)}")
    print(f"  Auth failures  : {stats.get('auth',0)}")
    print(f"  DHCP failures  : {stats.get('dhcp',0)}")
    print(f"  DNS failures   : {stats.get('dns',0)}")
    print(f"  Success        : {stats.get('success',0)}\n")
