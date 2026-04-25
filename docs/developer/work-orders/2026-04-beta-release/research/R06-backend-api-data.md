# R06 Backend API Data

Status: complete

## Scope

Backend API, data model, migrations, app-first sessions, devices, subscriptions, managed profiles, admin APIs.

Read-only research pass. Edited only this file.

## Files/docs inspected

- confirmed: `portal_bot/api.py`
- confirmed: `portal_bot/models.py`
- confirmed: `portal_bot/migrations.py`
- confirmed: `portal_bot/app_first_service.py`
- confirmed: `portal_bot/web_auth_service.py`
- confirmed: `portal_bot/events_service.py`
- confirmed: `portal_bot/pay_attempts_service.py`
- confirmed: `portal_bot/device_service.py` is absent
- confirmed: backend test map in `docs/developer/repository-map.md`
- confirmed: `portal_bot/tests/test_app_first_api.py`
- confirmed: `portal_bot/tests/test_app_first_service.py`
- confirmed: `tests/test_smart_connect_api.py`
- confirmed: `tests/test_network_rollout_api.py`
- confirmed: `tests/test_api_auth_and_tickets.py`
- confirmed: `tests/test_api_payments_callbacks.py`
- confirmed: `tests/test_portal_api.py`
- confirmed: `docs/architecture/system-overview.md`
- confirmed: `docs/architecture/app-first-and-bonus-flows.md`
- confirmed: must-read platform docs from `AGENTS.md` were sampled before code review.

## Current state

- confirmed: app-first bootstrap is implemented at `POST /api/client/session/start-trial`. It requires `install_id`, creates or reuses a `User` keyed by `users.app_install_id`, issues a signed app/web session token, returns `session`, `client_policy`, `access`, `linked_identities`, `free_caps`, `redeem_eligibility`, `promo_slots`, `hidden_transport_matrix`, `location_matrix`, and `provisioning`.
- confirmed: caller-provided trial duration is not in `AppStartTrialIn`; `APP_TRIAL_DEFAULT_DAYS` is used server-side and tests assert the canonical 5-day behavior even when old payloads include `trial_days`.
- confirmed: app session storage is stateless HMAC token based on `WEBAPP_SESSION_SECRET`/fallback secrets, with default TTL from `WEBAPP_SESSION_TTL_SECONDS` or 86400 seconds. There is no `app_sessions` table or per-session revocation store in the inspected model.
- confirmed: the current device model is one app-device identity on `users`: `app_install_id`, `app_device_name`, `app_platform`, OS/app/locale/timezone, `app_last_seen_at`, `app_last_ip`, and persisted route-policy fields. There is no separate `devices` table or `device_service.py`.
- confirmed: `app_install_id` and `linked_telegram_id` have partial unique indexes in SQLite/Postgres migrations.
- confirmed: profile delivery is implemented through `GET /api/client/profile/managed` and the compatibility subscription route `/s8Kx2mP7qR4wT/{token}`. New public `subscription_url` values are built through `public_urls.build_subscription_url`, while the route still supports legacy numeric `tg_id` fallback when enabled and records a fallback event/admin notification path.
- confirmed: free-vs-premium pool logic is explicit. `user_uses_free_pool` path resolves free users to the canonical free node only; premium/trial/bonus/paid users use enabled non-free nodes. Tests cover paid pool, trial pool, and `NL-free` isolation.
- confirmed: smart-connect is implemented in `GET /api/client/profile/managed` and `POST /api/client/nodes/latency-samples`. It filters disabled, draining, unhealthy, stale, CPU-hot, low-health, transport-mismatched, and rollout-disallowed nodes, caps free shortlist at 1 and premium shortlist at 5, and stores accepted RTT samples as `Event(event_name="smart_connect_latency_sample", session_id=install_id)`.
- confirmed: route mode is persisted in `users.route_mode`, `users.route_selected_apps_json`, and `users.route_requires_elevated_privileges`. `GET/POST /api/client/route-policy`, `/api/dashboard`, `/api/user/{tg_id}`, and `client_policy` expose the mirrored `route_policy.*` contract.
- confirmed: traffic/accounting is split between DB policy and panel/runtime evidence. Access state uses `_build_access_policy`; runtime usage comes from panel summaries when available, with legacy panel fallback, while node aggregate traffic comes from `node_health_samples`.
- confirmed: access-key commerce is implemented through `GET /api/access-keys/status/{key}`, `POST /api/access-keys/redeem`, and `POST /api/admin/access-keys/issue`. Redeem uses `GiftCard` rows plus plan catalog metadata, atomically marks `redeemed_by/redeemed_at`, updates the user, then syncs control-panel access.
- confirmed: ticket APIs exist and are session guarded: list/create/upload/read/message under `/api/tickets*`; admin ticket list/reply/status under `/api/admin/tickets*`.
- confirmed: uploads enforce auth, non-empty body, max byte size via `SUPPORT_UPLOAD_MAX_BYTES`, generated filenames, sanitized original names, and local storage under `SUPPORT_UPLOAD_DIR`; mounted static serving is enabled for that directory.
- confirmed: admin API guard is `_require_admin`, based on Telegram init data, web session token, or explicit local dev auth if `WEBAPP_DEV_AUTH` is enabled and request origin is localhost/allowed dev origin.
- confirmed: admin summary and metrics APIs exist: `/api/admin/summary`, `/api/admin/metrics/status`, `/api/admin/nodes/traffic`, `/api/admin/metrics/timeseries`, `/api/admin/nodes/health`, plus node lifecycle/sync/drift routes.
- confirmed: payment callback idempotency exists through unique indexes on `external_orders(provider, order_id)` and `external_payment_events(provider, event_type, external_id)`; tests cover duplicate callback behavior and invalid signature behavior.
- confirmed: migrations are additive and dialect-aware. `run_migrations` dispatches to PostgreSQL-specific migrations for Postgres and idempotent PRAGMA/ALTER/index logic for SQLite.
- confirmed: observer retention cleanup exists in `observer_service.cleanup_observer_retention`, called by worker, with default `OBSERVER_RETENTION_DAYS >= 30`.

