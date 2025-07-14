# modules/fun_tools.py
from colorama import Fore
import random
import time

def run():
    print("\n Fun Tools")
    print("Options:")
    print("  1. Random Hacker Phrase")
    print("  2. ASCII Fireworks")
    choice = input("\nChoose an option: ").strip()

    if choice == '1':
        hacker_phrase()
    elif choice == '2':
        fireworks()
    else:
        print(Fore.RED + "Invalid choice.")

import random
from colorama import Fore

def hacker_phrase():
    phrases = [
        "🔓 Breach detected. Initiating lockdown.",
        "👾 Hacking the Gibson...",
        "🛡️ Firewall breached. Deploying countermeasures.",
        "🌐 Node compromised. Retaliation sequence triggered.",
        "💻 Upload complete. Systems compromised.",
        "📡 Signal intercepted. Origin: Unknown.",
        "🧠 Brainwave synchronization successful.",
        "🔮 Quantum tunnel established. Awaiting payload.",
        "⛓️ Blockchain anomaly detected. Mining intervention.",
        "🛰️ Satellite uplink secure. Command injection active.",
        "🚨 Perimeter defenses neutralized. Proceeding to mainframe.",
        "🕶️ Agents spotted. Evading detection.",
        "🧬 Genetic firewall cracked. Replicating data strands.",
        "🕸️ Darknet gateway accessed. No witnesses.",
        "♻️ Loop exploit initiated. Memory overflow imminent.",
        "🧯 Suppressing alarms... Suppression failed. Going loud!",
        "⚡ Zero-day payload deployed. Exploit successful.",
        "📦 Encrypted payload received. Parsing contents.",
        "🛰️ Launching orbital drone reconnaissance.",
        "🔗 SSH chain completed. Session hijacked.",
        "🔏 SSL certificate spoofed. Traffic redirected.",
        "🛠️ Rootkit embedded successfully.",
        "💿 Backup server infiltrated. Extraction underway.",
        "👣 Tracks erased. No digital footprints remain.",
        "💣 Kernel panic triggered remotely.",
        "🌪️ Network flood initiated. Signal distortion rising.",
        "⛔ Access Control List bypassed.",
        "🔐 VPN tunnel forged. Anonymity secured.",
        "📍 Physical server located. Tactical breach possible.",
        "🎯 Target system locked. Awaiting command execution.",
        "🔋 Power surge simulation deployed. UPS compromised.",
        "🧹 Data sanitized. No evidence left behind.",
        "🔫 Engaging ICE. Countermeasures initiated.",
        "🕵️ Surveillance feed corrupted. Blind spots created.",
        "🌌 Quantum key exchange complete. Unbreakable encryption established.",
        "🛡️ Defense grid integrity reduced by 75%.",
        "⏳ Session timeout evasion active.",
        "🧬 DNA fingerprint database corrupted.",
        "🌑 New node registered to shadow network.",
        "🎲 Random number generator poisoned."
    ]

    print("\n" + Fore.CYAN + random.choice(phrases))

def fireworks():
    for _ in range(10):
        print(Fore.YELLOW + "✨ BOOM ✨ " * random.randint(1, 5))
        time.sleep(0.2)
