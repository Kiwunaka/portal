# WO-004 — State/Core Truth

Status: `COMPLETE_I3`
Classification: `ACTIVE_EXECUTION`
Phase: `02`
Lane: active client and Core compatibility

## Bounded outcome

Replace UI-implied connection success with one typed client experience state.
The green/verified state requires current DNS and selected-outbound egress
evidence, not only a started Core or tunnel. Keep Core ABI, event ABI and saved
state migrations machine-readable and compatibility-tested before any breaking
change.

This WO creates no release candidate or runtime artifact and authorizes no
deploy, signing, publication, production mutation or public support claim.

## Entry evidence

- `WO-003B` locally proves strict release-handoff v2 enforcement across the
  platform, active client and Core promotion lines.
- `RuntimeSnapshot` already exposes host, DNS, uplink and Core egress evidence.
- Android already fails closed on a missing or failed selected-outbound Core
  probe.
- The desktop runtime already runs an authenticated egress probe before it
  returns a verified running snapshot.
- Home, profile, support and the shell controller still derive consumer state
  independently; the connect disc infers reconnecting from `busy && running`.
- Core publishes desktop ABI `2` in `config/release.json` and through
  `pokrovCoreAbiVersion`, but ABI v3 and saved-state rollback work are not yet
  implemented.

## Authority decisions

1. The active client owns consumer connection truth and presentation.
2. The Core owns exported ABI and event capabilities; the active client owns
   compatibility consumption.
3. A frontend adapter on the current contract precedes ABI v3. ABI v3 cannot
   silently block the reducer/presenter correction.
4. `ConnectedVerified` requires `running`, healthy host, healthy DNS, healthy
   uplink, no explicit DNS-readiness failure and
   `coreEgressValidated == true`. The current typed `dnsState == healthy`
   remains valid DNS proof when the older host omits the redundant
   `dnsReady` boolean.
5. A started tunnel without all proof is `ConnectedUnverified`, never green.
6. Disconnecting and reconnecting require explicit typed intents. They cannot
   be inferred from a boolean combination.
7. Raw Core errors remain outside UI copy. Only bounded public reason codes and
   redacted diagnostics may cross into the experience state.

## Execution slices

### WO-004A — Current-contract reducer and presenter

Repository: active client only.

Deliver:

- sealed `ConnectionExperienceState` variants for idle, permission required,
  preparing, connecting, connected-unverified, connected-verified,
  disconnecting, reconnecting, blocked and failed;
- typed stage, transition intent, blocked reason and bounded failure reason;
- one `ConnectionPresentation` for title, CTA, semantics, tone, connect-disc
  phase and busy/degraded/verified flags;
- an explicit legal transition matrix and exhaustive pair coverage;
- strict `RuntimeSnapshot.isCleanlyHealthy` proof requirements;
- Home, profile, support and shell-controller consumption through the adapter;
- explicit disconnect/reconnect disc phases;
- one tap haptic per primary action and at most one actual outcome haptic.

Acceptance:

- `running` without healthy host, DNS, uplink or egress proof, or with an
  explicit DNS-readiness failure, is never `ConnectedVerified`;
- `connectedVerified -> disconnecting -> idle` never renders reconnecting;
- reconnecting appears only with an explicit reconnect intent;
- CTA, status copy, tone, disc phase and semantic label come from one
  presentation object on Home;
- support/profile do not own parallel connection status copy;
- reducer and transition tests pass on all supported host enums without a
  native runtime artifact.

### WO-004B — Core ABI/event compatibility contract

Repositories: Core and active client; platform release metadata only if the
strict v2 schema needs a compatible additive field.

Deliver after 004A:

- one machine-readable Core capability/ABI owner generated or checked against
  `config/release.json` and exported symbols;
- ABI v2 marker-only compatibility retained while an additive capability and
  closed lifecycle-event descriptor is introduced;
- typed lifecycle events for profile, Core start, TUN, routes, DNS, egress,
  recovery and stop reason;
- exported-symbol, client binding, compatibility and fail-closed unknown-event
  tests;
- Core CI coverage for Go race/security checks that are supported by the
  current toolchain, Android ABI contents, Windows exports and reproducibility
  checks without manufacturing candidate evidence.

ABI v3 may advance only after the current client passes both v2 compatibility
and a separate v3 binding/capability fixture. `004B` deliberately keeps ABI 3
unsupported: claiming familiar capabilities cannot make an unknown ABI
runnable. Core callback ownership, event ABI v3, `core_run_id`/`attempt_id` and
transport failure taxonomy stay in `WO-006`; they are not fabricated under the
released ABI 2 marker.

## 004B closure evidence — 2026-08-21

Result: `COMPLETE_I3` for the ABI 2 compatibility baseline and client-owned
typed lifecycle journal. This is not ABI v3, a built artifact, or candidate
proof.

- Core now owns `config/abi-contract.json`; `config/release.json`, all desktop
  `//export` declarations and the exact embedded descriptor are checked by
  `scripts/verify-abi-contract.ps1`.
