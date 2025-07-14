# modules/scan_manager.py

import os
import ipaddress
import subprocess
import threading
import time
from colorama import Fore, Style
import socket

active_hosts = []
lock = threading.Lock()

def quick_scan():
    print(Fore.CYAN + "\n[Quick Scan] Auto-detecting your network...")
    scan_subnet("192.168.0.0/24")

def manual_scan():
    cidr = input("\nEnter CIDR to scan (e.g., 192.168.1.0/24): ").strip()
    if cidr:
        scan_subnet(cidr)

def multi_subnet_scan():
    cidrs = input("\nEnter multiple CIDRs (comma separated): ").strip().split(",")
    for cidr in cidrs:
        scan_subnet(cidr.strip())

def smart_sweep():
    base_ip = input("\nEnter base IP (default: 192.168.0.): ").strip() or "192.168.0."
    numbers = input("Enter last octets to scan (e.g., 1,2,10,100): ").strip().split(',')

    print(Fore.CYAN + f"\n[Smart Sweep] Scanning selected IPs...\n")
    for num in numbers:
        target = f"{base_ip}{num.strip()}"
        threading.Thread(target=ping_host, args=(target,)).start()

def live_dashboard():
    print(Fore.CYAN + "\n[Live Dashboard] (coming soon — building real-time view...)\n")
    time.sleep(1)

def scan_from_file():
    filename = input("\nEnter filename (default: networks.txt): ").strip() or "networks.txt"
    if not os.path.exists(filename):
        print(Fore.RED + f"File '{filename}' not found.")
        return
    with open(filename, 'r') as f:
        lines = f.readlines()
    for line in lines:
        scan_subnet(line.strip())

def scan_subnet(cidr):
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        print(Fore.YELLOW + f"\nScanning {cidr}...\n")
        threads = []

        for ip in network.hosts():
            t = threading.Thread(target=ping_host, args=(str(ip),))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        print_summary()

    except Exception as e:
        print(Fore.RED + f"Invalid CIDR: {cidr} ({e})")

def ping_host(ip):
    try:
        start = time.time()
        result = subprocess.run(["ping", "-c", "1", "-W", "1", ip],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        end = time.time()

        if result.returncode == 0:
            latency = round((end - start) * 1000, 2)
            try:
                hostname = socket.gethostbyaddr(ip)[0]
            except:
                hostname = "Unknown"

            with lock:
                active_hosts.append((ip, latency, hostname))
                print(Fore.GREEN + f"[+] Host is up: {ip} | {latency} ms | {hostname}")

    except Exception as e:
        pass

def print_summary():
    print(Fore.MAGENTA + "\n📊 Scan Summary:")
    if active_hosts:
        for ip, latency, hostname in active_hosts:
            print(Fore.YELLOW + f" - {ip} ({hostname}) - {latency} ms")
    else:
        print(Fore.RED + "No active hosts found.")
    print(Fore.MAGENTA + f"\nTotal Active Hosts: {len(active_hosts)}\n")
    active_hosts.clear()

def run():
    while True:
        print(Fore.CYAN + """

🛰️  NetAssist Network Scan Manager
Options:
  1. Quick Scan (Auto-detect local network)
  2. Manual Scan (Enter one CIDR)
  3. Multi-Subnet Scan (Enter multiple CIDRs)
  4. Smart Sweep (Gateway + Common IPs)
  5. Live Dashboard (Real-Time View)
  6. Scan from File (Import CIDRs)
  7. Exit

        """)
        choice = input(Fore.GREEN + "Choose an option: ").strip()

        if choice == '1':
            quick_scan()
        elif choice == '2':
            manual_scan()
        elif choice == '3':
            multi_subnet_scan()
        elif choice == '4':
            smart_sweep()
        elif choice == '5':
            live_dashboard()
        elif choice == '6':
            scan_from_file()
        elif choice == '7':
            print(Fore.YELLOW + "\nReturning to NetAssist main menu...\n")
            break
        else:
            print(Fore.RED + "Invalid choice.")

