# modules/bandwidth_monitor.py
import psutil
import time
import csv
import os
from typing import Dict, Optional, List, Tuple
from colorama import Fore
import logging

# Constants for unit conversions
BYTES_TO_MBPS = 8 / 1_000_000  # Bytes to Mbps factor (8 bits/byte, /1e6 for Mega)
PACKETS_TO_PPS = 1  # Packets per second (direct)

# Default monitoring interval in seconds
DEFAULT_INTERVAL = 1.0

# Default export directory
EXPORT_DIR = 'data/bandwidth_logs'
if not os.path.exists(EXPORT_DIR):
    os.makedirs(EXPORT_DIR)

class BandwidthMonitor:
    """
    Expert-level bandwidth and network stats monitor using psutil.
    Supports real-time rate calculations for bytes, packets, errors, and drops.
    Includes interface validation, export to CSV, and comprehensive stats.
    """

    def __init__(self):
        self.interfaces = self._get_interfaces()
        self.logger = logging.getLogger(__name__)

    def _get_interfaces(self) -> List[str]:
        """Retrieve list of available network interfaces."""
        try:
            return list(psutil.net_if_addrs().keys())
        except Exception as e:
            self.logger.error(f"Error retrieving interfaces: {e}")
            print(Fore.RED + f"Error retrieving interfaces: {e}")
            return []

    def _validate_interface(self, iface: str) -> bool:
        """Validate if the interface exists."""
        if iface not in self.interfaces:
            print(Fore.RED + f"Invalid interface: {iface}. Available: {', '.join(self.interfaces)}")
            return False
        return True

    def _get_io_counters(self, pernic: bool = True) -> Dict[str, psutil._common.snetio]:
        """Get network IO counters with nowrap to prevent wrapping issues."""
        return psutil.net_io_counters(pernic=pernic, nowrap=True)

    def _get_interface_stats(self, iface: Optional[str] = None) -> Dict:
        """Get additional interface stats like speed, duplex, MTU."""
        stats = psutil.net_if_stats()
        if iface:
            return stats.get(iface, {})
        return stats

    def _calculate_rates(
        self,
        old_stats: psutil._common.snetio,
        new_stats: psutil._common.snetio,
        interval: float
    ) -> Tuple[float, float, float, float, int, int, int, int]:
        """Calculate rates for bandwidth, packets, errors, and drops."""
        if not old_stats or not new_stats:
            return 0.0, 0.0, 0.0, 0.0, 0, 0, 0, 0

        sent_mbps = (new_stats.bytes_sent - old_stats.bytes_sent) * BYTES_TO_MBPS / interval
        recv_mbps = (new_stats.bytes_recv - old_stats.bytes_recv) * BYTES_TO_MBPS / interval
        sent_pps = (new_stats.packets_sent - old_stats.packets_sent) / interval
        recv_pps = (new_stats.packets_recv - old_stats.packets_recv) / interval
        errin = new_stats.errin - old_stats.errin
        errout = new_stats.errout - old_stats.errout
        dropin = new_stats.dropin - old_stats.dropin
        dropout = new_stats.dropout - old_stats.dropout

        return sent_mbps, recv_mbps, sent_pps, recv_pps, errin, errout, dropin, dropout

    def list_interfaces(self):
        """List available network interfaces with additional stats."""
        print(Fore.CYAN + "\nAvailable Network Interfaces:")
        stats = self._get_interface_stats()
        for iface in self.interfaces:
            iface_stats = stats.get(iface, {})
            speed = iface_stats.speed if hasattr(iface_stats, 'speed') else 'N/A'
            duplex = iface_stats.duplex if hasattr(iface_stats, 'duplex') else 'N/A'
            mtu = iface_stats.mtu if hasattr(iface_stats, 'mtu') else 'N/A'
            print(Fore.GREEN + f"  - {iface}: Speed={speed} Mbps, Duplex={duplex}, MTU={mtu}")
        print()
        self.logger.info("Listed network interfaces with stats.")

    def real_time_monitor(self, iface: Optional[str] = None, duration: Optional[int] = None):
        """Real-time monitoring with rate calculations for all metrics."""
        if iface and not self._validate_interface(iface):
            return

        print(Fore.CYAN + f"\nReal-Time Monitoring on {iface or 'all interfaces'} (Ctrl+C to stop)...")
        if duration:
            print(Fore.YELLOW + f"Duration: {duration} seconds")
        
        header = "{:<8} | {:>10} | {:>10} | {:>8} | {:>8} | {:>5} | {:>5} | {:>6} | {:>7}".format(
            "Time", "Sent Mbps", "Recv Mbps", "Sent PPS", "Recv PPS", "ErrIn", "ErrOut", "DropIn", "DropOut"
        )
        print(Fore.YELLOW + header)
        print("-" * len(header))

        old_stats = self._get_io_counters(pernic=True)
        start_time = time.time()
        data_log = []  # For potential export

        try:
            while True:
                time.sleep(DEFAULT_INTERVAL)
                new_stats = self._get_io_counters(pernic=True)
                current_time = time.strftime('%H:%M:%S')

                if iface:
                    rates = self._calculate_rates(old_stats.get(iface), new_stats.get(iface), DEFAULT_INTERVAL)
                    print(Fore.RESET + "{:<8} | {:>10.2f} | {:>10.2f} | {:>8.2f} | {:>8.2f} | {:>5} | {:>5} | {:>6} | {:>7}".format(
                        current_time, rates[0], rates[1], rates[2], rates[3], rates[4], rates[5], rates[6], rates[7]
                    ))
                    data_log.append((current_time, iface, *rates))
                else:
                    for if_name in self.interfaces:
                        rates = self._calculate_rates(old_stats.get(if_name), new_stats.get(if_name), DEFAULT_INTERVAL)
                        print(Fore.RESET + "[{0}] {1:<8} | {2:>10.2f} | {3:>10.2f} | {4:>8.2f} | {5:>8.2f} | {6:>5} | {7:>5} | {8:>6} | {9:>7}".format(
                            if_name, current_time, rates[0], rates[1], rates[2], rates[3], rates[4], rates[5], rates[6], rates[7]
                        ))
                        data_log.append((current_time, if_name, *rates))

                old_stats = new_stats
                self.logger.info(f"Real-time bandwidth monitored for {iface or 'all interfaces'}")

                if duration and (time.time() - start_time) >= duration:
                    break
        except KeyboardInterrupt:
            print(Fore.YELLOW + "\nReal-time monitoring stopped.")
        
        if data_log:
            self._offer_export(data_log)

    def bandwidth_summary(self, iface: Optional[str] = None):
        """Display comprehensive summary of total network stats."""
        if iface and not self._validate_interface(iface):
            return

        stats = self._get_io_counters(pernic=True)
        print(Fore.CYAN + f"\nBandwidth Summary for {iface or 'all interfaces'}:")
        
        if iface:
            stat = stats.get(iface)
            if stat:
                self._print_summary_row(iface, stat)
                self.logger.info(f"Bandwidth summary for {iface}: {stat}")
        else:
            for if_name, stat in stats.items():
                self._print_summary_row(if_name, stat)
                self.logger.info(f"Bandwidth summary for {if_name}: {stat}")
        print()

    def _print_summary_row(self, iface: str, stat: psutil._common.snetio):
        """Helper to print summary row."""
        print(Fore.GREEN + f"  [{iface}]")
        print(f"    Bytes Sent: {stat.bytes_sent / 1_048_576:.2f} MB")
        print(f"    Bytes Received: {stat.bytes_recv / 1_048_576:.2f} MB")
        print(f"    Packets Sent: {stat.packets_sent}")
        print(f"    Packets Received: {stat.packets_recv}")
        print(f"    Errors In/Out: {stat.errin} / {stat.errout}")
        print(f"    Drops In/Out: {stat.dropin} / {stat.dropout}")

    def _offer_export(self, data_log: List[Tuple]):
        """Offer to export monitored data to CSV."""
        choice = input(Fore.YELLOW + "\nExport data to CSV? (y/n): ").strip().lower()
        if choice == 'y':
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(EXPORT_DIR, f"bandwidth_log_{timestamp}.csv")
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Time", "Interface", "Sent Mbps", "Recv Mbps", "Sent PPS", "Recv PPS", "ErrIn", "ErrOut", "DropIn", "DropOut"])
                writer.writerows(data_log)
            print(Fore.GREEN + f"Data exported to {filename}")
            self.logger.info(f"Exported bandwidth data to {filename}")

