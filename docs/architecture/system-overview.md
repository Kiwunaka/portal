# POKROV System Overview

Last updated: 2026-08-17

## Document Status

This file is living source of truth for the platform architecture map.

## Purpose

`POKROV` is a platform composed of:

- a Python backend and Telegram control plane
- a user cabinet, a standalone admin ops app, and a retained legacy admin web surface during parity
- a marketing and legal site
- a dedicated active client repo at `C:/Users/kiwun/Documents/ai/POKROV-app`
- a retained `app-next/` bootstrap archive/reference lane
- a retained legacy client rollback/archive reference lane
- operational scripts for deployment, node management, and release flow

## Wave 0 Rework Target

The new target architecture for the global rework freezes these boundaries before later code waves land:

- platform truth remains in this root repository
- `POKROV-app/main` is the only active client development and client-doc truth, with local checkout path `C:/Users/kiwun/Documents/ai/POKROV-app`
- `app-next/` is the retired bootstrap-source archive/reference workspace for that repo after the initial local snapshot landed
- `external/client-fork/app/` is the retired rollback/archive client reference workspace
- the front-end rebuild is an atlas-driven shell reset: acquisition lives on `marketing/`, continuation lives on `webapp/`, and the app shell is locked to `Protection / Locations / Rules / Profile`
- one app-first account becomes the identity root for `install_id`, email, Telegram, devices, and activation keys
- public acquisition, pricing, and paywall move entirely onto `marketing/`, with trial, install, and first connection as the primary public CTA path and checkout as explicit continuation, while `webapp/` becomes session-aware continuation, redeem, support, and renewal continuation; `adminapp/` owns the new dedicated operator surface
- public browser copy and visual governance are centralized through `shared/copy.ts`, `copy/catalog.ru.json`, and `shared/design-tokens.json`, with locked host and product facts inherited from the shared fact files
- visible user-facing cabinet IA is `Главная / Доступ / Помощь / Аккаунт`, with `/devices/`, `/statistics/`, `/downloads/`, `/redeem/`, support thread/legal routes, and hosted-checkout continuation treated as task/detail routes rather than parallel acquisition surfaces
- commerce moves to hosted checkout plus activation-key issuance and redemption instead of raw subscription-link-first UX
- remote promo content is limited to approved first-party promo slots; third-party ad SDKs remain out of scope
- the public location story collapses to one logical location per user, while the transport matrix stays hidden behind rollout, diagnostics, and admin controls

Reference-lane note:

- `app-next/` and `external/client-fork/app/` may still be consulted for archived bootstrap or rollback evidence
- those retained workspaces do not override the active architecture truth in `POKROV-app/main`

## Main Components

### Control Plane

- `portal_bot/api.py`
  FastAPI composition root for shared dependencies, middleware, compatibility
  exports, and ordered route registration. HTTP implementations are grouped in
  `api_public_routes.py`, `api_surface_routes.py`, `api_admin_routes.py`, and
  `api_subscription_routes.py`; see the
  [backend module map](../developer/backend-module-map.md).
- `portal_bot/app_first_service.py`
  Bounded app-first/session helper used by the API for trial bootstrap, session payload shaping, and Telegram link start context.
- `portal_bot/account_foundation_service.py`
  Additive canonical-account projection and idempotent legacy backfill for
  accounts, typed identities, devices and legacy entitlement snapshots.
- `portal_bot/account_experience_service.py`
  Account-scoped onboarding and first-connection UX projection. It reconciles
  account merges and reads trusted `ConnectionEvidence`, but never owns access,
  trial activation, payment, or reward authority.
- `portal_bot/auth_session_service.py`
  Device-bound access/refresh issuance, one-time rotation, refresh-family reuse
  detection, persisted logout, fresh-auth device revoke and access validation.
- `portal_bot/account_recovery_service.py`
  HMAC-only one-time recovery codes, limited recovery sessions, controlled
  access reissue and account lockdown orchestration.
- `portal_bot/email_auth_service.py`
  Verified email identity, five-minute six-digit OTP and retained password
  compatibility during the migration window.
- `portal_bot/web_auth_service.py`
  Bounded browser-auth helper used for Telegram web login, additive email verification/recovery, session issuance, and checkout handoff tokens.
- `portal_bot/channel_bonus_service.py`
  Bounded Telegram bonus helper used by the API for read-only subscriber checks and explicit claim flow.
- `portal_bot/warp_service.py`
  Bounded app-facing WARP lifecycle helper used by the API for client-local
  readiness status, consent/revoke/rotation events, runtime fallback
  telemetry, and secret redaction before ledger persistence. It also owns
  optional encrypted-at-rest per-user/per-install WARP material shaping for
  managed profile delivery when an operator explicitly provisions material.
- `portal_bot/bot.py`
  Telegram composition root for shared dependencies, presentation helpers,
  compatibility exports, and ordered handler registration. Customer, admin,
  payment, and operator implementations live in the four `bot_*_handlers.py`
  slices documented in the
  [backend module map](../developer/backend-module-map.md). The user-facing
  presentation layer uses editable rich messages with equivalent HTML
  fallback, semantic button colors, and a curated custom-emoji registry;
  callback and payment behavior remain independent of those Telegram client
  capabilities.
- `portal_bot/helpbot.py`
  Dedicated support bot.
- `portal_bot/support_agent_service.py`
  Exact disabled/legacy/harness route selector shared by the app assistant, ticket hints, and `@pokrov_supportbot`; all failure paths return the deterministic local fallback.
- `portal_bot/support_ai_service.py`
  Legacy one-call OpenAI-compatible helper and shared bounded sanitizer; retained only when `SUPPORT_AI_ENABLED=true` and `SUPPORT_AI_AGENT_ENABLED=false`.
- `portal_bot/support_agent_harness.py`, `portal_bot/support_agent_context.py`, and `portal_bot/support_agent_provider.py`
  Bounded mini-agent loop, stable cacheable context, and an exact-route OpenAI-compatible adapter for canonical `deepseek-v4-flash-0731` with medium reasoning. The exact OpenRouter route maps it to `deepseek/deepseek-v4-flash-0731` on the wire, leaves the completion budget provider-managed so reasoning cannot consume a short `max_tokens` cap, excludes the private reasoning trace, allows a 45-second provider window inside a 50-second harness deadline, and normalizes only a single clean JSON Markdown fence before the unchanged closed-schema safety checks.
- `portal_bot/support_agent_policy.py`, `portal_bot/support_agent_knowledge.py`, and `portal_bot/support_agent_sessions.py`
  Fail-closed policy/KB validation, read-only local topic retrieval, and owner-scoped process-memory/rate limits.
- `portal_bot/worker.py`
  Background jobs for retention, bonus enforcement, and free-cycle operations.
- `portal_bot/models.py`
  SQLAlchemy model layer.
- `portal_bot/migrations.py`
  Additive schema migration helpers.

### Delivery Plane

