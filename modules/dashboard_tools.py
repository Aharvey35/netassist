# modules/dashboard_tools.py

import os
import time
import psutil
import subprocess
import statistics
from datetime import datetime
import socket
import shutil

# === Helper Functions ===
def get_default_gateway():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()

        parts = local_ip.split('.')
        gateway = f"{parts[0]}.{parts[1]}.{parts[2]}.1"
        return gateway
    except Exception:
        return "192.168.1.1"  # fallback

def centered_print(text):
    columns = shutil.get_terminal_size().columns
    print(text.center(columns))

GATEWAY_IP = get_default_gateway()
INTERNET_IP = "8.8.8.8"

LIVE_TARGETS = [
    ("GW", GATEWAY_IP),
    ("NET", INTERNET_IP)
]

def ping(host):
    try:
        output = subprocess.check_output(["ping", "-c", "1", "-W", "1", host], stderr=subprocess.DEVNULL)
        output = output.decode('utf-8')
        time_ms = float(output.split('time=')[1].split(' ')[0])
        return time_ms
    except Exception:
        return None

def display_bar(label, percent, critical=80, warning=50):
    blocks = int((percent / 100) * 30)
    bar = '█' * blocks + ' ' * (30 - blocks)

    if percent >= critical:
        color = "\033[91m"  # Red
    elif percent >= warning:
        color = "\033[93m"  # Yellow
    else:
        color = "\033[92m"  # Green

    reset = "\033[0m"
    return f"{label}: {color}[{bar}] {percent:.1f}%{reset}"

def clear_screen_soft():
    print("\033c", end="")  # ANSI clear

# === Tactical Live Monitor ===
def start_dashboard():
    latencies = []

    try:
        while True:
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory()

            target_results = []
            for label, ip in LIVE_TARGETS:
                latency = ping(ip)
                target_results.append((label, ip, latency))

                if latency:
                    latencies.append(latency)

            if len(latencies) >= 2:
                recent_latencies = latencies[-10:] if len(latencies) >= 10 else latencies
                jitter = statistics.stdev(recent_latencies)
            else:
                jitter = None

            clear_screen_soft()

            centered_print("===============================================")
            centered_print("NetAssist LIVE Modular Dashboard")
            centered_print(f"Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            centered_print("===============================================")

            centered_print(display_bar("🧠 CPU", cpu))
            centered_print(display_bar("💾 MEM", mem.percent))

            for label, ip, latency in target_results:
                if latency is not None:
                    centered_print(f"{label} ({ip}): {latency:.1f} ms (OK)")
                else:
                    centered_print(f"{label} ({ip}): No Response (DOWN)")

            if jitter is not None:
                centered_print(f"📡 Jitter: {jitter:.1f} ms")
            else:
                centered_print("📡 Jitter: Calculating...")

            centered_print("===============================================")
            centered_print("CTRL+C to exit")

    except KeyboardInterrupt:
        print("\n\n🚪 Exiting Live Dashboard...\n")

# === Silent Operator Dashboard Control ===
def run():
    while True:
        try:
            clear_screen_soft()
            print("\n--- NetAssist Dashboard Control ---")
            print("Available Commands: start | add <label> <ip> | remove <label> | list | exit\n")
            cmd = input("[dashboard]> ").strip()

            if not cmd:
                continue

            parts = cmd.split()

            if parts[0] == "start":
                start_dashboard()

            elif parts[0] == "list":
                clear_screen_soft()
                print("\n📋 Current Monitored Targets:\n")
                for label, ip in LIVE_TARGETS:
                    print(f" - {label}: {ip}")
                print("\nAvailable Commands: start | add label ip | remove label | list | exit\n")

            elif parts[0] == "add" and len(parts) == 3:
                label = parts[1].upper()
                ip = parts[2]
                LIVE_TARGETS.append((label, ip))
                clear_screen_soft()
                print(f"\n✅ Target '{label}' ({ip}) added.\n")
                print("Available Commands: start | add label ip | remove label | list | exit\n")

            elif parts[0] == "remove" and len(parts) == 2:
                label = parts[1].upper()
                before = len(LIVE_TARGETS)
                LIVE_TARGETS[:] = [(l, i) for (l, i) in LIVE_TARGETS if l != label]
                clear_screen_soft()
                if len(LIVE_TARGETS) < before:
                    print(f"\n✅ Target '{label}' removed.\n")
                else:
                    print(f"\n⚠️ Target '{label}' not found.\n")
                print("Available Commands: start | add label ip | remove label | list | exit\n")

            elif parts[0] == "exit":
                print("\n🚪 Returning to main NetAssist console.\n")
                break

            else:
                clear_screen_soft()
                print("\n⚠️ Unknown dashboard command.\n")
                print("Available Commands: start | add label ip | remove label | list | exit\n")

        except KeyboardInterrupt:
            print("\n\n🚪 Returning to main NetAssist console.\n")
            break
