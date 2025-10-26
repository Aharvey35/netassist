# modules/meraki/actions/license.py
from . import action
from ..api import CTX, CFG, get
from ..utils import save_json, pull_flag, stamp
from colorama import Fore, Style

@action("license", "Organization license overview", cat="General")
def license_overview(args):
    org_id = CTX.org_id() or CFG.get("default_org_id")
    if not org_id:
        print("Select an org first."); return

    jflag, jname, args = pull_flag(args, "--json")   # optional export
    try:
        info = get(f"/organizations/{org_id}/licenses/overview") or {}
    except Exception as e:
        print(f"Meraki API error: {e}"); return

    status = (info.get("status") or "-").lower()
    color  = Fore.GREEN if status in ("ok","active","good") else (Fore.YELLOW if status in ("warning","expiring") else Fore.RED)
    exp    = info.get("expirationDate") or "-"

    print(Fore.CYAN + "\nLicense Overview\n" + Style.RESET_ALL)
    print(f" Status   : {color}{status}{Style.RESET_ALL}")
    print(f" Expires  : {exp}")

    ldc = info.get("licensedDeviceCounts") or {}
    if ldc:
        print("\n Licensed device counts:")
        for k, v in ldc.items():
            print(f"  - {k}: {v}")

    states = info.get("states") or {}
    if states:
        print("\n Per-device-licensing states:")
        for k, block in states.items():
            c = (block or {}).get("count", 0)
            print(f"  - {k}: {c}")

    print()
    if jflag:
        save_json(info, jname or stamp("license", "json"))