- `portal_bot/control_panel.py`
- `portal_bot/panel_client.py`
- node inventory and routing logic
- 3x-ui panels as node-local execution layer
- observer-lite uses `xray access.log -> node collector -> brain ingest -> Postgres state -> web admin`
- capacity-aware routing state lives in additive tables such as `access_keys`, `node_capacity_policy`, `node_runtime_metrics`, `key_usage_rollups`, `key_source_observations`, `key_pressure_state`, `subscription_fetch_events`, `rendered_subscription_snapshots`, `node_pool_membership`, and `node_provisioning_jobs`
- transport rollout uses a per-node catalog so a node can carry `legacy_reality_fallback`, `grpc_443_primary`, hidden reserve `reserve_xhttp_cdn`, emergency `ru_bridge_relay`, and operator-only `operator_lab` entries side by side
- `nodes.transport_profiles_json` is the canonical per-node transport catalog; legacy inbound fields such as `inbound_id`, `vless_port`, and `reality_*` remain compatibility input and are synthesized into `legacy_reality_fallback` when the catalog is empty
- `AppSetting.network_rollout_config` is the operator-controlled rollout policy for transport, DNS, routing, and operator lab allowlists, and it is exposed through admin GET/PUT endpoints
- `network_rollout_config` is a JSON policy blob with `version`, `defaults`, `carrier_overrides`, `cohort_overrides`, `reserve_xhttp_cdn`, `ru_bridge_relay`, `operator_lab`, `package_catalog_feed`, `routing_rules_feed`, and `support_recovery_order`
- `defaults` normally pin `routing_mode_default=all_except_ru`, `transport_profile=legacy_reality_fallback`, and `dns_policy=ru_direct_split`; the owner-approved `2026-06-01` incident posture may promote `transport_profile=ru_bridge_relay` while keeping `legacy_reality_fallback` as the rollback target
- dormant reserve transport metadata also lives in rollout config and node catalogs under `reserve_xhttp_cdn`; it stays disabled by default and becomes active only through explicit rollout allowlists
- `ru_bridge_relay` is the owner-approved `2026-06-01` emergency profile: the app receives a sing-box manifest where the top selector lists countries and each non-US country contains nested `Обычный` and `Белые списки` choices; `us` remains available only as a normal direct target. The rollout policy keeps legacy single-bridge top-level fields for compatibility, while the current additive format can also carry `ru_bridge_relay.endpoints[]` entries merged by stable `id`.
- rollout overrides may only change `transport_profile`, `dns_policy`, `routing_mode_default`, and `ip_version_preference`
- `operator_lab` stays allowlist-only and carries `enabled`, `allowlist_install_ids`, `allowlist_tg_ids`, `allowlist_node_codes`, and `expires_at`
- app-managed session/profile payloads resolve their transport profile from rollout policy, while manual/export compatibility links stay on `legacy_reality_fallback` until a separate share-link parity wave
- `GET /api/client/profile/managed` is the primary app-managed provisioning endpoint and returns `version`, `profile_revision`, `transport_profile`, `transport_kind`, `engine_hint`, `config_format`, `config_payload`, `fallback_order`, `support_context`, `smart_connect`, and managed-profile `warp_policy`
- `smart_connect` contains a rollout-compatible shortlist, internal probe targets, capacity/scoring hints, rejection counters, and stickiness metadata so the client can combine real RTT with backend health, dataplane, and network-pressure signals without guessing
- `client_policy.warp_policy` remains sanitized; the default WARP path is
  client-local through Hiddify core, so the backend must not require
  server-managed WireGuard material before the client can set
  `warp.enable=true` after explicit local user consent. WireGuard
  config/account material may appear only in the authenticated managed-profile
  `warp_policy` when an operator-provisioned optional material lane marks it
  ready.
- scoped WARP material lives in `warp_materials` encrypted at rest; operators
  may provision it through `PUT /api/admin/client/warp/material`, while public
  status and dashboard policy continue to expose only sanitized readiness
  fields. This material lane is optional and not the normal client-local WARP
  prerequisite.
- scoped WARP provisioning and rotation are protected by per-hour backend
  limits; stale material is rejected from managed profiles after
  `WARP_MATERIAL_MAX_AGE_HOURS`, and operators can inspect redacted material
  counts plus runtime state/reason/event headers via
  `GET /api/admin/client/warp/summary`
- `GET /api/client/warp/status`, `POST /api/client/warp/consent`,
  `POST /api/client/warp/revoke`, `POST /api/client/warp/rotate`, and
  `POST /api/client/warp/events` own the app-facing WARP lifecycle; these
  routes write `WarpEvent` rows and redact runtime secrets from public status
  and ledger metadata
- `GET /api/client/nodes/candidates`, `POST /api/client/nodes/select`, and optional `selected_node_code` on `GET /api/client/profile/managed` form the primary app node-selection contract; `POST /api/client/nodes/latency-samples` remains compatibility telemetry for install-scoped RTT samples and carrier/platform context
- `GET /api/client/locations` preserves the existing country/city catalog and adds a stable safe `variants` list per city for manual route choice: `direct` / `Обычный` is always first, while enabled `ru_bridge_relay` endpoint ids and short labels appear only when that exact node passes endpoint validity, bridge allowlist/exclusion, and transport-eligibility checks. The variant projection never exposes bridge hosts, ports, Reality material, hidden selector tags, or raw config, and uses the same availability helper as Hiddify/sing-box rendering so excluded targets such as US stay direct-only.
- `GET /api/client/emergency-network/catalog`, `POST /api/client/emergency-network/profile`, and authenticated `POST /api/client/emergency-network/offline-bundle` own the separate trial/paid emergency-network surface. The bundle atomically returns the signed safe catalog plus every fresh or still-valid signed last-known-good reserve/supported-chain profile for device-local encrypted prewarming; a new `precache_only` request permits that download after trial/paid access is proven, while the `entitlement_precache` marker keeps activation behind trusted RU evidence or the explicit limited-network switch. The bundle is `no-store` on the HTTP boundary and bounded to 4–20 reserves and at most 60 profiles. Every envelope binds to the active `AccountDevice` named by the access token, not the canonical user's legacy install. Emergency leases last at most seven days and never beyond account, catalog, or eligibility expiry. Probe age remains visible as `working` or `stale`, while the signed catalog expiry remains the offline-use authority. Clients start a valid cached profile without a control-plane request and refresh it only when connectivity exists. The normal location catalog, WARP and third-party routing/DNS policy are not reused as implicit emergency behavior. Emergency DNS uses IPv4-only, fixed literal-IP DoH inside the selected encrypted reserve-first chain. This avoids local-RU DNS dependence and paired A/AAAA pressure on the constrained first hop while keeping DNS encapsulated by VLESS rather than exposing it to the local network. Public catalog projection contains only stable ids, country, status, latency, freshness and supported modes; endpoint material appears only inside authenticated signed managed profiles.
- emergency snapshots move through `staging` to one atomic `active` revision only after exact adapter probes. Promotion builds a bounded pool of up to 20 unique hosts: fresh successes from the current revision first, then still-fresh exact successes retained from recent active, superseded, or staging revisions. A proof is reusable only for 24 hours and only when the stable material identity still matches; source-only claims, failed probes, RU exits, duplicate hosts, and future timestamps never enter the pool. Automatic promotion rejects fewer than four pool members, excessive churn while the active catalog still has a fresh four-endpoint quorum, and an operator-disabled distribution state; a saturated 20-endpoint verified pool or the loss of that active fresh quorum may roll forward despite high source churn so emergency delivery cannot remain pinned to four old variants. Rollback reproduces the exact signed target set instead of merging newer history. Disable blocks new catalog/profile delivery but cannot recall a valid signed catalog already cached on a device; entitlement and snapshot expiry remain mandatory client-side checks.
- `GET /api/client/notifications` emits access notices only in actionable expiry
  windows. Paid access uses T-3/T-1/T0; trial and bonus access use T-1/T0. A
  stable id includes access kind, stage and expiry date, so reading an old
  notice cannot hide a later entitlement. Telegram delivery uses the same
  access distinction, respects 09:00–21:00 in the last known device timezone
  with Moscow fallback, and lets lifecycle warnings suppress operator promo.
