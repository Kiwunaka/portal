# RU-Origin Probe

Last updated: 2026-04-26

RU-origin readiness must be measured from `mini` or a replacement external RU probe host. It cannot be inferred from the operator workstation or the control-plane host.

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
