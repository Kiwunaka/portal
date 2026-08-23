# WO-006 — Observability, Diagnostics And Support Evidence

Status: `COMPLETE_I3`
Classification: `ACTIVE_EXECUTION`
Phase: `04`
Lanes: platform contracts/backend, active client, Core compatibility; Operator
Center presentation is coordinated with WO-009

## Bounded outcome

Build one privacy-bounded causal evidence path for user-impacting failures:

```text
client intent/reducer
  -> native host or privileged service
  -> Core
  -> portal request/job
  -> redacted local timeline
  -> explicit user preview/consent
  -> encrypted support bundle
  -> short-lived case-bound upload
  -> isolated ingest
  -> L1 summary / L2 audited access
```

The result must answer which phase failed, with which stable reason code and
which verified proof was missing, without collecting browsing destinations,
raw network material, credentials, private messages, package names or raw
identity.

This WO authorizes local source, schemas, migrations, tests and canonical
documentation. It does not authorize production telemetry enablement, remote
support mode, object-storage provisioning, production retention deletion,
bundle upload, operator access, deploy, alert delivery or exact-candidate
overhead/crash claims.

## Input classification and reconciliation

`POKROV_release_1.2.0_full_audit_with_client_logging_RU.md` is design/audit
input, not executable authority. Its sections 23–38 supply the four data modes,
event fields, error families, redaction rules, bundle shape and ingest threat
model. The frontend and Operator Center audits supply the preview/recovery and
L1/L2 presentation requirements. `frkn-org.md` contributes only the lesson to
prefer preview, consent, redaction and ticket history over raw power-user logs;
its observed product behavior and configuration are not imported.

Current repository authority changes the proposed design in two important
ways:

- the platform already owns first-party product `Event Envelope V1`; it remains
  the bounded aggregate telemetry envelope and does not become a transport for
  local operational logs or bundles;
- the client already has a small desktop lifecycle JSONL journal, Android typed
  state, Windows privileged breadcrumbs and a shallow support diagnostics
  preview. These are migration inputs, not parallel permanent contracts.

The new operational observability contract is separate from product analytics.
Only an explicit allowlisted aggregate projection may enter Event Envelope V1.
Payment/access authority remains provider callbacks and entitlement ledgers.

## Non-negotiable data modes

1. `local_operational`: always-on, low-volume, device-local, bounded structured
   lifecycle and recovery evidence.
2. `aggregate_release_health`: minimal first-party counters/results by build,
   platform and closed code; no destinations, raw stack, account or install
   identity.
3. `user_support_bundle`: deterministic redacted encrypted evidence generated
   only after preview and explicit consent.
4. `server_security_audit`: mandatory auth/payment/admin/support/release audit
   records, never reused as product analytics.

Temporary `support_mode` is a signed-policy extension of local collection, not
a fifth data mode. It is visible, opt-in, TTL <= 30 minutes and volume-bounded;
it cannot enable packet capture, arbitrary destination tests, heap dumps or raw
configuration.

## Global invariants

- All events use a versioned closed schema and a stable error catalog. Unknown
  versions, fields, codes and enum values fail closed or enter a bounded local
  quarantine; they are never serialized as free-form metadata.
- `installation`, `boot`, `session`, `attempt`, `operation`, `trace` and
  `support_case` identifiers are opaque, bounded and scoped. A support case ID
  exists only after an explicit support action.
- Generation and monotonic sequence fence late callbacks. Occurrence and
  receive timestamps remain distinct; ordering-sensitive transitions are not
  deduplicated away.
- Logging calls never accept raw errors, request/response bodies, URLs,
  destinations, profiles, tokens, cookies, authorization headers, provider
  payloads, arbitrary file paths or arbitrary metadata maps.
- Sensitive wrapper types (`Credential`, `SecretString`, `RawConfig` or their
  equivalents) cannot implement the observability value interface.
- Normal operation never relies on Android logcat, Event Viewer, journalctl or
  console output. Debug tooling may mirror already-sanitized events only.
- Producers enqueue without blocking UI, network, Core or privileged mutation.
  Critical rollback/security records use priority flush; queue saturation is
  reported through closed pipeline-health counters.
- Rotation is atomic and bounded. Phase target caps are 24 MiB on Android and
  64 MiB on Windows; the Linux value is inactive because Linux is not shipped.
- A planted-secret or integrity/redaction failure blocks bundle export/upload.
  There is no plaintext ZIP fallback.
- Source/unit proof can reach `I3`. Crash, overhead, signed support policy,
  upload, retention, RBAC and exact release health require their named `I4`
  environment/candidate evidence.

## Ownership and package shape

Platform canonical owners:

```text
shared/contracts/observability/
  observability-event.schema.json
  error-catalog.schema.json
  error-catalog.json
  README.md

portal_bot/
  observability_contracts.py
  observability_ingest.py
  support_bundle_service.py
  support_bundle_worker.py
```

Active client target packages:

```text
packages/observability_contracts/
packages/observability_runtime/
packages/diagnostics_collectors/
packages/support_bundle/
packages/support_upload/
```

Core target seam:

