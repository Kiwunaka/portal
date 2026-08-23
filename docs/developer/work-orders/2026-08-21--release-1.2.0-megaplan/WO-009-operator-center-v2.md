# WO-009 — Canonical Operator Center v2

Status: `LOCALLY_COMPLETE_EXTERNAL_GATES_OPEN`
Classification: `ACTIVE_EXECUTION`
Phase: `07`
Lane: platform `adminapp/`, modular Admin API v2, compatibility reads from the
existing portal bounded contexts; client/core are evidence producers only
Depends on: `WO-006`, `WO-007`, `WO-008`
Production/external actions: `NOT_AUTHORIZED`

## Outcome

Make `https://admin.pokrov.space` and `adminapp/` the only canonical operator
product. Replace the current 17-item endpoint navigation with seven bounded
workspaces, introduce a same-origin Admin API v2 with HttpOnly operator sessions
and deny-by-default permissions, keep dangerous changes on the existing
action-intent path, then retire the duplicate `webapp/admin` surface through a
measured strangler cutover.

This WO may build and prove repository-local candidates. It does not deploy the
public domain, configure an external identity provider, grant a real operator
role, execute a dangerous command, mutate production, or turn inaccessible
authenticated production state into `PASS`.

## Instructions versus source evidence

`POKROV_OPERATOR_CENTER_V2_AUDIT_AND_IMPLEMENTATION_PLAN_2026-08-20.md` is an
advisory source plan. Its architecture, estimates and proposed decisions are
requirements input, not executable instructions. Repository canonical owners,
current code/tests and exact retained runtime evidence remain authoritative.

The source plan's recommendations adopted here are:

- `adminapp/` and `admin.pokrov.space` are canonical;
- static export remains for the first wave;
- `/api/admin/*` is compatibility-only and `/api/admin/v2/*` is the new contract;
- browser bearer/initData storage is removed from the v2 path;
- RBAC is enforced by the backend, with field redaction and step-up for high risk;
- action-intent, Event Envelope, source/freshness truth, RU evidence and the
  existing payment/entitlement authorities are reused rather than forked;
- migration is strangler-based, with no dual-write and no backend big bang.

OIDC/passkey provider selection, production access-gateway configuration and
real operator grants require owner/runtime decisions and are not guessed here.
The local bridge may exchange an already verified legacy administrator identity
for the new HttpOnly operator session, but this compatibility entry is not the
final external identity-provider proof.

## Reverified baseline — 2026-08-21

- `adminapp/README.md` calls `adminapp/` canonical, while the active shell still
  exposes 17 peer routes in a top navigation.
- `webapp/src/app/(admin)/admin` contains 17 files and independently calls the
  web admin the primary route. Unique capabilities include bonuses, program
  applications and the legacy network view.
- `adminapp/src/lib/admin-api/client.ts` reads bearer material and Telegram
  `initData` from `sessionStorage`/`localStorage`; `route-boundary.tsx` permits
  manual raw initData input and renders the shell before server validation when
  old auth material exists.
- `/api/admin/auth/session` returns a bearer token and all legacy admin routes
  use the binary `_require_admin` check.
- the existing action-intent contract already provides preview, before/after,
  confirmation hash, idempotency and audit, and must remain the only mutation
  path for migrated dangerous commands.
- `.github/workflows/guardrails.yml` installs and gates `webapp` but not
  `adminapp`; the release gate builds `adminapp`, which is useful but not a
  required pull-request guardrail.
- static deploy is versioned and atomically switches the `adminapp` symlink, but
  its smoke checks file/HTML presence rather than exact product identity.
- authenticated production visual state remains `BLOCKED_BY_ACCESS`; no public
  deploy/readback claim follows from local work.

## Authority and collision decisions

- `adminapp/README.md` owns operator-frontend behavior and route/workspace truth.
- `docs/architecture/system-overview.md` owns the browser/BFF/session and bounded
  context architecture.
- `docs/architecture/api-contracts.md` owns Admin API v2 envelopes, permission
  and command contracts.
- `docs/operations/monitoring-and-visibility.md` owns source/freshness semantics,
  admin self-observability and operator interpretation.
- `docs/operations/deployment-and-access.md` owns build identity, access,
  candidate smoke and rollback.
- existing domain owners retain money, entitlement, telemetry, incident
  compensation and release evidence truth. Admin API v2 is a BFF/read-model and
  command-policy boundary, not a second domain database.
- `webapp/admin` receives no new feature implementation. Until destination
  parity is proved it remains a compatibility source; after parity it redirects
  to the canonical domain. There is no dual-write period.
- the existing `ServiceIncident` root is extended additively; no parallel outage
  root is introduced. Alert, incident and operator task stay distinct.
- client/core telemetry can support an investigation but cannot prove payment,
  entitlement or a trusted connection.

## Capability destination inventory

