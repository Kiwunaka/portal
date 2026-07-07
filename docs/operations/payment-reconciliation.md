# Payment Reconciliation

Last updated: 2026-07-05

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

## Evidence Terms

`refund evidence` means practical proof that a refund path is handled end to end:

- a Lava.top refund callback, dashboard refund export, or operator replay fixture with secrets redacted
- the matching local `ExternalOrder` moves to `refunded` or `manual_review`
- the user or issued access key is not silently extended after the refund
- the evidence note includes order id, provider external id, amount, currency, plan, previous local status, final local status, and redaction note

`chargeback evidence` means practical proof that a dispute/chargeback path is not treated as paid:

- a provider dispute/chargeback callback, dashboard proof, or operator replay fixture with secrets redacted
- the local order is marked `chargeback` or `manual_review`
- existing access is not silently renewed by that order after the dispute state is known
- the evidence note records whether any manual access action was required

`reconciliation drill` means an operator manually compares one Lava.top order with the local ledger:

1. pick a paid, failed, refunded, chargeback, or suspicious order
2. compare provider id, local order id, amount, currency, plan, payment method, and final provider status
3. update the local status only through the documented admin/API/manual-review path
4. write a redacted audit note without card data, buyer personal data, secrets, raw callback signatures, or full provider payloads

`finance-ops queue` means an admin/operator list where payment rows are grouped by action state, not just by raw provider status. Minimum queues:

- `paid`: verify fulfillment exists and is idempotent
- `failed`: confirm no access was granted
- `refunded`: confirm access was not extended or was manually reviewed
- `chargeback`: confirm the disputed order is not counted as clean revenue
- `manual_review`: compare provider truth with local intent and attach redacted evidence

Production checkout maturity is not closed until the queue and the three evidence classes above have at least one current redacted proof each for Lava.top.
