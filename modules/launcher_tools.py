# modules/launcher_tools.py
import os, shutil, subprocess, sys, platform, urllib.parse

def _in_wsl() -> bool:
    try:
        return "microsoft" in platform.release().lower() or "wsl" in platform.version().lower()
    except Exception:
        return False

def _which_first(candidates):
    for c in candidates:
        p = shutil.which(c)
        if p:
            return p
    return None

def _open_with_system(url_or_path: str) -> bool:
    """
    Generic fallback: opens a URL or file with the OS default handler.
    Returns True on success, False otherwise.
    """
    try:
        if sys.platform.startswith("win"):
            subprocess.Popen(["cmd.exe", "/c", "start", "", url_or_path], shell=False)
            return True
        elif sys.platform == "darwin":
            subprocess.Popen(["open", url_or_path])
            return True
        else:
            opener = _which_first(["xdg-open", "gio"])
            if opener:
                subprocess.Popen([opener, url_or_path])
                return True
    except Exception:
        pass
    return False

def _looks_like_url(token: str) -> bool:
    """
    Heuristic: treat token as URL if it has a scheme:// OR looks like a host.tld[/...]
    and contains no spaces.
    """
    if not token or " " in token:
        return False
    if "://" in token:
        return True
    # bare domain/path: example.com or dashboard.meraki.com/login
    parts = token.split("/")
    host = parts[0]
    return "." in host and not host.startswith("-")

def _ensure_scheme(url: str) -> str:
    return url if "://" in url else f"https://{url}"

def _build_search_url(query: str, engine: str = "google") -> str:
    q = urllib.parse.quote_plus(query.strip())
    e = engine.lower().strip()
    if e in ("ddg", "duckduckgo"):
        return f"https://duckduckgo.com/?q={q}"
    if e in ("bing", "ms", "edge"):
        return f"https://www.bing.com/search?q={q}"
    # default google
    return f"https://www.google.com/search?q={q}"

def _chrome_candidates():
    if sys.platform.startswith("win"):
        return [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
    elif sys.platform == "darwin":
        return ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    else:
        return ["google-chrome-stable", "google-chrome", "chromium-browser", "chromium", "brave-browser"]

def _firefox_candidates():
    if sys.platform.startswith("win"):
        return [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
        ]
    elif sys.platform == "darwin":
        return ["/Applications/Firefox.app/Contents/MacOS/firefox"]
    else:
        return ["firefox"]

def _find_browser(exe_candidates):
    for c in exe_candidates:
        if os.path.isfile(c):
            return c
    return _which_first(exe_candidates)

def _launch_windows_from_wsl(browser, args):
    try:
        cmd = ["powershell.exe", "-NoProfile", "-Command", "Start-Process", browser] + args
        subprocess.Popen(cmd)
        return True
    except Exception:
        pass
    try:
        cmd = ["cmd.exe", "/c", "start", "", browser] + args
        subprocess.Popen(cmd)
        return True
    except Exception:
        return False

def _launch_native(cmd_and_args):
    subprocess.Popen(cmd_and_args)
    return True

def _normalize_args(raw_args):
    return [a for a in (raw_args or []) if str(a).strip()]

def _split_flags_and_words(args):
    flags = [a for a in args if a.startswith("--")]
    words = [a for a in args if not a.startswith("--")]
    return flags, words

def _resolve_target_from_args(words, engine_flag: str | None):
    """
    Decide what to open based on non-flag words.
    - If first word looks like a URL, open that (adding https:// if needed).
    - Otherwise, treat ALL words as a search query and build a search URL.
    """
    if not words:
        return ""  # nothing provided -> open blank browser
    first = words[0]
    if _looks_like_url(first):
        return _ensure_scheme(first)
    # Merge all words into a query
    query = " ".join(words)
    engine = "google"
    if engine_flag:
        # --engine=ddg  |  --engine=bing  |  --engine=google
        try:
            engine = engine_flag.split("=", 1)[1]
        except Exception:
            pass
    return _build_search_url(query, engine)

def launch_app(app: str, raw_args=None):
    """
    app: 'chrome' or 'firefox'
    raw_args: list[str] (e.g., ['meraki', '--new-window']) or ['https://example.com']
    Behavior:
      - If args look like a URL, open that.
      - Else treat args as a search query and open a search results page (default Google).
      - Recognizes optional --engine=google|ddg|bing to pick the search engine.
      - Passes through browser flags like --new-window, --incognito, etc.
      - Cross-platform with WSL awareness; falls back to OS default opener if needed.
    """
    app = (app or "").lower().strip()
    args = _normalize_args(raw_args)

    # Parse flags/words
    flags, words = _split_flags_and_words(args)
    engine_flag = next((f for f in flags if f.startswith("--engine=")), None)
    target = _resolve_target_from_args(words, engine_flag)  # may be "" if no words

    # Keep only browser-compatible flags (leave --engine out)
    browser_flags = [f for f in flags if not f.startswith("--engine=")]
    final_args = browser_flags + ([target] if target else [])

    if app == "chrome":
        candidates = _chrome_candidates()
    elif app == "firefox":
        candidates = _firefox_candidates()
    else:
        # Unknown app → try system default open for the target
        if target:
            ok = _open_with_system(target)
            if not ok:
                print("Could not find a way to open the target.")
        else:
            print("Nothing to open.")
        return

    exe = _find_browser(candidates)

    if _in_wsl():
        # Launch Windows browser from WSL if needed
        if (exe and exe[1:3] == ":\\") or (exe is None):
            browser_name = exe if exe else ("chrome" if app == "chrome" else "firefox")
            ok = _launch_windows_from_wsl(browser_name, final_args)
            if not ok:
                if not (target and _open_with_system(target)):
                    print(f"Failed to launch {app} from WSL.")
            return

    if exe:
        try:
            _launch_native([exe] + final_args)
        except Exception:
            if not (target and _open_with_system(target)):
                print(f"Failed to launch {app}.")
    else:
        if target:
            ok = _open_with_system(target)
            if not ok:
                print(f"{app} not found and system opener failed.")
        else:
            print(f"{app} not found. Provide a URL or search terms.")
