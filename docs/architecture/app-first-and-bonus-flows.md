# App-First And Bonus Flows

Last updated: 2026-08-31

## Document Status

This file is living source of truth for app-first identity, Telegram linking, and Telegram reward logic.

## Goal

Document the current app-first identity model, account-scoped onboarding state,
first-connection evidence, automatic username sync path, checkout continuation,
node-pool assignment, and the live Telegram bonus flow used by the active
`POKROV-app/main` client line, with legacy `POKROV VPN` labels treated as
compatibility or archival leftovers only.

## Wave 0 Rework Target

The rework canon now freezes the following target identity and access model for later code waves:

- `POKROV-app/main` is the only active client lane expected to implement this contract family
- `app-next/` and `external/client-fork/app/` are retired bootstrap or rollback references only and must not override the active contract
- one canonical `app-first` account links `install_id`, email, Telegram, devices, and activation keys
- store-app entry remains the premium-trial path: the first valid device gets `5 days` of premium trial without mandatory registration, then moves to `expired_or_blocked` until purchase or another premium grant
- site email signup is a live additive browser continuation lane when `/api/auth/email/status` reports public delivery readiness; it must not be described as a premium-trial replacement for the app-first path
- browser continuation can start from app handoff, Telegram, or email; all three land in the same cabinet session family instead of creating competing account tracks
- Telegram is recovery, linking, restore-premium, bonus, community, support fallback, and bot-side fallback commerce, not the primary login or commerce wall
- commerce becomes `buy key -> redeem key -> managed premium`; raw subscription links are hidden from default UX and exposed only in the authenticated Apple manual-connection path
- consumer free-tier delivery is retired and fail-closed by default (`FREE_TIER_ENABLED=false`); legacy `free_standard`/`free_soft` roles remain only as rollback and cleanup compatibility and must never fall back to paid nodes
- `GET /api/dashboard`, `GET /api/user/*`, `POST /api/client/session/start-trial`, and `GET /api/client/profile/managed` should converge on one linked-identity and access-state contract that also carries redeem eligibility, promo-slot payloads, and the hidden transport matrix
- normal consumer UI shows one logical location; ordered transports such as `vless_reality -> vmess -> trojan -> xhttp` remain hidden rollout detail rather than mass-UI choice

Client-canon note:

- this document describes the active contract that `POKROV-app/main` must implement
- any retired bootstrap or rollback docs that still describe older surfaces are reference-only and must not override this contract

## Current Canonical Account Foundation

Deployment status: this additive foundation is repo-implemented on
`codex/market-ready-cis-integration` but is not deployed. The live platform
continues to use legacy auth, entitlement, payment, support, bonus,
`users.tg_id` and stateless-bearer behavior until the manual predeploy gates
below are complete.

- `accounts.id` is the additive immutable UUID account root.
- `users.account_id` maps current legacy user rows into that root while
  `users.tg_id` remains the live compatibility key for bot, panel, payment and
  current public API responses.
- first app trial, email registration/verification and Telegram first-touch
  synchronize typed identities, a real `account_devices` row and a
  non-authoritative legacy entitlement snapshot in the same transaction.
- existing rows are backfilled once per database behind the
  `migration.account_foundation.v1` completion marker. Later app, email and
  Telegram writes synchronize only the affected account component. Explicit
  `linked_telegram_id` edges merge app and direct-Telegram rows without deleting
  payment, support or access history; ambiguous identity ownership creates an
  operator review row. Arrival order is deterministic: if an app row points to
  a Telegram ID before the direct Telegram row exists, the later direct row
  converges through that explicit reverse edge.
- PostgreSQL transaction advisory locks serialize the one-time projection and
  runtime projection: ordinary writes share the global projection lock and
  account merges take it exclusively. The real Telegram bind also locks its
  one-time `start_links` row and both user rows, then commits the link and the
  canonical-account merge atomically before it reports success.
- all paths use one deadlock-safe order: lock affected `users` rows in numeric
  order, acquire deterministic per-user advisory locks, then acquire the shared
  or exclusive global projection lock. Startup coordination uses a separate
  advisory key and never holds the projection lock while waiting on user rows.
  A transaction chooses the final global mode once and never upgrades a shared
  projection lock to exclusive.
- for existing legacy chains, component membership is discovered without row
  locks first, the complete ID set is locked by one numeric `FOR UPDATE` query,
  and the closure is rechecked before any global lock is taken.
- bot linking accepts only a direct app-account to Telegram pair. If either
  endpoint already participates in another link direction, the bot leaves the
  one-time link unused and sends the case to support instead of building a
  transitive `A -> B -> C` identity chain.
- the additive `auth_sessions` and `recovery_codes` tables now have
  repository-candidate rotating device-session, email OTP, one-time recovery
  exchange, limited-scope and reissue behavior, but none of it is deployed
- `antiabuse_events` receives a canonical account/device/session trial-start
  signal and versioned IP/install HMACs. The reservation and initial ledger row
  commit together; session issuance then fills the canonical session reference.
  Raw IP is capped at 72 hours, full-IP HMAC at seven days and `/24` or `/64`
  prefix HMAC at 90 days. A dedicated early-sweep worker drains covered ledger
  and legacy raw-IP fields before sleeping. This candidate behavior is not
  deployed
- `account_entitlement_grants` carries the repository-candidate premium-trial
  reservation and activation authority. The pre-existing
  `entitlement_grants` activation-key history keeps its legacy integer schema
  and rows unchanged; it is not reused as the UUID account ledger.
  `connection_evidence` is append-only, account-owned server evidence keyed
  uniquely without subscription URLs, bearer tokens, provider secrets, source
  IPs, or traffic payloads. Existing legacy snapshot grants remain unchanged
  as compatibility fallback. This candidate is not deployed
- PostgreSQL schema creation and additive migrations use the same
  `pokrov_schema_bootstrap` transaction advisory lock, preventing their
  separate transactions from overlapping during concurrent first startup.
- The repository migration rehearsal uses a consistent SQLite backup,
  reviewed source-count manifest, disposable `_rehearsal` PostgreSQL target
  confirmation, streaming table copy, direct account projection, critical
  orphan/null invariants, pre-backfill and post-commit sequence synchronization,
  and sanitized report/content digests. The reset/copy/backfill/invariant data
  phase is transactional; schema preparation and sequence state are reported
  separately rather than described as rollback-safe.

Predeploy account-foundation gates:

- `MANUAL_OWNER_TEST`: PostgreSQL rehearsal on a redacted production snapshot
  with a retained sanitized report, row counts, merge-review counts, sequence
  states and approved backup/restore evidence. Local synthetic fixtures are not
  production proof.
- `MANUAL_OWNER_TEST`: real two-connection PostgreSQL concurrency proof for
  projection, Telegram bind and concurrent first startup; local SQL-order tests
  do not claim live deadlock proof.
- `MANUAL_OWNER_TEST`: owner approval of backup, restore and code/data rollback
  steps before any production migration or deploy.
- `MANUAL_OWNER_TEST`: before/after preservation checks for public auth,
  entitlement, payments, support, bonus, `users.tg_id` compatibility and the
  current stateless bearer.

## App-First Trial Flow

1. client creates and persists `install_id`
2. client collects soft device context
3. user taps `Try free`
4. client calls `POST /api/client/session/start-trial`
5. backend creates:
   - legacy app-user compatibility row
   - canonical UUID account projection
   - real device registry row
   - current compatibility bearer session
   - one account/device trial reservation expiring after `5 days`
6. backend returns:
   - `session` payload with canonical session fields
   - `client_policy` payload with routing, DNS, transport, and recovery defaults
   - `access` payload with `reserved` or `active` trial state plus reservation
     and activation timestamps
   - `provisioning` payload with explicit readiness state
7. client silently imports the profile
8. client asks how this device should be optimized before the first live route activation
9. client saves the per-device route policy and then switches to `Quick Connect`

Contract rule:

- caller-controlled `trial_days` is no longer part of the canonical client contract; the backend always enforces the fixed `5-day` trial from shared truth
- the provisional credential remains usable during the `5-day` reservation,
  but `activated_at` and the effective expiry are written exactly once only
  from authenticated internal observer evidence; expiry is
  `first_valid_evidence_at + 5 days`
- `/api/connect/confirm`, `clicked_connect`, `connected_ok`, and other
  client-authored events remain diagnostics only and cannot activate access
