# WO-013GN — candidate.32 Windows clean runtime

Status: `PASS_CLEAN_BOOT_PRELOGIN_SERVICE_ORDINARY_UI_TRUSTED_IPC_INITIALIZE_DISCONNECTED`

Observed: `2026-09-04T02:50:38Z` through `2026-09-04T02:56:54Z`

Production/public mutation: `NONE`

## Outcome

Resume WO-013GM's powered-off exact clean-installed snapshot and prove the
first bounded ordinary runtime without configuring a profile or changing the
network. The host display, mouse, keyboard, VPN route and DNS were not used or
changed.

At boot `POKROVService` reached Running/Auto/LocalSystem while no console user
was logged in and no UI was running. After the same VM user logged in, a
diagnostic CLI compiled from exact client source `2d6adfce…` was hash-checked,
staged beside the exact service through a bounded elevated task and then used
only from the ordinary medium-integrity session.

## Ordinary runtime

Before initialization, trusted IPC returned `artifact_ready`, `core_ready=false`
and no connect, tunnel or DNS state. The ordinary `initialize` command was
accepted and moved the service to `initialized` with `core_ready=true`, while
`can_connect`, running tunnel, Core egress and DNS all remained false because
no profile was staged.

The exact ordinary UI then opened in the same owner/session, exposed a main
window without UAC and retained trusted compatible IPC. No onboarding,
activation or entitlement action was performed. The UI was stopped after the
probe.

The safe adapter/route/DNS-count contour remained byte-equivalent before and
after. No POKROV adapter was up. The diagnostic CLI, bounded tasks, scripts and
guest result copies were removed after host-side evidence retention; the exact
service remains running.

## Evidence boundaries

This proves clean-installed boot-time service startup before login, ordinary
owner UI/IPC and disconnected initialization. It does not prove the enabled
launch-at-login preference timing, a managed reboot after initialization,
public-1.1.6 migration, connected default/AWG/Smart DNS, connected uninstall,
or non-owner/elevated-admin IPC behavior.

Gate F stays `BLOCKED 2/17/0`; no evidence index changes. No deploy, public
asset, Store object, tag, stable pointer or promotion occurs.

## Evidence

- normalized record:
  `evidence/013GN-candidate32-windows-clean-runtime/013GN-candidate32-windows-clean-runtime.json`;
- raw retained root:
  `E:/POKROV-tools/release-evidence/1.2.0-candidate32-windows-clean-runtime-2026-09-04/`;
- normalized record SHA-256:
  `f78802e315d68584cbb34f89b168f72396710fa9d9b4740c531fa5744fd428d8`.

## Follow-up

Preserve this clean initialized state before separately testing a public-1.1.6
migration. Then run the managed default connection, packaged AWG3.1/AWG2,
Smart DNS, connected service recovery/reboot/uninstall and the explicit
launch-at-login preference timing.
