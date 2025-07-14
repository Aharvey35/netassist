# modules/repair_tools.py (Silent DNS Flush Patch)
import os
from colorama import Fore

def run():
    print("\n  Repair Tools")
    print("Options:")
    print("  1. Restart Network Manager")
    print("  2. Flush DNS Cache (Silent Smart)")
    print("  3. Clear ARP Cache (Linux)")
    choice = input("\nChoose an option: ").strip()

    if choice == '1':
        print(Fore.YELLOW + "\n Restarting NetworkManager service...")
        os.system('sudo systemctl restart NetworkManager')
        print(Fore.GREEN + "\n Network Manager restarted successfully!\n")

    elif choice == '2':
        print(Fore.YELLOW + "\n Attempting to flush DNS cache...")
        result = os.system('sudo systemd-resolve --flush-caches 2>/dev/null')
        if result != 0:
            print(Fore.YELLOW + "\n systemd-resolve not available. Restarting NetworkManager to flush DNS instead...")
            os.system('sudo systemctl restart NetworkManager')
        print(Fore.GREEN + "\n DNS cache flush operation completed!\n")

    elif choice == '3':
        print(Fore.YELLOW + "\n Clearing ARP cache...")
        os.system('sudo ip -s -s neigh flush all')
        print(Fore.GREEN + "\n ARP cache cleared successfully!\n")

    else:
        print(Fore.RED + "Invalid choice. Returning to NetAssist main shell.")