- replayed observer batches/evidence return idempotently without moving expiry;
  an unactivated stale reservation projects to `expired_or_blocked` while paid and
  unrelated active grants or current paid/bonus `User` projections remain
  untouched
- canonical-account merge keeps exactly one trial authority: active beats
  reserved, then expired, reversed, superseded, and unknown states; the earliest
  status-specific effective timestamp and grant ID break ties. Every other
  `source=premium_trial` row leaves the unique-index source set and is retained
  as `premium_trial_superseded` audit history with prior status/reversal and
  winner provenance; rerunning the merge is idempotent
- observer evidence timestamps and evidence keys use canonical UTC. The stable
  key uses owned node plus immutable resolved legacy user identity, not mutable
  canonical account ID, so post-merge/different-batch replay remains one row
- panel provisioning stays retryable and outside the irreversible ledger
  decision; panel failure does not create connection evidence
- initial panel convergence is limited to four seconds. A timeout returns the
  existing `pending_sync` contract without rolling back the committed account,
  device, session, or trial reservation
- each successfully converged node records its `UserNode` confirmation before
  the aggregate wait reaches a slower peer. A later managed-profile request may
  use only that confirmed healthy subset while the unavailable node remains
  pending; one slow node must not erase completed provisioning evidence or turn
  the whole first run into a false total failure
- the backend must return the same `client_policy` contract from `start-trial`, `user`, and `dashboard` flows so the app can reconcile defaults without guessing

### Account Experience And First Connection

`account_experience_state` is small account-owned UX state. It is not an
entitlement, payment, trial, or connection-evidence ledger.

- `GET /api/user/{tg_id}` returns additive `experience.onboarding`,
  `experience.first_connection`, and `experience.next_step` fields.
- Cabinet onboarding completion or skip is written through
  `POST /api/account/experience/onboarding`; browser storage must not decide
  whether another device or browser sees the onboarding again.
- The native welcome shown before an account exists remains install-scoped by
  necessity. After the runtime really reaches `RuntimePhase.running`, the
  active client reports runtime UX state and marks account onboarding complete
  through the authenticated app session.
- `POST /api/client/runtime/stats` may set the first connection state to
  `reported`. That client-authored fact can drive copy and progression only; it
  cannot activate a trial, grant days, or prove a working route.
- Signed observer ingestion remains the only path to `verified`. It records
  append-only `connection_evidence`, stores the earliest verified timestamp,
  and preserves the existing trial activation rules.
- The local first-connect hint is completed only after the runtime reaches
  `running`; a tap, permission prompt, timeout, or failed connect leaves the
  milestone pending.
- Account merge preserves the strongest onboarding result (`completed`, then
  `skipped`, then `pending`) and the earliest reported and verified connection
  timestamps.

Current `client_policy` contract:

- `routing_mode_default`: `all_except_ru`
- `transport_profile`: `legacy_reality_fallback`
- `transport_kind`: `reality`
- `engine_hint`: `singbox`
- `profile_revision`: rollout-derived profile revision string
- `dns_policy`: `ru_direct_split`
- `route_mode_default`: `all_traffic`
- `route_mode_choices`: `all_traffic`, `selected_apps`
- `route_mode_requires_elevation`: platform-specific elevation hint for the default or chosen route mode
- `route_mode`: persisted current per-device route mode
- `selected_apps`: persisted package/process identifiers for the current split-tunnel choice
- `requires_elevated_privileges`: persisted current elevation requirement for the chosen route mode
- `route_policy.mode`: normalized mirror of the current `route_mode`
- `route_policy.selected_apps`: normalized mirror of the current `selected_apps`
- `route_policy.requires_elevated_privileges`: normalized mirror of the current elevation requirement
- `POST /api/client/route-policy` rejects `route_mode=selected_apps` with an
  empty normalized `selected_apps` list as HTTP `422` with stable code
  `selected_apps_required`; it leaves the prior persisted policy unchanged.
- `package_catalog_version`: versioned Android direct-app catalog stamp from shared facts
- `ruleset_version`: versioned routing/ruleset stamp from shared facts
- `support_context.transport`: `legacy_reality_fallback`
- `support_context.routing_mode`: `all_except_ru`
- `support_context.ip_version_preference`: `ipv4_only`
- `support_recovery_order`: `app`, `web`, `telegram`
- `warp_policy`: sanitized enhanced-privacy/WARP metadata only; it may expose
  `enabled`, `runtime_ready`, `state`, `mode`, `source`, and
  `wireguard_config_available`, but must not expose WireGuard keys, account
  IDs, access tokens, license keys, or generated config material

Emergency readiness is prepared after the normal app-first session proves
`trial_premium` or `paid_unlimited`. The authenticated client may request
`POST /api/client/emergency-network/offline-bundle` with
`precache_only=true`; the backend rechecks access and returns a device-bound
signed catalog plus all fresh or still-valid signed last-known-good
reserve/chain profiles even before an outage. That precache does not claim the
device is in RF: the client keeps it hidden until a trusted RU observation or
the person's explicit `Ограниченная сеть` confirmation. The encrypted copy may
then run without the control plane until the earliest signed account, catalog,
eligibility, or seven-day boundary. This is not an offline signup or
fresh-device authorization path.

First-run route-mode choice:

- the client must show exactly two first-layer consumer choices: `Optimize everything on this device` and `Only selected apps`
- `Optimize everything on this device` is the default public path and stays `TUN`-first
- `Only selected apps` is the split-tunneling path and must write per-device app/process selection state instead of revealing raw proxy or service controls
- An empty selected-app set is invalid: the API must not persist it for
  `selected_apps`, and the client must block connect/sync and direct the user
  to choose at least one app. It must never degrade to a device-wide tunnel.
- the chosen mode must round-trip through backend-owned `route_mode`, `selected_apps`, and `route_policy.*` fields so `start-trial`, `dashboard`, and recovery flows all agree on the live device state
- Windows should use a known-app or executable picker; Android should use an installed-package picker
- current P3 client work may use manual app/process identifiers as a bridge; Android app-managed profiles map selected package identifiers into sing-box `include_package`
- native Android package picking and Windows process/exe picking remain follow-up work; raw rule editing must stay outside normal consumer UI
- the saved route-mode choice must remain editable later from a dedicated route-mode screen rather than only through hidden advanced settings

Rollout note:

- `AppSetting.network_rollout_config` resolves the transport profile for app-managed session and profile payloads
- `GET /api/client/profile/managed` is the primary app-managed provisioning endpoint and returns a manifest with `version`, `profile_revision`, `transport_profile`, `transport_kind`, `engine_hint`, `config_format`, `config_payload`, `fallback_order`, `support_context`, and `warp_policy`
- Its optional `fallback_from_revision` query requests only the already
  advertised ordinary TCP/REALITY fallback of a currently authorized
  `awg2_lab`, `awg31_lab` or `hy2_lab` device profile. The exact current lab
  revision must match, otherwise HTTP 409 is returned before rendering.
  Device authentication, entitlement/node eligibility and normal control-panel
  provisioning still apply. The per-request effective policy identifies
  `legacy_reality_fallback` and revision
  `<source-revision>:fallback:legacy_reality_fallback`; route/DNS policy fields
  are retained. This request does not modify cohort selection or rollout state.

- managed-profile `warp_policy` is the only app endpoint allowed to carry
  optional backend-provisioned WireGuard config/account material, and only when
  that optional material lane is `runtime_ready=true`; public `client_policy`
  copies stay sanitized
- backend-owned WARP material is stored per user/install in `warp_materials`
  using encrypted-at-rest WireGuard/account payloads; rollout-level WARP
  material remains a compatibility fallback and must not become the default
  long-lived source for real credentials
- `PUT /api/admin/client/warp/material` is the operator provisioning endpoint
  for scoped WARP material; responses expose only redacted material metadata,
  a material hash, and sanitized WARP status, never raw WireGuard/account data
- WARP material provisioning and app-requested rotation are rate-limited through
  `WARP_MATERIAL_PROVISION_LIMIT_PER_HOUR` and
  `WARP_ROTATION_LIMIT_PER_HOUR`; rate-limit hits are recorded as sanitized
  `WarpEvent` rows for operator visibility
- active WARP material older than `WARP_MATERIAL_MAX_AGE_HOURS` is treated as
  `material_stale`; stale material must not be returned in managed profiles
  until re-provisioned
