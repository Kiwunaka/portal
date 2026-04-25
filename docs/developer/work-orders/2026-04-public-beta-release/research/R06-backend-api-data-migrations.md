# R06 Backend API Data Migrations

Status: complete
Agent: R06
Date: 2026-04-25
Scope: backend API, data model, migrations for public beta

## Guardrails

- confirmed: Read-only research pass. Edited only this assigned file.
- confirmed: Worktree already had unrelated changes from other agents, including `portal_bot/api.py`, backend tests, docs, webapp, marketing, shared files, and public-beta work-order scaffolding. I did not revert or edit them.
- confirmed: Source-of-truth docs read before code review: `AGENTS.md`, `docs/README.md`, product overview, system overview, app-first/bonus flows, deployment/access, monitoring/visibility, developer guide, and repository map.
- confirmed: Inherited evidence read only from prior paid-beta R06 and W05:
  - `docs/developer/work-orders/2026-04-beta-release/research/R06-backend-api-data.md`
  - `docs/developer/work-orders/2026-04-beta-release/work-orders/WO-005-backend-contract-hardening.md`
  - `docs/developer/work-orders/2026-04-beta-release/evidence/logs/WO-005-backend-contract-hardening.md`

## Files Inspected

- confirmed: `portal_bot/api.py`
- confirmed: `portal_bot/app_first_service.py`
- confirmed: `portal_bot/models.py`
- confirmed: `portal_bot/migrations.py`
- confirmed: `portal_bot/db.py`
- confirmed: `portal_bot/network_rollout.py`
- confirmed: `portal_bot/node_policy.py`
- confirmed: `portal_bot/nodes_repo.py`
- confirmed: `portal_bot/free_cycle_service.py`
- confirmed: `portal_bot/channel_bonus_service.py`
- confirmed: `portal_bot/web_auth_service.py`
- confirmed: Relevant test inventory and spot checks from `portal_bot/tests/test_app_first_api.py`, `portal_bot/tests/test_app_first_service.py`, `tests/test_smart_connect_api.py`, `tests/test_network_rollout_api.py`, `tests/test_api_auth_and_tickets.py`, `tests/test_api_payments_callbacks.py`, `tests/test_portal_api.py`, `tests/test_free_cycle_service.py`, and `tests/test_worker_retention.py`.

## Current Public-Beta Backend State

- confirmed: `POST /api/client/session/start-trial` creates or reuses a `User` row keyed by `users.app_install_id`, issues a signed app/web bearer session token, calls control-panel sync, and returns `session`, `client_policy`, `access`, `linked_identities`, `free_caps`, `redeem_eligibility`, `promo_slots`, `hidden_transport_matrix`, `location_matrix`, and `provisioning`.
- confirmed: `AppStartTrialIn` no longer accepts caller-controlled `trial_days`; `APP_TRIAL_DEFAULT_DAYS` is loaded server-side from shared product facts/env and defaults to 5.
- confirmed: The current app session model is stateless token-based via `web_auth_service.create_web_session_token`; there is no `app_sessions` table, durable session ledger, central revocation list, or app-device session lifecycle.
- confirmed: The current device model is a single install-backed device folded into `users`: `app_install_id`, device name/platform/version/locale/timezone, last seen, last IP, and route policy. There is no first-class `devices` table or `device_service.py`.
- confirmed: `GET/POST /api/client/route-policy` persist backend-owned `route_mode`, `route_selected_apps_json`, and `route_requires_elevated_privileges`; the same route policy is mirrored into `client_policy`.
- confirmed: `GET /api/client/profile/managed` builds a managed manifest from rollout policy, node inventory, access state, and smart-connect. It returns transport metadata, config payload, fallback order, support context, subscription fallback URL, smart-connect, linked identities, access, promo slots, hidden transport matrix, and location matrix.
- confirmed: `POST /api/client/nodes/latency-samples` accepts up to 10 RTT samples, filters samples to the current smart-connect shortlist, and stores accepted diagnostics as `Event(event_name="smart_connect_latency_sample", session_id=install_id)`.
- confirmed: Free-vs-premium node pool boundaries are explicit in `node_policy.py` and `_nodes_for_user`: free states use the canonical free node only; premium-grade states use enabled non-free nodes.
- confirmed: `user_uses_free_pool` treats `current_plan_code in {"trial", "channel_bonus", "start_99"}` and paid/bonus/trial subtypes as premium-pool users even when `sub_type` is `FREE`.
- confirmed: Expired premium/free users are auto-downgraded or extended into `free_monthly` by `_maybe_downgrade_expired_to_free` when `AUTO_DOWNGRADE_TO_FREE` is true; free cycle fields are initialized/reset by `free_cycle_service`.
- confirmed: Access-key commerce uses `GiftCard` rows plus `PlanCatalog`: public status, session-auth redeem, and admin issue are implemented at `/api/access-keys/status/{key}`, `/api/access-keys/redeem`, and `/api/admin/access-keys/issue`.
- confirmed: Access-key redeem atomically updates `GiftCard.redeemed_by/redeemed_at`, upgrades the user to `PAID`, sets `current_plan_code`, returns unified access-contract family fields, and then attempts control-panel sync.
- confirmed: Telegram reward claim remains explicit and separate from subscriber check. Subscriber check is read-only; claim requires linked Telegram for app users, checks channel membership, grants `+10 days`, marks bonus state, and attempts paid-pool control-panel sync.
- confirmed: Admin network rollout config is stored in `app_settings` under `network_rollout_config` and exposed through `/api/admin/network-rollout-config`.
- confirmed: `db.init_db()` calls `Base.metadata.create_all(engine)` and then dialect-aware additive `run_migrations(engine)`. There is no Alembic-style ordered migration history.

