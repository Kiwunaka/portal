# Runtime App Download Smoke Access

Generated: 2026-05-07 19:31 MSK

## Verdict

BLOCKED_BY_ACCESS / SKIPPED_NO_LIVE_TOKEN.

The runtime app-download smoke could not reach `/api/client/apps` because live Telegram WebApp init data is not available in the current shell.

## What I Checked

- `TELEGRAM_INIT_DATA`: absent.
- `python scripts\runtime_app_download_smoke.py --redact --base-url https://api.pokrov.space --require-release-handoff` reached the public API health endpoint and returned `[OK] /api/health -> 200`.
- The same command then stopped before `/api/client/apps` with the redacted init-data requirement failure.

## Classification

- Runtime app-download smoke with env-only Telegram init data: `BLOCKED_BY_ACCESS`.
- Missing input needed to unblock: fresh `TELEGRAM_INIT_DATA` from a real Telegram WebApp session with access to the current account.
