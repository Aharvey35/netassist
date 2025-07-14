# modules/security_tools.py
import socket
from colorama import Fore

try:
    import whois
    WHOIS_AVAILABLE = True
except ImportError:
    WHOIS_AVAILABLE = False

def run():
    print("\n🔒 Security Tools")
    print("Options:")
    print("  1. Port Check")
    print("  2. Whois Lookup")
    choice = input("\nChoose an option: ").strip()

    if choice == '1':
        port_check()
    elif choice == '2':
        whois_lookup()
    else:
        print(Fore.RED + "Invalid choice.")

def port_check():
    host = input("Enter hostname or IP: ").strip()
    port = input("Enter port number: ").strip()
    if not host or not port:
        print(Fore.RED + "Hostname and port required.")
        return
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((host, int(port)))
        if result == 0:
            print(Fore.CYAN + f"\n✅ Port {port} on {host} is OPEN.\n")
        else:
            print(Fore.RED + f"\n❌ Port {port} on {host} is CLOSED.\n")
        sock.close()
    except Exception as e:
        print(Fore.RED + f"Port check error: {e}")

def whois_lookup():
    domain = input("Enter domain (example.com): ").strip()
    whois_direct(domain)

def whois_direct(domain):
    if not domain:
        print(Fore.RED + "No domain provided.")
        return
    if not WHOIS_AVAILABLE:
        print(Fore.RED + "Whois module not installed. Install with 'pip install python-whois'.")
        return
    try:
        data = whois.whois(domain)
        print(Fore.CYAN + f"\n🔎 Whois data for {domain}:")
        for key, value in data.items():
            print(f"  {key}: {value}")
        print()
    except Exception as e:
        print(Fore.RED + f"Whois lookup error: {e}")
