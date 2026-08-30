# WO-013CT — candidate.10 Core AWG2/AWG3.1 RU-Pi interoperability

## Outcome

Execute both owned AWG transports from an owned Raspberry Pi 4 on its direct
Russian fixed-network path, using the exact Core source bound into signed
candidate.10. Keep this source-level RU-origin proof separate from the Android,
Windows and general release-origin matrices.

## Exact boundary

| Item | Value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.10` — unchanged |
| Candidate Core source | `a45d69e40ed7d892619a2b5c4592a527f630665e` |
| Candidate client source | `3459438f02bd774e722b1b858e7f7f16d57a9f5c` — not executed by this slice |
| Guarded operation source | `8dfaeab61f26f66f61bec485336093e737cd22cb` |
| Execution host class | owned Raspberry Pi 4, Linux ARM64 |
| Origin | RU fixed-network path; physical location owner-attested, direct-default-route preflight passed |
| Observed at | `2026-08-30T08:02:54Z` |

No candidate byte, endpoint material, server configuration, control-plane row,
runtime, tag, release or stable pointer changes. The physical Android phone is
unavailable and untouched.

## Guarded execution contract

`scripts/remote_run_owned_awg_core_interop.py` now supports a confirmed owned
Pi execution path in addition to its existing current-origin mode. The remote
path:

- requires a clean exact Core revision and cross-builds only the existing
  operator interop test as `linux/arm64` with `CGO_ENABLED=0`;
- requires strict SSH host-key verification and an exact caller-confirmed
  alias;
- accepts only Raspberry Pi 4/aarch64 and rejects a default route through
  `tun`, `wg`, `awg`, WARP or Tailscale;
- transfers a digest-verified test binary to one random exact
  `/tmp/pokrov-awg-ru-pi-<uuid>` directory;
- carries decrypted endpoint material only over SSH stdin into the test
  process environment, never into a file, command argument, stdout or retained
  artifact;
- removes and verifies absence of its exact temporary directory in `finally`;
- returns only closed outcome fields and Core, binary and material
  fingerprints.

Focused operation, manifest, live-probe and documentation/context tests pass
`33 + 8 subtests` and `32`; the platform context audit and diff check pass.

## Runtime result

One exact ARM64 test binary, SHA-256
`c17386c0d11f7505dfce0b9bf51b969f3168ba4621ecc61a6478db024b4027e4`,
executes both profiles:

| Profile | Result | What passed |
|---|---|---|
| `awg2_lab` | `PASS` | outer AWG exchange, tunneled TCP, verified TLS and exact authenticated-egress `204` marker |
| `awg31_lab` | `PASS` | randomized-trailer AWG3.1 outer exchange, tunneled TCP, verified TLS and the same authenticated-egress marker |

Both reports bind Core `a45d69e...`, direct-default-route preflight,
`runtime_mutated=false`, `server_mutated=false`,
`raw_material_returned=false` and `temporary_remote_state_removed=true`.
Post-run readback returns zero matching temporary roots and zero test
processes.

## Index and release decision

`FRKN_AWG/AWG-10` advances `I1 -> I2` as
`PARTIAL_RU_FIXED_CORE_INTEROP`: a real RU fixed-network Core path now passes
both AWG families, but the row still lacks mobile/fixed multi-ASN and regional
coverage plus exact candidate Android/Windows execution. `FRKN_PLAN/W9-02`
remains `I1`: its general candidate.10 RU manifest is still `FAIL 9/11` on the
separate NL and RU-SPB reachability targets. This AWG-specific PASS cannot
overwrite those failures.

Gate C stays `BLOCKED/I3`; Gate F stays `NO_GO 6 PASS / 13 non-PASS / 1 FAIL`.
The physical candidate.10 Android run, connected clean-VM Windows parity,
external leak/UDP53/MTU/OEM/endurance and broader RU-origin matrices remain
open. No Gate G or promotion is authorized.

The independent Smart-DNS recheck still returns `NXDOMAIN` from all four
delegated Timeweb servers (`0/4`), so ACME/runtime/server/frontend APPLY remains
`NOT_RUN`.

Normalized evidence is retained in
`evidence/013CT-candidate10-core-ru-pi-awg/013CT-candidate10-core-ru-pi-awg.json`.
