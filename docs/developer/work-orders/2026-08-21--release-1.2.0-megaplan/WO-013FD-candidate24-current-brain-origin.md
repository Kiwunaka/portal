# WO-013FD — candidate.24 current/Brain read-only origin refresh

Status: `PASS_CURRENT_PUBLIC_API_AND_BRAIN_SOURCE_READINESS_DELIVERY_AUTHENTICATED_CLIENT_RU_AGGREGATE_OPEN`

Observed: `2026-09-03T00:53:30Z`–`2026-09-03T00:54:41Z`

Production/public mutation: `NONE`

## Outcome

Refresh the current-origin public API and Brain-origin source/readiness/delivery
slices against exact private signed candidate.24. The two contours stay
separate and are not relabeled as authenticated client egress, physical-device
traffic or general RU-origin proof.

| Check | Result |
|---|---:|
| Brain deployed payload vs exact platform source | `197/197 PASS` |
| Brain runtime readiness | `23/23 PASS` |
| Brain subscription stability | `5/5 PASS` |
| Enabled delivery from Brain, three samples | `7/7`, `7/7`, `7/7 PASS` |
| Current-origin public health | p95 `36.2096 ms <= 100 ms`, `50` samples, PASS |
| Current-origin public catalog | p95 `49.9565 ms <= 200 ms`, `50` samples, PASS |
| Permanent STOP-SHIP regressions | `7/7 PASS` |
| Owner-solo PR controls | `3/3 PASS` |
| Open P0 label/title counts, platform/client/Core | `0/0` for each repository |
| Aggregate STOP-SHIP | `BLOCKED` |

## Exact boundary

Candidate `pokrov-1.2.0-candidate.24`, app `1.2.0+4053`, binds platform
`06b932b48ffcb92c8ec024b8892aaa9c36359673`, client
`54259b0f84e16c58e2d1f5f04b369af4fd0834b2`, Core
`cd8f0f4169d570d693992a959d81d17c2c44884d` and signed manifest
`bdd51f2c428298e3178fd94d9befaf79aa442445a384f52882995ffd5d9ddeed`.
All three exact source worktrees remain clean.

The Brain source probe uses the canonical deploy map and compares remote
hashes with exact Git blobs. Four files match raw bytes and `193` differ only
by CRLF-to-LF normalization; all `197` match semantically and no remote content
is retained. Readiness and enabled-node probes are read-only and retain only
closed states and node codes.

The current-origin collector disables proxy discovery and binds requests to a
locally assigned physical source. Five warmups are discarded before each
50-sample run. Private sample files stay outside Git because they contain the
local source address; tracked evidence keeps only the fingerprint, aggregates
and hashes.

## Decision boundary

All seven permanent regressions and three owner-solo PR controls pass. Branch
state remains two `BLOCKED_BY_ACCESS` policies plus the owner-accepted
unprotected Core branch. One live manual gate is `NOT_RUN`; independent review
and final live no-open-P0/false-green/privacy attestation are not claimed.

`current_origin` and `brain_origin` may become `PASS` in candidate.24 Gate F.
`FRKN_PLAN/W9-02` stays `I2`; authenticated client egress, general RU-origin,
physical mobile/fixed and additional-ASN coverage remain open. No completion
index level changes.

## Verification and evidence

- normalized record:
  `evidence/013FD-candidate24-current-brain-origin/013FD-candidate24-current-brain-origin.json`;
- external Brain root: `E:/POKROV-tools/temp/candidate24-brain-origin`;
- external current-origin root: `E:/POKROV-tools/temp/candidate24-current-origin`;
- external STOP-SHIP report:
  `E:/POKROV-tools/temp/candidate24-release-refresh/stop-ship.json`.

Tracked evidence contains no credential, private key, token, remote content,
response body, host/address, local source address or device identity. No
runtime, database, network configuration, public asset or stable pointer is
changed.
