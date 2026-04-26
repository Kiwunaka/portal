# Tech Debt Register

Status: active  
Date: 2026-04-26

| ID | Area | Debt | Impact | Label | Owner |
| --- | --- | --- | --- | --- | --- |
| TD-001 | Payments | Active Lava.top provider proof is not attached to local evidence. | Blocks public paid checkout and any stable release claim. | blocked by missing access | W06 |
| TD-002 | Payments | Fulfillment is direct-entitlement-first, not activation-key-first. Refund/chargeback behavior is not entitlement-safe. | Blocks payment-and-access-key contract claims. | confirmed | W05/W06 |
| TD-003 | Payments | Callback idempotency is event-oriented rather than order-fulfillment-oriented. | Duplicate or reordered provider events need stricter proof before launch. | confirmed | W06 |
| TD-004 | Client | Android release-build physical audit evidence is missing. | Blocks public Android claim. | blocked by missing access | W07 |
| TD-005 | Client | Android audit gate defaults to a legacy package identifier. | Physical audit can target the wrong app without override. | confirmed | W07 |
| TD-006 | Client | Windows beta remains unsigned/trust-gated. | Blocks public-safe Windows distribution claim. | confirmed | W07 |
| TD-007 | Operations | RU-origin evidence depends on external probe availability. | Blocks geography-specific release confidence. | blocked by missing access | W08 |
| TD-008 | Operations | Runtime app download smoke wrapper now exists, but live env-only Telegram init data and approved handoff URLs are missing. | Blocks runtime download evidence for public distribution. | blocked by missing access | W06/W08 |
| TD-009 | Security | Release evidence redaction does not explicitly cover Telegram init-data fields or `--init-data`. | Risk of leaking session material into logs/evidence. | confirmed | W09 |
| TD-010 | Security | Support attachments are served as static files after upload. | Privacy hardening remains needed before larger support volume. | confirmed | W09 |
| TD-011 | Frontend | `/checkout/` is absent from the marketing sitemap. | Primary checkout acquisition route is not represented in canonical sitemap. | confirmed | W02 |
| TD-012 | Design | Root `DESIGN.md` and token schema now exist; generated Flutter/client token sync is still not automated. | Visual parity review still needs a generated client-token pipeline. | confirmed | W01 |
| TD-013 | Docs/Launch | Launch notes, known issues, support macros, and store metadata pack are not canonicalized. | Operators may improvise inconsistent beta wording. | confirmed | W10 |
