# Synergy Monitor Switcher

Automatically switches your physical monitors' inputs whenever the mouse moves to another
screen in [Synergy](https://symless.com/synergy). Share one set of monitors between
multiple computers: move the mouse off the edge, and the monitors follow.

It works by tailing the Synergy server log for `switch from "X" to "Y"` lines and sending
a DDC/CI "input select" command (VCP code `60`) through NirSoft
[ControlMyMonitor](https://www.nirsoft.net/utils/control_my_monitor.html).

## Requirements

- Windows, running the Synergy **server**
- Python 3.8+
- ControlMyMonitor.exe
- Monitors that support DDC/CI (enable it in the monitor's OSD menu)

## Setup

1. Copy `config.example.json` to `config.json`.
2. Set `control_my_monitor_path` (or put `ControlMyMonitor.exe` next to the script or on your PATH).
3. List your monitors and their IDs:
   ```
   ControlMyMonitor.exe /smonitors
   ```
   `"Primary"` addresses the primary display. For other monitors, use the short monitor ID,
   serial number, or index.
4. Under `screens`, add one entry for each Synergy screen name, exactly as it appears in the
   Synergy log. Map each monitor ID to the input value that screen uses. To find the values,
   switch a monitor to each input by hand and read VCP code `60` in the ControlMyMonitor GUI.
   Some monitors report back a different value than the one you need to write.

`config.json` is git-ignored, so your hostnames and paths stay local.

## Usage

```
python Synergy-monitor-switcher.py            # switch all configured monitors
python Synergy-monitor-switcher.py --primary  # only switch the primary monitor
python Synergy-monitor-switcher.py --config path\to\other.json
```

Set `"echo_log": true` in the config to print every Synergy log line, which helps with debugging.
If the mouse moves to a screen that isn't in `screens`, the script prints a warning so you
know which name to add.
