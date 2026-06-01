# Tech Debt Register

Status: active  
Date: 2026-05-26

Current interpretation:

- The outside-store Android + Windows public beta is `GO` from the `2026-05-15` launch-decision evidence pack.
- Manual/external checks that require owner hardware, provider dashboards, real Telegram/WebApp users, signing/store access, or RU probe access are tracked as explicit labels, not as blockers for the local agent task.
- Do not use the beta GO to claim stable `1.0.0`, app-store readiness, trusted Windows signing, raw Android device evidence, or RU-origin readiness.

| ID | Area | Debt | Impact | Label | Owner |
| --- | --- | --- | --- | --- | --- |
| TD-001 | Payments | Lava.top proof is attached for the beta, but production payment maturity still needs refund/chargeback, reconciliation, and fulfillment-ledger evidence. | Does not block outside-store beta paid checkout; blocks production payment claim. | beta resolved / production follow-up | W06 |
| TD-002 | Payments | Fulfillment remains partly direct-entitlement-oriented while the desired commercial contract is key-first with clean refund/chargeback semantics. | Blocks mature payment-and-access-key contract claims. | confirmed | W05/W06 |
| TD-003 | Payments | Callback idempotency has beta evidence, but order-fulfillment-level replay/ordering proof should stay part of every future provider or production claim. | Does not block current beta; blocks stronger provider reliability claim. | production follow-up | W06 |
| TD-004 | Client | Android release-build physical audit is owner-attested for the beta, but raw retained device evidence is not attached. | Does not block outside-store beta; blocks raw Android audit and stronger Android safety claims. | OPERATOR_ATTESTED / MANUAL_OWNER_TEST | W07 |
| TD-005 | Client | Android audit gate now defaults to the active package `space.pokrov.pokrov_android_shell`, but future release candidates must keep package evidence explicit. | Prevents old-package drift from recurring. | resolved with regression watch | W07 |
| TD-006 | Client | Windows beta remains unsigned/trust-gated. | Does not block outside-store beta; blocks trusted Windows distribution claim. | accepted beta risk / follow-up | W07 |
| TD-007 | Operations | RU-origin evidence depends on external probe availability and was skipped by operator for the beta decision. | Blocks RU-origin readiness and Telegram-from-Russia claims. | SKIPPED_BY_OPERATOR | W08 |
| TD-008 | Operations | Runtime app download smoke and public APK/EXE handoff are green, but real-user Telegram WebApp opening is not proven by local evidence. | Does not block beta; leaves manual owner test for real-user Telegram path. | PASS / MANUAL_OWNER_TEST | W06/W08 |
| TD-009 | Security | Release evidence redaction must continue to cover Telegram init-data fields, payment identifiers, callback payloads, SSH material, and subscription URLs. | Risk of leaking session or provider material into logs/evidence. | confirmed guardrail | W09 |
| TD-010 | Security | Support attachments are served as static files after upload. | Privacy hardening remains needed before larger support volume. | confirmed | W09 |
| TD-011 | Frontend | `/checkout/` is now present in the marketing sitemap helper; the remaining gap is broader browser/SEO degradation coverage for checkout and install flows. | Marketing static truth is better, but visual/browser evidence still needs expansion. | resolved with coverage follow-up | W02 |
| TD-012 | Design | Root `DESIGN.md` and token schema now exist; generated Flutter/client token sync is still not automated. | Visual parity review still needs a generated client-token pipeline. | confirmed | W01 |
| TD-013 | Docs/Launch | Launch notes, known issues, support macros, and store metadata still need a single post-2026-05-15 beta-ready language pack; admin release cockpit has been resynced to beta GO with manual gates. | Operators may improvise inconsistent beta wording or overclaim skipped gates. | partially resolved / copy-pack follow-up | W10 |
