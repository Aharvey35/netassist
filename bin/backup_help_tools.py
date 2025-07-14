# modules/help_tools.py

from colorama import Fore

def run():
    pages = [
        Fore.CYAN + """

======================
🆘  NetAssist Help Menu
======================

Available Base Commands:
  - system          => Access system tools
  - network         => Access network tools
  - connect         => Access connection utilities
  - security        => Access security scanners
  - weather         => Fetch live weather
  - crypto          => Crypto tools and converters
  - fun             => Games and fun extras
  - repair          => Self-repair network services
  - dashboard       => Real-time system dashboard
  - scan            => Quick CIDR network scan
  - netscan         => Advanced scan manager (multi-subnet, file import)
  - shortcuts       => View shortcut reference
  - motd            => Fetch quote of the day

Quick Utilities:
  - ping <host>
  - traceroute <host>
  - dnslookup <domain>
  - geoip <ip>
  - publicip
  - whois <domain>
  - sslcheck <hostname>
  - ntptest <ntp server>
  - battery         => Check battery health
  - time            => Show local time
  - stat            => Quick system health
  - note add <note> => Add a note
  - note list       => View saved notes

Hot Keys / Useful Tips:
  - Type `shortcuts` to view all command shorthands.
  - Type `savealias` and `loadalias` to manage your personal aliases.
  - Type `clear` or `cls` to refresh the terminal view.
  - Use `< >` brackets to understand expected input (Cisco-style guidance).

Special:
  - Threatfeed       => Fetch live cybersecurity threat feeds
  - rce <target>     => Remote shell to saved devices

🚀 Keep building your empire, Commander {user_name} the {user_rank}!

Press [Space] to scroll or [Enter] to exit.

"""
    ]
    return pages
