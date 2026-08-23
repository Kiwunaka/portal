# WO-013J — Fail-closed public release-index contract

Status: `COMPLETE_LOCAL_IMPLEMENTATION_UNPUBLISHED_OWNER_KEY_BLOCKED`
Phase: `01`, `11`
Rows: `REL/REPO-001`, `FE/P12-023`
Publication: `NOT_AUTHORIZED`

## Outcome

Replace the ambiguous “release index unavailable” state with an exact audit of
the real public `Kiwunaka/pokrov` repository, implement its missing v2 source
contract on an isolated local branch, and make candidate preflight distinguish
legacy checksum-only content from a signed, published, same-byte-capable trust
surface.

## Public baseline audit

The public repository is accessible. `origin/main` is
`d0bf8e8c70ebeaa241f4c8f5b8a4452fd339ed15` and contains one README. All
visible release tags are lightweight references to that commit. GitHub reports
the commit signature as `unsigned`.

The current public 1.1.6 release is retained, not relabelled:

- release id `373029908`, tag `v1.1.6`, eight uploaded assets;
- GitHub asset digests match the downloaded `SHA256SUMS.txt` entries;
- `SHA256SUMS.txt` is 673 bytes at
  `b30c9cd93ea3b4e7c4f030cc7253fe60a8bbd767e4a045130e92e594b13e015b`;
- the Windows manifest is 2,799 bytes at
  `2e4383b901629aeb1998b7774e7e308a333a77c5233335a4200cf5677803886d`;
- there is no detached manifest signature, source-commit/SBOM/provenance
  binding or Windows publisher signature;
- the legacy Windows manifest contains absolute local build paths.

Therefore 1.1.6 is
`LEGACY_CHECKSUM_ONLY_NOT_CANDIDATE_ELIGIBLE`. Checksums prove downloaded-byte
identity, not signer authority or candidate provenance.

## Local release-index implementation

Local release-index branch `codex/1.2.0-release-index-v2` at
`f07654af496d042fa8dba3d8b2695e987c8e9eb7` adds:

- `release-index.contract.json`: target 1.2.0 pre-candidate state, exact
  candidate-manifest staging path, frozen schema hash, Ed25519 threshold-one
  detached-signature policy, GitHub digest parity and same-byte/no-rebuild
  promotion rules;
- `schemas/release-index-manifest-v2.schema.json`: exact product/build/channel,
  platform/client/Core/release-index revisions, contract hashes,
  compatibility, Android/Windows artifact identity, trusted signer lineage,
  SBOM/provenance, release notes, known issues and rollback/promotion fields;
- `trusted/release-signing-keys.json`: intentionally empty, with
  `BLOCKED_OWNER_KEY_PROVISIONING` state; no private key or invented public key
  is committed;
- a fail-closed validator using pinned `cryptography==50.0.0` and
  `jsonschema==4.26.0`; ready mode validates schema, unique asset ids/names,
  GitHub digest parity, exact release-index revision and a raw 64-byte Ed25519
  signature over the exact manifest bytes;
- source/negative signature tests and a read-only pinned-action GitHub workflow.

The contract SHA-256 is
`56d255e2116d20be1d2576a7c5a91b383f719eb8e95d6a50b566897c3195b95e`;
the manifest schema SHA-256 is
`9342fbe1d3124742dad85d598f6b4aaeab58e5d2057ca3edc7a895ada865fe5e`.

## Verification

- Repo-local source validator: `PASS`, status
  `BLOCKED_OWNER_SIGNING_KEY`, active signing keys `0`,
  `candidate_created=false`, `promotion_authorized=false`.
- Repo-local `--require-ready`: expected fail with “owner must provision an
  active trusted Ed25519 key”. This is a credited negative gate, not a PASS.
- Unit tests: `2/2 PASS`, including exact-byte signature acceptance and
  one-byte mutation rejection with an ephemeral test-only key.
- Ruff, format, Python compile, JSON parse and `git diff --check`: `PASS`.
- Platform preflight regression: `15/15 PASS` and independently rejects a
  missing/invalid contract, schema-byte drift, empty keyring, wrong remote and
  unpublished revision.

## Clean preflight

Against clean platform `d44bc9c40fe444b34c1d4d59c7158d667ee27db2`, client
`336d5454d47fa33d08b7a6bae79b7980cc6b11b4`, Core
`fcb3c8bbc6efdeed284417369aacb522722ebfa2` and local release-index
`f07654af496d042fa8dba3d8b2695e987c8e9eb7`, the read-only preflight is
`BLOCKED`, exact Core bytes remain verified and four blockers remain:

1. `release_index_revision_unpublished` — local HEAD is not public
   `origin/main`;
2. `release_index_signing_key_missing` — owner has not provisioned an active
   trusted Ed25519 public key;
3. `ledger_pre_freeze_incomplete` — three rows;
4. `ledger_external_pre_candidate_incomplete` — three rows.

The report is 45,911 bytes with SHA-256
`2c964ea96c64627468fade92e0d6216a1484222e26bccc5f53c636f280ac4f24`.

## Index decision

`FE/P12-023` advances `I1 -> I2`: the fail-closed manifest/checksum/signature
projection is implemented and locally verified in its own repository, but it
is neither published nor owner-key-ready. `REL/REPO-001` remains `I2`: source
and retained-history separation is implemented, while the exact signed public
revision is still absent.

Distribution becomes `I3=303`, `I2=20`, `I1=39`, `I0=15`; 74 of 377 rows
remain below `I3`. Stage counts remain `3/33/17/21` for
pre-freeze/candidate/external/deferred. `P12-023` remains an external
pre-candidate row below `I3`.

## Current external truth

- Hosted run list for `Kiwunaka/POKROV-app` is empty; the updated client has no
  Ubuntu run.
- Platform/client branch-protection readback returns GitHub `403`: the current
  private-repository plan does not expose that feature.
- Core `main` branch-protection readback returns `404 Branch not protected`.
- No release-index push/PR, owner key, candidate manifest/signature, release
  asset, tag, deployment, publication or promotion was created.

## Next action

Owner must provision and review the public half of the release Ed25519 key,
approve a review/push of `f07654a...` to the public repository, and retain the
hosted source-contract workflow plus public `origin/main` readback. Separately,
run the updated client gate in hosted Ubuntu, resolve/retain the private-plan
branch-protection limitation and run hosted review/required checks for exact
isolated PR-00 revision `dcfbbce...`. The local no-visible-UI proof exists, but
does not replace hosted PR evidence. Only then can preflight freeze the public
index revision for candidate input.
