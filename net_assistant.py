#net_assistant.py - NetAssist Pro 5.1 Tactical CLI OS

# === IMPORTS ===
import os
import sys
import importlib
import readline
import datetime
import logging
import requests
import platform
import json
import random
import time
from modules import user_manager
from colorama import init, Fore
from difflib import get_close_matches

# === INITIALIZE COLORAMA ===
init(autoreset=True)

# === GLOBAL SETTINGS ===
VERSION = "NetAssist Pro 5.3"
#USER_NAME = "Aaron"  # TODO: make dynamic later
#USER_PROFILE = user_manager.load_user(USER_NAME)

#USER_RANK = USER_PROFILE["title"]
#USER_BADGE = USER_PROFILE["badge"]
#USER_LEVEL = USER_PROFILE["level"]
#USER_XP = USER_PROFILE["xp"]

# --- stub globals so print_banner() can always see them ---
USER_NAME = ""
USER_PROFILE = {}
USER_RANK = ""
USER_BADGE = ""
USER_LEVEL = 0
USER_XP = 0


import yaml
from pathlib import Path

# === YAML profiles for leveling & titles ===
PROFILES_FILE = Path('data/user_profiles.yaml')
# JSON list of selectable roles
TITLES_FILE   = Path('data/titles.json')
DEFAULT_PROFILE = { "xp": 0, "level": 1, "title": "Rookie", "badge": "::..::" }

def load_all_profiles():
    if not PROFILES_FILE.exists():
        PROFILES_FILE.parent.mkdir(exist_ok=True)
        PROFILES_FILE.write_text("")  # create empty file
    return yaml.safe_load(PROFILES_FILE.read_text()) or {}

def save_all_profiles(p):
    PROFILES_FILE.write_text(yaml.dump(p, sort_keys=False))

def get_or_create_profile(username, profiles):
    # case-insensitive lookup
    key = next((u for u in profiles if u.lower() == username.lower()), username)
    if key not in profiles:
        profiles[key] = DEFAULT_PROFILE.copy()
    return key, profiles[key]

MODULES_FOLDER = 'modules'
# Load available titles first
try:
    with open('data/titles.json', 'r') as f:
        AVAILABLE_TITLES = json.load(f)
except:
    AVAILABLE_TITLES = ["Comander", "Architect", "Operator", "Sentinel"]  # fallback titles

# Load or request user profile
PROFILE_FILE = 'data/user_profile.json'

def load_user_profile():
    try:
        with open(PROFILE_FILE, 'r') as f:
            profile = json.load(f)
            return profile.get("user_name", "Aaron"), profile.get("user_rank", "Architect")
    except:
        return None, None

def save_user_profile(user_name, user_rank):
    profile = {
        "user_name": user_name,
        "user_rank": user_rank
    }
    with open(PROFILE_FILE, 'w') as f:
        json.dump(profile, f)



    print("\nAvailable Titles:")
    for idx, title in enumerate(AVAILABLE_TITLES, start=1):
        print(f"{idx}. {title}")

    selected_title = input("\nChoose your title by number (or hit Enter for 'Architect'): ").strip()

    if selected_title.isdigit() and 1 <= int(selected_title) <= len(AVAILABLE_TITLES):
        USER_RANK = AVAILABLE_TITLES[int(selected_title) - 1]
    else:
        USER_RANK = "Architect"

    save_user_profile(USER_NAME, USER_RANK)

today = datetime.date.today().isoformat()

# === COMMANDS ===
COMMANDS = [
    'help', 'clear', 'exit', 'motd', 'version', 'history', 'ls', 'masterkey',
    'password', 'ping', 'profile', 'traceroute', 'dnslookup', 'geoip', 'publicip', 'subnetcalc',
    'wildcardcalc', 'speedtest', 'whois', 'sslcheck', 'ntptest',
    'ascii', 'ifconfig', 'ipconfig', 'ssh', 'tracert', 'role',
    'system', 'bandwidth', 'network', 'dashboard', 'connect', 'security', 'weather',
    'bonus', 'portcheck', 'banner', 'crypto', 'repair', 'fun', 'sysadmin', 'stat', 'matrix', 'fireworks',
    'alias', 'scan', 'netscan', 'savealias', 'threatfeed', 'loadalias', 'shortcuts', 'battery', 'notes', 'wifi'
]

