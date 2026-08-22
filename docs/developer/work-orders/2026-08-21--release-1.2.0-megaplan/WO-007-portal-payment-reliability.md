# WO-007 — Portal Payment And Reliability Boundaries

Status: `COMPLETE_LOCAL_I3`
Classification: `ACTIVE_EXECUTION`
Phase: `05`
Lane: platform backend/API/worker only

## Bounded outcome

Close the two confirmed FreeKassa stop-ships, make provider checkout and paid
entitlement delivery fail closed and replay safe, and establish the smallest
maintainable server boundaries required by Gate D: payment context, shared
bounded outbound HTTP, an explicit non-blocking transition for payment API use
cases, and a transactional payment-entitlement outbox. This is a strangler
slice inside the existing modular monolith, not a database rewrite or a new
service.

This WO does not enable FreeKassa, change the active Lava.top-only public beta,
deploy code, contact providers, mutate a production payment, or claim refund/
chargeback maturity.

## Authority and current evidence

Canonical behavior owners:

- `docs/product/payment-and-access-key-contract.md`;
- `docs/architecture/payment-state-machine.md`;
- `docs/architecture/app-first-and-bonus-flows.md`;
- `docs/operations/payment-reconciliation.md`.

Implementation evidence starts in `portal_bot/api.py`,
`portal_bot/api_public_routes.py`, `portal_bot/payment_providers.py`,
`portal_bot/payment_entitlement_service.py`, `portal_bot/economy_service.py`,
`portal_bot/models.py`, migrations, worker and focused payment tests.

Observed baseline on 2026-08-21:

- `_parse_freekassa_payment_url` is still defined twice in `api.py`;
- both definitions manufacture an `oa=0` URL when the provider response has no
  checkout URL;
- payment/provider helpers still create per-operation `aiohttp.ClientSession`
  instances;
- async payment routes execute synchronous ORM work directly in the event-loop
  call path;
- durable entitlement grants exist, but there is no payment-entitlement
  transactional outbox contract;
- the API composition has explicit slices, but FreeKassa/provider orchestration
  and transaction rules still live in the compatibility root/public slice.

## Architectural decisions

1. Keep synchronous SQLAlchemy for 1.2.0 and use the audit's transitional path:
   move complete synchronous payment use cases behind focused service functions
   and execute them through a bounded threadpool from async handlers. Do not mix
   one SQLAlchemy session across threads or across an awaited provider call.
2. Persist immutable local order intent before any provider request. Provider
   success metadata is attached in a second short transaction; failure leaves a
   local fail-closed order/reconciliation fact rather than inventing a URL.
3. Use one lifespan-owned outbound HTTP registry with provider-specific total,
   connect and socket-read limits. Tests may inject a client explicitly; no
   global session is created at import time.
4. A payment-entitlement outbox row is written in the same database transaction
   as the canonical grant/projection. Its unique idempotency key, aggregate,
   schema version, attempt count, next retry and terminal reason are bounded.
   The supervised worker claims and dispatches it idempotently. Outbox delivery
   is downstream notification/provisioning evidence, never payment authority.
5. Extract only the payment/provider and transaction seams changed by this WO.
   Preserve `api.<legacy_name>` compatibility through explicit imports/exports;
   do not mechanically split unrelated admin, account or subscription code.

## WO-007A — FreeKassa stop-ship closure

Deliver:

- one payment-URL parser in a focused FreeKassa/provider module;
- accepted nested/top-level provider response shapes and strict HTTPS URL
  validation;
- missing, malformed, non-HTTPS or untrusted-host checkout URL fails closed with
  a stable provider error and never synthesizes `oa=0`;
- the existing signed SCI URL builder remains the only local URL construction
  path and requires exact positive amount/order/source/shop configuration;
- regression/source tests prove one definition and no `oa=0` fallback.

Rows eligible after proof: `REL/PAY-001`, `REL/PAY-002` to local `I3`.

