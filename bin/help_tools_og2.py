# modules/help_tools.py

from colorama import Fore

def run():
    help_sections = [
        Fore.CYAN + "\n=== NetAssist Help System ===\n",
        Fore.YELLOW + "\nCore System Commands:\n" + Fore.RESET +
        "- help\n- clear\n- exit\n- motd\n- version\n- history\n- ls\n- masterkey\n",
        
        Fore.YELLOW + "\nNetwork Tools:\n" + Fore.RESET +
        "- ping\n- traceroute\n- dnslookup\n- geoip\n- publicip\n- subnetcalc\n- wildcardcalc\n- speedtest\n- whois\n- sslcheck\n- ntptest\n",
        
        Fore.YELLOW + "\nSystem Tools:\n" + Fore.RESET +
        "- stat\n- ifconfig\n- ipconfig\n- battery\n- time\n",
        
        Fore.YELLOW + "\nConnection Tools:\n" + Fore.RESET +
        "- ssh\n",
        
        Fore.YELLOW + "\nAdmin / Repair Tools:\n" + Fore.RESET +
        "- system\n- network\n- security\n- repair\n- notes\n- sysadmin\n- dashboard\n- scan\n- netscan\n",
        
        Fore.YELLOW + "\nAlias Management:\n" + Fore.RESET +
        "- alias\n- savealias\n- loadalias\n- shortcuts\n",
        
        Fore.YELLOW + "\nFun / Bonus Tools:\n" + Fore.RESET +
        "- ascii\n- matrix\n- fireworks\n- weather\n- crypto\n- fun\n",
        
        Fore.YELLOW + "\nRemote Management:\n" + Fore.RESET +
        "- rce\n- rceconnect\n",
        
        Fore.YELLOW + "\nThreat Intelligence:\n" + Fore.RESET +
        "- threatfeed\n",
        
        Fore.MAGENTA + "\nHelpful Tips:\n" + Fore.RESET +
        "- Type 'shortcuts' for quick command reference!\n" +
        "- Use 'masterkey' for full categorized command listing.\n" +
        "- Use 'scan' for a simple scan, 'netscan' for advanced scanning.\n",
        
        Fore.CYAN + "\n=== End of Help ===\n"
    ]

    for section in help_sections:
        print(section)
        if "[Press SPACE to continue]" in section:
            input(Fore.YELLOW + "\nPress SPACE to continue...")
