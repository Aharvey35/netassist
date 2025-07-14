# modules/help_tools.py

from colorama import Fore
import sys
import tty
import termios

def wait_for_space():
    """Wait for the spacebar to be pressed, then clean the prompt."""
    print(Fore.YELLOW + "\n[Press SPACE to continue...]", end="", flush=True)
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        while True:
            ch = sys.stdin.read(1)
            if ch == ' ':
                # Overwrite the [Press SPACE] line with spaces
                sys.stdout.write('\r' + ' ' * 40 + '\r')
                sys.stdout.flush()
                break
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def run():
    help_sections = [
        Fore.CYAN + "\n=== NetAssist Help System ===\n",
        
        Fore.YELLOW + "\nCore System Commands:\n" + Fore.RESET +
        "- help\n- clear\n- exit\n- motd\n- version\n- history\n- ls\n- masterkey\n",

        Fore.YELLOW + "\nNetwork Tools:\n" + Fore.RESET +
        "- ping\n- traceroute\n- dnslookup\n- geoip\n- publicip\n- subnetcalc\n- wildcardcalc\n- speedtest\n- whois\n- sslcheck\n- ntptest\n- portcheck\n- bandwidth\n",

        Fore.YELLOW + "\nSystem Tools:\n" + Fore.RESET +
        "- stat\n- ifconfig\n- password\n- ipconfig\n- battery\n- time\n",

        Fore.YELLOW + "\nConnection Tools:\n" + Fore.RESET +
        "- ssh\n",

        Fore.YELLOW + "\nAdmin / Repair Tools (Module Based *):\n" + Fore.RESET +
        "- system (*)\n- network (*)\n- security (*)\n- repair (*)\n- notes (*)\n- sysadmin (*)\n- dashboard (*)\n",

        Fore.YELLOW + "\nScanning Tools:\n" + Fore.RESET +
        "- scan\n- netscan (*)\n",

        Fore.YELLOW + "\nAlias Management:\n" + Fore.RESET +
        "- alias\n- savealias\n- loadalias\n- shortcuts\n",

        Fore.YELLOW + "\nFun / Bonus Tools:\n" + Fore.RESET +
        "- ascii\n- matrix\n- fireworks\n- weather\n- crypto (*)\n- fun (*)\n",

        Fore.YELLOW + "\nRemote Management:\n" + Fore.RESET +
        "- rce\n- rceconnect\n",

        Fore.YELLOW + "\nThreat Intelligence:\n" + Fore.RESET +
        "- threatfeed\n",

        Fore.MAGENTA + "\nHelpful Tips:\n" + Fore.RESET +
        "- (*) indicates a module-based menu (interactive)\n" +
        "- Type 'shortcuts' for quick references.\n" +
        "- Use 'masterkey' for full categorized listing.\n" +
        "- 'scan' = simple single CIDR scan | 'netscan' = advanced scans.\n",

        Fore.CYAN + "\n=== End of Help ===\n"
    ]

    all_lines = []
    for section in help_sections:
        all_lines.extend(section.strip('\n').split('\n'))

    page_size = 18
    total_lines = len(all_lines)
    lines_printed = 0

    for idx, line in enumerate(all_lines):
        print(line)
        lines_printed += 1

        if lines_printed >= page_size and idx < (total_lines - 10):
            wait_for_space()
            lines_printed = 0  # Reset after space

