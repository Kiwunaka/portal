# POKROV Story Test Evidence Audit

Last updated: 2026-06-27

## Purpose

This companion audit classifies every canonical user-story row by the strength of its test evidence. The same auditor also builds the entrypoint-to-story coverage bridge.

It does not replace the canonical feature tracker. It answers narrower questions: whether a story row points to machine-checkable automated test files, only to retained imported workbook evidence, or to an owner-controlled manual gate, and whether required story-contract fields remain populated.

## Canonical File

- CSV: [pokrov-story-test-evidence-audit.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-story-test-evidence-audit.csv)
- Entrypoint coverage CSV: [pokrov-entrypoint-story-coverage.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-entrypoint-story-coverage.csv)
- Entrypoint coverage summary: [pokrov-entrypoint-story-coverage.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-entrypoint-story-coverage.md)
- Owner-gated scenarios: [pokrov-owner-gated-scenarios.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-owner-gated-scenarios.csv) and [pokrov-owner-gated-results.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-owner-gated-results.csv)
- Source tracker: [pokrov-canonical-feature-tracker.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-canonical-feature-tracker.csv)
- Auditor: [audit_story_test_evidence.py](C:/Users/kiwun/Documents/ai/VPN/scripts/audit_story_test_evidence.py)
- Auditor test: [test_story_test_evidence_audit.py](C:/Users/kiwun/Documents/ai/VPN/tests/test_story_test_evidence_audit.py)

## Current Counts

| Evidence tier | Count |
| --- | ---: |
| `direct_file_ref` | 524 |
| `imported_pass_no_file_ref` | 0 |
| `manual_owner_gate` | 1 |
| `stale_file_ref` | 0 |
| `weak_or_missing_evidence` | 0 |

### Retest Proof Status

| Retest proof status | Count |
| --- | ---: |
| `direct_test_ref_passed` | 524 |
| `manual_owner_gate_open` | 1 |
| `direct_test_ref_without_pass_result` | 0 |
| `stale_test_ref` | 0 |
| `imported_pass_without_direct_ref` | 0 |
| `pass_without_direct_ref` | 0 |
| `weak_or_missing_retest_evidence` | 0 |

| Metric | Count |
| --- | ---: |
| Total audited story rows | 525 |
| Missing referenced test files | 0 |
| Missing required story contract fields | 0 |
| Priority-only `canon_guardrails` rows | 0 |
| Rows without resolvable `code_evidence` refs | 0 |
| Rows with unresolved `source_tracker` refs | 0 |
| Owner-gated scenario rows | 8 |
| Owner-gated result rows | 8 |
| Required owner-gated scenarios still open | 2 |

### Entrypoint Coverage Output

| Coverage tier | Count |
| --- | ---: |
| `direct_route_test_ref` | 165 |
| `direct_script_test_ref` | 123 |
| `direct_story_test_ref` | 226 |
| `needs_story_mapping_review` | 0 |

## Interpretation

- `direct_file_ref` means the row references one or more existing automated test files.
- `imported_pass_no_file_ref` means a retained XLSX source tracker records passing evidence, but the canonical CSV does not yet expose a machine-checkable test-file mapping for that individual story.
- `manual_owner_gate` means the row is correctly blocked on owner-controlled live/device/provider/store/RU evidence.
- `stale_file_ref` would mean a referenced test file no longer exists.
- `weak_or_missing_evidence` would mean the row has neither strong automated evidence, imported-pass evidence, nor an explicit manual gate.
- `retest_proof_status` is a stricter per-story retest label: local non-manual stories must be `direct_test_ref_passed`; owner-only stories must be `manual_owner_gate_open`; all weak/stale/direct-without-pass buckets must remain 0.

## Current Result

`STORY-EVIDENCE-MAP-001` is closed for local repository evidence mapping: every non-manual canonical story row now has at least one direct existing automated test-file reference.

The remaining `manual_owner_gate` row is a real owner-controlled client/device/live verification gate, not a missing local test-file mapping.

That row is decomposed in `pokrov-owner-gated-scenarios.csv` so the manual phase has atomic scenarios, expected behavior, required evidence, allowed result labels, and source-doc references. Latest manual results, evidence refs, defect notes, fix status, and retest status live in `pokrov-owner-gated-results.csv`. The guard also checks the reverse link: every owner-gated scenario must point to a canonical row that is still `Manual owner test`.

Progress in this pass:

- mapped all 66 non-manual `POKROV client app` imported rows to direct Dart/Kotlin test-file references
- mapped Telegram, WebApp/admin, and marketing imported rows to direct Playwright/pytest/story-contract test-file references
- added `tests/test_marketing_story_contracts.py` and `tests/test_telegram_story_contracts.py` for story-level source/route/trigger contracts that were previously only visible as workbook or command evidence
- kept the one client manual-owner row as `manual_owner_gate`
- added `pokrov-entrypoint-story-coverage.csv` so source entrypoints are mapped to route/story/script evidence instead of relying on function-name token matches
- fixed stale client `code_evidence` paths to active `packages/app_shell/lib/src/features/...` paths
- made six Telegram handler mappings explicit in canonical rows and `tests/test_telegram_story_contracts.py`
- added `test_canonical_code_evidence_source_refs_exist` so stale root/client source refs are caught in pytest
- added 20 active script/operator rows from `scripts/manifest.yaml` and kept the two legacy FreeKassa CLIs explicit as deprecated, not active user stories
- added `test_canonical_source_trackers_are_resolvable` so tracker provenance must resolve to an existing source workbook/path or to the generated-source labels backed by `portal_bot/api.py` and `scripts/manifest.yaml`
- added `test_owner_gated_scenarios_are_explicit_and_resolvable` so every manual-owner canonical row is decomposed into concrete source-linked scenarios and matching result-ledger rows before owner execution

## Regeneration

Run:

```powershell
python scripts/audit_story_test_evidence.py
```

Validation used in this pass:

```powershell
python -m pytest tests/test_postgres_operator_scripts.py tests/test_story_test_evidence_audit.py tests/test_code_function_inventory.py tests/test_check_script_manifest.py -q --basetemp .tmp/pytest-script-manifest-status
python -m pytest tests/test_story_test_evidence_audit.py -q --basetemp .tmp/pytest-priority-only-guardrails-pack
python -m pytest tests/test_story_test_evidence_audit.py tests/test_code_function_inventory.py tests/test_check_script_manifest.py -q --basetemp .tmp/pytest-source-tracker-focused
python -m pytest tests/test_story_test_evidence_audit.py::test_owner_gated_scenarios_are_explicit_and_resolvable -q --basetemp .tmp/pytest-owner-gates-targeted
python scripts/audit_story_test_evidence.py
```
