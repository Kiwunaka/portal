# WO-013AL — Exact candidate.3 Gate C decision

Status: `EXACT_CANDIDATE_PLATFORM_MATRIX_BLOCKED_I2`
Classification: `ACTIVE_EXECUTION_EVIDENCE`
Phase: `03`, decision replay in Phase `11`
Row: `REL_GATE/GATE-C`
Candidate: `pokrov-1.2.0-candidate.3`
Production/external mutation: `NONE`

## Outcome

Evaluate Gate C against the signed candidate instead of transferring current
client main, post-candidate Linux or phone-lab evidence. Candidate.3 contains
the implemented Windows and Android lanes and the exact Core ABI. Its Windows
installer passes a bounded clean-host service/IPC lifecycle, and its universal
Android APK again passes exact-byte LDPlayer package and launch readback.

The required platform matrices are still incomplete. Windows lacks live
TUN/DNS/egress and connected recovery. LDPlayer has no active entitlement, so
Android catalog/TUN/DNS/egress cannot be tested; physical API/OEM/network/power
and Play-managed store paths remain manual. Linux is deliberately absent from
candidate.3 and from the 1.2.0 public Android/Windows pair. Gate C therefore
returns `BLOCKED`, exposes no new candidate defect and remains `I2`.

## Exact candidate result

| Requirement | Result | Exact boundary |
|---|---|---|
| Windows service/helper | `PASS_PARTIAL_EXACT_CANDIDATE` | Installer `9962e3e8...` passes clean install, eight-file identity, LocalSystem service, authenticated IPC, restart, uninstall and unchanged idle route/DNS state. Live connected networking and recovery remain `MANUAL_OWNER_TEST`. |
| Android service split | `PASS_SOURCE_AND_INSTALL_PARTIAL_RUNTIME` | Exact source lifecycle/error fencing passes `45/45`; state/diagnostics/migrations pass `107/107`; signed universal APK `f41c76eb...` launches on LDPlayer without a crash or VPN false green. Authenticated runtime remains access-blocked. |
| Direct/store flavors | `PASS_SOURCE_AND_ARTIFACT_PARTIAL_RUNTIME` | Signed artifact set contains direct APK variants and the market AAB under the production certificate. Physical direct permission/upgrade and Play-managed store update remain manual. |
| Conditional Linux beta | `NOT_SHIPPED_IN_CANDIDATE3` | Candidate.3 contains no Linux source or artifact. The later fail-closed daemon/non-root UI foundation is source-only and cannot be credited retroactively. |
| Core ABI/CI matrix | `PASS_EXACT_CANDIDATE_SOURCE_AND_ARTIFACT` | Exact Core `344b317...` passes observability/libbox/ABI contracts; Windows runtime engine passes `63/63`, including 100 start/stop cycles, and native contracts pass `7/7`. |

## Fresh LDPlayer readback

LDPlayer 9 `emulator-5554` reports Android 9/API 28 and model `SM-S9280`.
Installed package `space.pokrov.pokrov_android_shell` is `1.2.0+30`; on-device
SHA-256 of `base.apk` is exactly
`f41c76ebf7bf69f6681d7df87e7722dcdccdec383ef950156b69829caee71c51`,
matching the signed manifest and the retained pulled APK.

The exact activity starts successfully in `568 ms`, the process remains alive,
the package crash buffer is empty and the UI remains `Не защищено`. No VPN
transport or TUN interface exists. No connect action was repeated: the expired
account already makes authenticated network proof unavailable, and another
SPB attempt would add no Gate C evidence.

Sanitized screenshot/UI-tree captures are retained outside the repository at
`E:/POKROV-tools/release-evidence/1.2.0-candidate3-gate-c-2026-08-27` with
SHA-256 `a8bdff70...` and `7781d5cf...`. The connected physical phone was not
used and its post-candidate lab build was not overwritten.

## Decision boundary

Gate C does not pass from source tests or compilation. Its exact candidate
decision is `BLOCKED`, not `FAIL`: no new platform defect was observed, but the
required runtime evidence is unavailable or manual. Candidate.3 remains
overall `NO_GO` because Gate B already has an explicit frozen-source failure.

Linux does not block this candidate's declared Android/Windows public pair.
If Linux is selected for 1.2.0 later, it requires a replacement candidate with
live Core/TUN, NetworkManager/resolved/nft rollback, a signed package and a
clean Ubuntu network/recovery matrix.

## Evidence digests

| File | SHA-256 |
|---|---|
| `013AL-gate-c-test-evidence.json` | `51485c2b02487d196ea24f5c7b3e35c7126add9a72e66162f774dd635b2c3347` |
| `013AL-gate-c-decision.json` | `58aeaf052b6b3bf14051990c4daf41f9bddc97fe3ce2df5b115221fe34bc5988` |

The decision binds candidate identity and the exact platform boundaries; it
does not authorize production, publication or Gate G.

## Ledger decision

`REL_GATE/GATE-C` remains `I2`; its status becomes
`EXACT_CANDIDATE_PLATFORM_MATRIX_BLOCKED`. Distribution remains `I4=4`,
`I3=312`, `I2=19`, `I1=41`, `I0=1`.

## Next action

Use an active owned entitlement for exact-candidate Android catalog/TUN/DNS/
egress on LDPlayer, then run the same bytes on the physical API/OEM/network and
store/direct matrix. Separately execute the Windows 10/11 live network and
connected recovery matrix. Do not spend more time on SPB without evidence that
the location itself is the failing Gate C boundary. Linux remains outside the
candidate unless the owner explicitly adds it to the release scope.
