# WO-013AZ — AWG bind contract correction and replacement runtime recheck

## Outcome

The replacement Core had one concrete `conn.Bind` contract defect: `Open(0)`
opened real UDP packet connections but returned port `0`, requested IPv6 on
port `0` again and leaked the IPv4 packet connection when IPv6 setup failed.
Core commit `6b8ddcadeec6c261220f2f2a2e996c6179081634` now reports the allocated
port, requests that port for the second family, closes partial state on error
and fails with `EAFNOSUPPORT` when neither family can open. The regression test
was observed failing before the correction and the focused plus full Core
gates pass after it.

This correction is real but it is not the AWG handshake root-cause fix.
Production-signed diagnostic replacement bytes using that Core were installed
on the owned LDPlayer. Both `awg2_lab` and `awg31_lab` again created an Android
VPN transport, stayed in the client checking state and emitted the bounded
diagnostic `AWG · handshake_retry · #4`. Literal-IP ICMP passed; DNS-name ICMP,
literal-IP HTTPS, DNS-name HTTPS and authenticated egress did not pass.

Candidate.5 remains immutable and `REJECTED_FOR_REPLACEMENT`. No release row
advances, no replacement candidate exists and no physical-device, Beeline or
RU-origin result is inferred from this emulator rehearsal.

## Exact source and artifacts

| Component | Exact identity |
|---|---|
| Platform evidence source | `63241eb8743ecedce9fc80a4e6ee9f696548aece` before this work order |
| Client source | `7a633a83ca6605df9d06b8bf17a7c36240824bbb` |
| Core source | `6b8ddcadeec6c261220f2f2a2e996c6179081634` |
| Core Android AAR | 107,408,874 bytes; SHA-256 `b42a548910b7369f64fcd484c5acf74180583d77299629ce4d2f9156fc598007` |
| ARM64 diagnostic APK | 101,357,398 bytes; SHA-256 `930aec975927c1c40a87440f62f67b25295a12920e85876adca297b715426058` |
| x86_64 diagnostic APK | 109,942,293 bytes; SHA-256 `8f6f1e96ad019774c071ffee6b089696068f1c7655ad012efca41dcadb15fd49` |
| Android certificate | SHA-256 `0A0602A7DF5D96A0B427909D004F3DDF26DEF86587634BF16694DA8D654B2500` |
| App identity | `1.2.0+4046`; diagnostic pre-candidate, not candidate.5 and not release |

The exact prior tracked client AAR was restored after the isolated build:
107,390,782 bytes, SHA-256
`7c392883ee8a09c15e414a0e9d70a4d4d3cb259032e51c5481cd14a571950745`.
The client and Core worktrees were clean at evidence capture.

## Runtime comparison

| Profile | Android/UI boundary | Bounded Core diagnostic | Independent network smoke | Verdict |
|---|---|---|---|---|
| `awg2_lab` | VPN present and Android-validated; POKROV remained checking/requires attention | `handshake_retry #4` | literal IP ping PASS; DNS-name ping FAIL; literal-IP HTTPS FAIL; DNS-name HTTPS FAIL | `FAIL_HANDSHAKE_AND_EGRESS_UNCHANGED` |
| `awg31_lab` | VPN present and Android-validated; POKROV remained checking/requires attention | `handshake_retry #4` | literal IP ping PASS; DNS-name ping FAIL; literal-IP HTTPS FAIL; DNS-name HTTPS FAIL | `FAIL_HANDSHAKE_AND_EGRESS_UNCHANGED` |

The Android connectivity service marking the VPN transport validated does not
prove an AWG handshake or authenticated exit. The client therefore remains
non-green. The diagnostics-screen DNS label is not promoted over the failed
independent DNS-name smoke.

The source-level owned interop probe from current Windows origin also failed
for both profiles with `failed_no_outer_response`. That is useful origin
separation: it does not reproduce candidate.5's physical Beeline observation
where outer packets returned, and it cannot diagnose the physical rejection by
itself.

After both runs the app was force-stopped, Android exposed no active POKROV
VPN, the guarded binder restored `default`, readback resolved
`legacy_reality_fallback`, and cohort/lab membership was absent. No extra
entitlement day was granted in this slice. Raw device, account, endpoint, key
and packet material is absent from retained evidence.

## Verification

- Pre-fix focused regression: failed with allocated port expected and `0`
  returned.
- Post-fix `go test ./transport/awg -count=1`: PASS.
- Post-fix `go test ./transport/awg ./protocol/awg -count=1`: PASS.
- Core `scripts/test.ps1` under Go 1.25.13: PASS, including brand, ABI,
  observability, AWG2, AWG 3.1, HY2 and release-CI contracts.
- Production Android builder: PASS for universal and three ABI APKs; retained
  ARM64/x86_64 sign with the existing production certificate.
- Client tracked Core AAR restore and clean-worktree readback: PASS.
- Normalized evidence:
  `evidence/013AZ-awg-bind-contract/013AZ-awg-bind-contract.json`, SHA-256
  `52af7e99ab4ff55c867cbb4e23414fe2b0a9d1d4fee1daf05a830924a2ba2060`.

## Release interpretation and next action

- Keep Core commit `6b8ddca` as a reviewed replacement correction; do not claim
  that it fixed the live handshake.
- Candidate.5 and its frozen Gate F report remain unchanged.
- Do not assemble a replacement candidate from these bytes.
- The next diagnostic must distinguish the physical mobile-origin returned
  datagrams at the bounded parser boundary using the already allowlisted
  unknown-type/MAC/response codes. The current phone is not online in ADB, so
  that exact physical slice remains `MANUAL_OWNER_TEST`, not emulator PASS.
- Continue official pinned AmneziaWG interoperability work; do not fork or
  modify cryptography.
