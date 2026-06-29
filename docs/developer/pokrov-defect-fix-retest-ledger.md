# POKROV Defect Fix Retest Ledger

Last updated: 2026-06-27

## Purpose

This generated ledger extracts every canonical story row with
`defects_or_issues` and records the fix, retest, proof refs, and closure
status in one audit table. It supports the goal requirement to document
discrepancies, fixes, and repeat verification separately from the full
feature/story tracker.

## Canonical Files

- CSV: [pokrov-defect-fix-retest-ledger.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-defect-fix-retest-ledger.csv)
- Source tracker: [pokrov-canonical-feature-tracker.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-canonical-feature-tracker.csv)
- Story evidence audit: [pokrov-story-test-evidence-audit.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-story-test-evidence-audit.csv)
- Generator: [generate_defect_fix_retest_ledger.py](C:/Users/kiwun/Documents/ai/VPN/scripts/generate_defect_fix_retest_ledger.py)

## Current Counts

| Metric | Count |
| --- | ---: |
| Defect rows | 18 |
| Closed and retested rows | 16 |
| Closed no-product-change rows | 2 |
| Rows needing retest proof | 0 |
| Manual owner-gate defect rows | 0 |
| Open or weak closure rows | 0 |

### By Closure Status

| Label | Count |
| --- | ---: |
| `closed_retested` | 16 |
| `closed_retested_no_product_change` | 2 |

### By Defect Area

| Label | Count |
| --- | ---: |
| `client_app_story` | 1 |
| `operator_script_safety` | 3 |
| `telegram_ux_logic` | 5 |
| `test_harness_or_audit` | 4 |
| `webapp_user_flow` | 5 |

### By Subsystem

| Label | Count |
| --- | ---: |
| `Marketing site` | 4 |
| `POKROV client app` | 1 |
| `Scripts and Ops` | 3 |
| `Telegram bots` | 5 |
| `WebApp and Admin` | 5 |

## Completion Rule

Local defect rows are considered closed only when `closure_status` is
`closed_retested` or `closed_retested_no_product_change` and
`retest_proof_status` is `direct_test_ref_passed`. Owner-only gates stay
outside this local defect ledger unless their canonical row records a
defect.

## Regeneration

```powershell
python scripts\generate_defect_fix_retest_ledger.py
```
