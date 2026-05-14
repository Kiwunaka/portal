# Public Beta Handoff

Generated: 2026-05-07 02:58 MSK

## Verdict

NO-GO for public beta publication.

Local implementation and quick release gates are green, and fresh Android/Windows artifacts were built. Do not publish GitHub Releases, deploy changed backend/static surfaces, or post Telegram launch copy yet because P0 release evidence is still incomplete.

## What Changed

- Telegram/web auth now treats expired Telegram Login Widget and web-session tokens as human reauth states; valid Telegram init data can silently refresh an expired browser session when safe.
- Public email register/recovery is hard-blocked unless email public mode is enabled, debug echo is off, and delivery is configured.
- RUB checkout is Lava.top-configured by default and remains blocked when paid access-key email delivery is not ready.
- Marketing free-trial CTAs now start from app install instead of paid checkout pressure.
- Cabinet download CTAs now point to `https://pokrov.space/install/` instead of a dead `#download` anchor.
- Email-auth cabinet copy was moved to Russian UI text for the enabled-email path.
- Windows packaging now stages a first-layer unsigned setup EXE, portable ZIP, and manifest through `build-windows-release.ps1`.
- Telegram channel launch drafts were prepared in `docs/launch/telegram-announcement.md`; do not post until a future GO handoff.

## Verification

- `python -m pytest tests/test_lavatop_payment_providers.py tests/test_api_payments_callbacks.py portal_bot/tests/test_email_auth.py -q` -> PASS, 41 tests.
- `python -m pytest tests/test_api_auth_and_tickets.py tests/test_package_windows_script.py tests/test_run_client_release_gate.py tests/test_marketing_release_readiness.py tests/test_frontend_text_integrity.py tests/test_public_copy_guardrails.py tests/test_shared_surface_facts.py -q` -> PASS, 97 tests.
- `python -m pytest tests/test_api_lifecycle_smoke.py -q` -> PASS.
- `python -m pytest tests/test_public_copy_guardrails.py tests/test_marketing_release_readiness.py -q` -> PASS, 14 tests.
- `python scripts/release_gate_check.py --quick --output docs/audit-artifacts/release-gate-local-2026-05-07.md` -> PASS.
- `python scripts/run_client_release_gate.py preflight` -> PASS.
- `python scripts/client_security_smoke.py` -> PASS.
- `python scripts/run_client_release_gate.py build --target windows` -> PASS.
- `python scripts/run_client_release_gate.py build --target android-apk` -> PASS.
- `python scripts/verify_brain_ready.py --brain-ip 82.21.114.104` -> PASS.

Known test-environment note: some pytest runs still print a Windows `pytest-current` cleanup `PermissionError` after successful exit; release-gate subprocesses use repo-local `--basetemp` and did not fail on it.

## Built Artifacts

- Android APK: `C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/build/app/outputs/flutter-apk/app-release.apk`
  - SHA256: `1A369891641964A9A30A296E7D47111A07B6DDAAD5ABC293F7EF938A654DADB0`
- Windows setup EXE: `C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/build/release_bundle/pokrov-windows-beta-x64-0.2.0-beta.1-setup.exe`
  - SHA256: `59A42D923F107F3C8211E679E60088802AB455AAE2127D6C166DA8FD6A62B347`
- Windows portable ZIP: `C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/build/release_bundle/pokrov-windows-beta-x64-0.2.0-beta.1.zip`
- Windows manifest: `C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/build/release_bundle/pokrov-windows-beta-x64-0.2.0-beta.1.manifest.json`

These are local engineering artifacts only. They are not public release URLs.

## Origin Checks

- current-origin check: PASS via local quick release gate.
- brain-origin check: PASS via `verify_brain_ready.py`; `caddy`, `portal-api`, `portal-bot`, `portal-helpbot`, and `portal-feedbackbot` were active, and public web/API/subscription probes responded.
- RU-origin check: FAIL / `RU_ORIGIN_TELEGRAM_DEGRADED`.
  - Evidence: `docs/audit-artifacts/ru-origin-mini-2026-05-07.json`.
  - From `mini` (`176.123.166.119`), `pokrov.space`, `app.pokrov.space`, `api.pokrov.space/api/health`, and node TCP checks passed.
  - `t.me` and `api.telegram.org` timed out from the RU-origin host.

## Blockers

- Android physical release-build localhost/control-surface audit: BLOCKED_BY_ACCESS. No physical device was visible through adb in this session.
- Runtime app-download smoke: BLOCKED_BY_ACCESS / `SKIPPED_NO_LIVE_TOKEN`. `TELEGRAM_INIT_DATA` was not set in the shell.
- Lava.top live invoice/payment evidence: BLOCKED_BY_ACCESS. Live API secret/offer env was not available in the shell.
- Email delivery live probe: BLOCKED_BY_ACCESS. Relay URL/secret env was not available in the shell.
- Lava.top real paid callback, replay/idempotency from provider history, failed-payment evidence, and reconciliation evidence: EXTERNAL_DEPENDENCY.
- RU-origin Telegram reachability from `mini`: FAIL, must be resolved or documented before claiming Telegram-dependent readiness from RU-origin.
- Windows trusted signing: EXTERNAL_DEPENDENCY. Current setup EXE is unsigned beta-only and may trigger unknown-publisher warnings.

## Deploy / Publish State

- GitHub Releases: NOT PUBLISHED.
- Backend deploy: NOT DEPLOYED from this workspace.
- Static marketing/webapp deploy: NOT DEPLOYED from this workspace.
- Telegram channel post: NOT POSTED.

Reason: public release gates are not green.

## Safe Public Claims

- POKROV is preparing a limited Android and Windows beta outside app stores.
- Local engineering builds exist for Android APK and an unsigned Windows setup EXE.
- Windows beta installation may show an unknown-publisher warning until trusted signing is ready.
- Paid checkout remains unavailable unless Lava.top and email key delivery evidence are green.
- Email login/recovery is shown only when delivery is configured and public mode is enabled.

## Unsafe Claims

- Do not claim broad public launch.
- Do not claim app-store availability.
- Do not claim Windows is trusted-signed.
- Do not claim Android is public-ready until the physical localhost/control-surface audit passes.
- Do not claim Lava.top paid checkout is live until redacted live evidence is attached.
- Do not claim RU-origin Telegram readiness while `mini` times out to Telegram hosts.