## Migrations And Data Model

- confirmed: `models.py` includes app-first fields directly on `User`, not separate account/device/session tables.
- confirmed: `models.py` includes `Node.transport_profiles_json`, `AppSetting`, `PlanCatalog`, `GiftCard`, `UserNode`, `SupportTicket`, `SupportTicketMessage`, `Event`, `ExternalOrder`, `ExternalPaymentEvent`, observer tables, and key-policy/admin-audit tables.
- confirmed: `migrations.py` adds app-first user columns for SQLite and Postgres, including app install/device fields, route policy fields, and linked Telegram fields.
- confirmed: `migrations.py` creates partial unique indexes for `users.app_install_id` and `users.linked_telegram_id` when non-null.
- confirmed: `migrations.py` backfills `nodes.transport_profiles_json` from legacy node fields when empty.
- confirmed: `migrations.py` creates `app_settings`, `plan_catalog`, external order/payment event tables, support/ticket-related supporting tables, node health samples, observer tables, and admin/key-policy tables additively.
- confirmed: Plan catalog is seeded from `shared/tariff-catalog.json`; runtime access-key metadata depends on `plan_catalog` being present or the shared fallback resolving.
- unknown: Live Postgres may have drift from the additive migration expectations. No production-safe schema query against the real `DATABASE_URL` was run in this pass.

## Rate Limits

- confirmed: Inherited W05 work added `_enforce_beta_rate_limit` with in-process hashed fingerprints, per-minute defaults, structured `429` detail, and `Retry-After`.
- confirmed: Current rate-limited scopes include `start_trial`, `access_key_status`, `access_key_redeem`, `telegram_auth`, `email_auth`, `ticket_create`, and `ticket_upload`.
- confirmed: Fresh `start-trial` creation is rate-limited by origin; same-`install_id` retries bypass the fresh-install limiter to preserve idempotency.
- confirmed: Telegram Login Widget `/api/auth/telegram/web-login`, email auth endpoints, access-key status/redeem, ticket create, and upload call `_enforce_beta_rate_limit`.
- confirmed: Telegram OIDC `/api/auth/telegram/oidc/start` and `/api/auth/telegram/oidc/finish` do not currently call `_enforce_beta_rate_limit`, despite the app-first docs saying Telegram auth beta surfaces are throttled.
- probable: The in-process limiter is acceptable as a beta guardrail only for a single `portal-api` process. If live deployment gains multiple API workers or replicas, counters split by process and no longer provide a coherent origin quota.

## Highest-Risk Findings

1. blocked by missing access: Live Postgres schema/migration state is unverified for public beta. Need a production-safe check for app-first columns, partial unique indexes, plan catalog rows, `app_settings.network_rollout_config`, payment idempotency indexes, node transport catalogs, support/ticket tables, observer tables, and free-cycle columns before release.
2. confirmed: There is no first-class app session or multi-device table. Public beta can safely promise one install-backed app account and panel/IP-limit enforcement, but exact device inventory, per-device revoke, per-device admission control, and central session revocation are not backend-complete.
3. probable: Trial abuse remains wider than the public-beta surface wants. A same-`install_id` retry is idempotent, but a fresh generated `install_id` can create a new account/trial; W05 rate limits slow this by origin only and are in-process, not durable across restarts/processes/origins.
4. blocked by missing access: Live control-panel sync is still not proven for start-trial, access-key redeem, channel bonus, and managed profile delivery. Code can return `pending_sync` or `sync_ok=false`; public beta needs live smoke evidence that new accounts actually receive usable access on the intended node pool.
5. confirmed: Telegram OIDC start/finish endpoints are not throttled while docs describe Telegram auth beta surfaces as rate-limited. This is a public endpoint mismatch and should be fixed or explicitly documented before wider traffic.

## Additional Findings

