# modules/master_key.py
from colorama import Fore

def show_master_key():
    print(Fore.CYAN + """
============= NetAssist Pro 4.5 Master Command List =============

Core Commands:
- help              Show basic help
- version           Show version info
- motd              Show random quote
- history           Show command history
- clear / cls       Clear the screen
- ls                List top-level modules

Habit Shortcuts:
- ifconfig          Show Linux network config (maps to 'ip a')
- ipconfig          Windows-style alias for 'ip a'
- ssh user@host     Native ssh support
- tracert target    Native traceroute shortcut

Direct Network Commands:
- ping target       Ping an IP or domain
- traceroute target Traceroute to a domain or IP
- dnslookup domain  DNS resolve
- geoip IP          GeoIP lookup
- publicip          Your public IP address
- subnetcalc CIDR   Subnet calculator (e.g., subnetcalc 10.0.0.0/24)
- wildcardcalc CIDR Wildcard mask calculator (e.g., wildcardcalc 10.0.0.0/24)
- speedtest         Run speedtest
- portcheck         Check if port(s) are open (e.g., portcheck 192.168.1.1 80,443)

Direct Security Commands:
- whois domain      Whois lookup
- password          Enter a PW Mgmt Menu

Direct Bonus Tools:
- sslcheck domain   SSL Certificate checker + days left
- ntptest ntpserver Check if NTP server is reachable

Fun/Utility:
- ascii             Show banner and tip of the day
- weather city      (coming in Phase 2!)

===============================================================
""")
