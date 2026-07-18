# RU-Origin Probe

Last updated: 2026-04-26

RU-origin readiness must be measured from `mini` or a replacement external RU probe host. It cannot be inferred from the operator workstation or the control-plane host.

`ru_probe_runner.py --probe-host ...` only records an origin label in the
report. It does not connect to that host. Run the probe process inside the
actual origin host, or use a strict-host-key SSH wrapper that stages and runs
the exact candidate there. A workstation process labelled `mini` is invalid
evidence.

## Required Labels

- `current-origin check`: operator workstation.
- `brain-origin check`: `82.21.114.104`.
- `RU-origin check`: external RU probe.

## Minimum Probe Content

- `https://pokrov.space/`
- `https://app.pokrov.space/`
- `https://api.pokrov.space/api/health`
- Telegram channel or bot reachability check, when possible.

Store only redacted output under release evidence.
