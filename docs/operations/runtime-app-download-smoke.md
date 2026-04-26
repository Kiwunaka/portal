# Runtime App Download Smoke

Last updated: 2026-04-26

Use the wrapper script so retained evidence is redacted:

```powershell
$env:TELEGRAM_INIT_DATA="<redacted live init data>"
python scripts/runtime_app_download_smoke.py --redact --check-providers --require-release-handoff
```

Rules:

- prefer env-only `TELEGRAM_INIT_DATA`;
- never paste raw init data into markdown;
- keep empty Android/Windows URLs as a blocked result, not a copy problem;
- verify `/api/client/apps` agrees with the client release handoff before public download copy changes.
