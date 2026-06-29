# POKROV Owner-Gated Execution Guide

Last updated: 2026-06-27

## Purpose

This guide turns the remaining owner-only user scenarios into an executable
evidence packet. It does not replace the canonical ledgers:

- Scenario matrix: [pokrov-owner-gated-scenarios.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-owner-gated-scenarios.csv)
- Result ledger: [pokrov-owner-gated-results.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-owner-gated-results.csv)
- Summary: [pokrov-owner-gated-scenarios.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-owner-gated-scenarios.md)
- Source-symbol manual scope: [pokrov-symbol-coverage-audit.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-symbol-coverage-audit.csv)

Use this file when the owner is ready to execute `Q-004`.

## Scenario Matrix Contract

Every row in `pokrov-owner-gated-scenarios.csv` must keep these fields filled:

| Field | Requirement |
| --- | --- |
| `gate_id` | Stable owner-gate identifier used by the result ledger. |
| `canonical_row` | Canonical story row that remains manual; currently `CLIENT_APP-US-067`. |
| `gate_area` | Human-readable gate area. |
| `current_status` | Same allowed status vocabulary as the result ledger. |
| `required_for_goal_completion` | `yes` for required owner gates, `no` for conditional gates. |
| `blocking_question_id` | Open owner question that blocks closure; current owner-gate rows point to `Q-004`. |
| `scenario` | Concrete user/operator scenario to execute. |
| `expected_behavior` | Behavior that must be true before the gate can pass. |
| `required_evidence` | Minimum redacted evidence required for pass or attestation. |
| `allowed_result_labels` | Semicolon-separated allowed result labels. |
| `source_docs` | Canonical docs that justify the gate. |
| `claim_guardrail` | Public-claim limitation while the gate remains open. |
| `next_action` | Concrete next owner/operator action. |

Client platform/tray source-symbol rows in `pokrov-symbol-coverage-audit.csv`
use `manual_gate_refs` to point back to this scenario matrix. Any
`OWNER-GATE-*` symbol reference must match a `gate_id` in
`pokrov-owner-gated-scenarios.csv`; symbols outside the current public beta
target use `NOT_CURRENT_PUBLIC_BETA_TARGET`.

## Result Ledger Contract

For each executed gate, update exactly one row in
`pokrov-owner-gated-results.csv`.

Required result fields:

| Field | Requirement |
| --- | --- |
| `gate_id` | Must match one row in `pokrov-owner-gated-scenarios.csv`. |
| `current_status` | Use only `PASS`, `FAIL`, `MANUAL_OWNER_TEST`, `OPERATOR_ATTESTED`, `SKIPPED_BY_OWNER`, `BLOCKED_BY_ACCESS`, `NOT_REQUESTED`, or `NOT_APPLICABLE`. |
| `latest_result` | Human-readable result with exact artifact/session/probe context. |
| `evidence_ref` | Required for `PASS` and `OPERATOR_ATTESTED`; optional for still-manual rows. |
| `defects_or_issues` | Required for `FAIL`; include user-visible mismatch and source/evidence pointer. |
| `fix_status` | `Not needed`, `Needs fix`, `Fixed`, `Blocked by access`, or equivalent explicit state. |
| `retest_status` | `Retest passed`, `Needs retest`, `Manual owner test`, `Blocked by access`, `Not requested`, or equivalent explicit state. |
| `owner_or_access_note` | State who/what access was required and whether it was available. |
| `next_action` | Concrete next step, not a vague reminder. |
| `updated_at` | Use the date of the evidence update. |

Do not put secrets, raw Telegram init data, bearer subscription links, payment
tokens, private keys, dashboard session IDs, or unredacted personal contact data
in any evidence reference.

## Gate Checklist

