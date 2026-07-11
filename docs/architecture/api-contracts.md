# API Contracts

Last updated: 2026-07-12

This page is a concise router to the current domain owners. It is not a
complete endpoint inventory.

## Account Ownership Boundary

The repository now implements additive account foundation: UUID `accounts.id` is persisted and `users.account_id` is a nullable projection.
The public numeric `account_id`, stateless bearer flow, payment fulfillment, and entitlement authority remain on the legacy-compatible path.
Production deployment of account foundation is not proven.
Rotating sessions, recovery exchange, payment ownership cutover, and entitlement-ledger authority are not implemented current truth and must not be claimed.

## Domain Owners

- Identity, account linking, username sync, and bonus flows:
  [App-First And Bonus Flows](app-first-and-bonus-flows.md).
- Payment lifecycle and entitlement transitions:
  [Payment State Machine](payment-state-machine.md); product-facing purchase,
  activation-key, and access rules live in
  [Payment And Access Key Contract](../product/payment-and-access-key-contract.md).
- Approved client binaries, runtime links, and update metadata:
  [Client Downloads Flow](client-downloads-flow.md).
- Support tickets, attachments, feedback, and moderation:
  [Support And Feedback Flow](support-feedback-flow.md).
- Backend and admin responsibility boundaries:
  [System Overview](system-overview.md). `adminapp` remains the primary operator
  surface, the web admin is a parity fallback, and Telegram admin is fallback-only.
- Active Android and Windows client contracts:
  [POKROV App Docs Index](C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md).