| Current capability | Current UI owner | V2 workspace/destination | Domain authority | Cutover rule |
|---|---|---|---|---|
| overview/action queue | `adminapp /` and `webapp/admin/dashboard` | `shift` / My Shift | ops overview, durable alerts, tasks | migrate counts, then legacy dashboard redirect |
| nodes and online runtime | both surfaces | `network/fleet`, `network/nodes/:code` | node health/runtime/observer services | source/age parity before redirect |
| traffic | `adminapp /traffic` | `network/traffic` | traffic rollups | preserve retirement labels |
| alerts | `adminapp /alerts` | `network/alerts` | durable alert service | alert is never silently promoted to incident |
| provider caps | `adminapp /provider-caps` | `network/providers` | provider quota service | retain guarded mutations |
| emergency network | `adminapp /emergency-network` | `network/emergency` | emergency catalog service | exact staging/promotion/rollback intent parity |
| FREE archive | `adminapp /free-tier` | `money/access/free-archive` | entitlement projection | read-only historical surface |
| users and device context | both surfaces | `support/users/:id` | account/device/observer read models | safe field inventory and command parity |
| tickets | both surfaces | `support/inbox`, `support/tickets/:id` | ticket repository/service | server assignment/SLA/version first |
| payments | both surfaces | `money/payments`, `money/reconciliation/:id` | signed callback/order/entitlement lineage | telemetry never becomes money truth |
| funnel | both surfaces | `growth/funnel` | acquisition projection | preserve denominator and redaction |
| promos/campaign slots | both surfaces | `growth/campaigns` | commercial campaign root/policy | legal/capacity/revision gates remain server-owned |
| referrals | both surfaces | `growth/referrals` | referral service | guarded decisions only |
| bonuses | `webapp/admin/bonuses` only | `money/access/bonuses` | entitlement/bonus service | migrate before legacy redirect |
| program applications | `webapp/admin/programs` only | `growth/programs` | program service | migrate before legacy redirect |
| legacy network routes | `webapp/admin/network` only | `network/routes` | network rollout service | no copy of route truth in frontend |
| release evidence | both surfaces | `releases/cockpit` | release handoff/evidence contracts | exact commits/artifacts and honest labels |
| broadcasts | both surfaces | `growth/broadcasts` | guarded broadcast service | preview/dry-run is not delivery proof |
| news | `adminapp /news` | `growth/news` | news-draft service | explicit operator publication only |
| operator/role/audit/source governance | partial audit only | `governance/*` | Admin v2 identity/RBAC/audit/source health | new canonical capability |

The public legacy shell is a deployment artifact, not a fourth implementation
owner. Its exact fingerprint must be identified during candidate cutover; the
source-plan crawler observation is not sufficient production evidence.

## Owned ledger rows

All Operator Center rows are owned here:

- foundation: `OC/OC-000`, `OC-100`, `OC-110`, `OC-120`, `OC-130`, `OC-140`;
- work and incidents: `OC-200`, `OC-210`, `OC-220`, `OC-230`;
- support/diagnostics: `OC-300`, `OC-310`, `OC-320`, `OC-330`, `OC-340`;
- network/money/access: `OC-400`, `OC-410`, `OC-420`, `OC-430`, `OC-440`;
- release/growth: `OC-500`, `OC-510`, `OC-520`, `OC-530`, `OC-540`;
- governance/cutover: `OC-600`, `OC-610`, `OC-620`, `OC-630`, `OC-640`.

No row advances solely because this work order exists. Each slice records exact
implementation and proof before updating `EXECUTION-LEDGER.csv`.

## WO-009A — Canonical oracle, build identity and required guardrail

Deliver:

- checked-in capability/workspace manifest and legacy freeze/deprecation policy;
- deterministic `__build.json` and route manifest in every static candidate,
  including application name, frontend commit, build time, route manifest hash
  and expected API schema;
- `/api/admin/v2/meta` with bounded backend/schema/release identity and no secret;
- PR guardrail for adminapp install, lint, production build and focused E2E;
- local deploy validation that rejects a missing/mismatched admin identity and a
  retained rollback pointer contract;
- canonical documentation and regression tests for the oracle.

Eligible rows after proof: `OC-000`, `OC-120`, `OC-130`.

## WO-009B — Operator session, RBAC and Admin API v2 security boundary

Deliver:

- modular `portal_bot/admin_v2/` package without `bootstrap_slice(globals())`;
- opaque HttpOnly/Secure/SameSite=Strict `__Host-` session, idle and absolute
  expiry, CSRF, session inventory/revoke and `Clear-Site-Data` logout;
- compatibility bootstrap from an already verified legacy admin identity, with
  no session token in the response and no browser storage;
- persistent operator/role/session records, role registry, environment scope,
  deny-by-default permission dependency and permission snapshot in audit;
- response/error/source envelope and explicit permissions for every v2 route;
- high-risk step-up contract; actual external IdP/passkey proof remains manual.

Eligible rows after proof: `OC-100`, `OC-110`, `OC-120`, `OC-600`, `OC-610`.

## WO-009C — Seven-workspace shell and stable data boundary

Deliver:

- seven workspace navigation groups: shift, support, network, money, growth,
  releases and governance;
- accessible desktop rail, compact tablet drawer and bounded mobile primary nav;
- topbar identity: environment, frontend/API/schema/release fingerprints,
  source health, session expiry and mismatch banner;
- global search shell with safe previews and no sensitive recent-search values;
- route-scoped refresh registry; remove DOM text-button discovery;
- typed v2 boundary/adapters, stable last-good-data/freshness states and URL-owned
  filters/selection. A query library may be added only if it replaces concrete
  duplicated behavior in the migrated slice.

Eligible rows after proof: `OC-140` and supporting `OC-120`.

