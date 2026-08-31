# WO-013DH — candidate.16 DE provider outage and guarded AWG retry boundary

Status: `PARTIAL_PROVIDER_RECOVERY_INCOMPLETE; AWG_PROTOCOL_RESULT_NOT_RUN`

Observed: `2026-08-31T16:22:15Z` through `2026-08-31T18:16:59Z`

## Scope

Classify the shared candidate.16 AWG2/AWG3.1 egress failure against exact Core
from the owned RU Raspberry Pi, verify whether the owned DE node is available
after the owner begins correcting the provider account state, and prevent a
provider outage from being recorded as a protocol failure.

No server mutation, protocol-parameter change, endpoint-material change,
physical-device action, LDPlayer retry, public release, stable pointer or
Store action is in scope while the owned node is unavailable.

## Exact boundary

| Item | Value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.16`, `1.2.0+4049` |
| Candidate Core source | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Execution host | owned Raspberry Pi 4, Linux ARM64, direct RU fixed-network route |
| AWG2 binary SHA-256 | `2fc69b97c198c35d8c2995a564d6ef81bd3ecd2d8b4b128bda79609164033ae0` |
| AWG3.1 binary SHA-256 | `9f5f53bd755d06ddac384b104be3d4a3659feaf6a25095477eba08e896a1bb7c` |
| Node | owned `de` |
| Provider state | owner attests account was unpaid; payment correction in progress |

The exact runner exported only candidate.16 Core, cross-built one digest-bound
ARM64 test binary per profile, verified the Pi direct-default-route preflight,
sent endpoint material only over process stdin, retained no raw material, made
no server/runtime mutation and removed its exact temporary remote state.

## Exact-Core observations

Both profiles ended as `failed_no_outer_response`:

| Profile | Material SHA-256 | Result |
|---|---|---|
| AWG2 | `07ae6a2f8bdbfc3bd78bb6fabf105db5380f1bf9a0989efed7a8330d0f7648a9` | no outer response |
| AWG3.1 | `7effbffdbab9013e682f60832c89d488ef0ecfe0829c4e8acb788918bbfaea50` | no outer response |

Those material fingerprints are byte-identical to the retained candidate.10
RU-Pi runs where both profiles passed verified TLS and authenticated egress.
This does not transfer an old PASS to candidate.16; it only proves that the
client-side material input did not change between the older passing run and
the current outage observation.

## Provider recovery check

After the owner reported the unpaid Datalix account and began correcting it,
the node recovered only partially:

- current-origin TCP accept returned on the primary SSH and HTTPS ports;
- neither DE address produced an SSH banner;
- the owned RU Pi independently received no SSH banner from either address;
- the secret-safe AWG alignment could not reach a completed remote readback
  and was stopped without mutation;
- no service, listener, firewall, route, key or live handshake readback was
  available.

This is `PROVIDER_RECOVERY_INCOMPLETE`. A TCP accept without an SSH banner or
service readback is not node health and not a protocol result.

## Decision

WO-013DF's exact LDPlayer profile activation, TUN, DNS and route observations
remain valid. Its authenticated-egress failure is now bounded by an
independently observed shared owned-node outage, but it is not converted into
PASS. Candidate.16 AWG2 and AWG3.1 protocol interoperability remain
`NOT_RUN_AFTER_PROVIDER_OUTAGE_CLASSIFICATION` until the node is fully
responsive.

`FRKN_AWG/AWG-10` remains `I2`; `FRKN_PLAN/W3-02` and `W3-03` remain `I3`.
Gate B, Gate C, Gate E and Gate F do not advance. The 378-row distribution
remains `I4=5`, `I3=317`, `I2=22`, `I1=34`, `I0=0`. Gate G remains
`NOT_AUTHORIZED`.

The next authorized sequence is strictly:

1. prove both DE SSH and ordinary service readback;
2. run secret-safe alignment for AWG2 and AWG3.1;
3. rerun exact candidate.16 Core interop from the owned RU Pi;
4. only after Core PASS, repeat candidate.16 AWG3.1/AWG2 on LDPlayer;
5. leave the physical phone untouched unless the owner separately reopens it.

Do not alter protocol parameters or spend release time on SPB while the owned
DE node is not healthy.

## Evidence

- normalized record:
  `evidence/013DH-candidate16-de-provider-outage/013DH-candidate16-de-provider-outage.json`;
- normalized record SHA-256:
  `d57e3e763ac5cb0142afbe102b914bb5c8483a6e8d2cb478133d516034128fa2`;
- exact AWG2 Core result SHA-256:
  `1928f39d91ee1dd1ff871b94c0cd88fd8e9cc92ca63eba065264d767a3d2515e`;
- exact AWG3.1 Core result SHA-256:
  `58bc1df0d61bd132b4a6085d33c20c335d636ed79256d3871bc29a31cf870084`;
- provider recovery check SHA-256:
  `09871d66b90dc841e5a12f397d64ac191833d10bbea91023faca8d89fa2508fa`.

External evidence remains outside Git and contains no credential, private key,
raw endpoint material or device identifier.

## Handoff

Current state is safe: both exact runners cleaned their Pi temporary state,
the alignment retry made no mutation, no lab selection changed and the
physical phone was not touched. Resume only after DE returns a real SSH banner
and ordinary service readback.
