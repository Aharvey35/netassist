# NetAssist Meraki — L2/L3 lookups
# Commands provided:
#   show arp
#   show mac address        (alias: show mac address-table)
#   client find <mac|ip>
#
# Notes:
# - Works for MS (switch) and MX (appliance) ARP via Live Tools.
# - If MX Live Tools ARP isn’t available, falls back to recent clients.
# - Auto-heals NETWORK_ID from current prompt context to avoid “No network selected”.

from __future__ import annotations
import time, re
from typing import Dict, List, Any, Optional

# Core API wrapper (your existing module)
from .. import api as API

# ---- utils (use your existing ones; provide light fallbacks if missing) ----
try:
    from ..utils import save_csv, save_json, pull_flag, human_duration
except Exception:
    def save_csv(rows, path: str):
        import csv
        if not rows:
            return
        # union of all keys, stable-ish order
        keys = list({k for r in rows for k in r.keys()})
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(rows)

    def save_json(rows, path: str):
        import json
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)

    def pull_flag(args, name: str, default=None):
        a = list(args)
        if name in a:
            i = a.index(name)
            try:
                v = a[i + 1]
                # remove pair from list (callers pass *args, so we just return the value)
                return v
            except Exception:
                return default
        return default

    def human_duration(s):
        try:
            s = float(s)
            if s < 60:
                return f"{s:.1f}s"
            m = int(s // 60)
            r = int(s % 60)
            return f"{m}m{r:02d}s"
        except Exception:
            return str(s)

# pad() may not exist in older utils.py; provide a safe fallback
try:
    from ..utils import pad  # type: ignore
except Exception:
    def pad(s, w: int) -> str:
        s = "" if s is None else str(s)
        return (s[:w]).ljust(w)

# Optional action registrar (decorator or function depending on your build)
try:
    from . import action
except Exception:
    action = None  # we’ll no-op if not present; commands will still be callable directly

get = API.get
post = API.post

COLS = {"ip": 16, "mac": 18, "vlan": 6, "switch": 18, "port": 8, "age": 19}

# ----------------- helpers -----------------
def _poll_job(getter, timeout_s: int = 20, interval_s: float = 1.0) -> Dict[str, Any]:
    t0 = time.time()
    last = {}
    while True:
        last = getter() or {}
        st = last.get("status")
        if st in ("complete", "failed"):
            return last
        if time.time() - t0 > timeout_s:
            last["error"] = f"timeout after {human_duration(time.time() - t0)} (status={st})"
            return last
        time.sleep(interval_s)

def _devices_in_network(net_id: str) -> List[Dict[str, Any]]:
    return get(f"/networks/{net_id}/devices") or []

def _ms_switches(devs): 
    return [d for d in devs if str(d.get("model", "")).upper().startswith("MS")]

def _mx_appliances(devs):
    out = []
    for d in devs:
        m = str(d.get("model", "")).upper()
        if m.startswith("MX") or m.startswith("VMX"):
            out.append(d)
    return out

def _device_name(d): 
    return d.get("name") or d.get("serial") or d.get("model") or "device"

def _resolve_device_name(serial: str, cache: Dict[str, str], net_devs: List[Dict[str, Any]]) -> str:
    if not serial:
        return ""
    if serial in cache:
        return cache[serial]
    for d in net_devs:
        if d.get("serial") == serial:
            cache[serial] = _device_name(d)
            return cache[serial]
    try:
        info = get(f"/devices/{serial}") or {}
        cache[serial] = info.get("name") or info.get("serial") or "device"
        return cache[serial]
    except Exception:
        return serial

def _print_header(headers):
    line = "  ".join(pad(h, w) for h, w in headers)
    print(line)
    print("-" * len(line))

def _fmt_age(ts):
    if not ts:
        return ""
    try:
        return ts.replace("T", " ")[:19]
    except Exception:
        return ts

def _ensure_network_id() -> Optional[str]:
    """
    Self-heal NETWORK_ID using org + network name from CTX if needed.
    Avoids 'No network selected' when the prompt already shows a network.
    """
    if getattr(API.CTX, "NETWORK_ID", None):
        return API.CTX.NETWORK_ID

    org_id = getattr(API.CTX, "ORG_ID", None)
    net_name = getattr(API.CTX, "NETWORK_NAME", None)

    if org_id and net_name:
        try:
            nets = API.list_networks(org_id) or []
            hit = next((n for n in nets if n.get("name") == net_name or n.get("id") == net_name), None)
            if hit:
                API.CTX.NETWORK_ID = hit.get("id")
                API.CTX.NETWORK_NAME = hit.get("name") or net_name
                return API.CTX.NETWORK_ID
        except Exception:
            pass

    # fallback to config default if present
    try:
        def_id = API.CFG.get("default_network_id")
        if def_id:
            API.CTX.NETWORK_ID = def_id
            return def_id
    except Exception:
        pass
    return None

# ----------------- show arp -----------------
def show_arp(*args):
    """
    show arp  [--device <serial|name>]  [--save]
      • MS: Live Tools ARP per switch
      • MX: Live Tools ARP; fallback to recent clients if live tools unavailable
    """
    net_id = _ensure_network_id()
    if not net_id:
        print("No network selected. Use 'use org <name>' then 'use net <name>' and try again.")
        return

    dev_filter = pull_flag(args, "--device", None)
    want_save  = any(f in args for f in ("--save", "--csv", "--json"))

    devices = _devices_in_network(net_id)
    if dev_filter:
        f = str(dev_filter).lower()
        devices = [
            d for d in devices
            if f in (_device_name(d) or "").lower() or f in str(d.get("serial", "")).lower()
        ]
        if not devices:
            print(f"No device matches '{dev_filter}'.")
            return

    ms_list = _ms_switches(devices)
    mx_list = _mx_appliances(devices)
    rows: List[Dict[str, Any]] = []

    # MS switches
    for sw in ms_list:
        serial = sw["serial"]; sw_name = _device_name(sw)
        try:
            job = post(f"/devices/{serial}/liveTools/arpTable", json={}) or {}
            jid = job.get("arpTableId")
            if not jid:
                print(f"[{sw_name}] ARP job failed (no id)")
                continue
            res = _poll_job(lambda: get(f"/devices/{serial}/liveTools/arpTable/{jid}"))
            if res.get("status") != "complete":
                print(f"[{sw_name}] ARP job not complete: {res.get('status')} {res.get('error', '')}")
                continue
            for e in res.get("entries", []) or []:
                rows.append({
                    "ip": e.get("ip"),
                    "mac": e.get("mac"),
                    "vlan": e.get("vlanId"),
                    "switch": sw_name,
                    "port": "",
                    "age": _fmt_age(e.get("lastUpdatedAt")),
                })
        except Exception as ex:
            print(f"[{sw_name}] ARP fetch error: {ex}")

    # MX appliances
    for mx in mx_list:
        serial = mx["serial"]; mx_name = _device_name(mx)
        did_live = False
        try:
            job = post(f"/devices/{serial}/liveTools/arpTable", json={}) or {}
            jid = job.get("arpTableId")
            if jid:
                did_live = True
                res = _poll_job(lambda: get(f"/devices/{serial}/liveTools/arpTable/{jid}"))
                if res.get("status") == "complete":
                    for e in res.get("entries", []) or []:
                        rows.append({
                            "ip": e.get("ip"),
                            "mac": e.get("mac"),
                            "vlan": e.get("vlanId"),
                            "switch": mx_name,
                            "port": "",
                            "age": _fmt_age(e.get("lastUpdatedAt")),
                        })
        except Exception:
            pass

        if not did_live:
            # fallback: approximate from recent clients (best-effort)
            try:
                clients = get(
                    f"/networks/{net_id}/clients",
                    params={"perPage": 1000, "timespan": 86400}
                ) or []
                for c in clients:
                    if c.get("recentDeviceSerial") == serial and c.get("ip") and c.get("mac"):
                        rows.append({
                            "ip": c.get("ip"),
                            "mac": c.get("mac"),
                            "vlan": c.get("vlan"),
                            "switch": mx_name,
                            "port": c.get("switchport") or "",
                            "age": "",
                        })
            except Exception as ex:
                print(f"[{mx_name}] fallback (clients) error: {ex}")

    if not rows:
        print("No ARP entries found.")
        return

    headers = [
        ("IP", COLS["ip"]),
        ("MAC", COLS["mac"]),
        ("VLAN", COLS["vlan"]),
        ("Device", COLS["switch"]),
        ("Port", COLS["port"]),
        ("LastSeen", COLS["age"]),
    ]
    _print_header(headers)
    for r in rows:
        print("  ".join([
            pad(r.get("ip", ""), COLS["ip"]),
            pad(r.get("mac", ""), COLS["mac"]),
            pad(str(r.get("vlan", "") or ""), COLS["vlan"]),
            pad(r.get("switch", ""), COLS["switch"]),
            pad(str(r.get("port", "") or ""), COLS["port"]),
            pad(r.get("age", ""), COLS["age"]),
        ]))

    if want_save:
        save_csv(rows, "show_arp.csv")
        save_json(rows, "show_arp.json")
        print("\nSaved to show_arp.csv / show_arp.json")

# ----------------- show mac address -----------------
def show_mac_address(*args):
    """
    show mac address  [--device <serial|name>]  [--save]
      • Pulls MS Live Tools MAC/CAM tables across switches.
    """
    net_id = _ensure_network_id()
    if not net_id:
        print("No network selected. Use 'use net <name>' first.")
        return

    dev_filter = pull_flag(args, "--device", None)
    want_save  = any(f in args for f in ("--save", "--csv", "--json"))

    devices = _devices_in_network(net_id)
    if dev_filter:
        f = str(dev_filter).lower()
        devices = [
            d for d in devices
            if f in (_device_name(d) or "").lower() or f in str(d.get("serial", "")).lower()
        ]
        if not devices:
            print(f"No device matches '{dev_filter}'.")
            return

    ms_list = _ms_switches(devices)
    if not ms_list:
        print("No MS switches found in this network.")
        return

    rows = []
    for sw in ms_list:
        serial = sw["serial"]; sw_name = _device_name(sw)
        try:
            job = post(f"/devices/{serial}/liveTools/macTable", json={}) or {}
            jid = job.get("macTableId")
            if not jid:
                print(f"[{sw_name}] MAC-table job failed (no id)")
                continue
            res = _poll_job(lambda: get(f"/devices/{serial}/liveTools/macTable/{jid}"))
            if res.get("status") != "complete":
                print(f"[{sw_name}] MAC-table job not complete: {res.get('status')} {res.get('error', '')}")
                continue
            for e in res.get("entries", []) or []:
                rows.append({
                    "switch": sw_name,
                    "port": e.get("port"),
                    "vlan": e.get("vlanId"),
                    "mac": e.get("mac"),
                })
        except Exception as ex:
            print(f"[{sw_name}] MAC-table fetch error: {ex}")

    if not rows:
        print("No MAC entries found.")
        return

    headers = [("Switch", COLS["switch"]), ("Port", COLS["port"]), ("VLAN", COLS["vlan"]), ("MAC", COLS["mac"])]
    _print_header(headers)
    for r in rows:
        print("  ".join([
            pad(r.get("switch", ""), COLS["switch"]),
            pad(str(r.get("port", "") or ""), COLS["port"]),
            pad(str(r.get("vlan", "") or ""), COLS["vlan"]),
            pad(r.get("mac", ""), COLS["mac"]),
        ]))

    if want_save:
        save_csv(rows, "mac_address_table.csv")
        save_json(rows, "mac_address_table.json")
        print("\nSaved to mac_address_table.csv / mac_address_table.json")

# ----------------- client find (enhanced) -----------------
def client_find(*args):
    """
    client find <mac|ip|hostname>  [--timespan <seconds>]
      → Shows device + exact switchport when available.
    """
    net_id = _ensure_network_id()
    if not net_id:
        print("No network selected. Use 'use net <name>' first.")
        return

    if not args:
        print("Usage: client find <mac|ip|hostname> [--timespan <seconds>]")
        return

    q = None
    timespan = int(pull_flag(args, "--timespan", 86400) or 86400)
    for a in args:
        if not str(a).startswith("--"):
            q = a
            break
    if not q:
        print("Provide a MAC or IP to search.")
        return

    q_is_mac = bool(re.match(r"^([0-9a-f]{2}[:-]){5}[0-9a-f]{2}$", str(q).lower()))
    q_is_ip  = bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", str(q)))

    params = {"perPage": 1000, "timespan": timespan}
    if q_is_mac:
        params["mac"] = q
    elif q_is_ip:
        params["ip"] = q
    else:
        params["mac"] = q  # best-effort

    clients = get(f"/networks/{net_id}/clients", params=params) or []
    if not clients:
        print("No clients matched.")
        return

    # prefer exact match if present
    c0 = next(
        (c for c in clients if (q_is_mac and c.get("mac", "").lower() == str(q).lower()) or (q_is_ip and c.get("ip") == q)),
        clients[0]
    )

    # enrich from detail endpoint if we have an ID
    cid = c0.get("id")
    if cid:
        try:
            c0 = get(f"/networks/{net_id}/clients/{cid}") or c0
        except Exception:
            pass

    dev_serial = c0.get("recentDeviceSerial") or c0.get("recentDevice") or c0.get("deviceSerial")
    switchport = c0.get("switchport")

    net_devs = _devices_in_network(net_id)
    dev_name = next((d.get("name") for d in net_devs if d.get("serial") == dev_serial and d.get("name")), None)
    if not dev_name:
        dev_name = _resolve_device_name(dev_serial, {}, net_devs)

    print(f"Client: {c0.get('description') or c0.get('dhcpHostname') or ''}  ({c0.get('mac')})")
    print(f"IP: {c0.get('ip')}   VLAN: {c0.get('vlan')}   Manufacturer: {c0.get('manufacturer') or ''}")
    print(f"Seen: {c0.get('lastSeen') or ''}   Usage: {c0.get('usage', '')}\n")
    print("Attachment:")
    print("  Device : ", dev_name, f"({dev_serial})" if dev_serial else "")
    print("  Port   : ", switchport or "(unknown)")
    if not switchport and dev_serial:
        print("\nTip: run 'switch ports' and filter for the device above to investigate live port status.")

# ----------------- self-registration -----------------
def _register_actions():
    if not action:
        return
    # Try decorator-style first (action(name, desc) -> decorator)
    try:
        action("show arp", "Network ARP: MS Live Tools + MX fallback")(lambda *a, **k: show_arp(*a))
        action("show mac address", "Switch CAM table via MS Live Tools")(lambda *a, **k: show_mac_address(*a))
        action("show mac address-table", "Alias for 'show mac address'")(lambda *a, **k: show_mac_address(*a))
        action("client find", "Locate client and show device + port")(lambda *a, **k: client_find(*a))
        return
    except TypeError:
        pass
    # Fall back to function registration: action(name, desc, fn, aliases=[...])
    try:
        action("show arp", "Network ARP: MS Live Tools + MX fallback", show_arp, aliases=["arp"])
        action("show mac address", "Switch CAM table via MS Live Tools", show_mac_address,
               aliases=["show mac", "mac address-table", "show mac address-table"])
        action("client find", "Locate client and show device + port", client_find, aliases=[])
    except Exception:
        # If loader expects a different API, ignore — commands remain import-callable
        pass

_register_actions()