## WO-009D — My Shift, operator task and Incident Room

Deliver:

- distinct additive operator task model/read model with owner, team, status,
  priority, due time, next action, source and linked entity;
- My Shift queues for mine/team/unassigned, failed commands, tickets, incident
  work, payment review, release blockers and source failures;
- additive incident lifecycle, optimistic version, owner/team, impact, timeline,
  notes, linked entities, runbook, communications, postmortem and follow-ups;
- explicit alert acknowledge/create/link/false-positive transitions;
- existing compensation preview/apply integrated through action-intent without
  duplicate grants or a second compensation authority.

Eligible rows after proof: `OC-200`, `OC-210`, `OC-220`, `OC-230`.

## WO-009E — Support Inbox, User 360 and diagnostics

Deliver:

- server-owned ticket priority, queue, assignment, SLA, waiting/escalation,
  incident/attempt link and optimistic version;
- Support Inbox claim/assign/reply/internal-note/macro flows with collision
  protection and guarded mutations;
- User 360 entity header and grouped installation/session/attempt timeline;
- bounded diagnostic fingerprints and correlated attempt explorer;
- safe client/core evidence adapter that preserves Event Envelope privacy,
  support-bundle TTL/access audit and trusted observer authority.

Eligible rows after proof: `OC-300`, `OC-310`, `OC-320`, `OC-330`, `OC-340`.

## WO-009F — Network, money, growth, release and governance parity

Deliver vertical migrations for:

- Fleet/Node 360/RU/emergency/providers with authority and age;
- payment reconciliation/payment 360/entitlement lineage;
- bonuses, applications, access grants, promos, referrals, broadcasts and news;
- release candidate/deployment/rollout/adoption/regression/evidence cockpit;
- operator/session/JIT/audit/source/privacy/retention governance.

Every mutation reuses action-intent and its owning domain service. Reads may be
shadow-compared; writes are never duplicated.

Eligible rows after proof: `OC-400..540`, `OC-600..620`.

## WO-009G — Strangler cutover, authenticated proof and rollback

Deliver:

- route/capability parity matrix with counts, actions and redaction checks;
- legacy read-only mode, canonical redirects and removal of the stale public
  shell only after exact candidate proof;
- browser/accessibility/responsive/performance/security matrix;
- authenticated staging and production read-only smoke with exact build/API
  fingerprints and retained screenshots;
- real static rollback drill plus backward-compatible API/DB readback;
- canonical docs cleanup after redirect, without erasing history.

Eligible rows after proof: `OC-630`, `OC-640`; all other rows require their own
exact-candidate evidence before `I4` and observation before `I5`.

## Global acceptance oracle

- exactly one canonical frontend/domain and every capability has one owner and
  destination;
- public candidate returns the exact expected build/route/API fingerprints;
- JavaScript cannot read the operator session secret and v2 stores no bearer or
  raw initData in Web Storage;
- every v2 route names a backend permission; default is deny;
- high-risk mutations require permission, step-up, reason and action-intent;
- My Shift items expose owner/status/age/next action;
- incident lifecycle, support assignment/SLA, grouped user attempts,
  fingerprints, source authority and payment lineage are server-owned;
- admin CI is required and exact-candidate authenticated smoke is retained;
- legacy paths redirect only after parity; rollback is actually exercised;
- privacy/retention inventory passes and no unresolved P0 remains.

## Verification matrix

Minimum local verification grows with each slice:

- `python -B -m pytest -p no:cacheprovider` for focused Admin v2/model/API
  contracts plus existing admin action/ops/payment regressions;
- from `adminapp/`: `npm.cmd run lint`, `npm.cmd run build`, focused Playwright,
  then full `npm.cmd run test:e2e` at slice closure;
- from `webapp/`: build/lint and redirect tests when legacy routing changes;
- generated build/route/OpenAPI/SDK clean checks;
- `python -B scripts/check-links.py`, agent docs checks and `git diff --check`;
- no production, external IdP, real operator, real payment, real command or
  authenticated public claim without separate retained evidence.

## Rollback

- all database changes are additive; legacy columns/endpoints remain through at
  least one observed release cycle;
- v2 UI is feature/candidate gated until parity; legacy is read-only fallback;
- static rollback switches the versioned adminapp pointer to the retained prior
  bundle; it does not run down-migrations;
- v2 command adapters call the existing single domain/action-intent path, so
  disabling the v2 route does not require command-data reconciliation;
- a failed session/RBAC migration fails closed and never falls back to a browser
  bearer on a v2 route.

## WO-009A closure — 2026-08-21

`WO-009A` is locally complete:

- `adminapp/operator-center.manifest.json` is the checked-in canonical oracle.
  It freezes all 17 current routes, maps them and the three unique
  `webapp/admin` capabilities into exactly seven target workspaces, and records
  the no-new-legacy-feature/no-dual-write cutover policy;
- `adminapp/scripts/generate-build-contract.mjs` deterministically creates
  `__build.json` and `__routes.json`. The current route-manifest SHA-256 is
  `976030111b170e399639d1412403bd4c6dfe7c5581e8a79fd212e34875d48d2f`;
- `portal_bot/admin_v2/meta.py` and guarded `GET /api/admin/v2/meta` establish
  the modular v2 identity envelope without inventing missing deployment truth;
