# Android/Windows client audit (2026-02-14)

## Current status

- Fork workspace exists: `external/client-fork/app`
- Remote/checklists/scripts are present in `external/client-fork/`
- Missing runtime release config files:
  - `external/client-fork/release-links.env` (absent)
  - `external/client-fork/branding/brand.env` (absent)
- `APP_*` links in backend env are not filled yet.

## What is ready

- Bootstrap scripts for fork sync and branding workspace.
- Release handoff script for generating URLs.
- URL smoke checker (`scripts/check_release_urls.py`).
- Backend endpoint `GET /api/client/apps` already serves env-based links.

## Next steps to reach release-ready

1. Create `external/client-fork/branding/brand.env` from template and apply branding.
2. Run fork release workflow and publish Android/Windows artifacts.
3. Generate `external/client-fork/release-links.env` via `release_handoff.ps1`.
4. Copy generated `APP_*` URLs into `/root/portal_bot/.env`.
5. Restart `portal-api` + `portal-bot`.
6. Run smoke check:
   - `python scripts/smoke_client_apps.py --base-url https://kiwunaka.space --init-data '<telegram_init_data>'`
7. Verify links on:
   - `portal-privacy.online` (marketing download block)
   - `/webapp/` (connect tab)

## Out of scope in this phase

- No release pipeline execution in this task.
- No store submission actions.