- ABI 2 adds the caller-owned `pokrovCoreCapabilities` descriptor without
  breaking released marker-only ABI 2 libraries. The active client supports
  both lanes and releases descriptor memory through `freeString`.
- The client fails closed on ABI 3, malformed descriptors, unknown descriptor
  or event ABI versions, missing/extra capabilities and unknown lifecycle
  event identifiers before Core setup.
- Desktop runtime journaling uses the closed typed vocabulary for
  initialization, profile, Core start, TUN, routes, DNS, egress, recovery and
  stop, with bounded probe and stop-reason enums.
- Core ABI contract: `PASS`, descriptor schema `1`, event ABI `1`, `13`
  declared exports. Core focused WARP regression: `1 passed`; Core full test
  script and both TLS lanes: `PASS`; `go vet` for supported runtime packages:
  `PASS`.
- Client runtime engine: `51 passed`, `1` real-DLL test skipped. Full client
  gate: app shell `320 passed`; runtime engine `51 passed`, `1` skipped;
  Android shell `8 passed`; Windows shell `17 passed`; Android Gradle
  `BUILD SUCCESSFUL`.
- Cross-repository client/Core parity, strict release-handoff v2, client CI
  contract, docs contract and seed validation: `PASS`; client/Core
  `git diff --check`: `PASS`.
- Core CI now declares `go vet` and Linux race jobs. Local Windows race is
  `NOT_RUN` because the verified portable Go runtime has `CGO_ENABLED=0` and
  `-race` requires cgo; hosted execution is unclaimed.
- The Windows build now requires MinGW `objdump` and checks the completed DLL
  for every contract export. The DLL build/export probe, Android AAR rebuild,
  reproducibility comparison, vulnerability scan, signing, device and hosted
  CI evidence are `NOT_REQUESTED`/not executed; no candidate was created.

### WO-004C — Versioned saved-state migrations and rollback

Repository: active client, with Core only if a Core-owned persisted format is
actually identified.

Deliver after the persisted-state inventory is frozen:

- explicit versions and bounded decoders for client experience, session,
  staged runtime configuration and update state that are actually retained;
- forward-unknown fail-closed behavior where safety requires it;
- previous-version fixtures, idempotent migration tests and downgrade/rollback
  expectations;
- canonical ownership and retention rules without copying secrets into
  fixtures or evidence.

The current `PokrovClientExperienceState` emits `version: 1` but does not route
decoding by version. That is evidence for 004C, not permission to redesign all
local storage during 004A.

## 004C closure evidence — 2026-08-21

Result: `COMPLETE_I3` for the locally implemented saved-state inventory,
version routing, migrations and rollback behavior. This is not physical-device
upgrade/downgrade or exact-candidate proof.

- The canonical client owner is
  `docs/architecture/persisted-state-contract.md`. It inventories app-first
  metadata, secure credentials, client experience, Android staged-profile
  reuse, emergency/WARP state, materialized config, rule-set cache, update
  handoff, runtime journal and scalar convenience markers.
- App-first metadata now emits `schema_version: 1`; unversioned `v0` is
  atomically migrated. Secure raw-token `v0` values migrate best-effort to the
  existing credential JSON `version: 1`. A future or malformed version is not
  used and is preserved.
- Client experience retains current `version: 1`, explicitly routes
  unversioned `v0`, rewrites it once, and returns empty convenience state
  without overwriting a future version.
- Android staged-profile SharedPreferences now emit `schema_version: 1`.
  Valid unversioned records migrate idempotently; absent legacy safety fields
  disable Quick Settings reuse and require Core egress proof. Future versions
  do not restore into runtime and are not erased.
- Materialized runtime JSON is derived and regenerated; only the Android
  pointer/attestation is restored. Update phase/byte counters are process
  memory only; the retained APK cache is keyed and reverified by exact size and
  SHA-256. No fictitious update-state or Core-owned persisted schema was added.
- Sanitized `v0` fixtures cover bootstrap metadata, client experience and
  Android staged-profile preferences. They contain no credential, provider
  endpoint, private key or real account/customer identifier.
- Focused app-shell migration/bootstrap tests: `90 passed`. Full client gate:
  app shell `326 passed`; runtime engine `51 passed`, `1` real-DLL test
  skipped; Android Flutter `8 passed`; Windows `17 passed`; Android JVM `146
  passed`; Gradle `BUILD SUCCESSFUL`.
- Cross-repository client/Core parity, release-handoff v2 (`12` cases), strict
  CI contract, docs contract, seed validation and client `git diff --check`:
  `PASS`.
- The unqualified Gradle `testDebugUnitTest` task was also attempted and failed
  while configuring a third-party Flutter plugin because its cache and build
  files were on different Windows drive roots. The repository-owned
  `:app:testDebugUnitTest` gate passed and is the documented command.
- Physical-device upgrade/downgrade, clean-VM rollback, hosted CI, signing,
  artifacts and exact-candidate evidence remain `NOT_REQUESTED`; no candidate
  was created.