### 007A local closure — 2026-08-21

- the duplicate compatibility-root definitions are removed; one parser in
  `payment_providers.py` is re-exported through the legacy `api` name;
- known top-level and nested response shapes are accepted only when the URL is
  HTTPS, has no credentials/control whitespace, has a nonempty path, and
  matches the exact configured payment hostname/port;
- missing/malformed/http/cross-host/userinfo/no-path values fail with stable
  `502`; fallback order/source arguments cannot manufacture a URL; source tests
  prove neither `api.py` nor the provider module contains `oa=0`;
- focused boundary tests `11/11`, legacy compatibility test `1/1`, and full
  payment/provider/callback regression `106/106` plus `12` subtests PASS. The
  19 warnings are existing datetime/httpx deprecations, not test skips/failures.

`REL/PAY-001` and `REL/PAY-002` advance from observed `I1` to local `I3`. The
global distribution is now 108 rows at `I3`, 8 at `I2`, 5 at `I1`, and 256 at
`I0`; 121 of 377 rows remain at least `I1`. FreeKassa is still disabled and no
production provider/configuration/payment evidence is claimed. 007B is active.

## WO-007B — Immutable local order and provider adapter boundary

Deliver:

- extract order-intent normalization/persistence and provider response
  application into a focused payment application service;
- local order is durable before external request; amount/currency/plan/source/
  owner and entitlement snapshot cannot be rewritten from provider response;
- provider failure/missing URL leaves a non-fulfilling local state with bounded
  sanitized evidence; retry reuses exact local order intent;
- callback replay returns the same order/grant result without duplicate access.

Rows strengthened: `REL_DOD/DOD-08`; supports `REL_GATE/GATE-D`.

### 007B local closure — 2026-08-21

- `payment_order_service.py` now owns normalization, initial persistence,
  authority comparison, safe provider-result application and failure evidence;
- the first transaction persists `pokrov-payment-order-intent-v1` before
  provider I/O. Its digest binds provider/order, owner, amount, currency, plan,
  source and the complete entitlement snapshot; an exact retry reuses the row,
  while any scalar or snapshot drift raises a closed intent conflict;
- checkout completion uses a fresh transaction and cannot regress a terminal
  callback state to `pending`. Only allowlisted provider reference/status
  scalars and `url_present` are retained; checkout URL, query, raw request/body,
  buyer email from provider payload and secret-like fields are absent;
- provider failure returns the original HTTP error after committing closed
  `provider_checkout_error` evidence on the non-fulfilling `created` order;
- service tests passed `10/10`; focused route tests passed `3/3`, including
  committed-before-network failure and preservation of the direct-promo path.
  The full payment regression result is recorded in the execution index.

`REL_DOD/DOD-08` advances from `I0` to `I2`: immutable local-order authority and
existing callback/grant replay protection are implemented, but the
same-transaction entitlement outbox required by 007C is not yet present. The
distribution is now 108 rows at `I3`, 9 at `I2`, 5 at `I1`, and 255 at `I0`;
122 of 377 rows are at least `I1`. No provider was enabled and no production
payment, callback, reconciliation or deployment evidence is claimed. 007C is
active.

## WO-007C — Transactional payment-entitlement outbox

Deliver:

- additive model and rerunnable SQLite/PostgreSQL migration;
- same-transaction enqueue for a newly applied or repaired provider-payment
  grant, unique by provider/order/event schema;
- bounded worker claim/retry/dead-letter with stale-claim recovery and integer
  health counters;
- duplicate callback and worker replay cannot duplicate grant, projection or
  dispatched event; malformed payload fails closed without access mutation.

Row eligible after proof: `REL_DOD/DOD-08` to local `I3`; contributes to
`REL_GATE/GATE-D`.

### 007C local closure — 2026-08-21

- `payment_entitlement_outbox.py` and additive SQLite/PostgreSQL migrations now
  own the `pokrov-payment-entitlement-v1` event, unique provider/order identity,
  bounded attempts, next-run clock, claim token, stale recovery, delivery and
  dead-letter state;
