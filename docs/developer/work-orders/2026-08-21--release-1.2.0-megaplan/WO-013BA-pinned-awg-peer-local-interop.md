# WO-013BA — Pinned AWG peer local interoperability

## Outcome

Core commit `3c2b1147c1b42e39026231525c08558a50bc3d0f` adds a
deterministic loopback interoperability regression at the exact boundary that
remained uncertain after `WO-013AZ`. For both the bounded AWG2 and AWG 3.1
profiles, the POKROV transport using `bind_adapter` establishes an
authenticated handshake with a direct peer from the pinned official
`github.com/amnezia-vpn/amneziawg-go/v3 v3.1.20260814` module and exchanges an
inner TCP payload in both directions.

This proves the corrected POKROV bind adapter can interoperate with the pinned
official engine over real local UDP sockets. It does not prove that the owned
remote endpoint has matching parameters or state, that a mobile carrier passes
the packets unchanged, or that authenticated production egress works. The
failed candidate.5 physical result and the later LDPlayer replacement result
remain valid. No candidate, release row or production state changes here.

## Exact boundary

| Side | Implementation | Outer transport | Inner proof |
|---|---|---|---|
| Client | POKROV `Device` with `bind_adapter` and upstream netstack TUN | real OS IPv4 UDP loopback, dynamically allocated port | TCP dial, write and exact echo read |
| Peer | direct pinned `amneziawg-go/v3` `device.NewDevice`, `conn.NewStdNetBind` and upstream netstack TUN | real OS IPv4 UDP loopback, dynamically allocated port | netstack TCP listener, exact read and echo write |

Each subtest generates ephemeral Curve25519 key pairs in memory. Keys, IPC
configuration and packet contents beyond the fixed non-secret marker are not
logged or retained. The AWG 3.1 subtest additionally exercises header
protection, instruction-chain parsing, content padding, random trailers and
bounded randomized timing/header ranges. No production profile, server,
account or device material enters the test.

## Results

| Profile | Authenticated handshake path | Inner TCP exchange | Result |
|---|---|---|---|
| bounded AWG2 | POKROV bind adapter to direct pinned peer | exact bidirectional echo | `PASS` |
| bounded AWG 3.1 | POKROV bind adapter to direct pinned peer | exact bidirectional echo | `PASS` |

The package command
`go test ./transport/awg ./protocol/awg -count=1` passes. The repository
`scripts/test.ps1` gate under Go 1.25.13 also passes, including brand, ABI,
observability, AWG2, AWG 3.1, Hysteria2 and release-CI contracts.

## Release interpretation

- Keep Core commits `6b8ddca` and `3c2b114` in the replacement line.
- Do not create a replacement candidate from local interop evidence alone.
- Candidate.5 remains immutable and `REJECTED_FOR_REPLACEMENT`.
- This result rules out a general inability of the corrected POKROV bind path
  to handshake with the pinned engine. It does not rule out a mismatch in the
  exact owned endpoint parameters, server runtime state, protected profile
  delivery or carrier-path packet handling.
- The next discriminating test remains the production-signed replacement on
  the physical mobile origin with bounded unknown-type/MAC/response
  diagnostics. The physical phone was not online in ADB for this slice, so that
  check remains `MANUAL_OWNER_TEST`.
- Do not fork or alter cryptography. Continue using the pinned official module.

## Evidence

Machine-readable evidence is retained at
`evidence/013BA-awg-pinned-peer-interop/013BA-awg-pinned-peer-interop.json`,
SHA-256
`c9affbb68e2ca14bbdcaa9cd2c756870790252b360a365a5ffa4fd081344302d`.
Raw identifiers, credentials, keys, endpoints and packet captures are absent.
