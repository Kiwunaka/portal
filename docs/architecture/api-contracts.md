# API Contracts

Last updated: 2026-04-26

This page captures release-critical API contract expectations for Open Beta v4.

## Client Apps

`GET /api/client/apps` must return only approved runtime links. Empty Android or Windows URLs mean the corresponding public download is not available and must be presented as gated/support-routed.

## Payment Providers

`GET /api/payments/providers` must expose provider availability and enough unavailable-state detail for checkout to avoid presenting blocked payment paths as live.

## Support

Support ticket APIs must avoid exposing private attachments or session data in public logs. Attachment privacy remains a beta hardening item.

## Admin

Admin APIs must keep payment, download, node, ticket, and user states audit-friendly. Telegram admin remains fallback-only; web admin is the primary operator surface.
