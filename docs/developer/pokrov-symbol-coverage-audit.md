# POKROV Source Symbol Coverage Audit

Last updated: 2026-07-14

## Purpose

This audit gives every active source-level symbol from `pokrov-code-function-inventory.csv` an explicit coverage/status tier and generated `expected_behavior_from_code` note.

It closes the literal "each function/class/method" tracking gap without pretending that every private helper should become a user story. User-visible behavior remains tracked in `pokrov-canonical-feature-tracker.csv`; this table keeps low-level symbols measurable and reviewable.

## Canonical File

- CSV: [pokrov-symbol-coverage-audit.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-symbol-coverage-audit.csv)
- Source inventory: [pokrov-code-function-inventory.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-code-function-inventory.csv)
- Private helper coverage matrix: [pokrov-private-helper-coverage.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-private-helper-coverage.csv) and [pokrov-private-helper-coverage.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-private-helper-coverage.md)
- Generator: [generate_code_function_inventory.py](C:/Users/kiwun/Documents/ai/VPN/scripts/generate_code_function_inventory.py)
- Private helper generator: [generate_private_helper_coverage.py](C:/Users/kiwun/Documents/ai/VPN/scripts/generate_private_helper_coverage.py)
- Generator test: [test_code_function_inventory.py](C:/Users/kiwun/Documents/ai/VPN/tests/test_code_function_inventory.py)

## Current Counts

| Coverage tier | Count |
| --- | ---: |
| Story source file | 3316 |
| Story dependency source file | 810 |
| Entrypoint mapped | 464 |
| Direct token test ref | 266 |
| Module test ref | 78 |
| Private inventory only | 23 |
| Client platform host manual gate | 77 |
| Entrypoint route test ref | 22 |
| Operator tooling inventory | 5 |
| Next route boundary inventory | 7 |
| Client desktop tray manual gate | 3 |
| QA tooling inventory | 1 |
| Script CLI deprecated | 2 |
| Telegram WebApp bootstrap inventory | 1 |
| Entrypoint story source ref | 11 |
| Client package public API review | 3 |
| Entrypoint needs mapping review | 0 |
| Public symbol review | 12 |

### Manual Gate Reference Counts

| Label | Count |
| --- | ---: |
| OWNER-GATE-ANDROID-PHYSICAL-INSTALL-CONNECT | 32 |
| OWNER-GATE-WINDOWS-INSTALL-CONNECT | 26 |
| NOT_CURRENT_PUBLIC_BETA_TARGET | 22 |

## Interpretation

- `entrypoint_mapped` means the symbol maps to entrypoint route/story/script coverage.
- `entrypoint_route_test_ref` means a FastAPI route path is directly referenced by automated tests but should be promoted to route/story coverage if it becomes a public contract.
- `entrypoint_story_source_ref` means an entrypoint is at least tied to a story source file, but a narrower route/handler mapping is preferable when behavior changes.
- `script_cli_deprecated` means a script has a `main()` CLI entrypoint and is explicitly retained outside active workflow coverage, currently for legacy FreeKassa guard tooling.
- `story_source_file` means the symbol lives in a file referenced by canonical story evidence.
- `story_dependency_source_file` means a local Python or TypeScript/TSX dependency, including symbol-free barrel/re-export modules, is reachable from a source file referenced by canonical story evidence.
- `direct_token_test_ref` means the symbol name appears in automated test files.
- `module_test_ref` means the source module/import path or parent type appears in automated tests, but the individual symbol name is not directly asserted.
- `client_platform_host_manual_gate` means public native client host symbols are tracked separately from ordinary backend/web helpers and need platform/unit/simulator/device evidence before stronger runtime claims.
- `client_desktop_tray_manual_gate` means Windows shell tray callbacks are tracked as desktop-host behavior that needs Windows shell smoke or manual owner evidence before runtime claims.
- `manual_gate_refs` links those manual-tier symbols to the relevant owner gate (`OWNER-GATE-ANDROID-PHYSICAL-INSTALL-CONNECT`, `OWNER-GATE-WINDOWS-INSTALL-CONNECT`) or to `NOT_CURRENT_PUBLIC_BETA_TARGET` for iOS/macOS host code that is inventoried but not part of the current public beta target.
- Any `OWNER-GATE-*` value in `manual_gate_refs` must resolve to `pokrov-owner-gated-scenarios.csv`; this keeps low-level symbol scope synchronized with the Q-004 manual scenario ledger instead of a hard-coded side list.
- `client_package_public_api_review` means a public Flutter/Dart package API exists without a direct story/test signal in the root audit; current count is `3`.
- `next_route_boundary_inventory` means a Next.js `layout`, `error`, `not-found`, or similar route boundary component is invoked by framework convention and should be covered through route/e2e behavior.
- `telegram_webapp_bootstrap_inventory` means the Telegram WebApp root-layout integration component is app-wide bootstrap glue, not an ordinary helper.
- `qa_tooling_inventory` and `operator_tooling_inventory` keep QA/operator-only tools visible without treating them as public user stories.
- `private_inventory_only` is expected for low-level helpers that are not story contracts. The generated CSV is guarded so this tier contains only `visibility=private` symbols with no entrypoint hint. Q-001 records that story/symbol tiers are sufficient for this audit unless the owner later requires one-test-per-private-helper coverage.
- `public_symbol_review` is a triage bucket: these public symbols have no direct story, entrypoint, or token-test signal yet.
- `expected_behavior_from_code` is a generated behavior-preservation note for every symbol. It names what the symbol must preserve under its current tier and explicitly keeps manual/review tiers from becoming false coverage claims.

