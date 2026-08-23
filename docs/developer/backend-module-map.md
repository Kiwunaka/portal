# Backend Module Map

## Purpose

The platform backend remains one deployable modular monolith. `portal_bot/api.py`
and `portal_bot/bot.py` are thin compatibility composition roots; route and
handler implementations are grouped into ordered domain slices, while business
rules continue to live in focused service and repository modules.

This split preserves the historical `api.<name>` and `bot.<name>` import
surfaces used by tests, operator scripts, and emergency tooling. It does not
create another process, database, network boundary, or deployment unit.

## FastAPI Composition

`portal_bot/api.py` owns:

- configuration and dependency imports;
- shared constants, Pydantic request/response models, middleware, and app
  construction;
- lifespan ownership for the bounded payment-provider HTTP registry;
- cross-domain compatibility helpers used by more than one route family;
- explicit, ordered loading of the twelve API slices;
- the direct `uvicorn` development entrypoint.

The route slices load in this exact order:

| Module | Responsibility |
| --- | --- |
| `api_public_routes.py` | Health, emergency/public catalog, authentication, client session/recovery bootstrap, and route-policy transport |
| `api_client_routes.py` | Managed client locations/subscription/devices/notifications/profile/node/runtime/WARP/Telegram transport plus retained compatibility order-application helpers and promo media |
| `api_commercial_offer_routes.py` | Anonymous server-authoritative offer quote/token transport with legal, capacity, revision and quota fail-closed responses |
| `api_payment_routes.py` | Payment success/failure pages, provider callbacks, RUB order/start-99 transport, and historical FreeKassa transport |
| `api_observability_routes.py` | Authenticated, privacy-bounded aggregate release-health ingestion; raw body/compression limits and request-to-service orchestration |
| `api_support_bundle_routes.py` | Authenticated signed-key distribution plus case-bound, resumable encrypted support-bundle upload; ciphertext is queued for the isolated worker and never unpacked here |
| `api_operator_observability_routes.py` | Admin release-health/known-issue views, L1 bundle summary, and explicitly allowlisted audited L2/SRE ciphertext access/retention holds |
| `api_surface_routes.py` | Metrics summaries, cabinet/dashboard data, apps and nodes, rewards, redemption, reviews, feedback, and private user support |
| `api_admin_routes.py` | Admin summaries, payments, users, incidents, programs, campaigns, tickets, node read models, alerts, and ordinary transport orchestration |
| `api_admin_action_routes.py` | Guarded action-intent policy adaptation, database/external execution orchestration, compatibility response shaping, and prepare/status HTTP bindings |
| `api_admin_network_routes.py` | Guarded emergency-network stage/promote/disable/rollback plus node disable/resync HTTP bindings; it loads after the base admin orchestration slice |
| `api_subscription_routes.py` | Transport selection, sing-box/Clash/Happ materialization, preview endpoints, subscription rendering, and render evidence |

Route order is part of the compatibility contract. Static paths such as ticket
uploads must remain registered before parameterized ticket paths, and the
subscription endpoint stays after its transport helpers.

The guarded mutation boundary is split without duplicating policy truth:

- `admin_action_intent_service.py` owns domain payload normalization, entity
  snapshots, previews, challenges and the single mutable `ACTION_POLICIES`
  registry;
- `admin_action_intent_runtime.py` owns generic intent identity, persistence,
  expiry, confirmation, locking, idempotency, replay and bounded external-
  outcome state. The service passes its exact registry and constant-time
  comparator explicitly; the runtime registers neither actions nor routes;
- thin service wrappers preserve the established
  `prepare_action_intent`/`execute_action_intent`/`get_action_intent_status`
  import surface used by legacy API slices, Operator Center v2 and jobs.

## Telegram Bot Composition

`portal_bot/bot.py` owns:

- aiogram and platform dependency wiring;
- shared bot configuration and process state;
- delivery/rich-message helpers;
- account, entitlement, reward, tariff, and keyboard helpers shared by several
  handler families;
- startup-validated paid tariff prices and durations projected from
  `commercial_contract.py`;
- explicit, ordered loading of the four handler slices;
- the polling entrypoint.

The handler slices load in this exact order:

| Module | Responsibility |
| --- | --- |
| `bot_user_handlers.py` | Start and navigation, cabinet/key delivery, device actions, rewards, referrals, support, tickets, and customer text/media input |
| `bot_admin_handlers.py` | Interactive admin panels, broadcasts, promos, live updates, mass actions, user controls, and emergency maintenance callbacks |
| `bot_payment_handlers.py` | Stars/RUB checkout, payment reconciliation, entitlement fulfillment, retries, and subscription creation |
| `bot_operator_handlers.py` | Operator commands, moderation, promo/gift commands, expiry monitoring, Telegram profile setup, and polling startup |

Aiogram resolves handlers in registration order. Do not alphabetize or
auto-discover these modules.

## Compatibility Runtime

`portal_bot/module_slices.py` performs three bounded jobs:

1. seeds each explicitly named slice with the already-created composition-root
   dependencies before decorators execute;
