# WO-013EQ — Bind candidate.21 exact-source privacy controls

Status: `CANDIDATE21_EXACT_SOURCE_PRIVACY_PASS_BRANCH_AND_LIVE_AGGREGATE_OPEN`

Observed: `2026-09-02`

Production/public mutation: `NONE`

## Outcome

Repeat the canonical source-only privacy and STOP-SHIP controls against the
clean exact signed candidate.21 tuple: platform `e2608130...`, client
`1e164586...` and Core `cd8f0f4...`. This replaces candidate.20 as the current
source-privacy authority without changing the immutable candidate.21 bytes.

The permanent STOP-SHIP registry passes `7/7`, all three retained owner-solo
PR/check bindings pass, and fresh GitHub open-P0 label/title queries return
`0/0`. The canonical verifier still returns `BLOCKED`: platform and client
branch protection are `BLOCKED_BY_ACCESS`, Core remains accepted-but-
unprotected, and the generic source-only WIN-003 manual input remains
`NOT_RUN`. Owner policy is retained as policy, not rewritten as a technical
PASS. WO-013EH separately owns the exact candidate.21 Windows default-path
runtime evidence.

## Exact source privacy result

The exact platform source passes `75/75` tests across release-health baseline
and ingest plus support-bundle contracts, migrations, upload, ingest and worker
boundaries. The exact client source passes:

- release-source logging over `145` production files plus all four fail-closed
  negative fixtures;
- observability runtime `29/29`, including planted-secret, generated-redaction,
  bounded queue, rotation, crash-tail and legacy translation contracts;
- support bundle `15/15`, including deterministic manifest/hashes, encrypted-
  only output, planted-material rejection, TTL/volume caps and resumable/offline
  delivery.

The two pure-Dart package workspaces materialize with `flutter pub get
--offline` from the existing cache, under Flutter `3.38.5`. Platform tests run
under Python `3.12.5`. All three exact source worktrees remain clean after the
checks.

These are source and contract checks. WO-013EP separately owns bounded static
inspection of all six exact distribution artifacts. Neither slice replaces
physical Android/Windows runtime, installed-device journals and bundles,
deployed encrypted upload/ingest or the final live no-open-P0/false-green/
privacy owner attestation.

## Ledger effect

`REL_DOD/DOD-12`, `OBS-005`, `OBS-006`, `OBS-010`, `OBS-075` and `OBS-076`
retain `I3` with exact candidate.21 source replacement evidence. `DOD-01`
already retains the same exact-source STOP-SHIP/P0 result from WO-013EL and is
not promoted again. Gate F remains `I3/NOT_RUN` because branch-policy status
and remaining live/manual gates are non-PASS.

Distribution remains `I4=7`, `I3=320`, `I2=19`, `I1=32`, `I0=0` across `378`
unique rows. No Gate F or Gate G decision is generated.

## Commands and results

- `release_1_2_stop_ship_gate.py` with exact platform/client/Core roots,
  `--query-github`, owner-solo evidence and `--expect-nonpass`: exit `0`, local
  `7/7 PASS`, owner-solo `3/3 PASS`, aggregate `BLOCKED`;
- GitHub issue search: open P0 label/title counts `0/0`;
- focused platform privacy suite: `75 passed in 116.60s`;
- client source logging gate and negative contract: `145 + 4 PASS`;
- client observability runtime: `29/29 PASS`;
- client support bundle: `15/15 PASS`.

## Documentation verification

- release/documentation contracts: `65/65 PASS`;
- platform context and script-manifest audits: `PASS`;
- ledger: `378/378` unique rows, distribution unchanged;
- normalized/private hash binding, JSON parse, `git diff --check` and bounded
  sensitive-shape scan: `PASS`.

## Evidence

- normalized record:
  `evidence/013EQ-candidate21-source-privacy/013EQ-candidate21-source-privacy.json`;
- normalized record SHA-256:
  `07f37349ab8a66b61c67f7f4c3ab266419c498c7f54abf3d706ef48acb581ead`;
- private source-verifier report SHA-256:
  `35d659c9abec551ccfb07f957295954ca30581d703714326e1bb48c951556753`;
- private report location:
  `E:/POKROV-tools/temp/candidate21-source-privacy/stop-ship.json`.

The private report contains no credential or customer/provider payload. It
remains outside Git because the normalized record is the tracked release
authority for this slice.
