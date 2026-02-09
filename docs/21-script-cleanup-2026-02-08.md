# Script Cleanup (2026-02-08)

## What changed

- Legacy standalone scripts moved to `legacy/archive-202602/`.
- Active operational entrypoints are now listed in `scripts/manifest.yaml`.
- Added guard check `scripts/check_script_manifest.py` to fail when docs reference denylisted or unknown scripts.

## Denylist policy

Deprecated legacy entrypoint moved to archive.

Admin guide now references:

- `scripts/remote_deploy_brain_portal_code.py`

## Validation

Run:

```bash
python scripts/check_script_manifest.py
```

Expected result:

- `Script manifest check passed.`
