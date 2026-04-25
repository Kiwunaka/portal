# Research Synthesis

Status: research complete, synthesis created from written R01-R10 artifacts only.

## Executive Summary

POKROV is not paid-beta-ready yet. The research wave confirms a usable product direction, but the current candidate still has P0 blockers in paid checkout safety, provider verification, public copy truthfulness, cabinet continuation, admin operator coverage, client artifact readiness, live deployment evidence, and release gate freshness.

The safest cut line is a paid, invite-limited beta for at most 25 users only after the P0 items below are fixed or explicitly accepted as beta-only limitations. Android can remain internal APK only; Windows can remain unsigned only if the cabinet download warning is explicit and access-gated. Public Android/store and stable production claims remain blocked.

## Confirmed Beta Blockers

| Blocker | Area | Evidence | Owner WO | Severity |
|---|---|---|---|---|
| No payment provider is ready for paid beta until category acceptance and signed webhook behavior are confirmed or accepted as manual risk. | payments | `research/R07-payments-telegram-support.md`, `research/R10-qa-release-docs.md` | WO-006 | P0 |
| Paid fulfillment must create exactly one entitlement; duplicate, failed, cancelled, refunded, or unknown provider events need safe state handling and admin visibility. | payments/backend/admin | `research/R07-payments-telegram-support.md` | WO-006, WO-005, WO-004 | P0 |
| Current payment flow appears to activate access directly, while the paid beta policy prefers verified webhook to activation key or direct extension with explicit audit trail. Refund callbacks do not yet adjust access. | payments | `research/R07-payments-telegram-support.md` | WO-006 | P0 |
| Marketing contains unsafe public claims: Android public release labeling, `AES-256 / WireGuard` hero copy, 24/7 support wording, and hardcoded review JSON-LD provenance risk. | marketing/copy | `research/R02-design-system.md`, `research/R03-marketing-checkout.md` | WO-002, WO-001 | P0 |
| Android public release remains blocked by signing, handoff, runtime verification, and physical-device localhost/control-surface audit. | client/security | `research/R01-product-scope.md`, `research/R08-client-android-windows.md`, `research/R09-infra-observability-security.md`, `research/R10-qa-release-docs.md` | WO-007, WO-009, WO-010 | P0 for public; accepted limitation possible for internal APK |
| Windows public release remains blocked by unsigned seed-lane artifact, missing trusted signing, and incomplete public handoff. | client/release | `research/R08-client-android-windows.md` | WO-007, WO-010 | P0 for public; accepted limitation possible for gated beta |
| Client beta UX/contract has gaps: seed/dev version labels, no clear first-run beta lane, selected-apps MVP incomplete, checkout/support handoffs weak, and client still sends `trial_days`. | client/backend contract | `research/R08-client-android-windows.md` | WO-007, WO-005 | P0/P1 |
| Cabinet is not complete as a continuation-first paid beta surface: `/settings/` missing, `/statistics/` compatibility redirect weak, subscription checkout leaks internal/English copy, payment history absent, Telegram bonus not actionable. | webapp | `research/R04-webapp-cabinet.md` | WO-003 | P0 |
| Admin is not yet the complete operator surface for paid beta: no payment/order ledger, plan/promo management missing, device support not first-class, incidents/SLA incomplete, live access unverified. | admin | `research/R05-admin-console.md` | WO-004 | P0 |
| Backend live Postgres, migration, and control-panel/profile delivery evidence is missing; trial abuse and incomplete device management remain open risks. | backend/data | `research/R06-backend-api-data.md` | WO-005 | P0/P1 |
| Full release gate evidence is stale and not tied to the active client lane; payment callback/idempotency tests are not fully represented in the default gate. | QA/release | `research/R10-qa-release-docs.md` | WO-010 | P0 |
| Live production-domain deploy evidence is incomplete: current-origin, brain-origin, RU-origin, metrics freshness, backup/restore, and rollback proof are missing or blocked by access. | infra/ops | `research/R09-infra-observability-security.md`, `research/R10-qa-release-docs.md` | WO-008, WO-010 | P0/P1 |
| User/admin surfaces risk exposing sensitive details: activation key in URL flow, admin subscription URL/token, support upload static URLs, raw network rollout JSON, and screenshots/logs needing redaction. | security/privacy | `research/R03-marketing-checkout.md`, `research/R05-admin-console.md`, `research/R06-backend-api-data.md`, `research/R09-infra-observability-security.md` | WO-003, WO-004, WO-005, WO-009 | P0/P1 |

## Product Contradictions

