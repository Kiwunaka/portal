# WO-013EZ — candidate.22 packaged Windows AWG 3.1 and AWG2

Status: `PASS_EXACT_CANDIDATE22_WINDOWS_PACKAGED_AWG31_AWG2`

Observed: `2026-09-02`

Production/public mutation: `TEMPORARY_GUARDED_OWNER_LAB_BIND_RESTORED`

## Outcome

Run the exact installed candidate.22 Windows client against the existing
default-off owned AWG laboratories. The target is selected by the SHA-256 of
its app-first install identity; the guarded PLAN resolves exactly one active,
entitled Windows device and confirms both source materials are ready without
returning a raw identifier or connection material.

AWG 3.1 is selected first. The client fetches exact profile revision
`awg31-lab-v4-mobile-safe-trailers`, starts the packaged Core and one Windows
TUN, applies routes, passes its DNS and egress gates and renders connected.
Independent Windows requests resolve four controls, complete certificate-valid
HTTPS, reach the DE exit and pass ICMP. AWG2 is then selected, the application
is relaunched to refresh the externally changed owner-lab policy, and exact
revision `awg2-lab-v1` passes the same packaged Core, TUN, route, DNS, egress,
HTTPS, DE-exit and ICMP checks.

The first hot AWG3.1-to-AWG2 control-plane transition is deliberately excluded
from AWG2 evidence: the still-running client reused its already loaded AWG3.1
profile. After the application relaunch the revision changes to AWG2 and only
that run is counted. This is an owner-lab refresh boundary, not a user-facing
transport selector or a release claim.

Cleanup removes the exact install and user from the cohort and both lab
allowlists. Readback resolves `legacy_reality_fallback`; after relaunch the
ordinary profile reconnects successfully, then disconnect restores the DHCP
resolver, leaves no active `tun0`, keeps the automatic service running and
leaves zero POKROV crash dumps.

## Exact evidence

| Item | Value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.22`, `1.2.0+4051` |
| UI SHA-256 | `40ce4cc4520709aa4714737776aea2ada4a2043d7a346ce3d708a07160b7d66c` |
| Service SHA-256 | `18191f195309460b9d72a4a91a3fc817f3b3610d32891858a0ddddedaae11fb6` |
| Core SHA-256 | `f284fa8841f1a45271874a7a05ed6093fb0e3efbdd03e00001edd046be708204` |
| AWG 3.1 profile | `2026-06-01-direct-default-recovery:awg31_lab:awg31-lab-v4-mobile-safe-trailers` |
| AWG2 profile | `2026-06-01-direct-default-recovery:awg2_lab:awg2-lab-v1` |
| Exit | `DE`, identical privacy-safe address digest for both runs |

The normalized record retains only candidate identities, public profile
revisions, counts, booleans, response classes and hashes. It contains no raw
profile, key, endpoint material, credential, customer identifier or raw exit
address.

## Explicit non-PASS boundary

Server-side packet capture is `BLOCKED_BY_ACCESS`: the database-selected DE
address is not present in the local strict `known_hosts` file for the service
port. No key is accepted and no client PASS is relabelled as server capture.
The current evidence therefore proves packaged Windows Core/TUN/DNS/egress,
not an independent packet-direction or handshake-counter record.

Candidate.22 packaged Android, physical Wi-Fi/Beeline, direct UDP, IPv6,
forced MTU failure, sleep/resume, endurance and authenticated target sessions
remain `NOT_RUN`. No cross-platform or multi-ASN completion is inferred.

## Completion index and next boundary

`FRKN_PLAN/W3-02` and `W3-03`, `FRKN_AWG/AWG-03`, `AWG-05`, `AWG-07`,
`AWG-09` and `AWG-10`, `REL/WIN-003`, `REL_GATE/GATE-C` and
`REL_DOD/DOD-04` gain exact candidate.22 packaged Windows evidence without a
level change. Gate F remains the immutable WO-013EX `BLOCKED 3 PASS / 16
non-PASS / 0 FAIL`: its complete Windows and cross-platform authenticated
client rows still have other required slices open.

Next priority is exact candidate.22 packaged Android AWG3.1 then AWG2 on the
physical phone over Wi-Fi and Beeline. Separately reconcile the DE host-key
alias before retaining server packet counters, then complete UDP/IPv6/MTU,
network-change, lifecycle and endurance matrices. Gate G, public assets,
Store upload and stable promotion remain unauthorized.

## Evidence

- `evidence/013EZ-candidate22-windows-awg/013EZ-candidate22-windows-awg.json`;
- SHA-256
  `11dc27f9c7c7bba14928333c920482e5c01ec7a56e5a9c4d324dfc258d974902`.
