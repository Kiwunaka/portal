# WO-013EB — Bind candidate 20 offline STOP-SHIP and privacy source gates

Status: `CANDIDATE20_EXACT_SOURCE_STOP_SHIP_AND_PRIVACY_PASS_BRANCH_AND_LIVE_AGGREGATE_OPEN`

Observed: `2026-09-01`

Production/public mutation: `NONE`

## Outcome

Run the canonical source-only release controls against the clean exact
candidate 20 tuple: platform `d6898e6...`, client `8ab9815...` and Core
`cd8f0f4...`. No VPN, route, DNS, VM, LDPlayer, phone, server, provider,
payment, release asset or stable-pointer action is part of this slice.

The permanent STOP-SHIP registry passes `7/7` exact-source regression anchors.
GitHub queries return zero open issues with a `P0` label and zero open issues
with `P0` in the title. All three retained owner-solo PR/check bindings pass
without claiming independent review.

The canonical verifier still returns `BLOCKED`: platform and client branch
protection are `BLOCKED_BY_ACCESS`, Core is `FAIL_UNPROTECTED`, and the source-
only verifier reports its generic WIN-003 manual input as `NOT_RUN`. The owner-
accepted no-paid-protection policy is preserved as policy, not rewritten as a
technical pass. WO-013EA separately proves the exact candidate 20 Windows 11
default TUN/DNS/authenticated-egress/rollback slice; that evidence does not
rewrite the generic source report or prove Windows 10/non-default/recovery.

## Exact privacy regression result

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

The two pure-Dart package workspaces materialize only from the existing local
cache with `flutter pub get --offline`. The exact client worktree remains clean.
These are source/contract checks. They do not replace physical Android runtime,
remaining Windows recovery/protocol coverage, deployed encrypted upload/ingest
or the final live no-open-P0/false-green/privacy owner attestation.

## Ledger effect

`REL_DOD/DOD-01` advances `I2 -> I3`: the exact candidate 20 permanent
regressions and P0 query are now locally verified. `REL_DOD/DOD-12` remains
`I3` with candidate 20 replacement evidence. Gate F remains `I3/NOT_RUN`
because branch-policy status, Android runtime, remaining Windows, origins,
provider/Operator/legal, rollback, performance and final live aggregate gates
are still non-PASS.

The distribution becomes `I4=7`, `I3=320`, `I2=19`, `I1=32`, `I0=0` across
`378` unique rows. No Gate F or Gate G decision is generated.

## Commands and results

- `release_1_2_stop_ship_gate.py` with exact platform/client/Core roots,
  `--query-github`, owner-solo evidence and `--expect-nonpass`: exit `0`, local
  `7/7 PASS`, owner-solo `3/3 PASS`, aggregate `BLOCKED`;
- GitHub issue search: open P0 label/title counts `0/0`;
- focused platform privacy suite: `75 passed in 118.25s`;
- client source logging gate and negative contract: `145 + 4 PASS`;
- client observability runtime: `29/29 PASS`;
- client support bundle: `15/15 PASS`.

## Evidence

- normalized record:
  `evidence/013EB-candidate20-offline-source-gates/013EB-candidate20-offline-source-gates.json`;
- normalized record SHA-256:
  `f3943b70d23f2f8ec9239c741223762846ef559aadd2a79657f779d4b3facc91`;
- private source-verifier report SHA-256:
  `784f63ee034248280061d246e16eb7f01c012a004b6c977f8fa0924e71f79fea`;
- private report location:
  `E:/POKROV-tools/temp/candidate20-offline-gates/stop-ship.json`.

The private report contains no credential or customer/provider payload. It
remains outside Git because the normalized record is the tracked release
authority for this slice.
