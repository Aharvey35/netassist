# modules/rce_tools.py
"""
rce_tools.py

Polished WinRM remote-exec + streaming + RDP launcher + helper functions
Designed to be copied into your NetAssist project's modules/ folder.

Features:
- rce(host, username=None, password=None, command=None, use_ps=False, transport=None)
    -> run a simple remote command via pywinrm (blocking).
- rce_stream(host, command, username=None, password=None, transport=None, poll_interval=0.8)
    -> stream stdout/stderr for long-running commands using pywinrm Protocol.
- winrm_check(host, username=None, password=None)
    -> quick health check.
- rceconnect(host, width=1280, height=720, save_rdp=None)
    -> create .rdp file and launch mstsc on the Windows host (works from WSL).
- Logging to ~/.netassist/rce.log (append-only).

Requirements:
    pip install pywinrm
Optional (for credential features): pip install cryptography

Security notes (must-read):
- These functions execute commands remotely and require administrative credentials on target hosts.
- Use only on systems you own/control. Log activity and rotate credentials.
- Prefer domain/Kerberos or WinRM over HTTPS for production.
"""

from __future__ import annotations
import os
import time
import subprocess
from getpass import getpass
from typing import Optional, Tuple, Iterator

# Optional dependency: pywinrm
try:
    import winrm
    from winrm.protocol import Protocol
except Exception:
    winrm = None
    Protocol = None

LOGFILE = os.path.expanduser("~/.netassist/rce.log")
os.makedirs(os.path.dirname(LOGFILE), exist_ok=True)


def _log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOGFILE, "a", encoding="utf-8") as fh:
            fh.write(f"{ts} {msg}\n")
    except Exception:
        # don't fail operations just for logging errors
        pass


def ensure_pywinrm() -> None:
    if winrm is None:
        raise RuntimeError("pywinrm is not installed. Install with: python -m pip install pywinrm")


def rce(host: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        command: Optional[str] = None,
        use_ps: bool = False,
        transport: Optional[str] = None,
        timeout: int = 60) -> Tuple[int, str, str]:
    """
    Run a command via WinRM (blocking). Returns (rc, stdout, stderr).
    Prompts for username/password if omitted.
    """
    ensure_pywinrm()

    if username is None:
        username = input("Username (DOMAIN\\user or user@domain): ").strip()
    if password is None:
        password = getpass("Password: ")

    if transport is None and ("\\" in username or "@" in username):
        transport = "ntlm"

    session = winrm.Session(target=host, auth=(username, password), transport=transport or "ntlm")

    if command is None:
        command = input("Command to execute: ")

    try:
        if use_ps:
            res = session.run_ps(command)
        else:
            res = session.run_cmd(command)
    except Exception as e:
        _log(f"rce EXC host={host} cmd={command} err={e}")
        return (1, "", f"Exception: {e}")

    out = getattr(res, "std_out", b"") or b""
    err = getattr(res, "std_err", b"") or b""
    try:
        out_s = out.decode("utf-8", errors="ignore")
    except Exception:
        out_s = str(out)
    try:
        err_s = err.decode("utf-8", errors="ignore")
    except Exception:
        err_s = str(err)
    rc = getattr(res, "status_code", 0)
    _log(f"rce host={host} cmd={command} rc={rc}")
    return (rc, out_s, err_s)


def rce_stream(host: str,
               command: str,
               username: Optional[str] = None,
               password: Optional[str] = None,
               transport: Optional[str] = None,
               poll_interval: float = 0.8) -> Iterator[Tuple[str, str]]:
    """
    Stream stdout/stderr from a remote command using the Protocol API.

    Yields tuples (stream, text) where stream is one of: 'stdout', 'stderr', 'rc'.
    Example:
        for stream, text in rce_stream(...):
            if stream == 'stdout': print(text, end='')
            elif stream == 'rc': print('exit', text)
    """
    ensure_pywinrm()
    if Protocol is None:
        raise RuntimeError("pywinrm.Protocol not available. Ensure pywinrm is installed and recent.")

    if username is None:
        username = input("Username (DOMAIN\\user or user@domain): ").strip()
    if password is None:
        password = getpass("Password: ")

    if transport is None and ("\\" in username or "@" in username):
        transport = "ntlm"

    endpoint = f"http://{host}:5985/wsman"
    proto = Protocol(endpoint=endpoint, transport=transport or "ntlm", username=username, password=password)

    shell_id = None
    command_id = None
    try:
        shell_id = proto.open_shell()
        # run under cmd.exe /c to preserve classic command output semantics
        command_id = proto.run_command(shell_id, 'cmd.exe', ['/c', command])
        _log(f"rce_stream start host={host} cmd={command} shell={shell_id} cmdid={command_id}")
        while True:
            std_out, std_err, rc = proto.get_command_output(shell_id, command_id)
            if std_out:
                try:
                    yield ('stdout', std_out.decode('utf-8', errors='ignore'))
                except Exception:
                    yield ('stdout', str(std_out))
            if std_err:
                try:
                    yield ('stderr', std_err.decode('utf-8', errors='ignore'))
                except Exception:
                    yield ('stderr', str(std_err))
            if rc is not None:
                yield ('rc', str(rc))
                _log(f"rce_stream complete host={host} cmd={command} rc={rc}")
                break
            time.sleep(poll_interval)
    finally:
        try:
            if command_id and shell_id:
                proto.cleanup_command(shell_id, command_id)
        except Exception:
            pass
        try:
            if shell_id:
                proto.close_shell(shell_id)
        except Exception:
            pass


