# WO-013DI — candidate.16 isolated portal/client rollback rehearsal

Status: `PASS_LOCAL_EXACT_CANDIDATE16_PORTAL_CLIENT_ROLLBACK`

Observed: `2026-08-31T18:31:37Z`

## Scope

Verify the signed candidate.16 manifest, receipt, signature and exact source
tuple, generate its post-sign operational handoff, and execute the real portal
projection plus client stable-pointer mechanisms inside one disposable local
fixture:

```text
1.1.6+20260819 -> pokrov-1.2.0 candidate.16 -> 1.1.6+20260819
```

No tracked client catalog/pointer, portal runtime, production service, public
release, stable pointer, physical phone or LDPlayer state is changed.

## Exact boundary

| Item | Value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.16`, `1.2.0+4049` |
| Platform source | `719e23dc49407beb9ae30d98d17d4b73d18ae37c` |
| Client source | `75ba7e721cfee486f7189edd51de97aba2746722` |
| Core source | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Signed release-index source | `54cfa03502ffafa5e4fb230a2cbdb0c0572c429f` |
| Signed manifest SHA-256 | `ae1906e68df755b1e0ce6a77d6ede8256f923e72fe11da57f1cae89a82c4ffe6` |
| Detached signature SHA-256 | `f5df63578d56db84a48eac1c68f1192e81462e8b407b1b6ff877c2b415507a9a` |
| Signing receipt SHA-256 | `1231ab6988746ca0e9725296826de2a9696a9a78600aa5e7f0b0c1b8c5782de4` |
| Candidate handoff SHA-256 | `a55c34742d2645f4176c25175813664f8ec7c205c8fd1d83423f325c727b3029` |
| Candidate artifact-set SHA-256 | `d9bba178d184958f9577ac39e3e736ef081677297cc67dc5bcffcb327edb4f69` |
| Retained stable handoff SHA-256 | `563dd47835e017363eac63b33d66bdfeb9b41881168d4a14808f1daf48d3569f` |

The harness materializes exact committed source snapshots from the four
repositories, verifies the detached Ed25519 signature against the
manifest-bound public keyring and confirms all six artifact bindings. Physical
install binding remains mandatory for PB-14/Gate F but is intentionally not a
prerequisite for this isolated pointer-only rehearsal.

## Portal result

The portal consumer applies the candidate.16 projection, observes the expected
Android and Windows artifact hashes, then restores its initial fixture bytes
exactly. The before and rollback SHA-256 values are both
`c4d3ea78d382d6ca6ab7d1d4d5367edc4478a9d96d91527ec2000df80e38ecd7`.
An unrelated setting survives the forward and rollback sequence.

## Client stable-pointer result

All five client stages pass:

- initial stable validation;
- dry-run with `applied=false`;
- forward switch to candidate.16 with a same-byte stable backup;
- reverse switch to `1.1.6+20260819` with a same-byte candidate backup;
- final stable validation.

The final pointer SHA-256 equals the initial stable handoff exactly. Forward
receipt SHA-256 is
`3b0cd90e7aeed7308a1730700ff28e70abae4c70f926169da23b2fd26172be87`;
rollback receipt SHA-256 is
`cbf929e65017f5da6a07c78128d6e2674cbc1a023f69ce3a8ed8be57ae4417d0`.

## Verification and evidence ceiling

The focused rollback/PB-14 suite passes `16/16`. Exact platform, client, Core
and release-index worktrees remain clean after capture. The disposable fixture
is removed by the harness.

`REL_DOD/DOD-18` and `FE/P12-130` remain `I3`, now with exact candidate.16
local evidence instead of candidate.13 history. This local proof does not
replace an owner-authorized runtime pointer/kill rollback, external backup and
receipt, current/Brain-origin readback, post-rollback health, physical install
binding or public stable-pointer proof. Gate F and Gate G do not advance.

The 378-row distribution remains `I4=5`, `I3=317`, `I2=22`, `I1=34`,
`I0=0`.

## Evidence

- normalized record:
  `evidence/013DI-candidate16-local-rollback/013DI-candidate16-local-rollback.json`;
- normalized record SHA-256:
  `9c8695cacb04da0158d017f2fa111fbf0368985932016c7748868d146ff73490`;
- external signed-binding SHA-256:
  `dfa6e9073c3dcc419a57695f4c3521da6e8323b2d4333cda42a2ba4fe7736d0c`;
- external generated handoff SHA-256:
  `a55c34742d2645f4176c25175813664f8ec7c205c8fd1d83423f325c727b3029`;
- external rollback report SHA-256:
  `1f44dc80a6951159e07f5d30c5f467f814bca359763ea12b7bb11e52704d26c3`.

The external outputs are retained under the private candidate.16 rollback
evidence directory. They contain no signing private key, credential, customer
data or device identifier.

## Next action

Keep the public/stable pointer unchanged. A real runtime pointer/kill rollback
still requires its own guarded backup, receipt and current/Brain readback; the
exact physical Android install and isolated connected Windows gates remain
separate.
