# WO-006K — Signed temporary support mode and encrypted manual export

Status: `COMPLETE_LOCAL_I3`
Phase: `04` (source ledger rows `P08`)
Rows advanced: `OBS/OBS-070`, `OBS-071`, `OBS-072`, `OBS-073`, `OBS-074`
Promotion: `NOT_REQUESTED`

## Outcome

Close the five remaining local support-mode rows without creating a remote
command channel, a plaintext diagnostic export or another ticket/bundle
authority. The normal diagnostic path must remain useful without upload, while
temporary extended collection must require a case-bound, one-time, signed and
strictly bounded user-approved policy.

## Implemented contract

- The platform owns one additive `SupportModePolicy` row and one L2
  `support.mode.issue` Action Intent. Issuance is bound to an existing ticket,
  owner, environment and exact platform/app/build. The database stores only the
  activation-code SHA-256; safe idempotent action replay can regenerate the
  code only while the policy is issued and unexpired.
- `POST /api/client/support/mode/redeem` is normal-session-only, owner-bound and
  one-time. Audience mismatch does not consume the code. Successful redemption
  returns an Ed25519-signed closed v2 policy with nonce, <=30-minute expiry,
  exact category/collector pairs, <=2 MiB per-bundle, <=4 MiB cumulative and at
  most two bundles.
- The client independently verifies signature, schema, audience, issuance,
  expiry and nonce before showing the categories/TTL/caps. Activation requires
  a second explicit user confirmation. The persisted controller remembers
  nonces and usage, re-verifies on restore, fails closed on corruption, rejects
  replay/cap/expiry and automatically disables at expiry.
- A root-level live-region banner shows expiry and bundle usage for the whole
  active session and always exposes diagnostics and manual disable. The policy
  cannot hide or extend it.
- `PSD1-*` is a separate versioned 24-character, 14-day support code with CRC8.
  It contains only platform, route/connection class, app/build, issue date and
  a 16-bit diagnostic hash prefix. Client and platform share fixture
  `PSD1-6C4Q-J082-00FA-QK8B`; `support.read` decodes it without file upload or
  identity.
- Manual export resolves the same verified signed X25519 recipient as upload,
  encrypts first, then passes only the encrypted envelope to a host destination.
  Windows uses the system save dialog. Android uses one bounded
  `ACTION_CREATE_DOCUMENT` channel that validates exact name, size, algorithm,
  schema and diagnostic ID before writing bytes, and zeroes the buffer after
  completion. Cancellation creates no success claim.
- No policy field or client path can execute commands, mutate VPN/routes/DNS,
  read user files, capture packets/destinations, expose token/config material,
  bypass preview/redaction/encryption, hide the indicator or self-extend.

## Index decisions

- `OBS-070`: `I1 -> I3`. Signed-recipient export UI, encrypted-only service
  boundary, Android SAF contract/build and Windows save-dialog build are proved
  locally.
- `OBS-071`: `I1 -> I3`. Cross-language bounded codec, client presentation and
  no-upload operator decoder are locally proved.
- `OBS-072`: `I1 -> I3`. Case-bound issuance, one-time owner/exact-build redeem,
  independent client verification, explicit consent and nonce persistence are
  locally proved.
- `OBS-073`: `I1 -> I3`. The authoritative controller drives a persistent
  app-level banner with focused widget proof.
- `OBS-074`: `I1 -> I3`. TTL, per-bundle, cumulative byte and count caps are
  enforced by both the signed contract and persisted usage ledger.

## Local proof

- Platform service/schema/upload matrix: `12/12` PASS; Operator Center issuance
  path: `1/1` PASS; relevant Python modules compile.
- Client `support_bundle`: `15/15` PASS. Full app-shell suite: `384/384` PASS;
  analyzer: PASS with no issues.
- Android host security contract: PASS; `assembleDirectDebug`: PASS.
- Windows shell tests: `21/21` PASS; debug executable build: PASS.
- Regenerated candidate preflight remains honestly `BLOCKED`, with
  `candidate_created=false`; distribution is `I3=291`, `I2=28`, `I1=41`,
  `I0=17`, and below-I3 stage split is `16/32/17/21`.

Machine evidence:
`evidence/006K-signed-temporary-support-mode/006K-signed-temporary-support-mode.json`.

## Evidence ceiling

This is local source/test/debug-build evidence from dirty development
worktrees. No frozen revision, exact candidate, production signing/key custody,
deployed RBAC/audit readback, physical Android SAF save, Windows clean-host
save/readback, foreground/background runtime proof, server mutation,
deployment, publication or promotion occurred. Every local `I3` row still
requires exact-candidate runtime/custody evidence before `I4`.
