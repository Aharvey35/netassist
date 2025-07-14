# modules/remote_tools.py
import subprocess
import sys
import platform
import getpass
import json
import os
from colorama import Fore

DEVICES_FILE = 'data/devices.json'

def load_devices():
    if os.path.exists(DEVICES_FILE):
        with open(DEVICES_FILE, 'r') as f:
            return json.load(f)
    else:
        return {}

def run():
    print(Fore.CYAN + "\n=== Remote Execution Module (PS-Session Style) ===\n")
    print("Usage:")
    print(Fore.YELLOW + "  rce <target_ip>  (manual entry)")
    print("  rce <device_name>  (use saved device profile)\n")
    print("Saved Devices:")
    devices = load_devices()
    for name in devices:
        print(f"  - {name} ({devices[name]['ip']})")
    print()

def execute_remote_command(target_or_ip):
    if platform.system() != "Windows":
        print(Fore.RED + "Remote PS-Session style execution requires Windows platform!")
        return

    devices = load_devices()

    if target_or_ip in devices:
        target_ip = devices[target_or_ip]['ip']
        username = devices[target_or_ip]['username']
        print(Fore.GREEN + f"\n🔗 Target: {target_ip} ({target_or_ip})")
        print(f" Username: {username}")
    else:
        target_ip = target_or_ip
        username = input("\nEnter username: ").strip()

    password = getpass.getpass("Enter password: ").strip()
    ps_command = input("Enter PowerShell command to run: ").strip()

    if not username or not password or not ps_command:
        print(Fore.RED + "\nAll fields must be filled. Aborting.\n")
        return

    command = [
        "powershell",
        "-Command",
        f"$secpasswd = ConvertTo-SecureString '{password}' -AsPlainText -Force; "
        f"$cred = New-Object System.Management.Automation.PSCredential ('{username}', $secpasswd); "
        f"Invoke-Command -ComputerName {target_ip} -Credential $cred -ScriptBlock {{{ps_command}}}"
    ]

    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(Fore.GREEN + "\n=== Remote Command Output ===\n")
            print(result.stdout)
        else:
            print(Fore.RED + "\n=== Remote Command Error ===\n")
            print(result.stderr)
    except Exception as e:
        print(Fore.RED + f"\nError executing remote command: {e}")
