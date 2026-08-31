# WO-013DN — candidate.16 RU-probe immutable bundle and owned-Pi PLAN

Status: `PASS_CANDIDATE16_IMMUTABLE_BUNDLE_AND_REMOTE_PLAN; RU_ENVIRONMENT_INCOMPLETE`

Observed: `2026-09-01T00:22:26+03:00`

## Scope

Add the signed candidate.16 platform revision to the fail-closed RU-origin
bundle allowlist, build and independently reproduce its exact ten-member
package, inspect the owner-provided Raspberry Pi 4 without mutation, and run
only the guarded remote install PLAN.

No file was installed on the Pi, no timer or service was started, no runtime
material was supplied, no runner/uploader/heartbeat/admin readback ran, and no
production or release state changed.

## Exact boundary

| Item | Value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.16` |
| Signed platform source | `719e23dc49407beb9ae30d98d17d4b73d18ae37c` |
| Execution host class | owned Raspberry Pi 4, Linux ARM64, direct RU terminal access |
| Operation | read-only environment probe plus install `PLAN` |
| Runtime mutation | none |

The builder continues to reject arbitrary commits. This change only adds the
already signed candidate.16 platform revision and its candidate label; it does
not change the candidate, runner behavior or runtime configuration.

## Immutable bundle

Two independent builds are byte-identical:

| Property | Result |
|---|---|
| Members | `10` source/unit files |
| Size | `47,927` bytes |
| SHA-256 | `e09808e40809c7a2e9bb0c3b10d428eb7af524bec43e6dea873fcbce08b471a4` |
| Runtime material included | `false` |
| Verify | `PASS` |
| Local install PLAN | `PASS` |

The package contains no `probe.env`, `uploader.env`, `hmac.key` or
`profiles.json` and cannot install itself.

## Read-only owned-Pi result

The exact candidate.16 source comparison returns
`MANUAL_OWNER_TEST_ENVIRONMENT_INCOMPLETE`:

- `6/10` installed source/unit files match candidate.16;
- four source files have content differences;
- all ten install targets, process user/group, required tools, private spool
  and passwordless privilege boundary are present;
- NTP is synchronized;
- spool counts are zero for pending, blocked, quarantine and archive;
- both timers are inactive/enabled;
- uploader service is inactive;
- runner service retains a failed exit-code state;
- all four required runtime-material files are absent;
- no latest archive exists.

This is environment inventory, not a failed RU target verdict. No server or
heartbeat readback was attempted.

## Guarded remote PLAN

The candidate.16 install PLAN accepts the exact bundle and trusted SSH alias,
returns only redacted counts/state, and proves:

- `mode=PLAN`;
- `mutation_performed=false`;
- `raw_host_returned=false`;
- `raw_runtime_material_returned=false`;
- `runtime_material.supplied=false`;
- manual runner/uploader/heartbeat/admin readback remains `NOT_RUN`;
- RU-origin verdict remains `MANUAL_OWNER_TEST`.

## Verification

- bundle/remote-operation/environment focused tests: `29/29 PASS`;
- exact build repeated with identical bytes: `PASS`;
- bundle verification and local PLAN: `PASS`;
- guarded owned-Pi remote PLAN: `PASS_NO_MUTATION`.

## Completion-index effect

No row advances. `FRKN_PLAN/W9-02` remains `I2` with stronger exact-candidate
RU environment and PLAN evidence, but no RU run, upload, heartbeat or admin
readback. Gate F remains not run for its separate physical ARM64 and AWG egress
blockers. Gate G remains unauthorized.

The distribution remains `I4=5`, `I3=319`, `I2=20`, `I1=34`, `I0=0` across
`378` rows.

## Evidence

- normalized evidence:
  `evidence/013DN-candidate16-ru-probe-plan/013DN-candidate16-ru-probe-plan.json`;
- normalized evidence SHA-256:
  `1aa03607e8bfde973ebec4285424526e9f3511018cdf6c60f4265fd5af198d28`;
- external read-only environment evidence SHA-256:
  `13c68d3e8cd885c21afaac44466fdb41a5570aee5d177d4d485026c1679a494d`;
- external remote PLAN SHA-256:
  `89fcdfb88b1b910f76f554f8188d92ac9ab60fbfa88484594d7aec9080e6e586`.

External evidence contains no credential, runtime material, raw host, private
key, subscription URL or device identifier.

## Next action

Prepare the four private runtime-material files through the existing owner
channel and obtain explicit APPLY authorization. Then use the receipt-bound
installer, run runner and uploader once, and retain heartbeat plus admin
readback separately from current- and Brain-origin evidence.
