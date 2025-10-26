# modules/meraki/actions/admins.py
from . import action
from ..api import CTX, CFG, get
from colorama import Fore, Style

try:
    from ..utils import save_json, pull_flag, stamp
except Exception:
    def save_json(*a, **k): pass
    def pull_flag(args, flag): return (False, None, args)
    def stamp(p, e): return f"{p}.{e}"

@action("admins", "List organization admins", cat="General")
def admins(args):
    """
    admins
    admins --json
    """
    org_id = CTX.org_id() or CFG.get("default_org_id")
    if not org_id:
        print("Select an org first."); return

    jflag, jname, args = pull_flag(args, "--json")

    try:
        rows = get(f"/organizations/{org_id}/admins") or []
    except Exception as e:
        print(f"Meraki API error: {e}"); return

    if not rows:
        print("No admins found."); return

    print(Fore.CYAN + "\nOrganization Admins\n" + Style.RESET_ALL)
    print(Fore.LIGHTBLUE_EX + f"{'Name':28} {'Email':34} {'Role/Org Access':20}" + Style.RESET_ALL)
    for a in rows:
        name  = (a.get("name") or "-")[:28]
        email = (a.get("email") or "-")[:34]
        role  = (a.get("orgAccess") or a.get("role") or "-")[:20]
        print(f"{name:28} {email:34} {role:20}")
    print()

    if jflag:
        save_json(rows, jname or stamp("admins", "json"))
