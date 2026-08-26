# WO-013 — Exact 1.2.0 candidate, Gate F and promotion decision

Status: `LOCAL_PRE_CANDIDATE_ASSEMBLED_WINDOWS_SIGNING_BLOCKED`
Classification: `ACTIVE_EXECUTION`
Phase: `11`
Lanes: platform, active Android/Windows client, Core, public release index,
manual device/origin/provider/owner evidence
Depends on: `WO-001..012`
Production/external actions: `NOT_AUTHORIZED`; source GitHub controls:
`AUTHORIZED_OWNER_SOLO`

## Outcome

Turn the locally proved 1.2.0 source wave into one immutable, signed,
candidate-scoped evidence set. Candidate identity is the exact tuple of
product version/channel, platform/client/Core/release-index revisions and
artifact hashes. A rebuild, revision change, replacement artifact or changed
contract digest creates a different candidate and invalidates inherited
runtime evidence.

The local preparation slice may close missing source regressions, version and
contract consumers, migrations, privacy/security/chaos harnesses, full local
CI, reproducible unsigned artifact builds and the complete manual-gate matrix.
It may create local commits on the isolated feature branches after all scoped
checks pass. It may not manufacture a release candidate from dirty worktrees,
reuse 1.1.6 evidence or sign with untrusted/debug identities. `WO-013O`
authorizes the bounded owner-solo GitHub source controls and public Core branch
protection. It still may not deploy, publish candidate assets, update the stable
pointer, contact users, create a live transport server, run a campaign/cohort
or promote without the exact separate authority and access.

## Current preflight truth

Current override: `WO-013N` published the trust root and closed every explicit
local pre-freeze row. `WO-013O` records the sole-owner exception, protects
public Core main and advances `FE/P12-023` to `I3`. The older identities and
counts below are retained as the local-preflight snapshot that led to those
closures, not current release status. `WO-013P` subsequently promotes the
signed final platform/client/Core source tuple and closes `REL/REL-001` and
`REL_DOD/DOD-09` at `I3`. `WO-013Q` then assembles the exact local Android and
Windows artifact set, SBOM, provenance and strict-v2 handoff. Android signing
passes, but Windows trusted signing and support-mode key binding remain
missing; `candidate_created=false` is retained.

- Platform, client and Core worktrees are clean for the exact-byte-aware local
  preflight at platform `7a15ba2bd5d17617aca28205cd448b6c917929ab`,
  client `336d5454d47fa33d08b7a6bae79b7980cc6b11b4` and Core
  `fcb3c8bbc6efdeed284417369aacb522722ebfa2`. These are local source/artifact
  identities, not a release candidate.
- Product source target is now exact `1.2.0+30` for Android/Windows and
  `1.2.0` for app-shell. The retained public handoff remains historical
  `1.1.6` schema v1 truth and is explicitly forbidden for new promotion.
- The separately versioned Core source target is `1.1.0` in
  `PRE_CANDIDATE_LOCAL` state. Android and Windows artifacts built twice from
  the exact clean Core revision are byte-identical and are bound to the active
  client by exact size/SHA-256. The retained public Core `1.0.3` identity stays
  separate; no old hashes were relabelled and no `1.1.0` release tag exists.
- Release-handoff schema/generator/validator v2 and release-bound workflow
  contracts exist locally, but no new v2 candidate metadata or signed artifact
  set exists.
- The public release-index baseline is now inspected: public `origin/main`
  `d0bf8e8c70ebeaa241f4c8f5b8a4452fd339ed15` is legacy checksum-only and
  unsigned. Local branch `f07654af496d042fa8dba3d8b2695e987c8e9eb7`
  implements the fail-closed v2 schema/signature/same-byte contract, but is
  unpublished and has no owner-provisioned trusted signing key.
- Trusted Windows signing, Android production lineage, clean Windows VM,
  physical Android devices, current/brain/RU origins, provider/legal/OIDC
  surfaces and external pilot authorization remain manual/external gates.
- The current ledger has 303 rows at local `I3`; 74 of 377 remain below `I3`.
  Of those, 20 are `I2`, 39 are `I1` and 15 are `I0`. The clean source commits
  do not advance any row by themselves or create candidate/production proof.
