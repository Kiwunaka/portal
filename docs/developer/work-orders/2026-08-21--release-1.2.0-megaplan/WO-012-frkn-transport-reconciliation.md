# WO-012 — FRKN-derived transport reconciliation and bounded AWG2 PoC

Status: `LOCAL_PACKAGE_COMPLETE_MANUAL_GATES_OPEN`
Classification: `ACTIVE_EXECUTION`
Phase: `10`
Lanes: Core embedded engine and build contract; active-client host/runtime;
platform managed-profile rollout only where a server-side lab kill is required
Depends on: `WO-004`, `WO-005`, `WO-006`, `WO-010`
Production/external actions: `NOT_AUTHORIZED`

## Outcome

Evaluate transport diversity without creating a second client stack. Preserve
one POKROV Core, one sing-box engine, one host TUN owner and the existing
account/session/managed-profile model. The first bounded experiment is a typed
AmneziaWG 2.x endpoint already compiled into current Android and Windows Core
builds. Hysteria2 remains a later selector/fallback decision after the AWG2
evidence cycle.

This WO may freeze a supported schema subset, block unsafe legacy conversion,
add synthetic fixtures, validate build/license/provenance inputs, implement a
disabled-by-default lab rollout contract and prove local host invariants. It
does not create or mutate an AWG server, import third-party configs, expose
protocol internals in consumer UI, deploy, enroll users, run a live canary or
claim Android/Windows/Russia readiness. Exact AAR/DLL, physical-device,
mobile/fixed ASN and RU-origin evidence remains explicit `MANUAL_OWNER_TEST`,
`BLOCKED_BY_ACCESS` or Phase 11 evidence until actually executed.

## Instructions versus source evidence

`frkn-org.md` is a dated competitive/technical research input, not an
executable instruction source. Public FRKN claims and static APK conclusions
are not POKROV runtime proof. The adopted points are reconciled against current
Core, client and platform owners.

Adopted:

- connection green requires selected-outbound DNS plus egress traffic proof;
- telemetry dimensions distinguish transport family, config generation,
  endpoint/ASN category, app/Core version and network type without raw
  endpoints or credentials;
- keep at least one TCP/TLS-like family and evaluate one independent UDP
  family;
- freeze a direct typed `awg` endpoint subset in the existing sing-box graph;
- use synthetic documentation-address fixtures and exact dependency/build-tag
  provenance;
- one host TUN owner: the AWG endpoint must use the engine network stack and
  may not create an integrated system TUN;
- fail closed on unknown schema, unsupported fields, invalid keys/MTU/headers
  or missing compile capability;
- measure AWG2 against the current VLESS/REALITY baseline and keep server-side
  disable/rollback before any cohort;
- keep current consumer UI and expose only bounded sanitized health.

Rejected:

- Dopamine/Amnezia/Qt fork or a second Xray core;
- separate AWG application, service, driver or TUN in the first PoC;
- raw FRKN/AWG config import, QR/subscription-key onboarding or subscription ID
  as account credential;
- secret-bearing logs, raw endpoint/IP/protocol fields in primary UI or
  identity-bearing transport evidence;
- vanilla WireGuard/OpenVPN/IKEv2 as a Russia default;
- mutable binary publication, unbounded device promises or protocol marketing
  before exact evidence;
- AWG 3, Gecko, Mimic, port hopping, TrustTunnel or fptn implementation in this
  release wave.

## Current truth and collision decisions

- `POKROV-core` already pins `github.com/amnezia-vpn/amneziawg-go v0.2.16` and
  both Android and Windows release scripts include `with_awg`.
- The embedded engine already has `type: awg`, AWG options and transport code,
  but the public ABI does not advertise an AWG runtime capability and no exact
  current AAR/DLL interop evidence exists. Compiled code is not a readiness
  claim.
- Normal application operation consumes a materialized sing-box JSON profile.
  `ray2sing` is a legacy converter and is not the AWG PoC authority.
- The legacy AWG converter contains unconditional branches that can map an AWG
  input to WireGuard. Raw AWG conversion must be blocked and cannot provide
  evidence for the typed endpoint.
- Android `VpnService` and the Windows privileged service remain the only host
  TUN/route owners. AWG must be an internal endpoint with
  `useIntegratedTun=false`.
