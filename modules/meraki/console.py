# modules/meraki/console.py
from typing import List
import re
import os, datetime
from textwrap import dedent

# Core Meraki context/config + lookups used for completion
from .api import CFG, CTX, list_organizations, list_networks

# Action registry (autoloaded below)
from .actions import REGISTRY, list_actions
from . import actions as actions_pkg  # for dynamic autoload

# Colors
from colorama import Fore, Style

# Tab completion (Windows: pip install pyreadline3)
try:
    import readline  # type: ignore
except Exception:
    readline = None


# -----------------------------------------------------------------------------
# Pretty helpers
# -----------------------------------------------------------------------------
BOX_W = 56  # banner width

def _fit(s: str, width: int) -> str:
    s = (s or "").replace("\n", " ").replace("\r", " ").strip()
    return s if len(s) <= width else (s[: max(0, width - 1)] + "…")

def _banner(title: str) -> str:
    pad = max(0, BOX_W - 2)
    top = "╔" + "═" * pad + "╗"
    bot = "╚" + "═" * pad + "╝"
    t = _fit(title, BOX_W - 4)
    left = (BOX_W - 2 - len(t)) // 2
    right = BOX_W - 2 - len(t) - left
    mid = "║" + " " * left + t + " " * right + "║"
    return f"{Fore.CYAN}{top}\n{mid}\n{bot}{Style.RESET_ALL}"

_KEEP_PAREN = re.compile(r"\(interactive\)", flags=re.IGNORECASE)
_STRIP_PAREN = re.compile(r"\([^)]*\)")

def _clean_desc(desc: str) -> str:
    if not desc:
        return ""
    kept = []
    last = 0
    for m in _KEEP_PAREN.finditer(desc):
        pre = desc[last:m.start()]
        pre = _STRIP_PAREN.sub("", pre)
        kept.append(pre)
        kept.append(m.group(0))
        last = m.end()
    tail = _STRIP_PAREN.sub("", desc[last:])
    kept.append(tail)
    return " ".join(" ".join(kept).split())


# -----------------------------------------------------------------------------
# Autoload actions
# -----------------------------------------------------------------------------
def _autoload_actions():
    import importlib, pkgutil
    for m in pkgutil.iter_modules(actions_pkg.__path__):
        if m.ispkg or m.name.startswith("_"):
            continue
        modname = f"{actions_pkg.__name__}.{m.name}"
        if modname in globals():
            continue
        try:
            importlib.import_module(modname)
        except Exception as e:
            print(f"[action load skip] {m.name}: {e}")


# -----------------------------------------------------------------------------
# Help system (reorganized categories)
# -----------------------------------------------------------------------------
_HIDE_FROM_HELP = {"switch port status","switch ports status","switch status"}

# Reorganized block: Org & Admin vs Session & Context
_CATS = {
    "Org & Admin": {
        "setup","license","whoami","use org","use net","orgs","nets","overview"
    },
    "Session & Context": {
        "ctx","reset ctx"
    },
    "Network": {
        "airmarshal","client find","devices status","events","mx status","mx vpn",
        "neighbors","switch ports","vlan list","wan health","wifi health","wifi ssids"
    },
    "Configure": {"switch set","vlan add","wifi toggle"},
    "Inventory": {"overview","nets","orgs"},
}

_HDR_COLOR = Fore.LIGHTBLUE_EX

def _get_action_meta():
    acts = list_actions()
    reg_keys = set(REGISTRY.keys())
    return acts, reg_keys

def _resolve_action_name(tokens):
    key2 = " ".join(tokens[:2]).strip().lower()
    key1 = tokens[0].strip().lower() if tokens else ""
    if key2 in REGISTRY: return key2
    if key1 in REGISTRY: return key1
    acts, _ = _get_action_meta()
    cands = [k for k in acts.keys() if k.startswith(key2) or k.startswith(key1)]
    if len(cands) == 1:
        return cands[0]
    return None

def _print_action_help(tokens):
    name = _resolve_action_name(tokens)
    if not name:
        print("Unknown action. Try: help <action> (e.g., 'help mx vpn').")
        return
    acts, _ = _get_action_meta()
    meta = acts.get(name, {})
    desc = meta.get("desc", meta) if isinstance(meta, dict) else str(meta)
    cat  = meta.get("cat", "General") if isinstance(meta, dict) else "General"
    aliases = meta.get("aliases", []) if isinstance(meta, dict) else []
    fn = REGISTRY.get(name)
    doc = ""
    if fn and getattr(fn, "__doc__", None):
        doc = dedent(fn.__doc__ or "").strip()
    print(Fore.CYAN + f"\nHelp: {name}" + Style.RESET_ALL)
    print(f"  Description : {desc}")
    print(f"  Category    : {cat}")
    if aliases:
        print(f"  Aliases     : {', '.join(sorted(set(aliases)))}")
    if doc:
        print(Fore.LIGHTBLUE_EX + "\nUsage:" + Style.RESET_ALL)
        for line in doc.splitlines():
            print("  " + line.rstrip())
    else:
        print("\n  (No additional usage available.)")
    print()

