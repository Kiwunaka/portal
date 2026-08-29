# WO-013BB — Owned AWG reply routing and physical recheck

## Outcome

The owned `de` AWG node is multi-addressed. Both bounded profiles received
valid client initiations and produced cryptographic responses, but the normal
host route selected a different public source than the address used by the
client endpoint. Beeline therefore received no usable reverse packet. The
failure was outside the AWG2/AWG 3.1 cryptography and outside the corrected
POKROV bind adapter.

Platform commit `f79974c99adc4f00d6fa31f736d40c2cc10d0ee6` adds a guarded
PLAN/APPLY operator and makes the reply policy part of new owned-lab server
configurations. Each lab source port gets its own policy-routing table and
source-port rule before the existing narrow SNAT. The route selects the exact
endpoint address before packet emission; the SNAT remains a bounded final
guard. Both rules are limited to the owner-only UDP listeners and are removed
by the matching `PostDown` path.

The correction was applied only to the default-off `awg2_lab` and
`awg31_lab`. Backup, exact readback and service stop/start proof passed. No
ordinary VPN listener, public profile, key, cryptographic primitive or client
material changed.

## Root-cause evidence

| Probe | Server receive | Physical Beeline reverse path | Interpretation |
|---|---:|---:|---|
| normal route, AWG2 port | `3/3` | `0/3` | route-selected source differed from ingress |
| normal route, AWG 3.1 port | `3/3` | `0/3` | same shared node boundary |
| ingress-address `IP_PKTINFO`, both ports | `3/3` | `3/3` | carrier accepts a tuple-correct response |
| late SNAT only, AWG2 port | `3/3` | `0/3` | source rewrite after route selection is insufficient |
| source-port policy route, AWG2 port | `3/3` | `3/3` | pre-emission route/source selection is the correction |

Live client/server material alignment v2 passed for both profiles before the
network mutation. The official pinned Core peer also passed both profiles
after the correction and again after the service cycle. This rules out a need
to fork or alter the protocol cryptography.

## Guarded server correction

`scripts/remote_ensure_owned_awg_reply_source.py`:

- resolves the enabled owned node through Brain and retains only the endpoint
  address SHA-256;
- requires one public IPv4 assigned to `eth0`, one main default route through
  `eth0`, a gateway, and kernel UDP source-port rule support;
- rejects occupied policy priorities/tables, duplicate managed SNAT rules,
  conflicting configuration or inactive/mismatched lab services;
- creates a root-only server backup before mutation;
- injects idempotent `PostUp`/`PostDown` policy route, source-port rule and
  narrow SNAT lines for only `4500/udp` and `3478/udp`;
- applies and reads back the matching live state without returning addresses,
  keys or material;
- restores the saved configurations and services if APPLY or optional service
  cycling fails.

The final service-cycle APPLY returned `ok=true`, one managed SNAT rule per
profile, both policy routes/rules present, both services active and
`service_cycle_pass=true`. Rollback was not required.

## Physical replacement result

The exact production-signed replacement Android artifact was
`1.2.0+4046`, ARM64 SHA-256
`930aec975927c1c40a87440f62f67b25295a12920e85876adca297b715426058`,
from client `7a633a83ca6605df9d06b8bf17a7c36240824bbb` with Core
`3c2b1147c1b42e39026231525c08558a50bc3d0f`. The physical Android run used
Beeline cellular data with Wi-Fi disabled. No raw device identity is retained.

| Profile | Authenticated handshake | Outer traffic | Inner traffic | Result |
|---|---|---|---|---|
| `awg2_lab` | fresh, age `10s` at outer readback | `177` inbound / `277` outbound | `3` from client / `3` to client | `PASS_PHYSICAL_PRE_CANDIDATE` |
| `awg31_lab` | fresh, age `15s` at outer readback | `67` inbound / `76` outbound | owned-site browser slice: `6` from client / `7` to client | `PASS_PHYSICAL_PRE_CANDIDATE` |

After the server service cycle, exact current-origin Core interop returned
`passed` for AWG2 and randomized-trailer AWG 3.1. This proves live official
client/server interoperability after persistence, not only one Android UI
state.

## Cleanup and release interpretation

- POKROV was disconnected and force-stopped after the runs.
- The exact device was rebound to `default`; lab cohort membership and both
  material deliveries read back absent.
- Wi-Fi was restored and the previously active VPN app was reopened. Its
  connection was not changed or claimed.
- Candidate.5 remains immutable and `REJECTED_FOR_REPLACEMENT`.
- These are production-signed replacement bytes on a physical mobile origin,
  but they are not an immutable release candidate. Phase 10 therefore remains
  `I3`, not `I4`.
- A new digest-bound candidate, exact-candidate Android repeat, Windows parity,
  DNS/leak/origin matrix and Gate F remain open. No tag, public asset, store
  upload, stable switch or promotion occurred.

## Verification and retained evidence

Focused release/AWG checks pass with `66 passed, 29 subtests passed`; Ruff,
script-manifest and diff checks pass. Machine-readable evidence is retained at
`evidence/013BB-owned-awg-reply-routing/013BB-owned-awg-reply-routing.json`,
SHA-256
`07d422f1b4693d926c786211e513fe6261e96f8a56bd0cd8a705eb9cc51972a5`.
It contains no raw address, device identifier, account identifier, key,
credential or endpoint material.