- `POST /api/client/notifications/dismiss` records account-scoped dismissal of
  explicit notification ids; later inbox reads omit those ids without deleting
  the retained source update, incident, grant, or access history.
- `POST /api/client/runtime/stats` is best-effort app telemetry and must not be required from external subscription clients; `connected=true` may record only an account UX `reported` milestone
- signed observer ingestion remains the only `verified` first-connection path and the only connection source allowed to activate a reserved trial
- `GET /api/user/*` exposes account experience state, while `POST /api/account/experience/onboarding` persists cabinet/app onboarding completion or skip without touching entitlement state
- additive `client_policy` fields `transport_kind`, `engine_hint`, and `profile_revision` let the client apply the right engine/runtime without guessing
- one logical client is synchronized across all enabled inbounds in a node's transport catalog, while public UI still exposes only the rollout-selected app-managed path
- `reserve_xhttp_cdn` is prepared as a hidden reserve profile; when explicitly selected it resolves to `transport_kind=xhttp` with `engine_hint=xray`, while the normal consumer baseline stays `sing-box`
- `ru_bridge_relay` resolves to `transport_kind=ru_bridge` with `engine_hint=singbox`; it is not a normal delivery-node pool and does not make `mini` a control-plane host

Node lifecycle rule:

- `POKROV` database decides assignment and lifecycle
- 3x-ui executes the resulting config
- node retirement sequence is `drain -> resync -> disable`
- consumer free-tier delivery is retired by default: `FREE_TIER_ENABLED=false`, expired accounts keep recovery/payment access, and no free node may fall back to the paid pool
- user-facing and operator-effective access has exactly three states:
  `TRIAL`, `PAID`, and `PENDING`. Admin grants, gifts, bonuses, promos, and
  provider payments are `PAID` while their access window is active. Historical
  `FREE` values may remain in storage for migration/audit compatibility but are
  never exposed as a live product tier.
- panel desired state follows the effective window rather than the legacy
  `sub_type`: every active `TRIAL`/`PAID` identity is enabled across every
  enabled paid delivery node, while `PENDING` is disabled everywhere. Admin
  extensions synchronize after commit, the expiry worker disables panels before
  marking the local projection inactive, and the guarded reconciliation script
  repairs historical drift without printing user identifiers.
- the RF reserve contour lives outside the normal delivery lifecycle until explicitly promoted

### User Interfaces

- `webapp/`
  user cabinet and session continuation; legacy admin routes stay only until `adminapp/` parity is proven
- `adminapp/`
  standalone Russian-language Next.js operator surface for `https://admin.pokrov.space/`, with 17 direct route modules: dashboard, nodes, traffic, alerts, provider caps, emergency network, free tier, users, online, tickets, payments, funnel, promos, referrals, release, broadcast, and news drafts
- `marketing/`
  public website, pricing, legal pages, and public conversion flows
- `C:/Users/kiwun/Documents/ai/POKROV-app/`
  canonical active client repo for new Android and Windows product-direction work
- `app-next/`
  retired bootstrap-source archive/reference workspace for the client migration
- `external/client-fork/app/`
  retired rollback/archive reference client, with some legacy `POKROV VPN` identifiers still present for compatibility
- `shared/`
  shared public copy, canonical hostnames, product facts, and design tokens

Current public-surface split:

- `marketing/` owns the homepage, public `/checkout/` pricing/paywall flow, offer/privacy pages, indexable SEO landings, and metadata assets such as `robots`, `sitemap`, `manifest`, Open Graph, Twitter, and JSON-LD
- current canonical indexable entry routes are `/mobile/`, `/tiktok/`, `/youtube/`, `/devices/`, and `/telegram/`, with permanent redirects from the earlier legacy SEO slugs
- public marketing CTA priority is app-first trial, install, and first connection; checkout, install help, and cabinet-open flows remain explicit exits for known intent
- `webapp/` owns browser entry, dashboard, subscription, devices, statistics, support, task routes such as downloads, redeem, and hosted-checkout continuation, plus compatibility redirects for older cabinet routes
- `adminapp/` owns `admin.pokrov.space` and is the new primary operator surface; existing `webapp/src/app/(admin)/admin/` routes are retained only as a parity fallback until the dedicated panel covers every operator workflow and the old routes pass a deletion checklist
- `webapp/` browser entry is a continuation router for app handoff, Telegram login, and email login when delivery readiness is green
- `/pricing/` in `webapp/` is compatibility-only continuation that now redirects to `/subscription/` and must not drift back into a public acquisition surface
- `connect.pokrov.space` stays outside the marketing/cabinet storytelling layer and remains the config-delivery host for the one public connection link plus QR; it serves the rollout-selected app-managed profile, with `legacy_reality_fallback` as the baseline until canary cohorts flip to `grpc_443_primary`

Client release safety rule:

- Android and Windows remain the public `v1` target pair
- Android must not be released as publicly safe until release-build verification proves that localhost proxy, DNS, command, and admin surfaces are not exposed without acceptable protection

Admin ownership rule:

- `adminapp` is the primary new admin surface for user, online, node, payment, funnel, ticket, metrics, traffic, free-tier, provider-cap, emergency-catalog, release, broadcast, and durable-alert work
- `webapp` admin routes are retained as a temporary parity fallback and must not be deleted until the dedicated `adminapp` has full workflow parity and regression coverage
- Telegram admin in `portal_bot/bot.py` is fallback/emergency tooling and must follow the same user-status semantics as web admin
- `/api/admin/summary` remains the operator truth snapshot for entitlement counts, install-backed activity, observer-backed activity, and data-quality status badges
- `/api/admin/ops/overview` is the new dedicated ops snapshot for `adminapp`, combining summary, metrics freshness, capacity, traffic cap visibility, free-tier burn, provider quotas, and durable alerts
- `/api/admin/online/users` is the bounded live online aggregate for operator lists; it must not expose raw IP addresses outside individual user investigation views
- `/api/admin/payments/summary?period=today|7d|30d` is the payments aggregate for revenue, status counts, stuck-payment attention, and abandoned buy/checkout counts
- dangerous admin actions exposed by `adminapp` require a server-owned action intent, explicit confirmation, idempotency, and durable audit; broadcast and bulk-style work should use dry-run/preview first where the backend supports it
- `GET /api/admin/emergency-network/status` exposes only worker readiness,
  snapshot revisions/counts, active identity, aggregate probe levels, rejection
  summaries and retained rollback candidates. Stage, promote and rollback use
  the same action-intent boundary; raw bundle data, endpoint material,
  host-hashes, ciphertext, signatures and keys never cross the admin read
  boundary.

