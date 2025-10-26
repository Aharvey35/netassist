# modules/meraki/actions/airmarshal.py
from . import action
from ..api import CTX, get

@action("airmarshal", "List recent Air Marshal scan results (top 20)")
def airmarshal(_args):
    net_id = CTX.net_id()
    if not net_id:
        print("Select a network first.")
        return
    rows = get(f"/networks/{net_id}/wireless/airMarshal", params={"timespan": 7*24*3600}) or []
    if not rows:
        print("No Air Marshal results.")
        return
    print("\nAir Marshal (top 20):")
    for r in rows[:20]:
        ssid = r.get("ssid","<hidden>")
        ch   = ",".join(str(c) for c in (r.get("channels") or []))
        first = r.get("firstSeen","")
        last  = r.get("lastSeen","")
        print(f" - SSID: {ssid}  Channels: {ch}  FirstSeen: {first}  LastSeen: {last}")
    print()
