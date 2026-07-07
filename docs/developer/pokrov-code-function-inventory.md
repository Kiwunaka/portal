# POKROV Low-Level Code Function Inventory

Last updated: 2026-07-05

## Purpose

This companion inventory covers literal source-level symbols: functions, methods, and classes in active production/source code for the root platform repository plus the active `POKROV-app` client lane.

It complements the canonical feature tracker. The canonical tracker remains the user-story/status source of truth; this file and CSV make the lower-level helper/private-method scope measurable.

## Canonical File

- CSV: [pokrov-code-function-inventory.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-code-function-inventory.csv)
- Symbol coverage audit: [pokrov-symbol-coverage-audit.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-symbol-coverage-audit.csv) and [pokrov-symbol-coverage-audit.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-symbol-coverage-audit.md)
- Private helper coverage matrix: [pokrov-private-helper-coverage.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-private-helper-coverage.csv) and [pokrov-private-helper-coverage.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-private-helper-coverage.md)
- Generator: [generate_code_function_inventory.py](C:/Users/kiwun/Documents/ai/VPN/scripts/generate_code_function_inventory.py)
- Private helper generator: [generate_private_helper_coverage.py](C:/Users/kiwun/Documents/ai/VPN/scripts/generate_private_helper_coverage.py)
- Generator test: [test_code_function_inventory.py](C:/Users/kiwun/Documents/ai/VPN/tests/test_code_function_inventory.py)

## Scope

Included:

- root repo active source under `portal_bot/`, `scripts/`, `shared/`, `webapp/`, and `marketing/`
- active client source under `C:/Users/kiwun/Documents/ai/POKROV-app/apps`, `packages`, `lib`, and `scripts`
- Python symbols via `ast`
- TypeScript/TSX, Dart, Kotlin, Swift, and C/C++ host-shell symbols via conservative regex extraction
- token-level test-reference hints from root and active client test files

Excluded:

- `tests/`, `test/`, `e2e/` as source symbols
- `legacy/`, `docs/`, `outputs/`, `out/`, `.tmp/`, `build/`, `node_modules/`, generated, and ephemeral trees
- live/provider/device/RU-origin execution evidence

## Current Counts

| Metric | Count |
| --- | ---: |
| Total symbols | 4827 |
| Root repo symbols | 3586 |
| POKROV-app symbols | 1241 |
| Symbols with token-level test references | 1580 |
| Parser errors | 0 |

### By Language

| Language | Count |
| --- | ---: |
| Python | 2744 |
| Dart | 991 |
| TSX | 551 |
| TypeScript | 291 |
| Kotlin | 130 |
| Swift | 92 |
| C++ | 23 |
| C header | 5 |

### By Subsystem

| Subsystem | Count |
| --- | ---: |
| Backend and Telegram bots | 1663 |
| POKROV client app | 1202 |
| Scripts and Ops | 1081 |
| WebApp and Admin | 695 |
| Marketing site | 105 |
| Shared constants | 81 |

### By Symbol Kind

| Symbol kind | Count |
| --- | ---: |
| Function | 3425 |
| Method | 930 |
| Class | 472 |

### By Entrypoint Hint

| Entrypoint hint | Count |
| --- | ---: |
| FastAPI route handler | 185 |
| Telegram handler | 171 |
| Script CLI main | 125 |
| Framework override | 101 |
| FastAPI middleware | 1 |
| Next.js page component | 1 |

## Interpretation

- `test_ref_count` is a token-level reference signal, not proof that a private helper has a dedicated behavioral test.
- User-story completion is still tracked in `pokrov-canonical-feature-tracker.csv`.
- Helper-level rows are `inventory_only` until a future task chooses to require dedicated private-helper assertions.
- The generated symbol coverage audit guards that `private_inventory_only` is limited to private non-entrypoint symbols.
- The generated private-helper coverage matrix currently has 6 low-risk private inventory-only rows; Q-001 records that story/symbol tiers are sufficient for this audit.
- For public behavior, prefer feature/user-story tests over one-test-per-helper churn.
- Entrypoint hints are conservative labels; Aiogram `router.*` handlers are classified as Telegram handlers before HTTP route detection, and HTTP route detection requires route decorators such as `app.get`, `app.post`, or `app.api_route`.
- Source-symbol coverage status lives in `pokrov-symbol-coverage-audit.csv`; it distinguishes entrypoint/story/dependency/module-test/test/client-platform/manual-gate/framework/tooling/private/public-API-review tiers for all 4827 symbols.
- Source-symbol coverage also includes `expected_behavior_from_code`, a generated behavior-preservation note for every symbol that keeps manual/review buckets honest instead of treating them as direct proof.

## Regeneration

Run:

```powershell
python scripts/generate_code_function_inventory.py
```

Validation used in this pass:

```powershell
python -m pytest tests/test_code_function_inventory.py -q --basetemp .tmp/pytest-entrypoint-hints
python -m pytest tests/test_story_test_evidence_audit.py tests/test_telegram_story_contracts.py -q --basetemp .tmp/pytest-entrypoint-story-telegram-map
python -m pytest tests/test_postgres_operator_scripts.py tests/test_check_script_manifest.py tests/test_code_function_inventory.py -q --basetemp .tmp/pytest-script-manifest-status
python -m pytest tests/test_code_function_inventory.py tests/test_freekassa_staging_smoke.py tests/test_story_test_evidence_audit.py tests/test_check_script_manifest.py -q --basetemp .tmp/pytest-symbol-triage-focused
flutter test test/design_system_contract_test.dart --reporter compact  # in C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/
npm.cmd run build  # in webapp/
npm.cmd run build  # in marketing/
python -m pytest -q --basetemp .tmp/pytest-full-after-client-package-api
python scripts/generate_code_function_inventory.py
python scripts/generate_private_helper_coverage.py
```