- the app must treat managed-profile WARP material as optional capability data,
  not automatic consent. The default runtime path is client-local Hiddify WARP:
  Hiddify `warp.enable=true` is allowed after explicit local user consent even
  when the backend has no server-managed WireGuard material.
- app-facing WARP lifecycle state is backend-owned through
  `GET /api/client/warp/status`, `POST /api/client/warp/consent`,
  `POST /api/client/warp/revoke`, `POST /api/client/warp/rotate`, and
  `POST /api/client/warp/events`; the backend is the consent/event ledger, but
  it must not reject client-local consent solely because server-managed
  WireGuard material is absent.
- WARP lifecycle routes write `WarpEvent` ledger rows for consent, revoke,
  rotation request, and runtime fallback/error events; request/ledger metadata
  must be sanitized so WireGuard keys, account tokens, subscription URLs, and
  bearer-like material are never stored in this ledger
- `GET /api/admin/client/warp/summary` exposes only redacted operator
  telemetry: material counts, active consents, lifecycle counters, last runtime
  state/reason, per-state counts, and recent runtime event headers without
  client messages or raw metadata
- allowlisted carrier or cohort overrides may switch app-managed flows to `grpc_443_primary` without changing the public endpoint set
- one rollout-selected node transport may expose multiple public address choices through normalized `delivery_endpoints[]`. The generated sing-box profile keeps the stable logical country selector used by Smart Connect and nests the labeled address choices below it; Happ, Clash, and raw Reality compatibility exports render one entry per address. All choices reuse the same node-local transport identity and do not create duplicate provisioning or capacity rows
- allowlisted carrier or cohort overrides may switch app-managed flows to `ru_bridge_relay` during a RU reachability incident; that manifest keeps countries as the top-level choice, nests `Обычный` and configured `Белые списки` bridge endpoint choices under non-US countries, and leaves US as direct-only. The legacy top-level single-bridge fields continue to describe the primary `mini` bridge for older readers, while `ru_bridge_relay.endpoints[]` can add RU/RU-SPB type 2/type 3 choices by stable `id`.
- the native `GET /api/client/locations` catalog mirrors those choices through an additive per-city `variants` list: stable `direct` / `Обычный` is always present, and each usable bridge endpoint contributes only its stable id, short label, and short consumer description. Bridge variants are omitted when rollout is disabled, endpoint material is invalid, the city is excluded or outside a non-empty allowlist, its required transport is unavailable, or the endpoint identifies the same exact delivery node by stable id/configured host; no host, port, Reality key/short id, hidden outbound tag, or raw config enters this projection.
- managed provisioning now also returns a `smart_connect` contract with shortlist candidates, fallback metadata, rejection counts, and scoring hints
- node-backed managed provisioning gives panel synchronization and runtime reads
  one shared eight-second budget, gives panel sync a seven-second sub-budget,
  and runs them concurrently. Incomplete sync stays `pending_sync` unless a
  currently eligible shortlisted node already has durable provisioning
  evidence for that user. In that bounded case the manifest and Smart Connect
  contain only the confirmed subset and return `ready` with `sync_ok=false` and
  `readiness_source=confirmed_mapping`; successful live sync returns the current product
  pool with `readiness_source=live_sync`. Incomplete runtime read uses an
  unknown/zero fallback without changing either ready state into failure.
  Neither timeout becomes a connection claim, and the manifest no longer waits
  through the client's full retry window
- manual/export compatibility links stay on `legacy_reality_fallback` until a separate share-link parity wave
- `subscription_url` remains a compatibility and recovery artifact for manual import, legacy browser-visible delivery, and fallback when the managed manifest cannot be fetched
- `network_rollout_config` carries `version`, `defaults`, `carrier_overrides`, `cohort_overrides`, `reserve_xhttp_cdn`, `ru_bridge_relay`, `operator_lab`, `warp_policy`, `package_catalog_feed`, `routing_rules_feed`, and `support_recovery_order`
- `defaults` normally keep `routing_mode_default=all_except_ru`, `transport_profile=legacy_reality_fallback`, and `dns_policy=ru_direct_split`; incident response may temporarily promote `transport_profile=ru_bridge_relay` with rollback to `legacy_reality_fallback`
- overrides may only change `transport_profile`, `dns_policy`, `routing_mode_default`, and `ip_version_preference`
- `operator_lab` is allowlist-only and must stay out of public UI and mass session/profile payloads
- `awg2_lab` and `awg31_lab` are separate, exact-contract operator-lab profiles;
  neither profile silently upgrades or downgrades to the other
- both AWG profiles default to disabled with the server-side kill engaged, require
  an authenticated allowlisted account and device, and expire independently;
  missing, stale, malformed, digest-mismatched or server-not-ready material fails
  closed instead of falling back to a public or raw subscription profile
- compatibility or Telegram account credentials without an active device claim
  cannot receive a secret-bearing AWG managed profile, even when the legacy
  account row still has a matching install id
- AWG lab material is device-bound and encrypted at rest with a dedicated
  environment secret. Public subscriptions, location payloads, diagnostics,
  logs and operator summaries expose no private key, pre-shared key, raw config
  or endpoint payload
- `awg31_lab` consumes only the pinned official AWG 3.1 dependency through the
  typed `pokrov.awg31.endpoint.v1` contract. It is not a POKROV cryptographic
  fork, is not part of the immutable 1.2.0 candidate, and has no production,
  physical-device, mobile-origin or real-server interoperability claim until
  those exact checks are run and retained

Smart-connect contract:

- For node-backed transports, `GET /api/client/profile/managed` returns a shortlist revision plus `smart_connect.shortlist`; its material contains only those shortlisted nodes and returns `503 No eligible nodes` when the shortlist is empty
- Device-bound `awg2_lab` and `awg31_lab` are not node-backed: managed issuance bypasses Smart Connect and the ordinary node shortlist, ignores `selected_node_code`, and returns `smart_connect: null`. The typed per-device material and its own rollout/material gates remain fail-closed
- device-bound `awg2_lab`, `awg31_lab`, and `hy2_lab` do not call the legacy
  catalog-panel synchronization/runtime path during issuance; those unrelated
  panel calls cannot delay or authorize lab material
- premium users can receive up to `SMART_CONNECT_SHORTLIST_LIMIT` eligible non-free nodes, default `8`; expired users receive no delivery shortlist
- the shortlist rejects disabled, draining, unhealthy, stale, missing or dataplane-down, saturated, high-loss/retransmit, `cpu_percent >= SMART_CONNECT_CPU_REJECT_PERCENT`, transport-incompatible, and rollout-blocked nodes while `CAPACITY_AWARE_NODE_SELECTION=true`; neither explicit selection nor automatic selection may fall back to a rejected node
- shortlist items expose canonical `outbound_tag`, `health_score`, `cpu_percent`, `panel_latency_ms`, `backend_penalty`, `cpu_penalty`, `capacity_state`, `capacity_score`, `tx_ratio`, `tx_mbps`, `provisioned_clients_count`, `online_connections_hint`, and an internal `probe.host` / `probe.port` target for app-side RTT checks; `outbound_tag` identifies the unique direct proxy that must belong to the returned final selector
- the client asks `GET /api/client/nodes/candidates`, performs best-effort RTT probes, posts the result to `POST /api/client/nodes/select`, and promotes the selected `outbound_tag` inside the already authorized managed profile before materialization; one bounded `GET /api/client/profile/managed?selected_node_code=...` refetch is allowed only when local identity mapping cannot be proven
- the selection score is capacity-aware: `effective_score = rtt_ms + dataplane_rtt + cpu_penalty + backend_penalty + network_pressure`, with lower scores preferred; low `health_score` adds backend penalty but does not by itself hard-reject a node while dataplane and explicit capacity checks remain healthy
- stickiness stays active with a default `20%` threshold so the app does not flap between nodes on tiny wins
- explicit `UserNode` mappings are provisioning/history state; they may bound
  a timeout response to a currently eligible confirmed subset, but successful
  successful live synchronization must restore the current product pool so premium-grade
  users are not permanently trapped on one or two old nodes
- `POST /api/client/nodes/latency-samples` remains compatibility telemetry and must not be the only node-selection API
- `GET /api/client/subscription/preview` is an authenticated, raw-config-free support/debug view of resolved subscription format, node order, and excluded-node reasons
- the follow-up upload paths store `install_id`, `carrier`, `platform`, accepted RTT samples, selected node, previous node, and whether stickiness was applied without exposing raw telemetry in consumer UI