## Gaps against beta

- confirmed: there is no first-class multi-device table. The backend can report a `devices` list, but it is derived from the single app-install fields on `users`. Beta copy that implies per-device inventory, revoke, or multi-device lifecycle should be treated as not backed by a real backend device model yet.
- probable: device limits are enforced mainly through 3x-ui `limitIp` per node (`FREE_LIMIT_IP` / `PAID_LIMIT_IP`) and surfaced by `_plan_device_limit`, not through server-side registration/device admission. This likely protects concurrent IP usage but does not prevent new installs from creating independent accounts.
- confirmed: app-first `start-trial` is idempotent for the same `install_id`, but a fresh `install_id` can create a fresh app account/trial. No abuse-control gate beyond unique install_id was found in the inspected code.
- confirmed: route-policy persistence accepts up to 128 selected app/process strings and normalizes them, but does not validate Android package names or Windows executable paths beyond length/dedupe.
- confirmed: upload storage is local filesystem and publicly mounted under the configured URL prefix. Auth is required to upload and ticket access is guarded, but returned upload URLs are static file paths; no signed-download guard or attachment retention policy was found.
- confirmed: email auth endpoints are implemented and can create email-backed free accounts, but docs still say public email continuation is `soon`. The backend itself does not expose a single global "email auth disabled" gate in the inspected API route handlers; operational readiness depends on sender/webhook config and frontend exposure.
- confirmed: only diagnostics run has an in-memory per-user rate limit. No general rate limiting was found for start-trial, email auth, ticket creation/upload, access-key status, or payment-order creation.
- confirmed: data retention is partial. Observer records have cleanup, but no retention cleanup was found for app install/device IP fields, web sessions are stateless until expiry, events/pay attempts/external payment events/tickets/uploads appear retained unless manually cleaned.
- probable: production Postgres migration health is good structurally but cannot be confirmed without a live Postgres migration run; the local tests mostly use SQLite temp DBs.

