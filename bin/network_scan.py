# modules/network_scan.py

import ipaddress
import subprocess
import threading
import platform
import time
from colorama import Fore

def ping_host(ip, results, param):
    try:
        subprocess.check_output(
            ['ping', param, '1', str(ip)],
            timeout=2
        )
        results.append(str(ip))
    except subprocess.CalledProcessError:
        pass
    except subprocess.TimeoutExpired:
        pass
    except Exception:
        pass

def scan_network(cidr):
    try:
        net = ipaddress.ip_network(cidr, strict=False)
    except ValueError:
        print(Fore.RED + "\nInvalid CIDR format.\n")
        return

    print(Fore.YELLOW + f"\nScanning network {cidr}...\n")

    param = "-n" if platform.system().lower() == "windows" else "-c"

    threads = []
    results = []
    total_ips = len(list(net.hosts()))
    completed = 0

    def progress_bar():
        nonlocal completed
        while any(t.is_alive() for t in threads):
            print(f"Progress: {completed}/{total_ips}", end='\r')
            time.sleep(0.5)

    # Launch progress bar thread
    progress = threading.Thread(target=progress_bar)
    progress.start()

    for ip in net.hosts():
        t = threading.Thread(target=ping_host, args=(ip, results, param))
        threads.append(t)
        t.start()
        completed += 1

    for t in threads:
        t.join()

    time.sleep(0.5)  # slight wait for clean output

    if results:
        print(Fore.GREEN + "\nAlive Hosts:")
        for ip in results:
            print(Fore.CYAN + f"  {ip}")
    else:
        print(Fore.RED + "\nNo alive hosts found.\n")

def run():
    print(Fore.CYAN + "\n🌐 Network Scanner\n")
    cidr = input("Enter network CIDR (e.g., 192.168.1.0/24): ").strip()
    scan_network(cidr)