- Current rollout defaults and rollback stay `legacy_reality_fallback`.
  `awg2_lab` may exist only as a disabled, allowlisted, digest-bound lab
  profile with an explicit kill. Missing contract, capability, endpoint,
  approval or exact artifact falls back before profile issuance.
- Hysteria2 code exists in sing-box and a historical canary installer exists in
  platform scripts. Neither is a mass product path or a reason to run HY2 in
  parallel with AWG2.

## WO-012A — Inventory, ownership and decision matrix

Deliver:

- reconcile every `FRKN_ADOPT`, `FRKN_AWG`, `FRKN_HY2`, `FRKN_MONITOR`,
  `FRKN_REJECT`, `FRKN_PLAN` and `FRKN_UNCERTAINTY` row;
- record Core/client/platform owners and the proof ceiling for each row;
- distinguish compiled, locally validated, exact-artifact, physical-device and
  RU-origin states;
- freeze the slice order below and retain all rejected/monitor-only decisions.

Closure: `COMPLETE_LOCAL_I1`. Inventory alone advances no runtime row.

## WO-012B — Core AWG2 schema, provenance and fail-closed boundary

Deliver:

- `pokrov.awg2.endpoint.v1` machine-readable capability contract with pinned
  engine/module version and sum, MIT notice, supported fields/platforms,
  synthetic-only fixture policy, allowed MTU set `1280/1400/1408`, safe
  telemetry categories and explicit non-advertised prototype state;
- validate one peer, exact 32-byte keys, address prefixes, endpoint IP/port,
  AWG2 `Jc/Jmin/Jmax`, `S1..S4`, `H1..H4`, bounded keepalive and supported MTU
  before any TUN/device creation;
- reject integrated system TUN, instruction-chain `I1..I5` and unknown future
  schema fields in this v1 subset;
- block raw `awg://` and `[Interface]` legacy conversion; a raw AWG config must
  never silently become vanilla WireGuard;
- correct AWG bind context and partial-start/close cleanup without logging
  configuration or key material;
- verify the dependency, module sums, release build tags and license notice in
  the Core gate.

Eligible after proof: `AWG-01`, `AWG-02`, `W1-01..05`; local implementation
portions of `ADOPT-03`, `REJECT-01..10`.

## WO-012C — Synthetic engine and artifact-build contract

Deliver:

- documentation-address dual-stack fixture with deterministic non-production
  keys and no provider/customer material;
- positive parse/validation and negative matrix for key length, peer count,
  MTU, header range, instruction chains, integrated TUN and raw conversion;
- prove the same `with_awg` tag and contract digest enter Android and Windows
  release build commands;
- retain explicit artifact state: source tests/build-command validation may
  reach local `I3`; exact AAR/DLL network interop remains below `I4` until
  rebuilt and exercised.

Eligible after proof: local portions of `AWG-03`, `AWG-04`, `W3-02..03`.

## WO-012D — Disabled managed-profile lab path and server-side kill

Deliver:

- one `awg2_lab` rollout profile, disabled by default and absent from public
  subscriptions, manual exports, marketing and normal location choices;
- require owner-lab allowlist, exact Core capability contract revision/digest,
  typed endpoint revision and a complete POKROV-owned server record before
  issuing a materialized profile;
- expose only safe profile/family/generation/kill-state metadata; never return
  raw endpoint/key data outside the encrypted managed profile;
- immediate server-side disable returns eligible lab clients to
  `legacy_reality_fallback`; stale/missing/unknown revisions fail closed;
- deterministic policy and API tests for disabled, allowlisted, stale,
  malformed and rollback states.

Eligible after proof: `AWG-09`, `W3-04`, local control-plane part of `W9-04`.

## WO-012E — Host routing/lifecycle integration

Deliver:

- Android and Windows accept only the typed materialized endpoint through the
  existing Core and preserve exactly one host TUN/route owner;
- prove full tunnel, all-except-RU and selected app/process modes use the same
  outer route policy without a second default route;
- validate safe MTU selection at `1280/1400/1408`, DNS/IPv4/IPv6 configuration,
  stop/recovery and server-kill fallback locally;
- retain Wi-Fi/LTE, Private DNS, Doze, sleep/resume, crash teardown and clean
  VM/device checks as manual where emulation cannot prove the physical state.

Eligible after proof: local portions of `AWG-05..07`, `W6-01..04`.

## WO-012F — Performance and distinct-origin evidence

