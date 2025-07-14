# modules/network_tools.py

import requests
import socket
from ipaddress import ip_network
import speedtest
from colorama import Fore

def run():
    while True:
        print("\n Network Tools")
        print("Options:")
        print("  1. Public IP Lookup")
        print("  2. GeoIP Lookup")
        print("  3. DNS Lookup")
        print("  4. IP Subnet Calculator")
        print("  5. Speedtest")
        print("  6. Exit")
        
        choice = input("\nChoose an option: ").strip()

        if choice == '1':
            public_ip()
        elif choice == '2':
            geoip_lookup()
        elif choice == '3':
            dns_lookup()
        elif choice == '4':
            subnet_calc()
        elif choice == '5':
            speedtest_direct()
        elif choice == '6':
            print(Fore.YELLOW + "\nReturning to main NetAssist console...\n")
            break
        else:
            print(Fore.RED + "Invalid choice.")

def public_ip():
    try:
        ip = requests.get('https://api.ipify.org').text
        print(Fore.CYAN + f"\n Your Public IP Address: {ip}\n")
    except Exception as e:
        print(Fore.RED + f"Error fetching public IP: {e}")

def geoip_lookup():
    ip = input("Enter IP address: ").strip()
    geoip_direct(ip)

def dns_lookup():
    hostname = input("Enter hostname: ").strip()
    dnslookup_direct(hostname)

def subnet_calc():
    cidr = input("Enter network in CIDR (e.g., 192.168.1.0/24): ").strip()
    subnet_calc_direct(cidr)

def speedtest_direct():
    print("\nRunning Speedtest... (this may take a moment)\n")
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        download = st.download()
        upload = st.upload()
        print(Fore.CYAN + f"  Download Speed: {download / 1_000_000:.2f} Mbps")
        print(Fore.CYAN + f"  Upload Speed: {upload / 1_000_000:.2f} Mbps\n")
    except Exception as e:
        print(Fore.RED + f"Speedtest error: {e}")

# ==== Direct Commands for Fast CLI Usage ====

def geoip_direct(target_ip):
    if not target_ip:
        print(Fore.RED + "No IP provided.")
        return
    try:
        response = requests.get(f'https://ipinfo.io/{target_ip}/json')
        data = response.json()
        print(Fore.CYAN + f"\n GeoIP Info for {target_ip}:")
        for key, value in data.items():
            print(f"  {key}: {value}")
        print()
    except Exception as e:
        print(Fore.RED + f"GeoIP Lookup error: {e}")

def dnslookup_direct(target):
    if not target:
        print(Fore.RED + "No hostname provided.")
        return
    try:
        ip = socket.gethostbyname(target)
        print(Fore.CYAN + f"\n {target} resolves to {ip}\n")
    except Exception as e:
        print(Fore.RED + f"DNS lookup error: {e}")

def subnet_calc_direct(cidr):
    from ipaddress import ip_network
    import ipaddress

    if not cidr:
        print(Fore.RED + "No network provided.")
        return

    try:
        network = ip_network(cidr, strict=False)
        netmask = network.netmask
        wildcard = ".".join([str(255 - int(o)) for o in str(netmask).split('.')])
        first_ip = str(list(network.hosts())[0]) if network.num_addresses > 2 else str(network.network_address)
        last_ip = str(list(network.hosts())[-1]) if network.num_addresses > 2 else str(network.broadcast_address)

        def get_ip_class(ip):
            first_octet = int(ip.split('.')[0])
            if 0 <= first_octet <= 127:
                return 'Class A'
            elif 128 <= first_octet <= 191:
                return 'Class B'
            elif 192 <= first_octet <= 223:
                return 'Class C'
            elif 224 <= first_octet <= 239:
                return 'Class D (Multicast)'
            else:
                return 'Class E (Experimental)'

        def is_private(ip):
            return ipaddress.ip_address(ip).is_private

        print(Fore.CYAN + f"\n  Network Info for {cidr}:\n")
        print(f"  Network Address     : {network.network_address}")
        print(f"  Broadcast Address   : {network.broadcast_address}")
        print(f"  Usable Host Range   : {first_ip} – {last_ip}")
        print(f"  Total IPs           : {network.num_addresses}")
        print(f"  Usable Hosts        : {network.num_addresses - 2 if network.num_addresses > 2 else network.num_addresses}")
        print(f"  Subnet Mask         : {netmask}")
        print(f"  Wildcard Mask       : {wildcard}")
        print(f"  CIDR Notation       : /{network.prefixlen}")
        print(f"  Binary Mask         : {'.'.join(format(int(o), '08b') for o in str(netmask).split('.'))}")
        print(f"  IP Class            : {get_ip_class(str(network.network_address))}")
        print(f"  Private IP Space    : {'Yes (RFC1918)' if is_private(str(network.network_address)) else 'No'}\n")

    except Exception as e:
        print(Fore.RED + f"Subnet calc error: {e}")

def wildcard_calc_direct(cidr):
    if not cidr:
        print(Fore.RED + "No network provided.")
        return
    try:
        network = ip_network(cidr, strict=False)
        wildcard = [255 - int(octet) for octet in str(network.netmask).split('.')]
        print(Fore.CYAN + f"\n Wildcard Mask for {cidr}: {'.'.join(map(str, wildcard))}\n")
    except Exception as e:
        print(Fore.RED + f"Wildcard calc error: {e}")
