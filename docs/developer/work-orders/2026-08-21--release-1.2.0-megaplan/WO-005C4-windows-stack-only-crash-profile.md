# WO-005C4 — Windows stack-only crash profile

Status: `COMPLETE_LOCAL_I3`
Classification: `ACTIVE_EXECUTION`
Phase: `03`
Lane: active Windows client
Depends on: `WO-005B2`, `WO-005C3`, `WO-006A`
Production/external actions: `NOT_AUTHORIZED`

## Outcome

Close `OBS/OBS-035` without introducing Windows full-memory dumps, WER registry
mutation or a second observability pipeline. Both the ordinary UI and the SCM
service install one fail-open native unhandled-exception filter. Local evidence
proves the source, format and build contract only; it does not claim that an
exact candidate crashed, recovered or delivered the record on a clean host.

## Implemented boundary

- `POKROV_WINDOWS_CRASH_V1` contains only FILETIME ticks, process role, numeric
  exception code and at most 32 module-relative frame RVAs.
- The faulting x64 thread is unwound with Windows runtime unwind metadata.
  Fixed process, Flutter, Core and Dart app modules are allowlisted; unknown
  modules are omitted. Symbol names, module paths and absolute addresses are
  never resolved or serialized.
- UI and service use separate protected `Crash` roots and separate current plus
  previous files. The UI DACL admits only its current user, LocalSystem and
  administrators; the service DACL admits only LocalSystem and administrators.
- The crash path uses fixed-size stack buffers and a two-file replacement.
  It has no field or writer for registers, exception text, command line, raw
  profile/config, endpoint, token, heap or memory dump.
- `MiniDumpWriteDump`, WER `LocalDumps`, symbol resolution and Windows registry
  mutation are absent. The existing managed Dart/Flutter crash marker remains a
  separate input to the canonical observability runtime.
- Core module ranges are refreshed after the service loads the installed Core;
  the filter chains the preceding process handler and fails open if private
  storage cannot be prepared.

## Acceptance evidence

- `flutter build windows --debug`: `PASS`.
- Native Debug CTest: `7/7 PASS`, including the new closed-format, forbidden
  material, unknown-module and 32-frame-cap test.
- `flutter build windows --release`: `PASS`.
- Focused Release CTest `pokrov_windows_crash_profile`: `1/1 PASS`.
- Windows Flutter suite: `21/21 PASS`.
- `flutter analyze`: `PASS`, no issues.
- Client seed/cross-repository validation with explicit active platform/Core
  worktree roots: `PASS`, including release source logging and docs contracts.
- `git diff --check`: `PASS`; only line-ending warnings.
- `git status --short -- artifacts/releases`: empty; no retained release
  artifact changed.

One diagnostic `ctest -C Release` invocation ran the pre-existing
Debug-only service integration executable, which cannot accept `--test-once`
without `_DEBUG`, and returned `6/7`. It is retained as
`NOT_CREDITED_NONCANONICAL_DEBUG_ONLY_INTEGRATION`; the canonical Debug matrix
passed `7/7`, the Release build passed, and the affected Release crash-profile
test passed `1/1`.

Machine evidence:
`evidence/005C4-windows-stack-only-crash-profile/005C4-windows-stack-only-crash-profile.json`.

## Ledger effect

- `OBS/OBS-035`: `I0 -> I3`.

Distribution becomes `I3=274`, `I2=36`, `I1=47`, `I0=20`, total `377`;
`357` rows are at least `I1` and `103` remain below `I3`.

## Remaining exact-candidate gates

- Controlled UI and service crashes on the exact signed setup, followed by
  current/previous record and DACL readback.
- Real faulting-frame usefulness across POKROV, Flutter, Core and app modules
  without paths, symbols, unknown addresses or private material.
- SCM restart/recovery, route/DNS restoration and support-bundle inclusion
  after a service crash.
- Clean-host overhead and compatibility on the named Windows 10/11 matrix.

These remain `MANUAL_OWNER_TEST`/`I4` until retained against exact installer,
binary and signer identities.

## Rollback

Remove UI/service crash-filter installation, the shared native crash-profile
source/test and the seed/docs declaration together. Do not replace it with
full-memory minidumps, WER registry defaults, raw stack symbols or paths.
