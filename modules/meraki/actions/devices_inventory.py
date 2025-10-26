# modules/meraki/actions/devices_inventory.py
from . import action
from ..api import CTX, CFG, get
from colorama import Fore, Style

try:
    from ..utils import save_json, save_csv, pull_flag, stamp
except Exception:
    def save_json(*a, **k): pass
    def save_csv(*a, **k): pass
    def pull_flag(args, flag): return (False, None, args)
    def stamp(p, e): return f"{p}.{e}"

def _kind(model: str) -> str:
    m = (model or "").upper()
    if m.startswith(("MX","Z")): return "mx"
    if m.startswith(("MS","MG")): return "switch" if m.startswith("MS") else "cell"
    if m.startswith(("MR","CW")): return "ap"
    if m.startswith(("MV","MT")): return "cam" if m.startswith("MV") else "sensor"
    return "other"

@action("devices inv", "Org device inventory", cat="Inventory")
def devices_inv(args):
    """
    devices inv
    devices inv --type mx|switch|ap|cam|sensor
    devices inv --json | --csv
    """
    org_id = CTX.org_id() or CFG.get("default_org_id")
    if not org_id:
        print("Select an org first."); return

    jflag, jname, args = pull_flag(args, "--json")
    cflag, cname, args = pull_flag(args, "--csv")

    want = None
    if args and args[0] == "--type" and len(args) > 1:
        want = args[1].lower()

    params = {"perPage": 300}
    try:
        rows = get(f"/organizations/{org_id}/devices/statuses", params=params) or []
    except Exception as e:
        if "perPage" in str(e):
            rows = get(f"/organizations/{org_id}/devices/statuses") or []
        else:
            print(f"Meraki API error: {e}"); return

    items = rows if isinstance(rows, list) else (rows.get("items") or [])
    if want:
        items = [d for d in items if _kind(d.get("model")) == want]

    if not items:
        print("No devices found."); return

    print(Fore.CYAN + "\nDevice Inventory (org)\n" + Style.RESET_ALL)
    print(Fore.LIGHTBLUE_EX + f"{'Network':24} {'Name':22} {'Model':8} {'Serial':14} {'Status':10} {'LAN IP':15}" + Style.RESET_ALL)
    out = []
    for d in items[:1200]:
        net   = (d.get("networkName") or "-")[:24]
        name  = (d.get("name") or d.get("productType") or "-")[:22]
        model = (d.get("model") or "-")[:8]
        ser   = (d.get("serial") or "-")[:14]
        stat  = (d.get("status") or "-").lower()
        ip    = (d.get("lanIp") or d.get("ipv4") or "-")[:15]
        color = Fore.GREEN if stat == "online" else (Fore.YELLOW if stat == "alerting" else Fore.RED)
        print(f"{net:24} {name:22} {model:8} {ser:14} {color}{stat:10}{Style.RESET_ALL} {ip:15}")
        out.append({"network":net,"name":name,"model":model,"serial":ser,"status":stat,"lanIp":ip})

    print()
    if jflag: save_json(items, jname or stamp("devices-inv", "json"))
    if cflag: save_csv(out, ["network","name","model","serial","status","lanIp"], cname or stamp("devices-inv","csv"))
