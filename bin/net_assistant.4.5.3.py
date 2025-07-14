# net_assistant.py - Phase 2 Wave 3 Full Upgrade
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
from colorama import init, Fore
from difflib import get_close_matches

# Initialize colorama
init(autoreset=True)

# Global Settings
VERSION = "NetAssist Pro 4.9"
MODULES_FOLDER = 'modules'
today = datetime.date.today().isoformat()

# Command Categories
COMMANDS = [
    'help', 'clear', 'exit', 'motd', 'version', 'history', 'ls', 'masterkey',
    'ping', 'traceroute', 'dnslookup', 'geoip', 'publicip', 'subnetcalc',
    'wildcardcalc', 'speedtest', 'whois', 'sslcheck', 'ntptest',
    'ascii', 'ifconfig', 'ipconfig', 'ssh', 'tracert',
    'system', 'network', 'connect', 'security', 'weather',
    'bonus', 'crypto', 'fun', 'sysadmin', 'stat', 'matrix', 'fireworks',
    'alias', 'savealias', 'loadalias'
]

# Abbreviated Commands
SHORTCUTS = {
    'p': 'ping', 'tr': 'traceroute', 'dl': 'dnslookup', 'g': 'geoip', 'w': 'whois',
    'sp': 'speedtest', 'sc': 'subnetcalc', 'wc': 'wildcardcalc', 'ssl': 'sslcheck',
    'ntp': 'ntptest', 'wea': 'weather', 'c': 'crypto', 'f': 'fun',
    'sa': 'sysadmin', 'sys': 'system', 'con': 'connect', 'sec': 'security'
}

# Common Typos Map
COMMON_TYPOS = {
    'geop': 'geoip', 'pimg': 'ping', 'tracerotue': 'traceroute',
    'dnslooup': 'dnslookup', 'whios': 'whois', 'speetest': 'speedtest',
    'subntcalc': 'subnetcalc', 'wildcradcalc': 'wildcardcalc',
    'sslchek': 'sslcheck', 'netptest': 'ntptest'
}

# Soft Guidance Expected Inputs
COMMAND_HINTS = {
    'geoip': '<ip address>', 'dnslookup': '<domain>', 'ping': '<hostname or IP>',
    'traceroute': '<hostname>', 'whois': '<domain>', 'subnetcalc': '<cidr>',
    'wildcardcalc': '<cidr>', 'sslcheck': '<hostname>', 'ntptest': '<ntp server>',
    'ssh': '<user@host>', 'publicip': None, 'ascii': None, 'speedtest': None
}

# Module Map
MODULES = {
    'network': 'network_tools', 'system': 'system_tools', 'connect': 'connection_tools',
    'security': 'security_tools', 'ascii': 'ascii_art', 'weather': 'weather_tools',
    'bonus': 'bonus_tools', 'repair': 'repair_tools', 'crypto': 'crypto_tools', 'fun': 'fun_tools', 'sysadmin': 'sysadmin_tools'
}

# Alias Bank
ALIASES = {}

# Command History
COMMAND_HISTORY = []

# Setup logging
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

def completer(text, state):
    options = [cmd for cmd in COMMANDS + list(SHORTCUTS.keys()) + list(ALIASES.keys()) if cmd.startswith(text)]
    if state < len(options):
        return options[state]
    else:
        return None

readline.parse_and_bind('tab: complete')
readline.set_completer(completer)
readline.set_history_length(200)

def print_banner():
    print(Fore.CYAN + f"""
==============================================
    {VERSION}
    Welcome back, Commander Aaron 💪
==============================================
""")
    dynamic_motd()
    logging.info("Session started.")

def dynamic_motd():
    try:
        headers = {'User-Agent': 'NetAssistBot/1.0'}
        response = requests.get('https://zenquotes.io/api/random', headers=headers, timeout=5)
        response.raise_for_status()
        quote = response.json()[0]
        print(Fore.MAGENTA + f"\n\"{quote['q']}\" — {quote['a']}\n")
    except Exception as e:
        print(Fore.RED + f"\nDynamic MOTD unavailable. (Error: {e})\nFallback Tip: Stay sharp. Stay focused.\n")

