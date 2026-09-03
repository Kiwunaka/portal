# WO-013FL — candidate.26 CLI precursor and Windows 11 upgrade/reboot

Status: `PASS_PRE_CANDIDATE_WINDOWS_BUILD_AND_BOUNDED_VM_UPGRADE`

Recorded: `2026-09-03T06:52:33Z`

Production/public mutation: `NONE`

## Outcome

Build the post-WO-013FK successor Windows package entirely through the CLI,
verify that the corrected Debug/Release CTest registration survives a full
clean build, and exercise the resulting exact installer inside the isolated
Windows 11 VM without taking control of the owner's desktop.

The full release builder passes and produces a new setup plus an `11/11`
runtime manifest. The exact setup upgrades the retained candidate.23 VM state,
matches all installed files, runs the ordinary UI in session 1, completes
authenticated UI/service status IPC and survives a real guest reboot with the
LocalSystem service restored automatically.

This is deliberately a Windows-only `candidate.26-precursor`, not a created or
signed multi-platform candidate. Candidate.25 remains the current private
signed candidate and Gate F authority.

## Exact boundary

| Item | Identity |
|---|---|
| Client source | merged `POKROV-app/main` `ed74928a88ead8053a845f9d8e294d1298b83a6a` |
| Core source | exact `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Platform validation source | exact `2e8f6540132bd4080b8ba56de9da018d712e7c63` |
| App version | `1.2.0+4053` |
| Setup | `1e84ca5fbc110c0199e4625b7b13fc0db8206afd32074bab28647ec5e6b9b8f0`, `29140784` bytes |
| Build manifest | `ba06d031723e0d83014baae6f6dc335205e7addc9ed8db17cda678f562ba5c72`, `11/11` files |
| Windows signing | `SKIPPED_BY_OWNER`; direct-beta SmartScreen/unknown-publisher warning remains mandatory |

The first clean-worktree invocation stops before compilation because the
platform shared-facts root is not implicit outside the primary checkout. The
second invocation supplies the exact clean platform root explicitly and
passes. This is a build-environment preflight correction, not a product
failure.

## Full CLI build verification

- release/repository/shared-facts/observability/logging/handoff contracts:
  `PASS`;
- app-shell: `413/413 PASS`;
- runtime engine: `72/72 PASS` with one declared optional real-Core skip;
- Android shell Flutter tests: `8/8 PASS`;
- Windows widget tests: `23/23 PASS`;
- Android Gradle direct and store unit configurations: `PASS`;
- Windows analyze: `PASS`;
- native Debug CTest: `8/8 PASS`, including service integration;
- native Release CTest: `7/7 PASS`, correctly excluding the Debug-only
  integration executable;
- staged Windows payload: `303` files / `99269838` bytes scanned, zero
  definite private-key, authorization, credential-assignment, connection-URI
  or known live-token findings;
- raw installer: `29140784` bytes scanned with the same zero-finding result.

## Isolated Windows 11 verification

The powered-off rollback snapshot
`candidate23-retained-before-candidate25-20260903` is the exact ancestor. Its
freshly booted baseline has the older UI/service hashes, a running LocalSystem
service, no `tun0`, successful control DNS and failed
`portal.pokrov.space` DNS. The latter two facts predate the new installer.
WO-013FM later establishes that `portal.pokrov.space` was a non-canonical
harness sentinel, not a client control-plane prerequisite; the active client
uses `api.pokrov.space`, which resolves and returns healthy inside the same VM.

The exact precursor setup then passes:

- in-place installer exit `0`;
- present/size/hash identity `11/11`;
- service `Running`, `Automatic`, `LocalSystem`, exact installed path;
- installer owner SID equals the ordinary guest user;
- ordinary UI process runs in interactive session `1`;
- protected service journal confirms accepted authenticated IPC and status
  request without exporting raw journal content;
- after a real guest reboot at `2026-09-03T06:18:08.5Z`, the service is again
  `Running`, `Automatic`, `LocalSystem` with no interactive user, and the UI
  file still matches the precursor manifest.

Connected TUN/DNS/egress receives no credit. `tun0` was absent before the
upgrade and remains absent after UI launch because no managed profile or
connect action is supplied. No connection state is manufactured from an idle
predecessor snapshot. WO-013FM separately proves candidate.25's exact
direct-only TUN/DNS/disconnect and connected-reboot lifecycle after correcting
the hostname, without transferring managed-node or candidate.26 credit.

## Cleanup and release effect

The disposable build worktree (`6813385833` bytes) is removed after copying the
exact setup, manifest, full CLI log and JUnit evidence. The test VM is powered
off and restored to the named candidate.23 rollback snapshot; no new snapshot
is created. The owner's foreground UI, mouse, keyboard, installed services and
host network are never used.

No phase level changes. Candidate.25 stays immutable. Gate F remains exact
`BLOCKED 5 PASS / 14 non-PASS / 0 FAIL`; no public tag, release asset, Store
object, stable pointer or production mutation is created.

## Evidence

- `evidence/013FL-candidate26-cli-vm/013FL-candidate26-cli-build.json`, SHA-256
  `faa173636db872009a63fd0becc4eb341dae854b6ea6da5c8e64f8662b3e1173`;
- `evidence/013FL-candidate26-cli-vm/013FL-candidate26-windows-vm.json`, SHA-256
  `45d7fa083de7357b7975e8b318731e11522dd6d42d67edc3ab86a34cc6da204d`;
- external exact setup, build manifest, sanitized CLI log and Debug/Release
  JUnit records:
  `E:/POKROV-tools/release-evidence/1.2.0-candidate26-cli-build-2026-09-03/`.
