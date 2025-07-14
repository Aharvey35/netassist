# modules/dad_jokes.py
import requests
from colorama import Fore

def run():
    print(Fore.CYAN + "\n Dad Joke Time!")
    try:
        response = requests.get("https://icanhazdadjoke.com/", headers={"Accept": "application/json"})
        if response.status_code == 200:
            print(Fore.YELLOW + response.json()['joke'])
        else:
            print(Fore.RED + "No jokes today!")
    except Exception as e:
        print(Fore.RED + f"Error: {e}")
