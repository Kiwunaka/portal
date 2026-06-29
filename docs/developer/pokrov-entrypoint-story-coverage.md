# POKROV Entrypoint Story Coverage

Last updated: 2026-06-27

## Purpose

This audit links source entrypoints from `pokrov-entrypoint-inventory.csv` to the strongest current story, route, or script test evidence.

It complements the canonical feature tracker and prevents false gaps from literal token search. For example, a FastAPI handler does not need its Python function name mentioned in a test when the endpoint route is already covered by `pokrov-backend-route-coverage.csv`.

## Canonical File

- CSV: [pokrov-entrypoint-story-coverage.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-entrypoint-story-coverage.csv)
- Source entrypoints: [pokrov-entrypoint-inventory.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-entrypoint-inventory.csv)
- Auditor: [audit_story_test_evidence.py](C:/Users/kiwun/Documents/ai/VPN/scripts/audit_story_test_evidence.py)
- Auditor test: [test_story_test_evidence_audit.py](C:/Users/kiwun/Documents/ai/VPN/tests/test_story_test_evidence_audit.py)

## Current Counts

| Coverage tier | Count |
| --- | ---: |
| Direct route test ref | 165 |
| Direct script test ref | 123 |
| Direct story test ref | 226 |
| Needs story mapping review | 0 |

| Entrypoint type | Count |
| --- | ---: |
| FastAPI route | 165 |
| Script CLI | 123 |
| Aiogram handler | 172 |
| Next.js page route | 41 |
| Flutter feature file | 13 |

## Interpretation

- `direct_route_test_ref` means a FastAPI route maps to `pokrov-backend-route-coverage.csv` with direct automated test files.
- `direct_script_test_ref` means a script CLI maps to `pokrov-script-workflow-coverage.csv` with direct automated test files.
- `direct_story_test_ref` means an aiogram handler, Next.js page route, or Flutter feature file maps to canonical story rows with direct automated test files.
- Flutter helper files under `packages/app_shell/lib/src/features/<feature>/` can map to a story for the same feature directory when the user-facing surface file carries the scenario.
- `Needs story mapping review = 0` means every current source entrypoint has a local evidence mapping. It does not claim live Telegram account, payment-provider, physical-device, store/signing, deploy, SSH, or RU-origin execution.

## Latest Fixes

- Updated stale POKROV-app `code_evidence` paths from pre-`features/` layout paths to active `packages/app_shell/lib/src/features/...` paths.
- Made Telegram story mappings explicit for `noop`, `share_access`, `menu_more`, `handle_text_input`, helpbot `capture_ticket_reply`, and feedbackbot `fb_back_home`.
- Added a canonical source-evidence guard so every `code_evidence` file ref resolves in the root repo or active `POKROV-app` repo.
- Classified active script CLI entrypoints as active workflows, including the private-helper coverage generator, and kept 2 legacy FreeKassa CLIs out of active entrypoint coverage as deprecated manifest entries.

## Regeneration

Run:

```powershell
python scripts/audit_story_test_evidence.py
```

Validation used in this pass:

```powershell
python -m pytest tests/test_postgres_operator_scripts.py tests/test_story_test_evidence_audit.py tests/test_code_function_inventory.py tests/test_check_script_manifest.py -q --basetemp .tmp/pytest-script-manifest-status
```
