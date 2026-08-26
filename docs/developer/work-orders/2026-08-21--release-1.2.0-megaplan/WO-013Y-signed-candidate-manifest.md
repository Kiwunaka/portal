# WO-013Y — Signed candidate manifest artifact

Status: `SIGNED_CANDIDATE_MANIFEST_ARTIFACT_PROVED`
Phase: `11`
Rows: `OBS_DOD/DOD-29`, `REL/REL-001`, `REL_DOD/DOD-15`, `REL/REPO-001`, `FE/P12-022`, `FE/P12-023`
Candidate manifest: `CREATED_SIGNED_ACTIONS_ARTIFACT_ONLY`
Public candidate release: `NOT_CREATED`
Promotion: `NOT_AUTHORIZED_NOT_RUN`
Recorded: `2026-08-26`

## Goal

Merge the reviewed unsigned-Windows direct-beta source contract, run the
main-only secret-backed signer over the exact tracked six-artifact template,
download and independently revalidate its output, and retain non-expiring
copies without manufacturing public asset, runtime, stable or Store proof.

## Source-contract promotion

Public release-index PR 4 retained the exact narrow owner exception and passed
`source-contract` on head
`84d320b12dc503e944b6c31d4febde4026c1b8d1` in run `32990609397`, job
`98247041758`. It merged through the already authorized sole-owner lane as
public `main` merge commit
`c1d617093692b05d2a12ae8ad8394e5570b0df8a`. A main-only manual replay,
run `32991517919`, job `98249932066`, checked out that exact commit and passed
source validation and all release-index tests.

The exception remains limited to one artifact id/name/platform/kind/arch tuple:
`windows-x64-setup` / `pokrov-windows-setup-x64.exe` / Windows EXE x86_64.
It requires `SKIPPED_BY_OWNER`, exception code
`OWNER_ACCEPTED_UNSIGNED_WINDOWS_BETA_1_2_0`, direct-download-only distribution
and the SmartScreen/unknown-publisher warning. Android signing remains trusted;
stable, Store and broad signed-Windows claims still fail closed.

## Exact signing dispatch

The main-only `Prepare signed candidate manifest` workflow was dispatched with:

- template path
  `candidate-inputs/1.2.0/pokrov-1.2.0-candidate.1.json`;
- exact tracked template size `8240` and SHA-256
  `ced24a1c48b354af87974a8fa2a73446016260a71753cdc053e4aa8319dc972e`;
- candidate id `pokrov-1.2.0-candidate.1`;
- release-index source `c1d617093692b05d2a12ae8ad8394e5570b0df8a`.

Run `32991625280`, job `98250288850`, completed `SUCCESS`. It checked out exact
main, loaded the Ed25519 private key only from the owner-controlled Actions
secret, replaced the reviewed zero-commit placeholder, emitted canonical JSON,
signed it, revalidated the result without private material and uploaded only a
14-day Actions artifact. The private key was not read, printed, downloaded or
copied into evidence.

## Signed output readback

Artifact `9614812168`, named
`pokrov-pokrov-1.2.0-candidate.1-signed-manifest-c1d617093692b05d2a12ae8ad8394e5570b0df8a`,
was downloaded and independently checked against public release-index main:

| Output | Size | SHA-256 |
|---|---:|---|
| `release-index.json` | 6879 | `84695f6e318814bc2d1e9de1c9adc3aa4277015d551c5462b197664e574c28d6` |
| `release-index.json.sig` | 64 | `718cc5b8033d1f48d3dcb236561db0c5218b05d9581f472f232dc4f44e3adb56` |
| `signing-receipt.json` | 588 | `ca6abc0d0f91e1c93ee64ac47cd75e89f8dd7ae04fd438f5ce1642be98eaef28` |

The independent validator returned `READY_SIGNED_MANIFEST`, key id
`pokrov-release-2026-01`, six artifacts and exactly one owner-approved unsigned
Windows exception. Receipt, manifest and recomputed file hashes agree on the
candidate id, release-index commit, manifest digest, signature digest and
`promotion_authorized=false`.

The manifest binds platform/client/Core source
`8bed966e64e23527da982f3fcfb1b9e48ce6f408` /
`a74d2aea5aed62f5c31d3a0bbc258e408cebe3bd` /
`344b317a7a09eca7943a93866b193553538bd8f6` and the exact six hashes already
recorded by 013V. Direct Git-object hashing at the bound platform revision also
reproduced:

- error catalog
  `7d3bf242777d5bf76bbebcf162e5969d3f83d7f68b2787051e1c4fddeadc3dc7`;
- observability event schema
  `24ae72442f778d7f1334ae0a4bf4d774738e4de275707b29420ec733af65cc17`;
- product facts
  `3df7e7a03bf6a7e62e49e2791641428fb415cdca692a67b4a48fee79a853289e`.

The three exact signed outputs are copied under
`evidence/013Y-signed-candidate-manifest/` so the proof survives the Actions
artifact expiry. The detached signature remains public verification material,
not a private secret.

## Evidence ceiling

This creates and proves a signed candidate manifest as an artifact only. It
does not create the GitHub Release named by the manifest URLs, upload any of
the six public assets, produce GitHub asset-digest readback, mutate a stable
pointer, deploy backend/client code, submit to a Store or prove device/origin,
payment, Operator, legal, rollback or post-promotion health. The signed
manifest cannot make those absent transactions pass.

## Ledger decision

`OBS_DOD/DOD-29` advances `I3 -> I4`: its exact oracle is that the error-catalog
and observability-schema hashes are bound by a trusted signed candidate
manifest. The exact Git objects, canonical manifest, detached Ed25519
signature, public key verification and hosted receipt now prove that oracle.

No other row advances. `REL/REL-001` is refreshed but remains `I3` because its
device/origin/rollback and stable-promotion proof is absent. `REL_DOD/DOD-15`
remains `I2` because the ten required
direct-beta device/origin/provider/owner/rollback gates and same-byte public
promotion proof remain open. `REL/REPO-001`, `FE/P12-022` and `FE/P12-023`
remain `I3` because public asset/runtime/static-surface readback is absent.

Current distribution is `I4=1`, `I3=308`, `I2=17`, `I1=37`, `I0=14`; the
count at or above `I3` remains 309. Sixty-eight rows remain below `I3`, and the
stage split remains `0/33/14/21` across pre-freeze, candidate, external and
deferred stages.

## Next action

Retain physical Beeline and Windows clean-host evidence against the same bytes,
then close the remaining aggregate origin/provider/Operator/legal/rollback
gates. Public candidate asset upload and same-byte digest readback require a
separate publication authorization; stable promotion remains prohibited.
