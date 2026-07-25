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
- cross-domain compatibility helpers used by more than one route family;
- explicit, ordered loading of the four API slices;
- the direct `uvicorn` development entrypoint.

The route slices load in this exact order:

| Module | Responsibility |
| --- | --- |
| `api_public_routes.py` | Health, public catalog, authentication, client sessions, managed client runtime, node metrics, WARP, and payment entry/callback routes |
| `api_surface_routes.py` | Metrics summaries, cabinet/dashboard data, apps and nodes, rewards, redemption, reviews, feedback, and private user support |
| `api_admin_routes.py` | Admin summaries, payments, users, incidents, programs, campaigns, tickets, node operations, alerts, action intents, and guarded mutations |
| `api_subscription_routes.py` | Transport selection, sing-box/Clash/Happ materialization, preview endpoints, subscription rendering, and render evidence |

Route order is part of the compatibility contract. Static paths such as ticket
uploads must remain registered before parameterized ticket paths, and the
subscription endpoint stays after its transport helpers.

## Telegram Bot Composition

`portal_bot/bot.py` owns:

- aiogram and platform dependency wiring;
- shared bot configuration and process state;
- delivery/rich-message helpers;
- account, entitlement, reward, tariff, and keyboard helpers shared by several
  handler families;
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
| New public/auth/client/payment HTTP endpoint | `api_public_routes.py`, backed by a focused service |
| Cabinet, rewards, redemption, or support HTTP endpoint | `api_surface_routes.py`, backed by a focused service |
| Operator HTTP endpoint or guarded mutation | `api_admin_routes.py`, using admin action/audit services |
| Subscription or transport rendering | `api_subscription_routes.py`, using transport and node policy owners |
| Customer Telegram callback/message | `bot_user_handlers.py` |
| Telegram emergency admin workflow | `bot_admin_handlers.py` or `bot_operator_handlers.py` |
| Telegram payment and fulfillment | `bot_payment_handlers.py`, using payment entitlement services |
| Shared cross-surface business rule | A focused `*_service.py` or repository module, not a composition root |

## Current Size Budget

The 2026-07-25 split keeps every composition root and transport slice below
8,500 lines:

| Module | Lines |
| --- | ---: |
| `api.py` | 8,316 |
| `api_public_routes.py` | 4,446 |
| `api_surface_routes.py` | 3,231 |
| `api_admin_routes.py` | 6,349 |
| `api_subscription_routes.py` | 1,753 |
| `bot.py` | 4,318 |
| `bot_user_handlers.py` | 3,317 |
| `bot_admin_handlers.py` | 2,517 |
| `bot_payment_handlers.py` | 783 |
| `bot_operator_handlers.py` | 1,257 |

`tests/test_module_slices.py` enforces the root/slice ceilings. When a slice
approaches its ceiling, move domain logic into a focused service or repository;
do not create another implicit loader or restore a monolith.

## Verification

Run from the platform repository:

~~~powershell
$py = '.venv/Scripts/python.exe'
& $py -B -m pytest -p no:cacheprovider tests/test_module_slices.py -q
& $py -B -m pytest -p no:cacheprovider portal_bot/tests/test_app_first_api.py tests/test_portal_api.py -q
& $py -B -m pytest -p no:cacheprovider tests/test_api_auth_and_tickets.py tests/test_bot_paywall.py -q
~~~

`tests/test_module_slices.py` caps composition-root and slice size, checks the
declared module list, and verifies re-export, cross-slice lookup, reload, and
legacy patch mirroring.
