# POKROV Open Beta v4 Work Order

Status: public beta GO with accepted skips
Started: 2026-04-26
Platform branch: `codex/open-beta-v4`
Client branch: `codex/open-beta-v4`
Last indexed: 2026-05-26

This folder tracks execution of `POKROV_open_beta_1_0_orchestrator_superplan_v4.md`.

Current decision:

- `2026-05-15`: release `POKROV` as a public Android + Windows beta outside app stores.
- Machine-readable decision: `docs/audit-artifacts/public-beta-launch-decision-2026-05-15.json`.
- Human decision: `13-launch-decision.md`.
- Accepted limitations: RU-origin skipped by operator, Android raw physical audit evidence replaced by owner attestation for this beta, Windows remains unsigned.

Reference boundary:

- this folder is retained execution evidence for the Open Beta v4 preparation wave
- canonical product, architecture, operations, design, and active client truth remain in the root canonical docs and `C:/Users/kiwun/Documents/ai/POKROV-app/docs/`
- rendered route maps, visual audits, and mockup-like assets in this wave are reference evidence, not current UI authority by themselves

## Scope

- Target the honest `Open Beta` path unless every `1.0.0` P0 gate has redacted evidence.
- Keep public copy on `POKROV` and avoid direct public `VPN` product wording except legacy or technical contexts.
- Treat live Lava.top proof, runtime Telegram init-data smoke, RU-origin checks, and Android physical-device audit as evidence gates with explicit labels.
- For the current agent goal, checks that require owner hardware/accounts, provider dashboards, live deploy approval, signing identity, store access, or RU probe access are recorded as `MANUAL_OWNER_TEST`, `SKIPPED_BY_OWNER`, `OPERATOR_ATTESTED`, `NOT_REQUESTED`, or `BLOCKED_BY_ACCESS`; they do not block local docs/code synchronization.
- Do not upgrade accepted skips into stable, store, trusted-signing, RU-origin, or raw-device claims.

## Folder Map

- `00-orchestrator-context.md` — execution constraints and source-of-truth summary.
- `01-research-synthesis.md` — consolidated R01-R10 findings.
- `02-public-beta-prd.md` — selected public beta scope.
- `03-tech-debt-register.md` — release-relevant debt.
- `04-risk-register.md` — risk and mitigation tracker.
- `05-release-gate-plan.md` — gate matrix and commands.
- `06-performance-budget.md` — web, API, app, and infra budgets.
- `07-design-release-brief.md` — visual system and asset governance.
- `08-lavatop-payment-prd.md` — payment provider contract.
- `09-agent-iteration-ledger.md` — orchestration log.
- `10-internal-commit-ledger.md` — local change ledger.
- `11-fix-cycle-ledger.md` — fix and review loop ledger.
- `12-file-locks.md` — file ownership during parallel work.
- `13-launch-decision.md` — final decision statement.
- `14-final-git-promotion-record.md` — promotion and handoff record.
- `15-beta-ready-backlog.md` — category backlog, manual gates, beta-ready/non-production split.
- `research/` — R01-R10 research outputs.
- `work-orders/` — WO-001 through WO-010 implementation orders.
- `evidence/` — redacted supporting logs and reports.