- repository guardrails now install, lint, build and run the full `adminapp`
  Playwright suite. This is a required workflow definition, not proof that
  hosted branch protection or hosted CI has executed for an exact candidate;
- static deploy validation rejects missing/mismatched Operator Center identity
  and the obsolete `POKROV API superadmin v1` bundle, reads both identity files
  during smoke and records the previous release symlink as
  `adminapp.rollback`. No production deploy or rollback drill was performed.

Retained local proof:

- manifest/deploy contract tests: `8 passed`;
- focused Admin v2 meta API tests: `2 passed`, `31 deselected`;
- `npm.cmd run build:contract`: `PASS` with the SHA-256 above;
- `npm.cmd run lint`: `PASS`;
- production static build: `PASS`, Next.js `16.2.10`, `19` static pages;
- full Playwright: `60 passed` in `57.4s`;
- static deploy `--plan-only` with `127.0.0.1`: `PASS`; it bundled all three
  local static surfaces and opened no SSH connection.

`npm.cmd ci` reported six high-severity advisories in the existing locked
dependency graph. They are not hidden or auto-fixed in this bounded slice;
dependency upgrade and regression review remain required before exact-candidate
release qualification.

Ledger effect: `OC-000` and `OC-130` advance to `I3`; `OC-120` advances to
`I2`; `OC-100`, `OC-110` and `OC-140` advance to `I1`. The next active slice is
`WO-009B`.

## WO-009B closure — 2026-08-21

`WO-009B` is locally complete:

- `portal_bot/admin_v2/roles.py`, `security.py` and `router.py` form a real
  modular package. The v2 router is installed before the frozen legacy slices
  and does not use `bootstrap_slice(globals())`;
- `AdminOperator`, `AdminOperatorRole`, `AdminOperatorSession` and
  `AdminOperatorAudit` are additive persistent records created through the
  existing locked `Base.metadata.create_all` startup path. Roles and sessions
  are environment-scoped; raw session tokens are never stored;
- compatibility bootstrap verifies the existing legacy admin identity, issues
  an opaque token only as the Secure/HttpOnly/SameSite=Strict/Path=/ `__Host-`
  cookie and returns no session secret in JSON. The canonical frontend removed
  bearer/initData reads and writes, purges the old auth keys and reads raw
  initData only from the live Telegram runtime for the exchange;
- idle and absolute expiry, active-session bounds, `/auth/me`, inventory,
  self-revoke, logout with `Clear-Site-Data`, CSRF and trusted-Origin checks are
  enforced server-side. Short/missing secrets, invalid environment, revoked
  role/session, expired session, unknown role/permission and invalid CSRF fail
  closed;
- the static role registry enumerates every permission. Protected v2 routes use
  deny-by-default permission dependencies; frozen legacy routes accept a v2
  cookie only through `legacy.admin.access` and keep CSRF on unsafe methods;
- compatibility step-up re-verifies the same allowlisted Telegram actor. The
  permission contract rejects a missing or stale step-up for high-risk rights;
  audit rows for bootstrap/revoke/step-up retain environment, result/reason and
  exact role/permission snapshots with a normalized correlation ID.

Retained local proof:

- focused auth/RBAC/API: `7 passed`, `30 deselected`; cases include no token in
  body, exact cookie attributes, CSRF denial, inventory/revoke/logout,
  role revocation, idle expiry, permission default-deny, fresh/stale step-up and
  audit persistence;
- full admin ops API: `37 passed`; action-intent: `20 passed`; admin payments:
  `3 passed`; payment callbacks: `88 passed`, `12 subtests passed`; legacy
  route-gap coverage: `7 passed`; operator observability API/service:
  `9 passed`;
- module/manifest/policy/error-header contracts: `14 passed`; Ruff and
  `py_compile`: `PASS`;
- `adminapp` lint and production build: `PASS`, Next.js `16.2.10`, `19` static
  pages, unchanged route-manifest SHA-256
  `976030111b170e399639d1412403bd4c6dfe7c5581e8a79fd212e34875d48d2f`;
- full Playwright: `60 passed` in `57.6s`, including server-first `/auth/me`,
  storage cleanup, compatibility bootstrap and all 17 frozen routes.

The broad source-plan rows are not complete. External OIDC/passkey, JIT and
break-glass governance, field-level redaction, OpenAPI/generated SDK, operator
management UI, audit explorer/export/sensitive-access log/command lineage,
hosted CI, authenticated staging/production proof and rollback remain open.
The existing `/api/admin/auth/session` bearer endpoint is retained only for the
frozen fallback during the strangler cycle. No deployment, real operator/IdP,
production role migration or public readback was performed.

Ledger effect: `OC-100` and `OC-110` advance from `I1` to `I2`; `OC-600` and
`OC-610` advance from `I0` to `I2` for their persistent backend foundations;
`OC-120` remains `I2` with the security/error boundary now implemented. No OC
row advances to `I3` because each named source-plan row still includes one of
the unimplemented capabilities above. The next active slice is `WO-009C`.

## WO-009C closure — 2026-08-21

`WO-009C` is locally complete:

- the canonical shell now has exactly seven active workspaces and 24 direct
  routes: seven workspace entries plus the frozen 17 capability entries. The
  checked-in manifest state is `workspace-shell-active`; its SHA-256 is
  `8516df1cb79fcafe5d8198562ae5a3b737621916660dddfaffced2f9dd886fce`;
