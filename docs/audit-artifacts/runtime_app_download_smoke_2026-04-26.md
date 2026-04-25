# Runtime App Download Smoke

- timestamp_local: `2026-04-26`
- base_url: `https://api.pokrov.space`
- script: `scripts/smoke_client_apps.py`
- result: `BLOCKED_NO_LIVE_TOKEN`

## Command

`python scripts/smoke_client_apps.py --base-url https://api.pokrov.space --check-providers --require-release-handoff`

## Evidence

- `/api/health` returned HTTP `200`.
- `/api/client/apps` was not executed because the smoke requires `--init-data` or `TELEGRAM_INIT_DATA`.

## Interpretation

- Production API health is reachable.
- App-download runtime smoke remains blocked until a live Telegram init-data token is supplied for the test user.
- Raw token values must not be committed or copied into release evidence.
