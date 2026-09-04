# WO-013GM — candidate.32 Windows clean install

Status: `PASS_EXACT_CANDIDATE32_CLEAN_HOST_INSTALL_RECONCILED`

Observed: `2026-09-04T02:44:54Z`

Production/public mutation: `NONE`

## Outcome

Prove an exact candidate.32 machine-wide install from the dedicated Windows 11
VM's retained clean baseline. Before restoring the baseline, preserve the
completed in-place/reboot/forced-service-recovery state in its own return
snapshot. The host display, mouse, keyboard, VPN route and DNS were not used or
changed.

The restored `ready-for-pokrov-tests` baseline contained no POKROV install
root, ProgramData root, service, uninstall registration, adapter, process,
staging directory or candidate task. Five exact signed-supply files were staged
and hash-matched before elevation.

The exact installer exited `0`. Independent post-check proves:

- exact installed identity is `11/11`;
- product registration is `1.2.0+4053`;
- the service is Running, Auto and LocalSystem;
- the safe route/DNS contour is unchanged and no POKROV adapter is up;
- no UI or diagnostic fixture started;
- the installer remains `NotSigned` under the owner's direct-beta exception.

The result is preserved as powered-off snapshot
`candidate32-clean-installed-uninitialized-20260904`.

## Recovery-journal reconciliation

The successful installer collector initially marked the absent recovery journal
as a failure. Exact candidate.32 source
`apps/windows_shell/windows/service/service_recovery.cpp` with SHA-256
`a61c1f22415b3db86ee7b37c2ec5ec38661fa1372757aa17596ccb60b300aa23`
defines a missing journal as the clean initial state: it initializes the
generation to zeros and leaves the default clean, non-invalid stage. The file
is first needed when a network transaction begins.

The raw result already contained the clean pre-state, five supply matches,
installer exit `0`, `11/11`, product/service identity and unchanged network.
The product was not reinstalled. An independent elevated post-check binds that
raw result to the exact installed state and the source-owned initial-journal
contract.

An earlier collector attempt stopped before the installer because a foreign
uninstall-registry entry lacked `DisplayName`; that raw result also remains
retained.

## Evidence boundaries

This proves exact disconnected clean-host installation before first product
initialization. It does not prove ordinary UI/IPC on this clean state, reboot,
public-1.1.6 migration, saved-state rollback, connected default/AWG/Smart DNS,
connected uninstall, Windows 10 or SmartScreen UI.

Gate F stays `BLOCKED 2/17/0`; no evidence index changes. No deploy, public
asset, Store object, tag, stable pointer or promotion occurs.

## Evidence

- normalized record:
  `evidence/013GM-candidate32-windows-clean-install/013GM-candidate32-windows-clean-install.json`;
- raw retained root:
  `E:/POKROV-tools/release-evidence/1.2.0-candidate32-windows-clean-install-2026-09-04/`;
- normalized record SHA-256:
  `838ce9971ba802d5019471ad6bf3ffc1ea39d3a79bee32aa00fa946f85cf8d26`.

## Follow-up

Resume the retained clean-installed snapshot and prove ordinary UI/trusted IPC,
first initialization and reboot from this exact clean state. Preserve it before
separately restoring a public-1.1.6 baseline for migration. Then run connected
default, AWG3.1, AWG2, Smart DNS and connected uninstall matrices.
