# WO-005 — Runtime Privilege And Platform Boundaries

Status: `COMPLETE_LOCAL_LINUX_NOT_SHIPPED`
Classification: `ACTIVE_EXECUTION`
Phase: `03`
Lanes: active client, Core compatibility, platform execution evidence

## Bounded outcome

Correct the operating-system trust and lifecycle boundaries before adding the
release-wide diagnostics, support and frontend layers:

- Windows runs one ordinary per-user UI/tray process and a separately
  installed, constrained privileged control plane; the Flutter process is not
  relaunched as administrator;
- Windows activation, service IPC, privileged commands and network mutation
  are typed, authenticated and independently recoverable;
- Android keeps its working VPN lane while removing lockscreen disclosure,
  UID-wide traffic attribution, unsafe MTU fallback, unmanaged bridge work and
  direct-updater permission from the store flavor;
- Linux remains a conditional beta lane until a non-root UI, privileged
  daemon, package policy and exact clean-host matrix exist.

This WO authorizes local source, tests and canonical client documentation. It
does not authorize a release candidate, signing, publication, store action,
production mutation, service installation on the owner's machine, device/VM
mutation or a public Windows/Linux support claim.

## Input classification

The dated `POKROV_release_1.2.0_full_audit_with_client_logging_RU.md` is audit
input. Its proposed component tree and mechanisms are advisory until
reconciled here with the current client/Core owners. The user's request to
execute the complete 1.2.0 megaplan is the task authority; it does not turn an
old observation or an unrun manual check into a pass.

Current source establishes these entry facts:

- Windows forwards only a bounded acquisition URI through unauthenticated
  `WM_COPYDATA`; an ordinary second launch creates another UI process;
- Windows connect currently uses `ShellExecuteW(..., "runas", ..., "--connect")`
  and therefore elevates the complete Flutter/runtime process;
- the login Run entry starts the normal visible executable without an explicit
  startup mode;
- Windows has no service/helper binary, authenticated service protocol or
  privileged recovery journal;
- Android declares `REQUEST_INSTALL_PACKAGES` and its private update provider
  only in the direct flavor; store has neither surface;
- 005D1 has replaced the public detail-bearing Android notification with a
  private generic surface and removed UID sampling from that surface;
- 005D1 has replaced the runtime MTU `9000` fallback with a bounded
  `1280..1500` policy and platform-interface ceiling;
- 005D2 has replaced raw Android bridge threads with bounded parent scopes and
  has wired Core `CommandStatus` TUN totals into generation-fenced session
  rates with explicit unavailable/warming/reset/overflow states;
- 005D3 validates direct-update origin, size, SHA-256, package/version, SDK/ABI
  and signing-certificate continuity before installer handoff;
- 005D4 writes only closed Android lifecycle/permission/network/power/watchdog/
  updater outcomes to a bounded app-private no-backup journal;
- the active client has no Linux shell/daemon/package lane. Core contains
  portable Linux-capable dependencies, but that is not client beta evidence.

## Authority decisions

1. The active client owns host integration and canonical platform
   architecture. The platform repository owns only this execution/evidence
   record and cross-repository release gates.
2. The Core owns the embeddable engine ABI. A Windows service or Linux daemon
   may host that ABI, but it cannot fork or replace the Core truth.
3. Windows has three distinct trust domains: ordinary UI, privileged service,
   and installer/repair. UI activation is not privileged service IPC and
   cannot satisfy `REL/SEC-001` by itself.
4. The Windows UI never receives arbitrary privileged file, path or shell
   execution. The service accepts only closed commands with bounded typed
   arguments and server-side authorization.
5. No staged service cutover may silently fall back to elevating the full UI.
   Until the service lane is locally proved and packaged, the existing working
   path remains isolated behind the implementation branch; removal happens in
   the same slice that proves its replacement.
6. Network ownership has one writer. Once the Windows service owns Core/TUN,
   routes, DNS, proxy and kill-switch mutation, Dart FFI cannot mutate those
   resources in parallel.
7. Android refactoring is behavior-preserving except for the explicitly safer
   privacy, MTU, counter, permission and updater outcomes. The service remains
   the Android `VpnService` lifecycle authority.
8. Direct and store Android variants must retain an intentional compatible
   package/signing strategy. A flavor split cannot invent an upgrade path
   without signing-owner evidence.
9. Linux is feature-gated and absent from public platform facts until its own
   signed package and matrix reach candidate proof. A compiling daemon or UI
   is at most implementation evidence.
10. Platform lifecycle events may expose bounded seams required to test these
    components. Release-wide envelopes, error catalog, bundle/export, ingest,
    retention and support console remain `WO-006`.

## Dependency order

```text
005A architecture + Windows per-user activation/startup
  └─ 005B Windows service identity + authenticated typed IPC
       └─ 005C single-writer Core/network transaction + recovery journal
            └─ Windows clean-VM candidate matrix (WO-013)

005D1 Android privacy + safe MTU
  └─ 005D2 session-scoped work + Core/TUN counters
       └─ 005D3 direct/store updater identity boundary
            └─ 005D4 private operational journal + host producers
                 └─ Android device/store candidate matrix (WO-013)

005E Linux decision + daemon/UI/package foundation
  └─ Linux clean-host beta matrix (005F/WO-013)
```

Windows, Android and Linux implementation branches can progress independently
after this contract, but Gate C cannot close until every required branch and
its exact evidence close.

## WO-005A — Platform contract, Windows singleton and startup semantics

Repository: active client; platform index/evidence only.

