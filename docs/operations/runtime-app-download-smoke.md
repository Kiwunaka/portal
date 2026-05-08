# Runtime App Download Smoke

Last updated: 2026-05-08

Before runtime links are synced, a staged `/api/client/apps` shaped payload can be checked for URL policy only:

```powershell
python scripts/runtime_app_download_smoke.py `
  --redact `
  --apps-json docs/audit-artifacts/staged-client-apps-2026-05-07.json `
  --require-release-handoff `
  --policy-only
```

This confirms outside-store beta URL shape: no Play URL, GitHub Releases `.apk` / `.exe` links, and install docs under `https://pokrov.space/install/`. It deliberately skips URL reachability and does not replace live smoke.

Use the wrapper script so retained evidence is redacted:

```powershell
$env:TELEGRAM_INIT_DATA="<redacted live init data>"
python scripts/runtime_app_download_smoke.py --redact --check-providers --require-release-handoff
```

When raw Telegram WebApp `initData` is not available, use the brain-local signed smoke instead. It reads the runtime `BOT_TOKEN` on `brain`, generates synthetic signed init data inside that SSH session, calls `/api/client/apps`, and returns only redacted status plus public download URLs:

```powershell
python scripts/brain_runtime_app_download_smoke.py `
  --brain-ip 82.21.114.104 `
  --ssh-user root `
  --ssh-port 29374 `
  --tg-id 900000001 `
  --output docs/audit-artifacts/runtime-app-download-smoke-brain-2026-05-08.json
```

This proves backend auth and runtime download-link policy without printing `BOT_TOKEN` or raw init data. It is still not proof that a real user opened the Telegram WebApp.

Rules:

- prefer env-only `TELEGRAM_INIT_DATA`;
- if live init data is unavailable, use the brain-local signed smoke and label it as synthetic signed init data;
- never paste raw init data into markdown;
- keep empty Android/Windows URLs as a blocked result, not a copy problem;
- with `--check-providers`, accept a blocked provider catalog only when it includes blocked reasons; if the catalog is green, it must expose exactly one provider row, enabled Lava.top, with no disabled legacy provider rows;
- verify `/api/client/apps` agrees with the client release handoff before public download copy changes.
