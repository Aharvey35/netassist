# modules/ascii_art.py
from colorama import Fore
import random

BANNERS = [
    "╔═╗┬ ┬┌─┐┬ ┬┌┬┐",
    "║  ├─┤├─┤│││ ││",
    "╚═╝┴ ┴┴ ┴└┴┘─┴┘",
    " NetAssist: Master your network."
    " Fast. Smart. Tactical. NetAssist Pro 4.5",
    " Launch. Analyze. Dominate."
]

TIPS = [
    "Use tab-completion to save precious seconds!",
    "Need a public IP lookup? 'network' ➔ '1' or type 'publicip' direct.",
    "Subnet calculator saves lives. Try 'subnetcalc 10.1.1.0/24'.",
    "Ifconfig old habit? No worries, just type 'ifconfig'.",
    "Ping 8.8.8.8 instantly with 'ping 8.8.8.8'.",
    "Wildcard masks made easy: 'wildcardcalc 192.168.0.0/24'.",
    "Run 'ascii' anytime for inspiration and tactics."
]

def run():
    print("\n ASCII Art + Tactical Tip:")
    print(Fore.MAGENTA + random.choice(BANNERS))
    print(Fore.YELLOW + f"\n Tip: {random.choice(TIPS)}\n")
