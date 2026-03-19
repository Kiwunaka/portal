# Cleanup Report (2026-02-09)

## Scope
- Safe Wave A cleanup only (no runtime/business logic removal).
- Criteria: delete generated artifacts, keep runtime-critical files, mark ambiguous legacy assets for review.

## delete-now
- Removed build/cache artifacts:
  - `.pytest_cache/`
  - `__pycache__/` (root + `portal_bot/`, `scripts/`, `tests/`)
  - `webapp/dist/`
  - `marketing/out/`
- Removed local benchmark/reference clones:
  - `.tmp/bench/` (all nested reference repos)
- Removed local test SQLite files:
  - `portal_api_test_*.db` (all matches in repo root)

## keep
- Runtime/state data that may be used by local environment:
  - `portal.db`
  - `portal.db.cluster.db`
  - `portal.db.from-old-20260207-010831.db`
- Active scripts listed in `scripts/manifest.yaml` (validated by `scripts/check_script_manifest.py`).
- Application source trees:
  - `portal_bot/`
  - `webapp/src/`
  - `marketing/src/`
  - `tests/`

## needs-review
- Legacy and mockup artifacts with unclear operational value:
  - `legacy/`
  - `mockup.html`
  - `mockupv2.html`
  - `mockupv3/`
  - `amoguscan_o46.html`
  - `check.json`
- Local inventories/backups (may contain operationally useful historic state):
  - `node_facts-*.json`
  - `node_reality-*.json`
  - `xui_backup_inspected.json`

## guardrails added
- Updated `.gitignore` to block:
  - `webapp/dist/`, `marketing/out/`
  - `.tmp/bench/`
  - `portal_api_test_*.db`
  - `*.tsbuildinfo`
- Added CI guardrails:
  - `.github/workflows/guardrails.yml`
  - `scripts/ci_check_artifacts.py` (artifacts + forbidden public word check)

## scripts manifest policy check
- `scripts/check_script_manifest.py` passes.
- Added `scripts/ci_check_artifacts.py` to `scripts/manifest.yaml` as active script.

---

# Cleanup Update (2026-03-04)

## Scope
- Safe cleanup wave focused on outdated local test artifacts and old mockup workspaces.
- Goal: declutter repository root while preserving rollback/debug history in `legacy/`.

## moved-to-legacy
- Created archive folder:
  - `legacy/archive-20260304/`
- Moved outdated root test databases:
  - `portal_api_test_*.db` (38 files)
- Moved old local backup:
  - `portal.db.from-old-20260207-010831.db`
- Moved large deprecated mockup workspaces:
  - `mockup/`
  - `mockupv2/`
  - `mockupv3/`
  - `mockupv5/`

## keep-in-root
- Kept active local runtime/state files:
  - `portal.db`
  - `portal.db.cluster.db`
  - `x-ui.db`
  - `node_reality-20260208-235214.json`
- Reason: existing scripts use these as default local inputs when arguments are not passed.

## guardrails updated
- Added ignore rule:
  - `mockupv3/`
> Historical file. Preserved as an old cleanup snapshot after the 2026-03-20 documentation refresh.
