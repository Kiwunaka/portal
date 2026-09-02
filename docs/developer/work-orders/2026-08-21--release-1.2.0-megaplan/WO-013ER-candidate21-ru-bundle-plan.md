# WO-013ER — candidate.21 RU-origin bundle and owned-Pi install plan

Status: `CANDIDATE21_RU_BUNDLE_AND_REMOTE_PLAN_PASS_APPLY_NOT_RUN`

Observed: `2026-09-02`

Runtime mutation: `NONE`

## Outcome

The canonical RU-origin environment preflight on the owned direct-RU fixed
Raspberry Pi 4 remains
`MANUAL_OWNER_TEST_ENVIRONMENT_INCOMPLETE`. The host has the expected user,
group, tools, private spool and all ten install targets, but only `6/10`
candidate source/unit files match and all four runtime-material inputs are
absent. This is an environment gap, not a candidate.21 protocol failure.

The fail-closed bundle builder on the active platform line previously knew
signed candidates only through candidate.16 and correctly rejected exact
candidate.21 platform source `e2608130e85d9a0f8fa4b920f46cf3d7679332c3`
as not allowlisted. The builder now adds only that signed source revision as
`pokrov-1.2.0-candidate.21`; arbitrary revisions remain rejected. Its focused
suite passes `11/11`.

Two independent builds from the clean exact candidate.21 platform worktree
produce byte-identical 10-member bundles of `47928` bytes with SHA-256
`56218e199fff95bdf7ce2b5b29f019a24863c21f7aef99a5e54c122b5412279e`.
Verify and local install PLAN pass. The guarded remote PLAN on the owned Pi
also passes with `mutation_performed=false`, all ten targets present, the
private spool empty, and no raw host, path or runtime material returned.

No bundle was installed. Runtime material was not supplied. Runner, uploader,
ingest, archive, heartbeat and admin readback were not executed. Therefore the
general RU-origin verdict remains `MANUAL_OWNER_TEST`, not `PASS`.

## Release effect

No completion-index level changes. Distribution remains `I4=7`, `I3=320`,
`I2=19`, `I1=32`, `I0=0` across `378` unique rows. Gate F remains `NOT_RUN`;
Gate G remains unauthorized. Candidate.21 bytes, public assets, stable
pointers, devices and production runtime are unchanged.

## Next exact action

Prepare the exact private receipt-bound set `probe.env`, `uploader.env`,
`hmac.key` and `profiles.json`, then run the separately confirmed guarded
install APPLY with spool preservation. After install readback, execute the
manual runner/uploader sequence and verify ingest, archive, fresh heartbeat
and all three admin read endpoints before any RU-origin `PASS` or Gate F
regeneration.

## Evidence

- normalized record:
  `evidence/013ER-candidate21-ru-bundle-plan/013ER-candidate21-ru-bundle-plan.json`;
  SHA-256
  `38efbc6bfa0d4c5094ba16c42530cb6d61fa4dec5dd7ca7aaa401bb8e7204836`;
- private deterministic bundle SHA-256:
  `56218e199fff95bdf7ce2b5b29f019a24863c21f7aef99a5e54c122b5412279e`;
- preflight report SHA-256:
  `6118d3b8896a04da5674c1456a2d29b1ea40aa185599767dec088e5a01b11da3`.

The tracked record contains only candidate identities, hashes, counts and safe
state labels. It contains no credential, HMAC material, raw host, raw path,
profile, customer data or provider payload.