- every active `provider_payment`/`paid_access` grant writes its minimal event
  in the grant transaction. Historical projection-only facts do not enqueue,
  while a bounded backfill repairs pre-existing active grants without changing
  entitlement authority;
- the supervised worker conditionally claims a bounded batch, dispatches an
  idempotent `payment_entitlement_sync` provisioning job and marks delivery in
  the same transaction. Callback, backfill and worker replay converge on one
  grant, outbox row and provisioning job;
- malformed payload, reversed grant, exhausted retry and lost claim fail
  closed. Health/log projection contains integer counters only; account,
  Telegram, checkout URL, provider body and raw exception text are absent;
- focused outbox tests passed `9/9`; exact entitlement/account/provisioning/
  retention regression passed `124/124`; the exact payment/provider/callback
  matrix passed `126/126` plus `12` subtests. The `19` warnings are existing
  datetime/httpx deprecations, not skips or failures.

`REL_DOD/DOD-08` advances from `I2` to local `I3`. The distribution is now 109
rows at `I3`, 8 at `I2`, 5 at `I1`, and 255 at `I0`; 122 of 377 rows are at
least `I1`. No provider, production payment, callback, worker, deployment or
reconciliation drill was exercised; exact-candidate evidence remains open.
007D is active.

## WO-007D — Shared bounded outbound HTTP

Deliver:

- lifespan-owned HTTP client registry with explicit startup/shutdown;
- provider-specific timeout/pool policy and bounded response parsing;
- safe aggregate request telemetry only: provider/operation/status/latency/
  result code, never URL query, headers, credentials or raw provider body;
- migrate payment adapters and FreeKassa operations first; document any
  unrelated per-operation clients left for later owner slices.

Row eligible after proof: `REL/HTTP-001` to local `I3` only for the declared
payment/provider surface; broader platform migration remains explicit.

### 007D local closure — 2026-08-21

- `outbound_http.py` now owns one FastAPI-lifespan payment HTTP registry with a
  reusable session per provider policy and explicit total, connect, socket-read,
  pool and JSON-object response-byte bounds;
- Lava.top, Cardlink, Pally, Platima and the historical FreeKassa API wrapper
  receive the registry explicitly. The provider adapter contains no
  `ClientSession()` construction; FreeKassa uses a closed operation allowlist
  and no longer logs a raw response body;
- telemetry and its aggregate snapshot contain only provider, closed operation,
  status, integer latency and closed result code. URL/query, auth/request
  headers, credentials, request fields, response body and exception text are
  absent;
- FreeKassa's one-off operator probe now creates and closes the same registry
  explicitly. The local signed SCI builder performs no outbound HTTP;
- focused lifecycle/policy/limit tests passed `7/7`; composition/admin/provider
  checks passed `22/22`; the exact payment/provider/callback/outbox matrix passed
  `135/135` plus `12` subtests. Scoped Ruff and `git diff --check` PASS.

`REL/HTTP-001` advances from `I0` to local `I3` for the named payment/provider
surface only. The distribution is now 110 rows at `I3`, 8 at `I2`, 5 at `I1`,
and 254 at `I0`; 123 of 377 rows are at least `I1`. Telegram, email, auth,
panel, catalog, news, support-AI, standalone-script and bot-to-portal clients are
inventoried but not claimed migrated. No provider/deploy/runtime pool or latency
evidence is claimed. 007E is active.

## WO-007E — Non-blocking payment DB strategy

Deliver:

- payment handlers call complete synchronous DB use cases through Starlette's
  bounded threadpool; each use case opens/closes its own session and owns its
  transaction;
- no session or lazy ORM object crosses an `await` boundary;
- concurrency/fault tests show a slow DB payment use case does not stall an
  independent async request and rollback leaves no partial fulfillment;
