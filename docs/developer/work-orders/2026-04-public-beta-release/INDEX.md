# POKROV Public Beta Release Wave

Status: live-gates-partially-closed-release-blocked

Created: 2026-04-25
Release type: public beta
Audience: all users
Platform lane: portal/master
Client lane: POKROV-app/main
Platform worktree: C:/Users/kiwun/.config/superpowers/worktrees/VPN/public-beta-release-wave
Platform branch: codex/public-beta-release-wave

## Public Beta Goal

Prepare an open public beta release for POKROV on production domains, with truthful public copy, safe checkout/entitlement behavior, real cabinet/support/admin surfaces, release-aware client artifact states, monitoring, rollback, emergency controls, and a written go/no-go decision.

This wave upgrades the previous invite/paid beta candidate into a public beta decision framework. Public beta is stricter: no invite cap, no fake public availability, no fake admin modules, no fake support, no unsafe payment fulfillment, and no Android/Windows public claim without matching release evidence.

## Public Beta Non-Goals

- Production-stable or SLA-backed launch.
- Public Apple availability.
- Android public release without production signing and physical release-build localhost/control-surface audit.
- Windows stable claim while unsigned.
- Raw subscription-link-first UX.
- Public `VPN` wording as the direct product description.

## Current Blockers

| Blocker | Area | Status | Evidence | Owner |
|---|---|---|---|---|
| Root platform worktree inherits a large dirty candidate from the prior beta wave. | git/promote | open | `evidence/logs/platform/platform-git-status-before.txt` | W10 |
| Platform local base is behind `origin/master`; promotion strategy is not decided. | git/promote | open | `evidence/logs/platform/platform-local-head-before.txt`, `evidence/logs/platform/platform-origin-master-head-before.txt` | W10 |
| Payment provider acceptance blocks live paid checkout. Server-side FreeKassa path is reachable, but provider returns `Merchant not activated`. | payments | provider-blocked | `docs/audit-artifacts/payment_provider_probe_2026-04-26.md` | W06 |
| Android public release remains blocked until production signing plus physical-device release audit pass. | client | blocked-no-device | `docs/audit-artifacts/android_physical_audit_2026-04-26.md` | W07 |
| Windows public artifact exists as beta/unsigned; trusted signing and final public handoff are still not approved. | client | artifact-pass-risk-open | `docs/audit-artifacts/client_platform_builds_2026-04-26.md` | W07 |
| Live deploy, backup, rollback, and final promotion are not yet proven; brain-origin is now green, RU-origin is partial with Telegram unreachable from `mini`. | ops | partial | `docs/audit-artifacts/public_beta_release_gate_report_brain.md`, `docs/audit-artifacts/ru_probe_2026-04-26.md` | W08 |

## Emergency Controls Status

| Control | Owner | Implemented | Verified | Evidence |
|---|---|---:|---:|---|
| Disable checkout | W06/W04 | unknown | no | pending |
| Pause webhook fulfillment | W06/W04 | unknown | no | pending |
| Route unknown payments to manual_review | W06 | unknown | no | pending |
| Disable trial issuance | W05/W04 | unknown | no | pending |
| Disable Telegram bonus | W06/W04 | unknown | no | pending |
| Disable Android downloads | W03/W04/W07 | unknown | no | pending |
| Disable Windows downloads | W03/W04/W07 | unknown | no | pending |
| Disable all beta downloads | W03/W04 | unknown | no | pending |
| Maintenance banner/state | W02/W03/W04 | unknown | no | pending |
| Pause managed profile issuance | W05/W08 | unknown | no | pending |
| Pause node/location | W08/W04 | unknown | no | pending |
| Pause activation-key redemption | W05/W06 | unknown | no | pending |
| Manual access extend/revoke | W04/W06 | unknown | no | pending |
| Manual payment reconcile | W04/W06 | unknown | no | pending |
| Broadcast incident/update | W04/W10 | unknown | no | pending |

## Research Agents

| Agent | Model | Scope | Status | Output | Blockers |
|---|---|---|---|---|---|
| R01 | gpt-5.5 high | Product scope, public beta definition, canonical docs | complete | `research/R01-product-public-beta-scope.md` | Android/payment/live/operator blockers |
| R02 | gpt-5.5 high | Design system, brand, visual audit | complete | `research/R02-design-system-brand-visual-audit.md` | mojibake, fake timer, visual evidence |
| R03 | gpt-5.5 high | Marketing, checkout, install, legal | complete | `research/R03-marketing-checkout-install-legal.md` | stale paid/invite copy, checkout noindex |
| R04 | gpt-5.5 high | User cabinet | complete | `research/R04-user-cabinet.md` | payment history unavailable, live flows |
| R05 | gpt-5.5 high | Admin console | complete | `research/R05-admin-console.md` | emergency controls, raw rollout JSON |
| R06 | gpt-5.5 high | Backend API, data model, migrations | complete | `research/R06-backend-api-data-migrations.md` | live Postgres, session/device model, OIDC throttling |
| R07 | gpt-5.5 high | Payments, keys, Telegram, support/feedback | complete | `research/R07-payments-keys-telegram-support.md` | provider proof, key-first mismatch, refund policy |
| R08 | gpt-5.5 high | Android/Windows client public beta readiness | complete | `research/R08-client-android-windows-public-beta.md` | Android blocked, handoff mismatch |
| R09 | gpt-5.5 high | Infra, observability, security/privacy | complete | `research/R09-infra-observability-security-privacy.md` | brain/RU origin, backup, metrics semantics |
| R10 | gpt-5.5 high | QA, release gates, docs, public launch ops | complete | `research/R10-qa-release-docs-public-launch.md` | stale gates, live/deploy blockers |

