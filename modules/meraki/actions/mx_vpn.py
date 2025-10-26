# modules/meraki/actions/mx_vpn.py
from . import action
from ..api import CTX, get
from colorama import Fore, Style

@action("mx vpn", "Show site-to-site VPN status for the current network", cat="MX & WAN")
def mx_vpn(args):
    """
    Usage:
      mx vpn           -> current network
      mx vpn --all     -> org-wide (every network)
    """
    org_id = CTX.org_id()
    net_id = CTX.net_id()
    if not org_id:
        print("Select an org first."); return
    org_wide = "--all" in args

    # 1) Pull status (cap perPage at 300; retry w/o perPage on strict APIs)
    def fetch_status(params):
        try:
            rows = get(f"/organizations/{org_id}/appliance/vpn/statuses", params=params) or []
            return rows
        except Exception as e:
            if "perPage" in str(e):
                # retry without perPage
                p2 = dict(params); p2.pop("perPage", None)
                return get(f"/organizations/{org_id}/appliance/vpn/statuses", params=p2) or []
            raise

    params = {"perPage": 300}
    if not org_wide:
        if not net_id:
            print("Select a network first."); return
        params["networkIds[]"] = [net_id]

    rows = fetch_status(params)

    # Normalize to list
    if isinstance(rows, dict):
        rows = rows.get("vpnstatusentities", rows.get("items", [])) or []
    if not isinstance(rows, list) or not rows:
        print("No VPN status available."); return

    # 2) Enrich 3rd-party peers with IPs from config (if missing)
    config_peers = {}
    try:
        cfg = get(f"/organizations/{org_id}/appliance/vpn/thirdPartyVPNPeers") or []
        peers_list = cfg if isinstance(cfg, list) else (cfg.get("peers") or [])
        for p in peers_list:
            name = (p.get("name") or "").strip()
            rid  = (p.get("remoteId") or "").strip()
            pip  = p.get("publicIp") or p.get("ip") or p.get("publicIpAddress")
            if pip:
                if name: config_peers[("name", name.lower())] = pip
                if rid:  config_peers[("rid", rid.lower())]   = pip
    except Exception:
        pass  # enrichment is best-effort

    # 3) Render
    title = "Org-wide Site-to-Site VPN Status" if org_wide else "Site-to-Site VPN Status"
    print(Fore.CYAN + f"\n{title}:\n" + Style.RESET_ALL)

    def peer_ip_from_config(name, rid):
        if name:
            v = config_peers.get(("name", name.lower()))
            if v: return v
        if rid:
            v = config_peers.get(("rid", rid.lower()))
            if v: return v
        return "-"

    # If org-wide, group by network for readability
    for n in rows:
        net_name = n.get("networkName") or "-"
        serial   = n.get("deviceSerial") or "-"
        dev_stat = (n.get("deviceStatus") or "-").lower()
        vpn_mode = n.get("vpnMode") or "-"
        color = Fore.GREEN if dev_stat == "online" else (Fore.YELLOW if dev_stat == "alerting" else Fore.RED)

        if org_wide:
            print(Fore.LIGHTBLUE_EX + f"\n[{net_name}] {serial}" + Style.RESET_ALL)
        print(f"Mode: {vpn_mode}  Status: {color}{dev_stat}{Style.RESET_ALL}")

        # Uplinks
        ups = n.get("uplinks") or []
        if ups:
            print("  Uplinks:")
            for u in ups:
                print(f"    - {u.get('interface','?'):<6} {u.get('publicIp','-')}")

        # Meraki AutoVPN peers
        peers_mx = n.get("merakiVpnPeers") or []
        if peers_mx:
            print("  Meraki Peers:")
            for p in peers_mx:
                r = (p.get("reachability","-") or "-").lower()
                c = Fore.GREEN if r == "reachable" else Fore.RED
                print(f"    - {p.get('networkName','?')}: {c}{r}{Style.RESET_ALL}")

        # 3rd-party peers (with IP enrichment)
        peers_3p = n.get("thirdPartyVpnPeers") or []
        if peers_3p:
            print("  3rd-Party Peers:")
            for p in peers_3p:
                r = (p.get("reachability","-") or "-").lower()
                c = Fore.GREEN if r == "reachable" else Fore.RED
                name = (p.get("name") or p.get("publicIp") or p.get("ip") or "?").strip()
                rid  = (p.get("remoteId") or "").strip()
                ip   = (p.get("publicIp") or p.get("ip") or p.get("publicIpAddress")) or peer_ip_from_config(name, rid)
                subs = p.get("remoteSubnets") or []
                sub_str = (", ".join(subs))[:60] if subs else ""
                extra = f"  id:{rid}" if rid else ""
                if sub_str:
                    extra += f"  subnets:{sub_str}"
                print(f"    - {name:24} {ip:15} {c}{r}{Style.RESET_ALL}{('  '+extra) if extra else ''}")
    print()
