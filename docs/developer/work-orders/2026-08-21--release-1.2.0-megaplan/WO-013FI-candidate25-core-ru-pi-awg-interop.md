# WO-013FI — candidate.25 Core AWG2/AWG3.1 RU-Pi interoperability

Status: `PASS_EXACT_CORE_FIXED_RU_PARTIAL_PACKAGED_CLIENT_MATRIX_OPEN`

Observed: `2026-09-03T03:47:19Z`–`2026-09-03T03:48:52Z`

Production/public mutation: `NONE`

## Outcome

Both owned AWG lab profiles pass from the owner's Raspberry Pi 4 over its
direct Russian fixed-network route using the exact Core revision bound into
signed private candidate.25. AWG3.1 was run first, followed by AWG2. This is a
fresh candidate.25 source-level Core result; it does not replace packaged
Android, packaged Windows, mobile-network or multi-ASN evidence.

## Exact boundary

| Item | Value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.25`, `1.2.0+4053` |
| Platform source | `883cd1038a087fbf9f570cffcbfdfd5f5197ffd4` |
| Client source | `54259b0f84e16c58e2d1f5f04b369af4fd0834b2` — not executed |
| Core source | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Release-index source | `18d9cb4c5541481c5e60713376904f962ec19a7c` |
| Signed manifest | `7161bae715d590fac0623561d147e4d9ee069da14a5e3645001cc4c39aa329b6` |
| Execution host | owned Raspberry Pi 4, Linux ARM64 |
| Origin | direct RU fixed-network path; physical location operator-attested |

The guarded runner is byte-identical to the file in candidate.25 platform
source (Git blob `5d31b5638f4acfec3aa77489b377d79593269625`). It exports only the
confirmed Core commit into a private temporary snapshot, cross-builds the
existing interoperability test for Linux ARM64 and verifies the transferred
binary digest on the Pi.

Decrypted endpoint material travels only through the Brain session and SSH
stdin into the test-process environment. It is not written to a remote file,
placed in an argument, printed or retained. The randomized exact
`/tmp/pokrov-awg-ru-pi-<uuid>` root is removed in `finally`; the local
operation temp root is empty after each run. No server, runtime, profile,
client setting, release pointer or public state changed.

## Runtime result

| Profile | Result | Binary SHA-256 | Closed proof |
|---|---:|---|---|
| `awg31_lab` | `PASS` | `0c8874b46588f0f2f52eab873c1fc65cfbb048f38eac4111d8b2aff48df98c6f` | randomized-trailer outer exchange, tunneled TCP, verified TLS and authenticated-egress marker |
| `awg2_lab` | `PASS` | `04758bbbd85402d8a351e855b7120ba0fe909c8508af106531e1aa9d42635b8b` | outer exchange, tunneled TCP, verified TLS and authenticated-egress marker |

Both reports bind Core `cd8f0f4...`, pass the Pi 4/aarch64 and direct-default-
route preflight, return `runtime_mutated=false`, `server_mutated=false`,
`raw_material_returned=false` and
`temporary_remote_state_removed=true`.

Raw secret-free result hashes:

- AWG3.1: `ae83dca5d5f3ac88782034ce88497753d053f231eb2246be74c2a8ea521c15d6`;
- AWG2: `6d64dddb3be782b956984092701141cc0967bf42a3e353abde07d307c20d9d4b`.

## Index and release decision

`FRKN_AWG/AWG-10` remains `I2` with fresher status
`CANDIDATE25_EXACT_CORE_RU_FIXED_AWG31_AWG2_PASS_PACKAGED_CLIENT_MULTI_ASN_OPEN`.
The row requires distinct mobile/fixed networks and ASNs. One owned fixed RU
path plus source-level Core execution cannot satisfy that acceptance
criterion, and it does not prove the packaged Android or Windows client path.

Phase 10 stays `I3`. Candidate.25 Gate F stays
`BLOCKED 5 PASS / 14 non-PASS / 0 FAIL`; this supplemental record is not a
Gate F regeneration. Gate G, tag, public release, Store upload and stable
promotion remain unauthorized.

## Verification

- exact Core worktree revision and cleanliness: `PASS`;
- guarded-runner identity against candidate.25 platform source: `PASS`;
- AWG3.1 exact-Core RU-Pi runtime: `PASS`;
- AWG2 exact-Core RU-Pi runtime: `PASS`;
- local and remote temporary state removal: `PASS`;
- owned AWG operation regression: `31/31 PASS`;
- production, server, runtime and public mutation: `NONE`.

## Evidence

- normalized record:
  `evidence/013FI-candidate25-core-ru-pi-awg/013FI-candidate25-core-ru-pi-awg.json`;
- normalized record SHA-256:
  `75d9f3cd4c9622867809b71b64288f7bd1e11ea62284f7674b88f6013ad946df`;
- secret-free raw records:
  `E:/POKROV-tools/release-evidence/1.2.0-candidate25-awg-core-interop-2026-09-03/`.
