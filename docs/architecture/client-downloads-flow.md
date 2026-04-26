# Client Downloads Flow

Last updated: 2026-04-26

## Runtime Source

The canonical runtime source for public client links is `/api/client/apps`.

## Handoff Source

Client release metadata lives in `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/`. Public download URLs must not be invented in platform docs; they must come from approved client handoff evidence.

## Verification

Use:

```powershell
$env:TELEGRAM_INIT_DATA="<redacted live init data>"
python scripts/runtime_app_download_smoke.py --redact --check-providers --require-release-handoff
```

Do not pass raw init data directly on the command line in retained evidence.