Public connection delivery rule:

- `subscription_url` is generated by the backend and points to `https://connect.pokrov.space/s8Kx2mP7qR4wT/{token}`
- newly generated subscription URLs require a non-empty, non-numeric `sub_token`;
  URL construction fails closed instead of publishing a numeric Telegram/account
  identifier
- `connect.pokrov.space` serves the rollout-selected app-managed profile and keeps `legacy_reality_fallback` as the baseline until canary cohorts are explicitly enabled for `grpc_443_primary`
- `connect.pokrov.space/rules/` serves mirrored sing-box binary rule sets for client configs: `geoip-ru.srs` and `adblock.srs`; clients should not depend on `raw.githubusercontent.com` for these runtime rule downloads
- legacy `api.pokrov.space/s8Kx2mP7qR4wT/{token}` remains compatibility-only for older imports
- numeric route lookup is a separately gated emergency compatibility path:
  `SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED` defaults to `false`. Production removal
  is not proven until token backfill and panel `subId` reconciliation are complete
  and retained telemetry shows no legitimate numeric lookup for the agreed window
- explicit manual/recovery UX may expose one connection link and one QR, not separate smart/plain links; first-layer consumer screens should prefer app install, reconnect, route-mode change, checkout, and support

Current release scope rule:

- full public `v1` ship target: `Android` and `Windows`
- `iOS` and `macOS`: readiness and packaging documentation only in this wave

### Operational Tooling

- `scripts/`
  deploy, smoke, release, node, audit, and migration tooling
- `infra/`
  runtime units and infrastructure assets

## Data Source Of Truth

Production source of truth:

- Postgres from `DATABASE_URL`
- cross-surface public facts from:
  - `shared/product-facts.json`
  - `shared/public-urls.json`
  - `shared/design-tokens.json`
- active client-repo truth from `POKROV-app/main`

Account ownership transition:

- deployment status: the additive account foundation, rotating app-session,
  and canonical support-ownership slices are repo-implemented candidates but
  are not deployed. Production remains on the legacy auth, entitlement,
  payment, support, bonus, `users.tg_id` and stateless app-bearer paths until
  the predeploy gates below are approved.

- `accounts.id` is the new immutable UUID ownership root; `users.account_id`
  is an additive legacy projection and may point multiple legacy user rows at
  the same account after an explicit app-to-Telegram link.
- paid reward authority follows that UUID: `reward_account_states` owns wheel
  and calendar state, typed `entitlement_grants` own awarded duration, and
  `node_provisioning_jobs(job_type=reward_entitlement_sync)` own asynchronous
  panel convergence. Legacy `reward_claims`, achievements, `last_wheel_spin`,
  and monthly paid-streak fields are evidence/projections, not current reward
  authority.
- `users.tg_id` remains the compatibility adapter for current bot, panel,
  payment and public API behavior. Existing response fields that call the
  numeric value `account_id` have not switched to the UUID yet.
- `support_tickets.account_id` and `support_attachments.owner_account_id` are
  nullable canonical ownership projections. Exact account ownership controls
  non-admin access when present; exact legacy Telegram fallback is valid only
  while the relevant field is `NULL`. Public support responses retain their
  existing shape and do not expose canonical UUIDs.
- the distinct `migration.support_account_ownership.v1` startup backfill runs
  after account-foundation in one commit scope. It resolves only exact direct,
  explicit linked-Telegram, and enabled Telegram-identity evidence through
  bounded merge chains. Zero or multiple canonical candidates remain `NULL`
  and create idempotent metadata-only merge reviews. A direct repair entrypoint
  is retained after the startup marker is complete.
- account merge retargets canonical ticket and upload ownership without
  deleting support rows or changing messages, files, or legacy attribution.
  Notification delivery separately uses bounded deterministic linked-Telegram,
  enabled Telegram-identity, then real historical-ticket evidence. It skips
  safely when no real Telegram target exists.
- the first startup backfill uses deterministic UUIDv5 values, preserves legacy
  rows, creates typed identity/device projections and one non-authoritative
  `legacy_snapshot` entitlement grant per legacy user, then records the
  `migration.account_foundation.v1` completion marker. Later service starts use
  the indexed `users.account_id IS NULL` repair check and do not perform a full
  rescan unless a missed legacy write actually needs repair.
- PostgreSQL `Base.metadata.create_all` and additive migrations both take the
  same `pokrov_schema_bootstrap` transaction advisory lock. They still run in
  separate transactions, but concurrent API/bot/worker first starts cannot run
  schema creation and DDL migration at the same time.
- only explicit `linked_telegram_id` edges auto-merge legacy users. Conflicting
  typed identities remain unchanged and create `account_merge_reviews` rows.
  A direct Telegram row that arrives after an app row already points to it
  converges through that explicit reverse edge instead of creating a second
  account and conflict review.
- ordinary runtime projection takes a shared PostgreSQL global lock plus a
  per-user transaction lock; full backfill and account merges take the global
  lock exclusively. Explicit Telegram link merge is limited to that connected
  account component, and the bot locks the consumed link plus both user rows.
  Each transaction chooses its final global mode once; shared-to-exclusive
  upgrades are forbidden.
  Restrictive account state and the highest `auth_epoch` survive absorption.
- lock acquisition order is `users` rows by numeric ID, deterministic per-user
  advisory locks, then the global projection lock. A separate startup advisory
  lock serializes marker repair without creating a row/global lock inversion.
- new Telegram binds reject transitive identity chains before taking the global
  projection lock. Existing malformed chains remain migration/review data; the
  public bot does not extend them. Runtime migration discovers an existing full
  component first, locks all member rows in one numeric query, then verifies the
  closure before projection.
- `auth_sessions` now has repository behavior for short-lived device-bound
  access tokens, absolute-expiry rotating refresh families, reuse detection,
  persisted logout and fresh-auth device revoke. Raw refresh credentials are
  not stored. This behavior is not deployed and is not production proof.
- `recovery_codes` now has repository behavior for one-time HMAC-only codes,
  15-minute limited recovery sessions, email-OTP fresh auth, recovery-code
  rotation and controlled `vpn_credentials | account_lockdown` reissue.
  Recovery scope is server-enforced and cannot read normal subscription or
  managed-profile material before reissue. This behavior is not deployed and
  is not production proof.