def run():
    monitor = BandwidthMonitor()
    print(Fore.CYAN + "\nExpert Bandwidth Monitor Tools")
    print("Options:")
    print("  1. List Network Interfaces")
    print("  2. Real-Time Monitor (Interactive)")
    print("  3. Bandwidth Summary")
    print("  4. Exit")
    
    choice = input("\nChoose an option: ").strip()
    
    if choice == '1':
        monitor.list_interfaces()
    elif choice == '2':
        iface = input("Enter interface (or Enter for all): ").strip() or None
        duration_str = input("Enter duration in seconds (or Enter for indefinite): ").strip()
        duration = int(duration_str) if duration_str.isdigit() else None
        monitor.real_time_monitor(iface, duration)
    elif choice == '3':
        iface = input("Enter interface (or Enter for all): ").strip() or None
        monitor.bandwidth_summary(iface)
    elif choice == '4':
        print(Fore.YELLOW + "\nReturning to main NetAssist console...\n")
    else:
        print(Fore.RED + "\nInvalid choice.\n")

def bandwidth_direct(iface: Optional[str] = None):
    """Direct CLI command handler for quick 10-second bandwidth check."""
    monitor = BandwidthMonitor()
    if iface and not monitor._validate_interface(iface):
        return
    
    print(Fore.CYAN + f"\nQuick Bandwidth Check on {iface or 'all interfaces'} for 10 seconds...")
    monitor.real_time_monitor(iface, duration=10)