```text
internal/observability/
  event.go
  redaction.go
  catalog.go
  abi.go
```

The platform JSON files are canonical. Client/Core snapshots must declare the
canonical SHA-256 and pass cross-repository equality tests; they cannot fork the
catalog. Release-handoff v2 binds the exact event-schema and catalog hashes.

## Execution graph

```text
006A contracts/catalog/hash binding
  ├─ 006B client queue/sinks/rotation/redaction
  ├─ 006C Core structured ABI + host ingestion
  └─ 006D portal request/correlation + aggregate batch
       |
       v
006E phase instrumentation + crash markers
       |
       v
006F deterministic encrypted bundle + preview
       |
       v
006G case/ticket/upload + isolated ingest
       |
       v
006H retention/health/known issues + L1/L2 read models
```

006H supplies bounded backend/read-model contracts. WO-009 owns final Operator
Center interaction design and legacy-admin cutover.

## WO-006A — Contracts, catalog and release binding

Repositories: platform, active client, Core.

Deliver:

- canonical JSON Schema for operational events with required schema/event
  identity, occurrence time, component/subsystem/stage/name/severity/outcome,
  correlation hierarchy, generation/sequence, build identity, privacy class,
  stable error code and closed allowlisted attributes;
- canonical versioned error catalog covering bootstrap, auth, API, profile,
  Core, TUN, route, DNS, egress, update, Windows service, Android host, crash,
  support and security families;
- validators for schema/catalog structure, unique codes, safe user copy,
  component ownership and forbidden fields/terms;
- exact SHA-256 binding in release-handoff v2 and its client generator;
- `observability_contracts` client package plus Core snapshot/validation seam;
- compatibility note that product Event Envelope V1 receives only an
  allowlisted aggregate projection.

Acceptance:

- malformed/unknown event fields and catalog drift fail tests;
- planted forbidden field names such as authorization, cookie, URL,
  destination, raw config and private key fail validation;
- platform/client/Core compute the same event-schema and catalog hashes;
- v2 candidate metadata cannot validate without both hashes;
- `OBS/OBS-001..004`, `OBS-003`, `OBS-011` and `FE/P12-126` advance only for
  the exact implemented portions.

Rollback: consumers may remain on their old local journals while 006A is
reverted. Release-v2 cannot silently omit hashes after adoption; rollback must
explicitly revert the contract version before candidate creation.

### 006A local closure — 2026-08-21

Status: `COMPLETE_LOCAL_I3`.

Delivered:

- platform-owned closed operational event schema and a versioned catalog of
  117 unique base-1.2.0 codes across all 29 required families;
- offline schema/catalog/event validator with duplicate-key, unknown-field,
  unknown-code, unsafe-public-copy, required-family and planted forbidden-field
  failures;
- mandatory `error-catalog` and `observability-event` descriptors in
  release-handoff v2 JSON Schema and semantic validation, including exact
  canonical byte hashes;
- client generation that rejects caller-supplied observability descriptors and
  derives the two exact hashes from the platform checkout;
- identical checked client/Core snapshots, a typed client package containing
  all catalog codes and attribute keys, and cross-repository drift gates;
- explicit separation from Product Event Envelope V1: only a future reviewed
  aggregate projection may enter product analytics.

Evidence:

- platform observability plus release-handoff tests: `61 passed`;
- platform docs/script/link contracts: `30 passed`, manifest PASS, links PASS;
- client package: `3 passed`; release-handoff generator: `13 cases`; full
  cross-repository `validate-seed.ps1`: PASS;
- Core canonical `scripts/test.ps1`: PASS, including local snapshot validation;
- platform/client/Core exact hashes:
  event schema `3044d28db7e1e047654427bc0c38e5e33e95f2e48ec2c72cbbdf07e01d42ff13`,
  error catalog `515643c151dbc9d801b6cd300e035c4137e6ffa283c26eea705956dc5d3f4a5e`.

Rows advanced: `OBS/OBS-001..004`, `OBS/OBS-011` and `FE/P12-126` to
`I3`; broad `REL/OBS-001` only to `I1`. No runtime producer, remote telemetry,
support bundle, upload, retention, device, hosted CI, signed manifest or exact
candidate claim is made. 006B is active.

## WO-006B — Client runtime bus, sinks and privacy enforcement

Repository: active client.
Dependency: 006A.

Deliver:

- bounded non-blocking queue with priority-aware dropping and observable queue
  depth/drop/flush/rotation health;
- one writer per platform, atomic rotation, partial-record recovery and caps of
  24 MiB Android / 64 MiB Windows;
- safe in-memory breadcrumb ring and separate security/integrity slice;
- typed serializers and field-level privacy class enforcement;
- path/local-identity sanitizer, URL/destination removal and safe config
  fingerprint;
- release source gates against raw `print`, arbitrary `debugPrint`/logcat,
  Authorization/Cookie/body interpolation and unconstrained metadata;
- migration reader for the current desktop JSONL and Windows privileged journal
  that can include only allowlisted translated records in a future bundle.

Acceptance:

