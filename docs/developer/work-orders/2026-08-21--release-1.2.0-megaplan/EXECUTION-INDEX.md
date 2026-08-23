# POKROV 1.2.0 Execution Index

Last updated: 2026-08-23

## Item scale

| Index | Meaning | Required evidence |
|---|---|---|
| `I0` | Captured | Source-plan row exists; current state not yet reverified. |
| `I1` | Verified | Current authority/code/runtime evidence confirms scope and owner. |
| `I2` | Implemented | Authorized change exists in a scoped diff; required canonical owner is updated. |
| `I3` | Locally proved | Focused and relevant regression checks pass for the exact change. |
| `I4` | Candidate proved | Required exact-candidate CI/manual/runtime evidence is retained with honest labels. |
| `I5` | Promoted and observed | Immutable candidate is promoted through the correct branch/channel and required post-promotion observation passes. |

`Blocked`, `Deferred`, `Rejected` and `Not requested` are explicit statuses, not index values and never count as a pass. An item can advance only through retained evidence; prose confidence does not move the index.

## Primary key and duplicate handling

The ledger primary key is `(plan,id)`. This is mandatory because the technical findings table and observability backlog both contain an `OBS-001`. The keys are therefore `REL/OBS-001` and `OBS/OBS-001`.

## Plan aggregates

Report each plan as `count at or above current index / total`, plus blocker counts. Do not average index numbers. A phase is:

- `Not started` when all release-bound rows are `I0`;
- `In discovery` when any row is `I1` and none reaches `I2`;
- `In implementation` when any row is `I2`;
- `Locally proved` only when every required row is at least `I3`;
- `Candidate proved` only when every required row is at least `I4` and manual/owner gates are explicitly resolved;
- `Complete` only when every release-bound row is `I5`, or a canonical decision marks it deferred/rejected outside 1.2.0 with preserved rationale.

## Initial aggregate

Phase 00 reached `I3` on 2026-08-21 after the acceptance commands in `WO-001` passed. The implementation ledger contains 377 rows: 8 reverified starting gaps are `I1`; the other 369 release-plan items remain `I0`. Observed audit gaps may advance only when their row receives a durable evidence reference.

`WO-002` reached local `I3` on 2026-08-21 for the platform release-contract
sub-slice. This does not advance a broad source row: v2 generation, app/core
binding, CI enforcement, signing, artifacts and candidate evidence remain
open. Partial evidence is retained in the affected ledger rows.

`WO-003` reached local `I3` on 2026-08-21 for deterministic client generation,
app/Core/version parity and platform-validator adoption. Broad release rows do
not advance: release-bound CI, signing, real artifacts and exact-candidate
promotion evidence remain open. The aggregate therefore remains 8 rows at
`I1` and 369 at `I0`.

`WO-003B` reached local `I3` on 2026-08-21 for strict cross-repository
release-bound CI definitions and remote-orchestrator v2 enforcement.
`REL/REL-002` and `REL/REL-003` therefore advance from `I1` to `I3`. Hosted
GitHub runs, branch rules, commits, promotion and exact-candidate evidence are
unclaimed. The distribution is now 2 rows at `I3`, 6 rows at `I1`, and 369 rows
at `I0`; the count at or above `I1` remains 8 of 377.

`WO-004A` reached local `I3` on 2026-08-21 for the active client's typed
connection reducer, proof-driven green state, shared presenter, explicit
disconnect/reconnect semantics, transition matrix and bounded haptics. Eleven
directly proved rows advance to `I3`. `FE_PR/PR-01` and `FE_PR/PR-02` advance
only to `I1`: the source-plan shadow-comparison period and visual snapshots are
not present. ABI/event compatibility, migrations, native-device cycles, hosted
CI and exact-candidate evidence remain open. The distribution is now 13 rows at
`I3`, 8 rows at `I1`, and 356 rows at `I0`; 21 of 377 rows are at least `I1`.

`WO-004B` reached local `I3` on 2026-08-21 for the machine-readable ABI 2
owner, marker-only and descriptor negotiation, fail-closed capability/event
compatibility and typed client lifecycle journal. `REL/ABI-001` advances to
`I3`. `REL/CORE-001` advances only to `I2`: Core CI/build gates were expanded,
but hosted race, vulnerability, actual AAR/DLL, reproducibility and candidate
evidence remain unproved. `OBS/OBS-047..050` remain `I0` because Core callback
ABI v3, run/attempt correlation and transport taxonomy were not implemented.
The distribution is now 14 rows at `I3`, 1 row at `I2`, 7 rows at `I1`, and
355 rows at `I0`; 22 of 377 rows are at least `I1`.

Stable promotion is forbidden if any `STOP-SHIP` item is below `I4`, any release Gate A–F is unresolved, or any required release DoD row lacks exact-candidate evidence.

## 2026-08-21 — WO-009 Operator Center v2 started

The 2,848-line Operator Center audit was treated as an advisory requirements
source and reconciled against current repository owners and code. `WO-009`
freezes `adminapp/`/`admin.pokrov.space` as the canonical destination, records
the full capability migration matrix and divides `OC-000..640` into seven
evidence-bounded slices. Current code confirms browser bearer/initData storage,
binary admin authorization, a 17-route flat shell, a duplicate `webapp/admin`
surface and missing adminapp PR gates. No OC row advances from the work-order
draft alone; `WO-009A` is active and production authentication/deploy remain
`NOT_AUTHORIZED`/`BLOCKED_BY_ACCESS`.

`WO-005B2` reached local `I3` on 2026-08-21 for the authenticated Windows
service cutover: the production factory uses service IPC, the service owns the
fixed-path Core/profile lifecycle and fail-closed egress proof, machine-wide
installer source includes the service, and full-process elevation is absent.
`REL/WIN-002`, `REL/WIN-005` and `REL/SEC-001` advance to `I3`.
SCM installation, real traffic, recovery and candidate proof are unclaimed;
`REL/WIN-004` remains `I0`. The distribution is now 19 rows at `I3`, 1 row at
`I2`, 7 rows at `I1`, and 350 rows at `I0`; 27 of 377 rows are at least `I1`.

`WO-005C2` reached local `I3` on 2026-08-21 for the Windows recovery
coordinator. A versioned write-through journal retains a bounded snapshot of
the exact Core-owned `POKROV` adapter's prior IPv4/IPv6 interface fields,
addresses, routes and DNS. Rollback stops Core before restoration; any stop,
restore or journal-completion failure enters non-green `recovery_required` and
can be retried idempotently. Local faults cover all persisted connect stages,
repeated disconnect, service-object restart and partial/future journals.
`REL/WIN-004` advances to `I3`. The distribution is now 20 rows at `I3`, 1 row
at `I2`, 7 rows at `I1`, and 349 rows at `I0`; 28 of 377 rows are at least
`I1`. No SCM install, live network mutation/restoration, crash/reboot,
uninstall-while-connected, exact DLL or candidate claim is made. 005C3
service/network lifecycle breadcrumbs remain active.

`WO-005C3` reached local `I3` on 2026-08-21 for five Windows privileged
producer rows. A protected service-only `POKROV_SERVICE_EVENT_V1` journal uses
a bounded non-blocking queue, one background writer and two 256 KiB retained
files. Closed records cover SCM/power/boot, authenticated IPC request/response
correlation, Core/Wintun/adapter/route/DNS/egress and rollback. Strict Debug
build, native CTest `6/6`, Windows Flutter `20/20`, analyze and docs contract
passed. `OBS/OBS-031`, `032`, `033`, `034` and `036` advance from `I0` to `I3`;
`OBS/OBS-035` remains `I0`. The distribution is now 25 rows at `I3`, 1 row at
`I2`, 7 rows at `I1`, and 344 rows at `I0`; 33 of 377 rows are at least `I1`.
No installed SCM lifecycle, live network, physical sleep/reboot, crash dump,
support pipeline or exact-candidate claim is made. Android 005D1 is next.

`WO-005D1` reached local `I3` on 2026-08-21 for Android notification privacy
and safe MTU selection. Foreground and lockscreen notification content is
private and generic, retained detail preferences migrate to false, UID-wide
notification sampling is absent, managed/native MTU accepts `1280..1500`,
defaults to `1280` and honors a usable platform-interface ceiling. Android JVM
passed `147/147`; affected app-shell suites passed `230/230`; analyze and docs
contracts passed. `REL/AND-001` and `REL/AND-003` advance to `I3`. The
distribution is now 27 rows at `I3`, 1 row at `I2`, 7 rows at `I1`, and 342
rows at `I0`; 35 of 377 rows are at least `I1`. OEM lockscreen, physical
network/PMTU, signed build and exact-candidate proof remain unclaimed.

`WO-005D2` reached local `I3` on 2026-08-21 for Android session-scoped
concurrency and Core/TUN counters. The VPN service and Flutter host bridge own
separate bounded parent scopes; stop/replacement/destruction fences late work.
Core `CommandStatus` totals feed monotonic rates with explicit unavailable,
warming, reset and overflow states, and UID-wide `TrafficStats` is absent.
Android host compilation, focused `51/51`, full JVM `155/155`, runtime-engine
`52/52` with one external-artifact skip, app-shell `325/325`, analyze and docs
contracts passed. `REL/AND-002`, `REL/AND-004` and `OBS/OBS-040` advance to
`I3`. The distribution is now 30 rows at `I3`, 1 row at `I2`, 7 rows at `I1`,
and 339 rows at `I0`; 38 of 377 rows are at least `I1`. Physical process
death/restart, endurance, device, signing and exact-candidate proof remain
unclaimed. Android 005D3 is next.

`WO-005D3` reached local `I3` on 2026-08-21 for the Android direct/store update
identity boundary. Separate flavors keep installer permission, `FileProvider`,
APK download/cache and installer intents out of store; store can only hand off
to the exact Google Play package. Direct validates bounded origin/channel,
size/SHA-256, package, version/versionCode, SDK, ABI, pinned signer and installed
signer continuity before cache commit and repeats the full validation before
any intent. Direct/store JVM suites each passed `161/161`; app-shell `326/326`,
Android-shell `8/8`, runtime-engine `53` with one exact-Core skip, Windows-shell
`20/20`, analyzers, client contracts and the canonical workspace gate passed.
Real debug APK manifest/bytecode inspection confirmed the flavor boundary but
is not release evidence. `REL/AND-005`, `REL/UPD-001` and `REL_DOD/DOD-05`
advance to `I3`. The distribution is now 33 rows at `I3`, 1 row at `I2`, 7
rows at `I1`, and 336 rows at `I0`; 41 of 377 rows are at least `I1`.
Production signer/device/Play/exact-candidate proof remains unclaimed.

`WO-005E` records Linux as `NOT_SHIPPED_IN_1.2.0`. No distro/version,
desktop/init/network-manager, IPC-policy or package matrix was selected and
proved, so `REL/LNX-001` and `REL_DOD/DOD-06` remain `I0` and Linux stays out
of public product/platform facts. This truthful conditional decision completes
the local WO-005 exit condition without inventing compatibility evidence.
Phase 04 observability work is next.

`WO-006A` reached local `I3` on 2026-08-21 for the cross-repository
observability authority. The platform now owns a closed event schema and 117
stable error codes across 29 families; planted forbidden fields, unknown
fields/codes, duplicate keys and unsafe public copy fail offline validation.
Release-handoff v2 requires both exact byte hashes, the client generator derives
them instead of trusting candidate input, and client/Core snapshots plus typed
code/attribute sets must match the platform checkout. Platform focused tests
passed `61/61`, docs/manifest/link gates passed, the client package passed
`3/3`, release generation passed `13` cases, cross-repository seed validation
passed and Core canonical tests passed. `OBS/OBS-001..004`, `OBS/OBS-011` and
`FE/P12-126` advance to `I3`; broad `REL/OBS-001` advances only to `I1`.
The distribution is now 39 rows at `I3`, 1 row at `I2`, 8 rows at `I1`, and
329 rows at `I0`; 48 of 377 rows are at least `I1`. Runtime producers, bundles,
uploads, retention, hosted/signing and candidate evidence remain open. 006B is
next.

`WO-006B` reached local `I3` on 2026-08-21 for the client observability runtime
and release-source boundary. A pure-Dart non-blocking dispatcher now owns a
bounded priority queue, one batch writer, generation/sequence fence, separate
breadcrumb/security rings, exact Android 24 MiB and Windows 64 MiB two-file
retention, crash-tail recovery, field privacy, sanitizers, planted-secret guard,
safe config fingerprint and closed legacy readers. Raw production Dart and
Android logging was removed and a gate over 121 production files plus four
negative fixtures prevents regression. Package tests passed `13/13`; client
Flutter suites, both `161/161` Android flavor suites, analyzers, seed/docs and
cross-repository gates passed. Fifteen `OBS` rows plus `OBS_DOD/DOD-06` and
`DOD-09` advance to `I3`. The distribution is now 56 rows at `I3`, 1 row at
`I2`, 8 rows at `I1`, and 312 rows at `I0`; 65 of 377 rows are at least `I1`.
Remote aggregate routing (`OBS/OBS-029`), collectors, Core ABI, bundles,
uploads, retention, overhead/endurance, device and candidate proof remain open.
006C is next.

