# Repository Agent Contract

## Scope And Lanes

This is the universal Codex contract for the POKROV platform repository. The platform lane owns `portal_bot/`, `webapp/`, `adminapp/`, `marketing/`, `shared/`, `infra/`, `scripts/`, tests, and root documentation.

The Android and Windows client is a separate repository at `C:/Users/kiwun/Documents/ai/POKROV-app`; its promotion line is `POKROV-app/main`. Do not treat retained bridge, bootstrap, or client archive material in this repository as an active client lane.

Root `AGENTS.md` is the only tracked platform instruction file. Put scoped navigation in the task router instead of adding nested instruction files.

## Start Here

1. Follow instruction precedence: system and developer instructions, then the user's request, then this repository contract and scoped process documentation.
2. Inspect `git status --short --branch` and the relevant `git diff` before touching files. Preserve unrelated and concurrent work.
3. Classify the task, then open one matching row in the [task router](docs/developer/agent-context-map.md). Expand context only when that row or current evidence requires it.
4. Use the [classified documentation registry](docs/README.md) when the route names a document family or when current and historical material need separation.
5. If a missing decision would materially change the result, return `NEEDS_CONTEXT` before making speculative changes.

## Authority And Current Truth

Use the authority ladder for the question being answered. Canonical owner documents define intended behavior; current code and tests show implemented behavior; exact runtime evidence shows observed state. Work orders and history explain execution or prior decisions but do not silently override current owners.

External model output is advisory. Send only redacted, task-bounded context, never secrets or raw customer/provider data, and reconcile suggestions against repository authority before use.

Legacy paths and identifiers may remain for compatibility. Their names do not make archived or superseded content current.

## Universal Safety

- Integrity and safety checks are authorized only for the local POKROV repositories, owned runtime surfaces, and isolated fixtures named by the task. They are defensive validation; third-party systems, accounts, credentials, and data are out of scope.
- Never print, commit, move, copy into artifacts, or expose secrets, tokens, credentials, private keys, raw connection material, customer data, or unredacted provider payloads.
- Do not perform broad deletion, destructive Git operations, database resets, account deletion, production mutation, deploy, payment action, or external communication unless the task explicitly authorizes it and the required guard is satisfied.
- Preserve evidence, audit artifacts, archive history, rollback material, and generated provenance. Relabel unclear history; do not erase it during routine cleanup.
- Treat dirty files and other worktrees as concurrent work. Do not overwrite, revert, stage, or reformat changes outside the assigned scope.
- Keep cleanup targeted, reviewable, and reversible. Never use an automated cleanup `--apply` mode for repository-context work.

## Release And Evidence Honesty

Tie every release or readiness statement to the exact candidate, environment, origin, and retained evidence. A local pass is not production proof, and an older candidate does not prove the current one.

Use explicit labels such as `PASS`, `MANUAL_OWNER_TEST`, `OPERATOR_ATTESTED`, `SKIPPED_BY_OWNER`, `SKIPPED_BY_OPERATOR`, `BLOCKED_BY_ACCESS`, and `NOT_REQUESTED`. Never convert a skip, attestation, missing artifact, or inaccessible system into a pass.

Do not claim stable release status, store availability, trusted signing, physical-device proof, RU-origin readiness, payment maturity, provider readiness, or successful deploy without current evidence for that exact claim. Manual device, account, provider-dashboard, signing, store, and external-origin checks remain manual until executed and retained.

Keep `current-origin`, `brain-origin`, and `RU-origin` checks distinct in evidence and handoffs.

## Git, Worktrees, And Cleanup

The platform promotes through `master`; the separate client promotes through `main`. Use a scoped feature branch or worktree for implementation and keep the platform/client boundary intact.

Before and after work, inspect `git status`, `git diff --stat`, and the scoped `git diff`. Stage only authorized files. Do not use `git reset --hard`, destructive checkout, or blanket restore to clean a dirty tree.

Do not enter or modify a neighboring worktree unless it is explicitly in scope. Confirm resolved paths before recursive moves or deletion, and retain rollback evidence for any authorized cleanup.

## Documentation Impact

When behavior changes, update its canonical owner in the same task. Use the router's `Docs impact` cell to find that owner; do not duplicate product truth into this root contract.

Platform behavior belongs in root canonical documentation. Active client behavior and client release truth belong in `POKROV-app/docs/`; root docs may point to that truth but must not replace it. Evidence and historical records should be appended or reclassified, not rewritten to manufacture current authority.

Do not change docs-assistant or support knowledge-base allowlists as a side effect of context, documentation, or cleanup work.

## Verification And Handoff

Run the smallest focused checks that prove the change, then relevant regression checks. For context/docs work, include link/contract checks and `git diff --check`; for code, use the subsystem commands in the router.

Self-review the final diff for scope, secrets, destructive behavior, release claims, documentation impact, and retained evidence. Recheck `git status` and `git diff` before staging or handoff.

The handoff must state what changed, exact commands and results, manual or blocked checks, remaining concerns, and commit/deploy state. Keep it compact and never imply that an unrun check, push, deploy, or owner action happened.
