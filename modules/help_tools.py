# modules/help_tools.py

from colorama import Fore
import sys
import tty
import termios
import shutil

def wait_for_space():
    """Pager: SPACE = next page, ENTER = one line, q = quit."""
    prompt_text = "[SPACE = page  ENTER = line  q = quit]"
    prompt = Fore.YELLOW + prompt_text + Fore.RESET
    print(prompt, end="", flush=True)
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        while True:
            ch = sys.stdin.read(1)
            if ch == ' ':
                _clear_prompt(len(prompt_text))
                return "page"
            if ch in ('\r', '\n'):
                _clear_prompt(len(prompt_text))
                return "line"
            if ch.lower() == 'q':
                _clear_prompt(len(prompt_text))
                return "quit"
            # ignore other keys
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def _clear_prompt(length):
    sys.stdout.write('\r' + ' ' * length + '\r')
    sys.stdout.flush()

def run():
    help_sections = [
        Fore.CYAN + "\n=== NetAssist Help System ===\n",

        Fore.YELLOW + "\nCore System Commands:\n" + Fore.RESET +
        "- help\n- clear\n- exit\n- motd\n- version\n- history\n- ls\n- masterkey\n",

        Fore.YELLOW + "\nNetwork Tools:\n" + Fore.RESET +
        "- ping\n- traceroute\n- dnslookup\n- geoip\n- publicip\n- subnetcalc\n"
        "- wildcardcalc\n- speedtest\n- whois\n- sslcheck\n- ntptest\n- portcheck\n- bandwidth\n",

        Fore.YELLOW + "\nSystem Tools:\n" + Fore.RESET +
        "- stat\n- ifconfig\n- ipconfig\n- battery\n- time\n",

        Fore.YELLOW + "\nConnection Tools:\n" + Fore.RESET +
        "- ssh\n- chrome\n",

        Fore.YELLOW + "\nAdmin / Repair Tools (Module Based *):\n" + Fore.RESET +
        "- system (*)\n- network (*)\n- passsword (*)\n- security (*)\n- repair (*)\n"
        "- notes (*)\n- sysadmin (*)\n- dashboard (*)\n",

        Fore.YELLOW + "\nScanning Tools:\n" + Fore.RESET +
        "- scan\n- netscan (*)\n",

        Fore.YELLOW + "\nAlias Management:\n" + Fore.RESET +
        "- alias <shortcut>\n- savealias\n- loadalias\n- shortcuts\n",

        Fore.YELLOW + "\nFun / Bonus Tools:\n" + Fore.RESET +
        "- ascii\n- matrix\n- fireworks\n- weather\n- crypto (*)\n- fun (*)\n",

        Fore.YELLOW + "\nRemote Management:\n" + Fore.RESET +
        "- rce\n- rceconnect\n",

        Fore.YELLOW + "\nThreat Intelligence:\n" + Fore.RESET +
        "- threatfeed\n",

        Fore.MAGENTA + "\nHelpful Tips:\n" + Fore.RESET +
        "- (*) indicates a module-based menu (interactive)\n"
        "- Type 'shortcuts' for quick references.\n"
        "- Type 'role show' to view your Current Role.\n"
        "- Use 'masterkey' for full categorized listing.\n"
        "- 'scan' = simple single CIDR scan | 'netscan' = advanced scans.\n"
        "- Use 'password' for a full Password Management console!\n"
        "- Use <cmd> ? for an example and usage! i.e. 'whois ?'\n",

        Fore.CYAN + "\n=== End of Help ===\n"
    ]

    all_lines = []
    for section in help_sections:
        all_lines.extend(section.strip('\n').split('\n'))

    # Auto detect terminal size for page size
    page_size = max(8, shutil.get_terminal_size().lines - 6)
    total_lines = len(all_lines)
    lines_printed = 0

    for idx, line in enumerate(all_lines):
        print(line)
        lines_printed += 1

        if lines_printed >= page_size and idx < (total_lines - 10) and not line.rstrip().endswith(':'):
            action = wait_for_space()
            if action == "quit":
                print(Fore.CYAN + "\n=== End of Help ===")
                return
            elif action == "line":
                # allow one more line only
                lines_printed = page_size - 1
            else:  # page
                lines_printed = 0