- saturation cannot block a simulated connect/stop loop;
- fatal/rollback/security ordering survives lower-priority drops;
- crash-truncated last record is ignored while prior records remain valid;
- volume caps and at-most-two active generations are tested;
- planted-secret corpus has zero serialized matches;
- `OBS/OBS-005..006`, `009..013`, `019`, `021..030` and applicable DoD rows may
  reach local `I3`. Overhead/endurance stays below `I4` without measurements.

### 006B local closure — 2026-08-21

Status: `COMPLETE_LOCAL_I3`.

Delivered:

- pure-Dart `observability_runtime` with a synchronous non-blocking emit path,
  one asynchronous batch writer, bounded event/byte queue, priority eviction,
  generation/sequence fence and observable queue/serialize/write/rotation
  health;
- exact Android 24 MiB and Windows 64 MiB two-segment policies, at-most-two
  active files, atomic pending replacement and recovery that ignores a
  crash-truncated tail while retaining prior complete records;
- closed field/privacy validation, planted-secret serialized guard,
  path/local-identity sanitizers and canonical config fingerprint that never
  returns source material;
- separate bounded breadcrumb and security/fatal rings plus allowlisted readers
  for the prior Dart lifecycle JSONL and Windows privileged event journal;
- mandatory client workspace/bootstrap/test adoption and a release-source gate
  that rejects raw Dart stdout/developer logs, Android Logcat, Windows native
  output and raw exception serialization. Production Android/Dart raw sinks
  were removed; functional runtime state/error handling remains intact.

Evidence:

- package analyze PASS and `13/13` tests, including blocked-writer loops,
  priority saturation, writer failure, planted secrets, rotation and truncated
  records;
- source gate PASS across `121` production files plus four fail-closed negative
  fixtures;
- app-shell `326/326`, runtime-engine `53` plus one declared exact-Core-artifact
  skip, Android-shell `8/8`, Windows-shell `20/20`;
- Android direct and store JVM suites `161/161` each; changed Dart analyzers
  PASS; client seed/docs/cross-repository gates PASS.

Rows advanced to `I3`: `OBS/OBS-005`, `006`, `009`, `010`, `012`, `019`,
`021..028`, `030`, `OBS_DOD/DOD-06` and `DOD-09`. `OBS/OBS-013` remains for
isolated collectors, and `OBS/OBS-029` remains `I0` until a remote aggregate
projection actually exists. No remote telemetry, upload, support bundle,
retention, overhead/endurance, device, hosted, signing or candidate claim is
made. 006C is active.

Phase 11 follow-up: `WO-013B` later closed `OBS/OBS-013` with the isolated
`diagnostics_collectors` package analyzer and full `6/6` focused tests.
`OBS/OBS-029` remains open; this historical slice is otherwise unchanged.

## WO-006C — Core structured observability ABI

Repositories: Core and active client hosts.
Dependency: 006A; integrates with 006B sink.

Deliver:

- versioned callback ABI for closed Core lifecycle/phase/proof/failure events;
- run/attempt/generation/sequence correlation and bounded safe attributes;
- removal or release-build rejection of raw line forwarding;
- host adapters that fence stale callbacks and map only catalog codes;
- debug/support-mode handling for unknown upstream lines only after local
  redaction, never in normal release evidence.

Acceptance:

- ABI descriptor/capability negotiation fails closed on drift;
- raw config, endpoint, IP, domain and credential corpus never crosses ABI;
- reordered/late callback tests preserve the active attempt timeline;
- Core race/vulnerability/build gates cover the new callback path;
- `OBS/OBS-007`, `031..050`, `OBS_DOD/DOD-10` advance only where current code
  and tests exist; hosted artifact/candidate proof stays honest.

### 006C local closure — 2026-08-21

Status: `COMPLETE_LOCAL_I3_WITH_PARTIAL_TAXONOMY`.

Delivered:

- Core-owned `config/core-event-abi.json` and additive descriptor capability:
  desktop ABI remains `2`, event ABI is `1`, and audit-proposed ABI 3 is
  explicitly rejected until a separate binding/compatibility decision exists;
- bounded non-blocking Core emitters for initialize, start, stop and selected
  egress proof, carrying only occurrence time, run/attempt, generation,
  sequence, closed event identity, severity/outcome, catalog code and phase;
- Windows C exports `pokrovCoreSetEventCallback` and
  `pokrovCoreSetEventContext`, plus Android gomobile
  `OperationalEventHandler`/handler/context methods;
- Android and Windows host fences that reject unknown ABI fields, names,
  outcomes/codes, old run/attempt/generation and duplicate/late sequence;
  Android release handling discards arbitrary upstream Core debug lines;
- Windows protected journal support for strict `POKROV_CORE_EVENT_V1` records
  and closed Dart legacy translation without copying raw records;
- release manifest cutover truth: retained Core 1.0.3 hashes remain unchanged
  and explicitly lack structured events; a release 1.2.0 replacement artifact
  is pending and cannot be fabricated from development builds;
