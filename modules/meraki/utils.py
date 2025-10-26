# modules/meraki/utils.py
import os, json, csv, datetime
from typing import List, Dict, Any, Optional

def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def stamp(prefix: str, ext: str) -> str:
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{prefix}-{ts}.{ext}"

def save_json(obj: Any, filename: Optional[str] = None) -> str:
    _ensure_dir("exports")
    name = filename or stamp("export", "json")
    path = os.path.join("exports", name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
    print(f"Saved: {path}")
    return path

def save_csv(rows: List[Dict[str, Any]], fields: List[str], filename: Optional[str] = None) -> str:
    _ensure_dir("exports")
    name = filename or stamp("export", "csv")
    path = os.path.join("exports", name)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in fields})
    print(f"Saved: {path}")
    return path

def pull_flag(args: List[str], flag: str) -> (bool, Optional[str], List[str]):
    """
    Extracts --json [name] or --csv [name] style flags.
    Returns (present, value_or_None, remaining_args)
    """
    out = []
    present = False
    value: Optional[str] = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == flag:
            present = True
            if i + 1 < len(args) and not args[i+1].startswith("--"):
                value = args[i+1]
                i += 2
            else:
                i += 1
        else:
            out.append(a); i += 1
    return present, value, out
