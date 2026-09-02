# WO-013ES — candidate.21 existing RU-auth contract preflight

Status: `EXISTING_BRAIN_RU_AUTH_CONTRACT_PLAN_PASS_SECRET_TRANSFER_NOT_RUN`

Observed: `2026-09-02`

Runtime mutation: `NONE`

## Outcome

WO-013ER proved the exact candidate.21 RU bundle and a no-mutation install PLAN
on the owned direct-RU Raspberry Pi 4, but the Pi has no runtime material. A
fresh Brain-side PLAN now proves that the existing RU-origin authentication
registry and managed systemd drop-in are already present, active and exactly
compatible with the required contract.

The preflight was tightened before relying on that state. It now validates,
without returning the credential, that the registry contains exactly one
enabled key with key id `ru-mini-v1`, subject `mini`, origin `ru`, scopes
`ru_probe:manifest`, `ru_probe:ingest` and `ru_probe:heartbeat`, a bounded
visible-ASCII secret, and no extra metadata. It separately compares the
managed systemd drop-in byte-for-byte and verifies that the active
`portal-api` process uses the expected registry path. The focused suite passes
`10/10`.

The live read-only PLAN returns every host and contract flag true. It returns
no secret, secret hash or raw host and performs no mutation. Current evidence
therefore does not require key rotation or a `portal-api` restart. It does not
authorize or perform retrieval of the existing credential, Pi installation,
runner/uploader execution, ingest, archive, heartbeat or admin readback.

## Release effect

No completion-index level changes. Distribution remains `I4=7`, `I3=320`,
`I2=19`, `I1=32`, `I0=0` across `378` unique rows. General RU-origin remains
`MANUAL_OWNER_TEST`; Gate F remains `NOT_RUN` and Gate G remains unauthorized.
Candidate bytes, Brain/Pi runtime, public assets and stable pointers are
unchanged.

## Next exact action

Use a separately authorized guarded transfer of the existing Brain credential
into a private four-file Pi runtime-material directory, without stdout,
tracked artifacts or retained hashes. Validate that directory locally, then
run the confirmed candidate.21 Pi APPLY with spool preservation. Only the
subsequent runner/uploader, ingest, archive, fresh heartbeat and three admin
readbacks can produce general RU-origin evidence.

## Evidence

- normalized record:
  `evidence/013ES-candidate21-ru-auth-contract-plan/013ES-candidate21-ru-auth-contract-plan.json`;
  SHA-256
  `4b43e73095450785d9ce93791f5de7562713377b2ae5c0f7460fe804d49e4f7d`;
- exact candidate.21 RU bundle:
  `56218e199fff95bdf7ce2b5b29f019a24863c21f7aef99a5e54c122b5412279e`;
- private safe PLAN report SHA-256:
  `3b9b656ffa894eb7ebb101599c6bb4d4d3c7ec0aed26618e9b62bc7473aec3d6`;
- focused preflight tests: `10/10` PASS.

The tracked record contains only public candidate identities, expected key
metadata, booleans and safe state labels. It contains no credential value,
credential hash, private host, raw path, profile, customer data or provider
payload.
