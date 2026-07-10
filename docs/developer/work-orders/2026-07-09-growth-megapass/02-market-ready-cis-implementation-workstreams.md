# POKROV Market-Ready CIS Implementation Workstreams

Date: 2026-07-10
Status: active execution plan

## Dependency Order

1. Baseline and secret-safe planning evidence.
2. Canonical account schema, backfill and compatibility projections.
3. Device/session, OTP, recovery and antiabuse contracts.
4. Entitlement ledger and server-authoritative connection evidence.
5. Bot/economy/free/referral behavior.
6. Cabinet, admin, marketing, payment and support surfaces.
7. Notices and client delivery transports.
8. Client runtime/release integrity and exact-artifact verification.
9. Migration rehearsal, RC soak and stable promotion.

## Workstream A: Account And Security

Ownership: `portal_bot/models.py`, `migrations.py`, bounded account/session/
recovery/antiabuse services, and API routing in `portal_bot/api.py`.

Deliverables:

- `accounts`, `account_identities`, `account_devices`, `auth_sessions`.
- `entitlement_grants`, `recovery_codes`, antiabuse event/case/action ledger.
- Idempotent backfill, merge report, conflict queue and rollback evidence.
- Rotating refresh sessions, session reuse detection and fresh-auth scopes.
- OTP and one-time recovery exchange with rate limits.
- Raw-IP cleanup and versioned HMAC retention jobs.

## Workstream B: Economy And Bot

Ownership: `portal_bot/bot.py`, `worker.py`, `channel_bonus_service.py`,
`free_cycle_service.py`, `node_policy.py` and panel synchronization.

Deliverables:

- New-lead Telegram gate and 24-hour unsubscribe grace.
- Trial reservation/bootstrap/activation from internal node evidence.
- Additive, reversible grants and pre-payment stacking cap.
- Referral `+5/+15` with 72-hour review hold.
- Dedicated `NL-free` soft inbound at enforced 2 Mbps after 5 GB.
- Unified lifecycle workers with delivery-success dedupe.

## Workstream C: Web, Admin, Payment And Support

Ownership: `webapp/src`, `adminapp/src`, `marketing/src`, `shared`, payment and
ticket API services.

Deliverables:

- Recovery, devices, reissue, referral history and notices in cabinet.
- Email OTP and public checkout pending-entitlement claim.
- Correct checkout funnel events and payment return routing.
- One cross-surface support thread and redacted diagnostics.
- Primary `adminapp` write surface; legacy admin read-only fallback.
- Manual content queue and global/per-surface kill switches.

## Workstream D: Notifications

Ownership: persisted notice/delivery models, API, workers and client adapters.

Deliverables:

- Cursor-based notice feed, read state, dedupe and preference categories.
- Encrypted Android FCM token storage and opaque-ID delivery payloads.
- Windows 15-minute tray polling plus launch/resume refresh and local toast.
- Quiet hours, promo cap, fallback routing and delivery audit.

## Workstream E: Client And Release

Ownership: `POKROV-app/packages/app_shell`, `packages/runtime_engine`, Android
and Windows hosts, release scripts/config and active client docs.

Deliverables:

- Durable secure-storage migration and forced reinstall recovery path.
- Real multi-device/session API integration.
- Quick Settings tile and notification permission flow.
- Stable WARP active/degraded/fallback proof on Android and Windows.
- Binary-owned SemVer/build numbers, ABI-aware updates and SHA-256 checks.
- Fail-closed Android signing, signed Windows MSIX/direct packaging, SBOM and
  immutable release handoff metadata.

## Verification Gates

- Unit/integration tests follow RED/GREEN for every behavior change.
- Migration is repeatable and preserves payment/support/entitlement history.
- Numeric subscription fallback is disabled at cutover.
- Paid, failed, duplicate, refund and chargeback reconciliation pass.
- Exact uploaded artifacts pass install, recovery, connect/reconnect, routing,
  DNS/leak, notices, support, checkout, WARP and update paths.
- Release evidence records `current-origin`, `brain-origin`, and `RU-origin`
  checks separately. Missing RU access is labeled `BLOCKED_BY_ACCESS` or an
  owner-approved skip and never converted into a geographic readiness claim.
- RC requires zero open P0/P1, connect success >=95%, first connect >=90%,
  event completeness >=98%, API/checkout >=99.5% and support p90 <=4 hours.
- Stable promotion requires the immutable `1.0.0-rc.1` to reach 100 canary
  users and complete a seven-day soak without an open P0/P1 issue.
- Google Play and Microsoft Partner Center submissions must exist before the
  signed direct stable release; store moderation itself is not a blocker.
- The stable growth gate requires `trial -> first paid >=5%` after at least 200
  trials. Until that sample exists, the RC remains a measured canary and cannot
  be represented as validated mass-market conversion.