## Work Orders

| WO | Scope | Lane | Agent | Status | Validation | Risk |
|---|---|---|---|---|---|---|
| WO-001 | Design system, brand, public beta visual parity | platform | W01 | ready | copy/visual/build gates | public visual/copy drift |
| WO-002 | Marketing, public checkout, install, legal | platform | W02 | local partial complete | marketing build, SEO, copy guardrails | unsafe public claims |
| WO-003 | Public user cabinet | platform | W03 | local partial complete | webapp build/E2E, copy guardrails | fake continuation/download/support state |
| WO-004 | Public release admin console | platform | W04 | ready | admin smoke/E2E/API | fake operator modules |
| WO-005 | Backend contract hardening | platform | W05 | ready | backend/API tests | payment/session/profile bugs |
| WO-006 | Payments, keys, Telegram, support/feedback | platform | W06 | ready | payment/bot/ticket tests | unsafe entitlement fulfillment |
| WO-007 | Android/Windows public beta client | client | W07 | builds pass, release blocked | client tests/build/audit | Android physical audit, Windows unsigned posture |
| WO-008 | Infra, nodes, observability, deploy readiness | platform | W08 | origin partial | observer/node/deploy checks | RU Telegram reachability, rollback/deploy |
| WO-009 | Security, privacy, abuse, compliance audit | mixed | W09 | local partial complete | security/copy/payment/auth checks | data/secret leaks |
| WO-010 | Public beta release captain | mixed | W10 | local gate report complete | release gate/signoff | false go decision |

## Release Gate Snapshot

The current-origin and brain-origin gate sets are green, client platform builds are available, and RU-origin evidence now exists. Public beta is still blocked because payment provider activation, Android physical release audit, runtime app-download token smoke, RU Telegram reachability, and final deploy/rollback/promotion proof are not green.

| Gate | Status | Evidence |
|---|---|---|
| current-origin check | PASS | `docs/audit-artifacts/public_beta_release_gate_report.md` |
| brain-origin check | PASS | `docs/audit-artifacts/public_beta_release_gate_report_brain.md` |
| RU-origin canonical hosts and delivery nodes | PASS | `docs/audit-artifacts/ru_probe_2026-04-26.md` |
| RU-origin Telegram reachability | FAIL | `docs/audit-artifacts/ru_probe_2026-04-26.md` |
| client platform builds | PASS_WITH_RELEASE_GATES_REMAINING | `docs/audit-artifacts/client_platform_builds_2026-04-26.md` |
| Android physical release audit | BLOCKED_NO_PHYSICAL_DEVICE | `docs/audit-artifacts/android_physical_audit_2026-04-26.md` |
| runtime app-download smoke | BLOCKED_NO_LIVE_TOKEN | `docs/audit-artifacts/runtime_app_download_smoke_2026-04-26.md` |
| payment provider live order creation | BLOCKED_BY_PROVIDER_STATUS | `docs/audit-artifacts/payment_provider_probe_2026-04-26.md` |

## Decision Log

- 2026-04-25: Started public beta wave from `POKROV_public_beta_release_monster_plan_v3_agent_iterations_internal_commits.md`.
- 2026-04-25: Previous dirty paid/invite beta candidate was mirrored into an isolated `codex/public-beta-release-wave` worktree instead of continuing directly on root `master`.
- 2026-04-25: R01-R10 public-beta research completed; synthesis recommends keeping public beta `blocked` until P0 live/manual/artifact gates close or scope is narrowed.
- 2026-04-25: Applied local public-beta-safe surface deltas: removed stale paid/invite beta copy, made checkout indexable, replaced homepage fake connected timer, hardened downloads warning copy, and added guardrails for those regressions.
- 2026-04-25: Replaced wildcard credentialed API CORS with an explicit production/dev allowlist and added backend coverage for allowed versus blocked origins.
- 2026-04-25: Ran default `release_gate_check.py`; local current-origin gate set passed and produced `docs/audit-artifacts/public_beta_release_gate_report.md`, while brain-origin, RU-origin, Android physical audit, runtime app-download smoke, and client platform builds remain blocked/skipped/not requested.
- 2026-04-26: Fixed worktree node-access key lookup and ran brain-origin quick release gates against `82.21.114.104`; brain-origin passed.
- 2026-04-26: Ran RU-origin probe from `mini`; canonical POKROV hosts and foreign delivery nodes are reachable, while Telegram targets are unreachable and classified as `telegram_reachability_problem`.
- 2026-04-26: Built Windows beta zip/manifest, Android release APK, and Android release AAB from `POKROV-app`; Android public release remains blocked by the physical-device audit.
- 2026-04-26: Ran FreeKassa live API probe from brain for both `site` and `bot`; provider path is reachable but FreeKassa returns `Merchant not activated`.
- 2026-04-26: Added `14-master-main-promotion-plan.md`; promotion to `master`/`main` remains blocked until external release gates close and inherited dirty work is reviewed.

## Current Decision

`blocked`: current-origin and brain-origin gates are green, RU-origin and client build evidence exists, but public beta is not launch-ready until FreeKassa merchant activation/live checkout proof, Android physical release-build audit, runtime app-download token smoke, RU Telegram reachability or accepted fallback, and deploy/rollback/promotion proof are complete.