- expose bounded pool/transaction duration/failure counters without SQL or
  parameters.

Row eligible after proof: `REL/API-001` to local `I3` for payment routes. The
remaining non-payment async ORM inventory must stay named and cannot be claimed
complete from this slice.

### 007E local closure — 2026-08-21

- `payment_db_runtime.py` executes named sync payment use cases through
  Starlette/AnyIO's bounded threadpool and exposes only integer active,
  max-active, start/complete/fail, queue-wait and duration counters;
- order prepare, durable provider failure/result, callback validation/event/
  reversal/fulfillment/delivery completion, start-99 and historical FreeKassa
  reads/authorization now create and close their sessions inside one worker
  thread. No session, query, lazy relationship or ORM row crosses `await`;
- post-payment panel sync loads a detached `(uuid, tg_id)` tuple before network
  I/O instead of retaining a `User` row across an await;
- slow-use-case concurrency proves an independent coroutine remains live;
  failure proof confirms rollback and close occur in the same worker thread;
  `/api/health.payment_db` remains fixed-shape and integer-only;
- focused threadpool/source/health tests passed `11/11`; exact callback/order/
  outbox/provider regression passed `139/139` plus `12` subtests; module/admin
  checks passed `6/6`. Scoped Ruff and `git diff --check` PASS.

`REL/API-001` advances from `I0` to local `I3` for payment routes only. The
distribution is now 111 rows at `I3`, 8 at `I2`, 5 at `I1`, and 253 at `I0`;
124 of 377 rows are at least `I1`. The non-payment async ORM inventory,
production DB/thread-pool sizing, latency and fault evidence remain open. No
deploy or production payment was executed. 007F is active.

## WO-007F — Payment bounded-context composition

Deliver:

- transport-only payment route slice and focused provider/application/outbox
  modules with explicit imports;
- remove changed payment business rules from `api.py` while preserving tested
  compatibility exports and route order;
- update module map and canonical payment/operations owners;
- source/size/architecture regression prevents duplicate parser or a second
  payment implementation from returning to the composition root.

Rows eligible after proof: `REL/ARCH-002` and `REL_GATE/GATE-D` to the highest
honest local index supported by the remaining portal inventory.

### 007F local closure — 2026-08-21

- `api_payment_routes.py` is the dedicated ordered payment transport slice. It
  registers the former public-slice payment block in the same exact position;
  route-table regression proves order equality and no duplicate paths;
- `payment_callback_application.py` owns callback validation, immutable-order
  comparison, reversal/fulfillment, delivery evidence and notification
  orchestration through an explicit dependency contract. `api.py` constructs
  that contract and retains only a thin compatibility delegate;
- immutable order/result authority, provider adapters, transactional
  entitlement outbox, bounded reusable provider HTTP and bounded payment DB
  execution remain in their focused modules. The transport slice contains no
  `SessionLocal`, callback persistence or provider-result business rules;
- source/architecture checks prevent payment decorators from returning to the
  public slice, prevent callback orchestration from returning to `api.py`, and
  require the focused owner modules and exact ordered slice list;
- the exact payment/provider/callback/outbox matrix passed `142/142` plus `12`
  subtests. Module/retention/admin/app-first/auth/subscription regression passed
  `185/185` plus `8` subtests. Scoped Ruff PASS;
- `REL_GATE/GATE-D` advances from `I0` to local `I3`. `REL/ARCH-002` advances
  only to `I2`: the payment seam is implemented and verified, but the remaining
  large public/admin/action-service inventory prevents a broad portal
  decomposition claim.

The distribution is now 112 rows at `I3`, 9 at `I2`, 5 at `I1`, and 251 at
`I0`; 126 of 377 rows are at least `I1`. Production provider credentials,
callbacks, refund/chargeback/reconciliation drills, deployed DB/HTTP/outbox
behavior and exact-candidate evidence remain open. No deployment or production
payment was executed. WO-007 is locally complete.