Deliver:

- canonical client platform-privilege contract naming owners, trust domains,
  command boundaries, transaction stages and rollout/rollback rules;
- one per-user-session UI mutex with deterministic first/second-instance
  behavior;
- one versioned activation frame for `show` and bounded acquisition
  continuation, with exact lengths, closed command identifiers and rejection
  of unknown/malformed data;
- the same activation channel for normal second launch and acquisition URI;
- explicit `--startup` mode: install tray, keep the window hidden, do not
  auto-connect merely because Windows started the process;
- the Run value includes `--startup` and its readback requires the exact
  command;
- `--connect` remains only a migration input until 005B removes full-process
  elevation; it cannot be emitted by login startup;
- focused pure protocol, source-contract and Flutter behavior tests.

Acceptance:

- a second ordinary launch exits after delivering typed `show` to the first
  UI instance;
- a second acquisition launch delivers the bounded URI through the same frame;
- malformed, oversized, unterminated or future-version frames are rejected;
- mutex names are scoped to the current user session, not globally shared
  across interactive users;
- startup mode produces tray-only UI and no UAC or automatic connect request;
- activation raises the existing UI without granting privileged authority;
- source/build tests pass; interactive focus behavior remains
  `MANUAL_OWNER_TEST` until run on the exact Windows candidate.

Index rules:

- `REL/WIN-001` can reach `I3` only after protocol/unit/build checks pass;
- `REL/WIN-005` can reach at most `I2` before the service-readiness and
  network-availability portions are proved in 005B/005C;
- `REL/SEC-001` does not advance from activation work alone.

Rollback: remove the mutex/protocol source and restore the prior Run command.
This rollback may restore duplicate launches but must not alter runtime or
network state.

## WO-005B — Windows privileged control plane and authenticated IPC

Repositories: active client and Core compatibility; platform evidence only.
Dependency: 005A.

Deliver:

- a separately built `pokrov_service.exe` SCM service with its own product
  identity and singleton lifecycle;
- installer/repair-owned service registration; the UI cannot self-install or
  grant itself service rights during ordinary connect;
- local named-pipe protocol with explicit protocol/capability negotiation,
  bounded frame size, closed request/response/event schemas, correlation ID,
  deadline, cancellation and replay-resistant operation nonce;
- pipe ACL restricted to LocalSystem, Administrators and the installation
  owner's SID; server-side caller-token/SID verification on every connection;
- allowlisted status, connect, disconnect, cancel, recover and diagnostic-state
  commands; no arbitrary command, shell, URL or caller-selected privileged
  path;
- service readiness and compatibility states surfaced to the ordinary UI;
- fail-closed behavior for unknown versions/capabilities, caller mismatch,
  expired deadline, duplicate nonce, malformed frame and unauthorized command;
- local isolated protocol/auth tests using synthetic SIDs/tokens where Windows
  APIs permit; actual SCM/install-owner tests remain clean-VM gates;
- removal of `relaunchElevated`, `ShellExecuteW(..., "runas", ...)`,
  `--connect` elevation handoff and whole-Flutter elevation only when the UI
  connects through the proved service path.

Acceptance:

- ordinary UI startup and steady state are non-elevated;
- a non-admin user with the allowed installation-owner identity can request
  allowlisted runtime operations but cannot widen service authority;
- another local user/session, malformed client or unsupported protocol fails
  before privileged mutation;
- UI crash does not stop the service-owned active session; service crash is
  detected and enters recovery, never a false green state;
- Core ABI compatibility is checked before setup and no caller-controlled raw
  profile secret is written to logs or evidence;
- `REL/WIN-002` and `REL/SEC-001` reach `I3` only after the old elevated UI path
  is absent and focused local tests/build pass. Clean-VM/service-install proof
  is still below `I4`.

Rollback: retain an installer-controlled previous service binary and protocol
version for package rollback. There is no runtime fallback to an elevated UI.

Execution is split without weakening that acceptance:

- `005B1` builds and locally proves the service identity, SCM lifecycle
  skeleton, protocol, pipe ACL, caller authentication, session/deadline/replay
  controls and fail-closed `runtime_not_owned` response. It does not package or
  install the service and cannot close privilege migration.
- `005B2` adds the real UI client, installer/repair ownership, service
  compatibility/readiness presentation and service-hosted Core control. It
  removes the old full-process elevation only when the replacement passes.

## WO-005C — Windows single-writer transaction and crash recovery

Repositories: active client and Core compatibility; platform evidence only.
Dependency: 005B.

Deliver:

- one service-owned runtime coordinator and idempotent stop path;
- an atomic, versioned recovery journal with only the data needed to restore
  prior DNS, routes, proxy, Wintun adapter ownership, policy/firewall rules,
  session identity and committed phase;
- closed stages `clean`, `snapshotted`, `core_started`, `network_applied`,
  `verified`, `committed`, `rolling_back` and `recovered`;
- write-through before every external mutation and idempotent staged rollback
  after failure, service restart or reboot;
- current DNS plus selected-outbound egress probes before commit;
- generation/session fencing so stale UI or service callbacks cannot mutate a
  replacement session;
- bounded lifecycle evidence seams for service/SCM, adapter, route, DNS,
  sleep/resume/reboot and rollback without raw configuration or browsing data;
- fault-injection tests for every stage, repeated disconnect, partial journal,
  service restart and UI crash.

Acceptance:

- one coordinator owns Core/TUN/route/DNS/proxy mutation;
- stop and rollback are safe when called repeatedly or after partial progress;
- no stage reports verified/connected before DNS and selected-outbound egress
  proof;
- a corrupted/future journal fails closed and is preserved for bounded
  recovery, never silently discarded before network safety is established;
- `REL/WIN-004` may reach `I3` after local fault tests; physical reboot,
  uninstall-while-connected and clean-host route/DNS restoration stay `I4`
  candidate gates.

Rollback: the installer restores the previous service only after the current
service reaches `clean` or completes its compatible rollback routine.

## WO-005D1 — Android notification privacy and safe MTU

Repository: active client only.

Deliver:

- foreground notification lockscreen visibility `PRIVATE`;
- generic default text that exposes no country, selected route, application
  list, endpoint or speed on the lockscreen;
- detailed route/stats remain inside authenticated app UI only; any future
  optional notification detail needs an explicit persisted privacy setting;
- one validated MTU selector with a conservative Android default, bounded
  profile range and platform-interface ceiling;
- removal of MTU `9000` fallback and tests for missing, malformed, too-low and
  too-high input.

Acceptance:

- notification construction is privacy-safe in connecting, connected,
  reconnecting and failed states;
- no UID speed sample is required to render the notification;
- the selected MTU is deterministic and never `9000` without explicit later
  platform proof;
- `REL/AND-001` and `REL/AND-003` can reach `I3` after focused JVM and host
  tests; physical OEM/lockscreen behavior remains a device gate.

Rollback: restore the prior selector only with evidence that its value is safe;
privacy rollback to public route/speed disclosure is prohibited.

## WO-005D2 — Android session-scoped concurrency and tunnel counters

Repositories: active client and Core compatibility if a counter capability is
missing.
Dependency: 005D1.

Deliver:

- one session lifecycle owner with generation ID and parent cancellation;
- scoped child work for probes, network monitoring, latency, update metadata
  and stats, each with deadline and terminal cancellation;
- removal of raw unmanaged bridge threads from active lifecycle operations;
- Core/TUN byte counters with explicit unavailable/reset/overflow behavior;
- no `TrafficStats.getUidRxBytes/getUidTxBytes` connection-speed truth;
- late-callback, stop/reconnect, process-kill and counter-reset tests.

Acceptance:

- stopping a session cancels all owned work and a late result cannot mutate a
  new generation;
- counters represent the active tunnel/Core session, not unrelated app/API
  traffic;
- failure or absence of the counter capability renders stats unavailable and
  never substitutes UID totals;
- `REL/AND-002`, `REL/AND-004` and `OBS/OBS-040` can reach `I3` only after
  focused tests and a host build pass. Long-running/device evidence remains
  below `I4`.

Rollback: counter display may be disabled; it may not fall back to UID-wide
traffic. Structured jobs can roll back only to a generation-fenced executor
implementation, not unmanaged fire-and-forget threads.

## WO-005D3 — Android direct/store update identity boundary

Repository: active client; platform release metadata only if exact flavor
artifacts become part of a later candidate contract.
Dependency: 005D2.

Deliver:

- explicit `directRelease` and `storeRelease` build variants;
- `REQUEST_INSTALL_PACKAGES` and in-app installer only in direct builds;
- store builds use a store-managed update surface and cannot invoke the direct
  APK installer;
- fixed package/application ID and signing-continuity policy recorded without
  committing keys or certificate private material;
- before installer handoff, parse the completed APK and validate expected
  package ID, signing-certificate digest, minimum SDK and supported ABI in
  addition to channel, origin, monotonic version, size and SHA-256;
- reject redirect-origin drift, signer rotation without an authorized lineage,
  downgrade, incompatible SDK/ABI and malformed APK;
- atomic cache/download behavior and bounded user-visible source/version/size;
- sanitized fixtures and negative tests; real production signing identity and
  store behavior remain operator/device gates.

Acceptance:

- merged store manifest contains no install-packages permission;
- store code cannot reach the direct installer;
- a package/signer mismatch fails before an installer intent;
- cache reuse repeats identity validation, not only SHA/size validation;
- `REL/AND-005` and `REL_DOD/DOD-05` can reach `I3` after variant manifest/code
  tests; `REL/UPD-001` reaches `I3` only with parsed APK identity fixtures and
  host tests, and needs exact signed-candidate proof for `I4`.

Rollback: disable direct update and use manual canonical download. Never bypass
package or signer validation to preserve updater availability.

## WO-005E — Conditional Linux beta foundation

Repositories: active client and Core; platform public facts only after the
beta gate is proved.
Dependency: 005A contract; independent of Windows implementation.

Decision gate before implementation:

- confirm supported distro/version, init system, desktop session, network
  manager, package and policy matrix;
- choose one IPC authority: D-Bus with peer credentials/polkit, or a Unix
  socket with peer credentials plus an equally explicit policy owner;
- choose DEB-first or another single package lane. RPM/AppImage cannot be
  claimed from source compatibility alone.

Deliver after the decision is recorded:

- non-root Flutter UI and systemd-owned privileged `pokrov-daemon`;
- authenticated peer identity and allowlisted typed daemon protocol;
- NetworkManager-first transaction with explicit resolved/networkd/nft
  adapters only for chosen matrix entries;
- IPv4/IPv6 route/DNS fail-closed behavior and a recovery journal equivalent
  in guarantees, not necessarily format, to Windows;
- ownership/mode checks proving no world-writable socket, journal, config or
  secret;
- package install/upgrade/rollback/uninstall scripts and local namespace/VM
  tests;
