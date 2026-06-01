# Beta-Ready Backlog And Manual Gates

Status: active handoff
Date: 2026-05-26

This file is the category-level backlog for the current POKROV beta-ready state. It keeps the distinction between:

- what is already done for the outside-store public beta;
- what is beta-ready only;
- what must not be treated as production, `1.0.0`, store, trusted-signing, RU-origin, or raw-device proof;
- what remains a manual owner/operator check and should not block local agent docs/code work.

Primary evidence:

- `13-launch-decision.md`
- `docs/audit-artifacts/public-beta-launch-decision-2026-05-15.json`
- `webapp/public/release-status.json`
- root `AGENTS.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/cutover-readiness.md`

## Label Rules

| Label | Meaning |
| --- | --- |
| `PASS_FOR_BETA` | Good enough for the current outside-store public beta evidence pack. |
| `OPERATOR_ATTESTED` | Accepted owner/operator attestation; do not upgrade to raw proof. |
| `MANUAL_OWNER_TEST` | Requires physical device, real account, inbox, payment dashboard, or other owner-only resource. |
| `SKIPPED_BY_OPERATOR` / `SKIPPED_BY_OWNER` | Explicitly skipped for beta; do not claim the skipped capability. |
| `NOT_REQUESTED` | Out of selected beta scope. |
| `BLOCKED_BY_ACCESS` | Cannot be checked without external access; honest label, not an agent failure. |
| `PRODUCTION_FOLLOW_UP` | Required before stable, store, trusted, production, or `1.0.0` claims. |

## Category Backlog

| Category | Done / beta-ready | Not production proof | Remaining manual or follow-up |
| --- | --- | --- | --- |
| Release truth | Outside-store Android + Windows public beta is `GO` as of `2026-05-15`; root docs, launch notes, work-order gates, and client docs now say `GO with accepted skips`. | Not `1.0.0`, not app-store release, not broad stable launch. | Keep future release candidates tied to fresh exact-candidate evidence. |
| Payments | Lava.top-only paid checkout is `PASS_FOR_BETA`; provider catalog, invoice, callback, replay/idempotency, failed/manual-review, reconciliation, and email-key evidence are retained. | Not production payment maturity. Refund/chargeback and ongoing reconciliation are not fully proven as an automated production system. | `PRODUCTION_FOLLOW_UP`: refund, chargeback, provider-change, reconciliation drills, dashboard review. |
| Downloads / handoff | `/api/client/apps` runtime smoke and GitHub APK/EXE reachability are beta-green; marketing/cabinet copy now treats links as beta assets. | Does not prove future URLs or artifacts. Does not prove real-user Telegram WebApp opening. | Re-run runtime smoke before changing `APP_*`, GitHub tag, docs URL, or release candidate. Real-user Telegram opening is `MANUAL_OWNER_TEST`. |
| Android | Outside-store APK beta may rely on `OPERATOR_ATTESTED` physical audit. Package target is `space.pokrov.pokrov_android_shell`. | Not raw repo PASS, not Play release, not store-safe or stable Android proof. | Raw physical-device audit with retained redacted output is `MANUAL_OWNER_TEST`; production signing/store access is `NOT_REQUESTED` for beta. |
| Windows | Unsigned EXE beta risk is accepted; warning copy is required and docs/admin/copy do not claim trusted signing. | Not trusted-signed, not Microsoft Store-ready. | Trusted signing, SmartScreen reputation, MSIX/store path are `PRODUCTION_FOLLOW_UP`. |
| Webapp / admin | `/admin/release` now reflects beta GO with manual gates, not stale NO-GO; admin route map includes `/admin/payments` and `/admin/release`; checkout fallback copy no longer says launch proof is pending. | Admin UI is not a substitute for payment dashboard, raw Android audit, RU-origin probe, or live deploy approval. | Broaden admin E2E/visual coverage for payments, release, mobile admin ergonomics. |
| Cabinet user copy | Manual subscription fallback now frames compatible clients as recovery only; visible Hiddify-first copy was removed. | Manual import remains recovery/compatibility, not primary onboarding. | Continue removing legacy power-user wording from first-layer cabinet screens. |
| Marketing / SEO / schema | Marketing schema now uses `LimitedAvailability`; homepage/SEO landing plan cards show checkout-ready beta plan only; checkout still uses Lava.top readiness. | Not all tariff plans are production checkout-ready; `LimitedAvailability` is not a store claim. | Add browser/e2e degradation tests for checkout API outage, bad plan query, key lookup failure, promo state, and mobile layouts. |
| Design / assets | Root design tokens and generated asset policy remain source of truth; beta copy no longer overclaims public availability. | Generated Flutter/client token sync is not automated; asset traceability still matters for public/store assets. | `PRODUCTION_FOLLOW_UP`: screenshot matrix, generated asset records, client token pipeline, store screenshot pack. |
| Client app | App-first shell, trial bootstrap, checkout continuation, route-mode groundwork, support context, Android/Windows beta docs are aligned to current decision. | Selected-apps remains beta MVP; routing/DNS/leak proof is not broad production proof. | Android package picker, Windows process picker, persistence, OS-level enforcement, DNS/leak checks are follow-up. |
| Ops / monitoring / RU-origin | Brain/current-origin beta evidence is retained; `mini` is documented as RU-origin sandbox when access is current. | RU-origin was `SKIPPED_BY_OPERATOR`; do not claim Russia-origin or Telegram-from-Russia readiness. | RU probe from `mini` or replacement host remains `SKIPPED_BY_OPERATOR`/`BLOCKED_BY_ACCESS` until rerun. |
| Support / launch | Known issues, release notes, Telegram drafts, and support macros now distinguish beta from production claims. | Channel posting is not automatic; support is best-effort. | Owner manually posts channel copy; support macro pack and store/ASO metadata remain follow-up. |
| Research / performance | Historical research is superseded where 2026-05-15 evidence exists; stale blockers are marked as historical context. | Historical research does not prove current runtime health by itself. | Fresh performance, browser screenshots, Lighthouse, and real-device checks are future evidence, not agent blockers. |

## Agent-Safe Next Queue

These can be done without owner-only access:

1. Add Playwright coverage for marketing checkout degraded states and `/admin/release`.
2. Extend `scripts/ui_visual_smoke.py` or equivalent screenshot matrix to current homepage, checkout, cabinet, and release admin surfaces.
3. Centralize checkout-ready plan policy so marketing and checkout share one exported constant instead of local sets.
4. Continue copy cleanup for remaining compatibility/manual-import surfaces.
5. Add docs/tests that assert JSON-LD uses beta-limited availability while store claims are absent.

## Owner / Operator Queue

These must stay manual or explicitly skipped:

1. Raw Android physical-device release-build localhost/control-surface audit.
2. Real-user Telegram/WebApp opening with env-only init data handling.
3. RU-origin probe from `mini` or a replacement RU host.
4. Payment dashboard review, refund/chargeback/reconciliation drill, and provider credential rotation evidence.
5. Android/Windows signing, store accounts, store metadata approval, and trusted Windows signing.
6. Live deploy approval for any new release candidate.