- Public brand is POKROV, but older docs/copy still reference `POKROV VPN` as live meaning instead of legacy compatibility.
- Trial is canonical 5 days, but R01 found a stale 7-day `/gift trial` path in bot/operator context.
- Android public availability appears in marketing while canonical docs say Android public release is blocked until signing, handoff, runtime verification, and physical audit pass.
- Support copy implies guaranteed 24/7 availability in marketing, while paid beta policy allows only best-effort 24h response.
- Email/account continuation and Apple platforms must remain readiness-only or coming soon, not public promises.
- Route story must remain `All except RU` and `Full tunnel`; public `Blocked only` and RU/DNS/leak confidence are deferred until gates pass.

## Design Contradictions

- Attached references point to a light, mint/emerald, Russian-first premium utility surface; current surfaces still show violet/dark legacy styling in places.
- Logo references include `Premium VPN`, which may be retained as legacy asset evidence but must not ship as public semantic copy.
- Marketing exposes technical protocol/security badges that conflict with public copy rules.
- Cabinet checkout and client shell contain English/dev labels and seed-era visual language.
- Admin can use dense cards/tables, but every metric/module must be real, backend-empty, unavailable, or clearly outside beta gates.

## Backend/API Gaps

- Provider-agnostic payment event model needs explicit states, idempotency keys, signature status, raw-event hash, and admin-visible records.
- Refund/cancel/manual-review behavior needs entitlement policy.
- Live Postgres migrations and rollback evidence are missing.
- Managed profile delivery and node pool rules need fresh smoke against the active backend and client lane.
- Trial issuance needs stronger abuse controls around fresh `install_id` cycles.
- Device management is not complete enough for strong revoke/reset/device-count promises.
- Support uploads and diagnostic payloads need privacy-safe access, retention, and redaction policy.

## Client Gaps

- Android: debug/internal lane only until trusted signing and physical localhost/control-surface audit pass.
- Windows: unsigned gated beta artifact may be acceptable, but must show explicit SmartScreen/unknown-publisher warning.
- Handoff JSON and public artifact URLs are not production-ready.
- Client version labels and artifact names still read as seed/dev instead of beta.
- First-run beta UX lacks complete Try free, redeem, checkout handoff, route-mode selection, and support flow.
- Selected apps MVP is incomplete and should not be promoted unless W07 closes it.

## Security/Privacy Gaps

- Live evidence must be redacted; screenshots cannot show emails, Telegram IDs, payment IDs, private subscription links, or full identifiers unless protected internally.
- Payment logs must not print secrets, full webhook payloads, card data, or provider tokens.
- Admin-only details such as subscription URLs, rollout config, and sensitive user identifiers need stricter UI separation.
- Support uploads appear risky if static URLs remain bearerless after upload.
- Broad API rate limits, session revocation, CORS/CSRF/session posture, and Telegram/payment signature verification need final audit coverage.

## Ops/Release Gaps

- Dirty baseline is captured, but work agents must still distinguish baseline dirty files from their own changes.
- Promotion safety is not yet executed: local HEAD, remote HEAD, behind-origin state, and exact dirty patch state must be recorded before push/deploy.
- Release gates need a fresh run against current dirty candidate and active `POKROV-app/main` lane.
- Backup, migration, rollback, emergency switches, and low-volume payment/webhook checks must be verified before onboarding paid beta users.
- Live node metrics, current-origin, brain-origin, and RU-origin evidence are not sufficient for a paid beta deploy decision.

## Docs Gaps

- Product docs must explicitly separate paid beta, public release, and production cutover.
- Client cutover docs must keep Android public/store and Windows public approval blocked until signing, handoff, runtime verification, and audit evidence exist.
- User guide needs paid beta onboarding, artifact warnings, support path, bug-report content, and refund/manual reconciliation wording.
- Admin/operator docs need emergency controls, manual reconciliation, payment ledger, artifact disablement, and rollback instructions.
- Release docs need the final go/no-go table and accepted limitations.

## Recommended Beta Cut Line

Do not mark beta-ready yet. Proceed to work wave with W01, W05, and W09 first, then W02, W03, W04, W06, W07, and W08, and reserve W10 as the paid beta release captain.

Acceptable paid beta target after P0 closure:

- Invite-limited production-domain beta, max 25 active users.
- Live low-volume checkout only after provider acceptance/webhook verification or documented manual-risk acceptance.
- Cabinet-gated Android internal APK and Windows unsigned artifact with explicit warnings.
- Admin can inspect and manually reconcile users, payments, access, devices, tickets, downloads, and emergency switches.
- No public stable, store, production SLA, Apple, or guaranteed availability claims.
- All release gate failures classified, with rollback and support instructions ready before onboarding.