def load_module(name):
    try:
        mod = importlib.import_module(f'{MODULES_FOLDER}.{name}')
        return mod
    except Exception as e:
        print(Fore.RED + f"Error loading module '{name}': {e}")
        return None

def correct_typo(cmd):
    close = get_close_matches(cmd, COMMON_TYPOS.keys(), n=1, cutoff=0.7)
    if close:
        suggestion = COMMON_TYPOS[close[0]]
        print(Fore.YELLOW + f"\n📣 Did you mean '{suggestion}'?\n")
        return suggestion
    return cmd

def save_aliases():
    with open('data/aliases.json', 'w') as f:
        json.dump(ALIASES, f)
    print(Fore.GREEN + "\n💾 Aliases saved.\n")

def load_aliases():
    global ALIASES
    try:
        with open('data/aliases.json', 'r') as f:
            ALIASES = json.load(f)
        print(Fore.GREEN + "\n🔄 Aliases loaded.\n")
    except:
        print(Fore.RED + "\nFailed to load aliases.")

def matrix_mode():
    try:
        print(Fore.GREEN)
        while True:
            print(''.join(random.choice('01') for _ in range(80)))
            time.sleep(0.05)
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nMatrix mode exited.\n")

def fireworks_mode():
    try:
        for _ in range(20):
            print(Fore.YELLOW + "✨ BOOM ✨ " * random.randint(1, 5))
            time.sleep(0.2)
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nFireworks mode exited.\n")

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

def main():
    print_banner()
    while True:
        try:
            cmd = input(Fore.GREEN + "NetAssist> ").strip()

            if not cmd:
                continue

            # Parse input smartly
            words = cmd.split()
            if words[0] in SHORTCUTS:
                words[0] = SHORTCUTS[words[0]]
            cmd = ' '.join(words)

            if cmd.startswith('!'):
                index = int(cmd[1:]) - 1
                if 0 <= index < len(COMMAND_HISTORY):
                    cmd = COMMAND_HISTORY[index]
                    print(Fore.YELLOW + f"\n🔁 Re-running: {cmd}\n")
                else:
                    print(Fore.RED + "Invalid history reference.")
                    continue

            if cmd == 'savealias':
                save_aliases()
                continue

            if cmd == 'loadalias':
                load_aliases()
                continue

            if cmd == 'matrix':
                matrix_mode()
                continue

            if cmd == 'fireworks':
                fireworks_mode()
                continue

            if cmd == 'stat':
                system_status()
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

            if cmd in ['cls', 'clear']:
                os.system('cls' if os.name == 'nt' else 'clear')
                print_banner()
                continue

            if cmd == 'ls':
                print("\nAvailable Commands:")
                for c in sorted(COMMANDS):
                    print(f"  - {c}")
                print()
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
                print("\nCommands:")
                for c in sorted(COMMANDS):
                    print(f"  - {c}")
                print()
                continue

            if cmd == 'exit':
                print(Fore.YELLOW + "\nFarewell, champion.\n")
                logging.info("Session ended.")
                sys.exit()

            COMMAND_HISTORY.append(cmd)

            if cmd in ALIASES:
                cmd = ALIASES[cmd]
                print(Fore.YELLOW + f"\n💪 Alias expanding: {cmd}\n")

            words = cmd.split()
            base_command = words[0]
            args = words[1:]

            if base_command in MODULES:
                mod = load_module(MODULES[base_command])
                if mod:
                    mod.run()
                continue

            if base_command in COMMAND_HINTS:
                hint = COMMAND_HINTS[base_command]

                if args and args[0] == '?':
                    if hint:
                        print(Fore.YELLOW + f"\n📣 Expected input: {hint}\n")
                    else:
                        print(Fore.YELLOW + "\n📣 No input needed for this command.\n")
                    continue

                if hint and len(args) == 0:
                    print(Fore.YELLOW + f"\n📣 Missing input! Example usage:\n{base_command} {hint}\n")
                    continue

                # Dispatch specific commands if needed here

            print(Fore.RED + f"Unknown command: {cmd}. Type 'help'.")

        except KeyboardInterrupt:
            print(Fore.YELLOW + "\nInterrupt detected. Use 'exit' to quit cleanly.\n")
        except Exception as e:
            print(Fore.RED + f"Error: {e}")

if __name__ == "__main__":
    main()
