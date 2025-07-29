# modules/dispatcher.py
import importlib
import pkgutil

# Simple dispatcher registry
_builtin_cmds = {}


def register_builtin(name: str, func):
    """Register a built-in command handler."""
    _builtin_cmds[name] = func


def dispatch(cmd: str, session, args: list) -> bool:
    """
    Dispatch a command:
    1. Check built-ins
    2. Look for a module named '<cmd>_tools.py'
    3. Fall back to '<cmd>.py'
    """
    # 1) Built-in commands
    if cmd in _builtin_cmds:
        _builtin_cmds[cmd](session, args)
        return True

    # Helper to try loading module
    def try_module(module_name: str):
        try:
            module = importlib.import_module(f"modules.{module_name}")
            if hasattr(module, 'run'):
                module.run(session, *args)
                return True
        except ImportError:
            return False
        return False

    # 2) '<cmd>_tools.py'
    if try_module(f"{cmd}_tools"):
        return True

    # 3) '<cmd>.py'
    if try_module(cmd):
        return True

    # Unknown command
    return False