- Core security remediation discovered by the new vulnerability gate: Go was
  raised from 1.25.12 to 1.25.13 and both modules now pin at least gRPC 1.82.1,
  CIRCL 1.6.3, `x/crypto` 0.53.0, `x/net` 0.56.0 and `x/text` 0.39.0.
  CI now runs pinned `govulncheck v1.7.0` in addition to vet/race.

Evidence:

- Core canonical `scripts/test.ps1`: PASS after dependency remediation;
- root Core and nested daemon/libbox `go vet`: PASS; `go test -race`: PASS;
- official Go vulnerability database snapshot on 2026-08-21: reachable
  `govulncheck` findings `0` for root supported packages and daemon/libbox;
- current-source Go 1.25.13 Android dev AAR built as
  SHA-256 `8212d1470b1c66ec8949bc24074e953e8cb97a9c12a8ae61ac9cd664a954d9ef`;
  forced direct/store Gradle suites passed and the tracked 1.0.3 AAR was
  restored byte-for-byte as
  `6e6f3b688fe415c9392e19aa4f8660885316897cfc369cfd8c3ff3d01100ee14f`;
- current-source Go 1.25.13 Windows dev DLL built as
  SHA-256 `7f3866faa3ddd7291d9a27320d80fff034c3296f4ec6db8cd907b251f8857800`;
  all 15 contract exports passed inspection and a real callback smoke produced
  correlated initialize `started`/`succeeded` events at sequence 1/2;
- Windows client strict build and native CTest `6/6`; Android direct/store
  suites; runtime-engine `53` plus one declared exact-old-DLL skip;
  observability-runtime `14/14` plus analyzer; full seed/cross-repository/docs
  contract: PASS.

Rows advanced: `OBS/OBS-007`, `OBS/OBS-047..049` and
`OBS_DOD/DOD-10` to `I3`; `OBS/OBS-050` and `REL_DOD/DOD-10` to `I2`.
`REL/CORE-001` remains `I2`: hosted gates, second-build reproducibility, Apple
builds and exact-candidate evidence are not present. `OBS/OBS-037..039`,
`041..046` do not advance from this Core-host slice; Linux remains not shipped
and Android persistence/lifecycle/background/updater/watchdog instrumentation
belongs to later 006E/006F work. No tracked Core artifact, release hash,
signing, promotion, physical-device result or production runtime claim is made.
006D is active.

## WO-006D — Portal correlation and aggregate ingestion

Repository: platform modular monolith.
Dependency: 006A.

Deliver:

- request middleware that accepts only a safe correlation token or creates one,
  returns it on error and propagates it through typed service/job calls;
- exception-to-catalog mapping without raw exception echo;
- bounded idempotent aggregate release-health batch endpoint that accepts only
  Event Envelope V1 projection fields;
- strict event/byte limits, compression limits, authentication/rate controls and
  quarantine counters;
- no body/header/cookie/token logging and no telemetry authority for payment or
  access.

Acceptance:

- unsafe correlation input is replaced and never echoed;
- duplicate event IDs do not inflate aggregates;
- unknown fields/codes, oversize batches, compression bombs and forbidden
  identity/destination metadata fail closed;
- request logs and tests contain no Authorization, Cookie or body values;
- `OBS/OBS-008`, `051..053` and aggregate portions of `OBS_DOD/DOD-21` may reach
  `I3`.

### 006D local closure — 2026-08-21

Status: `COMPLETE_LOCAL_I3_WITH_PARTIAL_END_TO_END_CORRELATION`.

Delivered:

- global request middleware retains only canonical lowercase UUIDv4 client
  correlation, replaces every unsafe value, creates a distinct server UUIDv4,
  binds both in an immutable typed context and returns both response headers on
  success and error; configured CORS exposes the headers;
- unhandled exceptions return catalog code `API-007` and a request ID without
  exception or request-material echo; the aggregate boundary maps validation
  and contract-version failures to `API-008`/`API-009`;
- a fifth modular-monolith route slice owns authenticated
  `POST /api/client/observability/release-health/batches`, while
  `observability_ingest.py` owns closed validation and persistence;
- the endpoint accepts `1..100` identity-free Operational Event Envelope V1
  projections in at most 256 KiB JSON or one 64 KiB gzip member decoded to at
  most 256 KiB. Unknown/duplicate fields, versions, enums, codes, trailing gzip
  members, bombs, identity, destination, package and arbitrary metadata fail
  closed;
- `release_health_events` contains only event/build/platform/outcome/catalog
  dimensions. Unique event UUIDs make identical retry idempotent; reusing an ID
  with a different projection is a `409 event_id_conflict`. Rejections retain
  only bounded `quarantine.<reason>` counters, never payloads;
- SQLite/PostgreSQL additive bootstrap, indexes, separate durable rate scope
  and canonical architecture/API/operations/module-map documentation are in
  place. The path cannot mutate payment, entitlement, incident, compensation
  or support-case state.

Evidence:

- focused release-health/correlation/security/migration matrix: `25/25` PASS;
- isolated owner regression groups: app-first `42/42`, account foundation
  `41/41`, client/portal API `25/25`, and observability/migrations/slices
  `49/49`, for `157/157` PASS;
