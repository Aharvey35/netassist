# modules/sysadmin_tools.py
import os
import psutil
import getpass
import platform
from colorama import Fore

def run():
    print("\n🛠️ysadmin PRO Tools")
    print("Options:")
    print("  1. Current User")
    print("  2. Uptime (Detailed)")
    print("  3. CPU Info")
    print("  4. Memory Info")
    print("  5. Disk Info")
    print("  6. Network Interfaces")
    print("  7. List Processes")
    choice = input("\nChoose an option: ").strip()

    if choice == '1':
        current_user()
    elif choice == '2':
        uptime_detailed()
    elif choice == '3':
        cpu_info()
    elif choice == '4':
        memory_info()
    elif choice == '5':
        disk_info()
    elif choice == '6':
        network_info()
    elif choice == '7':
        list_processes()
    else:
        print(Fore.RED + "Invalid choice.")

def current_user():
    user = getpass.getuser()
    print(Fore.CYAN + f"\n Current User: {user}\n")

def uptime_detailed():
    uptime_seconds = int(psutil.boot_time())
    uptime_hours = (int(os.times().elapsed) / 3600)
    print(Fore.CYAN + f"\n System Uptime: {uptime_hours:.2f} hours\n")

def cpu_info():
    print(Fore.CYAN + f"\n CPU Cores: {psutil.cpu_count(logical=True)} (logical) / {psutil.cpu_count(logical=False)} (physical)")
    print(f"🖥️ CPU Usage: {psutil.cpu_percent(interval=1)}%\n")

def memory_info():
    mem = psutil.virtual_memory()
    print(Fore.CYAN + f"\n Memory Total: {mem.total // (1024**2)}MB")
    print(f" Memory Used: {mem.used // (1024**2)}MB")
    print(f" Memory Free: {mem.free // (1024**2)}MB")
    print(f" Usage: {mem.percent}%\n")

def disk_info():
    disk = psutil.disk_usage('/')
    print(Fore.CYAN + f"\n Disk Total: {disk.total // (1024**3)}GB")
    print(f" Disk Used: {disk.used // (1024**3)}GB")
    print(f" Disk Free: {disk.free // (1024**3)}GB")
    print(f" Usage: {disk.percent}%\n")

def network_info():
    net = psutil.net_if_addrs()
    print(Fore.CYAN + "\n Network Interfaces:")
    for interface, addrs in net.items():
        print(f"  {interface}:")
        for addr in addrs:
            if addr.family.name == 'AF_INET':
                print(f"    IP Address: {addr.address}")
            if addr.family.name == 'AF_PACKET':
                print(f"    MAC Address: {addr.address}")
    print()

def list_processes():
    print(Fore.CYAN + "\n Top 5 Running Processes (by CPU %):")
    processes = [(p.info['pid'], p.info['name'], p.info['cpu_percent']) for p in psutil.process_iter(['pid', 'name', 'cpu_percent'])]
    processes = sorted(processes, key=lambda p: p[2], reverse=True)[:5]
    for pid, name, cpu in processes:
        print(f"  PID {pid} | {name} | {cpu}% CPU")
    print()