- `antiabuse_events` now has repository behavior for trial-start and API
  security signals. Valid client IPs are normalized; code caps the raw-IP
  deadline at 72 hours, full-IP HMAC at seven days and IPv4 `/24` or IPv6 `/64`
  HMAC at 90 days. A dedicated worker makes fields eligible one hour early,
  runs bounded PostgreSQL `SKIP LOCKED` chunks outside the asyncio event loop
  and retries after one second while backlog remains. It also clears covered
  legacy `security_events.client_ip` and
  `users.app_last_ip` fields without deleting their audit rows. This behavior
  is not deployed and worker availability is not production proof. These are
  operational deadlines, not an in-database TTL: worker outage or persistent
  backlog is a release-blocking incident.
- `account_entitlement_grants` is the UUID account-foundation ledger. The
  pre-existing `entitlement_grants` table remains an untouched legacy
  activation-key history with integer IDs; migrations and rollback retain it
  separately instead of rebuilding it. Entitlement-authority cutover and
  automated antiabuse decisions are not live. A hard lock can be written
  through the antiabuse service only with an explicit operator ID and reason;
  no automatic rule may hard-lock an account.
- `scripts/migrate_sqlite_to_postgres.py rehearse` now provides a fail-closed
  synthetic rehearsal path: SQLite backup API plus `quick_check`, confirmed
  reviewed source-count manifest, disposable `_rehearsal` target,
  schema/bootstrap migrations, streaming copy, account backfill, critical
  orphan checks, explicit-ID sequence synchronization and a sanitized atomic
  JSON report. Reset, copy, backfill and invariants share one target data
  transaction. Sequences sync once after explicit copy so generated backfill
  inserts cannot collide, then again after commit; PostgreSQL sequence state is
  never described as rollback evidence. Rerun compares both report and streamed
  target-content digests. This local contract is not a redacted-production
  rehearsal or restore proof.

Predeploy account-foundation gates:

- `MANUAL_OWNER_TEST`: run a PostgreSQL rehearsal against a redacted production
  snapshot and retain the sanitized report, row counts, review counts, sequence
  states and an approved backup/restore result. Synthetic SQLite-to-SQLite
  evidence does not satisfy this gate.
- `MANUAL_OWNER_TEST`: prove the row/per-user/global lock order and no-upgrade
  behavior with two real PostgreSQL connections under concurrent projection,
  bind and first-start scenarios; local contract tests are not live concurrency
  proof.
- `MANUAL_OWNER_TEST`: approve the rollback position before migration or
  deployment, including backup/restore evidence and the decision not to drop
  additive account tables during code rollback.
- `MANUAL_OWNER_TEST`: verify preservation of public auth, entitlement,
  payments, support, bonus behavior, `users.tg_id` compatibility and the
  current stateless bearer before and after the rehearsal.
- `MANUAL_OWNER_TEST`: update Android and Windows secure storage to retain the
  one-time refresh token, rotate it atomically and fall back to recovery rather
  than repeating bootstrap.
- `MANUAL_OWNER_TEST`: the repository email-OTP and one-time recovery exchange
  do not authorize deploy by themselves. Exact Android/Windows reinstall,
  lost-credential, atomic refresh persistence, logout, recovery, reissue and
  device-revoke paths must pass before the repeated-bootstrap guard is enabled.
- `MANUAL_OWNER_TEST`: configure a dedicated `ANTIABUSE_HMAC_SECRET`, retain
  explicitly versioned previous peppers only for their active comparison
  windows, and prove `portal-worker` runs continuously with zero overdue
  backlog in the production topology.
- `MANUAL_OWNER_TEST`: inspect proxy/application logs and individual-user admin
  access so the database cleanup is not misrepresented as complete raw-IP
  deletion outside the covered first-party columns.

Not source of truth:

- local SQLite files
- archived test DBs
- audit snapshots
- generated frontend caches
- stale root markdown notes
- retired client-reference workspaces when treated as if they were active client canon

## Transport Rollout Control

The additive rollout model keeps the current Reality path intact while introducing a controlled app-first primary path.

Rollout rule:

- `legacy_reality_fallback` stays the rollback and manual/export baseline transport profile
- `grpc_443_primary` is the new app-first primary profile for allowlisted cohorts and premium-node canaries
- `reserve_xhttp_cdn` is the hidden reserve profile prepared on eligible nodes for emergency allowlisted fallback; it is not part of the default public rollout in this wave
- `ru_bridge_relay` is the RU reachability bridge for allowlisted, incident-promoted, or temporary default cohorts; it exposes countries first, then nested direct/`Белые списки` choices through configured bridge endpoints for non-US targets, while US stays direct-only. `mini` remains the legacy primary endpoint, and additional RU/RU-SPB bridge endpoints can appear as type 2/type 3 choices without replacing `mini`.
- sing-box subscription routing keeps RU IP ranges direct, blocks the mirrored adblock rule set, and routes BitTorrent to a hidden RU selector when at least one RU delivery node is present; if no RU delivery node is available, BitTorrent falls back to the legacy direct behavior
- `operator_lab` stays hidden behind allowlists and must not appear in public UI or mass session payloads
- `Naive`, `Trojan`, and `Hysteria2` are not part of the mass public payload for this wave

Operational shaping rule:

- repo-truth for node shaping lives in `infra/node-qdisc-profiles.json`
- `scripts/remote_apply_node_qdisc.py` applies and rolls back qdisc state
- `scripts/remote_node_qdisc_smoke.py` verifies that a heavy flow does not starve small HTTPS probes beyond the fixed threshold
- `infra/portal-node-qdisc.service` restores the configured qdisc after reboot

## Current Primary Flows

### App-First Client Flow

1. client generates `install_id`
2. user taps `Try free`
3. backend creates the legacy app user and synchronizes its canonical account,
   device and legacy entitlement projections
4. repository candidate creates the first `auth_sessions` row and returns the
   compatibility `session_token` field plus a short-lived `access_token`,
   one-time `refresh_token`, `session`, `client_policy`, `access`, and
   `provisioning` payloads plus a real subscription source
5. client imports and activates the profile

Deployment limit: production still returns the legacy stateless app bearer.
The rotating/recovery candidate must not be promoted before client secure
storage and exact-client recovery gates are green because repeated bootstrap
deliberately returns `device_recovery_required` once a device has session
history.

App-first contract note:

- `client_policy` is the additive cross-surface contract for routing, DNS, transport, package-catalog version, and support recovery order
- the same `client_policy` shape should be available from `start-trial`, `dashboard`, and `user` payloads
- `client_policy` is populated from `AppSetting.network_rollout_config`, not from a hard-coded transport default
- public recovery order stays `POKROV app -> web cabinet -> Telegram fallback`
- managed provisioning also returns `smart_connect`, which gives the client a shortlist revision, scoring hints, and fallback metadata before it measures live RTT from the device
- the follow-up latency upload path is `POST /api/client/nodes/latency-samples`; those samples are diagnostic/operator truth and do not change the free-vs-premium pool rule

Route-mode continuation note:

- after provisioning succeeds, the client must still ask the user whether this device should optimize `all traffic` or `only selected apps`
- the saved per-device route policy should expose `route_mode`, selected app/package identifiers when applicable, and whether the chosen mode requires elevated rights on the current platform
- `Only selected apps` is a consumer split-tunneling choice, not a reason to surface raw proxy or service toggles in first-layer UI

### Web Identity And Session Continuation Flow

