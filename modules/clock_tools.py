# modules/clock_tools.py

from datetime import datetime
import pytz

def run():
    print("\n  Clock Module")
    print("Options:")
    print("  1. Show Local Time")
    print("  2. Show Quick Timezone Time (ex: est, pst, ist, utc)")
    print("  3. List Available Quick Timezones")
    print("  4. Return to Main Menu")
    choice = input("\nChoose an option: ").strip()

    if choice == "1":
        show_local_time()
    elif choice == "2":
        quick_timezone_time()
    elif choice == "3":
        list_timezones()
    elif choice == "4":
        print("\nReturning to main menu...\n")
    else:
        print("\nInvalid choice.\n")
def show_local_time():
    now = datetime.now()
    print(f"\n Local Time: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")

def quick_timezone_time():
    tz_lookup = {
        "est": "US/Eastern",
        "pst": "US/Pacific",
        "cst": "US/Central",
        "mst": "US/Mountain",
        "ist": "Asia/Kolkata",
        "utc": "UTC"
    }

    tz_code = input("\nEnter quick timezone code (est/pst/cst/mst/ist/utc): ").lower()
    tz_name = tz_lookup.get(tz_code)

    if tz_name:
        tz = pytz.timezone(tz_name)
        now = datetime.now(tz)
        print(f"\n Time in {tz_code.upper()} ({tz_name}): {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
    else:
        print("\nUnknown timezone code. Use 'clock zones' to list options.\n")

def list_timezones():
    print("\nQuick Timezone Codes:")
    print("  est - US Eastern")
    print("  pst - US Pacific")
    print("  cst - US Central")
    print("  mst - US Mountain")
    print("  ist - India Standard Time")
    print("  utc - Coordinated Universal Time")