# WO-013GO — candidate.32 Windows public 1.1.6 migration

Status: `PASS_PUBLIC_1_1_6_PER_USER_TO_EXACT_CANDIDATE32_MACHINE_MIGRATION`

Observed: `2026-09-04T03:07:21Z` through `2026-09-04T03:10:21Z`

Production/public mutation: `NONE`

## Outcome

Restore the dedicated zero-POKROV Windows 11 baseline, install the exact
retained public `1.1.6` setup as an ordinary user, and migrate it to the exact
private signed candidate.32 machine/service package. The host display, mouse,
keyboard, VPN route and DNS were not used or changed.

The public setup is bound to canonical release handoff
`1.1.6+20260819`, repository `Kiwunaka/pokrov`, tag `v1.1.6`, size
`28,562,832` and SHA-256
`dbaa664cf9046205f969204df79f9366b8a944f7d2a6b8d8bbd371522a3b8ae8`.

## Public per-user baseline

Before public installation, the VM had no legacy directory, HKCU/HKLM POKROV
uninstall registration, machine install root, ProgramData root, service or
POKROV process. The ordinary medium-integrity setup exited `0` and produced:

- `{localappdata}\Programs\POKROV`;
- exact legacy executable SHA-256
  `2ec9ecb584cb58cf15fe246499175fe926b17a8b40176cc2f93379241add4b4c`;
- one HKCU uninstall entry with version `1.1.6+29`;
- no machine service, machine install root or running UI;
- unchanged adapter/route/DNS-count contour.

## Candidate migration

Five candidate.32 supply files were exact before elevation. The candidate
installer exited `0` and produced exact `11/11` machine files, version
`1.2.0+4053`, one HKLM uninstall entry and a Running/Auto/LocalSystem service.

Only after the machine service succeeded, the legacy per-user directory,
executable and HKCU uninstall record were absent. The candidate remained in its
clean pre-initialize recovery state. No UI, adapter, route or DNS mutation
appeared.

The bounded tasks and the full 58 MB guest staging directory were removed after
host evidence retention. The exact service was left running and the UI stopped.

## Evidence boundaries

This proves exact public-package per-user-to-machine migration. The public UI
was not used to create account/profile state, so this does not prove saved
account/profile-state migration. It also does not prove ordinary UI/IPC after
migration, downgrade/runtime rollback, connected default/AWG/Smart DNS,
connected uninstall or physical Android migration.

Gate F stays `BLOCKED 2/17/0`; no evidence index changes. No deploy, public
asset, Store object, tag, stable pointer or promotion occurs.

## Evidence

- normalized record:
  `evidence/013GO-candidate32-windows-public116-migration/013GO-candidate32-windows-public116-migration.json`;
- raw retained root:
  `E:/POKROV-tools/release-evidence/1.2.0-candidate32-windows-public116-migration-2026-09-04/`;
- normalized record SHA-256:
  `c7a208ed908c6797c8e67ee929f0fbbb250d75cfd122793bd6ca8af384503b05`.

## Follow-up

Run an ordinary candidate.32 UI/IPC check on the migrated state, then preserve
package migration separately from saved-state compatibility. Continue with
managed default, AWG3.1/AWG2, Smart DNS, connected recovery/uninstall and
guarded runtime rollback without transferring predecessor credit.
