# Repository Agents

This file documents the intended "agents" (roles) and the rules they must follow when changing anything under this directory.

## Global Rules

- Never commit or paste secrets (tokens, passwords, server IPs tied to auth) into the repo.
- All credentials must be provided via environment variables and/or secret managers on the target server.
- Any public-facing copy must not mention the word "VPN" unless explicitly required.
- Prefer backward-compatible changes where possible (fallback to legacy single-node behavior if `nodes` table is empty).
- For node operations, `PORTAL` DB is the source of truth; `3x-ui` must be treated as a node-local execution layer, not the authoritative inventory.
- RUB payments are now provider-agnostic: `PORTAL` chooses from enabled providers via env-driven catalog, with `Stars` as the built-in Telegram path.
- Payment-provider research or onboarding is allowed when explicitly requested by the owner or when replacing a failing active cashier.
- For release work, default completion includes `push + deploy`; if this is blocked, document the blocker and rollback-safe state in docs.
- After backend/frontend/infrastructure changes, a scope-appropriate smoke check is mandatory:
  - backend: health + subscription + checkout + ticket endpoints;
  - webapp/marketing: build + key routes + current Telegram links;
  - ops: systemd service/timer status + metrics freshness.

## Agents

### backend-infra
Scope:
- `portal_bot/`
- `scripts/`
- `infra/`
- root deployment scripts

Responsibilities:
- Multi-node data model (`nodes`, `user_nodes`) and idempotent migrations
- 3x-ui panel integration per node
- Subscription endpoint returns all countries
- Node lifecycle via `PORTAL`: `drain -> resync -> disable`
- Security hardening: remove hardcoded secrets, least-privilege access patterns

### frontend-ui
Scope:
- `webapp/` (Telegram WebApp / LK)
- `marketing/` (sales site)

Responsibilities:
- Make LK fast, readable, and touch-friendly
- Add "Countries" UI and quick actions
- Implement kinetic typography on marketing site (primary visual language)
- Keep copy compliant: do not mention "VPN"

### marketing-copywriter
Scope:
- `marketing/`
- `webapp/`
- `portal_bot/`
- `docs/` (copy packs and campaign playbooks)

Responsibilities:
- Write conversion-focused copy for landing, checkout, bot, and WebApp
- Build soft-sell user journeys (welcome, T-3 renewal, retention/reactivation)
- Prepare promo/campaign text packs for deep links and channel posts
- Keep tone premium-friendly and claims realistic
- Keep public copy compliant: do not mention "VPN"

### docs
Scope:
- `docs/`
- `USER_GUIDE_RU.md`, `ADMIN_GUIDE.md` (if/when updated)

Responsibilities:
- Clear setup/ops docs
- Node bootstrap + migration playbook
- Incident/runbook docs

### payments-integration
Scope:
- `portal_bot/`
- `docs/`
- `scripts/`

Responsibilities:
- Maintain provider-agnostic RUB integration contracts (site/bot flows, callbacks, idempotency, allowlist / signature rules).
- Keep payment env matrix, callback URLs, provider priority/fallback order, and runbooks consistent with production.
- Ensure checkout ticket flow and metadata contracts stay backward-compatible.

### qa-regression
Scope:
- `tests/`
- `portal_bot/`
- `webapp/`

Responsibilities:
- Maintain fast smoke/regression checks for core user/admin flows
- Catch behavioral regressions after backend/frontend changes
- Keep test scenarios aligned with multi-node and free/paid routing logic

### release-ops
Scope:
- `scripts/`
- `infra/`
- root deployment scripts

Responsibilities:
- Safe deploy/rollback procedures for bot, API, and static apps
- Post-deploy sanity checks (services, endpoints, subscription health)
- Keep deployment steps idempotent and operator-friendly

### security-audit
Scope:
- whole repository

Responsibilities:
- Detect secret leaks, weak defaults, and unsafe operational patterns
- Enforce environment-only credential usage and least-privilege access
- Maintain practical hardening checklist before production changes

### support-automation
Scope:
- `portal_bot/`
- `webapp/`
- `docs/`

Responsibilities:
- Build and evolve support workflows (FAQ, ticket intake, operator replies)
- Keep support entrypoints configurable via env (no hardcoded usernames/tokens)
- Align bot and WebApp support UX with the same status/diagnostic data

### network-stealth
Scope:
- `scripts/`
- `infra/`
- `docs/`

Responsibilities:
- Node-level network checks (DNS leak, TLS/SNI consistency, country-fit defaults)
- Safe rollout scripts for routing/security hardening on worker nodes
- Maintain reproducible diagnostics and rollback instructions for network changes

### metrics-analytics
Scope:
- `portal_bot/`
- `scripts/`
- `webapp/`
- `docs/`

Responsibilities:
- Maintain daily aggregates for registrations, churn, revenue (RUB + Stars), node traffic and device counts.
- Keep `portal-node-metrics.timer` runbook current and ensure freshness checks are documented.
- Verify admin metrics DTO/API compatibility (`summary`, `metrics/status`, `metrics/timeseries`, `nodes/traffic`).
- Maintain smoke scenarios for admin analytics screens and post-deploy metric sanity.

## Reporting Format

For any substantial task, leave a short mini-log in docs or the handoff:
- `Что проверил`
- `Что нашёл`
- `Что изменил`
- `Как проверил`
- `Что осталось / риск`

## Cross References

- `docs/PROJECT_MAP_RU.md`
- `docs/ISSUES_REGISTRY.md`
- `docs/SMOKE_TEST_CHECKLIST_RU.md`
- `docs/PAYMENTS_FLOW_RU.md`
- `docs/BONUS_SYSTEM_RULES_RU.md`
- `docs/METRICS_RU.md`
- `docs/INFRA_PLAN_RU.md`
- `docs/NODE_LIFECYCLE_RU.md`
- `docs/FINAL_REPORT_RU.md`
