# POKROV Coverage Policy Decision Guide

Last updated: 2026-07-14

## Purpose

This guide records the `Q-001` policy decision and keeps the stricter fallback
options visible if the owner changes policy later.

Canonical inputs:

- User-story tracker: [pokrov-canonical-feature-tracker.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-canonical-feature-tracker.csv)
- Low-level symbol inventory: [pokrov-code-function-inventory.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-code-function-inventory.csv)
- Source-symbol coverage audit: [pokrov-symbol-coverage-audit.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-symbol-coverage-audit.csv)
- Private-helper coverage matrix: [pokrov-private-helper-coverage.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-private-helper-coverage.csv) and [pokrov-private-helper-coverage.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-private-helper-coverage.md)
- Completion audit: [COMPLETION-AUDIT.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/work-orders/2026-06-27--repo-feature-story-audit/COMPLETION-AUDIT.md)

## Current Proven State

- Every canonical user-story row has expected behavior, code evidence,
  guardrails, status, latest result, fix status, retest status, and next action.
- Every non-manual story row has direct automated file evidence.
- Every active source symbol is listed in `pokrov-code-function-inventory.csv`.
- Every active source symbol has a tier in `pokrov-symbol-coverage-audit.csv`.
- Current source-symbol review buckets remain open: `public_symbol_review = 12`,
  `client_package_public_api_review = 3`, `script_cli_manifest_review = 1`, and
  `script_cli_active_without_workflow_mapping = 1`.
- The dedicated entrypoint-story ledger reports `needs_story_mapping_review = 0`.
  Separately, the source-symbol audit reports
  `entrypoint_needs_mapping_review = 0`; the dedicated zero does not close the
  four source-symbol review buckets above.
- `private_inventory_only` is guarded so it only contains private non-entrypoint
  symbols.
- `pokrov-private-helper-coverage.csv` currently has 23 private-inventory rows:
  21 low-risk and 2 medium-risk. It has 23 accepted-policy rows and
  0 owner-decision rows under `accepted_story_and_symbol_tiers_q001`; they stay
  tracked as source-inventory-only helpers unless the owner later asks for
  stricter one-test-per-private-helper coverage.
- Owner accepted `ACCEPT_STORY_AND_SYMBOL_TIERS` on 2026-06-28.

## Not Claimed

The current local audit does not claim one dedicated behavior test for every
private helper, every class method, or every low-level source symbol.

Token-level test references are triage signals. They do not prove that the
referenced helper is behavior-tested in isolation.

## Owner Decision Options

| Option | Meaning | Completion impact |
| --- | --- | --- |
| `ACCEPT_STORY_AND_SYMBOL_TIERS` | Source-symbol inventory plus story/entrypoint/public-API/high-risk tests are sufficient. | Selected by owner on 2026-06-28; no one-test-per-private-helper expansion is required for this audit. |
| `REQUIRE_PUBLIC_AND_ENTRYPOINT_ONLY` | Dedicated behavior tests are required for public APIs, external entrypoints, route handlers, script CLIs, and high-risk helpers; private implementation details remain tiered inventory. | Current local audit is largely aligned; any newly identified public/high-risk gaps must become findings and tests. |
| `REQUIRE_ONE_TEST_PER_PRIVATE_HELPER` | Every private helper/class method/source symbol needs a dedicated behavior test or explicit owner waiver. | Not selected; if owner later chooses this stricter policy, extend `pokrov-private-helper-coverage.csv` or pair it with a per-symbol test/waiver ledger. |

## Recommended Default

Use `ACCEPT_STORY_AND_SYMBOL_TIERS` for this audit unless the owner explicitly
requires one-test-per-private-helper coverage.

Reasoning:

- The user's original goal is behavior and user-story focused.
- The canonical tracker already covers user-visible behavior across backend,
  bots, WebApp/admin, marketing, scripts, and client app surfaces.
- Source-symbol tiers make private helpers measurable without turning internal
  implementation details into brittle product stories.
- Dedicated tests should stay focused on public APIs, entrypoints, regression
  findings, high-risk helpers, and user-visible behavior.

## If The Owner Requires One-Test-Per-Private-Helper

Use the existing baseline artifact first:

`docs/developer/pokrov-private-helper-coverage.csv`

It records each private-only symbol with expected behavior, risk, proof status,
and next action. The current matrix contains 23 rows: 21 low-risk and 2
medium-risk. Before future implementation under this strict policy, extend it
or create a paired execution ledger:

`docs/developer/pokrov-private-helper-test-matrix.csv`

Minimum columns:

| Column | Requirement |
| --- | --- |
| `symbol_id` | Must match `pokrov-code-function-inventory.csv`. |
| `path` | Source path from the inventory. |
| `qualified_name` | Symbol name from the inventory. |
| `coverage_required` | `yes`, `no`, or `waived_by_owner`. |
| `test_ref` | Required when `coverage_required=yes`. |
| `waiver_reason` | Required when `coverage_required=waived_by_owner`. |
| `status` | `Needs test`, `Retest passed`, `Waived by owner`, or `Blocked`. |
| `updated_at` | Date of the row update. |

Do not mark Q-001 complete under this option until every required private-helper
row has a passing dedicated test reference or an explicit owner waiver.

## Decision Record

The owner selected `ACCEPT_STORY_AND_SYMBOL_TIERS` on 2026-06-28. Keep Q-001
answered and nonblocking in `pokrov-open-questions.csv`; reopen it only if the
owner later requires a stricter coverage option.