1. user opens marketing or cabinet in the browser
2. browser continues from an app handoff, Telegram OIDC, or email auth when delivery readiness is green
3. backend issues a browser session with `auth_origin` and linked-identity summary
4. cabinet, support, renewal, and checkout continue from that same session

Architecture rule:

- additive email auth uses a six-digit OTP valid for five minutes; password
  login remains an explicitly labelled compatibility path until the guarded
  90-day cutover window is configured and completed
- email OTP can mark an existing bound device session as freshly authenticated
  or issue a new bound session when device policy permits it
- additive email auth is a live continuation lane only while sender identity, delivery configuration, and delivery confirmation are green
- app handoff, Telegram, and email are the active browser-continuation entry families today when their readiness checks are green
- email must land in the same cabinet session and linked-identity model rather than becoming a separate account track
- public email auth depends on external transactional mail delivery and verified sender identity
- if readiness fails, browser email entry must return to a truthful unavailable state instead of promising working verify or reset mail
- cabinet entry copy should continue the shared product story rather than re-pitching the product like another landing page
- cabinet and admin shells must keep explicit navigation back to the marketing site and standard cabinet entry

### Telegram Linking And Reward Flow

1. app-first account requests Telegram linking
2. backend issues a one-time deep link to `@pokrov_vpnbot`; the handoff expires
   after 15 minutes and stale rows are retained only as inactive audit history
3. bot links Telegram identity to the app-first account, except the configured admin Telegram identity cannot be bound to a non-admin app/email account
4. after returning from Telegram, the app re-reads the authenticated subscription
   projection before showing the linked username; Telegram does not supply email
5. app or web surfaces may call read-only subscriber status check
6. reward grant still happens only on the explicit claim API
7. backend validates membership in `@pokrov_vpn`
8. backend grants a new account-owned `+5 days` once when eligible; issued legacy `+10 days` grants remain grandfathered
9. membership loss opens `24 hours` of grace, and a due reversal removes only the unused channel interval

Linked Telegram identity supports recovery, bonuses, support context, and diagnostics. Admin API authorization must come from the authenticated admin account/session itself, not from an account's linked Telegram identity.

Paid wheel/calendar rewards are a separate account-owned flow. Both the API and
Telegram adapter call `rewards_service`; eligibility requires current paid
grant authority as well as an active paid projection, so trial/free/bonus tails
cannot mutate rewards. The state, typed grant, and durable sync job commit
together. Worker retry/manual-review and account-merge fencing keep panel drift
or alias changes from resetting or duplicating the reward.

### Checkout Continuation Flow

1. user opens public pricing or renewal continuation from marketing, webapp, or bot
2. hosted checkout sells an activation key against the canonical catalog
3. user redeems that key in the app or `webapp`
4. managed premium is refreshed on the canonical app-first account

Architecture rule:

- `marketing` owns public pricing and acquisition
- `webapp` renewal remains continuation-only and should defer to the same hosted key-first flow
- bot purchase flow remains valid, but it does not replace app-first public onboarding
- raw subscription links stay manual-recovery-only and must not reappear as the default commerce story
- payment callbacks normalize signed provider events into local statuses before fulfillment; only `paid` result events can extend access, while `failed`, `cancelled`, `refunded`, `chargeback`, `pending_verification`, and `manual_review` remain admin-visible reconciliation records without automatic access extension

### Public Web Journey

1. user lands on `https://pokrov.space/` or an indexable marketing landing page
2. marketing CTA defaults into `pokrov.space/checkout/`, while install help and cabinet entry stay secondary intent-driven exits
3. public checkout sells an activation key and sends the user toward redeem or install continuation
4. a known browser session, email auth, or app/bot handoff continues in `https://app.pokrov.space/`
5. `webapp` renders the relevant cabinet flow such as dashboard, subscription, redeem, downloads, devices, or support
6. successful redeem or renewal returns the user to the active cabinet journey

Public web rule:

- `marketing/` is the indexable discovery layer
- `webapp/` is the authenticated or session-aware continuation layer, not a second public acquisition page
- authenticated app, bot, and cabinet download payloads resolve runtime `APP_*` values through `/api/client/apps`
- the public install page resolves the cacheable, anonymous `/api/public/client-apps` projection of that same runtime source; it accepts only exact versioned POKROV GitHub assets with SHA-256 and size and fails closed without redirecting to login
- metadata icons, favicon, and share-preview assets remain build-time outputs and must be rebuilt or redeployed when derived brand assets change
- public SEO pages may vary the entry copy, but they must not create separate product rules or bypass the canonical checkout/session model

### API-Only Regression Flow

Release validation now includes a scripted API-only lifecycle contour:

1. start trial through `POST /api/client/session/start-trial`
2. load dashboard and profile snapshots
3. fetch config from `connect.pokrov.space`
4. create support ticket through `/api/tickets`
5. exercise bonus flows such as channel claim, promo redeem, gift redeem, and referral linkage
6. create a checkout order and simulate provider callback success
7. confirm renewal state, audit trail, and post-payment dashboard visibility

This contour is observe-and-verify only. It does not change cashier UI design, but it keeps backend purchase contracts trustworthy across bot, site, and app.

### Support Flow

1. user opens support from app, WebApp, or helpbot
2. the platform stores or routes the support thread
3. the shared facade selects exactly one path: disabled local fallback, legacy one-call provider helper, or bounded code-owned agent harness; legacy and harness never both call the provider
4. the harness sees only the typed policy, retrieved public-support topics, redacted six-message process memory, and redacted question; `safeDiagnostics` values, accounts, databases, attachments, keys/configs, arbitrary files, and command execution remain outside model context
5. code performs allowlisted retrieval before the model and sends only selected topic bodies, never the global KB index; the model has no tools and each eligible turn makes at most one provider request
6. fingerprint-bound public diagnostics cover WARP, location choice, route modes, notifications, trial limitations, Telegram bonus, and payment-not-applied cases before human handoff; provider failure may use only the same validated topic body
7. output schema, source provenance, actions, state, risky-action checks, success acknowledgement, fallback, and human transfer are enforced by code; missing or unsafe evidence cannot be repaired by a second model call
8. a successful ticket hint is stored as sender role `assistant`; operator responds through the current tooling, and the hint never closes or resolves the ticket

### Feedback And Review Flow

1. user leaves feedback from the app, WebApp, or `@pokrov_feedbackbot`
2. backend stores the submission for moderation
3. operator approves selected reviews for public display
4. marketing and cabinet surfaces render only featured reviews
5. visible nicknames are masked in a friendly format such as `mikh****`

## Runtime Hosts And Services

Canonical control-plane host:

- `brain`: `82.21.114.104`

Important services:

- `portal-api`
- `portal-bot`
- `portal-helpbot`
- `caddy`
- `x-ui`

Auxiliary RF hosts:

- `mini`
  dedicated RU probe vantage point plus owner-approved emergency RU bridge endpoint for non-US delivery reachability
- `rf1`
  reserve RF ingress for operator and VIP/manual access, chained onward to an EU exit

RF host rule:

- do not place control-plane services on `mini` or `rf1`
- keep `rf1` outside the default runtime delivery pool in phase 1
- `rf1` promotion remains in backlog
- owner-approved exception on `2026-06-01`: `mini` may run `ru_bridge_relay` on `tcp/443` as the legacy primary emergency bridge to enabled non-US POKROV delivery nodes; additional RU bridge hosts may be added as separate endpoint ids in `ru_bridge_relay.endpoints[]`. Keep all bridge hosts out of the standard delivery pool, keep US excluded, and keep a rollback path that disables the rollout profile without touching normal Reality delivery
- historical owner-approved exception on `2026-04-24`: the former dedicated free node (`151.245.217.23`) may retain a Telegram-only MTProto proxy on `tcp/9443`, but consumer free delivery is retired and the host has no enabled canonical delivery role; current MTProto or Xray service state requires fresh node-side evidence

## Public Hostnames And Migration Roles

Canonical public surfaces:

- `https://pokrov.space/`
- `https://app.pokrov.space/`
- `https://api.pokrov.space/`

Role split:

- `pokrov.space` is the canonical public hostname family
- `connect.pokrov.space` is the canonical config/connect host
- `pay.pokrov.space/checkout/` is the canonical hosted checkout entry
- `kiwunaka.space` is a migration compatibility layer for older subscriptions and must not be treated as a fresh-entry surface
- browser flows must prefer `api.pokrov.space` for API traffic and never rely on HTML returned from `app.pokrov.space` as if it were API JSON

Copy/config rule:

- new public and cabinet copy plus CTA text must stay centralized through `shared/copy.ts` and `copy/catalog.ru.json`; `webapp` should continue that shared story instead of inventing its own marketing voice
- locked cross-surface facts such as trial length, Telegram reward, canonical hosts, and design direction must stay centralized through `shared/product-facts.json`, `shared/public-urls.json`, and `shared/design-tokens.json`
- app-first marketing CTA priority, live/degraded email wording, and cabinet IA labels must resolve from those shared governance sources instead of drifting per surface
- public-facing marketing and cabinet language should stay calm and human-readable instead of surfacing transport acronyms, raw profile terms, or operator-facing implementation jargon
- bot, site, app, and checkout links should resolve from shared host config rather than hard-coded per surface

## Monitoring And Visibility Model

Current operational monitoring should correlate:

- canonical public hostname health
- app-first session bootstrap and dashboard health
- Telegram bot and support bot availability
- node reachability and public egress
- per-node metrics freshness, sustained resource pressure, and probe-failure reasons
- per-user observer-lite IP/node footprint and conservative `ok | watch | suspicious` state
- device and account visibility for support diagnosis

Current release validation also has to correlate:

- client localhost-listener security smoke
- routing preset smoke for `Full tunnel` and `Все, кроме РФ`
- subscription-rendered DNS defaults plus DNS split/leak checks; current sing-box subscription profiles use tunneled remote DNS by default, and client-side split-DNS remains evidence-gated
- three-vantage node checks from current operator origin, `brain`, and an RU-origin probe when available

Dashboard and user-cabinet traffic visibility must come from server-side node runtime snapshots rather than app-only telemetry.

- current traffic usage should prefer live panel/runtime counters aggregated across the user nodes
- current connection count should prefer runtime connection evidence such as active IP counts or active nodes, but `active_clients` / panel configured-client count is only provisioned-key evidence and must not be treated as online people or devices
- the cabinet/admin subscription-sharing proxy metric should be described as an estimate, not a people counter: it is derived from live IP activity and capped by recent unique IP evidence so operators can distinguish likely people-sharing from raw connection fan-out
- app device records remain useful, but they are a separate app-first visibility layer and must not be shown as the only source of "connected devices"

Admin funnel visibility is first-party only and exposes two non-interchangeable
cohorts:

- acquisition starts with `acquisition_sessions.first_touch_at` inside the
  selected period, then follows only exact handoff/order/payment/connect
  lineage; anonymous sessions without a valid handoff remain `unknown`
- product starts with distinct known users that opened the app/account inside
  the selected period; overlapping `events`, `pay_attempts`, and
  `external_orders` are deduplicated before later stages are intersected

The browser session id is stored only as a domain-separated SHA-256 digest.
Bounded first/last touch and approved event metadata are retained for `180
days`; opaque one-time cross-surface handles expire after `72 hours`. Raw
URL/query, IP, user agent, VPN destination history, message bodies, credentials,
provider payloads, anonymous ids, and customer ids are not exposed by the
aggregate admin API. The funnel is an operator diagnosis surface for “where did
people stop?” and must not replace signed payment callbacks, fulfillment
records, or Postgres entitlement truth.

Required external geography check:

- run an RU-based external probe every `6 hours`
- verify the probe host itself can reach `google.com`
- verify the current `POKROV` public hosts and API health from that external RU vantage point
- verify the current `POKROV` delivery nodes remain reachable from that external RU vantage point
- verify the RF reserve ingress state:
  - `xhttp_alive`
  - `hysteria_alive`
- keep the RU-origin release verdict limited to POKROV public hosts, API health, delivery-node reachability, and reserve ingress checks

This gives operators a useful distinction between:

- a broken probe host
- a broken node or public edge
- a hostname migration issue where legacy compatibility paths still work but canonical `pokrov.space` paths do not
- a reserve path that still works for operator and VIP access while canonical paths fail

Probe-readiness rule:

- `mini` is the preferred RU probe origin when it is healthy
- `mini` is not guaranteed to be available at all times
- RU-origin observability remains incomplete until `mini` or a replacement RU host is working again

Current admin status model for operators:

- `active`
- `expired`
- `blocked`
- `manual_test`

Manual/test cleanup rule:

- only explicit manual/test users may be deleted from admin
- real-user deletion is out of scope for the main admin surface in this wave

### RU-Origin Evidence Pipeline

The RU-origin contour is an asynchronous evidence pipeline. The browser never
runs a Russian probe and never decides freshness by itself.

```text
mini / replacement RU host
  -> ru_probe_runner.py
  -> immutable local spool (pending / blocked / quarantine / archive)
  -> ru_probe_uploader.py
  -> HMAC-authenticated internal ingest on brain
  -> ru_probe_runs + ru_probe_target_results + ru_probe_uploader_heartbeats
  -> admin read model
  -> adminapp overview, node detail, history, and release readiness
```

Boundary rules:

- `infra/pokrov-ru-probe.timer` schedules the runner at `00:00`, `06:00`,
  `12:00`, and `18:00` UTC; the uploader timer retries the spool independently
  every 15 minutes.
- The runner writes a canonical, immutable artifact before network delivery.
  A temporary API outage therefore leaves evidence in `pending` rather than
  destroying or pretending to complete the run.
- `scripts/ru_probe_uploader.py` sends the artifact and heartbeat to the exact
  `/api/internal/probes/ru-origin/*` paths. `internal_request_auth.py` verifies
  key id, subject, scope, timestamp, nonce, canonical body hash, and HMAC
  signature before the payload reaches the service layer.