- desktop uses an accessible left rail, tablet uses the full navigation dialog,
  and mobile exposes four bounded primary workspaces plus «Ещё». Every route
  keeps a Russian level-one heading, one route toolbar and no document-wide
  horizontal overflow in the tested viewports;
- the topbar joins the frontend build contract, `/api/admin/v2/meta` and the
  server session envelope. It exposes environment, frontend revision/source
  state, API schema, client release, idle expiry and required-source freshness;
  an identity/schema mismatch produces an explicit cutover-stop alert;
- global search keeps its strict safe-preview/canonical-href filter and does not
  retain the query or results after close or in Local/Session Storage;
- route resources explicitly register refresh callbacks. DOM button discovery
  and page reload fallback are removed; a failed refresh retains last-good data
  and visibly degrades freshness/status. Existing URL-owned filters, tabs and
  selections remain reproducible;
- typed identity/session adapters and a read-only governance session inventory
  use the v2 envelope. The page explicitly does not claim role management, JIT,
  break-glass, audit export or other later governance work.

Retained local proof:

- `adminapp` lint: `PASS`; production build: `PASS`, Next.js `16.2.10`, `26`
  static pages including all 24 operator routes;
- manifest/build-contract tests: `6 passed`;
- focused 009C Playwright checks: `32 passed`, then five new identity/source/
  last-good/search checks: `5 passed`;
- full Playwright regression: `63 passed` in `1.0m`. It covers all 24 direct
  routes, seven navigation regions, responsive layout, API-source isolation,
  mismatch alert, route-scoped refresh and storage-free search history.

No hosted CI, authenticated staging/production, real operator, public readback,
deploy or rollback is claimed. `OC-140` advances from `I1` to `I3`; `OC-120`
remains `I2` with stronger typed-boundary/error/freshness evidence because its
broader generated-SDK and redaction work remains open. The next active slice is
`WO-009D`.

## WO-009D closure — 2026-08-21

`WO-009D` is locally complete:

- additive `OperatorTask`, append-only `OperatorIncidentEvent` and typed
  `OperatorIncidentLink` records provide a separate work model without copying
  ticket/payment/release/alert authority. Existing `ServiceIncident` remains the
  public status and compensation root and gains environment-scoped workflow
  version, owner/team, impact, update, runbook, communications and postmortem
  fields. `OpsAlert` gains its own version and optional incident link;
- `/api/admin/v2/shift`, `/tasks`, `/incidents` and `/incidents/{id}` expose
  bounded read models behind explicit permissions. My Shift includes all eight
  required task/attention families and does not expose account IDs from ticket
  or payment projections;
- task create/update, incident create/update/link/compensate and alert
  acknowledge/false-positive/link/create-incident are registered policies in
  the single action-intent registry. Environment/operator/actor context is
  injected server-side; execute rechecks optimistic versions and appends
  incident timeline evidence;
- legacy incident mutation and alert-ack routes no longer write directly: they
  resolve and execute an owned stored intent. Read-only compensation dry-run is
  retained. L3 compensation requires fresh step-up and calls only the existing
  idempotent incident compensation/entitlement grant service;
- `adminapp` now has real My Shift and Incident Room routes. Alert acknowledge,
  false-positive and alert→incident link/create use the same prepare/confirm/
  execute dialog. Last-good route resources, explicit source state and no raw
  provider/customer payload behavior are retained.

Retained local proof:

- server `py_compile`: `PASS`; focused/relevant API, action-intent,
  compensation, migration, manifest and client regression: `79 passed`;
- additive legacy-SQLite migration rehearsal is rerunnable and preserves an
  existing incident row while adding work/incident/alert fields and indexes;
- `adminapp` lint and production build: `PASS`, Next.js `16.2.10`, `27`
  generated pages and `25` direct operator routes. Manifest SHA-256 is
  `61bde93f6edcd1fbbd616fe004e5be721a8cbe20ec175333d5ead21c31b55f94`;
- focused My Shift/Incident Room/alert action tests: `3 passed`; the first full
  Playwright run produced `64 passed, 1 failed` only because its static
  navigation expectation still counted the pre-009D route set. The updated
  navigation/direct-route/source-isolation checks then passed `3/3`; the final
  full Playwright regression passed `65/65` in `1.0m`.

No hosted CI, authenticated staging/production, production migration, deploy,
real compensation, public readback or rollback is claimed. `OC-200`, `OC-210`,
`OC-220` and `OC-230` advance from `I0` to local `I3`. The distribution becomes
119 rows at `I3`, 31 at `I2`, 4 at `I1`, and 223 at `I0`; 154 of 377 rows are at
least `I1`. The next active slice is `WO-009E`.

## 2026-08-21 — WO-009E Support Inbox, User 360 and diagnostics

WO-009E is locally complete. The existing `SupportTicket` authority now owns
environment, priority, queue, assignment/team, waiting-on, SLA, escalation,
incident/attempt links and optimistic version through additive rerunnable
migrations. Support Inbox reads are server-filtered and server-ordered. Claim,
assign and workflow update are native v2 Action Intent policies; reply/status
and internal note retain compatible route shapes but use the same stored intent,
idempotency and version recheck. Internal notes are visible to operators and
excluded from user API/bot/helpbot reads.