## App Session Model

Important concepts:

- `install_id` is a stable client-side identifier, not a reusable credential
- device context supports diagnostics and abuse control
- the repository candidate issues a short-lived device-bound access token plus
  one-time rotating refresh credential from first app bootstrap
- signed tokens carrying `session_id` are checked against `auth_sessions`, the
  canonical account `auth_epoch`, and the real device `credential_version` on
  every authenticated request
- browser, Telegram, email and retained compatibility bearers without
  `session_id` continue through the existing stateless verifier until their
  separate cutover
- Telegram is optional and not required for account creation

The rotating-session and recovery code is implemented on the integration
branch but is not deployed. The current production beta still depends on the
legacy bearer behavior. The candidate must not be deployed until updated
clients persist refresh tokens atomically and exact Android/Windows recovery,
reinstall and revoke paths pass.

Repository session rules:

- first `POST /api/client/session/start-trial` returns the existing
  `session_token` field plus `access_token`, one-time `refresh_token`, expiry
  fields, `session_id`, `refresh_family_id`, canonical account UUID and real
  device UUID
- later calls for the same `install_id` return
  `409 device_recovery_required`; `install_id` is never accepted as proof of
  possession, and the history guard runs before device metadata writes or panel
  synchronization
- `POST /api/client/session/refresh` consumes one refresh token and returns the
  next pair without extending the absolute family expiry
- refresh reuse revokes the whole family and returns
  `401 refresh_reuse_detected`
- `POST /api/client/session/revoke` revokes the current family but leaves the
  device registered
- a successful one-time device-pairing claim issues a new device-bound session
  for the existing canonical account; the client replaces its abandoned local
  trial session only after that claim succeeds and then re-reads subscription
  identity before declaring the profile restored
- app-derived cabinet handoff and cabinet-session tokens retain source
  session/device/epoch binding and are invalidated with that source family
- `GET /api/client/devices` reads the real registry; `DELETE` requires fresh
  auth, increments device credential version and revokes every bound session
- device revoke and account lockdown also invalidate active AWG2/AWG3.1/HY2
  material for the revoked account/install pairs in that transaction. A fresh
  login cannot restore those retained encrypted rows. Prior rotation history
  and other devices remain unchanged. For configured owned AWG targets, the
  existing worker performs separate persistent/live peer removal after committed
  revocation and retries failed server delivery. It also retires expired material
  and expired or disabled device/account access. A rotated key without an active
  copy becomes revoked, retaining ciphertext and the earlier timestamp. Shared
  legacy keys remain explicitly blocked until per-device migration. Database
  revocation alone is not proof of server removal; HY2 server enforcement remains
  separate. See the operational target configuration in
  [deployment and access](../operations/deployment-and-access.md).
- raw refresh credentials are never written to the database or logs; only a
  SHA-256 digest of a high-entropy token is retained
- `POST /api/auth/email/otp/start` returns an enumeration-resistant generic
  response and sends a six-digit code with an exact five-minute lifetime only
  for a verified identity
- `POST /api/auth/email/otp/finish` consumes that code once, can freshen the
  current bound session, and can issue a replacement device session when
  device policy permits it
- `POST /api/client/recovery-code/rotate` requires recent fresh auth, revokes
  prior active codes and returns `PKR-XXXX-XXXX-XXXX` once; only versioned HMAC
  and a masked hint are stored
- `POST /api/client/recovery/exchange` consumes the code once and creates a
  15-minute `recovery` session. Server-side scope enforcement blocks normal
  subscription, managed-profile and networking APIs before reissue
- `POST /api/client/access/reissue` accepts `vpn_credentials` or
  `account_lockdown`; both rotate subscription material and request managed-key
  rotation, while lockdown also increments account epoch and revokes other
  devices/sessions. Paid entitlement dates are not changed

## Preferred Device Identity Inputs

- `install_id`
- `device_name`
- `platform`
- `model`
- `app_version`
- soft fingerprint signal
- `last_ip`

This supports a friendlier device model than a Telegram-only account design.

## Username Sync Semantics

- app-first accounts may start with an app-side placeholder username before any Telegram identity is linked
- once Telegram or web-auth surfaces provide a real username, runtime flows should sync it automatically into the canonical account/session state
- automatic username sync is the primary path for normal operation, support context, and recovery continuation
- manual username sync remains compatibility/recovery tooling for operators and edge cases; it must not be treated as the normal happy path

## Visibility Expectations

For support and operations, the app-first account model should make it possible to inspect one connected story across:

- app account and session
- linked Telegram account when present
- device record and device name
- recent `last_ip`
- current subscription and node context

Visibility rule:

- Telegram remains optional for the user journey
- once linked, Telegram identity becomes part of the support and recovery context
- device and IP context should be used for diagnosis and abuse control, not as a public-facing marketing message
- install-scoped latency samples, carrier labels, and platform labels are operator-visible diagnostics for route quality and must not surface as raw telemetry in normal consumer UI

## Repository App-First Endpoints

Current repository backend contract. Deployment status must be checked
separately:

- `POST /api/client/session/start-trial`
- `POST /api/client/session/refresh`
- `POST /api/client/session/revoke`
- `GET /api/client/devices`
- `DELETE /api/client/devices/{device_id}`
- `GET /api/client/profile/managed`
- `GET /api/client/locations`
- `POST /api/client/nodes/latency-samples`
- `GET /api/client/warp/status`
- `POST /api/client/warp/consent`
- `POST /api/client/warp/revoke`
- `POST /api/client/warp/rotate`
- `POST /api/client/warp/events`
- `POST /api/client/telegram/link`
- `POST /api/client/telegram/link/events`
- `POST /api/client/device-pairing/claim`
- `PUT /api/admin/client/warp/material`
- `GET /api/admin/client/warp/summary`
- `GET /api/public/catalog`
- `GET /api/access-keys/status/{key}`
- `POST /api/access-keys/redeem`
- `POST /api/redeem`
- `POST /api/client/cabinet-token`
- `POST /api/auth/cabinet-handoff/exchange`
- `POST /api/admin/access-keys/issue`
- `GET /api/client/promo-slots`
- `GET /api/admin/promo-slots`
- `PUT /api/admin/promo-slots`
- `POST /api/client/telegram/link`
- `GET /api/bonuses/summary`
- `GET /api/bonuses/referral/summary`
- `GET /api/bonuses/history`
- `GET /api/bonuses/wheel/state`
- `POST /api/bonuses/wheel/spin`
- `GET /api/bonuses/calendar`
- `POST /api/bonuses/calendar/checkin`
- `POST /api/bonuses/promo/redeem`
- `POST /api/channel/subscriber/check`
- `POST /api/bonuses/channel/claim`
- `GET /api/tickets`
- `POST /api/tickets`
- `POST /api/tickets/uploads`
- `GET /api/tickets/attachments/{stored_name}`
- `GET /api/tickets/{ticket_id}`
- `POST /api/tickets/{ticket_id}/messages`

Related live surfaces also exposed by the backend:

- `GET /api/dashboard`
- `GET /api/user/{tg_id}`
- `GET /api/client/apps`
- `GET /api/nodes/status`
- `GET /api/bonuses`
- ticket endpoints under `/api/tickets`

Unified access-contract note:

- `GET /api/dashboard`, `GET /api/user/{tg_id}`, and `GET /api/client/profile/managed` now carry the same identity/access family additions: `linked_identities`, `free_caps`, `redeem_eligibility`, `promo_slots`, `hidden_transport_matrix`, and `location_matrix`
- the access-key redeem path returns the same access-state family so app, cabinet, and admin can refresh off one canonical contract
- `POST /api/redeem` is the app-facing activation facade; it supports paid access keys, legacy gift-card codes, and promo codes, returns `kind=access_key`, `kind=gift`, or `kind=promo`, and keeps raw subscription links rejected as non-account proof
- unified gift redemption routes through the existing gift-card service, preserves one-time/self-redeem/TOS/campaign guards, and returns a fresh bonus summary so the app can update Account without a second guess
- `POST /api/redeem` must reject raw `connect.pokrov.space`, subscription, and proxy URLs with structured `code=subscription_link_not_redeem_code`; those links are connection/import artifacts, not account proof

App/bot/cabinet parity smoke:

