# WO-013CL — Candidate.8 Android excluded-app physical proof

Status: `PASS_EXACT_CANDIDATE8_EXCLUDED_APP_TRAFFIC_AND_BYPASS_MATRIX_OPEN`
Classification: `ACTIVE_EXECUTION_EVIDENCE`
Phase: `03`, `11`
Candidate: `pokrov-1.2.0-candidate.8` remains immutable

## Outcome

Close the named inverse per-app routing gap on the exact signed candidate.8
ARM64 package without upgrading the aggregate Android row or Gate F. On one
physical Android 12 device, the same redacted control application first crossed
the active ordinary VPN while included and then left the Android VPN UID ranges
after explicit exclusion and the app-managed reconnect. It loaded a benign
public page directly while the active POKROV TUN accumulated only bounded
background traffic.

This is `PASS_EXACT_CANDIDATE_EXCLUDED_APP_TRAFFIC_AND_BYPASS`. It is not an
active-WARP, external IPv6/leak, blocked-UDP53, external-MTU, multi-OEM,
endurance, backup/exposed-port, Store or stable-release proof.

## Exact candidate binding

The installed package was pulled back and verified before retaining the result:

| Property | Exact value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.8` |
| Platform source | `241a83b4dca00799b39696a4ae0c3c97e087ec39` |
| Client source | `3459438f02bd774e722b1b858e7f7f16d57a9f5c` |
| Core source | `a45d69e40ed7d892619a2b5c4592a527f630665e` |
| Release-index source | `b242e0a3060b04f9b71641a0524bf251a75ce2a8` |
| Manifest SHA-256 | `f0006cec90c84e401e9920d9098102c7f50ab5ace5242e0d7683c3df709a6fbc` |
| Installed version | `1.2.0+4046`, release/non-debuggable |
| ARM64 package | `101366934` bytes, SHA-256 `9278c09fd8fa5768d3260cf796b4230db5acb0a092187aae00c441d717cfc572` |
| Signature | valid, exact production certificate matched |

The temporary pulled APK was deleted after verification.

## Physical differential

The ordinary foreign profile reached the client's proof-driven connected state
with Private DNS off and WARP disabled. The retained bounded measurements are:

| Slice | Structural state | TUN delta |
|---|---|---|
| Idle baseline, 6 seconds | control application still included | `208` RX / `208` TX bytes |
| Included control, 10 seconds | control UID inside VPN ranges; page load through VPN | `380962` RX / `379884` TX bytes |
| Excluded control, 12 seconds | control UID outside VPN ranges; benign page loaded directly | `776` RX / `776` TX bytes |

The excluded window stayed below the explicit `10000`-byte bounded-background
threshold. The POKROV host UID stayed outside the VPN ranges in both shapes.
Together with the included control, this proves traffic plus bypass rather than
only configuration rendering.

An earlier terminal UI-command marker was not created. It is retained only as
`NOT_EVIDENCE_UI_COMMAND_MARKER_NOT_CREATED`; it contributes no network claim.

## Privacy and restoration

No raw package name, UID range, device identifier, network identifier, terminal
history, runtime material, screenshot or UI dump is retained. The normalized
evidence contains only bounded facts and digests.

Cleanup restored `Всё устройство`, zero selected applications, WARP off, no
POKROV VPN service and no TUN. Wi-Fi was returned off, mobile data on, Private
DNS off and the owner's pre-existing foreground VPN application was restored.
No server, candidate, payment, stable pointer, public release or Store state was
mutated.

## Repository and verification

Client PR `38` merged as
`85a84df352e193197cd2dd486ca5d9417ad805cf`. Its hosted private-repository job
executed zero steps and is `SKIPPED_BY_OWNER`, not PASS. The client-side local
verification passed:

```text
docs contract                     -> PASS
exact seeded validation via pwsh -> PASS
git diff --check                 -> PASS
```

The seeded validation bound the exact platform and Core roots and passed
version/cross-repository truth, observability, `144` logging files plus four
negative fixtures, `16` handoff cases, five rollback-catalog synthetic cases,
strict CI, hygiene, gate, presentation, performance, documentation and seed
scaffold checks. A Windows PowerShell 5 attempt that lacks
`SHA256.HashData` is environment-only and is not presented as a product failure.

Sanitized evidence SHA-256 is
`2d8f57bfe9ba99285c691c39ece6428836ea6cf4e5065c91e26f4a6fa77a19c8`.

## Release interpretation

- the named candidate.8 excluded-app subcheck advances to PASS;
- the Android physical-device aggregate remains `MANUAL_OWNER_TEST/MATRIX_OPEN`;
- Gate C remains `BLOCKED/I3` below candidate proof for the complete matrix;
- Gate F remains `BLOCKED` at `6 PASS / 13 non-PASS / 0 FAIL`;
- signed candidate.8 and its source tuple remain unchanged;
- no tag, public release, Store object, stable pointer or promotion occurred.

## Required next evidence

1. active WARP traffic rather than fallback-only proof;
2. external IPv6/leak, blocked UDP53 and external MTU checks;
3. broader physical OEM/background and endurance coverage;
4. backup/exposed-port and public/store delivery evidence;
5. the remaining Windows, RU-origin, Smart-DNS, provider, Operator, legal,
   accessibility/performance and post-promotion Gate F rows.
