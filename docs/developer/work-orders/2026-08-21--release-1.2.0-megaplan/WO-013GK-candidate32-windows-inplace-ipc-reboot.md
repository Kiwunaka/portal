# WO-013GK — candidate.32 Windows in-place, IPC and reboot

Status: `PASS_INPLACE_REPLACEMENT_ORDINARY_UI_IPC_INITIALIZE_AND_DISCONNECTED_REBOOT`

Observed: `2026-09-04T02:20:44Z`

Production/public mutation: `NONE`

## Outcome

Advance exact private signed candidate.32 from the prior non-elevated
fail-closed boundary to a bounded installed Windows runtime result in the
dedicated Windows 11 VM. The owner authorized the private candidate and this
isolated VM; the host display, mouse, keyboard, VPN route and DNS were not
used or changed.

The elevated installer replaced the retained predecessor state from `8/11`
candidate.32-matching files to exact `11/11`, exited `0`, registered an Auto
LocalSystem service and left the recovery journal clean. The disconnected
safe route/DNS contour did not change.

## Exact ordinary-user runtime

A bounded diagnostic CLI was compiled from exact client source
`2d6adfcebc37f2109ef339276be6a1569cb7aa1e` using the production
`service_client.cpp`, `service_protocol.cpp` and `service_pipe_client.cpp`.
Its SHA-256 is
`3687e95575fe6df0d39798c322f77ce1d648b74c7856864c0b6f703487141f47`.
It was staged beside the installed service only for the SCM/path-bound IPC
probe and removed afterward.

From a non-elevated medium-integrity token:

- `status` was available, trusted, protocol-compatible and accepted;
- `initialize` moved the service from `artifact_ready` to `initialized`;
- `core_ready=true`, while `can_connect=false`, `running=false`,
  `dns_ready=false` and egress proof remained false without a staged profile;
- the safe network contour stayed unchanged;
- exact `pokrov_windows.exe` opened as the same ordinary user/session, stayed
  alive, exposed a main window and retained trusted IPC without UAC;
- no onboarding, activation, entitlement or account action was performed.

## Managed reboot

The VM boot time changed from `2026-09-04T01:50:22.5000000Z` to
`2026-09-04T02:17:05.5000000Z`. The service reached `Running` before user
login. After guest login:

- exact installed identity remained `11/11`;
- the service remained Auto/LocalSystem;
- the recovery journal was `clean`, with no pending or saved network state;
- route/DNS counts matched the pre-reboot contour;
- no POKROV UI, adapter or diagnostic fixture started automatically.

The launch-at-login preference was not enabled. This proves no premature
autoconnect for the observed default preference, not launch-at-login timing.

## Collector corrections

The installer itself succeeded before the initial evidence collector hit an
Uninstall-registry property-access mistake. The raw result records pre-state
`8/11`, installer exit `0` and that collector error. A medium-token post-check
then correctly encountered protected runtime ACLs; the first elevated
post-check exposed the same strict-property mistake. All three results remain
retained. The product was not reinstalled to hide them.

The final reconciliation binds the raw successful installer exit to an
independent elevated post-check proving `11/11`, service, recovery, network,
version and unsigned-owner-exception state.

## Evidence boundaries

This is not a clean install, public-1.1.6 migration, saved-state rollback,
connected default/AWG/Smart-DNS result, forced-kill, sleep/resume, connected
uninstall, Windows 10, SmartScreen UI or launch-at-login timing result.
Candidate.31 and older connected runtime remain predecessor history.

Gate F stays `BLOCKED 2/17/0`; it is not regenerated because the mandatory
Windows row still requires the clean/connected matrix. No index level changes.
No deploy, public asset, Store object, tag, stable pointer or promotion occurs.

## Evidence

- normalized record:
  `evidence/013GK-candidate32-windows-inplace-ipc-reboot/013GK-candidate32-windows-inplace-ipc-reboot.json`;
- raw retained root:
  `E:/POKROV-tools/release-evidence/1.2.0-candidate32-windows-runtime-2026-09-04/`;
- normalized record SHA-256:
  `783f1b7b951f7cb92c401b2609c29ca8e4b6a5d2f50073eae374f45b0c948ec3`.

## Follow-up

Continue exact candidate.32 Windows execution in this VM: forced service
termination/restart while disconnected, then a clean snapshot install,
public-1.1.6 migration, connected default, packaged AWG3.1/AWG2, Smart DNS,
sleep/resume, connected reboot/recovery and connected uninstall. Preserve
each boundary separately; do not transfer predecessor credit.
