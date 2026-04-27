# Payment Reconciliation

Last updated: 2026-04-26

## Goal

Keep paid access aligned with provider truth without relying on undocumented refund or chargeback webhook behavior.

For Lava.top, reconciliation must inspect the local `ExternalOrder` plus the latest `ExternalPaymentEvent`. Anonymous public purchases may have `tg_id=null`; those rows fulfill by an emailed access key recorded in internal order metadata, not by immediate account extension.

`manual_review` is the expected state for validly authenticated callbacks with mismatched amount, currency, plan, or missing local order. Operators should not manually mark those paid until provider evidence and order intent are attached with secrets redacted.

## Minimum Beta Procedure

1. Export or inspect provider-side order state.
2. Match provider external id to local order id.
3. Confirm amount, currency, plan, account/session, and final provider state.
4. Move ambiguous rows to manual review.
5. Do not grant new access for failed, cancelled, refunded, chargeback, or ambiguous states.
6. Record redacted evidence under the release work-order provider evidence folder.