- docs/context tests `30/30`, link check PASS, script manifest PASS,
  `git diff --check` PASS, Python compile PASS, and Ruff PASS on the new
  standalone ingest/request-context modules and their tests;
- planted payload, unsafe header and unhandled-exception secrets were absent
  from response/log capture; gzip-bomb, duplicate-key, unknown-code,
  forbidden-field and idempotency/conflict cases failed as required.

Rows advanced to `I3`: `OBS/OBS-051..053` and aggregate
`OBS_DOD/DOD-21`. `OBS/OBS-008` advances only to `I2`: the portal accepts and
propagates typed correlation, and the app/host/Core already own their local
hierarchy, but the active client does not yet emit `X-Correlation-ID` on portal
requests or upload aggregate batches. That end-to-end seam belongs to 006E.
No production telemetry enablement, hosted rate/load observation, retention
execution, alert, deploy, client upload, exact candidate or origin proof is
claimed. 006E is active.

## WO-006E — Phase timelines and crash markers

Repositories: active client, Core, platform mappings.
Dependencies: 006B–006D.

Deliver:

- bootstrap and connection reducer spans for profile, Core, TUN, route, DNS,
  egress, verified, rollback and stopped states;
- phase duration/proof outcome plus missing-proof facts;
- stable user-impacting code mapping for every current auth/connect/update
  failure;
- previous-exit/crash marker and next-launch breadcrumb recovery without heap or
  raw stack by default;
- problem-book mapping PB-01..PB-14 to required events, evidence and safe user
  actions. Linux PB-09 remains not shipped.

Acceptance:

- `connected` without current verified proof remains impossible and tested;
- cancellation/supersede/timeout/crash have distinct closed outcomes;
- crash marker has no secrets and cannot become runtime authority;
- every supported problem-book path identifies observed and not-observed phases;
- `OBS/OBS-016..020`, `OBS_DOD/DOD-01..04`, `07`, `09`, and applicable PB rows
  advance only with focused source tests.

### 006E local closure — 2026-08-21

Status: `COMPLETE_LOCAL_I3_WITH_EXACT_CANDIDATE_CRASH_PROOF_PENDING`.

Delivered:

- the Android and Windows entrypoints initialize a bounded local operational
  store before `runApp`, recover a versioned previous-exit marker, install
  sanitized Flutter/platform crash handlers and record bootstrap initialize and
  UI-ready boundaries. Synchronous crash writes contain only a closed crash code,
  a fixed signature and bounded allowlisted breadcrumbs; they never serialize
  the error, stack, heap or runtime state;
- one generation-fenced connection-attempt controller consumes the canonical
  `ConnectionExperienceState` reducer and records profile, Core, TUN, routes,
  DNS, selected-egress proof, verified, rollback and stopped phases. It records
  phase duration and the exact DNS/egress/host proof booleans. A successful
  terminal is emitted only from `ConnectionConnectedVerified`; unverified state
  emits missing-proof facts and cannot become green evidence;
- cancelled, superseded, timeout, failed, crash and successful terminals are
  distinct closed outcomes. A previous-exit marker is diagnostic evidence only
  and cannot replace the current host/service snapshot or privileged recovery
  journal;
- current portal/auth, public runtime-connect and update failure surfaces map to
  the closed catalog. The machine-readable PB-01..PB-14 table binds codes,
  observed events, missing events and safe actions; PB-09 is explicitly
  `notShipped` rather than a fabricated Linux implementation;
- every app-first JSON request carries a canonical UUIDv4
  `X-Correlation-ID`. The release-health mirror writes locally first, strips
  correlation and arbitrary attributes, and best-efforts the identity-free
  projection to the platform batch endpoint only when an existing app session
  is present. It never creates a trial/session for telemetry;
- the client/Core parity check now distinguishes exact clean artifact authority
  from `DEVELOPMENT_REPLACEMENT_PENDING`. The current dirty Core development
  tree is therefore not misreported as proof of the retained 1.0.3 binaries or
  a release 1.2.0 replacement candidate.

Evidence:

- observability runtime `20/20` and analyzer PASS; focused app-shell
  observability/bootstrap `85/85`; complete app-shell `329/329` and analyzer
  PASS;
- Android shell analyzer plus `8/8`, Windows shell analyzer plus `20/20`,
  runtime-engine `53` PASS with one declared exact-old-DLL backtest skip, and
  the canonical client workspace gate PASS;
- canonical workspace gate also passed observability contracts `3/3`, both
  host suites and Android direct/store JVM unit tests (`BUILD SUCCESSFUL`, 145
  tasks);
- seed/cross-repository/docs contract PASS with the Core state reported as
  `DIRTY_DEVELOPMENT_REPLACEMENT_PENDING`; release source logging gate scanned
  130 production files and its four planted negative cases passed;
- platform release-health/correlation plus cross-repository observability
  contract matrix `41/41` PASS. The active client test proves the exact endpoint,
  bearer use, canonical correlation header and absence of correlation from the
  body; unauthenticated delivery does not create a session.

