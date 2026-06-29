# Current-Origin Runtime App Download Smoke

Date: 2026-06-27

Command:

```powershell
python scripts\runtime_app_download_smoke.py --redact --base-url https://api.pokrov.space --timeout 20
```

Classification: `BLOCKED_BY_ACCESS`

Scope: unauthenticated current-origin smoke from the operator workstation. This
checks public API reachability only. It does not use Telegram init data, does
not fetch `/api/client/apps`, and does not prove authenticated app-session,
runtime release metadata, device install/connect behavior, or RU-origin
readiness.

Output:

```text
[OK] /api/health -> 200
[FAIL] --init-data <redacted> TELEGRAM_INIT_DATA) is required for /api/client/apps
```

Result: public `/api/health` returned `200`; authenticated `/api/client/apps`
remains owner/operator gated because no real Telegram init data was supplied.
