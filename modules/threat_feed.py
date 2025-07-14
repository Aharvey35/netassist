# modules/threat_feed.py
import requests
import datetime
import os
from colorama import Fore

# Tracker file to compare between sessions
TRACKER_FILE = 'data/threat_tracker.json'

def load_last_counts():
    if os.path.exists(TRACKER_FILE):
        import json
        with open(TRACKER_FILE, 'r') as f:
            return json.load(f)
    return {"critical": 0, "high": 0}

def save_current_counts(critical, high):
    import json
    with open(TRACKER_FILE, 'w') as f:
        json.dump({"critical": critical, "high": high}, f)

def fetch_feed(view="highonly"):
    today = datetime.datetime.utcnow()
    seven_days_ago = today - datetime.timedelta(days=7)

    start_date = seven_days_ago.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    end_date = today.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?pubStartDate={start_date}&pubEndDate={end_date}&resultsPerPage=50"

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    return response.json()

def run(view="highonly"):
    print(Fore.CYAN + "\n=== Cyber Threat Feed ===\n")

    try:
        feed = fetch_feed(view)
        vulnerabilities = feed.get('vulnerabilities', [])

        if not vulnerabilities:
            print(Fore.YELLOW + "\nNo vulnerabilities found.\n")
            return

        last_counts = load_last_counts()
        critical_count = 0
        high_count = 0
        entries = []

        for item in vulnerabilities:
            cve_id = item.get('cve', {}).get('id', 'Unknown CVE')
            description = item.get('cve', {}).get('descriptions', [{}])[0].get('value', 'No Description')

            metrics = item.get('cve', {}).get('metrics', {})
            cvss_score = None

            if "cvssMetricV31" in metrics:
                cvss_score = metrics["cvssMetricV31"][0]["cvssData"]["baseScore"]
            elif "cvssMetricV30" in metrics:
                cvss_score = metrics["cvssMetricV30"][0]["cvssData"]["baseScore"]
            elif "cvssMetricV2" in metrics:
                cvss_score = metrics["cvssMetricV2"][0]["cvssData"]["baseScore"]

            if cvss_score is None:
                continue

            if view == "highonly" and cvss_score < 7.0:
                continue

            severity_color = Fore.RED if cvss_score >= 9.0 else Fore.YELLOW if cvss_score >= 7.0 else Fore.GREEN

            if cvss_score >= 9.0:
                critical_count += 1
            elif cvss_score >= 7.0:
                high_count += 1

            entries.append((severity_color, cve_id, cvss_score, description))

        if not entries:
            print(Fore.YELLOW + "\nNo matching vulnerabilities found.\n")
            return

        print(Fore.CYAN + f"🛡️ {critical_count} Critical | {high_count} High vulnerabilities reported in past 7 days\n")

        change_crit = critical_count - last_counts.get("critical", 0)
        change_high = high_count - last_counts.get("high", 0)

        trend_color = Fore.GREEN if (change_crit + change_high) < 0 else Fore.RED if (change_crit + change_high) > 0 else Fore.YELLOW
        change_text = f"{'+' if (change_crit + change_high) > 0 else ''}{change_crit + change_high}"

        print(trend_color + f"🔄 Change since last scan: {change_text}\n")

        for idx, (color, cve_id, score, desc) in enumerate(entries, start=1):
            print(color + f"{idx}. {cve_id} (CVSS: {score})")
            print(Fore.BLUE + f"   {desc}\n")

        save_current_counts(critical_count, high_count)

        # Save results to memory for optional manual save
        global last_fetched_entries
        last_fetched_entries = entries

    except Exception as e:
        print(Fore.RED + f"\nUnable to fetch threat feed: {e}\n")

def save_feed_snapshot():
    if not last_fetched_entries:
        print(Fore.RED + "\nNo threat data available to save.\n")
        return

    if not os.path.exists('logs'):
        os.makedirs('logs')

    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'logs/threat_snapshot_{timestamp}.txt'

    with open(filename, 'w') as f:
        for idx, (_, cve_id, score, desc) in enumerate(last_fetched_entries, start=1):
            f.write(f"{idx}. {cve_id} (CVSS: {score})\n")
            f.write(f"   {desc}\n\n")

    print(Fore.GREEN + f"\nThreat snapshot saved to {filename}\n")

# Initialize fetched entries storage
last_fetched_entries = []