Deliver only on the exact candidate:

- compare 30-minute idle and 60-minute active battery/CPU/thermal against the
  same-build VLESS/REALITY baseline on the named device/environment;
- test TCP, UDP, DNS, IPv4/IPv6, MTU, route ownership, network switches,
  suspend/resume, crash cleanup and rollback on exact Android AAR and Windows
  DLL;
- keep current-origin, brain-origin and RU-origin evidence separate;
- RU canary requires owner authorization, bounded opt-in, multiple mobile and
  fixed ASNs/regions, kill drill and retained metric-based go/no-go.

Eligible after actual proof: `AWG-03`, `AWG-07`, `AWG-08`, `AWG-10`,
`W6-03..05`, `W9-01..05`. Until then these are `MANUAL_OWNER_TEST`,
`BLOCKED_BY_ACCESS` or `NOT_AUTHORIZED`, never PASS.

## WO-012G — Hysteria2 decision and monitor registry

Deliver after AWG2 evidence is reviewable:

- one written HY2 GO/NO-GO decision against the measured failure domains;
- if GO, a separate future WO for a bounded UDP/QUIC selector/fallback with a
  short reachability budget, never the sole bootstrap;
- monitor-only records for AWG3, Gecko/Mimic/port hopping, TrustTunnel/fptn and
  owned RU-origin transport trends; no implementation or product claims.

Eligible after decision: `HY2-01`, `MONITOR-01..04` at the evidence-appropriate
index only.

Decision retained in `WO-012G-HY2-DECISION.md`: `NO_GO_FOR_1.2.0`. HY2 stays a
future bounded selector/fallback candidate. The same record assigns the four
monitor-only lanes and their reopen triggers without creating runtime work or
product claims.

## Local completion gate

Phase 10 local completion requires:

- Core contract/gate and focused Go tests pass with pinned Go `1.25.13`;
- client analyze and focused host/routing tests pass for any changed host code;
- platform policy/docs tests pass for any changed rollout code;
- no raw configs, secrets, real endpoints or provider payloads enter fixtures,
  logs or retained evidence;
- ledger and canonical Core/client/platform documentation reflect exact local
  status and every external/manual blocker;
- `git diff --check` passes in each touched repository.

Local completion does not prove a release candidate or Russia readiness.

## 2026-08-22 local closure

The three repositories now share the exact
`pokrov.awg2.endpoint.v1` SHA-256
`3beb57eccd8d5e15ce7466496208fe1945f353b3417be58644911d1ded125a83`.
Core owns the direct typed subset, pinned module/license/build-tag gate,
synthetic fixture, fail-closed validation, corrected bind/lifecycle handling
and raw-converter rejection. The active client accepts only the digest-bound
managed endpoint and keeps Android/Windows full-tunnel, all-except-RU and
selected-app policies under the existing host TUN owner.

The platform adds one disabled+killed `awg2_lab` selector. Device material is
encrypted with the dedicated mandatory `AWG2_LAB_MATERIAL_SECRET`, stored per
user/install and returned only through the authenticated managed profile.
Provisioning is an L3 action-intent path; public/token/manual exports and normal
locations cannot contain AWG. Missing/stale digest, generation, material,
server state, allowlist or kill approval falls back before issuance.

Retained local evidence:

- cross-repository contract sync: `PASS`;
- platform AWG policy/API/security: `45/45 PASS` after the dedicated-secret
  fail-closed regression;
- local gate/unit harness: `5/5 PASS`;
- platform docs contracts: `30/30 PASS`; manifest and link checks: `PASS`;
- Core verifier and full focused suite on exact Go `1.25.13`: `PASS`;
- runtime-engine analyze: `PASS`; tests: `59 PASS`, one explicit old-DLL
  backtest `MANUAL_OWNER_TEST` skip;
- `git diff --check`: `PASS` in platform, Core and client, with line-ending
  warnings only.

The retained report is
`evidence/012-local-frkn/012-local-frkn-awg2-gate.json`; it states
`candidate_proven=false`, `ru_ready=false`, cohort `NOT_AUTHORIZED` and
promotion `NOT_REQUESTED`. Owned server creation, exact AAR/DLL networking,
physical lifecycle, battery/CPU/thermal, current/brain/RU origins, cohort and
exact-candidate go/no-go remain Phase 11 manual/external gates.