User 360 groups allowlisted Event Envelope facts into opaque account,
installation, session and attempt references and bounded diagnostic
fingerprints. The attempt explorer has a separate sensitive-read permission.
Raw `meta_json`, install/device/session/trace identifiers, IP, URLs, configs,
keys and tokens are not returned. Existing observer truth and support-bundle
TTL/retention/access-audit summaries remain read-only inputs rather than new
ticket, account or bundle authorities.

Final self-review closed three projection boundaries before the gate: incident
metadata is resolved only inside the ticket environment; User 360 includes
canonical account-owned tickets while retaining the legacy direct-owner
fallback; and events without session/trace/attempt facts receive event-scoped
opaque correlation references instead of being falsely merged.

Retained local proof:

- relevant backend/API/action-intent/migration/observability/support-bundle and
  manifest regression: `131 passed in 309.50s`;
- legacy SQLite support migration executed twice and preserved rows while
  backfilling workflow/SLA/version/message visibility;
- adminapp lint and production build: `PASS`, Next.js `16.2.10`, `27` pages,
  `25` direct routes, manifest SHA-256
  `96e00b508c25e181182fedc9a2a63d25491acf7c1803cd6866a360e5ea3c940d`;
- focused route-source repair: `1 passed`; final full Playwright regression:
  `66/66` in `1.1m`. The preceding full run was `65 passed, 1 failed` only
  because the source-isolation expectation still named the pre-009E ticket
  endpoint.

No hosted CI, authenticated staging/production, production migration, deploy,
real support data readback or rollback is claimed. `OC-300`, `OC-310`,
`OC-320`, `OC-330` and `OC-340` advance from `I0` to local `I3`. The
distribution becomes 124 rows at `I3`, 31 at `I2`, 4 at `I1`, and 218 at
`I0`; 159 of 377 rows are at least `I1`. The next active slice is `WO-009F`.

## 2026-08-21 — WO-009F1 Network fleet, Node 360 and emergency/provider work

WO-009F1 is locally complete. The network workspace now reads fleet, Node 360,
traffic, alerts, provider quotas, RU probe state and emergency catalog through
environment-scoped `/api/admin/v2/network/*` contracts. The BFF composes the
existing node observability, RU probe and emergency/provider authorities; it
does not create a second network database. Every response carries explicit
source authority/freshness, and host, panel, subnet, provider notes, updater
identity and raw probe/config material are omitted or reduced to opaque
fingerprints.

Node enable/disable/sync, provider quota changes, emergency catalog transitions
and alert silence use the single stored Action Intent boundary. Optimistic
context is rechecked at execution; destructive L3 actions require the existing
high-risk permission and fresh step-up. Invalid RU configuration now yields an
explicit bounded `ru_configuration_invalid` source/error instead of crashing
fleet/Node 360 or pretending that RU evidence exists. Final self-review also
fixed the v2 executor to always POST stored intents, corrected alert-silence
payload normalization and aligned browser fixtures with the real high-risk
action names.

Retained local proof:

- expanded backend/API/action-policy/migration/network/RU/emergency/support
  regression: `142 passed in 274.46s`;
- `adminapp` lint and production build: `PASS`, Next.js `16.2.10`, `27` pages,
  `25` direct routes and route-manifest SHA-256
  `295b85719bd445692ce68b9c293c9601776ad1adba890b7ae27b54392afcef32`;
- final full Playwright regression: `67/67` in `1.1m`.

No hosted CI, authenticated staging/production, real node/provider/emergency
mutation, RU-origin proof, deploy, public readback or rollback is claimed.
`OC-400`, `OC-410` and `OC-420` advance from `I0` to local `I3`. The
distribution becomes 127 rows at `I3`, 31 at `I2`, 4 at `I1`, and 215 at
`I0`; 162 of 377 rows are at least `I1`. The next active slice is `WO-009F2`
for payment reconciliation, entitlement lineage, access grants, promos,
bonuses and programs.

## 2026-08-21 — WO-009F2 money, access, bonuses and programs

WO-009F2 is locally complete. The production-only money workspace now exposes
payment summary/list/360, entitlement lineage, access/grant/outbox state, the
read-only FREE archive and promos through `/api/admin/v2/money/*`. The BFF
composes existing order, signed callback, claim, grant, outbox, catalog and
promo authorities; it creates no admin money ledger. Payment status and
callback status remain separate, mismatch queues are explicit, client
telemetry cannot confirm payment, and raw provider/order/claim/grant/outbox
payloads and buyer/provider identity do not reach the browser.

`/access`, `/bonuses` and `/programs` are real canonical routes. Stored
gift/access codes stay redacted; a newly generated code is visible only in the
successful L3 execute result and only while the dialog remains open. Wheel and
loyalty configuration use allowlisted reads and fingerprinted previews.
Program review is a version-bound L3 stored intent and calls the existing
program service, so the application decision and one idempotent entitlement
reward commit atomically. Payment reconcile, promo changes, code issuance and
bonus changes also reuse the single Action Intent registry; canonical screens
do not call their legacy mutation endpoints.

Retained local proof:

- full relevant Admin v2, Action Intent, policy, program and route-gap
  regression: `74 passed in 261.41s`;
