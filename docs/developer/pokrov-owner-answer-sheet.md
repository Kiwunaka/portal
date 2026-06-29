# POKROV Owner Answer Sheet

Last updated: 2026-06-28

## Purpose

This is the short owner-facing answer sheet for the remaining feature-story
audit questions. It complements the canonical ledgers:

- [pokrov-open-questions.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-open-questions.csv)
- [pokrov-coverage-policy-decision-guide.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-coverage-policy-decision-guide.md)
- [pokrov-owner-gated-scenarios.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-owner-gated-scenarios.csv)
- [pokrov-owner-gated-results.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-owner-gated-results.csv)
- [pokrov-owner-gated-execution-guide.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-owner-gated-execution-guide.md)

## Recorded Answers

### Q-001 Coverage Policy

Recorded owner answer: `ACCEPT_STORY_AND_SYMBOL_TIERS` on 2026-06-28.

| Code | Meaning | Next action |
| --- | --- | --- |
| `ACCEPT_STORY_AND_SYMBOL_TIERS` | Current story tests plus source-symbol tiers are sufficient for this audit. | Recorded; keep current audit policy unless the owner later changes it. |
| `REQUIRE_PUBLIC_AND_ENTRYPOINT_ONLY` | Public APIs, external entrypoints, route handlers, script CLIs, and high-risk helpers require dedicated tests. | Keep Q-001 open only for any newly identified public/high-risk gaps. |
| `REQUIRE_ONE_TEST_PER_PRIVATE_HELPER` | Every private helper/class method/source symbol needs a dedicated test or owner waiver. | Extend or create the private-helper test/waiver matrix before closing Q-001. |

Recommended default for this audit: `ACCEPT_STORY_AND_SYMBOL_TIERS`.

## Blocking Answers Needed

### Q-004 Owner-Gated Execution

Choose the next gate to execute, or explicitly mark a gate skipped/blocked with
evidence. The owner skipped Android, Windows build/install, payment maturity,
signing/store, and RU-origin checks for this audit on 2026-06-28. Required
Telegram WebApp/session and live deploy app-session gates remain open for
`CLIENT_APP-US-067`. Current-origin public hosts/API health, brain deploy-state,
and brain-origin signed `/api/client/apps` smoke passed on 2026-06-28, but real
Telegram/current-origin authenticated session evidence and owner deploy approval
are still not closed. Telegram WebApp execution is currently
`BLOCKED_BY_ACCESS` in this Codex session because no callable desktop-control
tool is exposed.

| Gate ID | Required | Current status | Answer format |
| --- | --- | --- | --- |
| `OWNER-GATE-ANDROID-PHYSICAL-INSTALL-CONNECT` | `yes` | `SKIPPED_BY_OWNER` | Reopen only if current Android physical evidence is needed. |
| `OWNER-GATE-WINDOWS-INSTALL-CONNECT` | `yes` | `SKIPPED_BY_OWNER` | Reopen only if owner runs the manual Windows exact-artifact smoke. |
| `OWNER-GATE-TELEGRAM-WEBAPP-SESSION` | `yes` | `BLOCKED_BY_ACCESS` | Provide redacted owner evidence, expose a callable desktop-control tool in a future session and answer `EXECUTE OWNER-GATE-TELEGRAM-WEBAPP-SESSION`, or `SKIP/ATTEST ... reason` |
| `OWNER-GATE-PAYMENT-DASHBOARD-MATURITY` | `yes` | `SKIPPED_BY_OWNER` | Reopen only if refund/chargeback/reconciliation proof is needed. |
| `OWNER-GATE-SIGNING-STORE-TRUST` | `yes` | `SKIPPED_BY_OWNER` | Reopen only if store/trusted-signing claims are needed. |
| `OWNER-GATE-LIVE-DEPLOY-APP-SESSION` | `yes` | `MANUAL_OWNER_TEST` | Current-origin public reachability, brain deploy-state, and brain-origin smoke are recorded; provide current-origin authenticated app-session/deploy approval evidence or `SKIP/BLOCK ... reason` |
| `OWNER-GATE-RU-ORIGIN-PROBE` | `yes` | `SKIPPED_BY_OWNER` | Reopen only with retained RU-origin probe evidence if a readiness claim is needed. |
| `OWNER-GATE-WARP-RUNTIME-RELEASE-BUILD` | `no` | `NOT_REQUESTED` | Keep `NOT_REQUESTED` unless stronger public WARP claims are planned. |

Allowed result labels are `PASS`, `FAIL`, `MANUAL_OWNER_TEST`,
`OPERATOR_ATTESTED`, `SKIPPED_BY_OWNER`, `BLOCKED_BY_ACCESS`,
`NOT_REQUESTED`, and `NOT_APPLICABLE`.

## Optional Answers

### Q-002 Tracker Format

Default answer: keep CSV/Markdown as canonical status artifacts; keep XLSX
files as source audit artifacts.

Owner override: request binary workbook status as canonical.

### Q-003 Execution Model

Default answer: no sub-agent reviewers unless explicitly approved.

Owner override: approve parallel sub-agent review for future broad passes.

## Recording Rule

Record owner answers in `pokrov-open-questions.csv`. Record gate execution
results in `pokrov-owner-gated-results.csv`.

Do not mark any owner gate `PASS` without current redacted evidence. If access
is unavailable, use `BLOCKED_BY_ACCESS`; if the owner deliberately defers a
gate, use `SKIPPED_BY_OWNER`.
