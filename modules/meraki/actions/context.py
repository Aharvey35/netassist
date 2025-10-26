# modules/meraki/actions/context.py
from . import action
from ..api import CFG, CTX, resolve_org, resolve_net, list_organizations, list_networks

def _pick_org():
    orgs = list_organizations()
    if not orgs:
        print("No organizations available.")
        return None
    print("\nOrganizations:")
    for i, o in enumerate(orgs, 1):
        print(f" {i}) {o.get('name')} ({o.get('id')})")
    sel = input("Choose org by number: ").strip()
    if sel.isdigit() and 1 <= int(sel) <= len(orgs):
        return orgs[int(sel)-1]
    return None

def _pick_net(org_id):
    nets = list_networks(org_id)
    if not nets:
        print("No networks in this org.")
        return None
    print("\nNetworks:")
    for i, n in enumerate(nets, 1):
        print(f" {i}) {n.get('name')} ({n.get('id')})")
    sel = input("Choose network by number: ").strip()
    if sel.isdigit() and 1 <= int(sel) <= len(nets):
        return nets[int(sel)-1]
    return None

@action("use org", "Switch current org (session-only; add --save to persist)")
def use_org(args):
    """
    use org <id|name> [--save]
    (no args) -> interactive picker
    """
    save = any(a == "--save" for a in args)
    key = next((a for a in args if not a.startswith("--")), None)

    if key:
        org_id, org_name = resolve_org(key)
        if not org_id:
            print("Org not found. Try exact id or name.")
            return
    else:
        o = _pick_org()
        if not o: return
        org_id, org_name = o.get("id"), o.get("name")

    CTX.set_org(org_id, org_name, clear_net=True)
    print(f"Current org → {CTX.org_name()} ({CTX.org_id()}); current network cleared.")

    if save:
        CFG.set("default_org_id", org_id)
        CFG.set("default_org_name", org_name)
        CFG.set("default_network_id", "")
        CFG.set("default_network_name", "")
        print("Saved as new defaults (network default cleared).")

@action("use net", "Switch current network (session-only; add --save to persist)")
def use_net(args):
    """
    use net <id|name> [--save]
    (no args) -> interactive picker in current org
    """
    save = any(a == "--save" for a in args)
    key = next((a for a in args if not a.startswith("--")), None)

    org_id = CTX.org_id()
    if not org_id:
        print("No org set. Run: setup or use org first.")
        return

    if key:
        net_id, net_name = resolve_net(org_id, key)
        if not net_id:
            print("Network not found in current org.")
            return
    else:
        n = _pick_net(org_id)
        if not n: return
        net_id, net_name = n.get("id"), n.get("name")

    CTX.set_net(net_id, net_name)
    print(f"Current network → {CTX.net_name()} ({CTX.net_id()})")

    if save:
        CFG.set("default_network_id", net_id)
        CFG.set("default_network_name", net_name)
        print("Saved as new defaults.")

@action("ctx", "Show session context and defaults")
def ctx_show(_args):
    cfg = CFG.as_dict()
    print("\n=== Session ===")
    print(f" Org    : {CTX.org_name()} ({CTX.org_id()})")
    print(f" Network: {CTX.net_name()} ({CTX.net_id()})")
    print("\n=== Defaults ===")
    print(f" Org    : {cfg.get('default_org_name')} ({cfg.get('default_org_id')})")
    print(f" Network: {cfg.get('default_network_name')} ({cfg.get('default_network_id')})\n")

@action("reset ctx", "Clear session overrides (revert to defaults)")
def ctx_reset(_args):
    CTX.reset()
    print("Session context cleared. Now using defaults.")
