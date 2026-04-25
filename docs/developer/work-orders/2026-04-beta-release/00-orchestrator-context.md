# Orchestrator Context

## Mission

Drive POKROV to a paid, invite-limited beta release candidate on production domains.

This wave does not claim stable production or public app-store cutover. It creates the research evidence, work orders, gates, and release-captain handoff needed to decide one of:

- beta-ready
- beta-ready with accepted limitations
- blocked

## Canonical Truth

- Platform lane: `portal/master`, normally `origin/master`.
- Platform integration branch for this wave: `codex/beta-release-platform`.
- Client lane: `POKROV-app/main`.
- Client integration branch for this wave: `codex/beta-release-client`.
- Active client checkout: `C:/Users/kiwun/Documents/ai/POKROV-app`.
- Archives and bridge material are retained evidence only.
- Production data truth is Postgres from `DATABASE_URL`.
- Shared public facts and copy live in `shared/*` and `copy/catalog.ru.json`.

## Product Guardrails

- Brand is `POKROV`.
- `POKROV VPN` is legacy compatibility only.
- Public direct-meaning `VPN` wording is forbidden.
- Paid beta scope is Android and Windows.
- iOS and macOS are readiness-only.
- Trial is 5 days.
- Telegram reward is +10 days.
- App-first identity and key-first purchase/redeem are the primary model.
- User UI must not expose raw hostnames, ports, raw configs, protocol labels, public IP, local control surfaces, or personal subscription links.
- Recommended public routing story is `All except RU` and `Full tunnel`.

## Dirty Baseline Capture

No pre-research resync is allowed.

Baseline evidence files were captured before research dispatch:

Platform:

- `evidence/logs/platform-git-status-before.txt`
- `evidence/logs/platform-git-diff-before.patch`
- `evidence/logs/platform-git-diff-stat-before.txt`
- `evidence/logs/platform-untracked-before.txt`
- `evidence/logs/platform-git-log-before.txt`
- `evidence/logs/platform-current-branch-before.txt`
- `evidence/logs/platform-local-head-before.txt`
- `evidence/logs/platform-origin-master-head-before.txt`

Client:

- `evidence/logs/client-git-status-before.txt`
- `evidence/logs/client-git-diff-before.patch`
- `evidence/logs/client-git-diff-stat-before.txt`
- `evidence/logs/client-untracked-before.txt`
- `evidence/logs/client-git-log-before.txt`
- `evidence/logs/client-current-branch-before.txt`
- `evidence/logs/client-local-head-before.txt`
- `evidence/logs/client-origin-main-head-before.txt`

Rules:

- Do not revert user or previous-agent changes.
- Do not delete untracked release artifacts.
- Do not assume dirty files are disposable.
- Work agents must distinguish baseline dirty changes from their own changes.
- If a file was dirty before the wave, the agent must record why it touched it.
- Do not overwrite baseline dirty work without orchestrator approval.

## Live Checks Policy

- Live production-domain checks are read-only unless the WO explicitly authorizes a low-volume write test.
- Payment live tests must use a controlled beta account and minimal real or sandbox amount where supported.
- All live evidence must be redacted.
- Do not print secrets, tokens, private webhook payloads, personal payment data, raw subscription links, private IPs, or full user identifiers.
- Screenshots must hide emails, Telegram IDs, payment IDs, and personal connection links unless stored in protected internal evidence.

## Promotion Safety

- Before push or deploy, capture current local HEAD and remote HEAD.
- If the platform branch is behind `origin/master`, do not force-push or overwrite remote changes.
- If the client branch is behind `origin/main`, do not force-push or overwrite remote changes.
- Orchestrator must decide merge, rebase, or cherry-pick strategy after gates.
- Deploy may use a local dirty beta candidate only if the exact commit and patch state is captured and rollback is documented.

## Known Starting Facts

- The previous `docs/developer/work-orders/2026-04-22--pokrov-global-rework/` wave is closed and should be referenced as prior evidence, not reused.
- `shared/redesign-spine.json` is absent in the current platform repo.
- `tests/test_redesign_spine.py` is absent in the current platform repo.
- Design refs exist under `PРИМЕРЫ ДИЗАЙНА ПРИЛОЖЕНИЯ И ЛК/` and attached screenshot files in the repository root.
- Root and client repos were behind their remotes at baseline; see baseline evidence files.
- Any untracked files that appeared after baseline capture must be classified before cleanup. Do not delete or overwrite them without orchestrator approval.