- confirmed: Email auth backend endpoints are live and rate-limited, but product docs still mark public email continuation as `soon`. Without a runtime/public-surface gate, backend capability can drift ahead of launch readiness.
- confirmed: `GET /api/access-keys/status/{key}` is unauthenticated by design. It is now rate-limited, but it still reveals key existence/status/plan metadata to anyone who can guess a key.
- confirmed: Access-key issue/redeem uses `GiftCard.card_type` as the plan code. This is backward compatible, but support/admin language should treat these as activation keys backed by plan catalog, not a separate gift-card product truth.
- confirmed: Smart-connect shortlist obeys free-vs-paid pool boundaries and rejects stale/unhealthy/cpu-hot/transport-mismatched nodes before client RTT. It still depends on node metrics freshness; stale/missing live metrics could produce no eligible nodes and require fallback handling.
- confirmed: `enabled_nodes(session)` falls back to a legacy synthetic node when DB node rows are absent. This is helpful for local tests but risky if a live Postgres/node seed failure is missed; live readiness should prove real node inventory exists.
- confirmed: Support uploads remain local-file backed and statically mounted after authenticated upload. Prior paid-beta privacy/retention risk remains unless a separate work order changed it elsewhere.
- confirmed: The managed profile response still includes `subscription_url` as a compatibility/recovery artifact. Consumer UI must keep hiding raw links by default.
- unknown: Live `portal-api` systemd unit and worker count were not verified. Repo bootstrap script shows single uvicorn worker, but deployed runtime truth needs brain-origin evidence.
- unknown: Live `AUTO_DOWNGRADE_TO_FREE`, `APP_TRIAL_DEFAULT_DAYS`, `FREE_TOTAL_GB`, `PAID_LIMIT_IP`, `FREE_LIMIT_IP`, and rate-limit env overrides were not read from production.
- needs local run: Current public-beta working-tree backend tests were not executed by R06 to avoid creating extra artifacts in a shared dirty worktree. Inherited W05 evidence reports passing targeted app-first/core/rollout/email tests, plus one known payment-copy expectation failure in `tests/test_api_payments_callbacks.py`.

## Tests Needed Before Public Beta

- needs local run: `python -m pytest portal_bot/tests/test_app_first_api.py portal_bot/tests/test_app_first_service.py -q`
- needs local run: `python -m pytest tests/test_smart_connect_api.py tests/test_network_rollout_api.py -q`
- needs local run: `python -m pytest tests/test_api_auth_and_tickets.py tests/test_api_payments_callbacks.py tests/test_portal_api.py -q`
- needs local run: Add or run a focused regression proving `/api/auth/telegram/oidc/start` and `/api/auth/telegram/oidc/finish` are either throttled or intentionally excluded from the documented beta rate-limit contract.
- needs local run: Add or run a migration smoke against a disposable Postgres instance, not only SQLite, covering `init_db()`, `run_migrations()`, `plan_catalog` seed, partial indexes, and `network_rollout_config` storage.
- blocked by missing access: Run production-safe Postgres schema/readiness check against the live `DATABASE_URL` after backup/rollback review.
- blocked by missing access: Run live API lifecycle smoke with real panel/node sync: start trial, auth session, managed profile, `connect.pokrov.space` fetch, latency sample upload, ticket create/upload, activation-key redeem, dashboard refresh, and node-pool assertion.
- blocked by missing access: Run brain-origin checks for `/api/health`, `/api/client/apps`, `/api/payments/providers`, `portal-api` unit state, and managed-profile connectivity.
- blocked by missing access: Run RU-origin checks separately if node reachability or public-beta geo claims are in scope for the release-captain handoff.

## Suggested Public-Beta Actions

- confirmed: Keep W05 rate-limit work, but close the Telegram OIDC gap or narrow the docs wording.
- probable: Add durable abuse controls for trial creation before broad public traffic: server-side device/account admission policy, install fingerprint watchlist, origin/IP cooldown in a shared store, or an explicit beta-accepted risk note.
- probable: Add a release-facing statement that current device support is install-backed and panel-limited, not a full per-device ledger, until a real devices/session model exists.
- blocked by missing access: Treat live Postgres schema/migration verification as a release blocker, not a nice-to-have.
- blocked by missing access: Treat live control-panel sync evidence as a release blocker because the user-visible trial must create working access, not only a DB/session payload.

## Handoff

### What I checked

- confirmed: Canonical docs and backend source files listed above.
- confirmed: Prior paid-beta R06/W05 inherited evidence.
- confirmed: Current API route inventory and relevant test names.

### What I found

- confirmed: Core app-first, managed profile, access-key, bonus, route-policy, free/premium pool, and beta rate-limit contracts exist in code.
- confirmed: Public-beta release risk is concentrated in live Postgres unknowns, live panel sync unknowns, lack of first-class session/device tables, install-id trial abuse, and Telegram OIDC throttling drift.

### What I changed

- confirmed: Added only this assigned research file.

### How I verified

- confirmed: Read source/docs/evidence locally.
- needs local run: No tests were run by R06 in this shared research pass.

### What remains / risk

- blocked by missing access: Live production DB, live control panel, brain-origin checks, and RU-origin checks remain unverified.
- needs local run: Current public-beta backend matrix still needs a fresh local run after other agents finish their edits.