## Current Open Review Buckets

- `script_cli_manifest_review`: 1.
- `script_cli_active_without_workflow_mapping`: 1.
- `public_symbol_review`: 12.
- `client_package_public_api_review`: 3.
- Manual-gate buckets remain evidence honest: `client_platform_host_manual_gate` 77, `client_desktop_tray_manual_gate` 3, and `telegram_webapp_bootstrap_inventory` 1. Platform/tray manual-tier rows carry `manual_gate_refs`; Telegram bootstrap inventory is tracked through browser/Telegram WebApp integration evidence rather than the platform owner-gate matrix.
- `entrypoint_needs_mapping_review`: 0.
- `private_inventory_only` public/entrypoint leakage: 0; current private inventory-only rows: 23.

## Latest Fixes

- Added route-path test fallback for FastAPI route symbols so callback/subscription/email-relay routes with direct tests are not misreported as unmapped.
- Added `tests/test_email_relay_app.py` for `/healthz` and fail-closed `/email/deliver` secret behavior.
- Split non-active script CLIs into explicit manifest-status tiers instead of mixing them with externally reachable entrypoint gaps.
- An earlier pass classified 20 script CLIs as active workflows and 2 legacy FreeKassa CLIs as deprecated; the current generated review/gap counts are reported above.
- Added `story_dependency_source_file` for Python and TypeScript/TSX files imported from story-mapped source files, and `module_test_ref` so public helpers in modules imported or parent-types exercised by tests are separated from truly untriaged public symbols.
- Added `client_platform_host_manual_gate` so native Android/iOS/macOS/Windows host symbols are visible as platform/manual verification scope instead of ordinary public helper review.
- Fixed TypeScript/Dart visibility and import-graph precision: module-local TS helpers and methods on private Dart classes are no longer treated as public API; multiline TS re-exports and symbol-free barrel modules now participate in story dependency mapping; generator self-tests are excluded from product coverage signals.
- Removed unused stale frontend helpers `webapp/src/lib/pricing.ts` and `marketing/src/components/ui/fade-up.tsx`.
- Added specialized tiers for Next route boundaries, Telegram WebApp bootstrap, QA/operator tooling, Windows tray callbacks, and client package public API review; the current `public_symbol_review` count is reported above.
- Added direct FreeKassa checkout-ticket helper coverage in `tests/test_freekassa_staging_smoke.py`.
- Added direct POKROV-app Flutter contract coverage for app-shell design-system and platform bootstrap public APIs; the current `client_package_public_api_review` count is reported above.
- Reclassified `@app.middleware` as `fastapi_middleware`, not as a FastAPI route handler.
- Added a generated-artifact guard that fails if `private_inventory_only` ever contains a public symbol or entrypoint hint.
- Added `pokrov-private-helper-coverage.csv` and `.md` so the current private-inventory rows have per-symbol expected behavior, risk, proof status, and Q-001 next action.
- Added `expected_behavior_from_code` to the source-symbol coverage CSV so all functions/classes/methods have a machine-readable behavior-preservation note tied to their current coverage tier.
- Added `manual_gate_refs` to the source-symbol coverage CSV so client platform/tray manual-tier functions point to the Android/Windows owner gate or an explicit not-current-beta-target scope marker; the guard resolves owner gate refs against `pokrov-owner-gated-scenarios.csv`.

## Regeneration

Run:

```powershell
python scripts/generate_code_function_inventory.py
```

Validation used in this pass:

```powershell
python -m pytest tests/test_code_function_inventory.py tests/test_freekassa_staging_smoke.py tests/test_story_test_evidence_audit.py tests/test_check_script_manifest.py -q --basetemp .tmp/pytest-symbol-triage-focused
python -m pytest tests/test_code_function_inventory.py::test_generated_private_inventory_tier_contains_only_private_non_entrypoints -q --basetemp .tmp/pytest-private-inventory-tier-targeted
flutter test test/design_system_contract_test.dart --reporter compact  # in C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/
npm.cmd run build  # in webapp/
npm.cmd run build  # in marketing/
python -m pytest -q --basetemp .tmp/pytest-full-after-client-package-api
python scripts/generate_code_function_inventory.py
python scripts/generate_private_helper_coverage.py
```