- bounded journald lifecycle seams and sanitized UI status only. Broad support
  export remains `WO-006`.

Acceptance:

- UI runs non-root and cannot directly mutate routes/DNS/TUN;
- daemon rejects an unauthorized peer and unknown command/version;
- package removal restores owned network state;
- source/unit/namespace evidence advances `REL/LNX-001` at most to `I3`;
- `REL_DOD/DOD-06` and public beta require signed package plus the named clean
  distro/network matrix at `I4`. Until then Linux remains absent from public
  product/platform facts.

Rollback: disable the feature flag, stop the daemon through its idempotent
rollback and uninstall the package. Do not leave UI-only AppImage copy
claiming VPN support.

## WO-005F — Platform matrices and Gate C

Dependencies: 005B–005E as applicable. Candidate proof is executed with
`WO-013`, not manufactured by local source tests.

Required retained evidence:

- Windows 10/11 clean VM, standard/admin users, install/update/rejected
  downgrade/uninstall, second launch, startup, service/UI/Core crash,
  sleep/resume/reboot, network changes, IPv4/IPv6/dual-stack, repeated
  connect/disconnect, update/uninstall while connected and verified TUN/DNS;
- Android supported API range and OEM matrix, lockscreen/privacy, direct/store
  manifests, exact signer/package updater rejection, Wi-Fi/mobile, captive
  portal, IPv6, battery restrictions, always-on/lockdown, process kill/reboot
  and long session;
- Linux only if 005E proceeds: every named distro/network-manager/package lane,
  non-root UI, peer authorization, IPv4/IPv6, suspend/resume, daemon/UI crash,
  upgrade/rollback/removal and network restoration;
- exact candidate, artifact digest, origin and evidence path on every result.

`REL_GATE/GATE-C` cannot pass from compilation or unit tests. It reaches `I4`
only when the exact candidate matrix is retained; stable release proof remains
`I5` under `WO-013`.

## Observability boundary

`OBS/OBS-031..046` are platform-specific producers, not permission to build a
second logging system. WO-005 may implement only:

- closed lifecycle event identifiers required by local platform tests;
- correlation/session/generation identifiers that contain no secret;
- bounded, non-blocking local sinks already owned by the client/OS;
- redaction-safe status summaries crossing service/daemon boundaries.

Envelope unification, error taxonomy, planted-secret checks, encrypted bundle,
ingest, operator console, retention, alerts and playbooks remain WO-006. A
producer seam does not advance those broader rows.

## Closed write scope — 005A

Client (`codex/1.2.0-release-v2`):

- Windows runner activation protocol/mutex files and CMake registration;
- Windows shell startup-mode behavior and focused tests;
- exact Run-entry code and focused source contract tests;
- one canonical platform privilege/runtime architecture document plus client
  docs registry/readiness reconciliation.

Platform (`codex/1.2.0-phase00`):

- this WO, wave index and only ledger/evidence rows actually proved.

Core has no 005A write scope.

## First active verification — 005A

```powershell
dart format apps/windows_shell/lib apps/windows_shell/test
flutter test apps/windows_shell/test
flutter analyze apps/windows_shell
flutter build windows --debug -t apps/windows_shell/lib/main.dart
powershell -ExecutionPolicy Bypass -File .\test\docs-contract.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\validate-seed.ps1 -PlatformRoot C:\path\to\platform -CoreRoot C:\path\to\POKROV-core
git diff --check
```

The debug build proves compilation only. Interactive focus, login startup,
UAC absence, service behavior, clean-host runtime, signing and exact-candidate
checks retain their explicit manual/not-requested labels.

## 005A closure evidence — 2026-08-21

Result: `COMPLETE_I3` for the per-user singleton and typed activation slice;
`IMPLEMENTED_I2` for login startup semantics because service readiness and
network-aware auto-connect do not exist yet. This is not service IPC,
clean-machine or candidate proof.

- The client canonical owner is
  `docs/architecture/platform-privilege-runtime-contract.md`. It separates UI
  activation from the future privileged service IPC and records Windows,
  Android and conditional Linux trust/lifecycle boundaries.
- Windows owns `Local\\POKROV.UI.<session-id>` for the first UI process. Later
  ordinary and acquisition launches use one versioned, closed activation frame
  and do not create another UI.
- Frame v1 has a fixed 16-byte header, maximum 512-byte payload and only `show`
  or `acquisition_continue`. The decoder rejects future/unknown commands,
  wrong lengths, trailing bytes, non-zero reserved data, another URI prefix
  and control characters.
- The product-specific window class is `POKROV_WINDOWS_UI_WINDOW_V1`; a valid
  activation restores/focuses that window. Activation grants no service or
  privileged authority.
- The exact per-user Run value now adds `--startup`. Startup keeps the window
  hidden behind the normal tray and suppresses legacy `--connect` even if both
  arguments appear. An acquisition continuation intentionally overrides hidden
  startup so the user can complete the flow.
- Windows debug build: `PASS`. Native CTest:
  `pokrov_activation_protocol`, `1/1 PASS`. A local debug smoke started one
  hidden `--startup` process, launched a second ordinary process, observed the
  second exit `0` and exactly one surviving first PID, then stopped the
  task-owned debug process.
- Focused Windows Flutter tests: `17 passed`; `flutter analyze`: no issues.
  Full client gate: app shell `326 passed`; runtime engine `51 passed`, `1`
  real-DLL test skipped; Android Flutter `8 passed`; Windows `17 passed`;
  Android Gradle `BUILD SUCCESSFUL`.
