# WO-013GL — candidate.32 Windows forced service recovery

Status: `PASS_DISCONNECTED_FORCED_TERMINATION_AUTOMATIC_SERVICE_RECOVERY`

Observed: `2026-09-04T02:29:31Z`

Production/public mutation: `NONE`

## Outcome

Advance the exact candidate.32 Windows lifecycle boundary after WO-013GK. In
the same dedicated Windows 11 VM, terminate the running service process while
the product is disconnected and prove that Windows Service Control Manager
restores the exact service without operator remediation or network mutation.

The host display, mouse, keyboard, VPN route and DNS were not used or changed.
The only interactive confirmation was sent to the VM's own keyboard device.

## Result

Before termination:

- exact installed identity was `11/11`;
- `POKROVService` was Running, Auto and LocalSystem;
- the recovery journal was `clean`, with no saved network state or pending
  file;
- no POKROV adapter was up, the UI was absent and the diagnostic CLI was
  absent.

The elevated probe forcibly terminated the service process. The old process
disappeared and SCM automatically started a new process after `5,252 ms`.
No manual `Start-Service` remediation was used.

After automatic recovery:

- exact installed identity remained `11/11`;
- the service was again Running, Auto and LocalSystem with a new process
  identity;
- the recovery journal remained `clean`;
- adapter, default-route and DNS counts were unchanged;
- no POKROV adapter, UI or diagnostic fixture appeared.

The bounded scheduled task and four temporary guest files were removed after
the result was copied to the retained host evidence directory. The service was
left running and the UI stopped.

## Evidence boundaries

This proves disconnected forced service termination and automatic SCM restart
only. It does not prove connected tunnel/DNS cleanup, AWG3.1/AWG2 or Smart DNS
recovery, sleep/resume, network change, endurance or connected uninstall.

Gate F stays `BLOCKED 2/17/0`; no evidence index changes. No deploy, public
asset, Store object, tag, stable pointer or promotion occurs.

## Evidence

- normalized record:
  `evidence/013GL-candidate32-windows-forced-service-recovery/013GL-candidate32-windows-forced-service-recovery.json`;
- raw retained root:
  `E:/POKROV-tools/release-evidence/1.2.0-candidate32-windows-runtime-2026-09-04/`;
- normalized record SHA-256:
  `620b26dc80376fe0a7312ce4a96db5c131a5a5a2776b1a3a082a9da6410867c3`.

## Follow-up

Prove clean install and public-1.1.6 migration separately, then exercise exact
candidate.32 connected default, AWG3.1, AWG2 and Smart DNS service recovery.
Continue with sleep/resume, network change, endurance and connected uninstall
without transferring predecessor credit.