- run `python scripts/app_bot_parity_smoke.py` before a `1.0.0-beta` handoff when app-first account, cabinet, Telegram bonus, support ticket, or redeem contracts change
- the smoke is static and secret-free; it verifies the platform API endpoints, webapp cabinet/support calls, Telegram bot entrypoints, and `POKROV-app` runtime adapter paths
- real Telegram bot and live same-account parity still require owner-controlled sessions and must be reported as `MANUAL_OWNER_TEST`, not as a local automated pass

Beta rate-limit contract:

- externally reachable beta surfaces for fresh trial creation, Telegram/email auth, access-key status/redeem, unified redeem, app-cabinet handoff token/exchange, support ticket create/upload/download, payment callbacks, subscription fetches, events, and unsafe admin actions apply backend-owned per-minute throttles
- `POST /api/client/session/start-trial` throttles only fresh installs from the same origin; a repeated existing `install_id` bypasses fresh-origin throttling but returns `409 device_recovery_required` instead of another credential
- `POST /api/client/session/refresh` uses a small bucket keyed by a truncated SHA-256 refresh fingerprint plus a separate high IP ceiling for CGNAT/random-token abuse; raw refresh material never enters rate-limit identity or logs
- throttled requests return HTTP `429` with a `Retry-After` header and structured detail containing `code=rate_limited`, `scope`, and `retry_after_seconds`
- rate-limit counters store hashed fingerprints in durable `security_rate_limit_buckets` with an in-memory dev/test fallback and can be tuned with `API_RATE_LIMIT_<SCOPE>_PER_MINUTE` environment variables

## Web Login, Email Auth, And Session Continuation

Web surfaces support app-first continuation through:

- app or bot handoff into an existing cabinet session
- app handoff through `POST /api/client/cabinet-token`, which returns a short-lived signed one-time handoff token for a relative cabinet path on canonical `https://app.pokrov.space/`
- cabinet entry exchanges that token through `POST /api/auth/cabinet-handoff/exchange`, receives a `Secure; HttpOnly` cookie for `.pokrov.space`, removes the handoff token from the URL, and honors the returned safe relative `target_path`; returned bearer tokens remain a temporary compatibility path for one release window
- failed cabinet handoff exchanges must clear URL token params and show localized cabinet copy for expired, already-used, invalid, and rate-limited states instead of dropping the user into an unexplained login wall
- Telegram widget or Telegram OIDC login in browser
- additive email signup, verification, login, recovery, and reset as a live browser continuation lane when delivery readiness is green
- dashboard and checkout continuation from an existing web session

Contract rule:

- canonical API base is `https://api.pokrov.space/`
- canonical public config host is `https://connect.pokrov.space/`
- HTML responses from `app.pokrov.space` must never be treated as valid API JSON
- web login should continue the user into account or checkout, not into a dead-end landing
- app handoff, Telegram, and email are the active browser-continuation entry families today
- expired or deprecated Telegram Login Widget, Telegram OIDC, WebApp `initData`, and browser-session tokens must clear the stale browser token and show a human repeat-login CTA instead of surfacing raw `telegram_*` / `web_session_*` errors
- stale Telegram Login Widget payloads should be rejected client-side before the backend sees them; users should be guided through a fresh Telegram login attempt
- additive email auth is live only when sender identity, delivery configuration, and delivery confirmation are green; if readiness fails, the UI must degrade back to unavailable instead of promising working verify or reset mail
- additive email auth must issue the same browser session family used by the cabinet, checkout, and support flows while exposing `auth_origin` and linked-identity summary for support/admin visibility
- app cabinet handoff tokens use `auth_origin=app_cabinet_handoff`, `scope=cabinet_handoff`, and a `60..120` second TTL; they are not accepted by normal authenticated API calls until exchanged
- handoff exchange is single-use through a backend ledger keyed by token hash; after exchange, the cabinet receives a normal browser session token with `scope=cabinet_session`
- expired handoff ledger rows are retained briefly for diagnostics and cleaned opportunistically by the backend after `CABINET_HANDOFF_LEDGER_RETENTION_SECONDS` (minimum one hour, default one day)
- the additive email-auth rollout uses endpoint families under `/api/auth/email/*` for register, verify, login, recovery, and reset
- public email register, verify, and recovery can be shown as live only while transactional sender identity and delivery-confirmation/webhook visibility are live
- browser entry screens in `webapp` are continuation-first and must not become a second landing-page pitch
- new user-facing `subscription_url` values must point to `connect.pokrov.space`
- new links require a non-numeric `sub_token`; missing or numeric credentials fail
  closed and produce no user-facing URL
- legacy `api.pokrov.space/s8Kx2mP7qR4wT/...` remains compatibility-only for older imports and recovery cases
- numeric subscription lookup is disabled by default and may be temporarily enabled
  only as an observed compatibility rollback. A production cutover requires token
  backfill, exact panel `subId` reconciliation, and an owner-approved observation
  window with zero legitimate numeric fallback hits
- the same `client_policy` contract still flows through `start-trial`, `user`, and `dashboard`, but the rollout policy behind it can vary by cohort without introducing a new endpoint

## Checkout Continuation

1. user opens public pricing, renewal continuation, or bot-side purchase
2. hosted checkout sells an activation key against the canonical catalog
3. the key is checked with `GET /api/access-keys/status/{key}` and then redeemed through `POST /api/redeem` in the app or `POST /api/access-keys/redeem` on legacy/cabinet surfaces; gift-card and promo codes also use the app-facing `POST /api/redeem` facade
4. the backend refreshes managed access on the same app-first account
5. app and web surfaces reload their unified access contract from the same identity root

Checkout rule:

- public pricing starts from app-first marketing surfaces; `pokrov.space/checkout/` is the public plan and activation-key continuation route, not the first-pressure onboarding step
- payment provider readiness is contractually separate from app-first access; public checkout must remain unavailable or degraded for any route not covered by `docs/product/payment-and-access-key-contract.md` and current provider evidence
- `webapp` renewal is continuation-only and should defer to the same hosted activation-key flow
- payment return uses the bounded server projection; `paid` must be followed
  by an authenticated account refresh before the cabinet claims active access,
  and a paid/inactive mismatch exposes refresh plus support rather than
  treating payment state as entitlement
- Telegram bot billing remains valid as a secondary path; bot orders are Telegram-ticket-bound and do not collect buyer email
- raw subscription links remain hidden from public commerce and Android/Windows flows; the authenticated cabinet and Telegram bot may reveal one `connect.pokrov.space` key only for iPhone, iPad, and macOS compatible clients
- signed payment callbacks must not grant access unless the normalized local status is `paid`; failed, cancelled, refunded, chargeback, invalid-signature, and unknown/manual-review states are recorded for operator reconciliation instead of extending the account

## Subscription Delivery Semantics

Current user-facing delivery semantics:

- one private base `ключ подключения` only in the authenticated Apple manual path
- one QR built from the same base URL only when that fallback is intentionally revealed
- one key-first commerce path: buy key -> redeem key -> managed premium
- no public format split in bot, site, or first-layer webapp wording
- consumer client and cabinet flows should prefer reconnect, refresh, route-mode change, checkout, and support over raw subscription copy/edit surfaces
- the main Telegram bot exposes Apple as a device choice, but the key and QR stay behind that explicit Apple screen; Android and Windows screens contain only official-file and app-login actions
- redeem surfaces must reject or clearly explain `connect.pokrov.space` URLs as connection links, not activation keys
- payment, gift, and bonus success messages prefer app/cabinet continuation and must not paste the bearer URL; Apple users reveal it only through the dedicated copy/QR action

Compatibility note:

- `?format=plain` still exists for backend compatibility and advanced/manual recovery
- `?format=happ` exists for Happ-compatible open subscription delivery; it returns VLESS fallback lines plus Happ `custom-tunnel-config` carrying the same smart sing-box manifest, including `Белые списки` where the client version supports that parameter. For paid manual recovery when smart ranking has no telemetry-eligible node, that embedded config uses the same transport-filtered legacy fallback as its VLESS lines.
- Smart managed material remains fail-closed when no eligible node exists. For
  paid explicit legacy/manual Reality recovery only, a transport- and
  rollout-filtered fallback is allowed solely for a node rejected because its
  telemetry is missing or stale. Disabled, unhealthy, draining, non-accepting,
  saturated, or otherwise hard-rejected nodes remain excluded; free legacy
  renders remain fail-closed.