- Cross-repository seed/release-handoff v2, client CI contract and client docs
  contract: `PASS`. Platform documentation tests: `30 passed`; platform
  context and link checks: `PASS`; client/platform `git diff --check`: `PASS`
  at the closure review.
- Interactive focus, actual login startup, service/SCM, clean VM, UAC capture,
  signing, artifact and exact-candidate checks remain `MANUAL_OWNER_TEST` or
  `NOT_REQUESTED`; no candidate was created.
- The current full-process `runas --connect` path remains present until 005B
  supplies and proves a service replacement. At 005A closure time,
  `REL/WIN-002` and `REL/SEC-001` therefore remained `I0`, and `REL/WIN-005`
  was capped at `I2`.

## 005B1 checkpoint evidence — 2026-08-21

Result: service/authentication protocol `IMPLEMENTED_I2`; privilege migration
only `BASELINED_I1`. This checkpoint is not an installed service, UI cutover,
Core/network ownership, clean-VM or candidate proof.

- Added a separately built `pokrov_service.exe` with SCM
  start/stop/shutdown state handling. Production startup fails closed unless a
  valid installation-owner SID exists in the protected HKLM service key.
- The production pipe name is fixed. Its protected DACL grants only
  LocalSystem, Administrators and the installation owner; it grants neither
  Everyone nor Anonymous.
- After reading only a bounded hello, the service impersonates the pipe client,
  reads the caller token and accepts only LocalSystem, an enabled Administrator
  or the exact installed-owner SID before any request.
- Protocol v1 has an 80-byte fixed header and 512-byte maximum sanitized body.
  It has closed frame kinds, commands and statuses; capability negotiation,
  correlation ID, a cryptographically random session token, operation nonce
  and a deadline no more than five minutes ahead.
- Unknown frames fail decoding. Session mismatch, expired/far deadline and
  duplicate nonce fail closed. The replay set retains 256 nonces and then
  refuses more work for that session instead of evicting replay evidence.
- Only status is implemented and returns `service_bootstrap`. Every allowlisted
  runtime command returns `runtime_not_owned`; the service cannot mutate Core,
  routes, DNS, proxy or files in this slice.
- Debug builds alone expose a one-client test entrypoint. A real local secured
  pipe integration test proved owner access, capability intersection, random
  session issuance, bounded status and duplicate-nonce rejection. Release
  builds do not include the debug entrypoint.
- Windows debug build: `PASS`; native CTest `4/4 PASS` (activation, service
  protocol, security and secured-pipe integration); Windows Flutter tests:
  `18 passed`; analyze: no issues.
- The service target is deliberately not installed or copied to the bundle;
  current release metadata still says no helper. No SCM registration, UAC,
  clean-VM, signing, package or exact-candidate test was run.
- The UI still uses direct desktop FFI and retains `runas --connect`. Thus
  `REL/WIN-002` advances only to `I1`, `REL/SEC-001` only to `I2`, and the old
  elevated path remains a stop-ship for completion of 005B2.

## 005B2 UI status-client checkpoint — 2026-08-21

Result: authenticated service discovery/readiness presentation
`IMPLEMENTED_I2`; Core/installer/privilege cutover remains active. This is not
service-hosted Core ownership, SCM installation, network mutation, clean-VM or
candidate proof.

- The ordinary UI runner now opens only the fixed production pipe and verifies
  the server before protocol use: the pipe server process token must be exact
  LocalSystem and its image must be the sibling `pokrov_service.exe`.
- The UI client negotiates protocol/capabilities, uses cryptographically random
  correlations and operation nonces, binds status to the issued session token
  and maps all failures to a closed five-state readiness result.
- The Flutter bridge exposes only typed booleans and a closed state name. Dart
  rejects contradictory or malformed native maps as `unavailable`; unsupported
  hosts do not invoke the Windows channel.
- Windows Debug build: `PASS`; native CTest `4/4 PASS`; Windows Flutter tests:
  `20 passed`; analyze: no issues.
- The service is still not bundled or installed, reports `service_bootstrap`,
  and does not host Core. The UI still uses direct desktop FFI and retains
  `runas --connect`; `REL/WIN-002` therefore remains `I1` and `REL/SEC-001`
  remains `I2`.

## 005B2 Core/installer cutover closure — 2026-08-21

Result: Windows privilege/runtime cutover `COMPLETE_I3` for local source,
build and test behavior. SCM installation, a real service-owned tunnel,
clean-user matrix, signing and exact-candidate proof were not run and do not
reach `I4`.

- The Windows runtime factory now selects `RuntimeLane.windowsService`.
  Ordinary UI calls use only the authenticated closed service channel; macOS
  retains direct desktop FFI.
- The service runtime loads only the exact sibling `pokrov-core.dll`, checks
  desktop ABI 2 and the optional closed capability descriptor, and owns Core
  setup/start/stop independently of UI pipe lifetime.
- Materialized profile bytes are bounded, never supplied as a caller path,
  written under protected `%ProgramData%\POKROV\ServiceRuntime`, flushed and
  atomically promoted from `managed-profile.pending` to
  `managed-profile.json` before Core security/start calls.
- After Core starts, a WinHTTP probe bypasses user/system proxy settings and
  requires the owned HTTPS endpoint to return exact `204` plus
  `X-Pokrov-Egress-Probe: pokrov-authenticated-egress-v1`. Failure stops Core,
  returns to `config_staged` and exposes only
  `core_egress_probe_failed`; `running`, `dns_ready` and egress proof cannot
  disagree at the UI parser.
