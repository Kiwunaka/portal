# WO-013DA — candidate.13 current/Brain/RU origin and Windows preflight

Status: `CURRENT_PASS_BRAIN_PASS_RU_MANUAL_WINDOWS_BLOCKED_BY_ENVIRONMENT`
Classification: `ACTIVE_EXECUTION_EVIDENCE`
Phase: `11`
Candidate: `pokrov-1.2.0-candidate.13`
Production/external mutation: `NONE`

## Outcome

Refresh the origin slices that can be proved read-only against exact platform
source `7d983c0ab52e9c01f94da8916a6bca6a0039be8d`, and inspect whether an
isolated Windows target exists without disturbing the owner's active tunnel.

| Slice | Result |
|---|---|
| current-origin health | `PASS`, p95 `39.7521 ms <= 100 ms`, 50 samples after 5 warmups |
| current-origin public catalog | `PASS`, p95 `40.4278 ms <= 200 ms`, 50 samples after 5 warmups |
| Brain runtime source | `PASS`, `197/197` semantic byte matches, zero mismatches |
| Brain readiness | `PASS`, `23/23`, including 5 stable subscription samples |
| RU Pi environment | `MANUAL_OWNER_TEST_ENVIRONMENT_INCOMPLETE` |
| isolated Windows target | `BLOCKED_BY_ENVIRONMENT` |

The current-origin probes bind directly to the physical wired adapter, disable
proxy discovery and retain only sanitized aggregate values in Git. The raw
local source address is not tracked.

The Brain checks use read-only SSH hashes and readiness requests. No remote
content, secret or response body is retained in the normalized evidence, and
no service or source is changed.

The RU Pi now has exact candidate.13 source files `10/10`, all four systemd
units loaded and both timers active. It intentionally lacks the probe env,
uploader env, HMAC key and profiles after the prior cleanup; no latest archive
exists. This is a clean fail-closed `MANUAL_OWNER_TEST`, not an RU-origin PASS.
Installing runtime material and executing the external probe requires separate
authorization.

## Windows boundary

No Windows Sandbox, VirtualBox, VMware or QEMU target is available and the
hypervisor is not active. The owner host has an active unrelated tunnel. The
candidate setup is therefore not installed or connected on this host, and no
clean-VM, TUN, DNS, recovery or uninstall claim is made.

## Completion-index effect

- `FRKN_PLAN/W9-02` advances `I1 -> I2`: exact candidate.13 current and Brain
  origins pass while RU remains separately and explicitly manual.
- Gate E stays `I3` with stronger exact candidate.13 current-origin performance
  evidence.
- Gate F stays `I3` and
  `NOT_RUN_MISSING_EXACT_ARM64_INSTALL_BINDING`; RU, clean Windows and other
  manual gates remain open.
- Distribution becomes `I4=6`, `I3=316`, `I2=22`, `I1=34`, `I0=0` across
  `378` rows.

No tag, public release, stable pointer, deploy, provider/payment action,
physical-device action or LDPlayer action occurred.

## Evidence

External generated reports are retained under:

```text
E:\POKROV-tools\temp\candidate13-origin-refresh-20260830
```

Normalized evidence is
`evidence/013DA-candidate13-origin-windows-preflight/013DA-candidate13-origin-windows-preflight.json`.
Its SHA-256 is
`50742ff0b752b9915ccade8b3d59987f3d2debb08637d7e1989e3375706a31fc`.

## Next action

Keep RU and Windows non-PASS. A guarded RU runtime-material install/probe is an
external APPLY and needs separate authorization. Windows needs an isolated
Windows target; do not disconnect or repurpose the owner's active host tunnel.
The exact ARM64 physical install binding remains the first Gate F prerequisite.