def winrm_check(host: str, username: Optional[str] = None, password: Optional[str] = None, transport: Optional[str] = None) -> bool:
    """
    Quick health check: run 'echo netassist_alive' and expect it back.
    """
    try:
        rc, out, err = rce(host, username=username, password=password, command="echo netassist_alive", transport=transport)
    except Exception:
        return False
    return rc == 0 and "netassist_alive" in (out or "").lower()


def rceconnect(host: str, width: int = 1280, height: int = 720, save_rdp: Optional[str] = None) -> bool:
    """
    Create a temporary .rdp file and launch mstsc via cmd.exe so the Windows GUI opens.
    Works when NetAssist runs from WSL on a Windows host.
    """
    rdp_lines = [
        "screen mode id:i:2",
        "use multimon:i:0",
        f"desktopwidth:i:{width}",
        f"desktopheight:i:{height}",
        "session bpp:i:32",
        f"full address:s:{host}",
        "compression:i:1",
        "redirectprinters:i:1",
        "redirectcomports:i:0",
        "redirectsmartcards:i:1",
        "displayconnectionbar:i:1",
        "disable wallpaper:i:0",
    ]
    tmp = save_rdp or f"/tmp/netassist_{host}.rdp"
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write("\n".join(rdp_lines))
    except Exception as e:
        _log(f"rceconnect failed write rdp host={host} err={e}")
        return False

    try:
        subprocess.Popen(['cmd.exe', '/C', 'start', 'mstsc', tmp], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        _log(f"rceconnect launched host={host} rdp={tmp}")
        return True
    except Exception as e:
        _log(f"rceconnect failed host={host} err={e}")
        return False


# ---------- Simple CLI for testing when run directly ----------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(prog="rce_tools")
    sub = parser.add_subparsers(dest="cmd")

    p_check = sub.add_parser("check", help="WinRM health check")
    p_check.add_argument("--host", required=True)
    p_check.add_argument("--user")

    p_run = sub.add_parser("run", help="Run a command (blocking)")
    p_run.add_argument("--host", required=True)
    p_run.add_argument("--user")
    p_run.add_argument("--cmd", required=False)
    p_run.add_argument("--ps", action="store_true", help="Run as PowerShell (run_ps)")

    p_stream = sub.add_parser("stream", help="Stream a long-running command")
    p_stream.add_argument("--host", required=True)
    p_stream.add_argument("--user")
    p_stream.add_argument("--cmd", required=True)

    p_rdp = sub.add_parser("rdp", help="Launch RDP (mstsc)")
    p_rdp.add_argument("--host", required=True)
    p_rdp.add_argument("--width", type=int, default=1280)
    p_rdp.add_argument("--height", type=int, default=720)

    args = parser.parse_args()
    if args.cmd == "check":
        ok = winrm_check(args.host, username=args.user)
        print("WinRM ok:", ok)
    elif args.cmd == "run":
        rc, out, err = rce(args.host, username=args.user, command=args.cmd, use_ps=args.ps)
        print("RC:", rc)
        if out:
            print(out)
        if err:
            print(err)
    elif args.cmd == "stream":
        try:
            for ev, txt in rce_stream(args.host, args.cmd, username=args.user):
                if ev in ("stdout", "stderr"):
                    print(txt, end="", flush=True)
                elif ev == "rc":
                    print("\nRemote exit code:", txt)
        except KeyboardInterrupt:
            print("\nInterrupted by user")
    elif args.cmd == "rdp":
        ok = rceconnect(args.host, width=args.width, height=args.height)
        print("Launched RDP:", ok)
    else:
        parser.print_help()