- The bundle requires `pokrov_service.exe`. Installer source is machine-wide,
  captures the original user's SID, writes protected HKLM service ownership,
  stops/configures/starts the fixed SCM service and deletes it on uninstall.
  Portable ZIP is unsupported. Autostart and `pokrov://` registration remain
  per-user UI responsibilities.
- `TokenElevation`, `ShellExecuteW(..., "runas", ...)`, the elevated
  `--connect` continuation, permission sheet and selectable per-user
  system-proxy lane were removed. Saved `systemProxy` state migrates to the
  service/TUN lane.
- Windows Debug native build: `PASS`; CTest: `5/5 PASS`; Windows Flutter tests:
  `20/20 PASS`; focused app-shell routing/state/UI tests: `164/164 PASS`;
  runtime-engine tests: `52 PASS`, `1` exact-DLL test skipped because the
  explicit real-Core root was not supplied; whole-client `flutter analyze`:
  no issues.
- Cross-repository seed validation passed with explicit client/platform/Core
  worktree roots. Inno compilation and unsigned local package generation
  passed using a dummy test-only emergency public key for syntax validation.
  The output still carried local app version `1.1.6+29`; it was not signed,
  installed, promoted or treated as a 1.2.0 candidate.
- `REL/WIN-002`, `REL/WIN-005` and `REL/SEC-001` advance to `I3` under their
  local acceptance rules. `REL/WIN-004` remains `I0`; 005C recovery and all
  candidate/clean-host gates remain open.

## 005C2 recovery coordinator closure — 2026-08-21

Result: Windows shutdown and route/DNS recovery coordinator `COMPLETE_I3` for
local source and injected fault behavior. No installed SCM service, live
network mutation/restoration, physical crash/reboot, uninstall while
connected, exact rebuilt DLL or release candidate was tested.

- The service owns `POKROV_RECOVERY_V1`, with atomic pending-file replacement,
  `FlushFileBuffers`, `MOVEFILE_WRITE_THROUGH`, a random 128-bit generation and
  closed stages from `clean` through `recovered`.
- A bounded, hex-encoded `POKROV_NETWORK_V1` payload stores only the prior
  state of the exact service-owned Windows interface. Core working source now
  names that interface `POKROV`; published Core `1.0.3` hashes predate this
  source change and remain historical evidence only.
- Before Core start, the service snapshots the owned adapter GUID, IPv4/IPv6
  IP-interface fields, unicast addresses, routes and DNS settings. The current
  service/TUN lane does not mutate WinINET proxy. Strict-route firewall rules
  use Core's dynamic WFP session and do not leave persistent policy state for
  the journal to duplicate.
- Rollback first persists `rolling_back`, then stops Core, deletes current
  owned-adapter routes/addresses/DNS, restores the captured interface state and
  only then advances through `recovered` to `clean`. A restart resumes the same
  sequence. Corrupt, partial and future journals are preserved and fail closed.
- A failed stop, adapter restore or journal completion enters
  `recovery_required`: `running`, DNS and egress are false, `can_connect=0`,
  profile mutation is refused and a repeated disconnect retries rollback.
- Injected tests cover snapshot failure, every persisted connect stage, Core
  start/egress failure, repeated disconnect, Core-stop failure, network-restore
  failure, journal-completion failure, service-object restart, partial journal
  and future journal. Native Debug build and CTest `5/5`, Windows Flutter
  `20/20`, client docs contract, whole-client analyze and the full Core test
  gate passed.
- `REL/WIN-004` advances to `I3` under the WO acceptance rule. Exact-candidate
  SCM install, live route/DNS restoration, crash/reboot and
  uninstall-while-connected remain `I4` gates. Secret-free lifecycle
  breadcrumbs for SCM/adapter/route/DNS/power/rollback continue in 005C3 and no
  observability row advances from this checkpoint.

## 005C3 privileged lifecycle evidence closure — 2026-08-21

Result: Windows privileged producer seams `COMPLETE_I3` for local source,
strict build and closed-format behavior. This is not an installed-service,
physical power-cycle, real network, crash-dump, support-upload or exact
candidate result.

- Privileged records are separate from the user-space
  `pokrov-runtime-events.jsonl` journal. `POKROV_SERVICE_EVENT_V1` writes only
  to `service-events.v1.log` and one previous file under the protected
  `%ProgramData%\POKROV\ServiceRuntime` root. Its System/Administrators DACL is
  protected and inheritable by child files.
- Each retained file is limited to 256 KiB. SCM, IPC and runtime producers
  enqueue at most 4096 closed records and perform no file I/O; one background
  writer preserves order, flushes records and rotates with
  `MOVEFILE_WRITE_THROUGH`. Shutdown drains the queue before reporting
  `SERVICE_STOPPED`.
- The wire has timestamp, sequence, closed event/outcome/command/status and an
  opaque request correlation or boot-epoch identifier. Its API cannot accept
  a request body, free-form error, profile, token, nonce, endpoint, URL, path,
  provider response or browsing destination.
- SCM events cover start-pending, running, stop, shutdown, preshutdown,
  stopped, suspend and resume. A FILETIME-minus-uptime boot marker stays stable
  across service restarts in one Windows boot and changes after a later boot.
- Authenticated IPC logs closed request/response spans with command, status and
  correlation ID only. Runtime events cover network snapshot, Core/Wintun,
  owned adapter, routes, DNS, egress, commit, Core stop, network restoration
  and rollback completion.