| Gate ID | Execute When | Minimum Evidence |
| --- | --- | --- |
| `OWNER-GATE-ANDROID-PHYSICAL-INSTALL-CONNECT` | The exact public APK asset is ready for owner physical-device review. | APK URL and SHA256, device model, Android version, install result, first-launch result, managed profile fetch, connect/disconnect result, localhost/control-surface audit output, redacted screenshots or screen recording. |
| `OWNER-GATE-WINDOWS-INSTALL-CONNECT` | The exact public Windows EXE or ZIP is ready for owner machine review. | Artifact URL and SHA256, Windows version, installer or ZIP path, unknown-publisher/SmartScreen note, first-launch result, connect/disconnect/reconnect result, redacted screenshots or screen recording. |
| `OWNER-GATE-TELEGRAM-WEBAPP-SESSION` | A real Telegram account can open the bot/WebApp for the exact deployed flow. | Telegram account class, redacted screenshots, authenticated app-session result, `/api/client/apps` status and asset metadata with secrets redacted, cabinet/support/checkout/redeem/bonus observations. |
| `OWNER-GATE-PAYMENT-DASHBOARD-MATURITY` | Provider dashboard and fulfillment-ledger access are available. | Provider dashboard screenshots with secrets redacted, payment attempt ID, webhook event ID, ledger/reconciliation output, refund or chargeback handling note. |
| `OWNER-GATE-SIGNING-STORE-TRUST` | Signing identity or store dashboard access is available. | Signing material presence without secrets, signed artifact metadata, package identity check, publisher identity check, store dashboard state, redacted submission screenshots, explicit note for unavailable trust lanes. |
| `OWNER-GATE-LIVE-DEPLOY-APP-SESSION` | Current deployed hosts and authenticated app session can be tested for the exact candidate. | Current-origin smoke output, brain-origin smoke output, authenticated `/api/client/apps` output, release URL/hash comparison, deploy approval note. |
| `OWNER-GATE-RU-ORIGIN-PROBE` | `mini` / `RFMINI` or an approved replacement RU-origin host is reachable. | Probe host identity, command output, target list, timestamp, redacted network errors, `PASS`/`FAIL`/`BLOCKED_BY_ACCESS` classification. |
| `OWNER-GATE-WARP-RUNTIME-RELEASE-BUILD` | Only before stronger public WARP/enhanced-protection claims. | Artifact and platform, Android/Windows artifact, runtime state, consent/revoke observations, fallback result, support diagnostics payload check, redaction check. |

## Status Rules

- `PASS` requires `evidence_ref`, `retest_status=Retest passed`, and either
  `fix_status=Not needed` or `fix_status=Fixed`.
- Use `PASS` only when the exact scenario was executed and evidence is attached.
- Use `OPERATOR_ATTESTED` only when the operator supplies an explicit current
  attestation that substitutes for raw evidence.
- `FAIL` requires `defects_or_issues`, `fix_status=Needs fix` or
  `fix_status=Blocked by access`, and `retest_status=Needs retest`.
- Use `FAIL` when behavior diverges from expected behavior; record the defect
  before starting a fix/retest loop.
- `BLOCKED_BY_ACCESS` requires `evidence_ref` and a clear access-block note in
  `latest_result`, `owner_or_access_note`, `fix_status`, or `retest_status`.
- Use `BLOCKED_BY_ACCESS` when the required account, device, host, dashboard, or
  probe cannot be accessed; include the blocked access evidence.
- `SKIPPED_BY_OWNER` requires owner context and an explicit skip or not-requested
  context in the result row.
- Use `SKIPPED_BY_OWNER` only when the owner deliberately defers a required gate.
- `NOT_REQUESTED` is allowed only for conditional gates and should use
  `retest_status=Not requested`.
- Keep `OWNER-GATE-WARP-RUNTIME-RELEASE-BUILD` as `NOT_REQUESTED` unless stronger
  public WARP/enhanced-protection claims are introduced.

## Completion Rule

The full repo feature-story audit goal is not complete while any required gate
has `current_status=MANUAL_OWNER_TEST` or `current_status=BLOCKED_BY_ACCESS`,
unless the owner explicitly narrows the goal or accepts that gate as out of
scope for completion.
