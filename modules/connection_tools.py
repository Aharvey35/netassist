# modules/connection_tools.py
import subprocess
import platform
from colorama import Fore

def run():
    print("\n Connection Tools")
    print("Options:")
    print("  1. Ping Host")
    print("  2. Traceroute Host")
    choice = input("\nChoose an option: ").strip()

    if choice == '1':
        ping_host()
    elif choice == '2':
        traceroute_host()
    else:
        print(Fore.RED + "Invalid choice.")

def ping_host():
    host = input("Enter hostname or IP to ping: ").strip()
    ping_direct(host)

def traceroute_host():
    host = input("Enter hostname or IP for traceroute: ").strip()
    traceroute_direct(host)

def ping_direct(target):
    if not target:
        print(Fore.RED + "No target provided.")
        return
    try:
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        print(Fore.CYAN + f"\nPinging {target}...\n")
        subprocess.run(["ping", param, "4", target])
    except Exception as e:
        print(Fore.RED + f"Ping error: {e}")

def traceroute_direct(target):
    if not target:
        print(Fore.RED + "No target provided.")
        return
    try:
        traceroute_cmd = 'tracert' if platform.system().lower() == 'windows' else 'traceroute'
        print(Fore.CYAN + f"\nRunning traceroute to {target}...\n")
        subprocess.run([traceroute_cmd, target])
    except Exception as e:
        print(Fore.RED + f"Traceroute error: {e}")
