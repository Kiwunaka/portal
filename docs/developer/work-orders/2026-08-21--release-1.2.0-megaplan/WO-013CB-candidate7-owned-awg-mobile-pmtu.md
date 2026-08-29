# WO-013CB — candidate.7 owned AWG mobile PMTU correction

## Outcome

Close the server/transport boundary identified by WO-013CA without replacing
or forking the pinned official AWG cryptography, repeat both owner-only
profiles on the exact signed candidate.7 ARM64 package over Beeline, and
restore the selected device to the ordinary default profile.

Both profiles now pass on the physical phone. AWG2 and AWG 3.1 each reach the
app's final green state: TUN, managed DNS and authenticated egress are
confirmed. AWG 3.1 additionally passes a secret-free exact-Core interop test
and an independent in-tunnel TCP/TLS/HTTP probe returning the owned `204`
marker.

This supersedes only WO-013CA's causal diagnosis and later runtime result. It
does not rewrite that fail-first evidence or WO-013BZ's immutable candidate.7
Gate F snapshot.

## Root cause and bounded correction

There were three independent layers:

1. The multi-address owned server lacked the persisted reply-source policy
   route/rule. The existing guarded operator installed it, cycled both services
   and read back the live rule, policy route and policy rule.
2. The Beeline path accepted an inner packet ceiling near `1280`; server and
   device material still declared MTU `1408`. A new guarded PLAN/APPLY operator
   moved both owned lab interfaces and both encrypted materials to `1280`,
   retained a root-only backup, restarted the exact services and passed live,
   persisted and material readback.
3. The old AWG 3.1 lab combined randomized trailers with `64-512` bytes of
   data-packet content padding. That additional packet growth black-holed TLS
   on the measured mobile path. The replacement
   `randomized_trailers_mobile_safe_v2` keeps header protection and randomized
   handshake trailers while setting data content padding to `0`.

No cryptographic primitive, handshake algorithm or key format was invented or
forked. The change is transport sizing and server policy around the pinned AWG
implementation.

## Fail-first and rollback honesty

The first AWG 3.1 variant APPLY changed the server, but its live readback
expected a literal zero-valued field. The server UAPI omits that field when it
is zero. The operator returned failure and restored the prior `64-512` variant.

The corrected readback accepts an absent live value as zero only while the
persisted systemd drop-in carries the explicit reset and every header,
random-trailer, port, service and material check passes. The second APPLY and a
later metadata-only reapply both passed. The latter corrected the control-plane
generation, server-record and variant labels to the current mobile-safe values.

## Exact physical result

| Profile | Core/server proof | Exact candidate.7 physical Beeline proof | Result |
|---|---|---|---|
| `awg2_lab` | alignment `11/11`; reply policy persisted; exact Core interop PASS | cold process start; TUN present; app reports tunnel, DNS and egress confirmed | `PASS_PHYSICAL_AUTHENTICATED_EGRESS` |
| `awg31_lab` | alignment `11/11`; reply policy persisted; exact Core interop PASS | TCP 443 PASS, TLS PASS, owned HTTP `204` marker PASS; cold process app reports tunnel, DNS and egress confirmed | `PASS_PHYSICAL_AUTHENTICATED_EGRESS` |

One warm app session retained a stale yellow diagnostic after multiple live
server rewrites. A process-cold repeat on the same selected profile reached the
green terminal state. The stale observation remains recorded and is not used
as the final result.

## Source correction

- new generated owned-lab material and server configs use MTU `1280`;
- `scripts/remote_set_owned_awg_mtu.py` owns guarded migration and readback;
- `scripts/remote_set_owned_awg31_variant.py` can migrate the legacy padded
  variant and understands zero-valued live UAPI omission without weakening the
  persisted checks;
- the activation helper now writes the current AWG 3.1 generation, server
  record and variant metadata rather than the superseded labels;
- focused platform tests cover the MTU transform, legacy migration,
  zero-omission readback and helper metadata.

## Release disposition

The candidate.7 Android bytes are now physically proven for both owned AWG
profiles. The full signed candidate.7 tuple is still not promoted: the
reproducible platform provisioning source changed after signing, and the phone
also exposed a separate Android notification false-green that belongs in the
successor client source. Candidate.8 must bind those source corrections before
a new Gate F.

Windows AWG app/service/TUN parity, Android leak/network-change/OEM/endurance,
exact RU execution, live Smart DNS, provider, Operator, legal/commercial and
the remaining manual gates stay open. `FRKN_UNCERTAINTY/UNCERT-02` advances
from `I1` to `I3` because owned mobile compatibility is now measured and
passing; no item advances to `I4`.

The original 377-row distribution becomes `I4=4`, `I3=316`, `I2=21`,
`I1=36`, `I0=0`. Including the derived Smart-DNS row, the ledger remains 378
rows and 321 are at or above `I3`.

## Cleanup

Final guarded default PLAN/APPLY readback reports
`selected_profile=default`, `resolved_profile=legacy_reality_fallback`, no lab
cohort/allowlist identity and no AWG material for the selected install. The
phone ends with no VPN/TUN, WARP off, Wi-Fi off, mobile data on and Private DNS
`off`. Temporary phone-side probe and UI files were removed. No entitlement,
payment, repository visibility, tag, public release, store or stable-pointer
mutation occurred.

## Evidence

The secret-free normalized record is
`evidence/013CB-candidate7-owned-awg-mobile-pmtu/013CB-candidate7-owned-awg-mobile-pmtu.json`.
Its SHA-256 is
`a57deb90907cc2d34ec237b4781d81faa18e0fd8ca7b0f26397b7140ae3ffce4`.
It binds hashes for the external candidate evidence under
`E:/POKROV-tools/release-candidates/pokrov-1.2.0-candidate.7/`. No raw device
identifier, address, hostname, key or endpoint material is retained.
