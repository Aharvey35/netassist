import requests
import random
from datetime import datetime

TERMS = [
    "latency", "bandwidth", "firewall", "routing", "subnet",
    "dhcp", "dns", "vpn", "nat", "spoofing",
    "load balancing", "packet", "tcp", "udp", "encryption",
    "hashing", "honeypot", "tokenization", "snmp", "zero trust"
]

def run():
    try:
        print("\nRetrieving today's tech term...")
        term = random.choice(TERMS)
        definition, source = fetch_definition(term)

        print("\nTech Term of the Day:")
        print(f"  Term       : {term.title()}")
        print(f"  Definition : {definition}")
        print(f"  Source     : {source}")

        print("\nDate:", datetime.now().strftime("%A, %B %d, %Y"))

    except Exception as e:
        print(f"Error fetching tech term: {e}")

def fetch_definition(term):
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{term.replace(' ', '_')}"
    resp = requests.get(url, headers={"User-Agent": "NetAssistBot/1.0"})
    resp.raise_for_status()
    data = resp.json()

    if "extract" in data:
        definition = data["extract"]
        source = data.get("content_urls", {}).get("desktop", {}).get("page", "Wikipedia")
    else:
        definition = "No definition found."
        source = "Wikipedia"

    return definition, source
