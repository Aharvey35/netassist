# modules/meraki/actions/firmware.py
from . import action
from ..api import CTX, CFG, get
from colorama import Fore, Style

try:
    from ..utils import save_json, pull_flag, stamp
except Exception:
    def save_json(*a, **k): pass
    def pull_flag(args, flag): return (False, None, args)
    def stamp(p, e): return f"{p}.{e}"


@action("firmware", "Org + device firmware status (safe, read-only)", cat="Inventory")
def firmware(args):
    """
    firmware
    firmware --json
    """

    org_id = CTX.org_id() or CFG.get("default_org_id")
    if not org_id:
        print("Select an org first."); return

    jflag, jname, args = pull_flag(args, "--json")

    # --------------------- Org-wide jobs log ---------------------
    jobs = []
    try:
        data = get(f"/organizations/{org_id}/firmware/upgrades") or {}
        if isinstance(data, list):
            jobs = data
        elif isinstance(data, dict):
            jobs = data.get("networks") or data.get("items") or []
    except Exception as e:
        print(f"Meraki API error (jobs log): {e}")

    if jobs:
        print(Fore.CYAN + "\nFirmware Jobs (org)\n" + Style.RESET_ALL)
        print(Fore.LIGHTBLUE_EX + f"{'Network':26} {'Product':8} {'Status':12} {'When':20}" + Style.RESET_ALL)
        for j in jobs:
            net = (j.get("name") or j.get("networkName") or j.get("networkId") or "-")[:26]
            prod = (j.get("product") or j.get("productType") or "-")[:8]
            stat = (j.get("status") or j.get("upgradeStatus") or "-").lower()
            when = j.get("scheduledAt") or j.get("time") or j.get("lastRunAt") or "-"
            color = (
                Fore.GREEN if "complete" in stat
                else Fore.YELLOW if "sched" in stat or "queue" in stat
                else Fore.RED
            )
            print(f"{net:26} {prod:8} {color}{stat:12}{Style.RESET_ALL} {when:20}")
    else:
        print(Fore.CYAN + "\nNo firmware jobs found.\n" + Style.RESET_ALL)

    # --------------------- Device-level firmware ---------------------
    devices = []
    try:
        devices = get(f"/organizations/{org_id}/devices") or []
    except Exception as e:
        print(f"Meraki API error (devices): {e}")

    if devices:
        print(Fore.CYAN + "\nDevice Firmware (org)\n" + Style.RESET_ALL)
        print(Fore.LIGHTBLUE_EX + f"{'Name':24} {'Model':12} {'Serial':16} {'Firmware':14} {'Status':10} {'Network':20}" + Style.RESET_ALL)
        for d in devices:
            name   = (d.get("name") or "-")[:24]
            model  = (d.get("model") or "-")[:12]
            serial = (d.get("serial") or "-")[:16]
            fw     = (d.get("firmware") or "-")[:14]
            stat   = (d.get("status") or "-").lower()
            net    = (d.get("networkName") or d.get("networkId") or "-")[:20]

            scolor = Fore.GREEN if stat == "online" else Fore.RED
            print(f"{name:24} {model:12} {serial:16} {fw:14} {scolor}{stat:10}{Style.RESET_ALL} {net:20}")
    else:
        print(Fore.CYAN + "\nNo device inventory data.\n" + Style.RESET_ALL)

    # --------------------- Optional JSON export ---------------------
    if jflag:
        all_data = {"jobs": jobs, "devices": devices}
        save_json(all_data, jname or stamp("firmware","json"))