Rows advanced to `I3`: `OBS/OBS-008`, `OBS/OBS-016..020`,
`OBS_DOD/DOD-01..04`, `OBS_DOD/DOD-07`, and PB-01, PB-03..PB-09 and PB-11.
`OBS/OBS-019` and `OBS_DOD/DOD-09` remain `I3` with stronger evidence. PB-02,
PB-10 and PB-12..PB-14 advance only to `I2`: their closed machine mappings
exist, but auth-phase, performance-sample, entitlement-refresh, support-bundle
or release-aggregate producer/consumer paths are owned by later slices and are
not fabricated here. Exact-candidate crash survival, overhead, remote delivery,
hosted observation and production telemetry remain `I4` work. 006F is active.

## WO-006F — Deterministic encrypted support bundle and preview

Repository: active client; platform signed key-set contract only.
Dependencies: 006B, 006C, 006E.

Deliver:

- profiles `summary`, `standard`, `extended`, `crash` with hard category/file/
  byte budgets; extended mode requires visible signed TTL policy;
- deterministic canonical manifest, event slices, system/network summary,
  crash index, redaction report and per-file hashes;
- isolated collectors that cannot enumerate arbitrary files/apps/destinations;
- mandatory planted-secret, traversal, symlink/reparse, race and integrity scan;
- user preview of categories, sizes, removed-field counts, optional categories
  and diagnostic ID before consent;
- encryption to a signed support public key before export; no plaintext ZIP or
  chat attachment fallback.

Acceptance:

- same sanitized input produces the same manifest and hashes;
- forbidden corpus, raw legacy logs and integrity failures block output;
- preview exactly matches encrypted contents/categories;
- cancellation removes only owned temporary material;
- `REL/OBS-001`, `REL_DOD/DOD-12`, `OBS/OBS-014`,
  `OBS_DOD/DOD-11..14`, `FE/P12-112` may reach local `I3`; external-key and
  physical candidate proof remain `I4`.

### 006F local closure — 2026-08-21

Locally proved:

- the active client now owns `diagnostics_collectors` and `support_bundle` as
  separate packages. Collectors accept only closed typed build/system/network/
  event/crash facts, emit six fixed virtual paths, copy caller input and cannot
  import filesystem APIs, enumerate files/apps or accept a destination;
- summary, standard, extended and crash profiles have exact hard limits. The
  extended profile accepts only an Ed25519-verified allowlist/byte ceiling with
  at most a 30-minute lifetime. Platform schemas under
  `shared/contracts/support/` own the signed envelope, X25519 recipient key set
  and extended-policy payload shapes without containing a key;
- canonical JSON produces a deterministic diagnostic ID, manifest hash,
  per-file SHA-256, categories, file sizes and removal counts. The prepared
  plaintext stays private to the library; the only output object is produced by
  X25519 + HKDF-SHA256 + AES-256-GCM encryption to a verified recipient;
- planted Bearer material, raw legacy-config markers, hostnames/domains, IPs,
  email, unsafe/unknown paths, contract tampering, expired/overlong policy and
  byte-budget overflow fail closed. Input/output byte copies close mutation
  races. Production packages have no file, directory, link, temp-write or ZIP
  surface, so traversal, symlink/reparse and cancellation cleanup cannot escape
  an owned temp area because no temp material is created at all;
- the Support sheet prepares an exact summary-profile preview before action:
  diagnostic ID, categories, total bytes, every virtual file/size, removal
  count and omitted optional categories. It separately labels the existing
  five-field ticket diagnostics map as a short summary and explicitly states
  that the encrypted bundle is not sent until signed-key/upload work exists;
- workspace bootstrap, seed validation, package inventory, host locks and the
  canonical client test gate include both packages.

Evidence:

- collectors `6/6`, support bundle `9/9`, both analyzers PASS; app-shell
  `329/329` and analyzer PASS;
- canonical client workspace gate PASS: observability contracts `3/3`, runtime
  `20/20`, new package suites, app-shell, runtime-engine `53` PASS plus one
  declared exact-old-DLL skip, Android `8/8`, Windows `20/20`, and Android
  direct/store JVM `BUILD SUCCESSFUL` with 145 tasks;
- seed/cross-repository/docs/source-logging contract PASS; the current Core is
  still honestly labelled `DIRTY_DEVELOPMENT_REPLACEMENT_PENDING`;
- platform signed-support schema tests `4/4`; combined docs/context suite
  `34/34`, context audit PASS, link check PASS and script manifest PASS.

Eight rows advance to local `I3`: `REL/OBS-001`, `REL_DOD/DOD-12`,
`OBS/OBS-014`, `OBS_DOD/DOD-11..14` and `FE/P12-112`. The distribution is now
92 rows at `I3`, 8 at `I2`, 7 at `I1` and 270 at `I0`; 107 of 377 rows are at
least `I1`. Production signing/recipient keys, custody/rotation, a deployed key
endpoint, encrypted upload/storage and physical exact-candidate proof remain
open `I4` work. 006G is active.

## WO-006G — Support case, upload and isolated ingest

Repository: platform and active client.
Dependency: 006F.

Deliver:

- idempotent support-case creation and existing-ticket binding;
- short-lived signed upload ticket bound to case/account-or-anonymous nonce,
  bundle ID, size, checksum, MIME and expiry;