- format variants must be derived with URL query parameters inside the opened
  authenticated manual section. They must not be sent to third-party pages,
  telemetry, support artifacts, or public HTML
- those compatibility overrides must stay out of normal user-facing onboarding and CTA copy
- app-first managed flows may still receive `grpc_443_primary` during rollout, but manual/export recovery and legacy browser-visible compatibility paths stay on Reality until the share-link parity wave lands

Focused compatibility matrix to run before changing support copy:

| Client | URL format | Import result | Server list result | Connect result | Decision |
| --- | --- | --- | --- | --- | --- |
| POKROV | managed app-first delivery | owned client release proof | backend-owned locations | owned connect flow | primary client |
| Hiddify | default private URL | required proof | required proof | required proof | verified manual fallback |
| Happ | `?format=happ`; plain VLESS only as no-bridge fallback | required proof | VLESS fallback should render; `Белые списки` require client support for `custom-tunnel-config` | test direct server first, then БС where visible | best-effort with dedicated format |
| v2rayN | `?format=plain`, `?format=vless`, `?format=clash` where supported | required proof | required proof | required proof | advanced/manual fallback |

`Pokrov-client` is an owned open-source source-only lane until it has separate APK/EXE/binary release evidence. Do not present it as an official user-facing binary fallback before that gate.

## Support Ticket Continuation

1. user opens support from app, cabinet, or helpbot
2. session-backed support may create a real ticket through `POST /api/tickets`
3. cabinet/support surfaces may load the thread through `GET /api/tickets/{ticket_id}`
4. follow-up replies continue through `POST /api/tickets/{ticket_id}/messages`
5. attachment-capable browser support stages through `POST /api/tickets/uploads`, sends only the returned opaque `attachment_id` on create/reply, then fetches authenticated `GET /api/tickets/attachments/{stored_name}` only after explicit user action; raw `/uploads/support/*` static access is not part of the current contract
6. operators continue the same case through `/api/admin/tickets/*`

Contract rule:

- app-first support may start from prepared context even before a live thread exists
- web and cabinet support must be documented as a real ticket lifecycle, not as decorative form state
- attachment-capable ticket flows belong to authenticated browser and admin paths today
- staged uploads are unbound until message commit, expire after 24 hours by default, and use account-first pending count/byte quotas; admission cleanup is same-owner only, while supervised reconciliation uses bounded per-run processing and memory for global expired/orphan cleanup and never sweeps bound or legacy null-expiry history; its filesystem candidate selection still enumerates the full upload directory once per run
- upload finalization fsyncs the file and, on POSIX, its parent directory before row commit; after atomic rename, ambiguous persistence outcomes retain the final file so a committed row never loses its file, while verified rowless finals age into grace-period reconciliation
- rolling old private `support/{stored_name}` triplets are ownership/metadata checked and canonicalized, while non-private Telegram/client media remains compatible
- bound attachment access follows ticket access; recovery sessions cannot upload, bind, receive metadata, or download even when a recovery actor numerically matches the admin ID
- canonical account ownership is internal and additive; public ticket payloads retain the legacy shape
- linked app, email, and Telegram identities on one canonical account share account-owned ticket and upload history
- exact legacy Telegram fallback applies only to `NULL`-owned rows and cannot override another non-null account owner
- read-only access never changes ownership; an exact historical actor may claim an eligible `NULL` ticket only while writing with an unambiguous canonical account
- account merge retargets ticket/upload ownership without deleting, deduplicating, or moving support history
- operator delivery uses bounded deterministic linked-Telegram, enabled Telegram-identity, then real historical-ticket evidence; no target means skip with a metadata-only warning
- client UX may poll the active ticket and show lifecycle hints such as
  checking, operator reply, closed, or temporarily offline while the support
  screen is open
- client UX must not fake typing, read receipts, or operator-online presence
  while the backed contract is asynchronous ticketing

## Telegram Linking Flow

1. app-first account requests Telegram linking
2. backend issues a deep link to `@pokrov_vpnbot`
3. user opens the bot link
4. bot binds the app account to Telegram identity
5. reward and recovery logic can then use the linked Telegram account

Contract rule:

- A direct Telegram-authenticated account is already Telegram-linked; the app
  shows its safe username/status and must not issue a second bot-link code.
- Telegram linking should also refresh the canonical linked username automatically when Telegram provides one
- Linked Telegram identity is support, recovery, bonus, and diagnostics context only; it must not grant `/api/admin/*` authority to an app/email account.
- The bot must reject attempts to bind the configured admin Telegram identity to any non-admin app/email account.
- Raw `sub_token` values and `connect.pokrov.space` subscription URLs are bearer connection secrets for compatible clients only. They must not be accepted as Telegram-linking proof or as access-key redemption codes.

## Telegram Bonus Claim Flow

1. the one-time Telegram offer is available before or after the first payment;
   a trial account may use it as an acquisition reward
2. app-first account must already be linked to Telegram
3. app or web surfaces may call `POST /api/channel/subscriber/check` to verify membership readiness
4. `POST /api/channel/subscriber/check` is read-only and must never grant points or mark campaign state
5. the real reward path calls `POST /api/bonuses/channel/claim`
6. backend checks membership for the linked Telegram account
7. if membership is valid, backend grants a new account-owned `+5 days` once
8. manual accounts, an already consumed Telegram grant, or a conflicting
   pre-payment acquisition grant remain ineligible with an explicit reason

Existing issued `+10 days` channel grants are grandfathered. Membership loss
starts `24 hours` of grace; rejoin cancels grace. A due reversal marks only the
channel grant reversed, then deterministically rebuilds the account projection
from the remaining typed trial, bonus, provider-payment, and compatibility
grants. Consumed channel time remains historical, every purchased interval and
unrelated grant keeps its full remaining duration, and access stays continuous.
Paid, free, trial/referral, session, and device state are not revoked.
When a legacy snapshot contains that issued channel interval, backfill records
the component provenance and splits the snapshot at the channel interval start;
the same channel time therefore cannot survive reversal through the aggregate
compatibility baseline.

Premium addition and rebuild classify contributions explicitly. Typed
`paid_access`, `premium_trial`, and `premium_bonus` intervals extend the premium
cursor. A compatibility `legacy_snapshot` contributes only when its persisted
`sub_type`/plan metadata classifies it as `PAID`, `TRIAL`, or `BONUS`; it is a
single aggregate baseline rather than another acquisition grant. `FREE`
snapshots and free-cycle resets are retained only as rollback/cleanup
compatibility, never delay a payment/bonus start and never select
`premium_pool`.

## Bonus Summary, Referral, And Promo Flow

- `GET /api/bonuses/summary` is the app-facing bonus summary for the Profile
  surface. It includes flat compatibility fields plus nested `referral`,
  `channel_bonus`, `opening_bonus`, `promo`, `history`, `wheel`, and
  `calendar` sections plus `reward_access`, which owns the paid eligibility of
  wheel, calendar, and referral rewards. `channel_bonus.eligible` and
  `channel_bonus.can_claim` are independent because the one-time Telegram
  reward is intentionally available during the trial.
- `GET /api/bonuses/referral/summary` returns referral count, referral code,
  safe Telegram referral link, bonus days, and current points tier for the
  app-first account. The app may expose copy/share/open actions for that link;
  referral anti-abuse, bonus granting, and campaign tuning remain backend-owned.
- An active paid account that predates referral-code provisioning receives one
  legacy-compatible, unique referral code lazily on its first bonus-summary or
  referral-summary read. The same code and safe Telegram link remain stable on
  later reads. Trial, free, expired, merged, and otherwise ineligible accounts
  must not receive a code as a side effect of those reads.
- App surfaces must fail closed when the backend has not returned a real safe
  referral link: do not invent a display code, expose dead share/copy controls,
  or imply that an invitation was created. Show a refreshable unavailable state
  until the server returns the stable link.
- one referred account has at most one account-owned referrer; self-referral and
  cycles are rejected while legacy `User.referrer_id` remains a projection
- the referred friend receives no grant from install, registration, trial,
  `ConnectionEvidence`, `clicked_connect`, or `connected_ok`; their first
  successful provider payment releases one idempotent `+5 day` grant
- referrer `+10 days` is queued by that same first successful payment and
  releases once after a full `72 hour` hold; gifts and renewals do not qualify
