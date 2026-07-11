# API Contracts

Last updated: 2026-07-10

This page captures release-critical API contract expectations for Open Beta v4.

## Account Ownership Boundary

The repository now implements additive account foundation: UUID `accounts.id` is persisted and `users.account_id` is a nullable projection.
The public numeric `account_id`, stateless bearer flow, payment fulfillment, and entitlement authority remain on the legacy-compatible path.
Production deployment of account foundation is not proven.
Rotating sessions, recovery exchange, payment ownership cutover, and entitlement-ledger authority are not implemented current truth and must not be claimed.

## Client Apps

`GET /api/client/apps` must return only approved runtime links. Empty Android or Windows URLs mean the corresponding public download is not available and must be presented as gated/support-routed.

## Payment Providers

`GET /api/payments/providers` must expose provider availability and enough unavailable-state detail for checkout to avoid presenting blocked payment paths as live.

## Support

Support ticket APIs must avoid exposing private attachments or session data in public logs. Attachment privacy remains a beta hardening item.

## Admin

Admin APIs must keep payment, download, node, ticket, and user states
audit-friendly. `adminapp` is the primary operator surface;
`webapp/src/app/(admin)/admin/` is the parity fallback, and Telegram admin
remains fallback-only.
