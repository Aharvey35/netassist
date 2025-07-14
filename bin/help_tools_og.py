# help_tools.py - Tactical Help Console for NetAssist
from colorama import Fore

def run():
    from net_assistant import paginate_output  # Import your paging function!

    lines = []
    lines.append(Fore.CYAN + "\n==== NetAssist Help Console ====")
    lines.append(Fore.YELLOW + "\n🔥 Pro Tip: Type 'shortcuts' anytime to see quick aliases and command mappings!\n")

    sections = {
        "Core System Commands": [
            ("help", "Show this help menu"),
            ("clear", "Clear the terminal"),
            ("exit", "Exit NetAssist"),
            ("motd", "Display random motivational quote"),
            ("version", "Show current NetAssist version"),
            ("history", "Show your session command history"),
            ("ls", "Show categorized command groups"),
            ("masterkey", "Show categorized command MasterKey"),
        ],
        "Network Tools": [
            ("ping <host>", "Send ICMP echo requests to a target"),
            ("traceroute <host>", "Trace network path to target"),
            ("dnslookup <domain>", "DNS lookup for domain"),
            ("geoip <ip>", "Geolocation lookup for IP address"),
            ("publicip", "Check your public IP address"),
            ("subnetcalc <CIDR>", "Subnet calculator for given CIDR"),
            ("wildcardcalc <CIDR>", "Wildcard calculator for CIDR"),
            ("speedtest", "Run internet speedtest"),
            ("whois <domain>", "Whois lookup for domain registration info"),
            ("sslcheck <domain>", "SSL certificate checker"),
            ("ntptest <ntp server>", "NTP server sync test"),
        ],
        "System Tools": [
            ("stat", "System quick status: CPU, Memory, Storage"),
            ("ifconfig", "Display network interface configurations (Linux)"),
            ("ipconfig", "Display network configs (Windows-like ref)"),
            ("battery", "Display laptop battery status"),
        ],
        "Connection Tools": [
            ("ssh <user@host>", "SSH into a device or server"),
        ],
        "⚙️ Module-Based Tools (Interactive)": [
            ("system", "System monitoring module"),
            ("network", "Network troubleshooting module"),
            ("connect", "Connectivity shortcuts module"),
            ("security", "Security and firewall checker module"),
            ("repair", "Basic repair tool module"),
            ("notes", "Save and view operational notes"),
            ("dashboard", "Tactical live dashboard view"),
        ],
        "Alias Management Tools": [
            ("alias <shortcut> <command>", "Create custom shortcut commands"),
            ("savealias", "Save current aliases to file"),
            ("loadalias", "Load saved aliases from file"),
            ("shortcuts", "List current quick shortcuts"),
        ],
        "Fun / Bonus Tools": [
            ("ascii", "Display fun random ASCII art"),
            ("matrix", "Enter Matrix mode"),
            ("fireworks", "Display fireworks animation"),
            ("weather <city>", "Check weather by city"),
            ("crypto", "Check Bitcoin price (and more coming)"),
            ("fun", "Random tech jokes and trivia"),
        ]
    }

    for section, cmds in sections.items():
        lines.append(Fore.YELLOW + f"\n{section}")
        for cmd, desc in cmds:
            lines.append(Fore.RESET + f" - {cmd:<20} {desc}")
        lines.append("")  # Blank line spacer

    paginate_output(lines)