- pending legacy referral queue rows are migrated idempotently into the same
  canonical relationship and first-payment hold using their original queued
  payment time. A row is marked `superseded_account` only after migration;
  missing or conflicting identities stay pending with bounded retry backoff so
  an old conflict cannot starve newer valid payments
- provider/order creates one durable account-owned payment grant while the
  canonical account row and normalized relationship are locked; app and bot
  projections read the same fact, and `User.first_purchase_done` is compatibility
  output rather than authority
- account-foundation backfill creates payment authority only from corroborated
  successful provider orders or Telegram platform payment attempts with
  per-order fulfillment evidence. A paid XTR attempt without that evidence becomes a
  stable `legacy_stars_payment_marker` in `manual_review`, remains repairable,
  and cannot silently claim that projection was applied. A historical
  `first_purchase_done` flag without that evidence becomes a stable
  `legacy_first_purchase_marker` in `manual_review` and cannot block the next
  genuine first payment
- Telegram platform payment confirmation and fulfillment are separate states. `PayAttempt`
  may be `paid` before the account grant exists; every replay resumes the stable
  XTR provider/order grant until its projection is durably applied, then
  retries panel provisioning. The processed marker is authoritative only when
  that applied grant exists, and provisioning never rewrites premium expiry
- after panel create or replay, the owned panel row is read back and its
  validated UUID, panel email, and `subId` become the exact local credential.
  `User`, primary `AccessKey`, applicable `UserNode`, and grant provisioning
  evidence commit atomically before the processed marker. A legacy panel lane
  with no positive database node ID is identified by its validated owned
  `node_code`: it persists the exact `AccessKey` and grant evidence without
  fabricating `UserNode(node_id=0)`. Missing both node identities or conflicting
  key provenance keeps fulfillment retryable, and no pre-generated token is
  exposed as success
- backfilled provider facts retain whether legacy fulfillment already applied
  their projection. An explicit fulfilled order, or an old paid record
  corroborated by a legacy paid projection, replays without adding duration;
  pending fulfillment remains unapplied and a later valid callback extends once
- account payment facts are normalized after backfill and merge so exactly the
  globally earliest successful `(paid_at, provider/order)` fact is first. Only
  that fact owns the referral hold; later facts are rewritten non-first, while
  already terminal reward/review state is preserved
- referral account merges preserve the strongest relationship fields and
  review state. Duplicate/self/cycle losers remain terminal `superseded`
  relationship rows under their original account IDs, with provenance
  transitions; active graph traversal ignores them and transition FK/orphan
  invariants remain valid on rerun
- account merge keeps one effective semantic `referral_friend` and
  `referral_referrer` grant per canonical reward, repairs relationship pointers,
  and retains duplicate grants as audit-visible `superseded` rows
- the Telegram channel gate applies only when a genuinely new lead requests the
  trial; payment, renewal, recovery, and support remain ungated
- `GET /api/bonuses/history` returns an app-safe, compact recent bonus ledger
  built from current platform truth: Telegram channel claim, opening campaign
  mark, promo usage, and feature-flagged wheel/calendar reward claims. It must
  not return raw subscription links, full promo codes, tokens, raw reward
  configuration, or backend event metadata.
- `POST /api/bonuses/promo/redeem` reuses the existing promo validation and
  application rules, then returns the promo result plus a fresh summary payload.
- `POST /api/redeem` also accepts promo codes and returns `kind=promo`.
- `GET /api/bonuses/wheel/state` and `GET /api/bonuses/calendar` expose
  server-owned state payloads that the app may render as safe Rewards Hub
  controls. Wheel defaults enabled with a `336 hour` cooldown; calendar remains
  disabled by default. When `BONUS_WHEEL_ENABLED` or `BONUS_CALENDAR_ENABLED` is true,
  they expose ready/cooldown/check-in state from the reward ledger.
- The wheel state exposes only ordered, validated reward-day `sectors` and
  one-use discount sectors needed for rendering. Backend-owned weights and
  probabilities remain private and must not be inferred by the client.
- `GET /api/client/promo-slots?surface=app` may feed eligible app placements
  with every enabled operator-authored promo slot in server priority order;
  the client does not silently truncate the response. Payloads may define
  optional copy, `logo|banner|media_only`, first-party static/animated/video
  media, poster/fallback, colors, audience, whole-card link, dismiss policy,
  start/end and server-aligned countdown. Media upload is admin-authenticated,
  magic-checked and content-addressed. Third-party ad SDKs, external tracking
  media, unsafe links and executable campaign payloads stay out of the app.

The bounded 1.2.0 winback placement is a stricter dynamic subtype of that
contract. App and cabinet consume one server-prioritized assignment only after
pilot, legal/channel, capacity, audience, holdout, price, schedule and quota
checks pass. The payload contains exact commercial lineage and a signed
checkout ticket. App promo impression/click/dismiss/expired events repeat that
lineage; the API rejects partial, stale or subject-conflicting values. Cabinet
uses the same assignment contract on `webapp.subscription.contextual` and
shows server price/deadline/terms/quota. Local dismiss/frequency state is only
presentation; payment success and suppression remain server-owned. Ordinary
access and offline product behavior continue when the pilot is absent, stale or
blocked.
- `POST /api/bonuses/wheel/spin` and
  `POST /api/bonuses/calendar/checkin` are app-facing, feature-flagged mutation
  routes. With flags off they return structured disabled errors. With flags on
  they create `RewardClaim` ledger rows, extend the app-first access window by
  the configured reward days, update safe achievement state, return a fresh
  bonus summary, and best-effort sync the paid-bonus access state to the panel.

## Paid Reward Authority And Durability

- `RewardAccountState` is one row per canonical `accounts.id` and owns wheel
  cooldown plus the 28-day calendar position. Neither state machine reads the
  legacy monthly paid-streak fields.
- Every awarded wheel/calendar duration is an `EntitlementGrant` with source
  `bonus_wheel` or `bonus_calendar`. `RewardClaim` and legacy achievement rows
  remain compatibility/history projections and cannot authorize duration.
- Eligibility is server-owned: the canonical account must be active and
  unmerged, at least one linked user projection must be active `PAID` with a
  future expiry, and a non-reversed active/grace `paid_access` grant from
  `provider_payment` or `compatibility_projection` must cover the current time.
  Trial/free/bonus-only access, expired paid intervals, and reward tails are
  rejected with `active_paid_required`.
- A mutation row-locks the canonical reward state, rechecks eligibility and the
  feature flag, writes the state and entitlement grant, and enqueues one
  idempotent `reward_entitlement_sync` `NodeProvisioningJob` in the same
  transaction. The API reports `not_required`, `sync_pending`, `synced`, or
  `manual_review`; an awarded grant remains durable even when panel sync is
  pending.
- The worker claims jobs with a lock token, recovers stale work, retries with a
  bounded schedule, and moves exhausted or unsafe outcomes to `manual_review`
  with stable redacted codes. It must read canonical ownership again before
  finalization and cannot finalize a stale source account after a merge.
- Account merge reconciles cooldown, calendar position, typed grants, and jobs
  into the canonical target without resetting progress or duplicating duration.
  Open merge reviews and invalid merge chains fence rollout backfill/readiness;
  they are not auto-resolved by the reward lane.
- `BONUS_WHEEL_ENABLED` and `BONUS_CALENDAR_ENABLED` are independent kill
  switches; wheel defaults true and calendar defaults false. The Telegram adapter and API call the same
  reward service; no adapter may retain a local random draw or direct expiry
  mutation.

## Access-State Continuation After Trial

Current backend-derived access states exposed to WebApp and admin surfaces:

- `trial_premium`
- `bonus_premium`
- `free_monthly` (legacy disabled compatibility)
- `free_soft_mode` (legacy disabled compatibility)
- `paid_unlimited`
- `expired_or_blocked`

Rules:

- the effective account status vocabulary is only `TRIAL`, `PAID`, or
  `PENDING`; it is derived from the current active window and grant/plan
  semantics, not directly from a legacy `sub_type` string
- admin-issued days, gifts, promos, referral/channel rewards, incident
  compensation, and provider payments are `PAID` for the duration of their
  active window; `PENDING` means there is no current usable entitlement
- app-first trial reserves premium-grade access for `5 days`; its `5-day`
  consumption clock starts at the first valid internal observer observation
