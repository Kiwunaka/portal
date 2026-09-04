# WO-013GX — candidate.33 Windows connected reboot recovery

Status: `PASS_BOUNDED_EXACT_CANDIDATE_CONNECTED_REBOOT_RECOVERY; GATE_F_BLOCKED`

Observed: `2026-09-04T12:06:48Z`–`2026-09-04T12:17:32Z`

Production/public mutation: `NONE`

## Outcome

The unchanged private signed candidate.33 passes the exact installed Windows
connected-reboot recovery slice in the dedicated headless Windows 11 VM. A
secret-free direct profile reaches the running TUN boundary through ordinary
authenticated IPC. The guest then reboots while the durable journal is
`committed` and returns with the exact service/Core safely disconnected.

This closes the bounded candidate.33 connected-reboot subcheck. It does not
close managed default/AWG, connected uninstall, sleep/resume, Windows 10,
IPv6/leak or interactive SmartScreen requirements. Gate F remains
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

## Connected reboot result

Before reboot, the exact installed service/Core reaches authenticated
`phase=running`, creates one TUN, changes route/DNS fingerprints, validates
Core egress and DNS, resolves the example/ChatGPT/Gemini/Xbox set and returns
platform API health `200`. The durable recovery journal is `committed` with a
retained network snapshot when the elevated guest-only harness requests the
reboot.

Windows completed an already queued guest update during the reboot. Power was
not interrupted. This was an unrelated harness interruption, not a product
failure. After the login screen returned, the exact automatic LocalSystem
service was running and ordinary medium-integrity IPC reported:

```text
phase=artifact_ready
running=false
failure=none
```

No POKROV TUN remained. The post-boot route and DNS fingerprints matched the
pre-reboot baseline exactly, DNS passed `4/4`, and API health returned `200`.
A fresh post-boot connect recreated the TUN and changed route/DNS
fingerprints; disconnect removed it and restored the exact post-boot baseline.

Final elevated cleanup validates a `clean` journal, running Automatic
LocalSystem service, `11/11` exact installed files, zero UI processes, zero
POKROV TUN adapters and absent diagnostic client.

## Harness update policy

After product verification completed, automatic Windows updates were disabled
only inside `POKROV-Win11-Test`: `NoAutoUpdate=1`, `AUOptions=2`,
`NoAutoRebootWithLoggedOnUsers=1`, and `wuauserv` is stopped/disabled. The
receipt includes rollback commands. This is test-harness configuration and
receives no product or release credit. The main Windows host was not changed.

## Evidence

The sanitized external evidence index is:

```text
E:/POKROV-tools/release-evidence/1.2.0-candidate33-windows-connected-reboot-2026-09-04/candidate33-connected-reboot-evidence-index.json
SHA-256 e9a9fd5df8fd5075e2742a8486903aa6042fc9499a56feb393cd5ff85ff1b4cf
```

The platform-retained summary is
`evidence/013GX-candidate33-windows-connected-reboot-recovery/013GX-candidate33-windows-connected-reboot-recovery.json`,
SHA-256 `5e24f5ce1eee61c053f5804f9f39ffe7c3f3280a72cff40b8169c5c88a10fac4`.

## Release impact

`REL/WIN-003` remains `I1`: connected crash recovery and connected reboot
recovery now pass for exact candidate.33, while managed default/AWG,
sleep/resume and connected uninstall remain open. The global distribution
stays:

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

Run exact candidate.33 managed default, AWG3.1 and AWG2 recovery, then connected
uninstall and the remaining Windows manual matrix. Keep sleep/resume and IPv6
labeled manual while the current VirtualBox guest cannot provide those paths.
