# POKROV Owner-Gated Scenario Matrix

Last updated: 2026-06-28

## Purpose

This matrix decomposes the remaining canonical `Manual owner test` row,
`CLIENT_APP-US-067`, into atomic owner/operator scenarios. It is part of the
repo feature-story audit because local automation cannot truthfully close these
checks without physical devices, real user accounts, provider dashboards, live
deploy approval, signing/store access, or RU-origin probe access.

Canonical CSV:
[pokrov-owner-gated-scenarios.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-owner-gated-scenarios.csv)

Result ledger:
[pokrov-owner-gated-results.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-owner-gated-results.csv)

Execution guide:
[pokrov-owner-gated-execution-guide.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-owner-gated-execution-guide.md)

## Current Status

Required owner-gated scenarios still open: 2.

| Gate area | Canonical row | Blocking question | Status | Required for goal completion | Why it is not locally closed |
| --- | --- | --- | --- | --- | --- |
| Android physical release build | `CLIENT_APP-US-067` | `Q-004` | `SKIPPED_BY_OWNER` | `yes` | Owner skipped Android physical execution for this audit on 2026-06-28; do not claim raw Android physical-audit proof. |
| Windows outside-store release build | `CLIENT_APP-US-067` | `Q-004` | `SKIPPED_BY_OWNER` | `yes` | Owner skipped Windows exact-artifact build/install execution for this audit on 2026-06-28; do not claim install/connect proof. |
| Real Telegram WebApp and user session | `CLIENT_APP-US-067` | `Q-004` | `BLOCKED_BY_ACCESS` | `yes` | Telegram Desktop is running, but this Codex session has no callable desktop-control tool; real Telegram account/session evidence is still required. |
| Payment provider and fulfillment maturity | `CLIENT_APP-US-067` | `Q-004` | `SKIPPED_BY_OWNER` | `yes` | Owner skipped payment maturity execution for this audit on 2026-06-28 and stated payments work; do not claim refund/chargeback/reconciliation proof. |
| Signing and store trust | `CLIENT_APP-US-067` | `Q-004` | `SKIPPED_BY_OWNER` | `yes` | Owner skipped all signing/store/trust execution for this audit on 2026-06-28; do not claim store or trusted publisher readiness. |
| Live deploy and deployed app session | `CLIENT_APP-US-067` | `Q-004` | `MANUAL_OWNER_TEST` | `yes` | Current-origin public hosts/API health, brain deploy-state, and brain-origin signed `/api/client/apps` passed on 2026-06-28, but current-origin real app-session and owner deploy approval evidence remain open. |
| RU-origin reachability | `CLIENT_APP-US-067` | `Q-004` | `SKIPPED_BY_OWNER` | `yes` | Owner skipped RU-origin execution for this audit on 2026-06-28 and stated the check was performed on 2026-06-27; retained probe evidence is not attached here. |
| Conditional WARP runtime proof | `CLIENT_APP-US-067` | `Q-004` | `NOT_REQUESTED` | `no` | Required only before stronger public WARP/enhanced-protection release-build claims. |

Partial current-origin artifacts are recorded for the live deploy gate at
`docs/audit-artifacts/current-origin-public-beta-preflight-2026-06-27.json` and
`docs/audit-artifacts/current-origin-runtime-app-download-smoke-2026-06-28.md`,
with dry post-deploy payment/email evidence at
`docs/audit-artifacts/current-origin-public-beta-post-deploy-probe-2026-06-27.json`
and public-host reachability at
`docs/audit-artifacts/current-origin-public-host-reachability-2026-06-28.json`.
Brain-origin authenticated runtime app-download evidence is recorded at
`docs/audit-artifacts/brain-runtime-app-download-smoke-2026-06-28.json`.
Brain deploy-state evidence is recorded at
`docs/audit-artifacts/brain-deploy-state-2026-06-28.md`.
Telegram Desktop tooling blocker evidence is recorded at
`docs/audit-artifacts/telegram-desktop-tooling-blocker-2026-06-28.md`.
They keep the live-deploy gate open: `pokrov.space`, `app.pokrov.space`, API
health, and checkout returned `200` from current origin, public email runtime
and provider catalog checks passed, brain-origin signed `/api/client/apps`
returned GitHub release metadata, and brain services/routes/subscription fetch
were green. The remaining live-deploy gap is real Telegram/current-origin
authenticated app-session evidence plus owner deploy approval.
Payment maturity is skipped by owner for this audit, not upgraded to PASS.

## Result Labels

Allowed labels for these gates are `PASS`, `FAIL`, `MANUAL_OWNER_TEST`,
`OPERATOR_ATTESTED`, `SKIPPED_BY_OWNER`, `BLOCKED_BY_ACCESS`, `NOT_REQUESTED`,
and `NOT_APPLICABLE`.

Do not convert local static tests, unauthenticated endpoint responses, old
operator notes, or stale release evidence into `PASS`. If access is missing,
record `BLOCKED_BY_ACCESS`; if the owner deliberately defers a gate, record
`SKIPPED_BY_OWNER` or `NOT_REQUESTED` as appropriate.

## Completion Rule

The full active goal cannot be marked complete while any required user scenario
in this matrix remains `MANUAL_OWNER_TEST` or `BLOCKED_BY_ACCESS`, unless the
owner explicitly narrows the goal or accepts that external gate as out of scope.
The conditional WARP gate is not required for this audit unless stronger public
WARP/enhanced-protection claims are introduced.

## Result Ledger Rule

`pokrov-owner-gated-results.csv` records the latest result, evidence reference,
defect note, fix status, retest status, owner/access note, next action, and
updated date for each `gate_id`. It must have the same gate IDs as this scenario
matrix. `PASS` and `OPERATOR_ATTESTED` rows require an evidence reference;
`FAIL` rows require a defect note before a fix/retest loop starts.