- a new paid-eligible channel claim adds `+5 days`; trial cannot claim it and
  already-issued `+10 days` grants remain grandfathered
- once premium expires, the account remains recoverable and payable but access becomes `expired_or_blocked`; automatic free downgrade is disabled
- entitlement rebuilds and the worker preserve or recover a `FREE` account as
  `trial` only from an exact bounded `premium_trial` grant in `reserved` or
  `active` state. A bounded reservation keeps paid-pool placement without
  starting the five-day consumption clock; missing, unbounded, or stale grant
  state is quarantined for manual review and projected to `expired_or_blocked`
- legacy free-cycle states, roles and provisioning jobs remain rollback-only while
  `FREE_TIER_ENABLED=false`; queued legacy free jobs are cancelled before claim
- `paid_unlimited` remains unlimited traffic with device limit `5`
- premium-grade access states `trial_premium`, `bonus_premium`, and `paid_unlimited` must use the paid pool: all enabled non-free delivery nodes
- backend-facing `node_policy` resolves premium-grade access to `paid_pool`; when free delivery is disabled it resolves no free node at all
- an active, unexpired legacy `PENDING` or empty subscription projection follows the same paid-pool decision as its effective premium access state; it must not show active premium in the client while profile delivery searches the disabled free pool
- a positive admin day grant for a non-manual account normalizes legacy empty, `FREE`, or `PENDING` subscription metadata to `PAID`; missing or free/trial plan metadata becomes `admin_grant`, while manual test accounts keep their explicit `MANUAL` identity
- the Telegram administrator tariff picker exposes paid durations only. Trial
  remains a one-time automatic first-device grant; stale callback buttons cannot
  assign it manually. Telegram day grants and tariff changes normalize the
  plan label in the same transaction and immediately request paid-node sync
- desired-state provisioning places only active `TRIAL`/`PAID` keys on every
  enabled paid node; `PENDING`, expired, and free-retired keys are disabled and
  must not be rerouted to paid or `operator_lab`. A successful admin extension
  triggers this sync after commit; the expiry worker and guarded reconciliation
  script close panel/database drift.

## Runtime Notes

The bonus path is live and configured for:

- public channel: `@pokrov_vpn`
- main bot: `@pokrov_vpnbot`
- support bot: `@pokrov_supportbot`
- feedback bot: `@pokrov_feedbackbot`
- legacy usernames `swazist_bot` and `portal_service_bot` are officially disabled and must not be used as active runtime or support surfaces

The worker and API distinguish channel failures such as:

- `channel_not_found`
- `bot_not_in_channel`
- `not_member`
- `telegram_http_error`

Production environment should keep:

- `PUBLIC_CHANNEL=pokrov_vpn`
- `NEWS_CHANNEL_ID=@pokrov_vpn`

## Support Flow Direction

Support direction should stay consistent across app, WebApp, and helpbot:

- first-layer client IA should stay `Protection`, `Locations`, `Rules`, and `Profile`
- `Support`, `Devices`, `Subscription`, and `Settings` should sit under `Profile`
- renewal and subscription state should remain first-class inside `Profile`, not treated as an isolated side flow
- legacy client route names such as `Logs`, `Config Options`, and `About` may survive only as compatibility redirects, not as the public IA
- support messages should include device context
- users should be able to start support from inside the app
- helpbot remains a valid external fallback
- `support@pokrov.space` remains the email fallback for cases where Telegram is unavailable or a store/support mailbox is required
- cabinet support should continue the same ticket thread and uploads contract exposed by `/api/tickets*`
- feedback collection and public-review intake should continue through `@pokrov_feedbackbot`, not replace the primary support path
- public recovery order must stay `POKROV app -> web cabinet -> Telegram fallback`

Support operators should also be able to see:

- whether Telegram is linked
- the current or most recent device name and platform
- recent `last_ip` context
- enough node and subscription state to understand whether the problem is user-specific or wider

Client-facing diagnostics rule:

- diagnostics may show the active routing mode and a safe route category summary
- diagnostics must not expose raw configs, keys, or internal topology that would make config leakage easier
- the app should prefer safe operator actions such as `change location`, `refresh profile`, `reconnect`, and `contact support`
- user-visible subscription edit, regenerate, and advanced share actions should stay in admin or recovery-only tooling, not the first-layer consumer path
- do not describe Private Space, split tunneling, Knox, Shelter, or similar isolation features as a verified fix for a local control-surface exposure unless a dedicated security audit has proven that statement

## Admin Status And Cleanup Semantics

Current effective status model used across admin surfaces:

- `active`
- `expired`
- `blocked`
- `manual_test`

Current cleanup rule:

- only explicit manual/test accounts may be deleted from admin
- customer accounts remain non-destructive and should be handled through support or billing flows instead

## Funnel And Failure Metrics

Current event taxonomy should make the app-first journey visible across bot, site, and app. Important live/expected events include:

- open / dashboard open
- auth handoff start
- pay start
- pay success
- config open
- config import attempt
- connect success
- connect fail
- reconnect loop detection
- ticket create
- expiry / churn
- renewal / return

The authenticated native first-session slice uses the fixed event names
`app_first_open`, `acquisition_handoff_received|failed`,
`trial_start_selected`, `existing_access_selected`,
`vpn_permission_explainer_shown`, `vpn_permission_result`,
`first_home_seen`, `connect_requested`, and `first_verified_connect`.
`/api/events` derives account/device correlation from the bearer session; the
native client does not upload an acquisition handle, session token, profile,
endpoint, provider response, or raw host error. These rows remain advisory
product telemetry and cannot activate a reserved trial or prove VPN egress.

## Release Scope Note

This flow document applies to the full public `v1` experience on:

- `Android`
- `Windows`

For `iOS` and `macOS`, only readiness, signing prerequisites, and packaging notes are in scope in this release wave.

## Feedback And Review Flow

1. user leaves feedback from the app, WebApp, or `@pokrov_feedbackbot`
2. backend stores the submission for moderation
3. operator approves selected reviews for public display
4. the public homepage and cabinet show only featured reviews
5. visible nicknames are masked in a friendly format such as `mikh****`

If a username is missing or unusable, the public display should fall back to a neutral label like `Пользователь`.

## Selected Loyalty, Pairing And Incident Additions

The app-first account now has three bounded continuation paths:

- an authenticated device or cabinet can issue a short-lived one-time pairing
  code; claiming it creates a separate revocable device session and enforces
  the account device limit;
- the canonical main bot exposes `Код для входа в POKROV` in its device picker
  and through `/start pair_device`; it issues the same server-owned,
  eight-character, single-use code with a ten-minute TTL and never stores or
  logs the plaintext code after the Telegram response;
- the referral summary exposes anonymized funnel counts and transition history,
  never invited-user identity or contact data;
- switch, research, and team-pack forms create manually reviewed applications.
  Affiliate capability is returned as disabled and cannot accept applications.

Useful achievements and quests are projections of server evidence: verified
first tunnel, active device count, the routing-lesson event, and an approved or
rewarded research application. They do not create an automatic entitlement.

The fortnightly wheel uses the server-owned
`paid_fortnightly_discounts_v3` table with a `336 hour` cooldown. Its maximum
premium-day result remains 30 days. Percentage discounts are one-use and do not
stack; a second pending discount is converted to one premium day. The activity
calendar remains server-authoritative and independently disabled by default.

Service incidents are operator-owned records with an affected account/window
boundary. Compensation runs through an idempotent entitlement ledger and a
supervised worker. A complaint, client event, or public status message alone
cannot issue access days.

## Related Files

- [portal_bot/api.py](C:/Users/kiwun/Documents/ai/VPN/portal_bot/api.py)
- [portal_bot/bot.py](C:/Users/kiwun/Documents/ai/VPN/portal_bot/bot.py)
- [portal_bot/worker.py](C:/Users/kiwun/Documents/ai/VPN/portal_bot/worker.py)
- [docs/architecture/client-downloads-flow.md](C:/Users/kiwun/Documents/ai/VPN/docs/architecture/client-downloads-flow.md)
- [docs/architecture/payment-state-machine.md](C:/Users/kiwun/Documents/ai/VPN/docs/architecture/payment-state-machine.md)
- [docs/architecture/support-feedback-flow.md](C:/Users/kiwun/Documents/ai/VPN/docs/architecture/support-feedback-flow.md)
- [POKROV App Docs Index](C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md)
