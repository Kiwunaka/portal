# WO-013EK — candidate.21 Core AWG2/AWG3.1 RU-Pi interoperability

Status: `PASS_EXACT_CORE_FIXED_RU_PARTIAL_PACKAGED_CLIENT_MATRIX_OPEN`

Observed: `2026-09-02T04:36:25Z`–`2026-09-02T04:38:06Z`

Production/public mutation: `NONE`

## Outcome

Both owned AWG lab profiles pass from the owner's Raspberry Pi 4 over its
direct Russian fixed-network route using the exact Core revision bound into
signed candidate.21. This replaces the candidate.16 provider-outage result for
the same bounded Core/RU-Pi slice. It does not replace Android, Windows,
mobile-network or multi-ASN evidence.

## Exact boundary

| Item | Value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.21`, `1.2.0+4050` |
| Platform source | `e2608130e85d9a0f8fa4b920f46cf3d7679332c3` |
| Client source | `1e164586d741484b5ae8fb2ee267ef5dd813cadb` — not executed |
| Core source | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Signed manifest | `ce0b8586d4d9b5b625bbcd2c93b03fd783f89b4958a7fd79e58ef65b52c3dc6b` |
| Execution host | owned Raspberry Pi 4, Linux ARM64 |
| Origin | direct RU fixed-network path; physical location operator-attested |

The guarded runner is taken from the exact candidate.21 platform source. It
exports only the confirmed Core commit into a private local snapshot, verifies
the pinned module cache with network selection disabled, cross-builds the
existing interop test for Linux ARM64 and verifies the transferred binary
digest on the Pi.

Decrypted endpoint material travels only through the Brain session and SSH
stdin into the test process environment. It is not written to a remote file,
placed in an argument, printed or retained. The randomized exact
`/tmp/pokrov-awg-ru-pi-<uuid>` root is removed in `finally`; post-run readback
returns zero matching roots and zero matching executables. No server, runtime,
profile, client setting, release pointer or public state changes.

## Runtime result

| Profile | Result | Binary SHA-256 | Closed proof |
|---|---:|---|---|
| `awg2_lab` | `PASS` | `20e403f1acb00baaf157ff2332020c2e35c27d87b6a352480d9c6ec6f7a71527` | outer exchange, tunneled TCP, verified TLS and authenticated-egress marker |
| `awg31_lab` | `PASS` | `e55d79585af166d8cf7d6a3b0c0f6727aab34689e63946dddce67ced465188ec` | randomized-trailer outer exchange, tunneled TCP, verified TLS and authenticated-egress marker |

Both reports bind Core `cd8f0f4...`, pass the Pi 4/aarch64 and direct-default-
route preflight, return `runtime_mutated=false`, `server_mutated=false`,
`raw_material_returned=false` and
`temporary_remote_state_removed=true`. The selected material fingerprints are
unchanged from the earlier server-bound records, so this is a fresh transport
result rather than a silent profile replacement.

Raw secret-free result hashes:

- AWG2: `1690a9bb760ead7df6d10f8f7da376d9d68ea44e0135a6f24139cbd15ff2ef08`;
- AWG3.1: `6415cb90b23ceca62629b72a6ec86967b92c316b005b17960ae8d8dae769b35b`.

## Index and release decision

`FRKN_AWG/AWG-10` remains `I2` with stronger current-candidate status
`CANDIDATE21_EXACT_CORE_RU_FIXED_AWG2_AWG31_PASS_PACKAGED_CLIENT_MULTI_ASN_OPEN`.
The row explicitly requires distinct mobile/fixed networks and ASNs. One owned
fixed RU path plus source-level Core execution cannot satisfy that whole
acceptance criterion, and it does not prove the packaged Android or Windows
client path.

Phase 10 stays `I3`. Gate F stays `I3/NOT_RUN`; Gate G, tag, public release,
Store upload and stable promotion remain unauthorized. Next evidence is exact
candidate.21 Android and isolated-Windows AWG selection, followed by physical
Wi-Fi/Beeline and additional named RU-origin/ASN canaries.

## Verification

- exact Core worktree revision and cleanliness: `PASS`;
- AWG2 exact-Core RU-Pi runtime: `PASS`;
- AWG3.1 exact-Core RU-Pi runtime: `PASS`;
- post-run temporary-root and executable readback: `0/0`;
- owned AWG operation regression: `31 passed, 8 subtests passed`;
- release/documentation contracts: `56 passed`;
- platform context audit, JSON parse, ledger uniqueness/distribution and
  `git diff --check`: `PASS`.

## Evidence

- normalized record:
  `evidence/013EK-candidate21-core-ru-pi-awg/013EK-candidate21-core-ru-pi-awg.json`;
- normalized record SHA-256:
  `d0f7ba4148bde455a484c8d9ff19cf00c1e4b1683504c99b0b47c2cb35044789`;
- secret-free raw records:
  `E:/POKROV-tools/release-evidence/1.2.0-candidate21-awg-core-interop-2026-09-02/`.