## Exact 004A write scope

Client (`codex/1.2.0-release-v2`):

- `packages/runtime_engine/lib/runtime_engine.dart` and focused tests;
- `packages/app_shell/lib/app_shell.dart`;
- one focused connection experience adapter under
  `packages/app_shell/lib/src/features/home/`;
- Home, profile, support, shell composition and connect-disc files only where
  needed to consume the typed presentation;
- focused app-shell tests and the client canonical architecture/testing docs.

Platform (`codex/1.2.0-phase00`):

- this WO, wave index and execution ledger/evidence only.

Core has no 004A write scope.

## 004A verification

```powershell
dart format packages/app_shell/lib packages/app_shell/test packages/runtime_engine/lib packages/runtime_engine/test
flutter test packages/runtime_engine/test/runtime_engine_test.dart
flutter test packages/app_shell/test/connection_experience_test.dart
flutter test packages/app_shell/test/design_system_contract_test.dart
flutter test packages/app_shell/test/pokrov_seed_app_test.dart
powershell -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\validate-seed.ps1 -PlatformRoot C:\path\to\platform -CoreRoot C:\path\to\POKROV-core
```

Native device, 20-cycle clean-host connection, GitHub-hosted workflow and
exact-candidate checks remain `NOT_REQUESTED` until separately authorized and
executed against the matching candidate.

## 004A closure evidence — 2026-08-21

Result at 004A closure time: `COMPLETE_I3` for the current-contract
reducer/presenter slice only. ABI compatibility and saved-state migrations
were still open then and are closed by the later 004B/004C sections above.

- Added the sealed connection experience reducer, one presentation owner,
  explicit disconnect/reconnect intents, the transition matrix and bounded
  haptic coordinator in the active client.
- Green state now requires healthy host, DNS and uplink evidence plus a
  successful selected-outbound egress probe on every supported host enum.
- Home, profile, support and shell-controller consumer state now use the shared
  presentation; local status-copy reducers were removed from those surfaces.
- Focused connection tests: `9 passed`; app-shell package: `319 passed`.
- Repository client gate: app shell `319 passed`; runtime engine `47 passed`,
  `1` real-DLL test skipped; Android shell `8 passed`; Windows shell `17
  passed`; Android Gradle `BUILD SUCCESSFUL`.
- Cross-repository `validate-seed.ps1`: `PASS`; client docs contract: `PASS`;
  platform docs/context contracts: `30 passed` plus `PASS platform-context`;
  client and platform `git diff --check`: `PASS`.
- Native device, clean-host cycles, hosted CI, signing, artifact and candidate
  proof remain `NOT_REQUESTED`; no candidate was created.
- `FE_PR/PR-01` remains `I1` because its source acceptance asks for a debug
  old/new shadow period; this slice performed a direct cutover instead.
- `FE_PR/PR-02` remains `I1` because visual snapshots are still absent even
  though presenter, disc and haptic behavior are locally proved.

### 004A2 follow-up closure — 2026-08-22

`WO-004A2` later closes both historical exceptions above. The current tree has
one guarded `ConnectionCoordinator`/reducer/presenter boundary and no legacy
live reducer to shadow. Reintroducing one would violate the accepted single-
truth architecture, so direct cutover is the explicit owner decision.

Four deterministic critical-state widget goldens now cover idle light, first
route-scope dark, verified dark and degraded light. The boundary check,
`14/14` focused reducer/coordinator tests and the four-image golden matrix pass.
`FE_PR/PR-01` and `FE_PR/PR-02` therefore advance from `I1` to local `I3`;
physical-device and exact-candidate visual evidence remain open before `I4`.

## Ledger ownership

004A/004A2 may advance only rows directly proved by the reducer/presenter,
direct-cutover boundary and deterministic visual tests:

- `REL/STATE-001`, `REL/UX-001`;
- `FE_BUG/P0-CONN-001..003`;
- `FE/P12-001..005`;
- `FE_PR/PR-01`, `FE_PR/PR-02`;
- `FRKN_ADOPT/ADOPT-01` only if the proof invariant is implemented and tested.

004B later advanced `REL/ABI-001` to `I3` and `REL/CORE-001` to `I2`; 004C
later advanced `REL/MIG-001` to `I3`. `WO-004B2` completes the release-CI
source contract and advances `REL/CORE-001` to local `I3` without crediting an
unrun hosted job or exact candidate. WO-006C closed `OBS/OBS-047..049`, and
WO-006I closed `OBS/OBS-050` plus aggregate Gate B with four reviewed transport
classes and current cross-repository tests. Remaining Core artifact/security
DoD remains `I2` until the hosted platform jobs and exact evidence execute.

WO-004D later reconciled `FE/P12-201` with the source plan: ABI v3
`ConnectionStatus` is a post-1.2.0 P2 proposal and cannot block this release.
The row is verified and explicitly deferred at `I1`; desktop ABI 2 and the
client-owned typed adapter remain the 1.2.0 authority.