2. re-exports slice definitions through `api` or `bot`;
3. mirrors later attribute replacement into loaded slices so existing
   `monkeypatch`, `patch.object`, and operator overrides still target the object
   actually used by a handler.

The runtime does not execute source strings and does not scan the filesystem.
It reloads slices when the owner module is reloaded, preventing duplicate or
missing route tables in the existing test harness.

This bridge is for legacy compatibility, not a pattern for new business logic.
New behavior belongs in an explicit service/repository module with typed
inputs. A slice should contain transport binding and orchestration, not a new
second copy of entitlement, payment, account, or node policy.

## Change Routing

| Change | Primary location |
| --- | --- |
| New public/auth/session-bootstrap HTTP endpoint | `api_public_routes.py`, backed by a focused service |
| New managed client feature/runtime HTTP endpoint | `api_client_routes.py`, backed by a focused service |
| Public commercial offer preview | `api_commercial_offer_routes.py`, backed by `commercial_offer_service.py`; campaign policy remains in `commercial_campaign_policy.py` |
| Payment HTTP endpoint | `api_payment_routes.py`, backed by the payment application/provider owners below |
| Consumer payment-return state | `payment_return_service.py`; `api_payment_routes.py` exposes the token-only read endpoint, while order creation issues the token after durable local intent |
| Operational release-health ingest endpoint | `api_observability_routes.py`, backed by `observability_ingest.py` |
| Encrypted support-bundle key/upload endpoint | `api_support_bundle_routes.py`, backed by `support_bundle_upload_service.py`; content validation stays in the worker-only ingest service |
| Operator observability or support-bundle evidence endpoint | `api_operator_observability_routes.py`, backed by `operator_observability_service.py`; raw access stays L2/SRE-only and encrypted |
| Cabinet, rewards, redemption, or support HTTP endpoint | `api_surface_routes.py`, backed by a focused service |
| Operator HTTP endpoint or guarded mutation | Ordinary admin transport stays in `api_admin_routes.py`; guarded action-intent orchestration belongs in `api_admin_action_routes.py`; emergency-network and node disable/resync transport belongs in the immediately following `api_admin_network_routes.py` slice |
| Guarded mutation policy or domain snapshot | `admin_action_intent_service.py`; the one `ACTION_POLICIES` registry stays here and is explicitly injected into `admin_action_intent_runtime.py` |
| Generic intent persistence/execution state | `admin_action_intent_runtime.py`; it owns confirmation, locks, idempotency, replay and external-outcome finalization but no domain policy or HTTP route |
| Subscription or transport rendering | `api_subscription_routes.py`, using transport and node policy owners |
| Device-bound AWG2 owner lab | `awg2_lab_service.py` owns exact contract validation, encrypted material, rollout readiness and managed config construction; `network_rollout.py` owns selection/rollback and `api_subscription_routes.py` keeps it out of public exports |
| Customer Telegram callback/message | `bot_user_handlers.py` |
| Telegram emergency admin workflow | `bot_admin_handlers.py` or `bot_operator_handlers.py` |
| Telegram payment and fulfillment | `bot_payment_handlers.py`, using payment entitlement services |
| Local RUB order intent/provider result | `payment_order_service.py`; HTTP binding lives in `api_payment_routes.py`, while the retained compatibility order-use-case wiring in `api_client_routes.py` delegates immutable intent/result rules to the service |
| Commercial reservation/order binding and paid consume | `commercial_order_service.py`; it owns locked policy/quota revalidation, unique order binding, failed-checkout expiry and callback-independent consume, while payment transport/provider I/O remains in the existing payment owners |
| Commercial payment/connect/retention attribution | `commercial_attribution_service.py`; it owns identity-free provider/order/stage projections and the read-only campaign/revision/capacity-unit read model. Payment callbacks own paid/reversed truth, observer `ConnectionEvidence` owns verified-connect/D7/D30, and client funnel telemetry owns neither |
| Provider callback orchestration | `payment_callback_application.py`; `api.py` only constructs the explicit dependency bundle and preserves the legacy delegating export |
| Applied provider grant delivery | `payment_entitlement_outbox.py` to idempotent `payment_entitlement_sync` jobs processed by `node_provisioning_service.py` |
| Payment-provider outbound HTTP | `outbound_http.py`; the API lifespan owns it and payment/provider callers receive it explicitly |
| Async payment DB execution/health | `payment_db_runtime.py`; complete sync use cases run in the bounded threadpool and return no ORM object |
| Commercial manifest/revision/base-price validation | `commercial_contract.py`; generated source is `shared/commercial-contract.json`, public transport stays in `api_public_routes.py`, and frontend adapters live in `shared/commercial-contract.ts` |
| Campaign legal/lifecycle/capacity policy | `commercial_campaign_policy.py`; `IncentiveCampaign` remains the single mutable root, guarded mutation/readback stays in `api_admin_routes.py`, and promo/gift application revalidates policy in API/bot composition paths |
| Commercial capacity automation/forecast | `commercial_capacity_service.py`; active entitlement grants are the only unit authority, the supervised worker applies audited pause/hold/resume transitions, and admin GET readback remains non-mutating |
| Commercial offer price/assignment/hold/token | `commercial_offer_service.py`; child rows remain under `IncentiveCampaign`, public no-store transport lives in `api_commercial_offer_routes.py`, and `commercial_order_service.py` owns atomic order binding/consumption |
| Payment-method capability mapping | `payment_providers.py`; consumers render its ordered available/unavailable rows and never infer provider support |
| Shared cross-surface business rule | A focused `*_service.py` or repository module, not a composition root |

