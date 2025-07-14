# modules/dice_roller.py
import random
from colorama import Fore

def run():
    print(Fore.CYAN + "\nDice Roller")
    try:
        roll_input = input(Fore.GREEN + "Enter dice roll (e.g., 2d6): ").strip().lower()
        num, sides = (1, int(roll_input[1:])) if 'd' not in roll_input else map(int, roll_input.split('d'))
        rolls = [random.randint(1, sides) for _ in range(num)]
        print(Fore.YELLOW + f"Rolls: {rolls} ➔ Total: {sum(rolls)}")
    except Exception as e:
        print(Fore.RED + f"Error: {e}")
