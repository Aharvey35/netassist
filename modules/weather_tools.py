# modules/weather_tools.py
import requests
from colorama import Fore

def run():
    city = input("\n Enter city for weather lookup: ").strip()
    get_weather(city)

def get_weather(city):
    if not city:
        print(Fore.RED + "No city provided.")
        return
    try:
        api_key = 'demo'  # Note: Replace with a real free API key later if needed
        url = f"https://wttr.in/{city}?format=3&u"
        response = requests.get(url)
        if response.status_code == 200:
            print(Fore.CYAN + f"\n{response.text}\n")
        else:
            print(Fore.RED + "Weather service error.")
    except Exception as e:
        print(Fore.RED + f"Weather lookup error: {e}")
