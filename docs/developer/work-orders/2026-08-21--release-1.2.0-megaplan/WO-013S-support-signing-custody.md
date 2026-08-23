# WO-013S — Support-mode signing pin and hosted custody proof

Status: `SUPPORT_SIGNING_SOURCE_AND_HOSTED_CUSTODY_PROVED_WINDOWS_CERTIFICATE_BLOCKED`
Phase: `11`
Rows: `REL_DOD/DOD-15`, `OBS/OBS-072`
Candidate: `NOT_CREATED`
Production/publication: `NOT_AUTHORIZED_NOT_RUN`

## Outcome

The support-mode Ed25519 input required for the next 1.2.0 build is now bound
across the active client source and the hosted platform custody boundary:

- client `main` `288c82b52cf3bda32b6c11f5261805aa8842bdc1` tracks the
  public seed `pokrov-support-2026-08` and makes production Android/Windows
  builds reject a missing, partial or different pin;
- platform `master` `f64905125bc515ff97b61c7e94a4050f280c45da` runs a
  master-only, fail-closed custody verifier over the exact client `main` pin;
- hosted custody run `32672708398`, job `97275867661`, proves that the
  configured private Ed25519 seed derives that exact public pin, that the
  support-code secret meets the minimum entropy contract, and that a
  revision-bound sign/verify challenge succeeds.

Only the public receipt was retained. No private seed or support-code secret
was printed, downloaded, committed or written to the artifact. The workflow
does not run for pull requests, has read-only repository permissions, persists
no checkout credentials and exposes secrets only to the verification step.

This closes the support-signing **source/build input and hosted custody** gap.
It is not deployed-runtime proof: no production service was redeployed and no
support-mode issue/redeem flow was executed against a candidate or production.

## Client public-pin control

Client PR 12 head `e9d5607d353f55348d0829b2c54635c7bf84b234` passed the
complete `cross-repository-contract` job in run `32671146618`, job
`97272076355`, and merged under `OWNER_SOLO_EXCEPTION` as client `main`
`288c82b52cf3bda32b6c11f5261805aa8842bdc1`.

The tracked seed carries only public material. Production build entrypoints
always load it and reject missing/partial overrides or an override that differs
from the tracked key identity. Focused support-pin and Windows tests, the
cross-repository seed contract, docs contract and the complete local client
standard gate passed. Post-merge client run `32671854568`, job `97273782247`,
repeats the full hosted contract and standard Flutter/Android flavor gate
successfully in `13m10s`.

The five byte-hashed migration fixtures are explicitly LF-normalized so the
same tracked bytes and SHA-256 values are validated on Windows and hosted
Linux runners.

## Platform custody control

Platform PR 24 head `88ddc9826fee5d45c67d2e6d59945aae3cb56c34`
passed Release v2 Contract run `32672197198`, job `97274597357`, and
Guardrails run `32672197177`, job `97274597329`. It merged under
`OWNER_SOLO_EXCEPTION` as platform `master`
`f64905125bc515ff97b61c7e94a4050f280c45da`.

The custody verifier fails closed unless all of the following agree:

- strict client seed schema, key id and canonical public-key encoding;
- hosted public key/id configuration and the client `main` public pin;
- private Ed25519 seed and its derived public key;
- a minimum 32-byte UTF-8 support-code secret;
- a signed challenge bound to exact platform and client revisions.

The public receipt reports:

- key id `pokrov-support-2026-08`;
- public-key SHA-256
  `44aed43310eaf5442b3493cbe566b5f0f620a5660bb84a6bd028832114f48845`;
- client seed SHA-256
  `1513ff81117f75e507c867f942197c966b2957303ce7b654f3a59550a0ccecc2`;
- exact platform/client revisions
  `f64905125bc515ff97b61c7e94a4050f280c45da` and
  `288c82b52cf3bda32b6c11f5261805aa8842bdc1`;
- `status=PASS`, `candidate_created=false` and
  `production_runtime_mutated=false`.

Post-merge Release v2 Contract run `32672708448`, job `97275867688`, passes
in `1m52s`. Hosted custody run `32672708398`, job `97275867661`, passes in
`28s`. Post-merge Guardrails run `32672708409`, job `97275867664`, passes in
`11m15s`.

## Candidate boundary

The 013Q artifact set and 013R next-build tuple remain historical inputs. The
active client build source is now
`288c82b52cf3bda32b6c11f5261805aa8842bdc1`; its public support pin is ready
for a regenerated artifact set. Platform runtime source remains
`2ed944c5eaa667c44a7bc1970d2dd175ff34f8c9`, Core remains
`bdbd97fae35103e705f55908caebf75b4a9ff72f`, and public-index source remains
`7d5e402c47186fbe2ea1eb30ee1dc8cafdf066b2`.

No trusted Windows Code Signing certificate exists in the inspected Windows
certificate stores. `WINDOWS_TRUSTED_SIGNING` therefore remains
`BLOCKED_BY_ACCESS`. Without it, no exact promotable artifact set or signed
candidate index can be created honestly.

No candidate, GitHub Release, stable pointer, store publication, device/origin
proof, provider action, production deploy or support-mode runtime mutation was
performed.

## Ledger decision

No row advances. `REL_DOD/DOD-15` remains `I2`: the support public-pin input
is now source-bound and hosted-custody-proved, but trusted Windows signing,
rebuilt artifacts, candidate signature and manual/promotion proof remain
absent. `OBS/OBS-072` remains `I3`: hosted source-control custody strengthens
the local implementation evidence, while deployed RBAC/audit and exact-device
activation/replay proof remain `I4` gates.

Distribution remains `I3=309`, `I2=17`, `I1=37`, `I0=14`; 68 rows remain
below `I3`, with stage split `0/33/14/21`.
