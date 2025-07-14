# modules/port_check.py
import socket
import time
from colorama import Fore
import logging
import re

def run():
    print(Fore.CYAN + "\n Port Check Tools")
    print("Options:")
    print("  1. Check Single Port")
    print("  2. Check Multiple Ports")
    print("  3. Check Common Ports")
    print("  4. Exit")
    
    choice = input("\nChoose an option: ").strip()
    
    if choice == '1':
        check_single_port()
    elif choice == '2':
        check_multiple_ports()
    elif choice == '3':
        check_common_ports()
    elif choice == '4':
        print(Fore.YELLOW + "\nReturning to main NetAssist console...\n")
    else:
        print(Fore.RED + "\nInvalid choice.\n")

def check_single_port():
    host = input("Enter hostname or IP: ").strip()
    port = input("Enter port number: ").strip()
    if validate_inputs(host, [port]):
        result = check_port(host, int(port))
        print_result(host, port, result)
        logging.info(f"Port check: {host}:{port} - {result}")

def check_multiple_ports():
    host = input("Enter hostname or IP: ").strip()
    ports_input = input("Enter ports (comma-separated, e.g., 80,443,22): ").strip()
    ports = [p.strip() for p in ports_input.split(",")]
    if validate_inputs(host, ports):
        for port in ports:
            result = check_port(host, int(port))
            print_result(host, port, result)
            logging.info(f"Port check: {host}:{port} - {result}")
            time.sleep(0.1)  # Small delay to avoid overwhelming the target

def check_common_ports():
    host = input("Enter hostname or IP: ").strip()
    common_ports = [22, 80, 443, 3389, 445, 21, 23, 25, 110, 143, 3306]
    print(Fore.CYAN + f"\nChecking common ports on {host}: {', '.join(map(str, common_ports))}\n")
    if validate_inputs(host, common_ports):
        for port in common_ports:
            result = check_port(host, port)
            print_result(host, port, result)
            logging.info(f"Port check: {host}:{port} - {result}")
            time.sleep(0.1)  # Small delay to avoid overwhelming the target

def validate_inputs(host, ports):
    """Validate host and port inputs."""
    if not host:
        print(Fore.RED + "Error: No hostname or IP provided.")
        return False
    
    # Validate host (basic check for IP or domain format)
    ip_pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    domain_pattern = r"^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9](?:\.[a-zA-Z]{2,})+$"
    if not (re.match(ip_pattern, host) or re.match(domain_pattern, host) or host == "localhost"):
        print(Fore.RED + "Error: Invalid hostname or IP format.")
        return False
    
    # Validate ports
    try:
        for port in ports:
            p = int(port)
            if not (1 <= p <= 65535):
                print(Fore.RED + f"Error: Port {port} is out of valid range (1-65535).")
                return False
    except ValueError:
        print(Fore.RED + "Error: Ports must be valid integers.")
        return False
    
    return True

def check_port(host, port):
    """Check if a port is open on the target host."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)  # 2-second timeout for responsiveness
    try:
        result = sock.connect_ex((host, port))
        sock.close()
        return "Open" if result == 0 else "Closed"
    except socket.gaierror:
        return "Error: Host not found"
    except Exception as e:
        return f"Error: {e}"

def check_port_nc(host, port):
    """Netcat-style port check for direct CLI usage."""
    result = check_port(host, port)
    status = Fore.GREEN + result if result == "Open" else Fore.RED + result if "Error" in result else Fore.YELLOW + result
    return f"{host}:{port} - {status}"

def print_result(host, port, result):
    """Print port check result in a formatted way."""
    if result == "Open":
        print(Fore.GREEN + f"{host}:{port} - Open")
    elif "Error" in result:
        print(Fore.RED + f"{host}:{port} - {result}")
    else:
        print(Fore.YELLOW + f"{host}:{port} - Closed")

def port_check_direct(host, ports):
    """Direct CLI command handler for portcheck <host> <port(s)>."""
    if not validate_inputs(host, ports):
        return
    for port in ports:
        result = check_port(host, int(port))
        print_result(host, port, result)
        logging.info(f"Port check: {host}:{port} - {result}")
        time.sleep(0.1)  # Small delay to avoid overwhelming the target
