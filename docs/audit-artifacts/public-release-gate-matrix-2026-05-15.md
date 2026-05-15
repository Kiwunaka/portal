# Public Release Gate Matrix

Date: 2026-05-15

Verdict: `COMPLETE_PUBLIC_RELEASE_GO`

Scope: POKROV public beta for Android APK and Windows EXE outside app stores. Secrets, private emails, Telegram initData, callback payloads, payment identifiers, subscription URLs, and access keys are intentionally redacted or omitted.

| # | Gate | Status | Evidence / command | Notes / next action |
| --- | --- | --- | --- | --- |
| 1 | Root git baseline | PASS | `git status --short`, latest `master` history | Dirty changes are current release work plus untracked owner `GOAL.md`. |
| 2 | Client git baseline | PASS | `C:/Users/kiwun/Documents/ai/POKROV-app`, `main` | Client repo remained on the active promotion line. |
| 3 | Current-origin quick gate | PASS | `docs/audit-artifacts/release-gate-local-quick-2026-05-15.md` | Quick release gate passed after cabinet routing fix. |
| 4 | Current-origin full gate equivalent | PASS | `docs/audit-artifacts/release-gate-full-local-2026-05-15.md` | Manual equivalent used because the monolithic wrapper timed out without a failing sub-gate. |
| 5 | Release pytest matrix | PASS | `python -m pytest ...`, recorded in full gate artifact | Release-critical backend/tooling matrix passed. |
| 6 | Admin/auth regressions | PASS | `tests/test_api_auth_and_tickets.py` | Auth, tickets, and admin regressions passed. |
| 7 | Payment callback regressions | PASS | `tests/test_api_payments_callbacks.py`, `tests/test_lavatop_payment_providers.py` | Lava callback auth, replay, and fulfillment behavior covered. |
| 8 | Payment and marketing honesty | PASS | `tests/test_bot_paywall.py`, `tests/test_marketing_release_readiness.py` | Public claims remain beta-scoped and Lava-only. |
| 9 | Probe redaction | PASS | `tests/test_live_probe_scripts.py`, `tests/test_brain_payment_email_readiness.py` | Probe outputs redact target emails, tokens, access keys, and response bodies. |
| 10 | Legacy provider guard | PASS | `tests/test_freekassa_api_probe.py`, `tests/test_freekassa_staging_smoke.py` | Legacy FreeKassa route stays blocked unless explicitly run as reconciliation. |
| 11 | GitHub release tooling | PASS | `tests/test_prepare_github_release_plan.py`, `tests/test_publish_github_release_assets.py` | Tooling validates release asset planning and publishing behavior. |
| 12 | Launch decision tooling | PASS | `tests/test_public_beta_external_access_preflight.py`, `tests/test_public_beta_launch_decision.py` | Machine decision tooling remains covered. |
| 13 | WebApp build | PASS | `npm.cmd run build` in `webapp/` | Re-run before deploy after final doc/status edits. |
| 14 | WebApp E2E | PASS | `npm.cmd run test:e2e` / focused cabinet routing E2E | Native Next.js cabinet navigation no longer hard reloads by default. |
| 15 | Marketing build | PASS | `npm.cmd run build` in `marketing/` | Static install/public pages are buildable. |
| 16 | Public link reachability | PASS | `docs/audit-artifacts/staged-client-apps-reachability-2026-05-15.md` | APK, EXE, and install page returned reachable responses. |
| 17 | UI visual smoke | PASS | `docs/audit-artifacts/release-gate-local-quick-2026-05-15.md` | Visual gate was sufficient for beta; design polish remains follow-up work. |
| 18 | Admin release cockpit | PASS | `webapp/public/release-status.json` from launch decision; `docs/audit-artifacts/brain-static-public-smoke-2026-05-15.md` | Cockpit now consumes dated GO evidence and deployed `release-status.json` returns HTTP 200. |
| 19 | Client preflight | PASS | `docs/audit-artifacts/release-gate-full-local-2026-05-15.md` | Active client preflight passed. |
| 20 | Client full tests | PASS | `docs/audit-artifacts/release-gate-full-local-2026-05-15.md` | Flutter and Android Gradle suites passed in the recorded full gate. |
| 21 | Client security smoke | PASS | `docs/audit-artifacts/release-gate-full-local-2026-05-15.md` | Security smoke included in the client release pass. |
| 22 | Android APK artifact | PASS | `docs/audit-artifacts/staged-client-apps-2026-05-15.json` | GitHub Release APK is reachable; no store claim. |
| 23 | Windows EXE artifact | PASS | `docs/audit-artifacts/staged-client-apps-2026-05-15.json` | GitHub Release EXE is reachable; unsigned warning remains public limitation. |
| 24 | Install docs reachability | PASS | `docs/audit-artifacts/staged-client-apps-reachability-2026-05-15.md` | `https://pokrov.space/install/` reachable. |
| 25 | Runtime app-download smoke | PASS | `docs/audit-artifacts/brain-runtime-app-download-smoke-2026-05-15.json` | Env-only Telegram initData generated on brain; raw initData omitted. |
| 26 | Brain verify | PASS | `docs/audit-artifacts/release-gate-brain-2026-05-15.md`; `docs/audit-artifacts/brain-static-public-smoke-2026-05-15.md` | Brain services, health, static HTML, deployed public surfaces, and subscription fetches verified. |
| 27 | Node predeploy readiness | PASS | `docs/audit-artifacts/node-predeploy-readiness-2026-05-15.json` | JSON reports `ok=true`; transient SSH banner warnings are not release blockers. |
| 28 | Live email status | PASS | `docs/audit-artifacts/live-email-auth-status-brain-2026-05-15.json` | Public email auth enabled, delivery configured, debug echo off. |
| 29 | Live payment provider status | PASS | `docs/audit-artifacts/live-payment-provider-status-brain-2026-05-15.json` | Lava.top is enabled and unblocked; no alternate public provider. |
| 30 | Email delivery probes | PASS | `docs/audit-artifacts/brain-post-deploy-live-probe-2026-05-15.json` | Verify, reset, and paid access-key delivery returned success with payloads redacted. |
| 31 | Lava invoice creation | PASS | `docs/audit-artifacts/brain-post-deploy-live-probe-2026-05-15.json` | Live invoice creation returned success with response body redacted. |
| 32 | Paid checkout aggregate | PASS | `docs/audit-artifacts/paid-checkout-launch-evidence-brain-2026-05-15.json` | Safe to keep Lava-only beta checkout enabled. |
| 33 | Public beta post-deploy probe | PASS | `docs/audit-artifacts/public-beta-post-deploy-probe-2026-05-15.json` | Email public mode and paid checkout aggregate are green. |
| 34 | Owner email confirmation | PASS | owner runtime report, 2026-05-15 | User confirmed email registration and verification arrived. No private email committed. |
| 35 | Owner Lava payment confirmation | PASS | owner runtime report, 2026-05-15 | User confirmed live Lava payment succeeded and access was credited. No payment id committed. |
| 36 | Android physical audit | OPERATOR_ATTESTED | owner attestation, 2026-05-15 | Accepted for this beta; do not claim raw repo physical-device validation. |
| 37 | Windows signing | PASS_WITH_LIMITATION | owner instruction, 2026-05-15 | Signatures not required; public copy must disclose unsigned beta warning. |
| 38 | RU-origin | SKIPPED_BY_OPERATOR | `docs/audit-artifacts/ru-origin-skip-accepted-2026-05-15.md` | Do not claim RU-origin Telegram availability. |
| 39 | External access preflight | PASS_WITH_ACCEPTED_SKIPS | `docs/audit-artifacts/public-beta-external-access-preflight-2026-05-15.json` | Accepted skips are Windows signing and RU-origin. |
| 40 | Release handoff policy | PASS | `docs/audit-artifacts/public-beta-handoff-2026-05-15.md` | Telegram announcement is prepared-only, not posted by automation. |
| 41 | Machine launch decision | PASS_WITH_ACCEPTED_SKIPS | `docs/audit-artifacts/public-beta-launch-decision-2026-05-15.json` | Public beta GO with exact safe and unsafe claims. |

Safe public claims are limited to the machine-readable launch decision. Anything outside that artifact requires a new dated evidence pass.
