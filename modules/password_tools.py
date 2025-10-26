import random
import string
import base64
import hashlib
import secrets
from pathlib import Path
from datetime import datetime
from colorama import Fore, Style

# File to store generated password history
HISTORY_FILE = Path('data/password_history.txt')


def save_password_history(password, method):
    """Append a generated password to the history file with timestamp and method."""
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{timestamp} [{method}] {password}\n")


def run():
    while True:
        print(Fore.CYAN + "\n Advanced Password Toolkit Menu")
        print("1. Generate Custom Password")
        print("2. Generate Hexadecimal Password")
        print("3. Generate Base64 Password")
        print("4. Generate SHA-256 Hash of Input")
        print("5. Generate Passphrase")
        print("6. Check Password Strength")
        print("7. Password Policy Validator")
        print("8. View Password History")
        print("9. Exit")
        choice = input(Fore.GREEN + "Select an option: ").strip()
        
        if choice == '1':
            custom_pwgen()
        elif choice == '2':
            hex_pwgen()
        elif choice == '3':
            base64_pwgen()
        elif choice == '4':
            sha256_hash()
        elif choice == '5':
            passphrase_gen()
        elif choice == '6':
            improved_strength_checker()
        elif choice == '7':
            enhanced_policy_validator()
        elif choice == '8':
            view_password_history()
        elif choice == '9':
            print(Fore.CYAN + "Exiting Password Toolkit.")
            break
        else:
            print(Fore.RED + "Invalid choice. Please try again.")


def quick_pwgen():
    password = ''.join(secrets.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(16))
    print(Fore.YELLOW + Style.BRIGHT + "\n==============================")
    print(Fore.GREEN + Style.BRIGHT + f"Generated Password: {password}")
    print(Fore.YELLOW + Style.BRIGHT + "==============================")
    print("")
    save_password_history(password, "quick")
    improved_strength_checker(password)


def improved_strength_checker(password=None):
    if not password:
        password = input(Fore.YELLOW + "Enter password to check: ").strip()
    score = 0
    if any(c.islower() for c in password):
        score += 1
    if any(c.isupper() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    if any(c in string.punctuation for c in password):
        score += 1
    if len(password) >= 12:
        score += 1
    strength_levels = {
        1: Fore.RED + "Weak",
        2: Fore.YELLOW + "Moderate",
        3: Fore.LIGHTGREEN_EX + "Strong",
        4: Fore.GREEN + "Very Strong",
        5: Fore.CYAN + "Excellent"
    }
    print(Fore.MAGENTA + f"Password strength: {strength_levels.get(score, Fore.RED + 'Weak')}")


def enhanced_policy_validator():
    print(Fore.CYAN + "\n🔎 Enhanced Password Policy Validator")
    password = input(Fore.YELLOW + "Enter password to validate: ").strip()
    print("This tool checks password against recommended policies for modern applications.")
    issues = []
    if len(password) < 12:
        issues.append("- Too short (minimum 12 characters recommended)")
    if not any(c.isupper() for c in password):
        issues.append("- Missing uppercase letter")
    if not any(c.isdigit() for c in password):
        issues.append("- Missing digit")
    if not any(c in string.punctuation for c in password):
        issues.append("- Missing symbol")
    if issues:
        print(Fore.RED + "\nPassword issues:")
        for issue in issues:
            print(issue)
    else:
        print(Fore.GREEN + "Password meets recommended policies!")


def custom_pwgen():
    length = input(Fore.GREEN + "Enter desired password length (default 16): ").strip()
    length = int(length) if length.isdigit() else 16
    include_symbols = input(Fore.GREEN + "Include symbols? (y/n, default y): ").strip().lower() or 'y'
    include_numbers = input(Fore.GREEN + "Include numbers? (y/n, default y): ").strip().lower() or 'y'
    exclude_ambiguous = input(Fore.GREEN + "Exclude ambiguous characters? (y/n, default n): ").strip().lower() or 'n'
    
    characters = string.ascii_letters
    if include_numbers == 'y':
        characters += string.digits
    if include_symbols == 'y':
        characters += string.punctuation
    if exclude_ambiguous == 'y':
        for ch in ['O','0','l','1']:
            characters = characters.replace(ch, '')
    
    password = ''.join(secrets.choice(characters) for _ in range(length))
    print(Fore.YELLOW + Style.BRIGHT + "\n==============================")
    print(Fore.GREEN + Style.BRIGHT + f"Generated Password: {password}")
    print(Fore.YELLOW + Style.BRIGHT + "==============================")
    print("")
    save_password_history(password, "custom")
    improved_strength_checker(password)


def hex_pwgen():
    length = input(Fore.GREEN + "Enter desired password length (default 32): ").strip()
    length = int(length) if length.isdigit() else 32
    characters = string.hexdigits.lower()
    password = ''.join(secrets.choice(characters) for _ in range(length))
    print(Fore.YELLOW + Style.BRIGHT + "\n==============================")
    print(Fore.GREEN + Style.BRIGHT + f"Generated Hexadecimal Password: {password}")
    print(Fore.YELLOW + Style.BRIGHT + "==============================")
    print("")
    save_password_history(password, "hex")
    improved_strength_checker(password)


def base64_pwgen():
    length = input(Fore.GREEN + "Enter desired byte length (default 16): ").strip()
    length = int(length) if length.isdigit() else 16
    raw_bytes = secrets.token_bytes(length)
    password = base64.b64encode(raw_bytes).decode('utf-8')
    print(Fore.YELLOW + Style.BRIGHT + "\n==============================")
    print(Fore.GREEN + Style.BRIGHT + f"Generated Base64 Password: {password}")
    print(Fore.YELLOW + Style.BRIGHT + "==============================")
    print("")
    save_password_history(password, "base64")
    improved_strength_checker(password)


def sha256_hash():
    input_str = input(Fore.YELLOW + "Enter string to hash: ").strip()
    hash_obj = hashlib.sha256(input_str.encode())
    print(Fore.YELLOW + Style.BRIGHT + "\n==============================")
    print(Fore.GREEN + Style.BRIGHT + f"SHA-256 Hash: {hash_obj.hexdigest()}")
    print(Fore.YELLOW + Style.BRIGHT + "==============================")


def passphrase_gen():
    words = ["galaxy", "nebula", "asteroid", "comet", "star", "planet", "orbit", "cosmos", "lunar", "solar"]
    count = input(Fore.GREEN + "Enter number of words (default 4): ").strip()
    count = int(count) if count.isdigit() else 4
    separator = input(Fore.GREEN + "Enter separator (default '-'):").strip() or '-'
    phrase = separator.join(secrets.choice(words) for _ in range(count))
    print(Fore.YELLOW + Style.BRIGHT + "\n==============================")
    print(Fore.GREEN + Style.BRIGHT + f"Generated Passphrase: {phrase}")
    print(Fore.YELLOW + Style.BRIGHT + "==============================")
    print("")
    save_password_history(phrase, "passphrase")
    improved_strength_checker(phrase)


def view_password_history():
    print(Fore.CYAN + "\n📜 Password History")
    if not HISTORY_FILE.exists():
        print(Fore.YELLOW + "No password history found.")
        return
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    if not lines:
        print(Fore.YELLOW + "No password history found.")
        return
    for line in lines:
        print(Fore.LIGHTWHITE_EX + line.strip())
