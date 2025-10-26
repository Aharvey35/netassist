# modules/meraki/actions/__init__.py
from typing import Callable, Dict, List, Optional

REGISTRY: Dict[str, Callable] = {}         # name/alias -> func
META: Dict[str, dict] = {}                 # canonical name -> meta

def action(name: str, desc: str, *, cat: str = "General", aliases: Optional[List[str]] = None):
    """
    Decorator for actions with optional category and aliases.
    """
    def deco(func: Callable):
        canon = name.lower().strip()
        func._action_name = canon
        func._action_desc = desc
        func._action_cat  = cat
        func._action_aliases = set(a.lower().strip() for a in (aliases or []))

        META[canon] = {"desc": desc, "cat": cat, "aliases": sorted(func._action_aliases)}
        REGISTRY[canon] = func
        for al in func._action_aliases:
            REGISTRY[al] = func
        return func
    return deco

def list_actions():
    """
    Returns a dict {canonical_name: {"desc":..., "cat":..., "aliases":[...]}}
    """
    return {k: dict(v) for k, v in META.items()}