- resumable/idempotent client upload with offline encrypted export and short
  summary fallback;
- completion endpoint that never unpacks in the web process;
- isolated worker validation for archive bombs, file count, traversal, schema,
  redaction report, checksum, MIME, hard limits and malware policy;
- encrypted-at-rest object lifecycle with no plaintext public storage.

Acceptance:

- replay/conflict/expired ticket and interrupted resume are deterministic;
- web workers cannot read archive contents;
- malicious archive corpus is rejected without escaping quarantine;
- case completion survives retry without duplicate bundles;
- `OBS/OBS-015`, `054..057`, `OBS_DOD/DOD-15..16` may reach local `I3`.
  Real object storage, key custody and upload remain `I4`.

### 006G local closure — 2026-08-21

Locally proved:

- normal authenticated clients can read the signed public recipient-key set,
  create or reuse a case-bound upload ticket, send sequential resumable chunks,
  read the authoritative offset/status and retry completion. Recovery scope is
  denied. Owner binding is canonical-account first with a server-owned
  anonymous-nonce fallback; the HMAC ticket binds owner, case, upload/bundle,
  declared bytes, SHA-256, exact MIME and bounded expiry;
- ticket creation, existing-ticket binding, exact chunk replay, lost-response
  resume, expiry renewal and completion are idempotent. Conflicting replay,
  cross-account case binding, over-limit bodies and invalid state fail closed;
- the API slice treats chunks as opaque ciphertext and has no ingest, archive or
  decrypt import. Completion only validates the persisted layout and queues the
  row. The opt-in worker alone loads a mounted X25519 private-key file, assembles
  bounded ciphertext, verifies every chunk/full digest and decrypts in memory;
- worker validation accepts only the canonical encrypted envelope and closed
  manifest/redaction/fixed virtual-file schemas. Unknown/traversal paths,
  duplicate files, count/byte/hash/MIME drift, raw config/destination/identity
  material and malware/script markers are rejected without escaping the private
  quarantine. Accepted storage contains only the original encrypted envelope;
- the client persists only the encrypted envelope in its private app-support
  outbox before network use, derives a deterministic idempotency key, follows
  the server offset and retains the encrypted object for explicit offline retry.
  The UI exposes encrypted send only with an explicit Ed25519 build pin; without
  it the existing short summary remains honestly labelled;
- Android and Windows release scripts accept the public signing key ID/key as an
  all-or-nothing pair. No private recipient key, production signing key, object
  store, deployment or successful real upload is included or claimed.

Evidence:

- platform upload/ingest/API/migration/worker tests `23/23`; combined slice,
  release-health and upload regression `31/31`; scoped Ruff PASS;
- client support-bundle tests `11/11`, outbox/integration tests `3/3`, app-shell
  `333/333`, runtime-engine `53` PASS plus one declared exact-old-DLL skip,
  Android `8/8`, Windows `20/20`, and direct/store Gradle unit gates
  `BUILD SUCCESSFUL` with 145 tasks;
- canonical client workspace gate PASS; seed/cross-repository/docs contract
  PASS with Core honestly reported as
  `DIRTY_DEVELOPMENT_REPLACEMENT_PENDING`;
- platform docs/context suite `34/34`, context audit, public link and script
  manifest checks PASS.

Seven rows advance to local `I3`: `OBS/OBS-015`, `OBS/OBS-054..057` and
`OBS_DOD/DOD-15..16`. The distribution is now 99 rows at `I3`, 8 at `I2`, 7
at `I1` and 263 at `I0`; 114 of 377 rows are at least `I1`. Production key
custody/rotation, deployed private object storage and worker isolation, a real
resumed upload and production retention remain exact `I4` work. 006H is active.

## WO-006H — Retention, release health and operator read models

Repository: platform; UI completion coordinated with WO-009.
Dependency: 006G.

Deliver:

- tested retention/deletion jobs and metrics for telemetry, encrypted bundles,
  quarantine and audited access;
- release/build/platform health aggregates, crash/connect/update deltas and
  version-scoped known-issue registry;
- L1 safe summary/timeline without bundle download;
- L2/SRE bundle access with least-privilege RBAC, reason, audit trail and
  expiry; no support L1 raw bundle access;
- incident/release observation links without letting telemetry create incidents,
  compensation or entitlements.

Acceptance:

- retention tests prove eligible deletion and legal/audit holds separately;
- aggregate responses contain no domain, IP, account, install or package name;
- every bundle access is role/reason/case scoped and audited;
- L1 can answer phase/code/attempt/build/proof outcome from summary alone;
- `OBS/OBS-058..060`, `OBS_DOD/DOD-17..21` may reach local `I3`. Production
  retention execution, real RBAC users, alerts and observation window are `I4`.

### 006H local closure — 2026-08-21

Locally proved:

- the telemetry worker now applies bounded retention to identity-free release
  health, accepted encrypted objects, rejected/incomplete quarantine chunks,
  upload rows and access audits. Exact owned names are validated before unlink;
  missing/file-error/held/deleted states are integer counters, and explicit
  bundle plus audit holds survive normal cleanup;
