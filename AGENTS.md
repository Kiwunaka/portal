# Repository Agents

This file documents the intended "agents" (roles) and the rules they must follow when changing anything under this directory.

## Global Rules

- Never commit or paste secrets (tokens, passwords, server IPs tied to auth) into the repo.
- All credentials must be provided via environment variables and/or secret managers on the target server.
- Any public-facing copy must not mention the word "VPN" unless explicitly required.
- Prefer backward-compatible changes where possible (fallback to legacy single-node behavior if `nodes` table is empty).

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

### payments-research (optional)
Scope:
- `docs/`
- root planning notes (no code changes)

Responsibilities:
- Research payment flows where users pay via SBP/card and you receive crypto
- Record integration constraints: webhooks, metadata, anti-fraud/limits, KYC/legal requirements

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
