# modules/wifi_scanner.py
import subprocess
import platform
import re
import os
from typing import List, Dict, Optional
from colorama import Fore
import logging
import csv
import time

# Default export directory
EXPORT_DIR = 'data/wifi_logs'
if not os.path.exists(EXPORT_DIR):
    os.makedirs(EXPORT_DIR)

class WiFiScanner:
    """
    Expert-level WiFi network scanner.
    Scans for nearby WiFi networks, displaying SSID, BSSID, signal strength, channel, encryption, and more.
    Supports Windows, Linux (using nmcli), macOS, and WSL (using Windows netsh) via platform-specific commands.
    Includes real-time scanning, filtering, and CSV export.
    Note: Signal strength units may vary by platform (% on Windows/Linux-nmcli, dBm on macOS).
    """

    def __init__(self):
        self.platform = platform.system().lower()
        self.is_wsl = self._check_if_wsl()
        self.logger = logging.getLogger(__name__)
        if self.platform not in ['windows', 'linux', 'darwin']:
            raise ValueError(f"Unsupported platform: {self.platform}")

    def _check_if_wsl(self) -> bool:
        """Check if running in WSL environment."""
        if 'WSL' in os.environ.get('WSL_DISTRO_NAME', ''):
            return True
        try:
            with open('/proc/version', 'r') as f:
                if 'microsoft' in f.read().lower():
                    return True
        except FileNotFoundError:
            pass
        return False

    def _run_command(self, cmd: List[str]) -> str:
        """Run a subprocess command and return output."""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command '{cmd}' failed with exit code {e.returncode}: {e.stderr}")
            print(Fore.RED + f"Error running command '{cmd}': {e.stderr or 'Unknown error'} (exit code {e.returncode})")
            return ""
        except FileNotFoundError:
            self.logger.error("Required command not found. Ensure WiFi tools are installed (e.g., nmcli on Linux, airport on macOS, netsh on Windows/WSL).")
            print(Fore.RED + "Required command not found. Ensure WiFi tools are installed (e.g., nmcli on Linux, airport on macOS, netsh on Windows/WSL).")
            return ""

    def _diagnose(self):
        """Platform-specific diagnostics for WiFi issues."""
        print(Fore.YELLOW + "\nRunning WiFi diagnostics...")
        if self.platform == 'linux' and self.is_wsl:
            print(Fore.YELLOW + "Detected WSL environment. Running Windows diagnostics via netsh.exe.")
            interfaces = self._run_command(['netsh.exe', 'wlan', 'show', 'interfaces'])
            print(Fore.CYAN + "WiFi Interfaces (via netsh):")
            print(interfaces)
            if 'There is no wireless interface' in interfaces:
                print(Fore.RED + "No wireless interface found on Windows host. Ensure WiFi is enabled on Windows.")
            drivers = self._run_command(['netsh.exe', 'wlan', 'show', 'drivers'])
            print(Fore.CYAN + "WiFi Drivers (via netsh):")
            print(drivers)
            return
        
        if self.platform == 'linux':
            radio_status = self._run_command(['nmcli', 'radio', 'wifi'])
            print(Fore.CYAN + f"WiFi radio status: {radio_status.strip()}")
            if 'disabled' in radio_status.lower():
                print(Fore.YELLOW + "WiFi radio is disabled. Enabling...")
                enable_output = self._run_command(['nmcli', 'radio', 'wifi', 'on'])
                print(Fore.CYAN + f"Enable output: {enable_output.strip()}")
            
            device_status = self._run_command(['nmcli', 'device', 'status'])
            print(Fore.CYAN + "Device status:")
            print(device_status)
            
            if 'wifi' not in device_status.lower():
                print(Fore.RED + "No WiFi device found. Check 'rfkill list' for blocks or ensure drivers/firmware are installed.")
            
            rfkill = self._run_command(['rfkill', 'list'])
            print(Fore.CYAN + "rfkill status:")
            print(rfkill)
        
        if self.platform == 'windows':
            interfaces = self._run_command(['netsh', 'wlan', 'show', 'interfaces'])
            print(Fore.CYAN + "WiFi Interfaces:")
            print(interfaces)
            drivers = self._run_command(['netsh', 'wlan', 'show', 'drivers'])
            print(Fore.CYAN + "WiFi Drivers:")
            print(drivers)

    def _parse_windows_output(self, output: str) -> List[Dict]:
        """Parse netsh wlan show networks output on Windows/WSL."""
        networks = []
        current_ssid = None
        current_network = {}
        lines = output.splitlines()
        for line in lines:
            line = line.strip()
            if line.startswith('SSID'):
                if current_ssid:
                    networks.append(current_network)
                current_ssid = line.split(':', 1)[1].strip()
                current_network = {
                    "SSID": current_ssid,
                    "BSSID": "N/A",
                    "Signal": 0,
                    "Channel": "N/A",
                    "Encryption": "N/A",
                    "Unit": "%"
                }
            elif line.startswith('Network type'):
                continue  # Skip
            elif line.startswith('Authentication'):
                auth = line.split(':', 1)[1].strip()
                current_network["Encryption"] = auth if "Encryption" not in current_network else current_network["Encryption"] + " / " + auth
            elif line.startswith('Encryption'):
                enc = line.split(':', 1)[1].strip()
                current_network["Encryption"] = current_network.get("Encryption", "") + " / " + enc
            elif line.startswith('BSSID'):
                bssid = line.split(':', 1)[1].strip()
                current_network["BSSID"] = bssid
            elif line.startswith('Signal'):
                signal = int(line.split(':', 1)[1].strip().rstrip('%'))
                current_network["Signal"] = signal
            elif line.startswith('Radio type'):
                # Could add if needed
                pass
            elif line.startswith('Channel'):
                channel = line.split(':', 1)[1].strip()
                current_network["Channel"] = channel
        if current_ssid:
            networks.append(current_network)
        return networks

    def _parse_linux_nmcli_output(self, output: str) -> List[Dict]:
        """Parse nmcli device wifi list output on Linux."""
        networks = []
        lines = output.strip().split('\n')[1:]  # Skip header
        for line in lines:
            if line.startswith('*'):  # Active connection marker
                line = line[1:].strip()
            parts = re.split(r'\s{2,}', line)
            if len(parts) < 7:
                continue
            bssid = parts[0]
            ssid = parts[1]
            # Skip MODE (parts[2])
            chan = int(parts[3])
            # Skip RATE (parts[4])
            signal = int(parts[5])
            security = ' '.join(parts[7:]) if len(parts) > 7 else parts[6]
            
            networks.append({
                "SSID": ssid,
                "BSSID": bssid,
                "Signal": signal,
                "Channel": chan,
                "Encryption": security if security != '--' else "Open",
                "Unit": "%"
            })
        return networks

    def _parse_macos_output(self, output: str) -> List[Dict]:
        """Parse airport -s output on macOS."""
        networks = []
        lines = output.splitlines()[1:]
        for line in lines:
            parts = re.split(r'\s{2,}', line.strip())
            if len(parts) < 6:
                continue
            ssid = parts[0]
            bssid = parts[1]
            signal = int(parts[2])
            channel = parts[3]
            security = parts[5]
            
            networks.append({
                "SSID": ssid,
                "BSSID": bssid,
                "Signal": signal,
                "Channel": channel,
                "Encryption": security,
                "Unit": "dBm"
            })
        return networks

    def scan_wifi(self) -> List[Dict]:
        """Scan for nearby WiFi networks based on platform, with WSL support."""
        self._diagnose()  # Run diagnostics before scanning
        
        if self.platform == 'windows' or (self.platform == 'linux' and self.is_wsl):
            cmd = ['netsh.exe' if self.is_wsl else 'netsh', 'wlan', 'show', 'networks', 'mode=Bssid']
            output = self._run_command(cmd)
            return self._parse_windows_output(output)
        elif self.platform == 'linux':
            # Try with rescan, if fails, try without
            output = self._run_command(['nmcli', 'device', 'wifi', 'list', '--rescan', 'yes'])
            if not output.strip():
                print(Fore.YELLOW + "Rescan failed, trying without rescan...")
                output = self._run_command(['nmcli', 'device', 'wifi', 'list'])
            return self._parse_linux_nmcli_output(output)
        elif self.platform == 'darwin':
            output = self._run_command(['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', '-s'])
            return self._parse_macos_output(output)
        return []

    def list_networks(self, min_signal: Optional[int] = None):
        """List scanned WiFi networks with optional signal filter."""
        networks = self.scan_wifi()
        if min_signal is not None:
            networks = [n for n in networks if n["Signal"] >= min_signal]  # Note: For dBm, higher (less negative) is better, but filter assumes > min

        if not networks:
            print(Fore.YELLOW + "\nNo WiFi networks found or matching filter.")
            print(Fore.YELLOW + "Troubleshooting tips:")
            if self.is_wsl:
                print(" - In WSL, ensure Windows WiFi is enabled and the adapter is active (check Windows Settings > Network & Internet > Wi-Fi).")
                print(" - Run 'netsh wlan show networks mode=Bssid' in Windows PowerShell/Command Prompt to verify.")
            else:
                print(" - Ensure WiFi is enabled (nmcli radio wifi on)")
                print(" - Check device status (nmcli device status)")
                print(" - Unblock if soft/hard blocked (rfkill unblock wifi)")
                print(" - Install linux-firmware if missing")
                print(" - Restart NetworkManager (systemctl restart NetworkManager)")
            return

        print(Fore.CYAN + "\nNearby WiFi Networks:")
        header = "{:<32} | {:<17} | {:>6} | {:>7} | {:<20}".format(
            "SSID", "BSSID", "Signal", "Channel", "Encryption"
        )
        print(Fore.YELLOW + header)
        print("-" * len(header))

        data_log = [[n["SSID"], n["BSSID"], n["Signal"], n["Channel"], n["Encryption"]] for n in networks]

        for net in sorted(networks, key=lambda x: x["Signal"], reverse=True):
            if net["Unit"] == "%":
                signal_color = Fore.GREEN if net["Signal"] > 70 else Fore.YELLOW if net["Signal"] > 40 else Fore.RED
            else:  # dBm
                signal_color = Fore.GREEN if net["Signal"] > -60 else Fore.YELLOW if net["Signal"] > -80 else Fore.RED
            print(Fore.RESET + "{:<32} | {:<17} | {} {:>6}{} {} | {:>7} | {:<20}".format(
                net["SSID"], net["BSSID"], signal_color, net["Signal"], net["Unit"], Fore.RESET, net["Channel"], net["Encryption"]
            ))
        print()

        self.logger.info(f"Scanned {len(networks)} WiFi networks.")
        self._offer_export(data_log)

    def real_time_scan(self, interval: float = 10.0, duration: Optional[int] = None):
        """Real-time WiFi scanning to detect changes in networks."""
        print(Fore.CYAN + f"\nReal-Time WiFi Scan (interval: {interval}s, Ctrl+C to stop)...")
        if duration:
            print(Fore.YELLOW + f"Duration: {duration} seconds")

        old_networks = set(tuple(sorted(n.items())) for n in self.scan_wifi())
        start_time = time.time()

        try:
            while True:
                time.sleep(interval)
                new_networks = set(tuple(sorted(n.items())) for n in self.scan_wifi())
                
                added = new_networks - old_networks
                removed = old_networks - new_networks

                if added or removed:
                    print(Fore.GREEN + f"\nChanges at {time.strftime('%H:%M:%S')}:")
                    if added:
                        print(Fore.GREEN + "New Networks:")
                        for net in added:
                            net_dict = dict(net)
                            print(f"  {net_dict['SSID']} ({net_dict['BSSID']}, Signal: {net_dict['Signal']}{net_dict['Unit']})")
                    if removed:
                        print(Fore.RED + "Removed Networks:")
                        for net in removed:
                            net_dict = dict(net)
                            print(f"  {net_dict['SSID']} ({net_dict['BSSID']})")
                    self.logger.info(f"Detected {len(added)} new and {len(removed)} removed WiFi networks.")

                old_networks = new_networks

                if duration and (time.time() - start_time) >= duration:
                    break
        except KeyboardInterrupt:
            print(Fore.YELLOW + "\nReal-time scanning stopped.")

    def _offer_export(self, data_log: List[List]):
        """Offer to export WiFi data to CSV."""
        if not data_log:
            return
        choice = input(Fore.YELLOW + "\nExport WiFi networks to CSV? (y/n): ").strip().lower()
        if choice == 'y':
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(EXPORT_DIR, f"wifi_scan_{timestamp}.csv")
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["SSID", "BSSID", "Signal", "Channel", "Encryption"])
                writer.writerows(data_log)
            print(Fore.GREEN + f"Data exported to {filename}")
            self.logger.info(f"Exported WiFi scan data to {filename}")