## Outbound HTTP ownership

`outbound_http.py` is the 1.2.0 owner for the payment-provider surface only.
The FastAPI lifespan starts and closes one registry; the registry keeps a
bounded reusable session per provider policy. Lava.top, Cardlink, Pally,
Platima and historical FreeKassa API operations use explicit total, connect,
socket-read, pool and response-body limits. FreeKassa method names are a closed
allowlist. Its public SCI checkout builder remains local and performs no HTTP.

The only emitted request dimensions are provider, closed operation, HTTP
status, integer latency and closed result code. URL/query, headers, credentials,
request JSON/form data, response body and exception text are not telemetry.

The following non-provider clients remain deliberately outside this WO and do
not count toward `REL/HTTP-001`: Telegram delivery/member checks in `api.py`,
`bot.py`, `channel_bonus_service.py`, `telegram_delivery_service.py` and
`worker.py`; the bot-to-portal checkout call and bot operator self-ping;
email-delivery webhook; Telegram OIDC/JWKS in `web_auth_service.py`; panel
sessions in `panel_client.py` and the legacy API usage reader; emergency catalog
mirror ingestion; news feeds; support-AI provider adapters; and standalone
health/relay scripts. Each stays with its process/domain owner until a bounded
WO can preserve its response, retry, credential and lifecycle contract.

`payment_db_runtime.py` is likewise a scoped transitional owner. Public payment
order and callback orchestration invokes complete sync functions through
Starlette/AnyIO's bounded threadpool. Each function owns session creation,
commit/rollback and close in the worker thread. Health is fixed-shape integer
aggregate only. `payment_callback_application.py` owns the callback use-case
sequence; `api.py` retains dependency construction and a thin compatibility
delegate so legacy imports and monkeypatches keep working. The payment route
table lives in `api_payment_routes.py` in the same registration position as the
previous public-slice block. Non-payment async routes with synchronous ORM and
the remaining large public/admin roots are explicit later inventories; this
slice does not authorize a repository-wide ORM rewrite or a second backend.

## Current Size Budget

The composition contract keeps every root and transport slice below its
declared test ceiling:

| Module | Lines |
| --- | ---: |
| `api.py` | 9,594 |
| `api_public_routes.py` | 2,019 |
| `api_client_routes.py` | 3,980 |
| `api_commercial_offer_routes.py` | 145 |
| `api_payment_routes.py` | 381 |
| `api_observability_routes.py` | 126 |
| `api_support_bundle_routes.py` | 431 |
| `api_operator_observability_routes.py` | 271 |
| `api_surface_routes.py` | 3,967 |
| `api_admin_routes.py` | 4,336 |
| `api_admin_action_routes.py` | 2,774 |
| `api_admin_network_routes.py` | 153 |
| `api_subscription_routes.py` | 1,909 |
| `admin_action_intent_service.py` | 6,488 |
| `admin_action_intent_runtime.py` | 2,034 |
| `payment_callback_application.py` | 387 |
| `payment_order_service.py` | 408 |
| `payment_entitlement_outbox.py` | 516 |
| `outbound_http.py` | 265 |
| `payment_db_runtime.py` | 106 |
| `commercial_contract.py` | 133 |
| `commercial_campaign_policy.py` | 466 |
| `commercial_offer_service.py` | 918 |
| `commercial_order_service.py` | 815 |
| `commercial_attribution_service.py` | 680 |
| `payment_return_service.py` | 321 |
| `commercial_capacity_service.py` | 420 |
| `bot.py` | 4,420 |
| `bot_user_handlers.py` | 3,483 |
| `bot_admin_handlers.py` | 2,526 |
| `bot_payment_handlers.py` | 783 |
| `bot_operator_handlers.py` | 1,261 |
| `worker.py` | 1,537 |

`tests/test_module_slices.py` enforces the root/slice ceilings. When a slice
approaches its ceiling, move domain logic into a focused service or repository;
do not create another implicit loader or restore a monolith.

## Verification

Run from the platform repository:

~~~powershell
$py = (Get-Command python.exe).Source
& $py -B -m pytest -p no:cacheprovider tests/test_module_slices.py -q
& $py -B -m pytest -p no:cacheprovider portal_bot/tests/test_app_first_api.py tests/test_portal_api.py -q
& $py -B -m pytest -p no:cacheprovider tests/test_api_auth_and_tickets.py tests/test_bot_paywall.py -q
~~~

`tests/test_module_slices.py` caps composition-root and slice size, checks the
declared module list, and verifies re-export, cross-slice lookup, reload, and
legacy patch mirroring.
