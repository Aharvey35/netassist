# modules/system_tools.py
import time
import platform
import psutil
from colorama import Fore

def run():
    while True:
        print("\n🖥️  System Tools")
        print("Options:")
        print("  1. Uptime")
        print("  2. CPU Usage")
        print("  3. Memory Usage")
        print("  4. Disk Usage")
        print("  5. Exit")
        choice = input("\nChoose an option: ").strip()

        if choice == '1':
            uptime()
        elif choice == '2':
            cpu_usage()
        elif choice == '3':
            memory_usage()
        elif choice == '4':
            disk_usage()
        elif choice == '5':
            print(Fore.YELLOW + "\nReturning to main NetAssist console...\n")
            break
        else:
            print(Fore.RED + "Invalid choice.")

def uptime():
    try:
        uptime_seconds = int(psutil.boot_time())
        system_uptime = platform.uname()
        print(Fore.CYAN + f"\n🕒 System Uptime Since: {time.ctime(uptime_seconds)}\n")
    except Exception as e:
        print(Fore.RED + f"Uptime error: {e}")

def cpu_usage():
    try:
        print(Fore.CYAN + f"\n🧠 CPU Usage: {psutil.cpu_percent(interval=1)}%\n")
    except Exception as e:
        print(Fore.RED + f"CPU usage error: {e}")

def memory_usage():
    try:
        mem = psutil.virtual_memory()
        print(Fore.CYAN + f"\n🗄️  Memory Usage: {mem.percent}% used\n")
    except Exception as e:
        print(Fore.RED + f"Memory usage error: {e}")

def disk_usage():
    try:
        disk = psutil.disk_usage('/')
        print(Fore.CYAN + f"\n💽 Disk Usage: {disk.percent}% used\n")
    except Exception as e:
        print(Fore.RED + f"Disk usage error: {e}")
