# WO-013EM — Candidate.21 isolated portal/client rollback rehearsal

Status: `PASS_LOCAL_EXACT_CANDIDATE21_PORTAL_CLIENT_ROLLBACK`

Observed: `2026-09-02T05:12:07Z`

Production/public mutation: `NONE`

## Outcome

Validate the exact signed candidate.21 manifest, receipt, detached signature
and four-repository source tuple, generate its post-sign operational handoff,
and execute the real portal projection plus client stable-pointer mechanisms
inside one disposable local fixture:

```text
1.1.6+20260819 -> pokrov-1.2.0 candidate.21 -> 1.1.6+20260819
```

The forward switch and rollback both pass. Portal state and the retained stable
handoff restore byte-identically, receipts validate, unrelated fixture state
survives, and the disposable root is removed. No tracked pointer, runtime,
public asset, device, emulator or Windows VM is changed.

## Exact boundary

| Item | Value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.21`, `1.2.0+4050` |
| Platform source | `e2608130e85d9a0f8fa4b920f46cf3d7679332c3` |
| Client source | `1e164586d741484b5ae8fb2ee267ef5dd813cadb` |
| Core source | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Signed release-index source | `cae911e506d95eb72c1364b847992e30cbf9baf9` |
| Signed manifest SHA-256 | `ce0b8586d4d9b5b625bbcd2c93b03fd783f89b4958a7fd79e58ef65b52c3dc6b` |
| Detached signature SHA-256 | `ef474e6e1e147093b8b15c3cdc29bd35b5779249854a63ef7d6535d2588c7a58` |
| Signing receipt SHA-256 | `aaa027cc5d71fd567c6f3c0b8a9e3b0e965a67760fd02d1769eb3d54062926f8` |
| Candidate handoff SHA-256 | `e4893b871a0e64b09a61c1140c00a81aed3a1f515a9f24f44aaaed4ddb18a91b` |
| Candidate artifact-set SHA-256 | `165f053dc75fcccfe6e56f137ef20d99c097ba875f7f2ee5c747de055648409d` |
| Retained stable handoff SHA-256 | `563dd47835e017363eac63b33d66bdfeb9b41881168d4a14808f1daf48d3569f` |

The harness materializes exact committed snapshots from all four repositories,
verifies the Ed25519 signature against the manifest-bound public keyring and
confirms all six artifact bindings. Hosted signer run `33586752995` and its
retained artifact metadata are bound without accessing the signing private key.

## Results

The portal consumer applies the candidate.21 projection, observes Android
artifact SHA-256 `d5dd9905bafdc30809a1199dde5961129680a03513b60a6e46f323a6a583693c`
and Windows artifact SHA-256
`87f90be11a927c271c84e8042f17e052ee1070a1ac4923fa3949d6e19c00dff3`,
then restores the initial fixture bytes exactly. Its before and rollback
SHA-256 values are both
`c4d3ea78d382d6ca6ab7d1d4d5367edc4478a9d96d91527ec2000df80e38ecd7`.
An unrelated setting survives both transitions.

The client channel passes initial validation, no-apply dry-run, forward switch
to candidate.21, reverse switch to `1.1.6+20260819` and final stable validation.
Stable bytes restore exactly. Forward receipt SHA-256 is
`98fd2fe791f81d01f780a426d861e77e2e3945e2e4eba33b121402e2b89a346e`;
rollback receipt SHA-256 is
`17186a04b6fbc6a2b2e081b36d0fe66c257a959e971163513d1eb47209c0c563`.

## Verification and evidence ceiling

The focused rollback/PB-14 suite passes `16/16`. Exact platform, client, Core
and release-index worktrees remain clean, and the disposable fixture is
removed.

`REL_DOD/DOD-18` and `FE/P12-130` remain `I3`, now with exact candidate.21
local evidence. This is not a production, public or origin proof. A real
runtime pointer/kill rollback still requires a guarded backup and receipt,
current/Brain-origin readback and post-rollback health. Gate F remains
`NOT_RUN` for candidate.21 and Gate G remains unauthorized.

The 378-row distribution remains `I4=7`, `I3=320`, `I2=19`, `I1=32`,
`I0=0`.

## Evidence

- normalized record:
  `evidence/013EM-candidate21-local-rollback/013EM-candidate21-local-rollback.json`;
- normalized record SHA-256:
  `7b4ed43186d7d80a710011f058f21cf81f400a887417893dc2a0eda920b52be3`;
- external signed-binding SHA-256:
  `e124680698ae71413a2479d6a2b4d227b234102aad15af3685d88475c042455a`;
- external generated handoff SHA-256:
  `e4893b871a0e64b09a61c1140c00a81aed3a1f515a9f24f44aaaed4ddb18a91b`;
- external rollback report SHA-256:
  `ff1228cf37a0fab2c08b05c65adc6b3fba66799a30d1dffad741783943ca3a6d`.

The external outputs remain under the private candidate.21 rollback evidence
directory. They contain no signing private key, credential, customer data or
device identifier.

## Next action

Keep public and stable pointers unchanged. Complete candidate.21 physical
Android, fresh Windows service-restart, packaged AWG/Smart-DNS, named-origin
and aggregate gates. Execute a real runtime pointer/kill rollback only under
its separate production guard.
