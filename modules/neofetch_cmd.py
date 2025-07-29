# modules/neofetch_cmd.py
import subprocess

def run_neofetch():
    """
    Invoke the system-installed neofetch tool and
    stream its output directly to stdout/stderr.
    """
    try:
        subprocess.run(
            ["neofetch"],
            check=True
        )
    except FileNotFoundError:
        print("❌ neofetch not found. Please install it first.")
    except subprocess.CalledProcessError as e:
        print(f"❌ neofetch exited with error code {e.returncode}.")