def run():
    try:
        scanner = WiFiScanner()
    except ValueError as e:
        print(Fore.RED + str(e))
        return

    print(Fore.CYAN + "\nExpert WiFi Scanner Tools")
    print("Options:")
    print("  1. Scan and List Networks")
    print("  2. Real-Time Network Changes")
    print("  3. Exit")
    
    choice = input("\nChoose an option: ").strip()
    
    if choice == '1':
        min_signal_str = input("Minimum signal strength (e.g., 50 for 50%, -70 for dBm, or Enter for all): ").strip()
        min_signal = int(min_signal_str) if min_signal_str.lstrip('-').isdigit() else None
        scanner.list_networks(min_signal)
    elif choice == '2':
        interval_str = input("Enter interval in seconds (default 10): ").strip() or "10"
        interval = float(interval_str) if interval_str.replace('.', '', 1).isdigit() else 10.0
        duration_str = input("Enter duration in seconds (or Enter for indefinite): ").strip()
        duration = int(duration_str) if duration_str.isdigit() else None
        scanner.real_time_scan(interval, duration)
    elif choice == '3':
        print(Fore.YELLOW + "\nReturning to main NetAssist console...\n")
    else:
        print(Fore.RED + "\nInvalid choice.\n")

def wifi_direct(min_signal: Optional[int] = None):
    """Direct CLI command handler for quick WiFi scan."""
    try:
        scanner = WiFiScanner()
        scanner.list_networks(min_signal)
    except ValueError as e:
        print(Fore.RED + str(e))