- Strict Windows Debug build passed. Native CTest passed `6/6`, including
  bounded rotation, version/field count, forbidden-field absence, boot/request
  correlation and runtime emission. Windows Flutter passed `20/20`; focused
  service source contract passed `4/4`; `flutter analyze` reported no issues;
  client docs contract passed.
- `OBS/OBS-031`, `OBS-032`, `OBS-033`, `OBS-034` and `OBS-036` advance to local
  `I3`. `OBS-035` remains `I0`: no Windows crash-profile or dump policy was
  added. WO-006 still owns envelope unification, error taxonomy, planted-secret
  gates, bundle/upload, ingest, retention, alerts and operator presentation.
- Exact-candidate ACL behavior, installed SCM lifecycle, live Wintun/network
  ordering, sleep/resume/reboot and crash recovery remain `I4` gates. No
  candidate, service install, signing, publication or production mutation was
  performed.

## 005D1 Android privacy and safe MTU closure — 2026-08-21

Result: Android notification privacy and MTU selection are `COMPLETE_I3` for
local source, JVM/Flutter behavior and canonical client contracts. No physical
device, OEM lockscreen, signed release build or exact candidate was tested.

- Foreground notification content is a closed generic state for connecting,
  connected, reconnecting and failed operation. The channel, notification and
  generic public version are private; country, route, selected apps, endpoint,
  WARP and speed are absent.
- UID-wide `TrafficStats` sampling and periodic notification refresh were
  removed. Detailed route/stats remain app-only; missing Core/TUN counter truth
  stays queued in 005D2 and no observability counter row advances here.
- Legacy `pokrov_system_surfaces` country/speed/route booleans default false,
  any retained true value migrates to false, native writes ignore attempts to
  re-enable detail and the authenticated app explains the privacy boundary
  without detail toggles.
- Managed-profile MTU accepts only integers in `1280..1500` and otherwise uses
  `1280`. The Android host validates every TUN inbound again, caps to a usable
  active-interface MTU and applies the same policy at descriptor creation.
- Android focused privacy/MTU/security tests and full JVM suite passed
  `147/147`; the two affected app-shell suites passed `230/230`; app-shell
  `flutter analyze` and the client docs contract passed. Client
  `git diff --check` reported no whitespace errors.
- `REL/AND-001` and `REL/AND-003` advance to `I3`. Physical OEM/lockscreen,
  live network/PMTU, endurance, signing and exact-candidate behavior remain
  `I4` gates.

## 005D2 Android session scope and Core/TUN counters closure — 2026-08-21

Result: Android session-scoped concurrency and Core/TUN live counters are
`COMPLETE_I3` for local source, JVM/Flutter behavior and canonical client
contracts. No physical process kill/restart, long-run sampling, signed release
build or exact candidate was tested.

- The VPN service owns a bounded generation-scoped parent for the Core status
  stream and selected-egress probe. Stop, runtime replacement, failed startup
  and service destruction fence callbacks, interrupt JVM work, disconnect the
  Core command client and clear session stats.
- The Flutter host bridge owns a separate bounded Activity lifecycle scope for
  verified update download, latency, location-variant and installed-app work.
  Flutter-engine cleanup cancels the scope, and updater verification checks
  cancellation before reads and before cache commit.
- Core `CommandStatus` supplies active-tunnel uplink/downlink totals at a
  one-second interval. Monotonic rate calculation records unavailable,
  warming, available, reset and overflow explicitly; counter decrease does not
  become a spike. `TrafficStats` and any UID-wide fallback remain absent.
- Native state accepts only the active session generation. Focused tests cover
  cancellation, interruption, late generation updates, stop invalidation,
  unavailable capability, reset, overflow and cancelled update verification.
  Source contracts bind service/Activity destruction to their parent scopes.
- Android host compilation passed; focused Android checks passed `51/51` and
  the full Android JVM suite passed `155/155`. Runtime-engine passed `52/52`
  with one exact-Core backtest honestly skipped because its external artifact
  was not supplied; app-shell passed `325/325`; both Flutter packages analyze
  clean; client docs contract and `git diff --check` passed.
- `REL/AND-002`, `REL/AND-004` and `OBS/OBS-040` advance to `I3`. Real process
  death/restart, network-switch endurance, live counter continuity/reset,
  physical devices, signing and exact-candidate behavior remain `I4` gates.

## 005D3 Android direct/store updater closure — 2026-08-21

Result: Android distribution/update authority is `COMPLETE_I3` for local
source, flavor builds, APK inspection and sanitized identity behavior. No
production-signed candidate, physical upgrade/downgrade or Play-console flow
was tested.

- Gradle now produces explicit `directRelease` and `storeRelease` variants
  from one canonical application ID. `REQUEST_INSTALL_PACKAGES`, the private
  `FileProvider`, GitHub downloader and package-installer intents exist only in
  direct source/manifest. Store source has no APK/network/cache path and opens
  only the exact package listing in `com.android.vending`.
- Direct request metadata is bounded to the configured stable channel, a
  canonical GitHub release URL, semantic version, 256 MiB maximum, exact size
  and SHA-256. Redirects remain bounded to GitHub-owned HTTPS asset hosts.
- The completed archive is parsed before atomic cache promotion and again
  before any permission/settings/installer intent. It must match application
  ID, requested version, increasing `versionCode`, minimum SDK, device ABI, the
  pinned production signer and continuity from the installed signer through
  Android's verified certificate history. Mismatch, downgrade, malformed APK,
  incompatible SDK/ABI and unauthorized rotation fail closed.
