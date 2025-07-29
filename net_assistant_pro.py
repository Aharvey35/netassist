# net_assistant.py
import os
import sys
import time
import logging
import json
import yaml
import importlib
import readline
from pathlib import Path
from colorama import init, Fore

from modules.profiles import Session
from modules.dispatcher import dispatch, register_builtin

VERSION = "NetAssist Pro 5.3"


def main():
    # Initialize colors and logging
    init(autoreset=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

    # Create session and load config
    session = Session(data_dir=Path("data"))
    session.prompt_username()
    session.load_user_profile()
    session.select_deployment_profile()
    session.apply_theme()
    session.show_splash()

    # Register built‑in commands
    register_builtin("help", lambda sess, args: sess.run_help())
    register_builtin("version", lambda sess, args: print(Fore.CYAN + f"Running {VERSION}"))
    register_builtin("cls", lambda sess, args: os.system("cls" if os.name == "nt" else "clear"))
    register_builtin("exit", lambda sess, args: sess.exit())

    # Main REPL loop
    while True:
        try:
            raw = input(session.prompt()).strip()
            if not raw:
                continue
            session.add_history(raw)
            command, *args = session.preprocess(raw)

            # Dispatch and XP award
            handled = dispatch(command, session, args)
            if handled:
                session.award_xp(5)
            else:
                print(Fore.RED + f"Unknown command: {command}")

        except KeyboardInterrupt:
            print(Fore.YELLOW + "\nInterrupted. Type 'exit' to quit.")
        except Exception as e:
            logging.error(f"Error: {e}")


if __name__ == "__main__":
    main()
