# modules/bonus_tools.py
import ssl
import socket
import datetime
import os
import platform
from colorama import Fore

def run():
    print("\n Bonus Tools")
    print("Options:")
    print("  1. SSL Certificate Checker")
    print("  2. NTP Test (Ping NTP Server)")
    choice = input("\nChoose an option: ").strip()

    if choice == '1':
        ssl_checker()
    elif choice == '2':
        ntp_test()
    else:
        print(Fore.RED + "Invalid choice.")

def ssl_checker():
    hostname = input("Enter hostname (without https://): ").strip()
    if not hostname:
        print(Fore.RED + "No hostname provided.")
        return
    try:
        context = ssl.create_default_context()
        conn = context.wrap_socket(socket.socket(socket.AF_INET), server_hostname=hostname)
        conn.settimeout(5.0)
        conn.connect((hostname, 443))
        cert = conn.getpeercert()
        expiry_date = cert['notAfter']
        expire_datetime = datetime.datetime.strptime(expiry_date, "%b %d %H:%M:%S %Y %Z")
        days_left = (expire_datetime - datetime.datetime.utcnow()).days
        print(Fore.CYAN + f"\n SSL Certificate for {hostname} expires on: {expiry_date} ({days_left} days left)\n")
    except Exception as e:
        print(Fore.RED + f"SSL check error: {e}")

def ntp_test():
    server = input("Enter NTP server (e.g., time.google.com): ").strip()
    if not server:
        print(Fore.RED + "No server provided.")
        return
    try:
        response = os.system(f"ping -c 3 {server}" if platform.system() != "Windows" else f"ping -n 3 {server}")
        if response == 0:
            print(Fore.CYAN + "\n NTP server is reachable.\n")
        else:
            print(Fore.RED + "\nNTP server is not reachable.\n")
    except Exception as e:
        print(Fore.RED + f"NTP test error: {e}")

def ssl_checker_direct(hostname):
    if not hostname:
        print(Fore.RED + "No hostname provided.")
        return
    try:
        context = ssl.create_default_context()
        conn = context.wrap_socket(socket.socket(socket.AF_INET), server_hostname=hostname)
        conn.settimeout(5.0)
        conn.connect((hostname, 443))
        cert = conn.getpeercert()
        expiry_date = cert['notAfter']
        expire_datetime = datetime.datetime.strptime(expiry_date, "%b %d %H:%M:%S %Y %Z")
        days_left = (expire_datetime - datetime.datetime.utcnow()).days
        print(Fore.CYAN + f"\n SSL Certificate for {hostname} expires on: {expiry_date} ({days_left} days left)\n")
    except Exception as e:
        print(Fore.RED + f"SSL check error: {e}")