# === COMMAND META (usage + example) ===
COMMAND_META = {
    "ping":         {"usage": "ping <host>",                 "example": "ping 8.8.8.8"},
    "traceroute":   {"usage": "traceroute <host>",           "example": "traceroute google.com"},
    "dnslookup":    {"usage": "dnslookup <domain>",          "example": "dnslookup example.com"},
    "geoip":        {"usage": "geoip <ip>",                  "example": "geoip 8.8.8.8"},
    "publicip":     {"usage": "publicip",                    "example": "publicip"},
    "subnetcalc":   {"usage": "subnetcalc <cidr>",           "example": "subnetcalc 10.10.10.0/24"},
    "wildcardcalc": {"usage": "wildcardcalc <cidr>",         "example": "wildcardcalc 10.0.0.0/16"},
    "speedtest":    {"usage": "speedtest",                   "example": "speedtest"},
    "whois":        {"usage": "whois <domain>",              "example": "whois example.com"},
    "sslcheck":     {"usage": "sslcheck <host>",             "example": "sslcheck example.com"},
    "ntptest":      {"usage": "ntptest <ntp-server>",        "example": "ntptest pool.ntp.org"},
    "portcheck":    {"usage": "portcheck <host> <ports>",    "example": "portcheck 192.168.1.1 22,80"},
    "bandwidth":    {"usage": "bandwidth [interface]",       "example": "bandwidth eth0"},
    # …add other commands here as you like
}

# === SHORTCUTS (Hidden in Menu) ===
SHORTCUTS = {
    'p': 'ping', 'tr': 'traceroute', 'dl': 'dnslookup', 'g': 'geoip', 'w': 'whois',
    'sp': 'speedtest', 'sc': 'subnetcalc', 'wc': 'wildcardcalc', 'ssl': 'sslcheck',
    'ntp': 'ntptest', 'wea': 'weather', 'c': 'crypto', 'f': 'fun',
    'pc': 'portcheck', 'pw': 'password', 'sa': 'sysadmin', 'sys': 'system', 'con': 'connect', 'sec': 'security', 'cls': 'clear'
}

# === COMMON TYPOS MAP ===
COMMON_TYPOS = {
    'geop': 'geoip', 'pimg': 'ping', 'tracerotue': 'traceroute',
    'dnslooup': 'dnslookup', 'baner': 'banner', 'whios': 'whois', 'speetest': 'speedtest',
    'subntcalc': 'subnetcalc', 'wildcradcalc': 'wildcardcalc',
    'sslchek': 'sslcheck', 'netptest': 'ntptest'
}

# === SOFT GUIDANCE INPUT EXPECTATIONS ===
COMMAND_HINTS = {
    'geoip': '<ip address>', 'portcheck': '<host> <port(s)>', 'dnslookup': '<domain>', 'ping': '<hostname or IP>',
    'traceroute': '<hostname>', 'bandwidth': '[interface]', 'whois': '<domain>', 'subnetcalc': '<cidr>',
    'wildcardcalc': '<cidr>', 'sslcheck': '<hostname>', 'ntptest': '<ntp server>', 'wifi': '[min_signal]',
    'ssh': '<user@host>', 'publicip': None, 'ascii': None, 'speedtest': None
}

# === MODULE MAPPING ===
MODULES = {
    'network': 'network_tools', 'bandwidth': 'bandwidth_monitor', 'wifi': 'wifi_scanner', 'portcheck': 'port_check', 'system': 'system_tools', 'connect': 'connection_tools',
    'security': 'security_tools', 'dashboard': 'dashboard_tools', 'ascii': 'ascii_art', 'weather': 'weather_tools',
    'bonus': 'bonus_tools', 'notes': 'notes_tools', 'clock': 'clock_tools', 'repair': 'repair_tools', 'crypto': 'crypto_tools', 'fun': 'fun_tools', 'sysadmin': 'sysadmin_tools'
}

# === ALIAS BANK ===
ALIASES = {}

# === COMMAND HISTORY ===
COMMAND_HISTORY = []

# === LOGGING ===
if not os.path.exists('data/session_logs'):
    os.makedirs('data/session_logs')
if not os.path.exists('data/aliases.json'):
    with open('data/aliases.json', 'w') as f:
        json.dump({}, f)

