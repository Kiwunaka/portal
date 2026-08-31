# WO-013DS — candidate.16 LDPlayer idle and direct API performance

Status: `PASS_BOUNDED_LDPLAYER_IDLE_AND_DIRECT_OS_API; DEVICE_GATES_OPEN`
Classification: `ACTIVE_EXECUTION_EVIDENCE`
Phase: `08/11`
Candidate: `pokrov-1.2.0-candidate.16`
Production/external mutation: `NONE`

## Outcome

Use only background Android SDK ADB commands while the owner retains PC
control. The installed LDPlayer APK hash matches the signed candidate.16
`x86_64` artifact. Package identity is exact `1.2.0` / version code `4049`.

The POKROV process is already present from prior state, but no runtime profile
is staged and no `tun0`, TUN address or TUN route exists. The slice does not
launch the application, start a VPN, inject input or touch the screen.

## Idle baseline

Twelve `/proc` samples over `56.35` seconds retain a stable PID:

| Metric | Result |
|---|---:|
| RSS min / p50 / p95 / max | `119.95 / 119.95 / 119.95 / 119.95 MiB` |
| Post-sample total PSS | `82.08 MiB` |
| Threads min / max | `40 / 40` |
| Process CPU over interval | `0.0%` |

This is a baseline, not a resource-budget PASS: the current performance
contract does not declare Android idle RSS, PSS or thread limits. It is also
not cold-start, connect, battery, thermal or endurance evidence.

## Direct emulator API path

One persistent HTTP/1.1 curl process per endpoint performs five warmups and
fifty measured requests over the direct LDPlayer operating-system path:

| Endpoint class | Result | Budget |
|---|---:|---:|
| Health | p95 `73.985 ms`, max `77.922 ms`, all HTTP `200` | `<= 100 ms`, PASS |
| Public catalog | p95 `97.756 ms`, max `120.793 ms`, all HTTP `200` | `<= 200 ms`, PASS |

An earlier process-per-request discovery run includes repeated process,
resolver and TLS setup and is deliberately excluded from gate evidence. The
retained measurements match the contract's persistent HTTP/1.1 shape, but
they remain an unauthenticated emulator OS path with no POKROV VPN. They do
not prove authenticated client egress.

## Physical-device boundary

The physical phone is not visible to the current Android SDK ADB session.
It is not waited on, accessed or given any result by this slice. Previous
exact physical install evidence remains authoritative; no physical runtime
result is inferred from LDPlayer.

## Evidence

- normalized record:
  `evidence/013DS-candidate16-ldplayer-idle-performance/013DS-candidate16-ldplayer-idle-performance.json`;
- normalized record SHA-256:
  `1d17625be9d3c5bf998e2ad7112d5b1954b7300b69e30935356f097ba06b827f`.

No raw device identifier, installed package path, endpoint response body or
local address is retained.

## Decision

`PERF-001`, `REL_DOD/DOD-13`, Gate E and Gate F gain stronger exact-candidate
LDPlayer evidence without index promotion. Cold-start/connect, physical
Android, connected Windows, comparable hardware, battery/thermal/endurance,
authenticated client egress and post-promotion measurements remain open.
Gate F stays `NO_GO 2/17/2`; Gate G, public assets, Store submission and stable
promotion remain unauthorized.
