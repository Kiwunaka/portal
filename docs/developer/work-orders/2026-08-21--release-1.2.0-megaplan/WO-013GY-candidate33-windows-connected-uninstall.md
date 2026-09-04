# WO-013GY — candidate.33 Windows connected uninstall

Status: `PASS_BOUNDED_EXACT_CANDIDATE_CONNECTED_UNINSTALL_AND_REINSTALL; GATE_F_BLOCKED`

Observed: `2026-09-04T12:35:01Z`–`2026-09-04T12:41:54Z`

Production/public mutation: `NONE`

## Outcome

The unchanged private signed candidate.33 passes the exact installed Windows
connected-uninstall slice in the dedicated headless Windows 11 VM. The exact
interactive UI is open in the ordinary user session while a secret-free direct
profile reaches the running TUN boundary through authenticated IPC. The exact
uninstaller then terminates UI, removes the service, product files, registry
and TUN, and restores the exact route/DNS baseline.

A clean reinstall from the same candidate.33 setup returns the guest to
`11/11` exact files with an Automatic LocalSystem service and unchanged
network baseline. This closes the bounded connected-uninstall subcheck. It
does not close managed default/AWG, sleep/resume, Windows 10, IPv6/leak or
interactive SmartScreen requirements. Gate F remains `BLOCKED 2/17/0`; no
completion level changes.

## Exact candidate boundary

| Fact | Exact value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.33` |
| Platform / client / Core / index source | `f530005...5bc1` / `6ab1bca...735e` / `cd8f0f4...884d` / `63993fb...c43c` |
| Windows setup | `250622f7...3580`, `29153792` bytes |
| Windows runtime manifest | `0f93211e...a5b`, `11/11` installed files |
| Interactive UI | exact manifest file `1b175a66...1d97`, session `1` |
| Diagnostic client | exact client-source build `2a445f6e...c26f`, temporarily staged under the protected install root |
| Profile | synthetic secret-free direct TUN, SHA-256 `b829c67b...6272` |

No production account or managed profile is used. No raw public address,
endpoint, key or provider payload is retained.

## Connected uninstall result

Before uninstall, ordinary medium-integrity IPC reports `phase=running` with:

- one exact interactive UI process in user session `1`;
- one POKROV TUN and changed route/DNS fingerprints;
- Core egress validation and DNS readiness;
- DNS success for the example/ChatGPT/Gemini/Xbox set;
- running Automatic LocalSystem service.

The exact uninstaller `0c9ad222...8dba` returns `0`. Product postcheck proves:

- UI process count `0`;
- `POKROVService` absent;
- all `11` manifest-owned product files absent;
- uninstall registry entries `0`;
- POKROV TUN count `0`;
- route and DNS fingerprints restored exactly.

The only file left in the installation root was the external diagnostic CLI,
which is not part of the candidate manifest. The harness verified its exact
SHA-256, removed it, and removed the empty directory. This external fixture is
not counted as product residue.

## Clean reinstall result

The exact candidate.33 setup then returns `0`, restores `11/11` manifest files
and runs `POKROVService` as Automatic LocalSystem. Route/DNS fingerprints stay
equal to the clean post-uninstall baseline; UI and TUN counts remain zero and
the diagnostic CLI is absent.

## Evidence honesty

Three harness errors are retained:

1. The first prepare used an incorrect expanded UI hash and stopped before
   network mutation. The installed UI matched the exact manifest.
2. The first post-uninstall collector encountered a StrictMode property error
   after the uninstaller had already returned `0`.
3. The first cleanup collector encountered a StrictMode empty-result error
   after zero product files remained and the exact external CLI was removed.

The final idempotent postcheck proves product cleanup without rerunning the
uninstaller. These collector errors are not relabelled as product failures or
hidden as PASS.

The sanitized external evidence index is:

```text
E:/POKROV-tools/release-evidence/1.2.0-candidate33-windows-connected-uninstall-2026-09-04/candidate33-connected-uninstall-evidence-index.json
SHA-256 bf222d369972aa36ddaad23395fe384f259940f4be106980974fc98627a4a771
```

The platform-retained summary is
`evidence/013GY-candidate33-windows-connected-uninstall/013GY-candidate33-windows-connected-uninstall.json`,
SHA-256 `ae9efa9b4454c7d237c9f05a62a814e888f3b81c3a27d94d3f6fe207cdd4e7f0`.

## Release impact

`REL/WIN-003` remains `I1`: connected crash, reboot and uninstall recovery now
pass for exact candidate.33, while managed default/AWG and sleep/resume remain
open. The global distribution stays:

```text
I4=8 I3=319 I2=19 I1=32 I0=0 total=378
```

Gate F remains:

```text
BLOCKED
required=19
pass=2
non_pass=17
fail=0
validation_errors=0
gate_g_authorized=false
```

No candidate byte, Gate G state, deploy, public asset, Store object, stable
pointer or production runtime changes.

## Follow-up

Run exact candidate.33 managed default, AWG3.1 and AWG2 recovery and the
remaining Windows manual matrix. Keep sleep/resume and IPv6 labeled manual
while the current VirtualBox guest cannot provide those paths.
