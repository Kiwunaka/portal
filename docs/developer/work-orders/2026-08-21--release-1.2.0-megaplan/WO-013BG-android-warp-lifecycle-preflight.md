# WO-013BG — Android WARP and lifecycle preflight

## Outcome

Run the next bounded Android runtime slice on the exact resolver-corrected
working APK without converting emulator or partial system evidence into a
physical WARP pass.

On LDPlayer, a WARP-enabled connection created the Android VPN transport, then
failed the required Core egress probe. The client performed its designed
ordinary-profile fallback, created a second TUN and failed the same probe with
terminal `EGRESS-001`. A separate WARP-disabled control then failed with the
same terminal code. This isolates the current LDPlayer result to the emulator
network/origin boundary; it does not prove a WARP regression or WARP egress.

On the connected physical Huawei, the app-owned service and TUN survived one
Wi-Fi to Beeline LTE to Wi-Fi sequence, forced Doze and app standby. The device
was then restored to Wi-Fi, mobile enabled, Doze active and app standby false;
the app was force-stopped and service/TUN absence was read back. Protected
egress and WARP UI state were not observed through the secure keyguard, so this
is partial host-lifecycle evidence only. The WARP preference restoration and
the remaining physical test are waiting for an owner unlock.

## Exact boundary

| Item | Exact identity | Result |
|---|---|---|
| Platform release truth | `bb1ebbaf47ddf4c77b9c7cb14d7802ff401c5c55` | clean release worktree before this record |
| Client release truth | `b2497af7704d0aa6901541e175ce154b0eab05d7` | exact canonical client evidence; clean and equal to `origin/main` |
| Runtime client binding | `68779c4dc806c2153d415ca8ca186c9130502f21` | production-signed working Android bytes |
| Core | `a45d69e40ed7d892619a2b5c4592a527f630665e` | exact resolver-corrected runtime |
| LDPlayer APK | `109952213` bytes; `3d95d82d…6fa4` | exact installed x86_64 `1.2.0+4046`; Android 9/API 28 |
| Physical APK | `101366934` bytes; `b583205d…7296` | exact installed ARM64 `1.2.0+4046`; Huawei/Android 12 |

## Runtime results

### LDPlayer

- WARP enabled state before connect: `PASS_UI_READBACK`;
- WARP primary TUN creation: `PASS_HOST_TRANSPORT_CREATED`;
- WARP primary selected-outbound egress: `FAIL_EGRESS_001`;
- automatic ordinary fallback TUN creation: `PASS_HOST_TRANSPORT_CREATED`;
- ordinary fallback selected-outbound egress: `FAIL_EGRESS_001`;
- independent WARP-off ordinary control: `FAIL_EGRESS_001`;
- WARP disabled readback after the controls: `PASS`;
- final POKROV service and `tun0` absence: `PASS`.

Classification:
`BLOCKED_BY_LDPLAYER_NETWORK_CURRENT_ORIGIN`, not a WARP-specific failure and
not a physical or candidate pass. Repeating either path on the unchanged
emulator would not add evidence.

### Physical Android

- exact package/version readback: `PASS`;
- service/TUN continuity across Wi-Fi/LTE/Wi-Fi: `PASS_HOST_LIFECYCLE_ONLY`;
- service/TUN continuity through forced Doze and app standby:
  `PASS_HOST_LIFECYCLE_ONLY`;
- final network/Doze/standby restoration: `PASS`;
- final service/TUN absence after force-stop: `PASS`;
- WARP protected egress, fallback generation and UI terminal state:
  `NOT_OBSERVED_SECURE_KEYGUARD`;
- WARP preference restoration: `BLOCKED_BY_SECURE_KEYGUARD_OWNER_UNLOCK`.

The host-lifecycle slice does not prove DNS, IP/HTTPS egress, per-app routing,
Private DNS, IPv6 leak, notification/tile control, OEM process death, battery,
thermal or endurance behavior.

## Release interpretation

- No execution-ledger row advances and Phase 10/11 remain at their existing
  indices.
- Candidate.5 remains immutable and rejected; no replacement candidate exists.
- Android exact-candidate WARP, full network/lifecycle, per-app, OEM, leak and
  endurance gates remain open.
- No backend deploy, cohort change, tag, release asset, stable pointer or
  publication occurred.

Machine evidence:
`evidence/013BG-android-warp-lifecycle-preflight/013BG-android-warp-lifecycle-preflight.json`.
Its SHA-256 is
`eab077cc30a01b580e709bf7c1af627c49ad8ace785396f6c338e3b469573243`.
It retains no endpoint, address, key, config, device serial, install ID,
account identifier, screenshot or raw UI/journal payload.
