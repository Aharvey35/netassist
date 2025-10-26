# modules/meraki/actions/net_summary.py
from . import action
from ..api import CTX, CFG, get
from colorama import Fore, Style

@action("net summary", "Network quick facts", cat="Network")
def net_summary(args):
    """
    net summary
    """
    nid = CTX.net_id() or CFG.get("default_network_id")
    if not nid:
        print("Select a network first."); return
    try:
        info = get(f"/networks/{nid}") or {}
    except Exception as e:
        print(f"Meraki API error: {e}"); return

    print(Fore.CYAN + "\nNetwork Summary\n" + Style.RESET_ALL)
    print(f" Name      : {info.get('name','-')}")
    print(f" Type      : {', '.join(info.get('productTypes') or []) or '-'}")
    print(f" Timezone  : {info.get('timeZone','-')}")
    tags = info.get("tags") or []
    if tags: print(f" Tags      : {', '.join(tags)}")
    print()
