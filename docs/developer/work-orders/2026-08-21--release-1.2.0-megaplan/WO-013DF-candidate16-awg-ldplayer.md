# WO-013DF — candidate.16 AWG 3.1 and AWG2 LDPlayer result

Status: `EXACT_PROFILE_ACTIVATION_PASS; AWG31_EGRESS_FAIL; AWG2_EGRESS_FAIL; FAIL_CLOSED_CLEANUP_PASS; PROMOTION_BLOCKED`

Observed: `2026-08-31T15:55:14Z`

## Scope

Repeat the guarded AWG 3.1 and AWG2 lanes against exact signed candidate.16 on
the owned LDPlayer emulator after the managed-profile readiness correction.
Prove separately whether the client activates the requested runtime profile,
whether tunnel/DNS/routes form, whether authenticated egress completes, and
whether failure and final default cleanup remain safe.

No physical device, public release, stable pointer, Store object or unrelated
production component is in scope.

## Exact boundary

| Item | Value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.16` |
| Version/build | `1.2.0+4049` |
| Platform source | `719e23dc49407beb9ae30d98d17d4b73d18ae37c` |
| Client source | `75ba7e721cfee486f7189edd51de97aba2746722` |
| Core source | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| x86_64 APK SHA-256 | `73c43e21dfc984c474941e14800c551f9545fe423b8f11458f6d41b8cb9af5ff` |
| Exact install identity SHA-256 | `d0be39313a1e22b3eda1c280a4cdfb465609098a8e4c23e0b0995ec6d9f17f1e` |
| Device | LDPlayer Android 9/API 28, `emulator-5554`, current origin |

The installed `base.apk` hashes byte-for-byte to the candidate.16 x86_64
artifact. All remote bind results are sanitized and return
`raw_identifiers_returned=false`.

## Managed-profile result

Both exact bind PLANs pass without an entitlement extension. Both guarded
APPLYs pass and return the requested resolved profile. On the next connection,
the client stages an internally consistent runtime containing exactly one AWG
endpoint:

- AWG 3.1 readback observes `awg31_lab` and matches the requested profile;
- AWG2 readback observes `awg2_lab` and matches the requested profile.

The candidate.14 `FAIL_MANAGED_PROFILE_ACTIVATION_CACHED_DEFAULT` condition is
therefore closed for candidate.16. Candidate.13's older success is not reused;
this is an independent exact-byte result.

## Transport result

Both current-candidate lab profiles start Android VPN service, create `tun0`,
assign the IPv4 route and reach the application's managed-DNS-ready state.
Neither completes authenticated egress through the selected lab transport.
The UI reports that the test address did not open through the selected
location, keeps protection in a requires-attention state, and does not present
false green.

The exact result for each lane is
`FAIL_EGRESS_NOT_CONFIRMED_AFTER_EXACT_PROFILE_ACTIVATION`. This is now a
runtime/transport result, not the earlier cached-profile control-plane defect.
It does not identify the remaining endpoint, reply-path or client engine
sub-boundary. Two optional read-only remote diagnostics timed out without a
result and are `NOT_RUN_TIMEOUT_NO_RESULT`, not PASS or FAIL evidence.

## Fail-closed and cleanup result

For each failed lab connection, the app removes the system VPN and `tun0` is
absent. Final default PLAN/APPLY passes with no cohort, allowlist, AWG2 material
or AWG 3.1 material retained for the exact install. A fresh ordinary connection
then stages `default`, reaches visible connected state, and disconnects
cleanly. Final `tun0` is absent and the crash buffer is empty.

No physical phone was touched.

## Release decision

`FRKN_PLAN/W3-02` and `W3-03` remain `I3`, now with a stronger but failing
current-candidate runtime boundary: exact profile activation, tunnel, DNS and
routes pass; authenticated egress fails. Gates B, C and E remain `I3` and
blocked. Gate F is still not generated because the exact ARM64 physical binding
is absent and the two current-candidate lab egress checks are non-PASS. Gate G
remains `NOT_AUTHORIZED`.

No completion-index stage changes. Distribution remains `I4=5`, `I3=317`,
`I2=22`, `I1=34`, `I0=0` across `378` rows.

## Evidence

- normalized evidence:
  `evidence/013DF-candidate16-awg-ldplayer/013DF-candidate16-awg-ldplayer.json`;
- normalized evidence SHA-256:
  `0272e02f157ea9d90d9e5ba2e26911bb79abef1c7851f39f80d6401286e41230`;
- external bounded result SHA-256:
  `970f2fb7fc79b07be10eeaffa0cbd7413304bb39b06f6d5d091f8ea0cd945fd8`.

Raw UI and emulator captures remain outside Git in the retained release
evidence root. The normalized record contains only bounded status, counts and
hashes; it contains no endpoint, address, key, credential or raw config.

## Rollback

Rollback is already complete: server-side selection is `default`, lab cohort
and material are absent for the exact install, the app is disconnected, no VPN
interface remains and the ordinary default path revalidated. Any later source
or artifact correction requires a separately signed successor candidate; do
not rewrite candidate.16.