## P0 blockers

- blocked by missing access: live production Postgres schema and migration state were not verified. Need a production-safe schema/migration check against `DATABASE_URL` or a brain-origin deploy verification before paid beta.
- blocked by missing access: live control-panel sync from app-first trial, access-key redeem, and node-profile delivery was not verified. Code catches sync failures and can return `pending_sync`, so beta readiness needs a real panel-backed smoke.
- needs local run: backend test matrix was not executed in this read-only pass. Minimum run should include `portal_bot/tests/test_app_first_api.py`, `portal_bot/tests/test_app_first_service.py`, `tests/test_smart_connect_api.py`, `tests/test_network_rollout_api.py`, `tests/test_api_auth_and_tickets.py`, `tests/test_api_payments_callbacks.py`, and `tests/test_portal_api.py`.
- probable: start-trial abuse control is insufficient for a paid beta if one physical user can reset/reinstall and obtain new trials by generating new `install_id`s. If the beta accepts this risk, document it as an operational watch item; otherwise add server-side anti-abuse before wider release.
- confirmed: true device management is not backend-complete. Do not ship user/operator promises for multi-device inventory, remote revoke, or exact device-count enforcement until a devices table/admission/revoke model exists or the promise is narrowed to panel IP limits.

## P1 beta polish

- confirmed: add a global backend feature flag or explicit 503/soon response for public email register/recovery unless email delivery is meant to be live in this wave.
- confirmed: add durable rate limits for app trial creation, email auth, ticket uploads, and access-key status/redeem. In-memory diagnostics rate limiting is not enough for externally exposed beta APIs.
- confirmed: tighten support upload delivery: private download endpoint or signed URLs, content-type allowlist, and retention cleanup.
- probable: make `app_last_seen_at` refresh on authenticated app/profile/dashboard calls, not only start-trial reuse, so admin install freshness reflects real beta activity.
- probable: add explicit local-run docs/evidence for Postgres migrations, because SQLite-heavy tests can miss dialect drift.

## P2 defer

- confirmed: normalize route selected apps by platform-specific rules later; current length/dedupe sanitation is acceptable for beta if the client picker owns correctness.
- confirmed: replace stateless app/web sessions with stored revocable sessions later if beta does not require forced logout/device revoke.
- confirmed: split `users` into first-class account/device/session tables later if beta scope only needs one install-backed device per app account.
- probable: add structured per-device traffic ledger later; current runtime/panel aggregation is enough for coarse access-state and admin visibility but not exact per-device billing.

## Technical debt

- confirmed: `portal_bot/api.py` is very large and owns API routes, policy shaping, profile generation, auth guards, payments, tickets, admin metrics, and node control. This makes beta-critical behavior harder to review in isolation.
- confirmed: `device_service.py` does not exist; device behavior is spread across `api.py`, `app_first_service.py`, and `users` columns.
- confirmed: migrations intentionally support both SQLite and Postgres. This is useful for tests but increases dialect drift risk.
- confirmed: local tests still create SQLite DBs (`portal_api_test_*.db` / tmp DBs). They are legitimate test artifacts, not source of truth, and should be cleaned by tests or routine cleanup.
- probable: access and device policies are split between DB-derived API payloads and 3x-ui panel policy (`limitIp`, `totalGB`), so support/admin copy must avoid claiming one canonical device ledger.

## Security/privacy risks