`WO-006C` reached local `I3` on 2026-08-21 for the structured Core-to-host
event path. Current authority keeps desktop ABI 2 and adds event ABI 1 instead
of declaring the audit-proposed ABI 3. Core, Android and Windows now carry only
closed initialize/start/stop/egress events with run/attempt/generation/sequence
fences; raw upstream lines cannot become release evidence. Current-source Go
1.25.13 Android AAR and Windows DLL development builds passed, all 15 Windows
exports were present, and a real callback smoke emitted correlated sequence
1/2 initialize events. Vet/race passed for root and daemon/libbox. The new
`govulncheck` gate first found 18 reachable vulnerabilities, which were
remediated by the Go/gRPC/x/*/CIRCL dependency floor; the repeated official
database scan found 0 reachable vulnerabilities. Five rows advance to `I3`
and two partial rows to `I2`. The distribution is now 61 rows at `I3`, 3 rows
at `I2`, 8 rows at `I1`, and 305 rows at `I0`; 72 of 377 rows are at least
`I1`. The tracked Core 1.0.3 artifacts and hashes remain unchanged, and exact
replacement artifacts, hosted/reproducible/Apple/candidate proof, expanded
transport taxonomy and later Android/Linux producers remain open. 006D is
next.

`WO-006D` reached local `I3` on 2026-08-21 for portal request correlation and
the aggregate release-health ingest boundary. Every request now has a new
server UUIDv4; only a canonical client UUIDv4 is retained, unsafe values are
replaced, and both headers survive success and error. Unhandled exceptions map
to `API-007` without raw echo. The authenticated endpoint accepts at most 100
closed identity-free event projections in bounded JSON/gzip, rejects unknown
fields/codes, compression bombs and identity/destination/package metadata, and
stores only event/build/platform/outcome/catalog dimensions. Event UUID retry
is idempotent and conflicting reuse fails closed; rejected payloads leave only
bounded reason counters. Focused tests passed `25/25`; isolated backend owner
groups passed `157/157`; docs `30/30`, links, manifest, compile and scoped lint
passed. `OBS/OBS-051..053` and `OBS_DOD/DOD-21` advance to `I3`.
`OBS/OBS-008` advances only to `I2` because the active client still lacks the
portal header/batch-sink seam. The distribution is now 65 rows at `I3`, 4 rows
at `I2`, 8 rows at `I1`, and 300 rows at `I0`; 77 of 377 rows are at least
`I1`. Production telemetry, hosted load/rate/storage evidence, retention,
alerts, deploy and exact-candidate proof remain open. 006E is next.

`WO-006E` reached local `I3` on 2026-08-21 for the active-client phase,
correlation and previous-exit path. Android and Windows initialize the bounded
store before UI startup, recover a sanitized diagnostic-only exit marker and
drive profile/Core/TUN/routes/DNS/egress/verified/rollback/stopped events from
the canonical reducer. Missing proof cannot become a successful terminal;
cancel, supersede, timeout and crash remain distinct. App-first requests now
carry canonical correlation, while the local-first release projection strips
identity/correlation and uploads only with an existing session. Runtime tests
passed `20/20`, app-shell `329/329`, host analyzers/tests and the complete
workspace/Gradle gate passed; cross-repository platform seams passed `41/41`.
Nineteen rows advance to `I3` and five mapping-only PB rows to `I2`. The
distribution is now 84 rows at `I3`, 8 rows at `I2`, 8 rows at `I1`, and 277
rows at `I0`; 100 of 377 rows are at least `I1`. Exact-candidate crash and
overhead, active auth/performance/entitlement producers, encrypted bundles,
upload/storage, retention and operator access remain open. 006F is next.

`WO-006F` reached local `I3` on 2026-08-21 for the deterministic encrypted
support-bundle boundary. Closed typed collectors emit only fixed bounded virtual
files; canonical JSON binds the exact preview, diagnostic ID, removal counts,
manifest and per-file hashes; extended collection requires a short-lived signed
policy; and only a signed-recipient X25519/HKDF/AES-GCM output can leave the
package. The Support sheet shows the exact summary-profile contents and labels
the existing ticket diagnostics map separately. Collectors passed `6/6`, bundle
tests `9/9`, app-shell `329/329`, the canonical workspace/Gradle gate and seed
contract passed, and platform schema/docs/link/manifest gates passed. Eight
rows advance to `I3`. The distribution is now 92 rows at `I3`, 8 rows at `I2`,
7 rows at `I1`, and 270 rows at `I0`; 107 of 377 rows are at least `I1`.
Production signing/recipient keys, custody/rotation, deployed distribution,
encrypted upload/storage and physical exact-candidate proof remain open. 006G
is next.

`WO-006G` reached local `I3` on 2026-08-21 for the case-bound encrypted upload
and isolated ingest lane. Authenticated clients use an idempotent short-lived
ticket, authoritative resumable offset and ciphertext-only private outbox;
recovery scope and cross-owner binding are denied. The web slice never imports
decrypt/ingest code. An opt-in worker loads mounted recipient keys, validates
the bounded canonical payload and hostile corpus in memory, and retains only
the original encrypted envelope in accepted/private quarantine storage.
Platform focused tests passed `23/23`, composition/release/upload regression
passed `31/31`; client bundle tests passed `11/11`, outbox tests `3/3`,
app-shell `333/333`, the canonical workspace/Gradle gate and scoped
seed/cross-repository/docs gates passed. Seven rows advance to `I3`. The
distribution is now 99 rows at `I3`, 8 rows at `I2`, 7 rows at `I1`, and 263
rows at `I0`; 114 of 377 rows are at least `I1`. Production key custody,
deployed object storage/worker isolation, real upload and retention evidence
remain open. 006H is next.

`WO-006H` reached local `I3` on 2026-08-21 for retention and bounded operator
read models. The worker selects eligible unheld release-health, encrypted
accepted/quarantine bundle and access-audit data in bounded batches, validates
owned paths and reports integer-only counters. Release health is grouped by
exact build/platform identity with crash/connect/update deltas; known issues are
candidate scoped and observational. L1 receives only the closed summary/
timeline, while an explicit empty-by-default L2/SRE allowlist gates fixed-
reason, expiring, actor-bound, atomic single-use ciphertext access with audit,
path, size and SHA-256 checks. Current focused tests passed `9/9`; the exact
combined regression passed `158/158`. Seven new rows
advance to `I3`; `OBS_DOD/DOD-21` remains `I3` with stronger evidence. The
distribution is now 106 rows at `I3`, 8 rows at `I2`, 7 rows at `I1`, and 256
rows at `I0`; 121 of 377 rows are at least `I1`. Production retention/RBAC/
ACL/alert/window evidence remains open. WO-006 is locally complete and WO-007
is next.

`WO-007A` reached local `I3` on 2026-08-21 for the two confirmed FreeKassa
stop-ships. One provider-module parser now accepts only known response shapes on
the exact configured HTTPS checkout host and the legacy API name re-exports it.
Missing, HTTP, credential-bearing, cross-host and no-path values fail closed;
the provider/root source contains no `oa=0` fallback. Focused tests passed
`11/11`, the compatibility test `1/1`, and the full payment/provider/callback
matrix `106/106` plus 12 subtests. Two rows move from `I1` to `I3`; the
distribution is now 108 rows at `I3`, 8 at `I2`, 5 at `I1`, and 256 at `I0`;
121 of 377 rows are at least `I1`. FreeKassa remains disabled and production
provider/payment evidence is open. 007B is next.

`WO-007B` reached local `I2` on 2026-08-21 for immutable local payment-order
authority and the provider adapter boundary. A versioned digest binds the
provider/order, owner, amount, currency, plan, source and entitlement snapshot
before provider I/O; exact retry reuses the row and drift fails closed. Only
allowlisted response facts are retained, provider failure stays non-fulfilling
and terminal callback state cannot regress. Service tests passed `10/10`,
focused API tests `3/3`, and the then-current full payment matrix passed
`117/117` plus 12 subtests. `REL_DOD/DOD-08` advanced to `I2`; the distribution
became 108 rows at `I3`, 9 at `I2`, 5 at `I1`, and 255 at `I0`. The
same-transaction entitlement outbox and production evidence remained open.

`WO-007C` reached local `I3` on 2026-08-21 for the transactional
payment-entitlement outbox. Active provider-payment grants and minimal,
identity-free events are written in one transaction; a bounded supervised
worker provides conditional claim, stale recovery, retry/dead-letter and
idempotent provisioning dispatch. Callback, backfill and worker replay converge
without duplicate access; malformed events and reversed grants fail closed.
Focused outbox tests passed `9/9`; exact account/provisioning/worker regression
passed `124/124`; the full payment/provider/callback matrix passed `126/126`
plus 12 subtests. `REL_DOD/DOD-08` advances from `I2` to `I3`. The distribution
is now 109 rows at `I3`, 8 at `I2`, 5 at `I1`, and 255 at `I0`; 122 of 377 rows
are at least `I1`. Production provider/callback/worker/reconciliation and
exact-candidate evidence remain open. 007D is next.

`WO-007D` reached local `I3` on 2026-08-21 for the declared payment/provider
HTTP surface. One FastAPI-lifespan registry owns reusable provider-policy
sessions with bounded total/connect/socket-read time, pool and response bytes.
Lava.top, Cardlink, Pally, Platima and the closed historical FreeKassa operations
use it explicitly; provider code creates no per-request session and emits only
provider/operation/status/integer-latency/result-code telemetry. Lifecycle and
limit tests passed `7/7`, composition/admin/provider checks `22/22`, and the
exact payment/callback/outbox matrix `135/135` plus 12 subtests. `REL/HTTP-001`
advances from `I0` to `I3` for this declared surface. The distribution is now
110 rows at `I3`, 8 at `I2`, 5 at `I1`, and 254 at `I0`; 123 of 377 rows are at
least `I1`. Inventoried non-provider clients and deployed provider pool/timeout/
latency evidence remain open. 007E is next.

`WO-007E` reached local `I3` on 2026-08-21 for the payment-route DB transition.
Named complete sync use cases now run in Starlette/AnyIO's bounded threadpool;
each owns session creation, commit/rollback and close in one worker thread and
returns only scalars/plain data. Order, callback, reversal, fulfillment,
delivery evidence, start-99 and FreeKassa DB paths are covered; no ORM row
crosses an await. Slow-DB concurrency and same-thread rollback tests passed in
the `11/11` focused set; exact payment regression passed `139/139` plus 12
subtests and module/admin checks `6/6`. `REL/API-001` advances from `I0` to `I3`
for payment routes only. The distribution is now 111 rows at `I3`, 8 at `I2`,
5 at `I1`, and 253 at `I0`; 124 of 377 rows are at least `I1`. Non-payment ORM
inventory and deployed capacity/latency/fault proof remain open. 007F is next.

`WO-007F` reached local payment-decomposition proof on 2026-08-21. The former
payment route block is now the dedicated ordered `api_payment_routes.py` slice;
provider-callback orchestration moved from `api.py` to the explicitly injected
`payment_callback_application.py`. Immutable order/result, provider, outbox,
bounded HTTP and bounded DB owners stay focused and independently tested while
legacy exports and route order remain compatible. Architecture/source tests
passed `6/6`; the exact payment matrix passed `142/142` plus 12 subtests; and
the adjacent module/retention/admin/app-first/auth/subscription regression
passed `185/185` plus 8 subtests. `REL_GATE/GATE-D` advances from `I0` to local
`I3`. `REL/ARCH-002` advances only to `I2` because the remaining large public,
admin and action-service inventory is not decomposed. The distribution is now
112 rows at `I3`, 9 at `I2`, 5 at `I1`, and 251 at `I0`; 126 of 377 rows are at
least `I1`. Production provider/DB/outbox/reconciliation and exact-candidate
evidence remain open. WO-007 is locally complete; WO-008 must be drafted next.

## 2026-08-21 — WO-008A commercial manifest and consumer gate

WO-008 is drafted and 008A is locally complete for commercial revision
`2026-08-21.1` / manifest SHA-256
`1d4b295a5ce9003345a2d32d8374852a144477659064fab8de8958be4f018f02`.
Generated JSON/schema/docs, Python/TypeScript adapters, source digests, API
revision/header/health, DB projection rejection, marketing/JSON-LD/cabinet/bot
base-price binding and server-only promo evaluation are implemented. Focused
contracts are `41 passed`; API/CORS route proof is `2 passed`; payment/admin regression
is `127 passed` plus `12 subtests`; both frontend Webpack production builds and
lint pass, as do marketing SEO and responsive smoke. No deploy or external
seller/legal/CDN/provider/capacity/readback proof was performed.

`REL/CONTRACT-001` advances `I1 -> I2`. `FE/P12-024`, `P12-129`, `P12-210`,
`MKT/MKT-600` and `FRKN_ADOPT/ADOPT-07` advance `I0 -> I2`. They remain below
`I3` because active-client adoption, whole-product copy reconciliation,
signed-offer/campaign work, atomic deploy/CDN/public readback, seller/legal and
runtime-capacity evidence are still open. The distribution is now 112 rows at
`I3`, 15 at `I2`, 4 at `I1`, and 246 at `I0`; 131 of 377 rows are at least
`I1`. WO-008B is active next.

## 2026-08-21 — WO-008B campaign/legal/capacity policy root

WO-008B is locally complete on the existing `IncentiveCampaign` root. Additive
SQLite/PostgreSQL schema, stable public IDs, closed lifecycle/legal/channel/
reason vocabularies, campaign/commercial revisions, seller/terms/channel
bindings, finite paid cap and a focused policy service are implemented. Policy
is revalidated at guarded preview/confirm, readback and actual promo/gift lookup;
legacy active bits cannot bypass it. The 300-unit entitlement projection,
70%/65% hysteresis, acquisition block and renewal/recovery exemption are proved
locally. Create/update/kill exact replay and stale revision are covered.

Focused policy/migration proof is `6 passed`; admin/bot/API/support proof is
`18 passed`; broader commercial/shared/admin/action-intent/route regression is
`50 passed`; focused Ruff and compilation pass. The existing content-addressed,
bounded, authenticated and audited promo-media upload was recorded as an
explicit low-risk admin-policy exemption after the broader gate exposed the
missing classification.

`MKT/MKT-000` and `MKT/MKT-300` advance `I0 -> I2`. They remain below `I3`
because the checked-in manifest still blocks seller/offer/RF advertising and
allows no channels, while deployed capacity, live auto-pause, public readback,
legal qualification and a bounded pilot are unproved. The distribution is now
112 rows at `I3`, 17 at `I2`, 4 at `I1`, and 244 at `I0`; 133 of 377 rows are at
least `I1`. WO-008C is active next.

## 2026-08-21 — WO-008C server-authoritative offer preview and signed hold

WO-008C is locally complete. Four additive SQLite/PostgreSQL child domains now
hang from the existing campaign root: exact-price offers, channel creatives,
HMAC-subject audience assignments and unique assignment reservations. The
separate no-store public preview route evaluates PromoCode, campaign/legal/
capacity/channel/audience policy, exact manifest price, finite quota and
absolute deadlines on the server. Invalid states repeat base price and issue no
token. A valid local ready-contract fixture receives an exact-field HMAC token
with no raw identity/provider data; refresh reuses one hold and expiry cannot
mint a replacement for the assignment.

Focused offer/model/migration/token/deadline/block proof is `7 passed`. Combined
commercial/shared/API/payment callback/order/module regression is `132 passed`,
`12 subtests passed`, with `21` existing deprecation warnings. Isolated API
reload and temporary-DB regression is `82 passed`; focused Ruff and Python
compilation pass.

`MKT/MKT-100` and `MKT/MKT-400` advance `I0 -> I2`. Atomic redemption/order
revalidation, consumer countdown/return UI and cross-surface consistency remain
open, so no frontend row advances. The checked-in manifest remains legally
blocked with no allowed channels, and no external offer, provider call, payment,
deploy or public readback occurred. The distribution is now 112 rows at `I3`,
19 at `I2`, 4 at `I1`, and 242 at `I0`; 135 of 377 rows are at least `I1`.
WO-008D is active next.

## 2026-08-21 — WO-008D atomic reservation/order binding

WO-008D is locally complete. RUB order creation now accepts only the signed
offer token as temporary-price proof and revalidates server-derived subject,
campaign/offer/creative/assignment/reservation lineage, exact manifest price,
revisions, deadlines, legal/channel/capacity policy and finite quota while the
quota owners are locked. First acceptance creates one unique bound reservation
and immutable v2 order intent before provider I/O; exact retry reuses the order
and drift/foreign reuse/over-cap binding fails closed.

Paid account or access-key fulfillment consumes the same reservation and paid
counters once in its durable transaction. Callback replay cannot introduce
attribution; refund retains the original consumed lineage. Failed provider
checkout remains bounded until the absolute hold and only bounded local `error`
evidence permits due release without rewriting order truth.

Focused commercial order/offer/intent proof is `24 passed`; the exact endpoint
through fake-provider, callback replay and refund scenario is `1 passed`, with
its adjacent direct-promo regression also `1 passed`. The broader payment/
provider/callback/API/entitlement/outbox regression is `154 passed` plus `12
subtests` and `20` existing deprecation warnings. Focused Ruff and compilation
pass. No external offer/provider/payment/deploy/readback occurred.

`FE/P12-014` advances `I0 -> I2`; `MKT/MKT-100` remains `I2` with stronger
atomic evidence. The distribution is now 112 rows at `I3`, 20 at `I2`, 4 at
`I1`, and 241 at `I0`; 136 of 377 rows are at least `I1`. WO-008E is active
next.

## 2026-08-21 — WO-008E campaign-to-revenue lineage

WO-008E is locally complete. The current signed commercial token and immutable
order lineage are v2 and carry server-owned impression/click IDs from checkout
acquisition handoff or reservation through payment. A new additive,
identity-free `commercial_conversions` projection is unique by
provider/order/stage. Paid/reversed stages commit with payment/entitlement
truth; first verified connect and D7 `[7d,14d)` / D30 `[30d,37d)` stages come
only from durable observer connection evidence; renewal requires a later
provider-payment grant. Callback/client/funnel payloads cannot create or repair
these stages.

The admin payment summary now exposes a read-only campaign/revision/capacity-
unit model with gross/refund/net RUB, paid, first-connect, retention, renewal,
authority labels and explicit freshness. Projection rows contain no raw
identity, token, callback body, destination or entitlement secret.

Focused token/order/projection/migration/read-model proof is `28 passed`; the
combined commercial/economy/observer/admin/exact callback matrix is `120 passed`
with `2` existing SQLite datetime deprecation warnings. The exact local fake-
provider callback/replay/refund projection is included; focused Ruff and
compilation pass. No external offer, provider,
payment, observer, deploy or public/admin readback occurred, and the legal
manifest remains launch-blocked.

`MKT/MKT-200` advances `I0 -> I2`. The distribution is now 112 rows at `I3`,
21 at `I2`, 4 at `I1`, and 240 at `I0`; 137 of 377 rows are at least `I1`.
WO-008F is active next.

## 2026-08-21 — WO-008F checkout and consumer integration

WO-008F is locally complete. Marketing and cabinet now consume server catalog,
offer, method-capability and payment-return contracts. They do not calculate
temporary price, extend deadlines, infer quota or turn a redirect into payment
truth. A signed identity-free return capability stays in versioned browser
session storage and drives a token-only, no-store, read-only projection with the
closed states `processing`, `paid`, `failed`, `cancelled`, `manual_review` and
`expired`. Provider URLs never carry that token.

The full payment matrix passed `88` tests plus `12` subtests. The combined
commercial/return/route/frontend matrix passed `68`; module slice, focused Ruff,
Python compilation, both frontend lints and both production builds passed. A
local mock-browser run proved server price/promo/deadline/terms, disabled card
capability and query stripping without invoking purchase. No live provider,
payment, campaign, deploy, public-origin or active-client flow is claimed.

`FE/P12-011`, `P12-012`, `P12-013`, `P12-120` and `FE_PR/PR-05` advance
`I0 -> I2`. `P12-014`, `P12-129` and `P12-210` remain `I2` with stronger
consumer evidence. The distribution is now 112 rows at `I3`, 26 at `I2`, 4 at
`I1`, and 235 at `I0`; 142 of 377 rows are at least `I1`. WO-008G is active
next.

## 2026-08-21 — WO-008G capacity automation and revision rollback

WO-008G and WO-008 are locally complete. Distinct active/grace entitlement
accounts remain the only capacity authority. A supervised, transactional and
audited owner policy auto-pauses acquisition/winback at 70%, holds through
65–70%, resumes only strictly below 65% after all non-capacity gates pass, and
never auto-resumes owner-paused/ended/killed rows; renewal/recovery are exempt.
Admin readback exposes exact revision, thresholds, forecast, gates, caps,
reservation/paid counts and freshness without mutating state.

The deterministic 8-file commercial revision bundle validates source and
contract digests, supports readback and defaults restore to dry-run. Apply needs
the current-revision and exact-bundle-SHA guards; isolated tests prove byte
readback and compensating preimage rollback after a planted partial failure.
Current-source evidence is `42` commercial tests, `11` admin policy/route tests,
`39` admin/client tests, `24` worker/migration tests and the exact `88` payment
tests plus `12` subtests. The local bundle readback for revision
`2026-08-21.1` is 8 files with SHA
`712ee1e9a2c33ca914b4d5d4b130c2c15b3814ba7be01511653b70f30914732a`;
repository restore dry-run reported zero changes.

No legal approval, deployed automation/readback, campaign, provider/payment,
deploy/CDN or production rollback is claimed. `MKT/MKT-300` and `MKT/MKT-600`
remain `I2` with stronger evidence. Totals remain 112 rows at `I3`, 26 at `I2`,
4 at `I1`, and 235 at `I0`; 142 of 377 rows are at least `I1`. Phase 07
Operator Center v2 is next.

## 2026-08-21 — WO-009A Operator Center oracle and candidate identity

WO-009A is locally complete. `adminapp/` and `admin.pokrov.space` now have one
checked-in capability oracle: the 17-route compatibility shell is frozen and
mapped, with three unique legacy web-admin capabilities, into exactly seven
target workspaces. Static builds emit deterministic build/route identity; the
current route-manifest SHA-256 is
`976030111b170e399639d1412403bd4c6dfe7c5581e8a79fd212e34875d48d2f`.
A modular guarded `/api/admin/v2/meta` exposes bounded backend/schema/release
identity, preserving missing fields as null plus warnings.

The repository guardrail now installs, lints, builds and runs full adminapp
E2E. Static deploy validation rejects absent/mismatched identity and the old
public shell string, smokes both identity files and retains the prior adminapp
symlink as a rollback pointer. Local proof is 8 manifest/deploy tests, 2 focused
meta API tests, build-contract, lint, a 19-page production build, 60 Playwright
tests and a three-surface plan-only bundle. No hosted CI, public/authenticated
readback, production deploy or real rollback drill is claimed. `npm ci` also
reported six high advisories in the existing lockfile; no unreviewed auto-fix
was applied.

`OC/OC-000` and `OC-130` advance to `I3`; `OC-120` to `I2`; `OC-100`,
`OC-110` and `OC-140` to `I1`. The distribution is now 114 rows at `I3`, 27 at
`I2`, 7 at `I1`, and 229 at `I0`; 148 of 377 rows are at least `I1` and there
are no duplicate `(plan,id)` keys. WO-009B is active next.

## 2026-08-21 — WO-009B operator session and RBAC boundary

WO-009B is locally complete. The canonical v2 frontend now validates a
server-owned opaque HttpOnly `__Host-` session, keeps CSRF only in memory,
purges legacy bearer/initData storage and uses raw Telegram initData only for a
bounded compatibility exchange. Additive operator, environment-scoped role,
HMAC-hashed session and audit records back idle/absolute expiry, inventory,
revoke/logout, active-role re-read and exact permission snapshots. The modular
v2 router enforces deny-by-default permissions; frozen legacy endpoints accept
the cookie only through `legacy.admin.access` and retain CSRF for unsafe calls.

Focused auth/RBAC proof is 7 tests; full admin ops is 37, action-intent 20,
admin payments 3, payment callbacks 88 plus 12 subtests, route gaps 7,
operator observability 9 and module/manifest/policy/error contracts 14.
Adminapp lint/build pass with 19 static pages and the unchanged manifest hash;
full Playwright is 60 passed in 57.6 seconds.

External OIDC/passkey, field redaction, JIT/break-glass, generated SDK,
operator-management UI and the audit explorer/export remain unimplemented;
therefore the broad source-plan rows do not advance to `I3`. `OC/OC-100` and
`OC-110` move from `I1` to `I2`; `OC/OC-600` and `OC-610` move from `I0` to
`I2`; `OC/OC-120` remains `I2` with stronger security evidence. The
distribution is now 114 rows at `I3`, 31 at `I2`, 5 at `I1`, and 227 at `I0`;
150 of 377 rows are at least `I1`. No deploy, real IdP/operator migration,
public readback or production rollback is claimed. WO-009C is active next.

## 2026-08-21 — WO-009C seven-workspace shell and stable data boundary

WO-009C is locally complete. The canonical Operator Center now exposes seven
active workspace entries around the frozen 17 capability routes, for 24 direct
routes total. Desktop rail, tablet drawer and bounded mobile navigation share
the checked-in manifest. The topbar joins frontend build, API meta and session
identity and raises an explicit mismatch/cutover-stop alert.

Route resources now register refresh callbacks explicitly; the DOM text-button
discovery and reload fallback are gone. Failed refresh keeps last-good data and
degrades the visible source state. Typed identity/session adapters, URL-owned
route state and safe global search are retained; query/results do not survive
palette close and are not written to browser storage. The read-only governance
route proves the session-inventory boundary without claiming later governance.

Local proof is adminapp lint/build with 26 static pages, 6 manifest/identity
tests and the full 63-test Playwright regression. No hosted CI, authenticated
public environment, deploy or rollback is claimed. `OC/OC-140` moves from `I1`
to `I3`; `OC/OC-120` remains `I2` with stronger evidence. The distribution is
now 115 rows at `I3`, 31 at `I2`, 4 at `I1`, and 227 at `I0`; 150 of 377 rows
are at least `I1`. WO-009D is active next.

## 2026-08-21 — WO-009D My Shift, operator tasks and Incident Room

WO-009D is locally complete. Additive operator tasks, an environment-scoped My
Shift projection, the extended single `ServiceIncident` authority, append-only
timeline/links and versioned alert linkage now back the real `/shift` and
`/incidents` workspaces. Task, incident and explicit alert transitions use the
single action-intent registry with optimistic versions. L3 compensation reuses
the existing idempotent incident/account grant service and requires fresh
step-up; direct legacy incident/ack writes are closed.

Local proof is server `py_compile`, 79 focused/relevant backend tests, additive
legacy-SQLite migration rehearsal, adminapp lint/build, three focused browser
flows, updated route/navigation/source-isolation checks and the final full
Playwright regression (`65/65` in `1.0m`). The 25-route
manifest SHA-256 is
`61bde93f6edcd1fbbd616fe004e5be721a8cbe20ec175333d5ead21c31b55f94`.
No hosted CI, production migration, authenticated public readback, deploy,
compensation or rollback is claimed. `OC-200`, `OC-210`, `OC-220` and
`OC-230` advance from `I0` to `I3`. The distribution is now 119 rows at `I3`,
31 at `I2`, 4 at `I1`, and 223 at `I0`; 154 of 377 rows are at least `I1`.
WO-009E is active next.

## 2026-08-21 — WO-009E Support Inbox, User 360 and diagnostics

WO-009E is locally complete. Additive ticket workflow/version fields, internal
message visibility, server-owned Support Inbox ordering, guarded claim/assign/
update/reply/note flows, User 360 opaque grouping and bounded fingerprints/
attempt explorer reuse the existing ticket, Event Envelope, observer and
support-bundle authorities. Final self-review also bound incident lookup to the
ticket environment, included canonical account-owned tickets in User 360 and
prevented false attempt correlation when session/trace facts are missing.
Relevant backend regression passed `131` tests;
adminapp lint/build passed with 27 pages and manifest SHA-256
`96e00b508c25e181182fedc9a2a63d25491acf7c1803cd6866a360e5ea3c940d`;
the final full Playwright run passed `66/66` in `1.1m`.

`OC/OC-300`, `OC-310`, `OC-320`, `OC-330` and `OC-340` advance from `I0`
to local `I3`. No production migration, hosted CI, authenticated public
readback, deploy or rollback is claimed. The distribution is now 124 rows at
`I3`, 31 at `I2`, 4 at `I1`, and 218 at `I0`; 159 of 377 rows are at least
`I1`. WO-009F is active next.

## 2026-08-21 — WO-009F1 network vertical

WO-009F1 is locally complete. Fleet, Node 360, traffic, alerts, provider quotas,
RU evidence and emergency catalog now use explicit environment-scoped Admin API
v2 reads with authority/freshness metadata and bounded redaction. Node,
provider, emergency and alert-silence mutations reuse stored Action Intent,
optimistic context and the existing high-risk step-up policy. Invalid RU
configuration degrades explicitly without inventing reachability evidence.

Expanded backend regression passed `142` tests in `274.46s`; adminapp
lint/build passed with 27 pages, 25 direct routes and manifest SHA-256
`295b85719bd445692ce68b9c293c9601776ad1adba890b7ae27b54392afcef32`;
full Playwright passed `67/67` in `1.1m`. `OC/OC-400`, `OC-410` and `OC-420`
advance from `I0` to local `I3`. No hosted CI, authenticated public readback,
real network mutation, RU-origin proof, deploy or rollback is claimed. The
distribution is now 127 rows at `I3`, 31 at `I2`, 4 at `I1`, and 215 at `I0`;
162 of 377 rows are at least `I1`. WO-009F2 is active next.

## 2026-08-21 — WO-009F2 money, access and bounded growth

WO-009F2 reached local `I3` for payment reconciliation/360, entitlement
lineage, access grants, the retired FREE archive, promos, bonuses and program
review. Production-only v2 reads compose the existing commerce and entitlement
authorities and fail closed elsewhere. The canonical UI has 28 direct routes;
generated codes are shown once from the L3 execute response, stored secrets stay
redacted, config previews are fingerprinted and program approval/reward uses one
version-bound idempotent transaction.

Full relevant backend regression passed `74` tests in `261.41s`; adminapp
lint/build passed with 30 generated pages and manifest SHA-256
`772bd40d9209be3c16453b9bf3c0868e416d6a307bc6dbb067f90eecfe087179`;
the final full Playwright regression passed `70/70` in `1.2m`. `OC/OC-430` and
`OC-440` advance from `I0` to local `I3`. No hosted CI, authenticated public
readback, production mutation, deploy or rollback is claimed. The distribution
is now 129 rows at `I3`, 31 at `I2`, 4 at `I1`, and 213 at `I0`; 164 of 377
rows are at least `I1`. WO-009F3 is active next.

## 2026-08-22 — WO-009F3 release and messaging parity

WO-009F3 reached local `I3` for the exact-candidate release cockpit,
platform/version adoption and regression, guarded rollout controls, broadcast
delivery and news/live-update lineage. The public client-app APIs consume the
same fail-closed rollout registry; rollback records that the external artifact
switch was not performed. Full relevant backend regression passed `77` tests in
`255.09s`; adminapp lint/build passed with 30 generated pages and manifest
SHA-256 `9d37db1afabaa08774321049b9e99c91aa1ad642b9eaa4e35c03586bb8521457`;
full Playwright passed `70/70` in `1.2m`.

`OC/OC-500` through `OC-540` advance from `I0` to local `I3`. No hosted CI,
authenticated public readback, real release/messaging mutation, external
artifact switch, device/signing/RU proof, deploy or rollback is claimed. The
distribution is now 134 rows at `I3`, 31 at `I2`, 4 at `I1`, and 208 at `I0`;
169 of 377 rows are at least `I1`. WO-009F4 governance parity is active next.

## 2026-08-22 — WO-009F4 governance and privacy parity

WO-009F4 reached local `I3` for operator/role/session governance, audit
exploration and safe CSV export, command lineage, sensitive-access visibility
and privacy/retention status. Stored Action Intent, optimistic versions and
fresh step-up guard privileged changes; self-escalation, invalid temporal
superadmin grants, pending-review regrant and last-superadmin removal fail
closed. Sensitive reads audit themselves, environment-scoped lineage stays
isolated, and privacy status exposes bounded anti-abuse and diagnostic-bundle
policy/backlog without HMAC secrets or raw identity material.

The final relevant backend regression passed `80` tests in `296.54s`;
governance/migration/manifest passed `9` tests, privacy/retention passed `13`,
documentation contracts passed `30`, and the platform context audit passed.
`adminapp` lint/build passed with 30 generated pages and manifest SHA-256
`343ee83d9dfb397dcc19d67f69a1796007a4bf90bf2f06dbbfe1f54cc8e9f19f`;
the final full Playwright regression passed `72/72` in `1.3m`.

`OC/OC-600`, `OC-610` and `OC-620` advance to local `I3`. No hosted CI,
authenticated staging/production readback, production migration, real
governance mutation, deploy or rollback is claimed. The distribution is now
137 rows at `I3`, 29 at `I2`, 4 at `I1`, and 207 at `I0`; 170 of 377 rows are
at least `I1`. WO-009G local cutover/parity is active next.

## 2026-08-22 — WO-009G local cutover and rollback package

WO-009G established a machine-readable cutover matrix for all 28 canonical
routes and seven workspaces, removed every legacy route state from the local
manifest, migrated the remaining overview/online/funnel/referral browser reads
to production-only v2 projections and moved referral processing to the growth
Action Intent boundary. Five compatibility read patterns remain explicitly
inventoried and read-only; there is no dual write and no claim that the public
legacy shell has been redirected or removed.

The static build identity now binds route and cutover hashes. The local verifier
rejects migrated legacy browser endpoints, legacy bearer/session storage and
JavaScript budget overruns. Explicit rollback tooling validates exact current
and prior fingerprints and atomically swaps constrained versioned symlink
targets, but the real command was not executed.

The final backend matrix passed `88` tests in `280.36s`; adminapp lint and the
cutover verifier passed; the verifier observed 28 routes, seven workspaces,
seven JavaScript chunks, `1,657,712` total bytes and `1,031,197` largest chunk;
full Playwright passed `72/72` in `1.3m`. Route-manifest SHA-256 is
`174894555db7c842f2c2b13f5ed8622cd9f8a31b8d93a2b0e5577a70984d3bc3` and
cutover-matrix SHA-256 is
`d766379788cc08d3ec7a2492ea45fdc8b76b3a8c8054e282193127c049c53717`.

`OC/OC-630` advances from `I0` to `I1`: the proof oracle is verified, while
exact-candidate authenticated staging/production readback, screenshots and
origin evidence remain unavailable. `OC/OC-640` advances from `I0` to `I2`:
the retirement package exists locally, while redirect/removal and real rollback
remain unexecuted. The distribution is now 137 rows at `I3`, 30 at `I2`, 5 at
`I1`, and 205 at `I0`; 172 of 377 rows are at least `I1`. Phase 08 is active
next; WO-009 external gates stay open until exact-candidate execution.

## 2026-08-22 — WO-010A frontend authority and current-state baseline

WO-010A reverified all 67 Phase 08 rows against their canonical product,
architecture, release, commerce, observability, design and performance owners
and the current client/cabinet/marketing code and test surfaces. The retained
inventory distinguishes existing prerequisites from the remaining product
work: typed connection presentation and encrypted support delivery exist, but
the shell ownership seam, first-session coordinator, platform-correct cabinet
download, on-demand checklist, reduced-motion/no-JS behavior, 200%/axe/visual
gates, diagnostics product surface and comparable performance baselines remain
partial or open.

Client analysis passed with no issues; connection/encrypted-outbox tests passed
12/12; focused first-launch/connect/support widget tests passed 3/3; cabinet and
marketing lint passed. This is current-state evidence, not implementation or
candidate proof, so all 67 rows advance only from `I0` to `I1`. The distribution
is now 137 rows at `I3`, 30 at `I2`, 72 at `I1`, and 138 at `I0`; 239 of 377
rows are at least `I1`. WO-010B1 is active with immutable
`ProtectionViewState` plus intents as the first architecture-first slice.

## 2026-08-22 — WO-010B1 protection presentation boundary

WO-010B1 introduced one immutable Home `ProtectionViewState` retaining the
exact typed `ConnectionPresentation` and one `ProtectionIntents` boundary. The
composition root no longer passes parallel connection copy, CTA or action
callbacks into Home. Direct Flutter haptics are centralized in one guarded
adapter, and a release-bound boundary test prevents Home prop leakage,
app-shell `part` growth above 29 and direct haptics elsewhere.

Client analysis, 11 connection tests, one haptic contract, three Home widget
scenarios, the new boundary, docs contract and full seed validation against the
active platform/Core worktrees passed. `FE/P12-101`, `P12-103` and `P12-114`
advance from `I1` to `I3`. The distribution is now 140 rows at `I3`, 30 at
`I2`, 69 at `I1`, and 138 at `I0`; 239 of 377 rows remain at least `I1`.
WO-010B2 connection-orchestration extraction is active next.

## 2026-08-22 — WO-010B2 connection state ownership

WO-010B2 moved mutable snapshot, explicit intent, action-in-flight state,
attempt clock/number, reducer/presenter derivation and runtime-action timeout
into one `ConnectionCoordinator`. The shell retains product orchestration but
cannot redeclare those raw fields under the release-bound boundary check.

Client analysis, 13 connection/coordinator tests, five focused connection
widgets, boundary/docs contracts and full seed validation passed.
`REL/ARCH-001` advances from `I1` only to partial `I2`; three of the four named
coordinator seams remain open. The distribution is now 140 rows at `I3`, 31 at
`I2`, 68 at `I1`, and 138 at `I0`; 239 of 377 rows remain at least `I1`.
WO-010B3 first-session ownership is active next.

## 2026-08-22 — WO-010B3..B5 complete coordinator ownership

WO-010B3..B5 moved the other three named mutable seams into focused
`FirstSessionCoordinator`, `AccountSessionCoordinator` and
`DiagnosticsCoordinator` contracts. Together with `ConnectionCoordinator`,
the client now has all four architecture-plan owners; the composition root
keeps orchestration adapters but cannot restore the raw fields under the
release-bound guard.

Client analysis passed. First-session, account/session and diagnostics
coordinator tests passed 7/7; fourteen focused first-launch, account/support and
Android runtime widgets passed; boundary/docs contracts and the full seed gate
against the active platform/Core worktrees passed. `REL/ARCH-001` advances from
partial `I2` to `I3`, and `FE/P12-102` advances from `I1` to `I3`. The
distribution is now 142 rows at `I3`, 30 at `I2`, 67 at `I1`, and 138 at `I0`;
239 of 377 rows remain at least `I1`. WO-010B6 progressive protection
disclosure and bounded large-screen separation is active next.

## 2026-08-22 — WO-010B6 protection disclosure and recovery

WO-010B6 added a coordinator-owned ten-second stage timer with safe Home stage
disclosure, rebuilt Protection Center as summary/details/support layers, moved
its mutable screen state behind a feature controller and added warned
three-step repair with verified/support outcomes. Raw host diagnostics remain
absent from consumer layers.

Client analysis, 14 connection/coordinator tests, ten focused widgets, the
complete 347-test app-shell suite, boundary/docs contracts and full seed
validation passed. `REL/UX-002` and `FE/P12-104..106` advance from `I1` to
`I3`; `REL/ARCH-003` advances only to partial `I2` because other retained large
screens remain part-bound. The distribution is now 146 rows at `I3`, 31 at
`I2`, 62 at `I1`, and 138 at `I0`; 239 of 377 rows remain at least `I1`.
WO-010C1 acquisition/restore/permission continuity is active next.

## 2026-08-22 — WO-010C1 first-session continuity

WO-010C1 moved trial selection, existing-access restore, opaque host-bound
acquisition consumption, Android VPN permission explanation/recovery and the
first-open/home/verified-connect milestones through one bounded
`FirstSessionCoordinator`. Welcome rendering no longer provisions a trial or
loads account data. Invalid/expired handoff state remains ephemeral and cannot
block normal access choices; permission dismissal does not connect and denial
has an explicit retry surface.

Authenticated analytics use a fixed first-session vocabulary, bearer-derived
account/device correlation and a bounded safe envelope. They contain no raw
handoff, credential, profile, endpoint or host-error material and never count
as access or connection proof.

Client analyze passed; complete app-shell passed `356/356`; runtime-engine
passed `54` tests with one exact-DLL backtest correctly skipped; the focused
Android JVM permission contract, client boundary/docs contracts and diff check
passed. Complete platform app-first regression passed `43/43`; docs contracts
passed `26/26`; link and diff checks passed.

`FE/P12-006..008` and `FE_PR/PR-03` advance from `I1` to local `I3`.
`MKT/MKT-700` remains `I1` pending retained marketing-to-installed-app proof.
The distribution is now 150 rows at `I3`, 31 at `I2`, 58 at `I1`, and 138 at
`I0`; 239 of 377 rows remain at least `I1`. WO-010D1 cabinet lifecycle and
platform-correct downloads is active next.

## 2026-08-22 — WO-010D1 cabinet lifecycle, downloads and payment return

WO-010D1 made cabinet downloads platform-correct and fail closed: Android and
Windows are selected from the browser platform, unknown platforms require an
explicit choice, no cross-platform fallback is allowed, and only a release
with URL, version, channel, publication date, positive size and valid SHA-256
gets a direct action. Partial/missing releases route to support, unbound
mirrors are not promoted and Apple remains a manual authenticated path.

The automatic dashboard tour became an on-demand launch checklist; the primary
action follows inactive/install/connect/complete/expiring lifecycle state.
Link-owned navigation now has a documented bounded wrapper and restores focus
to the destination main heading. Active cabinet surfaces no longer contain the
stale public/unsigned-beta copy. Payment return renders all six server states
and refreshes authenticated access before a paid result may claim entitlement;
paid/access mismatch, retry, new-payment and support paths are explicit.

WebApp lint and the 40-route production build passed; focused cabinet E2E
passed `63/63`; complete WebApp E2E passed `82/82` in 1.3 minutes. Payment
regression passed 99 tests plus 12 subtests, the client-app endpoint passed
5 focused tests, and text/copy/docs contracts passed `39/39`; link and diff
checks passed.

`FE/P12-009`, `P12-118`, `P12-119`, `P12-121`, `P12-122`, `P12-128` and
`FE_PR/PR-04` advance from `I1` to local `I3`. `FE/P12-120` remains `I2`
without measured complete active-client performance proof. The distribution is
now 157 rows at `I3`, 31 at `I2`, 51 at `I1`, and 138 at `I0`; 239 of 377 rows
remain at least `I1`. No hosted artifact, payment/provider, deploy,
physical-device, RU-origin or exact-candidate evidence is claimed. WO-010E1
adaptive controls and marketing motion safety is active next.

## 2026-08-22 — WO-010E1 adaptive behavior and marketing motion safety

WO-010E1 made client interaction physics host-adaptive: Apple uses Cupertino
scroll/switch/refresh behavior, Android uses Material overscroll and refresh,
and Windows/desktop uses clamped scrolling and native transitions/switches.
Client analyze, focused adaptive tests `3/3`, complete app-shell `359/359`, and
the presentation/docs contracts passed.

Marketing reveal content is now visible before JavaScript and only enters its
hidden pre-animation state after hydrated observer enhancement. OS reduced
motion replaces sticky showcase behavior with a static four-screen grid and
removes hero spatial motion; normal floating motion stops after two cycles,
stagger is bounded, and the mobile showcase has explicit controls and live
position. Lint, the 35-page production build, SEO, and the 57-route/viewport
responsive suite with no-JS/reduced-motion/mobile smokes passed.

Measurement justified the bundle change: strict asynchronous `LazyMotion`
reduced the Framer feature payload from 141.5/47.2 KiB raw/gzip to 43.5/17.1
KiB, saving 98.0/30.1 KiB. `FE/P12-015..017`, `P12-125`, `P12-204` and
`FE_PR/PR-06` advance from `I1` to local `I3`. `FE/P12-207` stays `I1`
pending an approved product and persistence contract for an explicit user
override. The distribution is now 163 rows at `I3`, 31 at `I2`, 45 at `I1`,
and 138 at `I0`; 239 of 377 rows remain at least `I1`. No retained success
screenshots, hosted/deployed, physical-device, provider/payment, RU-origin or
exact-candidate evidence is claimed. WO-010F1 accessibility and visual
contracts is active next.

## 2026-08-22 — WO-010F1 accessibility and visual contracts

WO-010F1 locally proved the client 200% critical path, unique action/status
semantics, meaningful live transitions and four deterministic widget goldens.
Marketing tabs now pass Arrow/Home/End and roving-tabindex browser smoke.
Cabinet dialog/route focus, direct serious/critical axe gates and an eight-state
mobile/desktop, light/dark, normal/reduced visual matrix pass in the release-
style browser suite. The global unlayered anchor color override was removed on
both web surfaces after axe exposed the contrast defect.

Client analyze and complete app-shell passed `362/362`; WebApp lint/build and
focused E2E passed `66/66`; marketing lint/build/SEO and its responsive,
no-JS, reduced-motion, keyboard and axe matrix passed. The final platform
text/copy/docs contract run passed `43/43`; client and platform presentation,
link and diff gates also passed.

`REL_DOD/DOD-14`, `FE/P12-018`, `P12-019`, `P12-115..117`, `P12-123` and
`P12-124` advance from `I1` to `I3`. The distribution is now 171 rows at `I3`,
31 at `I2`, 37 at `I1`, and 138 at `I0`; 239 of 377 rows remain at least `I1`.
No TalkBack, Narrator, physical-device, deployed-origin or exact-candidate
claim is made. WO-010G1 diagnostics, support and recovery UX is active next.

## 2026-08-22 — WO-010G1 diagnostics and encrypted support path

WO-010G1 replaced the static Profile diagnostics sheet with an importable,
refreshable Diagnostics route. It presents freshness plus tunnel, route, DNS
and egress proof, selects supported operational problem-book rules locally and
uses closed Russian/English safe-message keys. Raw host/provider/config detail
is excluded, and missing evidence never becomes a causal claim.

Diagnostics and Support chat now share the summary-profile bundle builder. The
screen previews exact categories, file count, size and redaction count, and one
configured action delegates case creation plus encrypted upload/offline queue
to the existing transfer authority. No competing cryptography or plaintext
export was introduced.

Client analyze passed; focused diagnostics tests passed `5/5`; the two profile
route/delivery widgets passed; complete app-shell passed `366/366`.
`OBS/OBS-067..069`, `OBS-086`, `OBS-089`, `OBS-090` and
`FRKN_ADOPT/ADOPT-06` advance from `I1` to `I3`. The distribution is now 178
rows at `I3`, 31 at `I2`, 30 at `I1`, and 138 at `I0`; 239 of 377 rows remain
at least `I1`. Contract-gated export, short-code, temporary-support-mode,
baseline/phase and exact-candidate claims remain open. WO-010G2 bounded
foreground polling with stop, jitter and backoff is active next.

## 2026-08-22 — WO-010G2 bounded foreground support polling

WO-010G2 replaced the fixed 10-second periodic support timer with one
importable one-shot coordinator. Polling now requires a mounted foreground
screen and eligible open ticket, adds bounded 0–2 second jitter, backs failures
off exponentially to two minutes and resets after success. Background, closed
ticket, loading/sending and disposal cancel pending work.

Client analyze passed; polling policy/coordinator tests passed `4/4`; the
success, failure and background-stop widgets passed; complete app-shell passed
`373/373`. `FE/P12-113` advances from `I1` to `I3`. The distribution is now
179 rows at `I3`, 31 at `I2`, 29 at `I1`, and 138 at `I0`; 239 of 377 rows
remain at least `I1`. Live-support traffic, physical-device background and
exact-candidate proof remain open. WO-010G3 remaining diagnostics authority
reconciliation is active next.

## 2026-08-22 — WO-010G3 phase graph and authority reconciliation

WO-010G3 added a bounded client connection phase graph backed only by the
sanitized breadcrumb ring. Closed event names, at most four attempts and
sixteen collapsed phases per attempt keep the view deterministic; reconnect
copy requires an observed rollback event, and raw JSONL attributes are never
read.

The contract audit retained encrypted host export, short support code,
temporary support mode and same-build comparison at `I1`: their required
export destination, encoder/decoder, policy-issuance/session and minimum-
cohort client projection authorities do not exist. Existing encrypted upload,
signed-policy verification primitives and operator release-health aggregate
are not relabelled as those missing product contracts.

Client analyze passed; focused diagnostics passed `6/6`; complete app-shell
passed `374/374`; scoped diff check passed with line-ending warnings only.
`OBS/OBS-088` advances from `I1` to `I3`. The distribution is now 180 rows at
`I3`, 31 at `I2`, 28 at `I1`, and 138 at `I0`; 239 of 377 rows remain at
least `I1`. WO-010H information architecture and bounded P2 decisions is
active next.

## 2026-08-22 — WO-010H information architecture and bounded P2 decisions

WO-010H proves the ordered Locations hierarchy, explicit latency freshness,
basic/expert Rules split, single expert change-summary/apply boundary and
grouped Profile ownership. The recovery launcher is framed as restoring
connectivity, while its technical whitelist-mode contract remains inside the
dedicated route.

Two expert-rule edits produce no early tunnel restart; one Apply action
produces exactly one disconnect/connect pair. Profile, Rules and Support keep
their existing product-state owners. Conditional P2 rows `P12-202`,
`P12-205..207` and `P12-209` remain `I1` with preserved evidence-based
deferrals because no P0/P1 acceptance failure requires those expansions.

Client analyze passed; focused IA tests passed `6/6`; complete app-shell
passed `375/375`. `FE/P12-107..111` and `FE_PR/PR-07` advance from `I1` to
`I3`. The distribution is now 186 rows at `I3`, 31 at `I2`, 22 at `I1`, and
138 at `I0`; 239 of 377 rows remain at least `I1`. WO-010I performance and
local quality gate is active next.

## 2026-08-22 — WO-010I performance and final local quality gate

WO-010I established performance contract `1.0.0` with 32 metrics, strict
nearest-rank/sample/environment/regression validation and repeatable static-
web, browser, API and client numeric collection. Evidence binds contract hash,
candidate/revision/dirty state, collector/toolchain, platform/device/origin and
metric-specific environment fields. The validator computes results and cannot
convert `MANUAL_OWNER_TEST`, `BLOCKED_BY_ACCESS` or a first observation into a
regression PASS.

The aggregate gate bound the dirty platform/client/Core worktrees and passed
all 15 local steps: performance tests `26/26`, app-shell analyze and `375/375`,
client seed/docs contracts, cabinet lint/build/E2E `66/66`, marketing build/
SEO/responsive/reduced-motion/axe, fresh admin build and static collection/
gate. Static stop budgets passed `9/9`; unmet optimization targets remain
explicit `target_met=false`. The retained report sets
`candidate_proven=false` and `promotion_status=MANUAL_OWNER_TEST`.

`REL/PERF-001`, `REL_GATE/GATE-E` and `FE_PR/PR-09` advance from `I1` to
local `I3`. `REL_DOD/DOD-13` remains `I1` without comparable exact-candidate
device/browser/API/artifact baselines. Conditional `FE/P12-203` remains `I1`
because no P0/P1 isolation failure justifies a second component-test
environment. The distribution is now 189 rows at `I3`, 31 at `I2`, 19 at
`I1`, and 138 at `I0`; 239 of 377 rows remain at least `I1`.

Phase 08 is locally complete. Physical devices, clean exact artifacts,
browser/network lab, controlled current-origin API, signing, current/brain/RU
origin and post-promotion performance remain Phase 11 evidence. Phase 09
`WO-011` marketing-pilot preparation is next; no campaign launch or external
communication is authorized.

## 2026-08-22 — WO-011 marketing governance and bounded pilot package

WO-011 established one closed marketing-governance registry and one bounded
winback contract, both digest-bound to the current commercial revision. The
repository remains legally launch-blocked and the holdout percentage remains
an unresolved owner decision. Trust-led copy, prohibited-claim scanning, exact
audience/suppression, two variants, the 3/6-month 10% offer, immutable 72-hour
window and 20-payment ceiling are locally enforced.

App and cabinet now consume at most one server-prioritized assignment with
exact price, deadline, terms, quota and complete commercial lineage. The same
IDs bind the signed checkout/order and identity-free paid, reversal,
first-connect, D7, D30 and renewal projections. The Operator Center exposes
legal/capacity/quota/payment/support/incident guardrails and the mature
`net_revenue_30d_per_capacity_unit`; the postmortem refuses CTR, early-payment
or incomplete-holdout winners and never auto-scales.

The dedicated local gate passed all 20 steps: current generated contracts,
copy scanner and manifest; backend `59/59`; operator API `1/1`; marketing,
cabinet and Operator Center lint/build plus SEO/responsive checks; client
analyze, bootstrap `83/83` and exact commercial-render widget `1/1`; docs
`30/30`; links. The retained dirty-worktree report
sets `candidate_proven=false`, `external_pilot_status=NOT_AUTHORIZED` and
`promotion_status=NOT_REQUESTED`.

Fifteen rows advance to local `I3`, `MKT_STAGE/STAGE-4` advances to `I2`, and
`MKT_STAGE/STAGE-5` advances only to `I1`. `MKT/MKT-600` remains `I2` pending
clean exact-candidate atomic deploy/readback/rollback proof. The distribution
is now 204 rows at `I3`, 27 at `I2`, 19 at `I1` and 127 at `I0`; 250 of 377
rows are at least `I1`.

Phase 09 is locally complete. Owner legal/channel approval, seller/terms,
provider, deployed revisions, live capacity, consent, support/rollback,
send/spend/launch and D30 outcomes remain external blocked/manual/not-authorized
lanes. Phase 10 `WO-012` FRKN-derived reconciliation is next.

## 2026-08-22 — WO-012 FRKN reconciliation and bounded AWG2 lab

WO-012 retained one Core and one sing-box graph while freezing the disabled
`pokrov.awg2.endpoint.v1` owner-lab subset. Core pins schema, module sum,
license, build tags and a synthetic-only fixture; validates keys, peer, MTU,
AWG headers and single-TUN behavior; and rejects raw AWG conversion instead of
silently mapping it to WireGuard. Client runtime accepts only the exact
digest-bound managed endpoint and preserves the existing Android/Windows host
owner and three outer routing modes.

Platform material is per-device authenticated ciphertext under the dedicated
AWG2 secret. One L3 provisioning action retains fingerprints only; the
disabled+killed allowlisted selector can issue material solely through the
authenticated managed profile. Public subscriptions, exports, locations and
consumer UI stay on legacy fallback. Missing/stale material or provenance and
the server kill fail closed before issuance.

The final local gate passed all 13 steps: cross-repo digest sync; platform
style, `45/45` AWG policy/API/security and `5/5` gate tests; docs `30/30`,
manifest and links; full Core verifier/tests on Go `1.25.13`; client analyze
and `59` runtime tests with one explicit old-DLL manual skip; and diff checks
in all three repositories. The dedicated report keeps
`candidate_proven=false`, `ru_ready=false`, cohort `NOT_AUTHORIZED` and
promotion `NOT_REQUESTED`.

HY2 is `NO_GO_FOR_1.2.0` until exact AWG/VLESS evidence identifies a concrete
gap and the owned server/kill/device budget prerequisites exist. AWG3,
Gecko/Mimic/port hopping, TrustTunnel/fptn and RU transport trends are retained
as monitor-only records.

Twenty-eight rows advance from `I0` to `I3`, two to `I2` and twenty-two to
`I1`. The distribution is now 232 rows at `I3`, 29 at `I2`, 41 at `I1` and
75 at `I0`; 302 of 377 rows are at least `I1`. Exact AAR/DLL traffic,
physical lifecycle, battery/CPU/thermal, owned server, current/brain/RU origins,
cohort and metric go/no-go remain manual, blocked or not authorized. Phase 10
local package is complete; Phase 11 `WO-013` exact-candidate preparation is
next.

## 2026-08-22 — WO-013B observability source-test closure (first slice)

The active client now retains a deterministic generated redaction corpus with
128 iterations over five secret/data families (640 fail-closed cases), plus a
literal `1.2.0` support-bundle manifest golden binding the diagnostic ID,
manifest hash, per-file hashes, sizes and categories, total bytes and removed
count. The isolated diagnostics collectors are reverified independently.

`observability_runtime` analyze and all `21/21` tests, `support_bundle` analyze
and all `12/12` tests, and `diagnostics_collectors` analyze and all `6/6` tests
passed. `OBS/OBS-013`, `OBS-075` and `OBS-076` advance from `I0` to local `I3`.
The distribution is now 235 rows at `I3`, 29 at `I2`, 41 at `I1` and 72 at
`I0`; 305 of 377 rows are at least `I1`. This is source-test evidence only: no
exact candidate, signed artifact, device/runtime or external-origin claim is
made.

The version boundary is also explicit: product packages target `1.2.0+30`,
Core source separately targets SemVer `1.1.0`, and both remain
`PRE_CANDIDATE_LOCAL` with `candidate_created=false`. The client keeps public
product `1.1.6` and exact Core `1.0.3` artifact evidence in separate retained
blocks. Core and client full source/seed gates plus four candidate-preflight
tests passed; no historical hash or release label was reused.

## 2026-08-22 — WO-013B observability source-test closure (second slice)

Release health now groups exact app/build/candidate/revision/platform/
architecture/channel/Core-ABI cohorts. Known issues reject missing or unknown
canonical error codes. A three-case crash/connect/update regression proves the
release-health gate refuses observation close and keeps rollout staged at 10%
when health deteriorates. Operator observability passed `6/6`, release policy
passed `5/5`, and ingest passed `26/26`, including 2,000 maximum-batch events,
100 idempotent replays and the existing rate/size/decompression guards within
the local time budget.

The new `pokrov.observability-data-inventory.v1` assigns purpose, allowed
modes, retention and owner to every event-envelope and persisted
release-health/support field. Its generator compares the live JSON Schema and
SQLAlchemy columns field-for-field. The generated 117-code support reference
is bound to the canonical catalog version/hash/count and fails on drift. The
inventory, support-reference and script-manifest slice passed `8/8` plus Ruff.
The canonical access-review playbook now defines post-JIT, weekly, monthly,
quarterly and pre-candidate reviews, independent ownership, Action Intent
review/revoke, redacted evidence and release-blocking findings; documentation
contracts passed `30/30` and the context audit passed. The playbook itself is
only `I1`: no production review run is claimed.

On the client, the safe deterministic `diag-*` code is visible and copyable
even when encrypted upload is unavailable, with explicit no-upload guidance.
App-shell analysis, the clipboard/no-upload widget cases and all `6/6`
diagnostics presenter tests pass. Those tests also retain bounded rollback and
failed-DNS timeline evidence; the existing Windows service runtime/recovery
fault matrix proves startup recovery, durable network restore, rollback retry
and fail-closed recovery errors. These remain local fixture/source proofs, not
physical-device crash, forced-kill or route/DNS cleanup evidence.

Fourteen rows advance from `I0` to local `I3`; `OBS/OBS-084` advances only to
`I1`. The distribution is now 249 rows at `I3`, 29 at `I2`, 42 at `I1` and 57
at `I0`; 320 of 377 rows are at least `I1`, and 128 remain below `I3`. No exact
candidate, signing, artifact, deployed-origin, production access review,
device/runtime or promotion claim is made.

## 2026-08-22 — WO-013B state migration and standard client gate

The client now owns `pokrov.client-state-migrations.v1` for the supported
`>=1.1.0 <1.2.0` to `1.2.0+30` boundary. Five sanitized fixtures are
checksum-bound to named migration, idempotency, future-schema and rollback
regressions for app-first session state, secure credentials, client experience,
the retired Windows system-proxy preference and Android runtime profiles.
Android update cache and the Windows service recovery journal are explicitly
inventoried as non-migrating state with their own tests; they are not silently
rewritten by a broad migration.

The client standard gate is now one PowerShell entrypoint on Windows and Linux.
It analyzes the three testless foundation packages, tests all eight
test-bearing packages/apps, selects `gradlew.bat` or `gradlew` by host and runs
both Android `direct` and `store` JVM tasks. The Ubuntu workflow pins Java 17
and Flutter 3.38.5 and calls the same runner after the cross-repository seed
gate. Source contracts require the full 11-module set, both wrappers and both
flavor tasks.

The exact Windows local run exited zero: 506 Flutter tests passed, the three
foundation analyses passed, and Gradle completed both flavor tasks with
`BUILD SUCCESSFUL` (`145` actionable, `10` executed, `135` up-to-date). The
one real released-DLL backtest stayed an explicit skip because
`POKROV_REAL_CORE_ROOT` was not supplied. The full cross-repository
`validate-seed` gate also passed. Hosted Ubuntu was not run, so `REL/TEST-001`
advances only to `I2`; `REL_DOD/DOD-11` advances to local `I3` on the migration
contract and Android/Windows fixture/source regressions.

The distribution is now 250 rows at `I3`, 30 at `I2`, 42 at `I1` and 55 at
`I0`; 322 of 377 rows are at least `I1`, and 127 remain below `I3`. No clean
candidate, hosted Linux result, signed artifact, physical upgrade/rollback or
promotion claim is made.

## 2026-08-22 — WO-013B fault, chaos and overhead contracts

The observability runtime now owns the exact 19-case connection-fault source
matrix from the release audit. Every injection is bound to a closed phase and
canonical known code, including the two-code TLS/clock and planted-token cases.
The Linux polkit case remains explicitly `NOT_SHIPPED`; this source map is not
misrepresented as end-to-end injection through portal, Core, TUN, service or
physical hosts. `OBS/OBS-077` therefore advances only to `I1`.

Loss, DNS unavailable, MTU black-hole and IPv6-path-unavailable scenarios now
execute through deterministic local attempt timelines. Each produces its
expected phase and error code and is forbidden from reaching verified state.
This is an implemented synthetic chaos contract, not real network mutation, so
`OBS/OBS-079` advances to `I2` and no device or route/DNS cleanup proof is
claimed.

## 2026-08-22 — WO-003H cross-repository version truth

The version audit found that active platform publishing/deployment/developer
owners still declared `v1.0.10` or `v1.0.13` while the client release authority
already retained public `v1.1.6` / `1.1.6+29` and the uncreated working target
`1.2.0+30`. It also found six completed old-version work-order waves still
classified as active execution.

The four platform owners now project the current retained/development facts and
name the client release-handoff seed as authority. The standard client gate
derives the required strings from that seed and validates every platform owner;
the release-bound CI source contract requires this check. No second manifest
was added. Completed `1.0.4-beta.1` through `1.1.1` waves remain intact as
`EVIDENCE`.

The full client seed/parity/cross-repository gate passes. Platform docs/context
and strict-v2 schema/runtime projection pass `89/89`; exact client-app API
release tests pass `6/6`; the update-prompt widget passes `1/1`. A deliberately
broader API-file observation first found one stale test fixture: program
application review omitted the mandatory action intent and correctly received
`428`. The fixture now proves direct fail-closed behavior, L3 prepare/confirm,
idempotent replay and opaque grant output. Its exact test passes `1/1`, the file
passes `9/9`, and the final combined platform slice is `98/98`; the initial
`97/98` remains recorded rather than hidden.

`REL/VER-001` advances from `I1` to local `I3`. The distribution is now 266
rows at `I3`, 35 at `I2`, 45 at `I1` and 31 at `I0`; 346 of 377 rows are at
least `I1`, and 111 remain below `I3`. Dirty worktrees, the absent release index
and absent exact candidate keep `I4` blocked.

The bounded overhead harness exercises the actual serializer, sequence fence,
queue and asynchronous writer. On the current Windows host it accepted
`266/266` events with zero loss: idle-series volume `8,472` bytes, connect burst
`216,872` bytes, maximum event `849` bytes and peak queue `216,872` bytes, all
within the initial Windows limits. The report is hard-coded
`PARTIAL_LOCAL/candidate_proven=false`; idle CPU, cold-start/connect/idle-app
deltas and physical battery remain `NOT_MEASURED`. `OBS/OBS-080` advances only
to `I1`.

`observability_runtime` analysis and all `27/27` tests pass, the fault/overhead
focused set passes `6/6`, and the full cross-repository client seed gate passes.
The distribution is now 250 rows at `I3`, 31 at `I2`, 44 at `I1` and 52 at
`I0`; 325 of 377 rows are at least `I1`, while 127 remain below `I3`. No exact
candidate, physical chaos, device overhead, signed artifact, deployed origin or
promotion claim is made.

## 2026-08-22 — WO-013B permanent STOP-SHIP gate

The exact seven STOP-SHIP findings from the full release audit are now owned by
`pokrov.release-stop-ship-regressions.v1`: `PAY-001/002`, `REL-001/002` and
`WIN-001/002/003`. The read-only validator fails on a missing ID, missing test
file or missing semantic anchor and records the source SHA-256. All seven local
anchors pass; the validator and script-manifest focused suite passes `9/9`, and
Ruff passes. `REL_DOD/DOD-01` advances only to `I2`: the permanent local gate
exists, but not all external/manual STOP-SHIP conditions pass.

The same command queried GitHub branch protection without mutation. The API
reports `BLOCKED_BY_ACCESS` for private `Kiwunaka/portal:master` and
`Kiwunaka/POKROV-app:main` because the current plan does not expose branch
protection, while `Kiwunaka/pokrov-core:main` is explicitly
`FAIL_UNPROTECTED`. The combined STOP-SHIP result is therefore `NO_GO`.
`REL/REL-001` and `REL_DOD/DOD-09` advance only to `I1`; enabling a supported
plan/visibility and changing repository settings requires an owner decision.

The WIN-003 false-green source regression is bound to the shared four-proof
connection contract, but exact clean-host Windows TUN/DNS/egress/rollback is
still `NOT_RUN`. `REL/WIN-003` advances only to `I1`. No source test converts
that manual gate into a pass.

The distribution is now 250 rows at `I3`, 32 at `I2`, 47 at `I1` and 48 at
`I0`; 329 of 377 rows are at least `I1`, while 127 remain below `I3`. No GitHub
setting, exact candidate, clean-host runtime, signing, deploy or promotion was
performed.

## 2026-08-22 — WO-013B stale aggregate source closure

Four aggregate rows that still said `I0` were rechecked against the current
cross-repository gates rather than advanced by documentation alone. The exact
local `run_client_release_gate.py contract` command passed product/Core version
parity, observability schema/catalog digest parity, release-source logging,
handoff v2, client CI/runner, presentation/performance/docs and the full client
seed contract across platform, client and Core. The platform focused suite
passed `51` tests plus `21` subtests. `REL_DOD/DOD-03` advances to local `I3`.

The shared connection reducer passed `14/14`: DNS, host/uplink and egress proof
are all required on every supported host, and a started tunnel without proof
is never green. Together with the full `observability_runtime` `27/27` pass,
`REL_DOD/DOD-07` advances to local `I3`. This is source/runtime-fixture proof,
not exact physical-host DNS/egress evidence.

The client PR workflow source contract passes and calls the same strict
cross-repository seed gate plus standard 11-module/two-flavor runner with pinned
Java 17 and Flutter 3.38.5. `FE/P12-020` advances to local `I3`; no hosted PR
run is claimed. The dispatcher remains non-blocking under a blocked writer and
the Windows in-process overhead limits pass, but device CPU/cold-start/connect/
idle/battery/thermal are still unmeasured. `OBS_DOD/DOD-05` advances only to
`I2`.

The distribution is now 253 rows at `I3`, 33 at `I2`, 47 at `I1` and 44 at
`I0`; 333 of 377 rows are at least `I1`, and 124 remain below `I3`. No clean
freeze, hosted CI, device measurement, exact candidate, signing, deploy or
promotion is claimed.

## 2026-08-22 — WO-013B critical frontend Playwright CI closure

The platform Guardrails workflow now installs Chromium with each frontend's
own Playwright dependency before running the critical suites. The static
workflow contract passes `34` tests plus `21` subtests and proves that the
webapp browser gate remains in the Quick release gate while adminapp runs its
own end-to-end command directly.

The local webapp suite passed `85/85`. The first adminapp run passed `71/72`
and exposed a stale route-source whitelist: the promo page intentionally owns
the promo list, promo slots and commercial-campaign sources because it mounts
the winback decision panel. The focused route-isolation test passed after the
whitelist was aligned with those three exact paths, then the full adminapp
suite passed `72/72`. No product fetch behavior was widened.

`FE/P12-021` advances from `I0` to local `I3`. The distribution is now 254
rows at `I3`, 33 at `I2`, 47 at `I1` and 43 at `I0`; 334 of 377 rows are at
least `I1`, and 123 remain below `I3`. Hosted GitHub Actions is `NOT_RUN` and
the separate STOP-SHIP branch-protection gate remains `NO_GO`; no clean freeze,
exact candidate, signing, deploy or promotion is claimed.

## 2026-08-22 — WO-013B Operator Center support operations closure

The Admin API v2 and canonical ticket UI now close `OBS/OBS-061..066`: ordered
case timeline; version plus permission/Core/TUN/DNS/egress summary; safe search
for case, opaque bundle and correlation code; version-scoped known-issue
matching; explicit L1/L2/SRE/Security separation; and reasoned, step-up,
actor-bound, one-use ciphertext access with grant/download audit.

Local proof passed: support/observability/role/frontend contracts `33/33`, the
new v2 end-to-end API test `1/1`, TypeScript, ESLint, production build, cutover
verification and full adminapp Playwright `75/75`. The first combined backend
run exposed one stale fixture code (`CORE-START-01`) already rejected by the
canonical registry; it was corrected to `CORE-001`, and the complete affected
suite then passed `33/33`.

Six rows advance from `I0` to local `I3`. The distribution is now 260 rows at
`I3`, 33 at `I2`, 47 at `I1` and 37 at `I0`; 340 of 377 rows are at least `I1`,
and 117 remain below `I3`. Authenticated staging/production, real operator
roles/data/access, hosted CI, clean freeze, exact candidate, signing, deploy and
promotion remain unproved or not authorized.

## 2026-08-22 — WO-003C reproducible dependency closure

Platform runtime, test and ops dependencies now have reviewed `.in` sources and
universal Python 3.12 locks with exact transitive versions and SHA-256 hashes.
`requests` is a direct runtime dependency rather than an accidental `geoip2`
transitive, and the test lane uses Starlette 1.6's preferred pinned `httpx2`
instead of a workflow-only `httpx` repair. Four release-bound workflows reject
dependency/toolchain drift and install the locks with `--require-hashes`.

Adminapp, webapp and marketing use exact direct versions, npm lockfile v3 and
one shared Python/Node/npm/Next/React/Tailwind/TypeScript/Playwright contract.
The Next 16.3.2 reconciliation exposed stale generated types and a real static
export segment-path mismatch. Clean builds passed after generated caches were
moved to recoverable temp locations; marketing now creates deterministic RSC
aliases and its responsive gate tests the production `out/` artifact.

Final local proof: Python hash-only resolutions and dependency contract `PASS`;
contract/script tests `7/7`; backend/API `139` tests plus `8` subtests; fresh
`npm ci` on all three frontends; admin build/cutover `PASS`; web full Playwright
`85/85`; admin full Playwright `75/75`; marketing production responsive `PASS`
across `19 × 3` route/viewports plus no-JS, reduced-motion, keyboard and axe
checks. Compatible dependency remediation leaves all three npm audits at zero
vulnerabilities and used no forced major rewrite.

`REL/DEP-001` advances from `I0` to local `I3`. The distribution is now 261
rows at `I3`, 33 at `I2`, 47 at `I1` and 36 at `I0`; 341 of 377 rows are at
least `I1`, and 116 remain below `I3`. Hosted CI, a clean frozen revision and
exact-candidate reproduction remain unproved. No deploy, signing or promotion
was performed.

## 2026-08-22 — WO-003D strict v2 runtime consumer

The release path had one real source gap: orchestration accepted only strict
schema v2, while the runtime sync consumer still projected only legacy
`downloads/runtime_env`. A valid v2 candidate would therefore pass the offline
validator and then fail to produce Android/Windows runtime values.

The consumer now validates v2 again before SSH is loaded, selects only the
canonical Android APK and Windows setup-EXE identities, and projects exact
release/channel/candidate, handoff SHA-256, artifact-set SHA-256 and Core
version/ABI/package. Authenticated and public client-app APIs expose the same
bounded identity only when the full tuple is valid; legacy or partial env
returns `null`.

Local proof passed: v2 projection/validator `53/53`; client-app API `6/6` and
the complete adjacent API regression `29` tests plus `4` subtests; release
orchestration `48` tests plus `21` subtests; synthetic v2 dry-run, compilation,
focused Ruff, webapp ESLint, docs `26/26`, links and scoped diff check. The
dry-run opened no SSH connection and wrote no runtime state.

`REL_DOD/DOD-02` and `FE/P12-022` advance from `I0` to `I2`. The distribution
is now 261 rows at `I3`, 35 at `I2`, 47 at `I1` and 34 at `I0`; 343 of 377 rows
are at least `I1`, and 116 remain below `I3`. The exact candidate, public
release-index revision, manifest signature, signed artifacts, hosted CI,
runtime/static readback, deploy and promotion remain unproved or unauthorized.

## 2026-08-22 — WO-003E shared release catalog reconciliation

Phase 01 reconciliation found that `FE/P12-010` had remained at `I0` despite
the accepted behavior already being delivered by `WO-010D1` and the strict v2
runtime/API work. One release-handoff-backed client-app catalog now feeds the
authenticated cabinet and its fail-closed public projection consumed by
marketing. The cabinet's Android and Windows cards render version, publication
date, positive size, architecture/format, channel and the complete SHA-256;
partial or missing metadata cannot expose a direct download.

A dedicated browser assertion now binds all six required facts for both
platform cards to the catalog fixture. The production build generated 40
routes and focused cabinet Playwright passed `67/67`. Client-app authenticated
and public projection tests passed `6/6`; the exact marketing install plus
frontend copy contracts passed `14/14`; docs/context/preflight tests passed
`34/34`, and context, link and scoped diff checks passed. Candidate preflight
remains `BLOCKED` by five conditions with 115 rows below `I3`. A wider adjacent
run produced 47 passes plus 4 subtests and one unrelated homepage-contract
failure because the test still required the unmounted `ServicesGrid`. That
initial result remains retained as `NOT_PASS`; the `WO-011H` follow-up below
closed it before final handoff.

`FE/P12-010` advances from `I0` to local `I3`. The distribution is now 262
rows at `I3`, 35 at `I2`, 47 at `I1` and 33 at `I0`; 344 of 377 rows are at
least `I1`, and 115 remain below `I3`. Exact-candidate authenticated/public
browser readback, published artifact verification, hosted CI, deploy and
promotion remain unproved or unauthorized.

## 2026-08-22 — WO-011H marketing homepage contract drift closure

The adjacent regression from `WO-003E` exposed two stale test expectations.
The current governed homepage intentionally omits the six-tile `ServicesGrid`
and uses the trust-led hero `Проверьте подключение до оплаты`; the story test
still required both the retired grid and the older service-led YouTube/TikTok/
ChatGPT claim. Restoring those claims would contradict the current marketing
governance and reintroduce a parallel promise surface.

The story contract now requires the current homepage sequence, explicitly
rejects remounting `ServicesGrid`, requires the governed hero and rejects the
old claim. The marketing README now points to the real `app/page.tsx` owner and
records the trust-led sequence. The exact marketing story suite passed `6/6`;
the complete adjacent API/marketing/copy rerun passed 48 tests plus 4 subtests.

No ledger row advances: this is a regression repair for already-proved local
marketing rows, not new product scope. No public deploy, campaign, claim
publication or promotion was performed.

## 2026-08-22 — WO-003F release identity consumers

The strict v2 handoff already owned candidate version and artifact identity,
but it had no release-notes field. Runtime projection therefore populated the
version while clearing both platform notes, even though the client update
prompt could render them. The cabinet also omitted release notes from its
otherwise complete release card.

Schema v2 now requires a bounded single-line summary and canonical GitHub
release URL whose tag matches `release.version`. The client generator preserves
that record and rejects a manifest version that differs from Android, Windows
or app-shell package identity. Release builds feed the package-derived version
to the shared `pokrovClientVersion`, which owns visible profile/navigation text,
diagnostics and update requests. Runtime sync projects the same manifest
version, notes and timestamp to Android and Windows; the API feeds both the
client prompt and cabinet. Missing notes now make a cabinet artifact partial
and remove its direct download.

Local proof passed: platform schema/validator/runtime projection `57/57`;
client strict-v2/parity/UI identity contract `15/15`; client seed/docs contract
`PASS`; exact update-prompt widget `1/1`; client-app API `6/6`; production build
40 routes; final cabinet Playwright `67/67`. The first browser run retained
`66/67` because an older secondary-APK fixture omitted the new required notes;
fail-closed behavior removed its link, the fixture was completed, and the full
suite reran green.

`REL_DOD/DOD-16` advances from `I0` to local `I3`. The distribution is now 263
rows at `I3`, 35 at `I2`, 47 at `I1` and 32 at `I0`; 345 of 377 rows are at
least `I1`, and 114 remain below `I3`. All worktrees remain dirty, the public
release index and exact candidate are absent, and hosted CI, signed artifact
identity, deployed readback, deploy and promotion remain unproved or
unauthorized.

## 2026-08-22 — WO-003G current readiness and retained history

The active client release backlog and Android, Windows, cutover, WARP,
responsive, motion/performance and Apple readiness owners now answer the
current 1.2.0 question explicitly. They name retained public `1.1.6`, the
uncreated `1.2.0+30` `PRE_CANDIDATE_LOCAL` target and the still-manual or blocked
exact-candidate gates without interleaving prior-candidate pass labels.

Six previous document bodies remain intact under client history directories as
`EVIDENCE`. The client registry and executable documentation contract enforce
the current/evidence split and current platform-matrix values. On the platform,
the public-beta runbook and 2026-08-13 direct-release tracker are now evidence
only; the latter routes current execution to this megaplan.

Client documentation and full seed/cross-repository contracts pass. Platform
documentation/context tests pass `31/31`, and the context audit, links, JSON and
scoped diff checks pass. No candidate, signing, deploy, sync or promotion was
performed.

`REL/DOC-001` advances from `I1` and `REL_DOD/DOD-19` from `I0` to local `I3`.
The distribution is now 265 rows at `I3`, 35 at `I2`, 46 at `I1` and 31 at
`I0`; 346 of 377 rows are at least `I1`, and 112 remain below `I3`. The exact
candidate and public release
index remain absent, and all three worktrees remain dirty, so `I4` is not
claimed.

## 2026-08-22 — WO-003I source and release-index separation

The exact tracked-file inventory found no temporary/build output in the
platform or Core repositories and two clean tracked helpers under the client
`packages/app_shell/.tmp/`. Those two files are now deleted by an ordinary Git
patch (53 lines total) and remain recoverable from blobs
`9522d859184c5609f40f3765ba6e788b980d7443` and
`9f7e3ac8809f0da575ef3053281c7cf6efabb58f` until the change is committed.

The client repository also retains 138 files / 4,642,837,966 bytes under
`artifacts/releases/**`. That tree is evidence and rollback history, not
disposable build output; it remains byte-untouched. Its boundary owner now
distinguishes three pinned active runtime binaries, frozen historical release
evidence, ignored local candidate staging, and the separate signed public
release index. Android and Windows output already stays under ignored
`apps/**/build/**`, so no packaging-path migration was needed.

An executable repository-hygiene gate now rejects tracked temp/build paths,
candidate binaries outside the three runtime dependencies, local staging in
Git, or development target `1.2.0` under retained history. The standard
cross-repository client gate runs it. The strict-v2 generator also rejects any
destination inside the client checkout except ignored candidate staging, while
preserving external temporary/release-index output. Focused hygiene, strict-v2
16-case, CI and docs contracts pass; the complete client seed/cross-repository
gate passes.

`REL/REPO-001` advances from `I0` to `I2`. The distribution is now 266 rows at
`I3`, 36 at `I2`, 45 at `I1` and 30 at `I0`; 347 of 377 rows are at least `I1`,
and 111 remain below `I3`. A clean committed client revision and the separate
signed public release-index repository/revision are still absent or
`BLOCKED_BY_ACCESS`; therefore source/index separation is not yet locally
complete at `I3`, and no candidate, signing, publication or promotion is
claimed.

## 2026-08-22 — WO-006I safe transport failure classification

The canonical error catalog now splits Core start transport failures into
`TRANSPORT-001` timeout, `TRANSPORT-002` refusal, `TRANSPORT-003`
authentication rejection and `TRANSPORT-004` protocol negotiation failure.
Core applies typed timeout/refusal checks plus a bounded marker set and emits
only the closed code over the unchanged event ABI 1 / desktop ABI 2 boundary.
Dart, Android and Windows consumers accept the four codes and continue to
reject raw URL/secret-like material.

Platform catalog/reference/handoff regression passed `75/75`; the canonical
Core Go 1.25.13 release gate passed; observability contracts/runtime passed
`3/3` and `27/27`; Android direct/store and the rebuilt Windows native runtime
test passed. The focused Gate B state, diagnostics and migration set passed
`24/24`, and runtime-engine passed 59 tests with one declared exact-old-DLL
skip. Full client cross-repository validation passed.

`OBS/OBS-050` advances from `I2` and aggregate `REL_GATE/GATE-B` from `I0` to
local `I3`. The distribution is now 268 rows at `I3`, 35 at `I2`, 45 at `I1`
and 29 at `I0`; 348 of 377 rows are at least `I1`, and 109 remain below `I3`.
Exact-candidate Android/Windows observations and operator production readback
remain `I4`; no candidate, signing, publication or promotion is claimed.

## 2026-08-22 — WO-003J Phase 01 residual authority reconciliation

The frontend source plan names `Kiwunaka/pokrov` as the stable trust surface
for canonical assets, checksums, signature metadata, manifest/notes and exact
release facts. Strict v2 defines those facts, but the separate repository is
unavailable and candidate 1.2.0 does not exist. `FE/P12-023` therefore advances
only from `I0` to verified `I1` with `BLOCKED_BY_ACCESS`.

PR-00's baselines/lanes, manifest/flags, deterministic product facts, stable
reason codes and motion semantics are implemented across WO-001, WO-002/003,
WO-008A, WO-006A/006I and WO-010E. Current contract regression passed `73/73`;
the focused client motion/app-shell regression passed `164/164`. Because these
changes share dirty worktrees with later visible UI slices, an isolated clean
no-visible-UI freeze cannot be claimed. `FE_PR/PR-00` advances from `I0` to
`I2`, not `I3`.

The distribution is now 268 rows at `I3`, 36 at `I2`, 46 at `I1` and 27 at
`I0`; 350 of 377 rows are at least `I1`, and 109 remain below `I3`. No commit,
public index readback, signing, candidate, publication or promotion occurred.

## 2026-08-22 — WO-004D ABI v3 post-1.2.0 decision

The frontend source authority requires the 1.2.0 typed adapter on Core ABI v2,
labels ABI v3 `ConnectionStatus` as a proposal after 1.2.0, places it in the P2
post-blocker table and explicitly forbids ABI v3 from blocking this release.
The current desktop ABI 2 / event ABI 1 contract and fail-closed future-ABI
client tests pass.

`FE/P12-201` advances from `I0` to verified `I1` with status
`DEFERRED_POST_1_2_0`; no v3 implementation is claimed. The distribution is
now 268 rows at `I3`, 36 at `I2`, 47 at `I1` and 26 at `I0`; 351 of 377 rows
are at least `I1`, and 109 remain below `I3`. Candidate and promotion state are
unchanged.

## 2026-08-22 — WO-005D4 Android private operational journal

Android now has one release-safe host journal under the app-private no-backup
directory. A 256-record single-writer queue feeds a current and one previous
256 KiB JSONL file. The schema accepts only time, sequence, optional positive
generation, dropped-record count and closed event/outcome enums; message, URL,
endpoint, interface, package, profile, token, exception and stack fields do not
exist.

Closed producers cover VPN service/TUN and VPN/notification permission
lifecycle, default-network callbacks, Doze, app-standby/background restriction,
a rate-limited stack-free main-thread watchdog, direct APK identity decisions
and installer/store handoff. Telemetry initialization/write failures do not
block application behavior and raw Core text remains outside the journal.

Direct and store JVM suites each passed `172/172`; both debug flavor builds,
client docs contract and explicit active-root seed/cross-repository validation
passed. The first seed invocation used its default neighboring Core checkout
and is retained as a wrong-root diagnostic; the explicit active-worktree rerun
is the credited pass. No retained release artifact changed.

`OBS/OBS-037`, `OBS-038`, `OBS-039`, `OBS-041` and `OBS-042` advance from `I0`
to local `I3`. The distribution is now 273 rows at `I3`, 36 at `I2`, 47 at
`I1` and 21 at `I0`; 356 of 377 rows are at least `I1`, and 104 remain below
`I3`. Physical-device journal delivery, controlled ANR, network/power cycles,
production-signed hostile upgrades and exact-candidate proof remain `I4` gates.

## 2026-08-22 — WO-005C4 Windows stack-only crash profile

The Windows UI and SCM service now share one fail-open native
`POKROV_WINDOWS_CRASH_V1` contract under separate protected storage roots. A
record contains FILETIME, process role, numeric exception code and at most 32
allowlisted module-relative RVAs from the process, Flutter, Core and Dart app
modules. Unknown modules are omitted. The handler writes one current and one
previous file per process and chains the preceding exception handler.

The source has no minidump writer, WER `LocalDumps` mutation, symbol/path
resolution, absolute addresses, registers, exception text, command line,
profile/config, endpoint, token, heap or full-memory field. Debug and Release
Windows builds passed; canonical Debug CTest passed `7/7`; the affected Release
crash-profile CTest passed `1/1`; Windows Flutter passed `21/21`; analyze and
the explicit-root client seed gate passed. An exploratory all-Release CTest
returned `6/7` only because the pre-existing service integration executable is
intentionally `_DEBUG --test-once`-only; it is retained as noncanonical
diagnostic evidence, not a PASS or product regression.

`OBS/OBS-035` advances from `I0` to local `I3`. The distribution is now 274
rows at `I3`, 36 at `I2`, 47 at `I1` and 20 at `I0`; 357 of 377 rows are at
least `I1`, and 103 remain below `I3`. Controlled UI/service crashes,
current/previous DACL readback, SCM recovery, route/DNS restoration,
support-bundle inclusion and exact signed candidate proof remain `I4` gates.

## 2026-08-22 — WO-013A2 exact candidate stage matrix

Candidate preflight no longer guesses release timing from a row's plan, phase,
status or free-form `next_action`. One versioned policy maps exact `(plan,id)`
keys to `pre_freeze`, `candidate`, `external` or `deferred`. Its fail-safe
default is `pre_freeze`; 70 exact overrides carry reasons, and every external
override declares `pre_candidate` or `post_candidate`. Unknown keys, duplicate
overrides, unsupported fields/stages, ambiguous external timing, a non-377
ledger and any non-safe default fail validation.

The 103 rows below `I3` now split into 33 local pre-freeze rows, 32 candidate
rows, 17 external rows and 21 deferred rows. Three external rows are explicit
pre-candidate blockers. Candidate and deferred rows no longer create the
impossible condition that candidate bytes must be proved before they can be
created; ordinary local gaps outside broad P11/Gate/DoD buckets now fail closed
instead of being ignored.

Focused regression passed `9/9`; Ruff, live expected-blocked preflight,
documentation/preflight tests, context audit, links, JSON and diff checks pass.
The report remains `BLOCKED` with seven explicit blockers and
`candidate_created=false`. No ledger row advances: distribution remains 274
rows at `I3`, 36 at `I2`, 47 at `I1` and 20 at `I0`; 103 remain below `I3`.

## 2026-08-22 — WO-004A2 direct cutover and visual baseline

The implemented connection architecture has one mutable owner,
`ConnectionCoordinator`, and derives the typed reducer and shared presentation
only inside the focused connection boundary. Home receives one aggregate
`ProtectionViewState` plus `ProtectionIntents`; the boundary contract rejects
parallel raw fields, copy and callbacks. Recreating the removed legacy reducer
for a shadow period would restore two live connection truths, so direct cutover
is accepted as the explicit owner decision for the already implemented PR-01.

Four deterministic `390 x 844` widget goldens retain idle light, first
route-scope dark, verified dark and degraded light. The presentation boundary
check passed, the focused reducer/coordinator suite passed `14/14`, and the
golden test compared all four images without update mode and passed `1/1`.

`FE_PR/PR-01` and `FE_PR/PR-02` advance from `I1` to local `I3`. The
distribution is now 276 rows at `I3`, 36 at `I2`, 45 at `I1` and 20 at `I0`;
357 of 377 rows are at least `I1`, and 101 remain below `I3`. The local
pre-freeze queue falls from 33 to 31 rows. Physical-device rendering,
TalkBack/Narrator, OS scaling and exact-candidate screenshots remain open before
`I4`; no candidate, signing, publication or promotion is claimed.

## 2026-08-22 — WO-004B2 Core release CI matrix

The Core workflow now has one explicit platform-build and source-quality
contract. Linux executes the complete root module plus focused ABI, vet, race,
reachable-vulnerability, bounded Staticcheck and parser-fuzz gates and writes
two deterministic CycloneDX source SBOMs. Separate clean-source jobs build
Android, Windows and Apple trees twice, reject any byte difference and retain
bounded evidence JSON. Android verifies four ABIs; Windows verifies all desktop
exports and runs the active client's 100-cycle proxy backtest. Linux ships no
artifact in POKROV 1.2.0.

The canonical local Core gate and exact bounded Staticcheck set pass. The fuzz
probe passed `66,088` executions with no panic. Two local SBOM generations are
byte-identical, but CycloneDX emits retained license-detection/version warnings
for local forks, standard library and several dependencies; this is inventory
proof, not legal clearance. The evidence-writer accepts matching fixtures and
rejects a one-byte mismatch. Workflow YAML and its fail-closed source contract
pass. Hosted Android/Windows/macOS jobs are `NOT_RUN`; no binary was uploaded,
signed, attested, tagged, published or promoted.

`REL/CORE-001` advances from `I2` to local `I3`; `REL_DOD/DOD-10` remains `I2`
until the hosted platform matrix and exact-candidate evidence exist. The
distribution is now 277 rows at `I3`, 35 at `I2`, 45 at `I1` and 20 at `I0`;
357 of 377 rows are at least `I1`, and 100 remain below `I3`. The pre-freeze
queue falls from 31 to 30; candidate/external/deferred counts remain
`32/17/21`. No candidate, signing, publication or promotion is claimed.

## 2026-08-22 — WO-008H active-client product facts adoption

The platform synchronizer now projects its product/public/commercial/tariff
authority into digest-pinned client JSON and a typed generated Dart library.
The active seed runtime consumes platform scope, engines, default route, trial,
Telegram reward and support facts. The standard client seed gate invokes the
synchronizer in read-only mode and rejects both generated-byte and runtime-
consumer drift. A negative temporary fixture proves the rejection does not
rewrite its target.

The first generated-file integration used a Dart `part`; the existing
presentation boundary correctly rejected the increase from 29 to 30. The
projection was converted to an ordinary import and the unchanged 29-part guard
passed. Platform tests passed `25/25`; the explicit-root client seed gate,
Flutter analyze and the exact updated runtime assertion pass. Prices, promo
terms, referral account state, quota, orders, payments and entitlements remain
server authority.

`REL/CONTRACT-001` advances from `I2` to local `I3`. `FE/P12-024` and
`ADOPT/ADOPT-07` remain `I2` because their wider exact-candidate/device criteria
are not proved here. The distribution is now 278 rows at `I3`, 34 at `I2`, 45
at `I1` and 20 at `I0`; 357 of 377 rows are at least `I1`, and 99 remain below
`I3`. The pre-freeze queue falls from 30 to 29; candidate/external/deferred
counts remain `32/17/21`. No candidate, signing, deployment, publication or
promotion is claimed.

## 2026-08-22 — WO-007G admin domain slices

The current admin transport exceeded its declared architecture ceiling:
`api_admin_routes.py` had 7,237 lines against a 7,100-line guard. The ceiling
was not raised. One contiguous modular-monolith split leaves a 4,336-line base
admin slice, a 2,774-line guarded action-intent orchestration slice and a
153-line guarded emergency-network/node transport slice. The single `api.*`
compatibility surface, process, route table and database authority remain.

Composition/order tests pass `4/4`; exact action/network tests pass `33/33`;
mutation-policy/manifest/probe tests pass `16/16`; the router-required backend
matrix passes 154 tests plus 8 subtests. The imported FastAPI table contains
300 unique method/path pairs and no duplicates. A new ceiling now inventories
the retained 8,365-line action-intent service instead of letting it grow
unbounded.

`REL/ARCH-002` remains `I2`: the large public/action-service inventory is still
explicitly open, so this partial split is not relabelled as full local proof.
The distribution remains `I3=278`, `I2=34`, `I1=45`, `I0=20`; 99 rows remain
below `I3` and the stage split stays `29/32/17/21`. No candidate, deployment,
server mutation, payment, publication or promotion occurred.

## 2026-08-22 — WO-010J release-critical client update owner

The client update check/prompt/progress flow no longer keeps its mutable gate,
deduplication key or presentation widgets in the 6,324-line shell composition
root. One ordinary imported feature library now owns that state machine and
presentation; metadata access, trusted installer/handoff execution and
lifecycle/observability side effects remain injected shell responsibilities.
The shell is 6,121 lines, the new owner is 325 lines and the guarded `part`
count stays 29.

Client analyze, coordinator tests `2/2`, focused update widgets `2/2`, the full
app-shell suite `379/379`, the strengthened presentation boundary, explicit-
root cross-repository seed validation and diff checks pass. Together with the
existing Protection Center controller, this closes the remaining concrete
P0/P1 screen-ownership failure without a mechanical rewrite of every retained
feature part.

`REL/ARCH-003` advances from partial `I2` to local `I3`. The distribution is
now `I3=279`, `I2=33`, `I1=45`, `I0=20`; 98 rows remain below `I3` and the
stage split becomes `28/32/17/21`. Physical Android/Windows installer,
accessibility, exact-candidate and public-index proof remain open before `I4`.
No candidate, artifact, signing, deployment, publication or promotion is
claimed.

## 2026-08-22 — WO-007H public/client route slices

The retained 5,822-line public route module is now a 2,019-line public/session
bootstrap slice plus a 3,980-line managed-client feature/runtime slice. The
9,594-line composition root still loads one explicit twelve-slice route table,
and payment transport retains no direct DB session lifecycle.

The mixed API regression exposed a restored-owner bug in the compatibility
loader: cleanup by function identity allowed an older `api` export to enter the
next slice bootstrap set, after which the fresh export lost ownership and
disappeared on a later import. Cleanup now uses the registered ownership set,
with permanent stale-slice and stale-owner regressions. The exact formerly
failing nine-file sequence passes 234 tests plus 12 subtests in one process;
focused architecture/payment/policy tests pass 25/25, network/module tests pass
16/16, and the imported FastAPI table retains 300 unique method/path pairs with
no duplicates.

`REL/ARCH-002` remains `I2`: the 8,365-line action-intent service is still
explicit inventory before a full portal architecture proof. Distribution stays
`I3=279`, `I2=33`, `I1=45`, `I0=20`; 98 rows remain below `I3`, and the stage
split remains `28/32/17/21`. No candidate, deployment, server mutation,
payment, signing, publication or promotion occurred.

## 2026-08-22 — WO-007I Action Intent domain/runtime boundary

The last declared portal architecture inventory is now bounded: the former
8,365-line Action Intent service is a 6,488-line domain-policy owner plus a
2,034-line generic persistence/execution runtime. `ACTION_POLICIES` exists only
in the domain service and is passed explicitly; the runtime imports no domain
service and registers no policy or route. Legacy and Operator Center v2 imports
remain thin wrappers over that one live mapping.

Action/policy/architecture tests pass 33/33, the broad admin/Operator Center
matrix passes 68/68, manifest/probe contracts pass 32/32, both modules compile,
and the imported twelve-slice FastAPI table retains 300 unique method/path
pairs with no duplicates.

`REL/ARCH-002` advances `I2 -> I3`. Distribution becomes `I3=280`, `I2=32`,
`I1=45`, `I0=20`; 97 rows remain below `I3`, and the stage split becomes
`27/32/17/21`. Production PostgreSQL/load, operator-action/rollback and exact-
candidate proof remain open before `I4`. No candidate, deployment, server
mutation, operator production action, payment, signing, publication or
promotion occurred.

## 2026-08-22 — WO-006J operational producers and routing count

The active client now emits closed auth, entitlement-refresh, live-performance
and encrypted-support start/finish events through the existing bounded
dispatcher. Android selected-app changes add one deduplicated count-only event;
the remote mirror and independent platform validator accept only integer
`selected_app_count=0..128` on the exact Android routing terminal event.
Package names and selected-app lists remain device-local. Persistence is an
additive nullable column, and the operator projection exposes only event and
count totals.

Platform schema/ingest/migration/operator/handoff regression passes `118/118`.
Client producer, contract and runtime/privacy tests pass `29/29`; support
polling/encrypted outbox passes `7/7`; focused repair paths pass `4/4`; the
app-shell analyzer and platform/client/Core hash parity pass. The event-schema
hash is now
`24ae72442f778d7f1334ae0a4bf4d774738e4de275707b29420ec733af65cc17`.

`OBS/OBS-029`, `OBS_PB/PB-02`, `PB-10`, `PB-12`, `PB-13`, and
`FE_PR/PR-08` reach local `I3`. `OBS_DOD/DOD-08` reaches only `I1`: the
Windows sanitized journal is baselined, Linux remains not shipped, and no
current native rebuild was credited. `PB-14` stays `I2` pending a single
signed-manifest health-breach promotion-stop proof. Distribution becomes
`I3=286`, `I2=28`, `I1=46`, `I0=17`; 91 rows remain below `I3`. No candidate,
device proof, deployment, publication or promotion occurred.

## 2026-08-22 — WO-006K signed temporary support mode

The support pipeline now has a closed temporary-mode lifecycle instead of
signature primitives without an owner. L2 issues one case-bound Action Intent;
the platform stores only the activation-code hash, and the authenticated owner
can redeem the exact platform/app/build code once for an Ed25519-signed v2
policy. The client independently verifies it, asks for explicit confirmation,
persists nonce/usage state, exposes a root-level indicator and fails closed on
replay, corruption, expiry or cumulative caps. The policy has no command,
VPN/route/DNS mutation, arbitrary-file, packet/destination or self-extension
surface.

Ordinary diagnostics now expose the cross-language `PSD1-*` short code without
upload. Manual Android/Windows export resolves the same verified recipient as
upload and gives the host only the encrypted `.pokrov-support` envelope;
Android uses bounded SAF validation and Windows the system save dialog.

Platform support tests pass `12/12`; the client support-bundle package passes
`15/15`, the full app-shell suite `384/384`, Android host contract/debug build
and Windows `21/21` plus debug build all pass. `OBS-070..074` advance
`I1 -> I3`. Distribution becomes `I3=291`, `I2=28`, `I1=41`, `I0=17`; 86
rows remain below `I3`, and the stage split becomes `16/32/17/21`.
Candidate preflight remains honestly blocked with no candidate created. No
production key custody, device/clean-host proof, deployment, publication or
promotion occurred.

## 2026-08-22 — WO-009H generated Admin API v2 contract

The live modular `/api/admin/v2/*` router now produces one deterministic
OpenAPI artifact with exact permission, session-cookie, CSRF and response
metadata for all 73 unique method/path operations. Seventy-one JSON operations
use the strict Pydantic `data/meta/sources/warnings` envelope; governance CSV
and encrypted support-attachment download are the two explicit binary
responses. The generator rejects permission drift, duplicate or unstable
operation IDs and unbounded list/offset parameters.

AdminApp consumes a generated TypeScript operation table with typed
path/query/body input and response-kind metadata. Prebuild rejects generation
drift. The browser additionally rejects an unknown v2 method/path before the
request and rejects a malformed HTTP 2xx envelope before feature code can
display it. Legacy `/api/admin/*` reads stay outside this contract.

Both generation checks, AdminApp lint/build, the complete `59/59` backend
matrix and full `76/76` Playwright suite pass. The negative browser scenario
proves that a malformed success envelope cannot produce false healthy data.
`OC/OC-120` advances `I2 -> I3`. Distribution becomes `I3=292`, `I2=27`,
`I1=41`, `I0=17`; 85 rows remain below `I3`, and the stage split becomes
`15/32/17/21`. No frozen revision, hosted clean check, exact-candidate schema
publication/readback, deployment, server mutation or promotion occurred.

## 2026-08-22 — WO-009I operator role usability and field redaction

The retained admin bridge is now an explicit compatibility boundary instead of
a role-wide legacy-admin grant. It authorizes the resolved HTTP method and
FastAPI route template for user list/card, sensitive investigation, typed
search, promo-slot reads and staged promo-media upload. Every unlisted legacy
route requires `legacy.admin.access` and fails closed for domain roles.

L1 support cannot use e-mail, linked identity, installation/device, key UUID or
panel e-mail as a search oracle. Sensitive user-360 diagnostics, app events,
payment rows and administrator audit are not queried without their matching
permission. Both legacy and v2 projections return explicit field-access state,
and AdminApp renders a permission message rather than treating redaction as an
empty dataset. Key-history operator identity and legacy user commands are also
removed for roles without their audit/legacy capabilities.

Network and payments operators now reach their real domain actions while L3
still requires a fresh step-up in addition to the domain write permission.
Readonly, L1/L2 support and security-auditor roles retain no high-risk command
capability. Existing environment-scoped assignments, expiring JIT/break-glass
grants and governance review remain the role authority.

The full Admin API/contract/command-center/support/manifest backend matrix
passes `75/75`; AdminApp lint/build and deterministic 73-operation generation
pass; the full Playwright matrix passes `77/77`, including the dedicated L1
redaction scenario. Documentation/preflight contracts pass `37/37`.

`OC/OC-110` advances `I2 -> I3`. Distribution becomes `I3=293`, `I2=26`,
`I1=41`, `I0=17`; 84 rows remain below `I3`, and the stage split becomes
`14/32/17/21`. No production IdP/passkey challenge, real operator
assignment/readback, external step-up, frozen exact candidate, deployment,
server mutation, publication or promotion occurred.

## 2026-08-22 — WO-008I product-copy and public-truth consumers

The active client now digest-pins `shared/public-urls.json` beside product,
tariff and commercial contracts. Its generated projection carries full offer,
privacy and official-release URLs; Profile consumes all three, while one shared
copy helper owns fallback trial/Telegram wording. The synchronizer rejects
known production-Dart numeric hardcodes and missing URL consumers.

Web cabinet trial math, economy/API/bot trial and reward constants, referral
friend/referrer/hold values and grandfathered channel handling now bind the
shared product owner. The live Telegram landing and homepage no longer require
a first payment for the Telegram bonus; catalog variables and shared facts
render the canonical no-payment promise. Commercial and account-specific
outcomes remain server authority.

Shared/copy contracts pass `23/23`; backend trial/referral/channel regression
passes `86/86`; bot focus passes `2/2` plus Telegram rich copy `5/5`. Marketing
and WebApp lint/build pass with 35 and 40 static routes. Client projection
check, focused URL widget and analyze pass. The explicit-root seed run proved
cross-repository facts/version/observability/logging/release-v2 contracts, then
stopped because the existing hygiene wrapper treated Git CRLF warnings as
failure; it is not counted as a full PASS.

`FE/P12-129` and `FRKN_ADOPT/ADOPT-07` advance `I2 -> I3`. Distribution becomes
`I3=295`, `I2=24`, `I1=41`, `I0=17`; 82 rows remain below `I3`, and the stage
split becomes `12/32/17/21`. No clean freeze, candidate, device/browser-lab
proof, deployed readback, legal approval, payment, campaign, publication or
promotion occurred.

## 2026-08-22 — WO-006L Windows sanitized-service native proof

The current Windows service already owns the shipped desktop privileged-host
journal: a closed service/Core schema, 512-byte maximum line, 4096-event
bounded asynchronous queue and protected current/previous files capped at
256 KiB each. Its regression forces rotation and rejects changed field counts,
unknown wire versions, profile material, session tokens, operation nonces and
endpoint material.

The first current MSVC configure exposed a real CMake defect: `/wd"4100"` was
escaped by Ninja and rejected by `cl.exe` as `D8021` before compilation. The
root Windows CMake owner now passes `/wd4100`. Visual Studio 2022 Build Tools
17.12.2, MSVC 19.42.34435, Windows SDK 10.0.22621.0 and Ninja then built the
service plus all native tests in Debug. Six service CTests pass `6/6`; the
complete native set including runner activation passes `7/7`; an immediate
rebuild reports no work.

`OBS_DOD/DOD-08` advances `I1 -> I3`. Linux remains explicitly
`NOT_SHIPPED_IN_1.2.0`, so no speculative Linux daemon or second logging owner
was added. Distribution becomes `I3=296`, `I2=24`, `I1=40`, `I0=17`; 81 rows
remain below `I3`, and the stage split becomes `11/32/17/21`. No service
installation, SCM/network mutation, clean-host run, exact candidate, trusted
signing, publication or promotion occurred.

## 2026-08-22 — WO-013A3 PB-14 candidate-stage correction

`OBS_PB/PB-14` no longer uses the fail-safe default `pre_freeze` stage. Its
remaining acceptance condition binds a signed-manifest cohort to an observed
health breach and proves promotion stop or rollback for one exact candidate;
requiring that evidence before candidate creation was circular. One exact
`PB-14 -> candidate` override is now machine-pinned, while the default remains
`pre_freeze` and all other remaining source gaps retain their current stage.

Focused preflight regression passes `9/9`. The explicit-root live preflight is
still expected `BLOCKED` with seven blockers and no candidate. The ledger does
not advance: distribution remains `I3=296`, `I2=24`, `I1=40`, `I0=17` and 81
rows remain below `I3`; only the pending stage split changes from `11/32/17/21`
to `10/33/17/21`. No signed manifest, cohort, health breach, rollback,
deployment, publication or promotion occurred.

## 2026-08-22 — WO-008J product-facts whole-client gate

The active-client facts gate now covers the complete local P12-024 boundary.
Seed composition must consume generated trial and Telegram reward values plus
the Android/Windows public and iOS/macOS readiness-only scope. Subscription
plans must parse `plans[].price` from the client API and Profile must render
that returned value. Production app-shell Dart with a currency-tagged numeric
price literal fails the synchronizer, so the client cannot grow a local tariff
fallback or calculator.

Commercial/copy/frontend/shared contracts pass `33/33`; the focused shared
facts suite with new negative price/device tests passes `11/11`; active-client
projection check, device-scope test and server-price parsing test pass. Focused
Ruff and Python compile pass.

`FE/P12-024` advances `I2 -> I3`. Distribution becomes `I3=297`, `I2=23`,
`I1=40`, `I0=17`; 80 rows remain below `I3`, and the stage split becomes
`9/33/17/21`. No exact candidate, physical device, deployed provider/public
readback, payment, campaign, deployment, publication or promotion occurred.

## 2026-08-22 — WO-008K state-aware subscription presentation

The cabinet subscription hero now consumes the canonical server
`access_state` directly. A single presentation policy maps `paid_unlimited`,
`trial_premium`, `bonus_premium`, `free_monthly`, `free_soft_mode` and
`expired_or_blocked` to a state-correct title and primary action. Unknown or
future values normalize to a neutral `Управление доступом` / `Выбрать срок`
presentation instead of inheriting a premium or active-state claim. No local
entitlement, price, offer or provider evaluator was added; the CTA still opens
the existing server-revalidated checkout.

Focused lint passes. The WebApp production build and TypeScript pass. Focused
Playwright proof passes `1/1`, covering all six canonical states plus the
unknown-state guard; the full cabinet and rewards regression passes `68/68`.

`FE/P12-011` advances `I2 -> I3`. Distribution becomes `I3=298`, `I2=22`,
`I1=40`, `I0=17`; 79 rows remain below `I3`, and the stage split becomes
`8/33/17/21`. No exact candidate, deployed server/provider/public-origin
readback, payment, deployment, publication or promotion occurred.

## 2026-08-22 — WO-008L checkout no-waterfall browser proof

`P12-120` is a `portal` row whose source acceptance criterion is “no
unnecessary waterfall”; it does not require an active-client data path. The
cabinet already starts catalog and provider capability requests together, and
public checkout starts catalog, provider capability and acquisition handoff
together. Offer preview remains correctly dependent on a verified catalog and
selected plan.

The local gates now prove runtime ordering instead of only matching
`Promise.allSettled` source text. Each browser probe holds the first responses
open and requires every independent request to arrive before releasing any of
them. Cabinet proves `2/2`; public checkout proves `3/3`; both also enforce a
sub-500 ms start spread. WebApp focused proof passes `1/1`, the complete
cabinet/rewards suite and production build pass `69/69`, and marketing lint,
production build, responsive/no-JS/reduced-motion/a11y plus the new checkout
concurrency gate pass.

`FE/P12-120` advances `I2 -> I3`. Distribution becomes `I3=299`, `I2=21`,
`I1=40`, `I0=17`; 78 rows remain below `I3`, and the stage split becomes
`7/33/17/21`. No exact candidate, deployed-origin timing, provider/public
readback, payment, deployment, publication or promotion occurred.

## 2026-08-22 — WO-013C explicit Linux and Android OEM limitations

The structured known-limitations owner now identifies `1.2.0` as its working
target and adds two exact boundaries. Linux is
`NOT_SHIPPED_IN_1.2.0`: transitive Flutter desktop dependencies,
compatibility-client instructions, dormant error codes and PB-09 do not create
an official binary, daemon, package, support matrix or availability promise.
Android OEM battery/background policy, VPN-permission handling, notification
delivery and cached Quick Settings state may stop or delay recovery; no
uninterrupted cross-OEM background claim is allowed.

Both canonical platform mirrors and the active-client product/cutover owners
carry the same limits. The Android boundary is machine-linked to PB-08 and
`AND-BG-001/002/003` plus `AND-VPN-004`; Linux is linked to PB-09
`notShipped` and exposes no runtime action. Platform canon/limitations tests
pass `31/31`; focused observability/limitation contracts pass `21/21`; client
docs contract passes and the exact Problem Book runtime test passes `7/7`.

`REL_DOD/DOD-17` advances `I0 -> I3`. Distribution becomes `I3=300`,
`I2=21`, `I1=40`, `I0=16`; 77 rows remain below `I3`, and the stage split
becomes `6/33/17/21`. Exact-candidate release notes and the physical Android
OEM matrix remain required for `I4`. No candidate, device run, deployment,
publication or promotion occurred.

## 2026-08-22 — WO-013D reversible stable pointer and rollback catalog

The active-client release lane now owns a machine-readable rollback catalog.
Its current retained target binds `1.1.6+20260819` to the exact versioned
Android/Windows handoff by identity and SHA-256; `1.2.0` is intentionally absent
until an exact candidate exists. Versioned handoffs remain immutable and no
retained artifact changed during implementation.

The pointer switcher is read-only by default. Apply requires an explicit
expected current release, cataloged target, same-filesystem external backup,
non-overwriting receipt and exact readback. The actual retained pointer
validates against its target, while an isolated fixture proves dry-run,
optimistic-lock rejection, atomic A→B switch, exact backup and byte-identical
B→A rollback. The standard cross-repository client seed gate, client docs and
repository hygiene contracts, platform docs contracts and context audit pass.
The client presentation guard exposed an unrelated 30th `part`; the pure
`ruDays` helper is now a normal exported library and the guarded count is 29.

`FE/P12-130` advances `I0 -> I3`. Distribution becomes `I3=301`, `I2=21`,
`I1=40`, `I0=15`; 76 rows remain below `I3`, and the stage split becomes
`5/33/17/21`. `REL_DOD/DOD-18` remains `I0`: no exact candidate, real pointer,
portal/runtime configuration, deployed surface, origin, publication or
promotion was mutated or proved.

## 2026-08-22 — WO-009J operator OIDC identity and step-up

Operator Center now uses Telegram OIDC Authorization Code plus PKCE as its
primary local identity contract. The browser receives a signed public state
without the verifier; the verifier and matching nonce, purpose and redirect
are held in a short-lived dedicated `__Host` HttpOnly transaction cookie
signed with the operator-session secret. Login and step-up use distinct
purposes and the finish endpoint rejects cross-purpose, cross-cookie and
cross-identity attempts before issuing or strengthening a session.

OIDC login never creates an operator or grants a role. It accepts only an
existing active operator linked to the verified Telegram subject with an
active assignment in the requested environment. Existing opaque HttpOnly
session, CSRF, idle/absolute expiry, inventory/revoke, logout and audit owners
remain unchanged. The compatibility Mini App bootstrap and empty-body step-up
are retained behind one explicit cutover flag; when disabled, both fail
closed. AdminApp starts OIDC explicitly, removes callback code/state from the
URL before exchange, and can recover a high-risk action through same-identity
OIDC step-up.

Focused backend, OpenAPI and manifest regression passes `64/64`. The generated
Admin API contract passes with 75 operations and semantic digest
`beebbea12e3c5168d0bb54cd96e752aeebf7768df15f5194d5f22bb94669531c`.
AdminApp lint and production build pass with 30 static pages; the complete
Playwright matrix passes `78/78`.

`OC/OC-100` advances `I2 -> I3`. Distribution becomes `I3=302`, `I2=20`,
`I1=40`, `I0=15`; 75 rows remain below `I3`, and the stage split becomes
`4/33/17/21`. No live BotFather registration, production IdP exchange, real
operator migration, exact candidate, deployment, server mutation,
publication or promotion occurred. Exact-candidate proof still requires
legacy disablement plus authenticated login, step-up, session inventory,
logout and retained audit readback.

## 2026-08-22 — WO-008M subscription and checkout aggregate

The five source-plan `PR-05` concerns now have one current local proof without
creating another price, payment or entitlement authority. Cabinet maps every
canonical access state and fails future states to a neutral action. Cabinet
and marketing consume the server catalog, ordered provider capabilities and
signed offer only; locked order creation revalidates price, revision, terms,
capacity, subject and idempotency before provider I/O.

The identity-free return capability stays in versioned session storage rather
than redirect URLs. The token-only no-store endpoint maps durable order and
hold truth to the closed processing/paid/failed/cancelled/manual-review/expired
contract. Cabinet additionally refreshes authenticated access before claiming
a paid entitlement and gives paid/access-stale an explicit refresh/support
path. Active Android/Windows Profile renders the server subscription/plan and
opens the bounded web checkout; it has no price or payment evaluator.

Payment analytics are diagnostics only: bounded checkout-start telemetry and
pay-attempt counts feed abandoned-funnel analysis, while signed callbacks and
external orders remain accounting truth. The current aggregate regression
passes backend `30/30`, active-client focused `2/2`, WebApp production build
with 40 routes and cabinet/rewards Playwright `69/69`, plus marketing lint,
SEO, production/responsive/no-JS/reduced-motion/browser checks.

`FE_PR/PR-05` advances `I2 -> I3`. Distribution becomes `I3=303`, `I2=19`,
`I1=40`, `I0=15`; 74 rows remain below `I3`, and the stage split becomes
`3/33/17/21`. `FE/P12-012..014` and `MKT/MKT-600` keep their current `I2`
ceilings because deployed provider, public readback, PostgreSQL concurrency
and atomic exact-candidate deployment are not local facts. No provider call,
payment, deployment, publication or promotion occurred.

## 2026-08-23 — WO-013H clean source freeze

Platform, active Android/Windows client and Core now have exact clean local
source identities: platform
`1ac65cb501a4f3866d2515855b7d168b88b99a25`, client
`551c6e1fb9977560fc2660d4562e08fe69a89742` and Core
`fcb3c8bbc6efdeed284417369aacb522722ebfa2`. No push or promotion-branch
mutation occurred.

Core passes its full gate with pinned Go 1.25.13. The client passes its full
standard gate and exact cross-repository seed validation. The platform
canonical release matrix passes `674/674` plus 38 subtests; dependency,
75-operation Admin API v2 OpenAPI/SDK, context, docs/preflight, compileall,
WebApp/Marketing/AdminApp local quality and diff checks pass. The platform
change manifest covers 502 files at
`3c081ee259b0d9d2dc93ecbfcef6835145cb1684e594430f6000415c017558d2`.
An unbounded repository-wide pytest diagnostic stopped at 6% is explicitly
`NOT_CREDITED_OVERSCOPED_ABORTED` and contributes no PASS claim.

The clean read-only preflight is expected `BLOCKED` with five blockers and
`candidate_created=false`: missing public release index, stale client/Core seed
binding, pending Core replacement artifact, three local pre-freeze rows and
three external pre-candidate rows. The dirty-worktree blocker is closed.

No row advances. Distribution remains `I3=303`, `I2=19`, `I1=40`, `I0=15`;
74 rows remain below `I3` and the stage split remains `3/33/17/21`.
`REL/TEST-001`, `REL/REPO-001` and `FE_PR/PR-00` remain `I2` because hosted
Ubuntu, the separate public index and isolated no-visible-UI PR proof are still
absent. No candidate artifact, trusted signature, device/VM run, provider call,
payment, deployment, publication, campaign, RU-origin proof or promotion
occurred.

## 2026-08-23 — WO-013I reproducible Core 1.1.0 artifact binding

Core revision `fcb3c8bbc6efdeed284417369aacb522722ebfa2` now produces
byte-identical Android and Windows trees across two credited local builds. The
Android AAR is 107,317,530 bytes at
`26a7b9ebcf05065b33cc40848147a66db5172a9655cb9c77a839fa685145bf93`;
the Windows DLL is 55,352,320 bytes at
`10ee475d04417c4317221a85ca4b043a7489294d654fc4ce7a64ec56dcdcdbff`;
and libcronet remains 8,596,992 bytes at
`8ef1f8bbde77f954af1ae47bee1819ac8dc2354bb0e1d4baba3dad9e58d7a6f7`.
The AAR contains four ABIs, the DLL has all 15 required exports, and the exact
Windows Core passes 100 proxy-only start/stop cycles. That backtest does not
claim TUN, DNS, route or leak protection.

Client commit `336d5454d47fa33d08b7a6bae79b7980cc6b11b4` binds those exact
bytes, Core SHA, reproducibility trees, SBOM identities and
candidate/promotion=false state. Its full standard gate and cross-repository
seed validation pass. The platform preflight at
`7a15ba2bd5d17617aca28205cd448b6c917929ab` now independently hashes the
three tracked runtime files and fails closed on metadata, source, evidence,
size or byte drift; focused regression passes `12/12`.

The clean read-only preflight is still expected `BLOCKED`, but the stale-seed
and pending-Core-artifact blockers are closed. Three blockers remain: missing
public release index, three local pre-freeze rows and three external
pre-candidate rows. No row advances. Distribution remains `I3=303`, `I2=19`,
`I1=40`, `I0=15`; 74 rows remain below `I3`, and the stage split remains
`3/33/17/21`.

The artifacts are unsigned `PRE_CANDIDATE_LOCAL` inputs. SBOM warnings are not
legal clearance. No push, release tag, hosted CI, trusted signing, physical
device/clean VM, current/brain/RU-origin run, public index, deployment,
publication or promotion occurred.

## 2026-08-23 — WO-013J fail-closed public release-index contract

The actual public `Kiwunaka/pokrov` baseline is now inspected rather than
labelled unavailable. Public `origin/main` is the single unsigned commit
`d0bf8e8c70ebeaa241f4c8f5b8a4452fd339ed15`; release tags are lightweight.
The retained 1.1.6 release has eight GitHub-digested assets and matching
`SHA256SUMS.txt`, but no detached manifest signature, source/SBOM/provenance
binding or Windows publisher signature. Its Windows manifest also contains
local build paths. It is explicitly legacy checksum-only evidence, not a
candidate-eligible trust surface.

Isolated release-index commit
`f07654af496d042fa8dba3d8b2695e987c8e9eb7` implements the missing source
contract: strict manifest schema, exact cross-repository revisions and contract
hashes, trusted artifact signer/SBOM/provenance fields, GitHub digest parity,
raw exact-byte Ed25519 detached signatures, same-byte/no-rebuild promotion,
pinned dependencies and pinned-action CI. Repo-local source validation and
`2/2` tests pass, including one-byte signature mutation rejection.

The keyring is intentionally empty and `--require-ready` fails as expected.
The local commit is not published. Platform preflight now fails closed on
missing/invalid contracts, schema drift, missing trusted key, wrong remote and
unpublished revision. Clean preflight remains `BLOCKED` with four blockers:
unpublished release-index revision, missing owner signing key, three local
pre-freeze rows and three external pre-candidate rows.

`FE/P12-023` advances `I1 -> I2`; its trust-surface implementation exists
locally but has no public/owner-key/candidate proof. `REL/REPO-001` remains
`I2`. Distribution becomes `I3=303`, `I2=20`, `I1=39`, `I0=15`; 74 rows
remain below `I3`, and stage split remains `3/33/17/21`.

Hosted client runs remain absent. Platform/client branch-protection readback is
blocked by the private-repository plan and Core main is unprotected. No owner
key, release-index push/PR, candidate, signature, deployment, publication or
promotion was created.

## 2026-08-23 — WO-013K corrected release-base PR-00 result

The first local-parent proof at `dcfbbce...` is withdrawn: although it changed
four files over local parent `9567299...`, its actual diff to `origin/master`
contained 514 paths and 121 visible UI paths. It was not PR-00-ready.

Corrected branch `codex/1.2.0-pr00-true` starts directly at the source plan's
real platform base `280ed9157f5804d4bc719cb8d6cab471caafb937` and contains
one commit, `1632234bb78d18b09fa83cd02249d27859b1c409`. Its actual promotion
diff contains nine allowlisted contract/snapshot/validator/test/workflow paths
and zero AdminApp, Marketing, WebApp or legacy portal UI paths.

The corrected validator result is
`PASS_RELEASE_BASE_ISOLATED_NO_VISIBLE_UI`: target and merge base are exact,
four Git-blob snapshots match size/SHA-256 and semantic checks, changed paths
are exactly `9/9`, and candidate/promotion flags remain false. Focused tests
pass `3/3`; Ruff check/format and scoped diff check pass. The 1,034-byte
validator JSON has SHA-256
`4098f52226694f15787620954b59435a73e89839ef07e338f1ffa0f20eab6a31`.

`FE_PR/PR-00` remains `I2`: branch push, hosted PR, review and required checks
are `NOT_RUN` and were not authorized. Distribution remains `I3=303`,
`I2=20`, `I1=39`, `I0=15`; 74 rows remain below `I3`, and the stage split
remains `3/33/17/21`. No candidate, key, signature, public-index publication,
device/origin run, deployment or promotion occurred.

## 2026-08-23 — WO-013L exact hosted client gate control

Release-base-isolated branch `codex/1.2.0-hosted-gate-control` starts at actual
platform promotion revision `280ed9157f5804d4bc719cb8d6cab471caafb937`
and contains one commit,
`085ac1ae49eea71f60209d70438fbb8f404b53af`. Its promotion diff contains five
allowlisted workflow/contract/validator/test/handoff paths and zero visible UI
paths.

The control binds platform `30859e115859386f5dd51210b5697af5440c36df`,
client `8c6b955dced3b018825c53fe5d14cb632271adeb` and Core
`fcb3c8bbc6efdeed284417369aacb522722ebfa2`. The pinned Ubuntu 24.04 workflow
verifies all checked-out HEADs, then runs the client's cross-repository seed
validation and complete standard entrypoint with Python 3.12, Java 17 and
Flutter 3.38.5. Local validator, `4/4` tests, Ruff check/format and diff check
pass. The 828-byte validator JSON has SHA-256
`8fbd975ca969a42246bd6da822d2d5ea4a0fb5506c4ebc6d296e3c9e27725a00`.

`REL/TEST-001` remains `I2`. Exact source publication, the owner-created
least-privilege `POKROV_RELEASE_REPO_READ_TOKEN`, branch push/PR, hosted run and
review are absent and were not authorized. Distribution remains `I3=303`,
`I2=20`, `I1=39`, `I0=15`; 74 rows remain below `I3`, and the stage split
remains `3/33/17/21`. No credential, candidate, signature, public-index
publication, device/origin run, deployment or promotion was created.

## 2026-08-23 — WO-013M full branch-policy STOP-SHIP gate

Platform commit `dfa96eb7e1139d7f41833f3cc70fb1b57b12c15e` replaces the
partial live branch audit with a full fail-closed policy check. A branch no
longer passes merely because strict check names exist: every required check
must be app-bound, and the policy must also enforce non-author/Code
Owner/last-push review, stale dismissal, admins, signed commits, linear
history, conversation resolution and force-push/deletion bans. Live
`.github/CODEOWNERS` must cover both the repository root and its own control
surface.

The clean read-only run binds client `8c6b955...` and Core `fcb3c8b...`. All
seven permanent source anchors pass, but the live aggregate is `NO_GO`:
platform/client protection is `BLOCKED_BY_ACCESS`, Core main is
`FAIL_UNPROTECTED`, WIN-003 is `NOT_RUN`, and all three repositories have zero
eligible non-author reviewers. No Code Owner is selected, so every reviewer
control is `BLOCKED_BY_OWNER_DECISION`. The 6,198-byte report has SHA-256
`b49fff4235a5a7030e88aa209c595826d4f8ce6c0d9c5c5de99a6d94dd7981a8`;
focused tests pass `13/13` and Ruff/script-manifest/diff checks pass.

`REL/REL-001` and `REL_DOD/DOD-09` remain `I1`; a stronger verifier is not a
remote setting. Distribution remains `I3=303`, `I2=20`, `I1=39`, `I0=15`; 74
rows remain below `I3`, and the stage split remains `3/33/17/21`. No
collaborator invitation, plan/visibility change, CODEOWNERS guess, branch
mutation, push, PR, candidate, signature, deployment or promotion occurred.

## 2026-08-23 — WO-013N authorized public and hosted pre-freeze closure

Owner authorization permitted scoped Git pushes, PRs, Actions secrets and
narrow evidence-only merges. Public `Kiwunaka/pokrov` PR 1 published the v2
source contract and Ed25519 trust root, then merged main as
`491436889ef911de868d704e68ba86e77102b0f1`. Post-merge run `32616614043`, job
`97138291041`, and exact public main readback passed. Private signing material
is secret-only under `POKROV_RELEASE_SIGNING_KEY_PEM`; no candidate manifest is
signed.

Platform PR 18 at `e26fcb0...` passed exact release-base isolation and
Guardrails with ten allowlisted freeze/contracts paths and zero visible UI
paths, then merged as `8cef00a...`. Three-path retained-workflow follow-up PR
19 passed Guardrails and merged as `a25fa8a...`. The absence of a non-author
review remains a separate branch-policy blocker rather than being relabelled a
pass.

Open PR 17 control `75a5c4f82c963d81f1c46dcf26a83cf39b8021cf`
checked out exact platform `9b9467c...`, client `66d82be...` and artifact-bound
Core `fcb3c8b...` with the read-only client deploy-key secret. Hosted run
`32621490357`, job `97150195041`, passed SHA verification, cross-repository
seed validation, App Shell `385/385`, runtime `59/59` plus one intentional
skip, Android `8/8`, Windows `21/21` and Android Gradle `BUILD SUCCESSFUL`.
Guardrails run `32621490362` also passed. Retained run `32620758845` remains a
cancelled-after-failure disk-exhaustion diagnostic, not a pass.

`REL/TEST-001`, `REL/REPO-001` and `FE_PR/PR-00` advance `I2 -> I3`.
Distribution becomes `I3=306`, `I2=17`, `I1=39`, `I0=15`; 71 rows remain
below `I3`, and the stage split becomes `0/33/17/21`. Candidate creation is
still blocked by three external pre-candidate rows: branch policy/reviewer
rows `REL/REL-001` and `REL_DOD/DOD-09`, plus `FE/P12-023` because the frozen
public trust revision lacks eligible non-author review. Signed exact-candidate
assets and detached public readback remain later `I4` proof. No candidate,
production deploy, device/origin claim, payment action, campaign or promotion
occurred.

## 2026-08-23 — WO-013O owner-solo promotion control

The sole repository owner explicitly authorized `OWNER_SOLO_EXCEPTION` for
release 1.2.0. The gate records `independent_review_performed=false`; it does
not invent a second approval. Non-author review, non-author CODEOWNERS and the
unavailable paid private-protection feature are waived only for this release.

The compensating control binds an owner-authored PR to its exact 40-hex head
and reads every named successful GitHub App check. Wrong owner/base/head,
closed-unmerged PR, missing/failed check or missing app binding fails closed.
PR-only promotion, signed public index, retained candidate evidence and
same-byte promotion remain mandatory.

Public `Kiwunaka/pokrov-core:main` now passes the solo-safe live policy: five
strict checks are bound to GitHub Actions app `15368`; admins, signatures,
linear history and conversation resolution are enforced; force pushes and
deletion are disabled. Platform/client remain `BLOCKED_BY_ACCESS` on the
private plan and require exact PR/check compensation.

The clean read-only run binds platform `2708bf6...`, client `66d82be...` and
Core `0e6b020...`. All seven local anchors pass, all reviewer controls report
`OWNER_SOLO_EXCEPTION`, Core protection passes, and the aggregate is honestly
`BLOCKED` because three exact PR controls plus WIN-003 remain `NOT_RUN`. The
7,905-byte report SHA-256 is
`1a8ef3e2cd3b7aeb82cc4337aadc3b930a737781e4c37afe4f1d9b19f7541546`.

`FE/P12-023` advances `I2 -> I3`: its public trust root, hosted source check and
exact readback were already proved, and the explicit owner exception resolves
the only missing review precondition without claiming independent review.
`REL/REL-001` and `REL_DOD/DOD-09` remain `I1` until exact final PR evidence
passes.

Distribution becomes `I3=307`, `I2=16`, `I1=39`, `I0=15`; 70 rows remain
below `I3`, and the stage split becomes `0/33/16/21`. Candidate assembly may
proceed, but no candidate, signature, production deploy, device/origin claim,
payment action, campaign or stable promotion occurred.

## 2026-08-23 — WO-013P final source promotion

The final 1.2.0 source tuple was promoted through exact owner-authored PRs under
the authorized `OWNER_SOLO_EXCEPTION`, with
`independent_review_performed=false` retained. Platform PR 20 head
`672a245aac1481220d118463a3b65b7d63275790` passed `repo-guardrails` run
`32654545629` and `cross-repository-contract` run `32654545639`, then merged
as signed platform `master`
`2ed944c5eaa667c44a7bc1970d2dd175ff34f8c9`. Its post-merge guard run
`32655166506` and cross-repository run `32655166477`, attempt 2, pass.

Client PR 10 head `4864e439126263296a68ea8c1ba213f25c57a5fb` passed the
full hosted gate in run `32655837199`, job `97234316532`, and merged as signed
client `main` `3904734ce7761cc92c4136f1eaf13e20f2354f72` with the exact same
Git tree. Client main run `32656692926`, job `97236406043`, repeats the
cross-repository contract, complete standard client gate and both Android
flavors successfully. Earlier run `32652910014` remains an `INFRA_FAILURE`
from GitHub runner disk exhaustion, not a test failure or a pass.

Core PR 2 head `0e6b0204d764ae6b1d726343f487a7004d13393b` passed all five required
jobs in run `32619396382` and merged as signed Core `main`
`bdbd97fae35103e705f55908caebf75b4a9ff72f` with the exact same Git tree.
Core main run `32651975372` passes all five jobs again. That final source
produces locally byte-identical Android and Windows builds. Final client main
embeds AAR SHA-256
`83a5bd740774a2a16117f0c242c3ada4bcbb22a65255c3ee008a751e681c06f0`,
Core DLL SHA-256
`ef9672b3ba9983012bfa78abd2e4cd8ef5ef65d8e4b6a49ff89f8c4d0d575040`
and Cronet SHA-256
`8ef1f8bbde77f954af1ae47bee1819ac8dc2354bb0e1d4baba3dad9e58d7a6f7`.
Hosted Linux Android reproducibility is retained separately and is not
misstated as byte-identical to the Windows-produced embedded AAR.

The final clean live gate binds the three merge commits, passes all seven
source regression anchors and all three exact owner-solo PR controls. It
remains correctly `BLOCKED` because exact-candidate Windows 10/11 clean-host
TUN, DNS, egress and rollback evidence is `NOT_RUN`; `candidate_proven=false`.
The 8,248-byte report SHA-256 is
`71512121d6c9b0ccd9c73423056a14707e11a1db7a2027ca851ad04130927109`.
Three earlier transient API readbacks remained fail-closed and were not
partially credited.

`REL/REL-001` and `REL_DOD/DOD-09` advance `I1 -> I3`. Distribution becomes
`I3=309`, `I2=16`, `I1=37`, `I0=15`; 68 rows remain below `I3`, and the stage
split becomes `0/33/14/21`. Source promotion is complete, but no candidate,
signature, physical-device/clean-host or origin proof, provider action,
production deploy, payment, campaign or stable promotion occurred.

## 2026-08-23 — WO-013Q exact local pre-candidate assembly

The frozen 013P tuple now produces six retained local app artifacts. Four APKs
and the store AAB use the production Android signer; the Windows service-first
installer passes the complete local gate and package checks but Authenticode is
`NotSigned`. The six-file set digest is
`6a89748d26f84da3bef8ecae3bd5fd897747a74bae02311be8028224d4649964`.
CycloneDX 1.5 SBOM, SLSA v1 provenance, final checksums and strict-v2 handoff
are retained.

Preflight tooling now separates frozen platform source from the post-freeze
evidence ledger and records both clean revisions. Focused release regressions
pass `58/58` plus 21 subtests. The final run binds platform `2ed944c...`, client
`3904734...`, Core `bdbd97f...`, public index `4914368...`, ledger `2522bf0...`
and tool `08dc6a9...`; it returns `READY_LOCAL_FREEZE` with zero blockers and
zero pre-candidate rows below `I3`.

This is `PRE_CANDIDATE_LOCAL`, not an RC. Trusted Windows signing and the
support-mode verification key are missing; applying them changes artifact
bytes and requires a regenerated handoff. The strict handoff retains 12
required promotion gates below `PASS`. No public release, store publication,
device/VM or origin proof, provider action, deployment or promotion occurred.

`REL_DOD/DOD-15` advances `I0 -> I2`. Distribution becomes `I3=309`, `I2=17`,
`I1=37`, `I0=14`; 68 rows remain below `I3`, and stage split remains
`0/33/14/21`.
