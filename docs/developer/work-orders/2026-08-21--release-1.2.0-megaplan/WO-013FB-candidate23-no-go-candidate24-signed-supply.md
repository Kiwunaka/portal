# WO-013FB — candidate.23 pipe-contention NO_GO and candidate.24 signed supply

Status: `CANDIDATE23_IMMUTABLE_NO_GO_CANDIDATE24_PRIVATE_SIGNED`

Observed: `2026-09-03`

Production/public mutation: `NONE`

## Outcome

Reject exact candidate.23 after reproducing its Windows service-client startup
contention in the isolated Windows 11 VM, then bind the corrected merged source
to immutable private candidate.24 without using the host mouse or publishing
release assets.

Candidate.23 is an immutable `NO_GO`. With its exact installed service still
`Running`, 32 simultaneous status clients produced `9` accepted and `23`
rejected requests. The probe was local to the guest named pipe, used no network
or UI control and retained no payload data. A running service that rejects most
concurrent startup clients is a release-blocking availability defect.

Candidate.24 contains the bounded named-pipe connection retry correction and
the 32-client regression. Exact client source is
`54259b0f84e16c58e2d1f5f04b369af4fd0834b2`; hosted client checks pass. Six
build-4053 artifacts bind to strict-v2 handoff, SBOM, provenance and the trusted
release-index manifest/signature/receipt. Offline supply validation passes all
six artifacts and all `11/11` required Windows runtime files.

## Exact candidate.24 identity

| Component | Revision or digest |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.24`, `1.2.0+4053` |
| Platform source | `06b932b48ffcb92c8ec024b8892aaa9c36359673` |
| Client source | `54259b0f84e16c58e2d1f5f04b369af4fd0834b2` |
| Core source | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Signed release-index source | `a2fb1067adc4f2881299b45929a0d46736f74fff` |
| Manifest SHA-256 | `bdd51f2c428298e3178fd94d9befaf79aa442445a384f52882995ffd5d9ddeed` |
| Signature SHA-256 | `ef47e339cafe23bd994844e70fe8263902a0d62f03312a35b10536913e7ac0bc` |
| Receipt SHA-256 | `1ff20e15adda261dff182c1166a276270a05721f3770f5cc4df1d77b61153343` |
| SBOM SHA-256 | `3fbfb3e5e1d33b942cac82714955d27ff46fcad1608d0bfaa694dd6c91893f3d` |
| Provenance SHA-256 | `7b89514a782f092e406e7d5c2fab166bbbe62997101fcde12f75ae3f0326adf4` |
| Release handoff SHA-256 | `87c688ffdd2f71363aa8cf4ca7bf99147d6109cc21d9d5887bc4f025f2fd2b63` |

Release-index input PR 49, receipt PR 50 and signer run `33698144521` pass.
The retained Actions artifact digest is
`sha256:09d407e22916f347c4e466ef098966c8f21a5aeb1cadd5c30e9741938f5e6656`.
Local detached-signature verification against the public keyring returns
`READY_SIGNED_MANIFEST`.

## Windows and static boundary

The exact candidate.24 installer is
`ffc9b07c59f75372b48c5c1e94551d6d9af710ac0287cd1352142b0964707fb3`,
`29139238` bytes. Its headless copy inside the isolated guest matches both
values. Debug native CTest passes `8/8`, including the pipe-client test.
Bounded artifact and Windows staging scans report zero definite findings.

Exact candidate.24 installation is `NOT_RUN`: the available guestcontrol token
is non-elevated, and invoking interactive UAC would violate the no-screen-input
boundary. No predecessor runtime result is relabelled as candidate.24 PASS.

## Evidence and next boundary

`013FB-candidate23-no-go-candidate24-supply.json` SHA-256 is
`fad5ec282f8264e7ea8dee362dec9da6b49b08d9168e4eee00bced9c22a09885`.

No completion-index row advances. Candidate.24 signed supply replaces the
active candidate identity, while exact Windows installation/runtime, Android,
AWG/Smart DNS, named origins, rollback, provider, Operator, legal/commercial,
performance and final attestations remain separate gates. `promotion_authorized`
is false; no tag, GitHub Release, public asset, Store upload or stable pointer
was created.
