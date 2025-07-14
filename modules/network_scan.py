# modules/network_scan.py

import ipaddress
import threading
import subprocess
from colorama import Fore

# Create a thread-safe lock for printing
print_lock = threading.Lock()

alive_hosts = []

def run(cidr=None):
    global alive_hosts
    alive_hosts = []
    print(Fore.CYAN + "\n Simple CIDR Scan")
    if cidr:
        quick_scan(cidr.strip())
    else:
        entered = input(Fore.GREEN + "\nEnter CIDR to scan (Example: 192.168.1.0/24): ").strip()
        if entered:
            quick_scan(entered)
        else:
            print(Fore.RED + "\n No CIDR provided. Aborting.")

def quick_scan(cidr):
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        threads = []
        print(Fore.YELLOW + f"\n Scanning {cidr} for active hosts...\n")
        for ip in network.hosts():
            t = threading.Thread(target=ping_host, args=(str(ip),))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        print(Fore.CYAN + f"\n Scan complete. {len(alive_hosts)} hosts found alive.\n")
    except Exception as e:
        print(Fore.RED + f"\n Invalid CIDR: {cidr} ({e})")

def ping_host(ip):
    try:
        result = subprocess.run(["ping", "-c", "1", "-W", "1", ip],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if result.returncode == 0:
            with print_lock:
                print(Fore.GREEN + f"[+] Host is up: {ip}")
            alive_hosts.append(ip)
    except Exception:
        pass