def _category_for(name: str) -> str:
    n = name.lower()
    # First respect explicit mapping
    for cat, names in _CATS.items():
        if n in names:
            return cat
    # Heuristics for uncategorized actions
    if n.startswith(("wifi","mx ","vlan","switch","client","events","airmarshal","neighbors")):
        return "Network"
    if n.startswith(("use ","org","net","overview","whoami","setup","license")):
        return "Org & Admin"
    if n.startswith(("ctx","reset ctx")):
        return "Session & Context"
    return "Org & Admin"

def _grouped_actions():
    acts = list_actions()
    groups = {k: [] for k in ("Org & Admin","Session & Context","Network","Configure","Inventory")}
    for name, meta in acts.items():
        if name in _HIDE_FROM_HELP: continue
        desc = _clean_desc(meta.get("desc","")) if isinstance(meta, dict) else _clean_desc(str(meta))
        cat = _category_for(name)
        groups.setdefault(cat, []).append((name, desc))
    for cat in groups:
        groups[cat].sort(key=lambda x: x[0])
    return {k: groups.get(k,[]) for k in ("Org & Admin","Session & Context","Network","Configure","Inventory")}

def _print_actions():
    print(Fore.CYAN + "\nAvailable Actions:" + Style.RESET_ALL)
    groups = _grouped_actions()
    name_w, desc_w = 22, 64
    # New order with the reorganized categories up front
    for cat in ("Org & Admin","Session & Context","Network","Configure","Inventory"):
        rows = groups.get(cat) or []
        if not rows: continue
        print(_HDR_COLOR + f"\n[{cat}]" + Style.RESET_ALL)
        for name, desc in rows:
            print(f"  {Fore.GREEN}{_fit(name,name_w):<{name_w}}{Style.RESET_ALL} {_fit(desc,desc_w)}")
    print()
    print(Fore.CYAN + "\nQuick tips:" + Style.RESET_ALL)
    print("  1) setup  → set API key and defaults (first run)")
    print("  2) use org <name>  → choose org; then use net <name>")
    print("  3) overview  → quick health snapshot")
    print("  4) switch ports  → list switch port config (interactive)")
    print("  5) mx status / mx vpn  → WAN/VPN checks (try: mx vpn --all)")
    print("  6) events wireless 60  → recent Wi-Fi events (60 mins)")
    print("  7) ctx / reset ctx  → show or clear session")
    print("  8) type 'help <action>' to list additional usage on various commands\n")


# -----------------------------------------------------------------------------
# TAB completion
# -----------------------------------------------------------------------------
def _setup_readline():
    if not readline: return
    action_names = sorted({k for k in REGISTRY.keys() if k not in _HIDE_FROM_HELP})
    first_tokens = sorted({a.split()[0] for a in action_names} | {"use","help","exit","quit","ctx"})
    def completer(text, state):
        buf = readline.get_line_buffer()
        parts = buf.split()
        if len(parts) <= 1 and not buf.endswith(" "):
            matches = [t for t in first_tokens if t.startswith(text)]
            return matches[state] if state < len(matches) else None
        if len(parts) == 1 or (len(parts) == 2 and not buf.endswith(" ")):
            head = parts[0]
            if head in ("use","help"):
                choices = [c for c in ["org","net","ctx"] if head=="use" and c.startswith(text)]
                if head == "help":
                    choices = [a for a in action_names if a.startswith(text)]
            else:
                choices = [a.split()[1] for a in action_names if a.startswith(head+" ") and len(a.split())>1 and a.split()[1].startswith(text)]
            return choices[state] if state < len(choices) else None
        if parts[0]=="use" and parts[1] in ("org","net"):
            needle = text.lower()
            try:
                names = [o.get("name","") for o in list_organizations()] if parts[1]=="org" else \
                        [n.get("name","") for n in list_networks(CTX.org_id() or CFG.get("default_org_id"))] or []
                matches = [n for n in names if n and n.lower().startswith(needle)]
                return matches[state] if state < len(matches) else None
            except Exception: return None
        return None
    readline.set_completer(completer)
    try: readline.parse_and_bind("tab: complete")
    except Exception: pass

def _audit_log(line: str) -> None:
    try:
        os.makedirs("logs", exist_ok=True)
        path = os.path.join("logs", datetime.datetime.now().strftime("opscenter-%Y%m%d.log"))
        with open(path,"a",encoding="utf-8") as f: f.write(line+"\n")
    except Exception: pass