- the operator release-health view groups exact app/build/candidate/revision/
  platform/architecture identity for a current and preceding equal window and
  exposes crash/connect/update counts and deltas without identity, destination,
  domain, IP, package or raw metadata;
- the known-issue registry is unique by candidate and issue code, requires
  closed version/platform/severity/status evidence and treats incident/release
  references as observational labels with no authority side effect;
- every authenticated admin can read the closed L1 bundle phase/code/attempt/
  build/proof/timeline projection, but only explicitly allowlisted L2/SRE actors
  can issue a fixed-reason, case/upload-bound, 60–900-second access grant. The
  grant is actor-bound and atomically single-use; grant, download and hold
  changes are audited. The API verifies canonical private path, symlink/
  junction rejection, size and SHA-256 and returns only original ciphertext;
- production defaults and the operations contract document the retention
  windows, empty-by-default L2 allowlist, process/key boundary and the alerts/
  permissions/backlog evidence still required before enablement.

Evidence:

- current focused operator service/API tests `9/9`, including L1 denial,
  L2 actor binding, replay, audit, hold, checksum/path and in-root symlink
  rejection;
- exact-current combined support-bundle, release-health, module-slice, worker,
  app-first/admin/portal regression `158/158` PASS;
- scoped Ruff and format checks PASS; documentation/context suite `43/43`,
  platform-context audit, public link check, script manifest and
  `git diff --check` PASS.

Seven previously unproved rows advance to local `I3`: `OBS/OBS-058..060` and
`OBS_DOD/DOD-17..20`; `OBS_DOD/DOD-21` remains `I3` with stronger read-model
evidence. The distribution is now 106 rows at `I3`, 8 at `I2`, 7 at `I1` and
256 at `I0`; 121 of 377 rows are at least `I1`. Production retention execution
and backlog, real operator RBAC/ACLs, alerts, observation windows, key custody,
object storage and real bundle access remain exact `I4` work. WO-006 is locally
complete; WO-007 is next.

## WO-006I — Safe transport classification addendum — 2026-08-22

The generic start-failure boundary now distinguishes timeout, connection
refusal, authentication rejection and protocol negotiation as
`TRANSPORT-001..004`. Core keeps event ABI 1 and desktop ABI 2, client hosts
accept only the additive closed codes, and raw URL/secret-like material still
fails closed. The canonical catalog now contains 121 entries at SHA-256
`7d3bf242777d5bf76bbebcf162e5969d3f83d7f68b2787051e1c4fddeadc3dc7`;
the event schema hash is unchanged.

Canonical Core, platform catalog/handoff, Dart runtime, Android direct/store,
Windows native and focused Gate B state/diagnostic/migration checks pass.
`OBS/OBS-050` and aggregate `REL_GATE/GATE-B` advance to local `I3`. Exact
candidate/device/runtime/operator evidence remains `I4`; no candidate or
external mutation was performed. Full detail is retained in `WO-006I` and its
machine-readable evidence.

`WO-004B2` later adds the separate Core release-CI matrix: full-module tests,
focused ABI/vet/race/vulnerability/Staticcheck/fuzz gates, deterministic source
SBOMs and clean-source two-build Android/Windows/Apple evidence. That closes
`REL/CORE-001` at local `I3`; it does not change this observability ledger slice
or advance `REL_DOD/DOD-10`, because the hosted and exact-candidate executions
remain unrun.

## Verification matrix

Each slice runs the smallest focused tests, then its repository contract gates:

- platform: observability schema/catalog validators, focused API/service/worker
  tests, docs/context/link checks and `git diff --check`;
- client: package tests/analyze, host tests, canonical `scripts/run-tests.ps1`,
  seed/docs/cross-repo contract and `git diff --check`;
- Core: focused ABI/redaction tests, race/vulnerability/build gates as applicable,
  reproducibility only when exact artifacts are actually built;
- cross-repository: release-handoff v2 exact hash agreement.

No test count, artifact, hosted gate, device result, upload, retention run or
operator action is credited until it exists for the exact source/candidate.

## Ledger ownership

WO-006 owns Phase 04 rows:

- `REL/OBS-001`, `REL_DOD/DOD-12`;
- `OBS/OBS-001..060`, excluding already completed platform-producer rows only
  where this WO has not changed their evidence;
- `OBS_DOD/DOD-01..21`, `OBS_PB/PB-01..14`;
- `FE/P12-112`, `FE/P12-126`, support/recovery portion of `FE_PR/PR-08`;
- observability-only portions of `FRKN_ADOPT/ADOPT-02` and `ADOPT-04`.

No row advances from this document alone.

## Exit condition

WO-006 is locally complete when the contracts/catalog/hashes, non-blocking
client/Core/portal event path, phase/error mapping, encrypted previewed bundle,
case-bound upload protocol, isolated ingest, retention and bounded operator read
models are implemented and tested. Exact-candidate crash/overhead, signed policy,
external key custody, real upload/storage/retention, RBAC and release observation
remain explicit `I4` gates and cannot be converted into local passes.