- Cache reuse repeats size, digest and full APK identity. Flutter sends channel
  and version across the method channel, maps store handoff explicitly and
  shows only bounded official-source/version/size/progress copy.
- Full Android JVM passed `161/161` separately for direct and store. App-shell
  passed `326/326`, Android-shell `8/8`, runtime-engine `53` with one explicit
  exact-Core artifact skip, Windows-shell `20/20`, and the canonical client
  wrapper passed. Both affected analyzers, client docs/cross-repo seed contract
  and PowerShell parsing passed.
- Real direct/store debug APKs retained the same package ID. `aapt` proved the
  direct permission/provider present and both absent from store; bytecode
  inspection proved store references Google Play and lacks direct
  FileProvider/package-installer references. Debug APKs are ignored local
  evidence, not release artifacts.
- `REL/AND-005`, `REL/UPD-001` and `REL_DOD/DOD-05` advance to `I3`.
  Production signing, same-lineage release upgrade, hostile-candidate device
  tests, Play behavior and exact-candidate evidence remain `I4` gates.

## 005D4 Android private operational journal closure — 2026-08-22

Result: Android release-safe platform diagnostics are `COMPLETE_I3` for local
source, closed-schema behavior, both distribution flavors and debug host
builds. No physical-device journal, controlled ANR, production-signed upgrade
or exact candidate was tested.

- A single background writer stores current plus previous 256 KiB JSONL files
  below the app-private no-backup directory. Its 256-record queue cannot block
  VPN/UI threads and carries a numeric dropped-record count forward.
- The record has no arbitrary string input: only time, sequence, optional
  positive generation and closed event/outcome enums. Message, URL, endpoint,
  interface, package, profile, token, exception and stack fields do not exist.
- Producers cover VPN service/TUN and VPN/notification permission lifecycle,
  default-network callbacks, Doze, app-standby/background restriction, a
  rate-limited stack-free main-thread watchdog, direct APK identity decisions
  and bounded installer/store handoff.
- Direct/store JVM suites each passed `172/172`; both debug flavor builds,
  client docs and explicit-root cross-repository seed validation passed.
  Retained `artifacts/releases/**` remained byte-untouched.
- `OBS/OBS-037`, `OBS-038`, `OBS-039`, `OBS-041` and `OBS-042` advance from
  `I0` to local `I3`. Device delivery/permissions, hang injection, long-run
  rotation/overhead and signed hostile-upgrade evidence remain `I4` gates.

Full evidence and rollback are in `WO-005D4-android-operational-journal.md`.

## 005E Linux decision closure — 2026-08-21

Decision: `NOT_SHIPPED_IN_1.2.0`. Linux remains a conditional future beta and
is absent from 1.2.0 public product/platform facts.

- No supported distro/version, desktop session, init/network-manager matrix,
  IPC policy authority or single package lane has been selected and proved.
  Claiming a daemon, DEB/RPM/AppImage or public beta from generic Flutter/Core
  compatibility would violate the decision gate.
- No Linux UI/daemon/package implementation is added in this wave. The target
  contract remains non-root UI plus a systemd-owned typed authenticated daemon,
  NetworkManager-first transaction/recovery and a named clean-distro matrix.
- `REL/LNX-001` and `REL_DOD/DOD-06` remain `I0`; no source compatibility is
  credited as a shipped or locally proved Linux lane. Reopening requires an
  explicit supported-matrix owner decision and a new bounded implementation
  slice.

## 005C4 closure: safe Windows crash profile

- The ordinary UI and SCM service install the same fail-open native crash
  contract under separate protected roots. The closed record contains only
  FILETIME, process role, exception code and at most 32 allowlisted
  module-relative RVAs. Unknown modules are omitted.
- No minidump, WER registry policy, symbol/path lookup, absolute address,
  register, exception text, profile/config, network material or heap capture is
  present. One current and one previous record are retained per process.
- Debug and Release builds pass; canonical Debug CTest passes `7/7`, focused
  Release crash-profile CTest passes `1/1`, Windows Flutter passes `21/21`,
  analyze and the explicit-root client seed gate pass.
- `OBS/OBS-035` advances from `I0` to local `I3`. Controlled crashes, file/DACL
  readback, SCM restart and network restoration remain exact-candidate `I4`
  evidence. No crash, service install, registry mutation, signing, deploy or
  promotion was performed.

## Ledger ownership

WO-005 owns only:

- `REL/WIN-001`, `REL/WIN-002`, `REL/WIN-004`, `REL/WIN-005`,
  `REL/SEC-001`;
- `REL/AND-001..005`, `REL/UPD-001`;
- `REL/LNX-001`;
- `REL_GATE/GATE-C`, `REL_DOD/DOD-05`, `REL_DOD/DOD-06`;
- platform-producer portions of `OBS/OBS-031..046` when concrete code and
  tests exist.

No row advances from this plan alone. `I3` means verified local behavior in the
named slice. `I4` requires the exact candidate/environment matrix. `I5`
requires the final promoted release evidence.

## Exit condition

WO-005 is complete locally only when Windows no longer elevates the full UI,
its privileged service/IPC and recovery transaction are locally proved;
Android privacy, MTU, counters, concurrency, direct/store updater and private
operational-journal boundaries are locally proved; and the Linux decision is either implemented to its
declared local beta boundary or explicitly recorded as conditional/not shipped
without a public claim. Gate C and release completion remain open until their
exact candidate matrices pass.