- confirmed: app sessions are bearer tokens accepted via `Authorization: Bearer` or `X-Web-Auth-Token`; token compromise lasts until TTL and cannot be revoked centrally.
- confirmed: support upload URLs are static paths after upload. Anyone with the URL can likely fetch the file while it remains present.
- confirmed: `/api/access-keys/status/{key}` is public and unauthenticated. It reveals validity/status/plan metadata for guessed keys; key entropy may make this acceptable, but add rate limiting before beta.
- confirmed: `/s8Kx2mP7qR4wT/{token}` has legacy numeric fallback if enabled. It logs only a fingerprint and notifies admin, but numeric fallback should remain monitored and ideally disabled once old clients are migrated.
- confirmed: `app_last_ip`, observer IP-derived keys, ticket bodies, uploads, payment events, and auth/email identities are retained in DB/filesystem. No broad retention/delete policy was found beyond observer cleanup and manual/test safe delete.
- confirmed: `WEBAPP_DEV_AUTH` is guarded by localhost and allowed dev origins, but it must remain disabled in production.

## Required implementation WOs

- R06-BE-01: Run and attach local backend matrix evidence for app-first, smart-connect, network rollout, auth/tickets, payments callbacks, and portal node policy tests.
- R06-BE-02: Verify production/brain Postgres migrations and live schema for app-first columns, unique partial indexes, payments idempotency indexes, node metrics tables, and support ticket/upload columns.
- R06-BE-03: Run live API lifecycle smoke with real control-panel sync: start trial, auth session, managed profile, `connect.pokrov.space` fetch, latency sample upload, ticket create/upload, access-key redeem, dashboard refresh.
- R06-BE-04: Decide beta stance on trial abuse and device model. Either narrow promises to install-backed single-device accounts plus panel IP limits, or implement first-class devices/admission/revoke.
- R06-BE-05: Add beta-safe rate limits for trial/email/ticket/upload/access-key/payment order surfaces.
- R06-BE-06: Add support upload privacy/retention guardrails or explicitly classify attachment URLs as bearer-style private links in operator docs.
- R06-BE-07: Add/confirm email-auth launch gate so `/api/auth/email/*` cannot accidentally become a public live promise while docs say `soon`.

## Validation commands

- needs local run: `python -m pytest portal_bot/tests/test_app_first_api.py portal_bot/tests/test_app_first_service.py -q`
- needs local run: `python -m pytest tests/test_smart_connect_api.py tests/test_network_rollout_api.py -q`
- needs local run: `python -m pytest tests/test_api_auth_and_tickets.py tests/test_api_payments_callbacks.py tests/test_portal_api.py -q`
- needs local run: `python scripts/api_lifecycle_smoke.py`
- blocked by missing access: production-safe Postgres migration/schema check against the real `DATABASE_URL`.
- blocked by missing access: brain/control-panel smoke proving `sync_ok=true` or expected `pending_sync` recovery behavior on live nodes.

## Evidence links

- confirmed: `portal_bot/api.py` endpoints: `/api/client/session/start-trial`, `/api/client/profile/managed`, `/api/client/nodes/latency-samples`, `/api/client/route-policy`, `/api/auth/session`, `/api/tickets*`, `/api/admin/summary`, `/api/admin/metrics/status`, `/api/access-keys/*`, `/s8Kx2mP7qR4wT/{token}`.
- confirmed: `portal_bot/app_first_service.py` owns install-id upsert, app session payload shaping, route-policy normalization/persistence, and client policy construction.
- confirmed: `portal_bot/models.py` includes `User`, `UserNode`, `GiftCard`, `SupportTicket`, `SupportTicketMessage`, `NodeHealthSample`, `Event`, observer tables, `PayAttempt`, `ExternalOrder`, `ExternalPaymentEvent`, `PlanCatalog`, `StartLink`, and `AppSetting`.
- confirmed: `portal_bot/migrations.py` includes SQLite and PostgreSQL additive migrations plus unique partial indexes for `app_install_id` and `linked_telegram_id`.
- confirmed: tests named in Repository Map cover app-first API/service, smart-connect, rollout policy, auth/tickets/admin metrics, payment callbacks/idempotency, and pool selection.