- non-production commerce fail-closed, order/list/360 redaction, mismatch
  lineage, FREE archive, access redaction, promos, bonus defaults and atomic
  program reward are included in the API regression;
- `adminapp` lint and production build: `PASS`, Next.js `16.2.10`, `30`
  generated pages and `28` direct operator routes. Manifest SHA-256 is
  `772bd40d9209be3c16453b9bf3c0868e416d6a307bc6dbb067f90eecfe087179`;
- focused money/network browser regression: `15/15`; shell/accessibility:
  `35/35`; final full Playwright regression: `70/70` in `1.2m`.

No hosted CI, authenticated staging/production readback, real payment/access/
promo/program mutation, deploy or rollback is claimed. `OC-430` and `OC-440`
advance from `I0` to local `I3`. The distribution becomes 129 rows at `I3`, 31
at `I2`, 4 at `I1`, and 213 at `I0`; 164 of 377 rows are at least `I1`. The
next active slice is `WO-009F3` for the release cockpit, adoption/regression,
rollout controls, messaging and client/core evidence.

## 2026-08-22 — WO-009F3 release cockpit, rollout and messaging

WO-009F3 is locally complete. The canonical `/release` screen now reads an
explicit `/api/admin/v2/releases/*` cockpit that binds one candidate to exact
component revisions, artifact/descriptor SHA-256, separate current/brain/RU
evidence, eleven diagnostic gates, aggregate platform/version adoption,
release-health delta, version-bound support delta and known issues. Adoption and
health projections contain no account, installation, device, session, IP,
destination or arbitrary event metadata.

The versioned `release_rollout_v1` AppSetting is the single rollout policy
registry. Evidence-gated start, percent change, pause, rollback, minimum
supported version and health-gated observation close all use stored Action
Intent. L3 commands require high-risk permission and fresh step-up. Public and
authenticated client-app metadata read the same registry and fail closed to
zero rollout on pause, rollback request, invalid state or candidate/configured
artifact mismatch. Rollback deliberately returns
`external_artifact_switch=NOT_PERFORMED`; it is not external artifact rollback
proof.

Broadcast delivery, news drafts and live-update lineage now read bounded
`/api/admin/v2/growth/*` projections. `broadcast.send` and live-update writes
use the same growth Action Intent boundary; the existing compatibility executor
is invoked only under that stored intent. Delivery output omits recipient ids
and raw Telegram responses, while publication keeps `source_draft_id`. The
frontend also reads v2 envelope `meta.trace_id` as the operator-visible request
ID on failures.

Retained local proof:

- full Admin Ops/Payments, Action Intent/policy, manifest and release-service
  regression: `77 passed in 255.09s`;
- `adminapp` lint and production build: `PASS`, Next.js `16.2.10`, `30`
  generated pages, `28` direct operator routes and route-manifest SHA-256
  `9d37db1afabaa08774321049b9e99c91aa1ad642b9eaa4e35c03586bb8521457`;
- final full Playwright regression: `70/70` in `1.2m`, including exact release
  evidence, route-source isolation, v2 broadcast prepare/execute/status,
  uncertain-outcome no-retry and v2 error trace propagation.

No hosted CI, authenticated staging/production readback, real rollout or
broadcast/publication command, external artifact switch, device/signing/RU
proof, deploy or rollback drill is claimed. `OC-500`, `OC-510`, `OC-520`,
`OC-530` and `OC-540` advance from `I0` to local `I3`. The distribution becomes
134 rows at `I3`, 31 at `I2`, 4 at `I1`, and 208 at `I0`; 169 of 377 rows are
at least `I1`. The next active slice is `WO-009F4` for operator governance,
audit exploration, sensitive-access visibility and privacy/retention parity.

## 2026-08-22 — WO-009F4 governance, audit and privacy parity

WO-009F4 is locally complete. The canonical `/governance` workspace now uses
explicit environment-scoped Admin API v2 reads for operators, roles, sessions,
audit exploration, command lineage, sensitive-access history and retention
status. Standing, JIT and break-glass grants, suspension, revocation, session
revocation and access review reuse stored Action Intent, optimistic versions,
fresh step-up and the existing operator-security authority. Self-escalation,
temporal superadmin grants, regrant with a pending review and removal of the
last active superadmin fail closed.

Audit CSV export neutralizes spreadsheet formulas. Sensitive reads create a
same-request, fail-closed audit record, command lineage does not cross the
selected environment, and legacy support-bundle access is labelled as a global
authority because its source table has no environment column. Privacy status
reports raw anti-abuse deletion/anonymization cutoffs and backlog, diagnostic
bundle TTL/hold/backlog and the retained field inventory without exposing HMAC
secrets or raw identity material.

Retained local proof:

- final Admin Ops/Payments, Action Intent/policy, manifest, release-service and
  migration regression: `80 passed in 296.54s`;
- focused governance/migration/manifest regression: `9 passed in 5.62s`;
- anti-abuse privacy/retention regression: `13 passed in 38.83s`;
- documentation contract regression: `30 passed in 0.43s` and platform context
  audit: `PASS platform-context`;
- `adminapp` lint and production build: `PASS`, Next.js `16.2.10`, `30`
  generated pages, `28` direct operator routes and route-manifest SHA-256
  `343ee83d9dfb397dcc19d67f69a1796007a4bf90bf2f06dbbfe1f54cc8e9f19f`;
