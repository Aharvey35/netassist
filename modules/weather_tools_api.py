# modules/weather_tools.py
import requests
from colorama import Fore

API_KEY = "YOUR_OPENWEATHER_API_KEY"  # Replace with your actual API Key
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"

def run():
    print("\n🌦️  Weather Lookup")
    city = input("Enter city name: ").strip()
    if not city:
        print(Fore.RED + "No city provided.")
        return

    try:
        params = {
            'q': city,
            'appid': API_KEY,
            'units': 'metric'
        }
        response = requests.get(BASE_URL, params=params)
        data = response.json()

        if data['cod'] != 200:
            print(Fore.RED + f"Error: {data.get('message', 'Unknown error')}")
            return

        print(Fore.CYAN + f"\nWeather for {city}:")
        print(f"  Description: {data['weather'][0]['description']}")
        print(f"  Temperature: {data['main']['temp']}°C")
        print(f"  Feels Like: {data['main']['feels_like']}°C")
        print(f"  Humidity: {data['main']['humidity']}%")
        print(f"  Wind Speed: {data['wind']['speed']} m/s\n")

    except Exception as e:
        print(Fore.RED + f"Failed to retrieve weather: {e}")
