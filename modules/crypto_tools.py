# modules/crypto_tools.py
import requests
from colorama import Fore

def run():
    print("\n Crypto Tools")
    print("Options:")
    print("  1. Bitcoin Price (BTC)")
    print("  2. Ethereum Price (ETH)")
    choice = input("\nChoose an option: ").strip()

    if choice == '1':
        crypto_price('bitcoin')
    elif choice == '2':
        crypto_price('ethereum')
    else:
        print(Fore.RED + "Invalid choice.")

def crypto_price(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        response = requests.get(url)
        data = response.json()
        price = data[coin_id]['usd']
        print(Fore.CYAN + f"\n💰 {coin_id.capitalize()} Price: ${price}\n")
    except Exception as e:
        print(Fore.RED + f"Crypto price lookup error: {e}")
