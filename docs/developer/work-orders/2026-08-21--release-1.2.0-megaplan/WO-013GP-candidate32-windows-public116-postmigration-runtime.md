# WO-013GP — candidate.32 Windows public 1.1.6 post-migration runtime

Status: `PASS_PUBLIC116_POST_MIGRATION_ORDINARY_UI_TRUSTED_IPC_DISCONNECTED`

Final pass observed: `2026-09-04T03:32:10Z`

Production/public mutation: `NONE`

## Outcome

Resume the exact Windows 11 state produced by WO-013GO. Before console login,
the exact candidate.32 service is already Running/Automatic with no Explorer or
POKROV UI process. After virtual console login, an ordinary medium-integrity
owner verifies the migrated install, exact UI/service bytes, trusted IPC and a
disconnected initialize without changing the host or guest network contour.

The migrated state retains one HKLM `1.2.0+4053` uninstall record, no HKCU
POKROV uninstall record and no legacy per-user directory. Status transitions
from trusted `artifact_ready` to `initialized`; `can_connect`, running tunnel,
DNS and egress stay false. The exact UI opens a real main window in the same
owner session without UAC and is stopped after the probe.

## Retained harness attempts

The first two attempts stop before IPC/UI on measurement-code errors: a missing
registry property under strict mode, then PowerShell singleton-array unrolling.
Both raw results are retained as `HARNESS_ERROR`, not product failures.

The third attempt deliberately exposes a security boundary after the exact CLI
is placed in the ordinary temporary directory. It returns `server_untrusted`
and rejects the service. Exact source at
`apps/windows_shell/windows/service/service_client.cpp` derives the expected
service path from the IPC client's own executable directory and compares it to
the SCM record. Therefore this result is the expected fail-closed behavior for
invalid diagnostic placement, not evidence that candidate.32 lost its service
artifact.

The exact CLI is then staged next to `pokrov_service.exe` by a high-integrity
bounded helper, rehashed, used by the ordinary session, rehashed again and
removed. Both stage and removal pass. No diagnostic file remains in Program
Files, the guest staging directory is removed, the UI is stopped and the VM is
powered off.

## Evidence boundaries

WO-013GO plus this slice prove exact public-package migration followed by
ordinary UI/trusted IPC/disconnected initialization. The public predecessor was
not used to create account/profile state, so saved-state compatibility remains
open. Connected default/AWG/Smart DNS, connected recovery/uninstall, Android
upgrade/downgrade and guarded runtime rollback also remain open.

Gate F stays `BLOCKED 2/17/0`; no index changes. No deploy, public asset, Store
object, tag, stable pointer or promotion occurs.

## Evidence

- normalized record:
  `evidence/013GP-candidate32-windows-public116-postmigration-runtime/013GP-candidate32-windows-public116-postmigration-runtime.json`;
- raw retained root:
  `E:/POKROV-tools/release-evidence/1.2.0-candidate32-windows-public116-postmigration-runtime-2026-09-04/`;
- normalized record SHA-256:
  `48607fa9df7b72f65bc0603447dd93a5240bfc194832ded271a7d9a7bf54401d`.

## Follow-up

Keep package migration separate from saved-state compatibility. Continue with
saved account/profile fixtures, managed default, AWG3.1/AWG2, Smart DNS,
connected recovery/uninstall, physical Android migration and guarded runtime
rollback without transferring predecessor credit.