# -----------------------------------------------------------------------------
# API ready check
# -----------------------------------------------------------------------------
def _ensure_api():
    try:
        from .api import _auth_headers
        _auth_headers()
    except Exception as e:
        print(f"\n{e}\nRun 'setup' first.")
        return False
    return True


# -----------------------------------------------------------------------------
# Mini dashboard (Org/Net + counts + gentle fallbacks)
# -----------------------------------------------------------------------------
def _mini_dashboard():
    try:
        org_name = CTX.org_name() or CFG.get("default_org_name") or "-"
        net_name = CTX.net_name() or CFG.get("default_network_name") or "-"
        org_id = CTX.org_id() or CFG.get("default_org_id")
        # Counts we can compute locally without extra helpers
        orgs = list_organizations() or []
        org_count = len(orgs)
        nets = list_networks(org_id) if org_id else []
        net_count = len(nets or [])
        # Render
        print(Fore.MAGENTA + "─" * BOX_W + Style.RESET_ALL)
        print(Fore.YELLOW + "Mini Dashboard" + Style.RESET_ALL)
        print(f"  Org          : {org_name}")
        print(f"  Network      : {net_name}")
        print(f"  Orgs         : {org_count}")
        print(f"  Networks     : {net_count} (in selected org)")
        # Nudge for deeper device/alert data (kept fast here)
        print(f"  Tip          : run 'overview' for device online/offline & alerts snapshot")
        print(Fore.MAGENTA + "─" * BOX_W + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + f"[mini-dash error] {e}" + Style.RESET_ALL)


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------
def run(argv: List[str]):
    _autoload_actions()
    print(_banner("Meraki Ops Center"))
    print("\nWelcome to ASi's Meraki Operations Deck\n")
    print("Type 'help' to list actions, 'exit' to leave.")
    _setup_readline()

    if argv:
        # builtin help passthrough
        if argv[0].lower() == "help":
            if len(argv) == 1:
                _mini_dashboard()
                _print_actions()
            else:
                _print_action_help(argv[1:])
            return

        if not _ensure_api() and argv[0] != "setup":
            return
        ts = datetime.datetime.now().isoformat(timespec="seconds")
        _audit_log(f"{ts} | {CTX.org_name() or '-'} / {CTX.net_name() or '-'} | {' '.join(argv)}")
        key2, key1 = " ".join(argv[:2]).lower(), argv[0].lower()
        if key2 in ("switch port status","switch ports status") or (key1=="switch" and len(argv)>1 and argv[1] in ("status","ports")):
            if "switch ports" in REGISTRY:
                args = argv[2:] if key2.startswith("switch ") else argv[1:]
                try: REGISTRY["switch ports"](args)
                except Exception as e: print(f"Action error: {e}")
                return
        action = REGISTRY.get(key2) or REGISTRY.get(key1)
        if not action:
            print("Unknown action. Try: meraki help")
            return
        try: action(argv[1:])
        except Exception as e: print(f"Action error: {e}")
        return

    # interactive mode
    _mini_dashboard()
    _print_actions()
    if not CFG.get("api_key"):
        print("No API key configured. Run 'setup' now.")
    while True:
        org_disp = CTX.org_name() or CFG.get("default_org_name") or "-"
        net_disp = CTX.net_name() or CFG.get("default_network_name") or "-"
        if getattr(CTX,"has_org_override",lambda:False)():
            net_disp = CTX.net_name() or "-"
        prompt = f"{Fore.LIGHTCYAN_EX}meraki[{org_disp}/{net_disp}]> {Style.RESET_ALL}"
        cmd = input(prompt).strip()
        ts = datetime.datetime.now().isoformat(timespec="seconds")
        _audit_log(f"{ts} | {CTX.org_name() or '-'} / {CTX.net_name() or '-'} | {cmd}")
        if not cmd: continue
        if cmd.lower() in ("exit","quit","q"): break
        if cmd.lower() in ("help","?"):
            _mini_dashboard(); _print_actions(); continue
        parts = cmd.split()
        if parts[0].lower()=="help" and len(parts)>1:
            _print_action_help(parts[1:]); continue
        if not _ensure_api() and not cmd.startswith("setup"): continue
        key2,key1 = " ".join(parts[:2]).lower(), parts[0].lower()
        if key2 in ("switch port status","switch ports status") or (key1=="switch" and len(parts)>1 and parts[1] in ("status",)):
            if "switch ports" in REGISTRY:
                args = parts[2:] if len(parts)>2 else []
                try: REGISTRY["switch ports"](args)
                except Exception as e: print(f"Action error: {e}")
                continue
        candidate = REGISTRY.get(key2) or REGISTRY.get(key1)
        if not candidate:
            print("Unknown action. Type 'help' to see options."); continue
        args = parts[2:] if candidate is REGISTRY.get(key2) else parts[1:]
        try: candidate(args)
        except Exception as e: print(f"Action error: {e}")
