# modules/meraki/actions/org_select.py
from . import action
from ..api import CTX, CFG, list_organizations, list_networks
from colorama import Fore, Style

# ------------------------- helper: fuzzy-ish scoring -------------------------
def _score(name: str, q: str) -> int:
    n = (name or "").lower()
    q = (q or "").lower()
    if not q: return 0
    if n == q: return 1000
    if n.startswith(q): return 900
    if q in n: return 500
    return 0

def _filter_sort(items, key, q):
    if not q:
        return list(items)
    scored = []
    for it in items:
        name = str(it.get(key, ""))
        s = _score(name, q)
        if s > 0:
            scored.append((s, name, it))
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [it for _, __, it in scored]

# ------------------------- helper: interactive picker ------------------------
def _pick(items, key, title, page_size=20, initial_query=""):
    if not items:
        print("No items.")
        return None

    q = initial_query
    page = 0

    while True:
        arr = _filter_sort(items, key, q) if q else list(items)
        total = len(arr)
        max_page = max(0, (total - 1) // page_size)
        page = min(page, max_page)
        start = page * page_size
        end = min(total, start + page_size)

        # Header + page indicator
        print(Fore.CYAN + f"\n{title}" + Style.RESET_ALL, end="")
        print(f" {Fore.MAGENTA}[Page {page+1}/{max_page+1} · {total} result(s)]{Style.RESET_ALL}")

        # Page rows
        for idx, it in enumerate(arr[start:end], start=start + 1):
            nm = it.get(key) or "-"
            extra = it.get("id") or it.get("serial") or ""
            print(f" {idx:>3}) {nm} {Style.DIM}[{extra}]{Style.RESET_ALL}")

        # Friendly instruction line
        print(
            Fore.YELLOW
            + "Select by number • type to filter • ENTER clears filter / next page "
              "• 'q' to cancel"
            + Style.RESET_ALL
        )

        s = input(Fore.LIGHTCYAN_EX + "filter/select> " + Style.RESET_ALL).strip()

        # Blank line behavior:
        # - if a filter is active, clear it and reset to page 0
        # - if no filter, advance page
        if not s:
            if q:
                q = ""
                page = 0
            else:
                if max_page > 0:
                    page = (page + 1) % (max_page + 1)
            continue

        l = s.lower()
        if l in ("q", "quit", "exit"):
            return None

        # Paging commands
        if l in ("next", ">"):
            page = min(max_page, page + 1); continue
        if l in ("prev", "<"):
            page = max(0, page - 1); continue

        # Show-all / clear filter explicitly
        if l in ("all", "clear", "*"):
            q = ""
            page = 0
            continue

        # Direct numeric selection
        if s.isdigit():
            i = int(s)
            if 1 <= i <= total:
                return arr[i - 1]
            print("Out of range."); continue

        # Otherwise treat input as new filter
        q = s
        page = 0

# ------------------------- context setters (safe fallbacks) ------------------
def _set_org_ctx(org):
    # Try several likely setters; fall back to session fields (no persist)
    if hasattr(CTX, "set_org_override"):
        CTX.set_org_override(org.get("id"), org.get("name"))
        # new org → clear network selection
        if hasattr(CTX, "set_net_override"):
            CTX.set_net_override(None, None)
        elif hasattr(CTX, "_net_id"):
            CTX._net_id = None; CTX._net_name = None
        return
    if hasattr(CTX, "set_org"):
        CTX.set_org(org.get("id"), org.get("name"))
        if hasattr(CTX, "set_net"):
            CTX.set_net(None, None)
        return
    try:
        CTX._org_id = org.get("id"); CTX._org_name = org.get("name")
        CTX._net_id = None; CTX._net_name = None
    except Exception:
        pass

def _set_net_ctx(net):
    if hasattr(CTX, "set_net_override"):
        CTX.set_net_override(net.get("id"), net.get("name")); return
    if hasattr(CTX, "set_net"):
        CTX.set_net(net.get("id"), net.get("name")); return
    try:
        CTX._net_id = net.get("id"); CTX._net_name = net.get("name")
    except Exception:
        pass

# ------------------------- actions: use org / use net ------------------------
@action("use org", "Switch current org (searchable)", cat="General")
def use_org(args):
    """
    use org
    use org <filter>
    use org --save <filter>

    Keys in picker:
      ENTER  → clear filter (or next page if no filter)
      next/> → next page
      prev/< → previous page
      all    → clear filter and show all
      q      → cancel
    """
    save = False
    q = ""
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--save":
            save = True; i += 1
        else:
            q = a if not q else q + " " + a
            i += 1

    orgs = list_organizations() or []
    if q:
        matches = _filter_sort(orgs, "name", q)
        chosen = matches[0] if len(matches) == 1 else _pick(orgs, "name", "Organizations", initial_query=q)
    else:
        chosen = _pick(orgs, "name", "Organizations")

    if not chosen:
        print("No change."); return

    _set_org_ctx(chosen)
    print(Fore.GREEN + f"Using org: {chosen.get('name')}" + Style.RESET_ALL)

    if save:
        try:
            CFG["default_org_id"] = chosen.get("id")
            CFG["default_org_name"] = chosen.get("name")
            if hasattr(CFG, "save"):
                CFG.save()
            print(Style.DIM + "Saved as default org." + Style.RESET_ALL)
        except Exception:
            pass

@action("use net", "Switch current network (searchable)", cat="General")
def use_net(args):
    """
    use net
    use net <filter>
    use net --save <filter>

    Keys in picker:
      ENTER  → clear filter (or next page if no filter)
      next/> → next page
      prev/< → previous page
      all    → clear filter and show all
      q      → cancel
    """
    save = False
    q = ""
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--save":
            save = True; i += 1
        else:
            q = a if not q else q + " " + a
            i += 1

    org_id = CTX.org_id() or CFG.get("default_org_id")
    if not org_id:
        print("Pick an org first (use org)."); return

    nets = list_networks(org_id) or []
    if q:
        matches = _filter_sort(nets, "name", q)
        chosen = matches[0] if len(matches) == 1 else _pick(nets, "name", "Networks", initial_query=q)
    else:
        chosen = _pick(nets, "name", "Networks")

    if not chosen:
        print("No change."); return

    _set_net_ctx(chosen)
    print(Fore.GREEN + f"Using network: {chosen.get('name')}" + Style.RESET_ALL)

    if save:
        try:
            CFG["default_network_id"] = chosen.get("id")
            CFG["default_network_name"] = chosen.get("name")
            if hasattr(CFG, "save"):
                CFG.save()
            print(Style.DIM + "Saved as default network." + Style.RESET_ALL)
        except Exception:
            pass
