# WO-013GW — candidate.33 Windows connected crash recovery

Status: `PASS_BOUNDED_EXACT_CANDIDATE_CONNECTED_CRASH_RECOVERY; GATE_F_BLOCKED`

Observed: `2026-09-04T11:42:34Z`–`2026-09-04T11:51:19Z`

Production/public mutation: `NONE`

## Outcome

The unchanged private signed candidate.33 passes the exact installed Windows
connected forced-service recovery slice in the dedicated headless Windows 11
VM. A secret-free direct profile reaches the running TUN boundary through an
ordinary authenticated client. Forced termination of the LocalSystem service
then triggers automatic SCM restart and durable network rollback to a safe
disconnected state.

This closes the bounded candidate.33 connected crash-recovery subcheck. It
does not close managed default/AWG, connected reboot/uninstall, sleep/resume,
Windows 10, IPv6/leak or interactive SmartScreen requirements. Gate F remains
`BLOCKED 2/17/0`; no completion level changes.

## Exact candidate boundary

| Fact | Exact value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.33` |
| Platform / client / Core / index source | `f530005...5bc1` / `6ab1bca...735e` / `cd8f0f4...884d` / `63993fb...c43c` |
| Windows setup | `250622f7...3580`, `29153792` bytes |
| Windows runtime manifest | `0f93211e...a5b`, `11/11` installed files |
| Diagnostic client | exact client-source build `2a445f6e...c26f`, temporarily staged under the protected install root and removed after proof |
| Profile | synthetic secret-free direct TUN, SHA-256 `b829c67b...6272` |

No production account or managed profile is used. No raw public address,
endpoint, key or provider payload is retained.

## Connected and recovery result

Before termination, the exact installed service/Core reaches:

- authenticated ordinary-user IPC with `phase=running`;
- TUN present with changed route and DNS fingerprints;
- Core egress validation and DNS readiness;
- DNS success for the example/ChatGPT/Gemini/Xbox set;
- platform API health `200`;
- durable recovery journal stage `committed` with a retained network snapshot.

The exact service process is then forcibly terminated. SCM automatically
starts a new service process in `5449` ms. No operator remediation is used.
Startup recovery returns the durable journal to `clean`, removes the TUN and
restores the exact pre-connect route and DNS fingerprints.

A new ordinary authenticated IPC request reports:

```text
phase=initialized
running=false
failure=none
```

The final cleanup validates `11/11` exact installed files, running Automatic
LocalSystem service, zero POKROV TUN adapters, zero UI processes, absent
diagnostic client, DNS `4/4` and API health `200`.

## Evidence honesty

Two earlier harness-only failures are retained. The first used unsupported
CLI argument syntax; the second ran the CLI from a location intentionally not
trusted by the installed service. Both stopped before network mutation and do
not represent candidate runtime failures.

The sanitized external evidence index is:

```text
E:/POKROV-tools/release-evidence/1.2.0-candidate33-windows-connected-recovery-2026-09-04/candidate33-connected-recovery-evidence-index.json
SHA-256 50552dddbb35ba9be280dd2437e25e7a90fad98231673debf064aaa37ad56109
```

The platform-retained summary is
`evidence/013GW-candidate33-windows-connected-crash-recovery/013GW-candidate33-windows-connected-crash-recovery.json`,
SHA-256 `7c7e1538d8f4325f58f9e9678dd2fe4f1adf3cfe1b3a096b13f0f745ac596079`.

## Client truth merge

Client PR 77 merges the canonical Windows readiness update at
`559f2a3d7d2c4098137a0e576f45905535f6925b`. Exact client/platform/Core seed
validation and `git diff --check` pass with no `artifacts/releases/**` delta.
The hosted `cross-repository-contract` job terminates with `steps=[]` and is
`BLOCKED_BY_ACCESS_GITHUB_BILLING`; it is not reported as a contract failure
or hosted PASS.

## Release impact

`REL/WIN-003` remains `I1`: the exact connected forced-service recovery
subcheck now passes, while its broader managed default/AWG, reboot,
sleep/resume and connected-uninstall requirements remain open. The global
distribution stays:

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

Run the exact candidate.33 managed default, AWG3.1 and AWG2 recovery paths,
then connected reboot/uninstall and the remaining Windows manual matrix. Keep
sleep/resume and IPv6 labeled manual while the current VirtualBox guest cannot
provide those paths.
