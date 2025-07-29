import json
import yaml
from pathlib import Path
from colorama import Fore

class Session:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(exist_ok=True)
        self.user_file = self.data_dir / 'user_profile.json'
        self.session = {}
        self.history = []

    def prompt_username(self):
        self.username = input(Fore.GREEN + "Enter your name: ").strip()
    
    def load_user_profile(self):
        if self.user_file.exists():
            with open(self.user_file) as f:
                self.user_profile = json.load(f)
        else:
            self.user_profile = {'username': self.username, 'xp': 0}
            self._save_profile()

    def select_deployment_profile(self):
        # Placeholder for multi-profile selection
        self.deployment = 'default'

    def apply_theme(self):
        # Load theme settings from profile if any
        pass

    def show_splash(self):
        print(Fore.CYAN + "Welcome to NetAssist Pro!")

    def prompt(self) -> str:
        return Fore.YELLOW + f"{self.username}@NetAssist> "

    def preprocess(self, raw: str):
        # Expand aliases/shortcuts
        parts = raw.split()
        # e.g., alias expansion here
        return parts

    def add_history(self, entry: str):
        self.history.append(entry)

    def award_xp(self, amount: int):
        self.user_profile['xp'] += amount
        self._save_profile()

    def run_help(self):
        # Print help text or load from file
        print("Available commands: help, version, exit, etc.")

    def exit(self):
        print(Fore.GREEN + "Goodbye!")
        # Save state if needed
        sys.exit(0)

    def _save_profile(self):
        with open(self.user_file, 'w') as f:
            json.dump(self.user_profile, f, indent=2)
