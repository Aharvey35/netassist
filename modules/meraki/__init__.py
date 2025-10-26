# modules/meraki/__init__.py
from colorama import init as _colorama_init
_colorama_init(autoreset=True)

from .console import run as run_console
