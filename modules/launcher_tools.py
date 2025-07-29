import subprocess
import platform

def launch_app(app_name):
    system = platform.system()

    # Map aliases to actual commands
    commands = {
        "chrome": {
            "Linux": "google-chrome",
            "Windows": "start chrome",
            "Darwin": "open -a 'Google Chrome'"
        },
        "firefox": {
            "Linux": "firefox",
            "Windows": "start firefox",
            "Darwin": "open -a 'Firefox'"
        }
    }

    if app_name not in commands:
        print(f"[!] Unknown app: {app_name}")
        return

    cmd = commands[app_name].get(system)

    if not cmd:
        print(f"[!] No launcher defined for {system}")
        return

    try:
        subprocess.Popen(cmd.split() if system != "Windows" else cmd, shell=(system == "Windows"))
        print(f"Launching {app_name.title()}...")
    except Exception as e:
        print(f"Failed to launch {app_name}: {e}")