- final full Playwright regression: `72/72` in `1.3m`.

No hosted CI, authenticated staging/production readback, production migration,
real governance mutation, deploy or rollback is claimed. `OC-600`, `OC-610`
and `OC-620` advance to local `I3`. The distribution becomes 137 rows at `I3`,
29 at `I2`, 4 at `I1`, and 207 at `I0`; 170 of 377 rows are at least `I1`.
The next active slice is `WO-009G` for local route/capability parity, canonical
cutover gates and rollback tooling while external production gates remain
explicitly unproved.

## 2026-08-22 — WO-009G local cutover package

WO-009G is locally complete without claiming a public cutover. The checked-in
cutover matrix binds all `28` canonical routes to seven workspaces, owned reads,
action boundaries, redaction rules and explicit external gates. The route
manifest contains no `legacy-route-active` state. Four remaining browser reads
now use production-only Admin API v2 compatibility projections for shift
overview, online support context, growth funnel and referrals. Referral queue
processing now prepares and executes through the growth Action Intent boundary.

Five legacy read patterns remain behind bounded v2 adapters: user list, user
detail, investigation, search and promo-slot reads. They are declared
read-only, add no feature or write authority, and are not evidence that the
legacy public shell was retired. There is no dual-write path. The static bundle
contract binds both the route-manifest and cutover-matrix SHA-256, rejects
compiled migrated legacy endpoints and browser bearer/initData storage, and
enforces a bounded JavaScript budget.

The deploy helper now has an explicit, confirmation-gated adminapp rollback
mode. It validates exact current and rollback route/cutover fingerprints,
constrains both symlink targets to versioned adminapp release directories,
verifies both bundle identities and atomically swaps the served and retained
rollback pointers. The command was tested as generated shell text only; it was
not executed against staging or production.

Retained local proof:

- final Admin Ops/Payments, Action Intent/policy, manifest, release-service,
  migration and deploy-helper regression: `88 passed in 280.36s`;
- focused cutover referral browser regression: `1/1`; final full Playwright:
  `72/72` in `1.3m`;
- `adminapp` lint: `PASS`; cutover verifier: `PASS` with `28` routes, seven
  workspaces, seven JavaScript chunks, `1,657,712` total JavaScript bytes and
  `1,031,197` largest chunk bytes;
- route-manifest SHA-256:
  `174894555db7c842f2c2b13f5ed8622cd9f8a31b8d93a2b0e5577a70984d3bc3`;
- cutover-matrix SHA-256:
  `d766379788cc08d3ec7a2492ea45fdc8b76b3a8c8054e282193127c049c53717`.

Authenticated staging/production readback, retained screenshots, actual
redirect/removal of the public legacy shell, current/brain/RU origin checks and
a real static rollback remain `BLOCKED_BY_ACCESS` or `NOT_RUN`. `OC-630`
advances to `I1` because the exact production-proof oracle and fail-closed gates
are verified. `OC-640` advances to `I2` because the local retirement package is
implemented but public retirement and rollback proof are not. The distribution
becomes 137 rows at `I3`, 30 at `I2`, 5 at `I1`, and 205 at `I0`; 172 of 377
rows are at least `I1`. Phase 08 may proceed locally while these external
Operator Center gates remain open for the exact release candidate.

## 2026-08-22 — WO-009E2 support operations closure

The canonical ticket detail now has one chronological case timeline and one
allowlisted diagnostic summary with platform/app/build plus permissions, Core,
TUN, DNS and egress facts. The global palette queries the existing general
search and an environment-scoped support search together; case IDs, opaque
support-bundle refs and safe correlation codes resolve only to canonical ticket
links. Raw upload IDs, object names, owner identity and Event metadata are not
returned.

Known issues are matched by error code and nullable/exact app version, build
and platform scope. Their safe summary and incident/release references are
observational actions only. Support-bundle UI shows L1 only the safe summary.
L2, the explicit SRE role and Security require `support.sensitive.read`, fresh
step-up and an allowed reason. The existing actor-bound grant is case scoped,
expires, is atomically single use, verifies the private ciphertext object's
size/SHA-256 and audits both grant and download with actor, reason and UTC time.

Retained local proof:

- support/observability service, API, role/manifest and frontend contract
  regression: `33/33`; the new end-to-end Admin API v2 grant/search test:
  `1/1`; the surrounding Admin API v2 file passed its `45` tests in the combined
  regression; the post-change actor-role attribution regression passed `4/4`;
- `adminapp` TypeScript, ESLint and production build: `PASS`, Next.js
  `16.2.10`, `30` static pages and `28` direct operator routes;
- cutover verifier: `PASS` with seven workspaces, seven JavaScript chunks,
  `1,674,703` total JavaScript bytes and `1,048,188` largest chunk bytes;
- final full Playwright regression: `75/75` in `1.3m`, including safe search,
  five-fact diagnostics, known-issue display, L1 denial and L2 one-use grant.

No hosted CI, authenticated staging/production readback, real support-data
access, production bundle download, role assignment, deploy or rollback is
claimed. `OBS/OBS-061..066` advance from `I0` to local `I3`. The distribution
is now 260 rows at `I3`, 33 at `I2`, 47 at `I1` and 37 at `I0`; 340 of 377 rows
are at least `I1`, and 117 remain below `I3`.