- The exact stage policy classifies those 74 rows as 3 `pre_freeze`, 33
  `candidate`, 17 `external` and 21 `deferred`. Three external rows are explicit
  pre-candidate blockers. With the local release-index branch supplied, the
  exact-byte-aware read-only preflight remains `BLOCKED` with four blockers:
  unpublished index revision, missing owner signing key, three local pre-freeze
  rows and three external pre-candidate rows. The stale seed and pending
  replacement-artifact blockers remain closed by exact revision/byte proof.

## Evidence labels

- `PASS`: exact local or candidate-scoped check actually ran and passed.
- `MANUAL_OWNER_TEST`: named physical/account/operator step is retained but
  has not been run by this automation.
- `BLOCKED_BY_ACCESS`: required environment, repository, credential or origin
  is unavailable.
- `BLOCKED_BY_OWNER_DECISION`: legal, channel, version/signing or go/no-go
  authority has not approved the action.
- `NOT_AUTHORIZED`: mutation, deployment, campaign, cohort or promotion is
  outside the current authority.
- `NOT_REQUESTED`: later action is intentionally not started because its
  prerequisite candidate does not exist.

None of the non-PASS labels advances a row to `I4`.

## WO-013A — Candidate authority and remaining-row matrix

Deliver:

- machine-check every one of the 377 ledger rows and classify every row below
  `I3` as local implementation, exact candidate, manual owner,
  external/access, deferred/rejected or promotion-only;
- bind every Gate A–F, release DoD, OBS DoD and STOP-SHIP row to one proof
  owner, environment, origin, acceptance command/artifact and rollback;
- define the version decision: product/app `1.2.0`, monotonically increasing
  platform build numbers generated from the candidate input, and a separately
  versioned Core identity/ABI;
- fail preflight on a dirty repository, missing public release-index revision,
  version drift, stale Core seed, missing contract digest, unresolved explicit
  pre-candidate external gate or any evidence row from a different candidate;
  candidate/manual rows remain below `I4` without circularly blocking creation
  of the exact bytes they must test.

Closure: matrix/preflight may reach local `I3`; no candidate row reaches `I4`.

Current implementation: `WO-013A2` binds all 377 keys through a fail-safe
`pre_freeze` default plus 70 exact overrides. Unknown/duplicate keys, ambiguous
external timing and a non-safe default fail validation. Candidate-stage rows no
longer block creation of the candidate they require, while ordinary local rows
outside P11/Gate/DoD remain blocking until local `I3`.

## WO-013B — Remaining local source and regression closure

Deliver the smallest missing local checks required by the open ledger:

- all STOP-SHIP defects map to permanent source regressions;
- state migrations from supported 1.1.x stores to 1.2.0 and rollback/future-
  schema behavior are deterministic on Android, Windows and platform DB;
- property/fuzz redaction, planted-secret, golden support-manifest, offline
  backpressure, fault/crash/hang, loss/DNS/MTU/IPv6 and bounded overhead tests;
- ingest load/abuse limits, privacy threat model/field inventory, access-review
  playbook and release-health stop policy;
- version/product/copy/error/observability/AWG/commercial/release-contract
  consumers agree across platform, client and Core;
- full repository test entrypoints, dependency/lock checks, docs/contracts,
  lint/analyze/build and focused browser/native matrices pass.

Local emulation/source checks are not physical-device or deployed-origin proof.

## WO-013C — Freeze clean source identities

After 013B passes:

1. self-review each repository diff for scope, secrets, generated/provenance
   truth, destructive behavior and docs impact;
2. commit platform, Core and client feature branches independently, in
   dependency order, without touching promotion branches;
3. re-run the release-bound gates on clean commits and retain exact revisions;
4. obtain or clone the public release-index repository and record its exact
   revision before constructing candidate input.

Any edit after the freeze requires new commits and a fresh gate run.

## WO-013D — Exact local artifact candidate build

Only from the clean frozen revisions:

- build Core Android AAR and Windows DLL twice with pinned toolchains and
  compare bytes/digests; bind ABI/capability/event/AWG contracts and SBOM/
  provenance;
- update the client runtime seed to those exact Core artifacts, then build
  direct Android artifacts, store AAB readiness artifact and Windows
  machine-wide installer from the same client commit;
