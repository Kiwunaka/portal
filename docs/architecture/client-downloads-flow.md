# Client Downloads Flow

Last updated: 2026-05-08

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

With `--check-providers`, the smoke checks payment policy as context for launch readiness: a blocked `/api/payments/providers` response must include blocked reasons, and any green provider catalog must expose exactly one enabled Lava.top row, with no disabled legacy provider rows.
