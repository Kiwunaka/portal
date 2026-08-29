# WO-013BN — candidate.6 isolated rollback rehearsal

## Outcome

Repeat the real portal projection and client stable-pointer mechanisms against
signed `pokrov-1.2.0-candidate.6` inside an isolated local fixture, without
touching production, tracked release state or the public channel.

The exact platform/client/Core tuple
`5713324c1c0c2566befadf527bc09ec0ecf84a4e` /
`b2497af7704d0aa6901541e175ce154b0eab05d7` /
`a45d69e40ed7d892619a2b5c4592a527f630665e` passed this sequence:

`1.1.6+20260819 -> pokrov-1.2.0-candidate.6 -> 1.1.6+20260819`.

The first invocation used the wrong input class: the public release-index
candidate JSON instead of the prepared strict-v2 handoff input. The harness
failed closed before any pointer or portal mutation and wrote no result. This
was operator input error, not a candidate metadata defect, and is not retained
as release PASS evidence.

The corrected invocation independently verifies the manifest/signature,
generates handoff SHA-256
`49d3db6d27c4e174d759808255146380111203f49dc1489572485726b37597ca`
and binds artifact-set SHA-256
`85dc98079544392d82eacec45d1be99608664584422982eab8105d39b514992b`.
Client validation, dry-run, forward atomic switch, reverse atomic switch and
final stable validation all pass. The final pointer returns byte-identically
to stable handoff
`563dd47835e017363eac63b33d66bdfeb9b41881168d4a14808f1daf48d3569f`.
The portal projection also returns byte-identically and preserves an unrelated
setting.

## Evidence ceiling

- `REL_DOD/DOD-18` remains `I3` with stronger exact candidate.6 local proof.
- `FE/P12-130` remains `I3` with stronger exact candidate.6 local proof.
- `REL_GATE/GATE-F` remains at the WO-013BM `3 PASS / 16 non-PASS / 0 FAIL`.
  Local rehearsal does not replace an authorized runtime pointer/kill drill,
  external backup/receipt, Brain readback or post-rollback health proof.
- Tracked client pointer/catalog, portal runtime, production, public release
  and stable pointer were unchanged.
- The temporary exact-source worktree was removed; the client, Core and
  platform release worktrees remained clean.

Focused regression: `5/5 PASS`. The full external rehearsal report SHA-256 is
`8c390d7e68f27bf5c82e9b585bdd34855d47e5eed9278ec225b7ba7882313d1f`.
Normalized evidence is
`evidence/013BN-candidate6-local-rollback/013BN-candidate6-local-rollback.json`;
its SHA-256 is
`a118b5a9b41baef63cbbbf62c1cac53508a3d09246625f14a7cdb8dc0c63ab71`.
It contains no address, hostname, credential, key, customer data, remote
payload or raw provider response.