- validate package/version/build/ABI, signer lineage, runtime dependencies,
  service/installer contract, artifact names/sizes/SHA-256 and absence of
  secret/debug inputs;
- generate strict release-handoff v2 outside historical release storage,
  validate it from platform/client/Core and refuse stable promotion while any
  required signing/provenance/manual gate is not PASS.

Unsigned/debug/local artifacts are `PRE_CANDIDATE_LOCAL`, not an RC.

## WO-013E — Exact manual/runtime matrix

Run and retain against the exact artifact hashes:

- Windows 10/11 clean VM: install/upgrade/uninstall, single instance, ordinary
  user UI, authenticated SCM service, Core/TUN/routes/DNS/egress, sleep/resume,
  crash/forced kill/reboot and rollback restoration;
- Android API/OEM matrix: direct/store identity, production signer upgrade,
  permission/notification privacy, Wi-Fi/LTE switch, Doze/standby/process death,
  MTU/IPv4/IPv6/Private DNS, selected apps, update and rollback;
- connection/observability fault matrix, encrypted bundle, support short code,
  access review and known-issue/release-health behavior;
- same-build performance/battery/CPU/thermal baselines;
- current-origin, brain-origin and RU-origin kept as distinct retained sets;
- payment providers, entitlement/outbox, legal/commercial revision, Operator
  Center OIDC/step-up/RBAC/action-intent/cutover and static rollback using exact
  deployed revisions.

Each unavailable lane stays manual/blocked. Operator attestation records what
was observed; it never substitutes for a missing machine artifact.

## WO-013F — Gate F and evidence-based go/no-go

Gate F is PASS only when:

- Gates A–E and every mandatory STOP-SHIP/DoD row have exact-candidate proof;
- no false-green, secret leak, payment/access inconsistency, auth/RBAC/
  action-intent bypass, legal/commercial blocker, rollback failure, significant
  performance regression or artifact/provenance mismatch remains;
- all artifact signing/SBOM/provenance and manual gates required for the target
  channel are PASS;
- release notes, known limitations, support docs and public product facts are
  derived/validated against the same v2 manifest;
- rollback triggers, kill switches, owners and observation windows are named.

Output one `GO`, `NO_GO` or `BLOCKED` decision bound to the candidate ID and
evidence digests. Missing evidence can only produce `NO_GO`/`BLOCKED`.

## WO-013G — Same-byte promotion and observation

Requires a separate explicit user/owner authorization after 013F GO.

- promote the exact bytes; never rebuild;
- update public release index and channel pointers atomically with readback;
- run current-origin, brain-origin and required external/RU checks separately;
- observe crash/connect/update/payment/support/incident guardrails for the
  defined window;
- rollback immediately on a stop trigger and retain both forward and rollback
  evidence.

No current instruction authorizes this slice.

## Current next action

`WO-013U` retains the earlier six-file direct-beta pre-candidate set and the
owner-approved unsigned-Windows/SmartScreen exception. The runtime tuple under
test advanced to platform `243dcbe4727041d62cc0a36e7d2fd5a8530c7c25`,
client `a74d2aea5aed62f5c31d3a0bbc258e408cebe3bd` and Core
`9b94e0bda7e454536e8fa9b4519f2281211798e0` for ABI-safe Android delivery,
selector correction, AWG 3.1 lab support and deployment/runtime fixes.

`WO-013E-android-mobile-runtime-matrix.md` records one production-signed
Android `1.2.0 (4031)` artifact, an in-place physical-device upgrade, the
partial Beeline route matrix, LDPlayer boundary and current deployed type-2/
type-3 reconciliation. It is explicitly pre-candidate evidence: no row moves
to `I4`, RU-origin stays `NOT_RUN` and AWG 3.1 stays lab-only
`BLOCKED_BY_ACCESS` without an isolated owned target.

Next, freeze the branch heads after this evidence lands, rebuild the complete
Android/Windows direct-beta set and regenerate strict handoff, SBOM,
provenance, checksums and signed release index from those same bytes. Only that
set can enter the remaining
exact device/VM, provider, OIDC, legal, current/brain-origin and rollback
matrix. Candidate creation and public promotion remain `NOT_CREATED`/
`NOT_RUN` until those gates are retained.
