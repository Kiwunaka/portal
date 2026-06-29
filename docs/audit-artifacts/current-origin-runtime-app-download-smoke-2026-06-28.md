# Current-Origin Runtime App Download Smoke

Date: 2026-06-28

Command:

```powershell
python scripts/runtime_app_download_smoke.py --redact --base-url https://api.pokrov.space --timeout 45
```

Classification: `BLOCKED_BY_ACCESS`

Scope: current-origin smoke from the operator workstation. This checks public
API reachability and then attempts the authenticated runtime app-download
smoke. It does not use Telegram init data, does not fetch `/api/client/apps`,
and does not prove real Telegram WebApp/session behavior, current-origin
authenticated app-session behavior, device install/connect behavior, deploy
approval, RU-origin readiness, or payment-provider maturity.

Output:

```text
[OK] /api/health -> 200
[FAIL] --init-data <redacted> TELEGRAM_INIT_DATA) is required for /api/client/apps
```

Result: public `/api/health` returned `200`; authenticated `/api/client/apps`
remains owner/operator gated because no real Telegram init data was supplied.

Note: a first attempt with a 20-second timeout returned a transient
`/api/health` timeout. The repeated 45-second smoke above is the retained
classification for this artifact.
