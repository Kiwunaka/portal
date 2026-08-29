# WO-013CA — candidate.7 physical AWG differential

Historical fail-first record. WO-013CB supersedes the causal diagnosis and
later runtime result after guarded server reply-policy, PMTU and AWG 3.1
padding corrections; this record and its hashes remain unchanged evidence.

## Outcome

Run the exact signed candidate.7 ARM64 package on the owner's physical Android
device over Beeline, compare the two default-off owned AWG profiles against the
ordinary release profile, and restore the device and server-side selection.

The ordinary `legacy_reality_fallback` control passes on the same package,
device and mobile origin. AWG2 and AWG 3.1 each create an Android-validated VPN,
TUN, IPv4 route and managed DNS, but POKROV cannot confirm the selected exit.
Both lab slices are therefore `FAIL_AUTHENTICATED_EGRESS_NOT_CONFIRMED`.
Candidate.7 is `REJECTED_FOR_REPLACEMENT`; this is no longer attributable to
the common LDPlayer network boundary.

## Exact identity and initial state

| Item | Retained value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.7` |
| Version/build | `1.2.0+4046` |
| ARM64 APK SHA-256 | `b583205db9e197c6de873264821319ef1108a2786f1ee5466501712568147296` |
| Install identity | exact candidate hash match; raw identifier not retained |
| Origin | Beeline mobile data |
| Initial network state | Wi-Fi off, mobile data on, Private DNS `off` |
| Initial client state | default profile, WARP off, no VPN/TUN, not protected |

No screenshot, raw device serial, IP, hostname, endpoint, key, profile material
or unrelated phone notification is retained.

## Profile matrix

| Profile | Control plane | Android/TUN | POKROV proof | Result |
|---|---|---|---|---|
| `awg2_lab` | PLAN/APPLY PASS; exact target and entitlement confirmed | VPN connected and Android-validated; `tun0`; IPv4 route `1`, IPv6 `0`; managed DNS ready | tunnel requires attention; selected exit not confirmed | `FAIL_AUTHENTICATED_EGRESS_NOT_CONFIRMED` |
| `awg31_lab` | PLAN/APPLY PASS; exact target and entitlement confirmed | same validated VPN/TUN/route/DNS shape | tunnel requires attention; selected exit not confirmed | `FAIL_AUTHENTICATED_EGRESS_NOT_CONFIRMED` |
| `default` | PLAN/APPLY PASS; resolves to `legacy_reality_fallback`; cohort/allowlist and both AWG material rows absent for the selected install | VPN connected and Android-validated; `tun0` | POKROV foreground state reports protection enabled | `PASS_PHYSICAL_MOBILE_CONTROL` |

No fatal exception, ANR, native fatal signal or `SecurityException` was observed
in the bounded AWG slices. That only proves host stability. A created or
Android-validated TUN is not counted as AWG success without POKROV's selected
exit proof.

## Differential conclusion

The default control removes the earlier LDPlayer ambiguity. The package,
device, mobile carrier, Private DNS state and test interval are shared, while
only the managed transport changes. Ordinary protected egress passes and both
owned AWG profiles fail at authenticated selected-exit proof. The supported
next diagnosis boundary is the AWG server/transport path, not the generic
Android client or a blanket Beeline outage.

This is a mandatory replacement trigger under the owner's requested AWG lane.
The remaining physical Android WARP, per-app, network-change, OEM/Doze,
DNS/IPv6 leak, endurance and recovery matrix is still incomplete and is not
promoted to PASS.

## Gate and release disposition

WO-013BZ's first candidate.7 Gate F is an immutable digest-bound snapshot at
`BLOCKED: 4 PASS / 15 non-PASS / 0 FAIL`. It is not rewritten. This later
exact-candidate stop-ship evidence rejects candidate.7 for replacement and
prohibits Gate G, a tag, public assets, stores and the stable pointer.

A successor Gate F should be generated only for replacement candidate bytes
after the AWG failure is corrected and the required row has complete exact
evidence. The ledger remains 378 unique rows with no completion-index advance.

## Cleanup

The guarded default PLAN/APPLY restored `selected_profile=default` and
`resolved_profile=legacy_reality_fallback`. Lab cohort and allowlist membership
are absent, and neither AWG material is provisioned to the selected install.
The client disconnected cleanly. Final device readback is:

- no active POKROV VPN or TUN;
- UI `Не защищено` with `Подключить`;
- WARP off;
- Wi-Fi off, mobile data on and Private DNS `off`, matching the initial state.

No entitlement extension, deploy, restart, payment action, repository
visibility change, tag, release, store object or stable-pointer mutation
occurred.

## Evidence

Machine evidence is under
`evidence/013CA-candidate7-physical-awg-differential/`.

| Evidence | SHA-256 |
|---|---|
| normalized physical runtime | `38a263f9b64edafed9996658b75ee5418872a25a32507253dcbb63fb195cd174` |
| baseline UI tree | `bd136b2907d2992e7e2a6f51fb87a03844bb51a406989605f51b0b973f47a4a1` |
| AWG2 expanded state | `514601c07f9d453ffccbeb658bb88cfef8eaecc8055eba79524cbe0b6fea8c79` |
| AWG 3.1 expanded state | `e53ab019814cc66a87d840d51f6fe542decfde63030543b2b8adb67b153d31f1` |
| final default UI tree | `c1b5fbae668780de6afb62179c84d27dabc4a1d1c5e21b00bb722d1caf868ebf` |

The six binder reports are also retained with their hashes inside the
normalized evidence file. They contain only counts, booleans, bounded safe
events and one-way digests; `raw_identifiers_returned=false`.

## Verification boundary

```text
exact candidate.7 ARM64 package readback
# PASS: 1.2.0+4046, APK SHA-256 matches signed candidate

guarded binder PLAN/APPLY: awg2_lab -> awg31_lab -> default
# PASS: exact target confirmed; no entitlement extension; final default restore

physical Beeline runtime: awg2_lab
# FAIL_AUTHENTICATED_EGRESS_NOT_CONFIRMED

physical Beeline runtime: awg31_lab
# FAIL_AUTHENTICATED_EGRESS_NOT_CONFIRMED

physical Beeline runtime: legacy_reality_fallback
# PASS_PHYSICAL_MOBILE_CONTROL

final Android/system readback
# PASS: no VPN/TUN; default; WARP off; Wi-Fi off; mobile on; Private DNS off
```