- `portal_bot/ru_probe_contract.py` validates the signed contract;
  `portal_bot/ru_probe_service.py` evaluates eligibility and stores normalized
  rows. Raw secret material and arbitrary probe payloads do not cross the
  admin read boundary.
- `GET /api/admin/probes/ru-origin/latest`, `/runs`, and `/uploader-status`
  expose bounded, redacted read models. Server time owns the 7-hour run-stale
  and 45-minute heartbeat-stale decisions.
- Unheld RU run rows have a default 180-day database retention window. A run
  bound to retained release evidence receives a retention hold and is excluded
  from routine pruning.

### Release Evidence And Admin Action Services

`portal_bot/release_evidence_service.py` owns exact-candidate evidence import.
The internal importer accepts a redacted descriptor plus per-origin evidence,
keeps `current`, `brain`, and `ru` separate, rejects candidate mismatches, and
binds eligible RU evidence to its stored probe run. `adminapp` reads candidates
and readiness through `/api/admin/releases/*`; it does not manufacture a green
release verdict from local test results.

`portal_bot/admin_action_intent_service.py` owns risky operator mutations. An
intent captures actor, action, target, normalized parameters, before-state,
expected effect, confirmation contract, expiry, idempotency key, result summary,
and audit linkage. The original mutation route executes only a matching live
intent. If the response is lost, the client reads intent status instead of
blindly replaying the side effect. Redaction and allowlists apply before
before/after/result material becomes durable or returns to the browser.

These two services are deliberately separate: release evidence proves an exact
candidate and origin; an action intent authorizes one operator mutation. Neither
is a production deploy mechanism.

## Device, Telegram, And IP Correlation

The app-first model is not only about authentication. It also provides a friendlier support map than a Telegram-only design.

Operator diagnosis should be able to correlate:

- app account
- linked email identity when present
- linked Telegram identity when present
- device record
- recent `last_ip`
- current node/subscription context
- current runtime connection footprint across assigned nodes
- current traffic usage source, including whether it comes from runtime panel data or a fallback

The general admin list prefers a linked Telegram handle or a non-synthetic
account name, and shows the normalized app device name/model and platform as
secondary context. Immutable numeric/install identifiers remain available for
exact support lookup but are not the only visible identity.

This visibility supports:

- connection triage
- abuse control
- account recovery
- targeted incident response

## Public API Shape

Major currently live public and app-first routes in `portal_bot/api.py` include:

- `GET /api/health`
- `GET /api/public/plans`
- `GET /api/public/catalog`
- `POST /api/auth/telegram/web-login`
- additive email-auth rollout endpoints under `/api/auth/email/*` for register, verify, login, recovery, and reset
- `POST /api/client/session/start-trial`
- `GET /api/client/warp/status`
- `POST /api/client/warp/consent`
- `POST /api/client/warp/revoke`
- `POST /api/client/warp/rotate`
- `POST /api/client/warp/events`
- `GET /api/access-keys/status/{key}`
- `POST /api/access-keys/redeem`
- `POST /api/admin/access-keys/issue`
- `GET /api/client/promo-slots`
- `GET /api/admin/promo-slots`
- `PUT /api/admin/promo-slots`
- `POST /api/client/telegram/link`
- `POST /api/client/telegram/link/events`
- `POST|GET|DELETE /api/client/device-pairing/*`
- `GET|POST|DELETE /api/client/programs*`
- `GET /api/public/status`
- `GET /api/public/programs`
- `GET /api/bonuses/summary`
- `GET /api/bonuses/referral/summary`
- `GET /api/bonuses/history`
- `GET /api/bonuses/wheel/state`
- `POST /api/bonuses/wheel/spin`
- `GET /api/bonuses/calendar`
- `POST /api/bonuses/calendar/checkin`
- `GET /api/payments/providers`
- `POST /api/payments/orders/create`
- `POST /api/payments/orders/create-public`
- `GET /api/dashboard`
- `GET /api/client/apps`
- `GET /api/public/client-apps`
- `GET /api/nodes/status`
- `GET /api/reviews`
- `POST /api/reviews`
- `POST /api/bonuses/promo/redeem`
- `POST /api/bonuses/channel/claim`
- tickets and admin APIs under `/api/tickets` and `/api/admin/*`

Selected-feature services add three bounded state machines to the modular
monolith: one-time device pairing, manually reviewed program applications, and
operator-owned service incidents. The worker polls pending incident
compensation records, writes idempotent account entitlement grants, and leaves
panel synchronization to the existing durable grant pipeline. Public status is
read-only; user complaints and client telemetry cannot create incidents or
grants.

App-facing wheel and calendar routes are intentionally disabled by default.
The client may surface truthful unavailable/preview state while flags are off.
When `BONUS_WHEEL_ENABLED` or `BONUS_CALENDAR_ENABLED` is turned on, mutation
routes write account-owned reward state, one typed `EntitlementGrant`, and an
idempotent durable panel-sync job in one transaction; compatibility
`RewardClaim`/achievement rows do not authorize access. The response returns a
fresh summary and `sync_state`. The client must expose controls only from
backend state, render wheel sectors without weights, and fail closed when
sector/state payloads are missing or unknown.

The backend exposes both public/app-first surfaces and a broader Telegram/admin-oriented API set. Keep docs aligned with the actual route inventory in `portal_bot/api.py`.

Product telemetry is first-party and uses one bounded Event Envelope V1 across
app, site, bot, payment and worker stages. `event_id` makes ingestion
idempotent; occurrence and receive times remain distinct; errors carry a safe
category/code/stage/duration/retry shape. Provider-confirmed payment and durable
entitlement records remain the authority for access. Telemetry never becomes a
source for browsing history, destination capture, private support text or raw
connection material.

The main Telegram bot is an acquisition/recovery adapter, not a second cabinet.
Its first level contains one state-aware next step, downloads, login/link code,
activation and short help. Device lists, payment history, referrals, settings,
manual URLs and historical Telegram payment compatibility remain outside the current main
menu. The web cabinet continues to own full account management.

`news_draft_service.py` reads a bounded HTTPS RSS allowlist once per day only
when explicitly enabled. It stores source name, item title/link, timestamps and
safe run aggregates, not article bodies. Duplicate items do not re-enter the
review queue. Manual L2 approval creates a `LiveUpdate`; autonomous publication
or Telegram posting is not part of the worker.

Current release-gate smoke focus should cover:

- `GET /api/health`
- `POST /api/client/session/start-trial`
- email-auth register / verify / login
- Telegram OIDC start and finish
- bot token handoff into webapp
- `GET /api/client/apps`
- anonymous `GET /api/public/client-apps` with exact APK/EXE metadata
- `GET /api/payments/providers`
- checkout continuation from session or ticket

## Telegram Registry

Canonical bot usernames:

- main bot: `pokrov_vpnbot`
- support bot: `pokrov_supportbot`
- feedback bot: `pokrov_feedbackbot`

Current channel state:

- verified public channel: `@pokrov_vpn`
- bonus verification is live
- `@pokrov_vpnbot` is an administrator in that channel
- `swazist_bot` and `portal_service_bot` are legacy usernames that are officially disabled and must not be treated as active production bots