## WO-007G follow-up — Admin domain slices

`WO-007G-admin-domain-slices.md` repairs a later composition regression without
raising its ceiling. The `7,237`-line admin slice is now a `4,336`-line base
admin slice plus ordered `2,774`-line guarded-action and `153`-line guarded-
network slices. All continue to re-export through the single legacy `api.*`
surface; there is no second process, route table or business authority.

The router-required backend matrix passed `154` tests plus `8` subtests, the
exact action/network matrix passed `33/33`, policy/manifest/probe tests passed
`16/16`, and the imported route table has `300` unique method/path pairs with
no duplicates. `REL/ARCH-002` remains `I2`: the public slice and the bounded but
still `8,365`-line action-intent service are retained inventory before an `I3`
claim. Historical 007A–007F counts above are not rewritten.

## WO-007H follow-up — Public and managed-client route slices

`WO-007H-public-client-route-slices.md` splits the retained `5,822`-line
public route module into a `2,019`-line public bootstrap owner and a
`3,980`-line managed-client owner. The composition root remains one process and
loads twelve explicit slices. Payment transport stays free of direct DB session
lifecycle.

The split also exposed and fixed a restored-owner reload defect in the
compatibility loader. The exact mixed API sequence that reproduced the defect
now passes `234` tests plus `12` subtests in one process; focused architecture,
payment and policy tests pass `25/25`, network/module tests pass `16/16`, and
the imported table retains `300` unique method/path pairs with no duplicates.
`REL/ARCH-002` remains `I2` because the `8,365`-line action-intent service is
still explicit remaining inventory. Historical 007A–007G results above are not
rewritten.

## WO-007I follow-up — Action Intent domain/runtime boundary

`WO-007I-action-intent-runtime.md` closes the final declared local architecture
inventory. The former 8,365-line Action Intent service is a 6,488-line domain
policy owner plus a 2,034-line generic persistence/execution runtime. The
runtime receives the sole live `ACTION_POLICIES` mapping explicitly and cannot
register actions or routes; thin wrappers preserve all established imports.

Action/policy/architecture tests pass `33/33`, the broad admin/Operator Center
matrix passes `68/68`, manifest/probe contracts pass `32/32`, and the imported
route table remains 300 unique method/path pairs with no duplicates.
`REL/ARCH-002` advances from `I2` to local `I3`; deployed PostgreSQL/load,
production operator actions, rollback and exact-candidate evidence remain open
before `I4`. Historical 007A–007H outcomes are not rewritten.

## Verification

Minimum focused commands from platform root:

```powershell
python -B -m pytest -p no:cacheprovider tests/test_api_payments_callbacks.py tests/test_lavatop_payment_providers.py tests/test_payment_email_readiness_smoke.py -q
python -B -m pytest -p no:cacheprovider tests/test_module_slices.py tests/test_worker_retention.py tests/test_admin_payments_api.py -q
python -B -m pytest -p no:cacheprovider portal_bot/tests/test_app_first_api.py portal_bot/tests/test_app_first_service.py tests/test_api_auth_and_tickets.py tests/test_subscription_preview_api.py -q
python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q
python -B scripts/agent_context_packet_audit.py --platform-context-root .
python -B scripts/check-links.py
python -B scripts/check_script_manifest.py
git diff --check
```

Add the smallest service/migration/concurrency/outbox tests needed by each
slice. Run broader portal/payment regression after the focused gates.

## Ledger ownership and exit

WO-007 owns the seven Phase 05 rows:

- `REL/PAY-001`, `PAY-002`, `API-001`, `HTTP-001`, `ARCH-002`;
- `REL_GATE/GATE-D`;
- `REL_DOD/DOD-08`.

No row advances from this document alone. WO-007 is locally complete only when
007A–007G are implemented and exact-current tests pass. Production provider
credentials/callbacks, refund/chargeback/reconciliation drills, deployment,
live pool/latency observations and real payment remain `I4` gates.
