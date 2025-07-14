# modules/repair_tools.py
import os
from colorama import Fore

def run():
    print("\n🛠️  Repair Tools")
    print("Options:")
    print("  1. Restart Network Manager")
    print("  2. Flush DNS Cache")
    print("  3. Clear ARP Cache (Linux)")
    choice = input("\nChoose an option: ").strip()

    if choice == '1':
        print(Fore.YELLOW + "\n🔄 Restarting NetworkManager service...")
        os.system('sudo systemctl restart NetworkManager')
        print(Fore.GREEN + "\n✅ Network Manager restarted successfully!\n")

    elif choice == '2':
        print(Fore.YELLOW + "\n🔄 Flushing DNS resolver cache...")
        os.system('sudo systemd-resolve --flush-caches')
        print(Fore.GREEN + "\n✅ DNS cache flushed successfully!\n")

    elif choice == '3':
        print(Fore.YELLOW + "\n🔄 Clearing ARP cache...")
        os.system('sudo ip -s -s neigh flush all')
        print(Fore.GREEN + "\n✅ ARP cache cleared successfully!\n")

    else:
        print(Fore.RED + "Invalid choice. Returning to NetAssist main shell.")