logging.basicConfig(
    filename=f'data/session_logs/{today}.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# === AUTOCOMPLETE ===
def completer(text, state):
    options = [cmd for cmd in COMMANDS + list(ALIASES.keys()) if cmd.startswith(text)]
    if state < len(options):
        return options[state]
    else:
        return None

readline.parse_and_bind('tab: complete')
readline.set_completer(completer)
readline.set_history_length(200)
# === BANNER ===
def print_banner():
    # Pull the experience title from YAML
    exp_title = USER_PROFILE.get("title", "Rookie")
    badge     = USER_PROFILE.get("badge", "")
    level     = USER_PROFILE.get("level", 0)
    xp        = USER_PROFILE.get("xp", 0)

    print(Fore.CYAN + f"""
============================================
{VERSION}
Welcome back, {exp_title} {USER_NAME} {badge}
LEVEL {level}  |  XP: {xp}
============================================
""")
    logging.info("Session started.")

# === DYNAMIC MOTD ===
def dynamic_motd():
    try:
        headers = {'User-Agent': 'NetAssistBot/1.0'}
        response = requests.get('https://zenquotes.io/api/random', headers=headers, timeout=5)
        response.raise_for_status()
        quote = response.json()[0]
        print(Fore.MAGENTA + f"\n\"{quote['q']}\" — {quote['a']}\n")
    except Exception as e:
        print(Fore.RED + f"\nDynamic MOTD unavailable. (Error: {e})\nFallback Tip: Stay sharp. Stay focused.\n")

# === Tactical Paging Function ===
def paginate_output(lines):
    import shutil
    import sys
    import termios
    import tty

    term_height = shutil.get_terminal_size().lines - 2  # Leave 2 lines for breathing room
    for i in range(0, len(lines), term_height):
        chunk = lines[i:i + term_height]
        for line in chunk:
            print(line)
        
        if i + term_height < len(lines):  # Only if more content remains
            print(Fore.YELLOW + "[Press SPACE to continue]", end='', flush=True)

            # Listen for a single keypress
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                key = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

            print("\r" + " " * shutil.get_terminal_size().columns + "\r", end='')  # Clear the line after

            if key.lower() != ' ':
                break  # Exit if they don't press space

        else:
            print("")  # Final blank line at the end for neatness

# === QUICK USAGE HELPER =================================================
def show_usage(cmd_key: str):
    """Print usage + example if the command is documented."""
    meta = COMMAND_META.get(cmd_key)
    if meta:
        print(Fore.CYAN + f"Usage   : {meta['usage']}")
        print(Fore.CYAN + f"Example : {meta['example']}")
# ========================================================================

# === MATRIX MODE (Standard) ===
def matrix_mode():
    try:
        print(Fore.GREEN)
        while True:
            print(''.join(random.choice('01') for _ in range(80)))
            time.sleep(0.05)
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nMatrix mode exited.\n")

# === FIREWORKS MODE (Fun) ===
def fireworks_mode():
    try:
        for _ in range(20):
            print(Fore.YELLOW + "✨ BOOM ✨ " * random.randint(1, 5))
            time.sleep(0.2)
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nFireworks mode exited.\n")

# === SECRET FUNCTION: FIRE EMOTE ===
def fire_emote():
    print(Fore.RED)
    for _ in range(30):
        print('🔥' * random.randint(10, 50))
        time.sleep(0.1)
    print(Fore.YELLOW + "\n🔥🔥 Fire mode exited.\n")

# === SECRET FUNCTION: EXTENDED MATRIX ===
def extended_matrix():
    try:
        print(Fore.GREEN)
        while True:
            print(''.join(random.choice('01') for _ in range(120)))
            time.sleep(0.02)
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nExtended Matrix mode exited.\n")

# === SECRET FUNCTION: HACKER QUOTE BLASTER ===
def hacker_quote_blast():
    quotes = [
        "Hack the planet!",
        "There is no security — only varying levels of insecurity.",
        "The quieter you become, the more you can hear.",
        "Every lock can be picked with a big enough hammer.",
        "The best defense is a good offense.",
        "You are only as secure as your dumbest user.",
        "In cyberspace, trust is a vulnerability."
    ]
    try:
        for _ in range(10):
            print(Fore.CYAN + random.choice(quotes))
            time.sleep(0.8)
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nHacker quote blaster exited.\n")

# === SECRET FUNCTION: HERO MOTIVATION ===
def epic_motivation():
    messages = [
        "Today you fight for your destiny. 🛡️",
        "Heroes are made in battle, not in comfort.",
        "Stand tall — legends rise under pressure.",
        "Every champion was once a contender who refused to give up.",
        "Pain is temporary. Glory is forever.",
        "You are the shield against the storm. 🌪️",
        "Command the network. Command your fate. 🚀"
    ]
    try:
        for _ in range(5):
            print(Fore.MAGENTA + random.choice(messages))
            time.sleep(1)
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nHero motivation mode exited.\n")

# === DYNAMIC PROMPT COLOR HANDLER ===

def get_prompt_color():
    color = ACTIVE_PROFILE.get("prompt_color", "green").lower()

    if color == "green":
        return Fore.GREEN
    elif color == "cyan":
        return Fore.CYAN
    elif color == "red":
        return Fore.RED
    elif color == "magenta":
        return Fore.MAGENTA
    elif color == "yellow":
        return Fore.YELLOW
    else:
        return Fore.WHITE


# === PROFILE LOADER ===
import os
import json

PROFILES_FOLDER = 'profiles'
ACTIVE_PROFILE = {}

def load_profile(profile_name):
    global ACTIVE_PROFILE
    try:
        profile_path = os.path.join(PROFILES_FOLDER, f"{profile_name}.json")
        if not os.path.exists(profile_path):
            print(Fore.RED + f"\nProfile '{profile_name}' not found! Loading default profile.\n")
            profile_path = os.path.join(PROFILES_FOLDER, "default.json")

        with open(profile_path, 'r') as f:
            ACTIVE_PROFILE = json.load(f)
        ACTIVE_PROFILE["name"] = profile_name
        apply_theme(ACTIVE_PROFILE.get("theme", "default"))
        splash_screen(ACTIVE_PROFILE.get("banner", "default"))

        print(Fore.CYAN + f"\n🛡️Profile '{profile_name}' loaded successfully.\n")

    except Exception as e:
        print(Fore.RED + f"\nFailed to load profile: {e}\n")
        ACTIVE_PROFILE = {}

def save_default_profiles():
    if not os.path.exists(PROFILES_FOLDER):
        os.makedirs(PROFILES_FOLDER)

    defaults = {
        "work": {
            "theme": "commander_blue",
            "banner": "hero"
        },
        "lab": {
            "theme": "matrix_green",
            "banner": "matrix"
        },
        "home": {
            "theme": "battle_red",
            "banner": "default"
        },
        "play": {
            "theme": "cyberpunk_purple",
            "banner": "cyberpunk"
        },
        "default": {
            "theme": "commander_blue",
            "banner": "default"
        }
    }

    for name, content in defaults.items():
        path = os.path.join(PROFILES_FOLDER, f"{name}.json")
        if not os.path.exists(path):
            with open(path, 'w') as f:
                json.dump(content, f, indent=4)

# === LIVE PROFILE SWITCHER INSIDE CLI ===

def live_profile_switch(args):
    if not args:
        print(Fore.RED + "\nUsage: profile select <work/lab/home/play>\n")
        return

    subcommand = args[0]
    if subcommand != "select":
        print(Fore.RED + "\nUnknown profile command. Did you mean 'profile select <name>'?\n")
        return

    if len(args) < 2:
        print(Fore.RED + "\nPlease specify which profile to select.\n")
        return

    chosen_profile = args[1].lower()

    if chosen_profile not in ["work", "lab", "home", "play"]:
        print(Fore.RED + "\n⚠️ Invalid profile name. Available: work, lab, home, play.\n")
        return

    load_profile(chosen_profile)


# === THEME ENGINE ===

CURRENT_THEME = "default"

def apply_theme(theme_name):
    global CURRENT_THEME

    if theme_name == "matrix_green":
        os.system('')  # enable color in terminal
        print(Fore.GREEN + "\n Matrix Green theme activated.\n")
    elif theme_name == "commander_blue":
        os.system('')
        print(Fore.CYAN + "\n Commander Blue theme activated.\n")
    elif theme_name == "battle_red":
        os.system('')
        print(Fore.RED + "\n Battle Red theme activated.\n")
    elif theme_name == "cyberpunk_purple":
        os.system('')
        print(Fore.MAGENTA + "\n Cyberpunk Purple theme activated.\n")
    else:
        os.system('')
        print(Fore.WHITE + "\n Default NetAssist theme activated.\n")

    CURRENT_THEME = theme_name

# === MINIMAL SPLASHSCREEN SYSTEM ===

def splash_screen(style="default"):
    os.system('cls' if os.name == 'nt' else 'clear')

    current_profile = ACTIVE_PROFILE.get("name", "unknown").upper()
    current_theme   = ACTIVE_PROFILE.get("theme", "default").replace("_", " ").title()

    print(Fore.GREEN + "[BOOT] NetAssist Pro 5.1 Initialized")
    print(Fore.CYAN  + f"[PROFILE] {current_profile}")
    print(Fore.CYAN  + f"[THEME]   {current_theme}")
    print(Fore.CYAN  + "[STATUS]  SYSTEMS ONLINE")

    # Show the profile_role (from titles.json) first
    role = USER_PROFILE.get("profile_role", "Operator")
    print(Fore.YELLOW + f"[READY]   Welcome, {USER_NAME}, the {role}")


# === STARTUP PROFILE SELECTOR ===

def select_profile_on_startup():
    save_default_profiles()  # Ensure /profiles/ exists and defaults saved

    print(Fore.CYAN + "\n[COMMAND CENTER] ACTIVATED")
    print(Fore.CYAN + "Choose Deployment Profile: [work] [lab] [home] [play]\n")

    chosen = input(Fore.YELLOW + "Profile > ").strip().lower()

    if chosen not in ["work", "lab", "home", "play"]:
        print(Fore.RED + "\n⚠️Invalid selection. Defaulting to 'work'.\n")
        chosen = "work"

    load_profile(chosen)

# == BATTERY ===
def show_battery_status():
    try:
        import psutil
        battery = psutil.sensors_battery()
        if battery is None:
            print("\n⚡ Battery info not available on this device.\n")
        else:
            plugged = battery.power_plugged
            percent = battery.percent
            time_left = battery.secsleft

            print("\n🔋 Battery Status:")
            print(f"    Charge: {percent}%")
            print(f"    Status: {'Charging' if plugged else 'Discharging'}")
            if time_left != psutil.POWER_TIME_UNLIMITED and time_left > 0:
                hours, remainder = divmod(time_left, 3600)
                minutes, _ = divmod(remainder, 60)
                print(f"    Time Remaining: {hours}h {minutes}m")
            print()
    except ImportError:
        print("\n⚡ psutil module is missing. Install with: pip install psutil\n")

# === SHOW SYSTEM STATS ===
def system_status():
    try:
        import psutil
        print(Fore.CYAN + f"\n⚙ System Status:")
        print(f"CPU Usage: {psutil.cpu_percent()}%")
        mem = psutil.virtual_memory()
        print(f"Memory Usage: {mem.percent}%")
        disk = psutil.disk_usage('/')
        print(f"Disk Usage: {disk.percent}%")
        print()
    except ImportError:
        print(Fore.RED + "Install psutil module to use system status.")


# === SHORTCUT VISUALIZER ===
def show_shortcuts():
    print(Fore.CYAN + "\n==== NetAssist Shortcut Quick Reference ====")

    print(Fore.YELLOW + "\nAbbreviated Shortcuts:")
    for k, v in SHORTCUTS.items():
        print(f"  - {k:<5} ➔ {v}")

    if ALIASES:
        print(Fore.YELLOW + "\nUser-Created Aliases:")
        for alias, target in ALIASES.items():
            print(f"  - {alias:<10} ➔ {target}")
    else:
        print(Fore.YELLOW + "\nUser-Created Aliases:")
        print("  (none yet)\n")

# === SAVE ALIASES ===
def save_aliases():
    with open('data/aliases.json', 'w') as f:
        json.dump(ALIASES, f)
    print(Fore.GREEN + "\n💾 Aliases saved.\n")

# === LOAD ALIASES ===
def load_aliases():
    global ALIASES
    try:
        with open('data/aliases.json', 'r') as f:
            ALIASES = json.load(f)
        print(Fore.GREEN + "\n🔄 Aliases loaded.\n")
    except:
        print(Fore.RED + "\nFailed to load aliases.")

# === LOAD MODULE (DYNAMIC IMPORT) ===
def load_module(name):
    try:
        mod = importlib.import_module(f'{MODULES_FOLDER}.{name}')
        return mod
    except Exception as e:
        print(Fore.RED + f"Error loading module '{name}': {e}")
        return None

# === MASTERKEY REFERENCE ===
def master_key():
    print(Fore.CYAN + "\n==== NetAssist Command MasterKey ====")

    sections = {
        "Core System Commands": [
            'help', 'clear', 'exit', 'motd', 'version', 'history', 'ls', 'masterkey'
        ],
        "Network Tools (Direct Commands)": [
            'ping', 'traceroute', 'dnslookup', 'geoip', 'publicip', 'subnetcalc', 'wildcardcalc',
            'speedtest', 'whois', 'sslcheck', 'ntptest'
        ],
        "System Tools (Direct Commands)": [
            'stat', 'ifconfig', 'ipconfig', 'battery'
        ],
        "Connection Tools (Direct Commands)": [
            'ssh'
        ],
        "⚙️ Module-Based Tools (Interactive Menus)": [
            'system (*)', 'network (*)', 'connect (*)', 'security (*)', 'repair (*)', 'notes (*)', 'sysadmin (*)', 'dashboard (*)'
        ],
        "Alias Management Tools": [
            'alias', 'savealias', 'loadalias', 'shortcuts'
        ],
        "Fun / Bonus Tools": [
            'ascii', 'matrix', 'fireworks', 'weather', 'crypto', 'fun'
        ]
    }

    # Collect all output into a list
    output_lines = []
    for section, cmds in sections.items():
        output_lines.append(Fore.YELLOW + f"\n{section}")
        for c in cmds:
            output_lines.append(Fore.RESET + f" - {c}")
        output_lines.append("")  # Spacer

    # Now paginate
    paginate_output(output_lines)

# === MAIN CLI LOOP ===
def main():
    global USER_NAME, USER_PROFILE, USER_RANK, USER_BADGE, USER_LEVEL, USER_XP

    # Step 1: Per-user login & profile load
    import yaml
    from pathlib import Path

    PROFILES_FILE = Path('data/user_profiles.yaml')
    profiles = yaml.safe_load(PROFILES_FILE.read_text()) or {}

    raw = input("Enter your name (or hit Enter for 'Master'): ").strip() or "Master"
    USER_NAME = raw.title()

    key = next((u for u in profiles if u.lower()==USER_NAME.lower()), USER_NAME)
    if key not in profiles:
        profiles[key] = {"xp":0,"level":1,"title":"Rookie","badge":"::..::"}

    USER_NAME, USER_PROFILE = key, profiles[key]
        # ─── Prompt for profile_role if missing ─────────────────────────
    if "profile_role" not in USER_PROFILE:
        from pathlib import Path
        import json

        # Load the list of roles
        with open(TITLES_FILE) as f:
            roles = json.load(f)

        # Show numbered list
        print("\nAvailable Roles:")
        for i, role in enumerate(roles, 1):
            print(f" {i}) {role}")

        # Let user pick one
        sel = input("\nChoose your role by number (or hit Enter to skip): ").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(roles):
            USER_PROFILE["profile_role"] = roles[int(sel) - 1]
            # Persist immediately
            PROFILES_FILE.write_text(yaml.dump(profiles, sort_keys=False))

    USER_XP    = USER_PROFILE["xp"]
    USER_LEVEL = USER_PROFILE["level"]
    USER_BADGE = USER_PROFILE["badge"]
        # Banner “rank” comes from profile_role if present, else experience title
    USER_RANK = USER_PROFILE.get("profile_role", USER_PROFILE["title"])

    #USER_RANK  = USER_PROFILE["title"]

    PROFILES_FILE.write_text(yaml.dump(profiles, sort_keys=False))

    # Step 2: deployment profile selection
    select_profile_on_startup()

    # Step 3: show splash & banner
    splash_screen()
    print_banner()

    while True:
        try:
            # ─── Read input ──────────────────────────────────────────
            raw_input = input(get_prompt_color() + "NetAssist> ").strip()
            if not raw_input:
                continue

            # ... rest of your loop unchanged ...


            # ---------- QUICK HELP TRIGGER ---------------------------------
            # user typed "<command> ?"   e.g. "ping ?"
            if raw_input.endswith(" ?"):
                base = raw_input[:-2].strip()
                if base in COMMAND_META:
                    show_usage(base)
                    COMMAND_HISTORY.append(raw_input)
                    continue
            # ----------------------------------------------------------------

            # 2) user typed "<command> ?"   e.g. "ping ?"
            if raw_input.endswith(" ?"):
                base = raw_input[:-2].strip()
                if base in COMMAND_META:
                    show_usage(base)
                    COMMAND_HISTORY.append(raw_input)
                    continue
            # ---------------------------------------------------------

            cmd   = raw_input
            words = cmd.split()

            # ─── Expand shortcuts ------------------------------------
            if words[0] in SHORTCUTS:
                words[0] = SHORTCUTS[words[0]]
            cmd = " ".join(words)

            # ─── Notes handling (this line already exists below) -----
            if words[0] == 'note':
                from modules import notes_tools

                if len(words) < 2:
                    notes_tools.run()
                    continue

                subcommand = words[1]

                if subcommand == 'add' and len(words) >= 3:
                    notes_tools.add_note(' '.join(words[2:]))
                elif subcommand == 'list':
                    notes_tools.list_notes()
                elif subcommand == 'read' and len(words) >= 3:
                    notes_tools.read_note(' '.join(words[2:]))
                elif subcommand == 'delete' and len(words) >= 3:
                    notes_tools.delete_note(' '.join(words[2:]))
                else:
                    print("\n⚠️ Unknown note command or missing arguments.\n")
                continue


            # Quick Re-run by !n syntax
            if cmd.startswith('!'):
                index = int(cmd[1:]) - 1
                if 0 <= index < len(COMMAND_HISTORY):
                    cmd = COMMAND_HISTORY[index]
                    print(Fore.YELLOW + f"\n🔁 Re-running: {cmd}\n")
                else:
                    print(Fore.RED + "Invalid history reference.")
                    continue

            # Built-in simple commands
            if cmd == 'savealias':
                save_aliases()
                continue

            if cmd == 'loadalias':
                load_aliases()
                continue
            if cmd == 'help':
                from modules import help_tools
                help_tools.run()
                continue
            
            if cmd == 'matrix':
                matrix_mode()
                continue

            if cmd == 'fireworks':
                fireworks_mode()
                continue
            if cmd == 'time':
                from datetime import datetime
                import pytz
                tz = pytz.timezone("US/Pacific")
                now = datetime.now(tz)
                print(Fore.CYAN + f"\n🕒 Current Pacific Time (PST): {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
                continue

            if cmd == 'stat':
                system_status()
                continue

            if cmd == 'battery':
                show_battery_status()
                continue


            if cmd.startswith('alias '):
                parts = cmd.split()
                if len(parts) >= 3:
                    alias_name = parts[1]
                    alias_command = ' '.join(parts[2:])
                    ALIASES[alias_name] = alias_command
                    print(Fore.GREEN + f"\n🔑 Alias '{alias_name}' set for: {alias_command}\n")
                    continue
                else:
                    print(Fore.RED + "\nUsage: alias <shortcut> <full command>\n")
                    continue

            if cmd == 'masterkey':
                master_key()
                continue

            if cmd == 'shortcuts':
                show_shortcuts()
                continue

            if cmd in ['cls', 'clear']:
                os.system('cls' if os.name == 'nt' else 'clear')
                #print_banner()
                continue

            if cmd == 'ls':
                master_key()
                continue

            if cmd == 'banner':
                print_banner()
                continue

            if cmd == 'history':
                for i, hist_cmd in enumerate(COMMAND_HISTORY, start=1):
                    print(f"{i}: {hist_cmd}")
                continue

            if cmd == 'motd':
                dynamic_motd()
                continue

            if cmd == 'version':
                print(Fore.CYAN + f"\nRunning {VERSION}\n")
                continue

            if cmd == 'help':
                master_key()
                continue

            if cmd == 'exit':
                print(Fore.YELLOW + "\nFarewell, Commander. NetAssist signing off.\n")
                logging.info("Session ended.")
                sys.exit()

            # SECRET CODES
            if cmd == ':fire:':
                fire_emote()
                continue

            if cmd == ':matrix:':
                extended_matrix()
                continue

            if cmd == ':idgaf:':
                hacker_quote_blast()
                continue

            if cmd == ':hero:':
                epic_motivation()
                continue

            COMMAND_HISTORY.append(cmd)
            # --- XP / RANK UPDATE -----------------------------------
            # Give 5 XP for any successful command
            USER_PROFILE = user_manager.award_xp(USER_NAME, amount=5)
            user_manager.save_user(USER_NAME, USER_PROFILE)

            # Refresh banner variables so the next banner shows new rank/xp
            USER_RANK  = USER_PROFILE["title"]
            USER_BADGE = USER_PROFILE["badge"]
            USER_LEVEL = USER_PROFILE["level"]
            USER_XP    = USER_PROFILE["xp"]
            # ---------------------------------------------------------

            # Expand Aliases
            if cmd in ALIASES:
                cmd = ALIASES[cmd]
                print(Fore.YELLOW + f"\n Alias expanding: {cmd}\n")

            # Split command for parsing
            words = cmd.split()
            base_command = words[0]
            args = words[1:]

            # === DISPATCHERS ===

            if base_command == 'ping':
                from modules import connection_tools
                connection_tools.ping_direct(args[0])
                continue

            elif base_command == 'scan':
                from modules import network_scan
                if args:
                    network_scan.run(args[0])
                else:
                    network_scan.run()
                continue

            elif base_command == 'role':
                import json, yaml
                from pathlib import Path

                # load roles
                with open(TITLES_FILE) as f:
                    roles = json.load(f)

                print("\nAvailable Roles:")
                for i, r in enumerate(roles,1):
                    print(f" {i}) {r}")

                sel = input("\nChoose your new role by number (or Enter to cancel): ").strip()
                if sel.isdigit() and 1 <= int(sel) <= len(roles):
                    new_role = roles[int(sel)-1]
                    USER_PROFILE["profile_role"] = new_role
                    USER_RANK = new_role   # just assign—no inline global needed

                    # persist back to YAML
                    PROFILES_FILE = Path('data/user_profiles.yaml')
                    all_profiles = yaml.safe_load(PROFILES_FILE.read_text()) or {}
                    all_profiles[USER_NAME] = USER_PROFILE
                    PROFILES_FILE.write_text(yaml.dump(all_profiles, sort_keys=False))

                    print(Fore.GREEN + f"\n Role updated: you are now {new_role}.\n")
                else:
                    print(Fore.YELLOW + "\nNo changes made.\n")

                continue



            elif base_command == 'bandwidth':
                from modules import bandwidth_monitor
                if args:
                    bandwidth_monitor.bandwidth_direct(args[0])
                else:
                    bandwidth_monitor.run()
                continue

            elif base_command == 'wifi':
                from modules import wifi_scanner
                if args:
                    min_signal = int(args[0]) if args[0].lstrip('-').isdigit() else None
                    wifi_scanner.wifi_direct(min_signal)
                else:
                    wifi_scanner.run()
                continue

            elif base_command == 'portcheck':
                from modules import port_check
                if len(args) < 2:
                    print(Fore.RED + "\nUsage: portcheck <host> <port(s)>\n")
                else:
                    port_check.port_check_direct(args[0], args[1].split(','))
                continue

            elif base_command == 'netscan':
                from modules import scan_manager
                scan_manager.run()
                continue

            elif base_command == 'traceroute':
                from modules import connection_tools
                connection_tools.traceroute_direct(args[0])
                continue

            elif base_command == 'rce':
                from modules import remote_tools
                if len(args) != 1:
                    print(Fore.YELLOW + "\nUsage: rce <target_ip>\n")
                else:
                    target_ip = args[0]
                    remote_tools.execute_remote_command(target_ip)
                continue

            elif base_command == 'threatfeed':
                from modules import threat_feed
                mode = 'highonly'
                if len(args) >= 1 and args[0] == 'all':
                    mode = 'all'
                threat_feed.run(mode)
                continue

            elif base_command == 'save-threats':
                from modules import threat_feed
                threat_feed.save_feed_snapshot()
                continue

            elif base_command == 'dnslookup':
                from modules import network_tools
                network_tools.dnslookup_direct(args[0])
                continue

            elif base_command == 'geoip':
                from modules import network_tools
                network_tools.geoip_direct(args[0])
                continue

            elif base_command == 'subnetcalc':
                from modules import network_tools
                network_tools.subnet_calc_direct(args[0])
                continue

            elif base_command == 'wildcardcalc':
                from modules import network_tools
                network_tools.wildcard_calc_direct(args[0])
                continue

            elif base_command == 'publicip':
                from modules import network_tools
                network_tools.public_ip()
                continue

            elif base_command == 'speedtest':
                from modules import network_tools
                network_tools.speedtest_direct()
                continue

            elif base_command == 'whois':
                from modules import security_tools
                security_tools.whois_direct(args[0])
                continue

            elif base_command == 'sslcheck':
                from modules import bonus_tools
                bonus_tools.ssl_checker_direct(args[0])
                continue

            elif base_command == 'ntptest':
                from modules import bonus_tools
                bonus_tools.ntp_test_direct(args[0])
                continue

            elif base_command == 'dice':
                from modules import dice_roller
                dice_roller.run()
                continue

            elif base_command == 'joke':
                from modules import dad_jokes
                dad_jokes.run()
                continue

            elif base_command == 'password':
                from modules import password_tools
                password_tools.run()
                continue

            elif base_command == 'space':
                from modules import space_facts
                space_facts.run()
                continue

            elif base_command == 'ascii':
                from modules import ascii_art
                ascii_art.run()
                continue

            elif base_command == 'ssh':
                os.system(f"ssh {args[0]}")
                continue

            elif base_command == 'profile':
                live_profile_switch(args)
                continue

            elif base_command == 'ifconfig':
                os.system('ifconfig')
                continue

            elif base_command == 'ipconfig':
                os.system('ip addr')
                continue


            # Safety check to ensure command is a string
            if not isinstance(base_command, str):
                print(Fore.RED + f"Invalid command format. Expected string but got {type(base_command)}: {base_command}")
                continue

            elif base_command in MODULES:
                mod = load_module(MODULES[base_command])
                if mod:
                    mod.run()
                continue

            else:
                print(Fore.RED + f"Unknown command: {cmd}. Type 'help'.")

        except KeyboardInterrupt:
            print(Fore.YELLOW + "\nInterrupt detected. Use 'exit' to quit cleanly.\n")
        except Exception as e:
            print(Fore.RED + f"Error: {e}")

# === FINAL EXECUTION ===
if __name__ == "__main__":
    main()
