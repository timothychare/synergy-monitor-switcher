"""
Synergy Monitor Switcher

Watches the Synergy server log and, whenever the mouse moves to another screen,
switches your physical monitors' inputs (DDC/CI VCP code 60) to that machine
using NirSoft ControlMyMonitor.

All machine-specific settings live in config.json (next to this script, or the
path given with --config). Copy config.example.json to config.json and edit it.
config.json is git-ignored so your personal details never get committed.

Usage:
    python Synergy-monitor-switcher.py [--primary] [--config path/to/config.json]

    --primary   Only switch the primary monitor this session (skip the others).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
DEFAULT_LOG_PATH = os.path.join(
    os.environ.get("PROGRAMDATA", "C:/ProgramData"), "Synergy", "synergy-daemon.log"
)

# Matches lines like: INFO: switch from "desktop" to "laptop" at 1919,540
SWITCH_PATTERN = re.compile(r'switch from "([^"]+)" to "([^"]+)"')


def get_arg(flag, default=None):
    """Return the value following a command-line flag, if present."""
    if flag in sys.argv:
        idx = sys.argv.index(flag)
        if idx + 1 < len(sys.argv):
            return sys.argv[idx + 1]
    return default


def find_control_my_monitor(configured_path):
    """Locate ControlMyMonitor.exe: config value, then next to the script, then PATH."""
    candidates = [
        configured_path and os.path.expandvars(os.path.expanduser(configured_path)),
        os.path.join(SCRIPT_DIR, "ControlMyMonitor.exe"),
        shutil.which("ControlMyMonitor.exe"),
    ]
    for path in candidates:
        if path and os.path.isfile(path):
            return path
    sys.exit(
        "[!] ControlMyMonitor.exe not found. Set \"control_my_monitor_path\" in config.json, "
        "place the exe next to this script, or add it to PATH."
    )


def load_config(path):
    if not os.path.isfile(path):
        sys.exit(
            f"[!] Config file not found: {path}\n"
            "    Copy config.example.json to config.json and fill in your values."
        )
    with open(path, "r", encoding="utf-8") as f:
        config = json.load(f)
    if not config.get("screens"):
        sys.exit("[!] config.json must define at least one entry under \"screens\".")
    return config


def apply_inputs(cmm_path, input_map, label, primary_monitor, switch_secondary):
    """Switch each monitor to the input value configured for the given screen."""
    for monitor_id, value in input_map.items():
        if monitor_id != primary_monitor and not switch_secondary:
            continue
        try:
            subprocess.run(
                [cmm_path, "/SetValue", monitor_id, "60", str(value)],
                check=True,
            )
            print(f"[*] {label}: {monitor_id} -> input {value}")
        except Exception as e:
            print(f"[!] Failed to switch {monitor_id}: {e}")


def follow(path):
    """Yield new lines appended to the log file, like `tail -f`."""
    while not os.path.isfile(path):
        print(f"[.] Waiting for {path} to appear...")
        time.sleep(2)
    f = open(path, "r", encoding="utf-8", errors="replace")
    f.seek(0, os.SEEK_END)  # only react to new switches, not old history
    while True:
        line = f.readline()
        if line:
            yield line
            continue
        time.sleep(0.1)
        # Reopen if the log was truncated or replaced (e.g. Synergy restarted)
        try:
            if os.path.getsize(path) < f.tell():
                f.close()
                f = open(path, "r", encoding="utf-8", errors="replace")
        except OSError:
            pass


def main():
    config = load_config(get_arg("--config", DEFAULT_CONFIG_PATH))
    cmm_path = find_control_my_monitor(config.get("control_my_monitor_path"))
    log_path = os.path.expandvars(config.get("synergy_log_path") or DEFAULT_LOG_PATH)
    primary_monitor = config.get("primary_monitor", "Primary")
    screens = config["screens"]
    verbose = config.get("echo_log", False)
    switch_secondary = "--primary" not in sys.argv

    print(
        "Starting Synergy Log Listener... (secondary monitors: "
        f"{'enabled - disable using --primary' if switch_secondary else 'disabled via --primary'})"
    )
    print(f"Configured screens: {', '.join(screens)}")
    print(f"Watching {log_path} - make sure the Synergy server is started from the Synergy app.")

    try:
        for line in follow(log_path):
            if verbose:
                print(f"SYNERGY LOG: {line.strip()}")

            match = SWITCH_PATTERN.search(line)
            if not match:
                continue

            source, target = match.groups()
            if target not in screens:
                print(f"[?] Mouse moved to unknown screen \"{target}\" - add it to config.json \"screens\".")
                continue

            print(f">>> Mouse moved {source} -> {target}. Switching inputs...")
            apply_inputs(cmm_path, screens[target], target, primary_monitor, switch_secondary)

    except KeyboardInterrupt:
        print("\nStopping listener...")


if __name__ == "__main__":
    main()
