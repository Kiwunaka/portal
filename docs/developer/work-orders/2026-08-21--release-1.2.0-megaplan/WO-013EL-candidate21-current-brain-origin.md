# WO-013EL — candidate.21 current/Brain read-only origin refresh

Status: `PASS_CURRENT_PUBLIC_API_AND_BRAIN_SOURCE_READINESS_DELIVERY_AUTHENTICATED_CLIENT_RU_AGGREGATE_OPEN`

Observed: `2026-09-02T04:49:31Z`–`2026-09-02T04:58:59Z`

Production/public mutation: `NONE`

## Outcome

Refresh the current-origin public API and Brain-origin source/readiness/delivery
slices against the exact signed candidate.21 tuple. These two contours remain
separate. Neither is relabeled as authenticated client egress, physical-device
traffic or general RU-origin proof.

| Check | Result |
|---|---:|
| Brain deployed payload vs exact platform source | `197/197 PASS` |
| Brain runtime readiness | `23/23 PASS` |
| Brain subscription stability | `5/5 PASS` |
| Enabled delivery from Brain, three samples | `7/7`, `7/7`, `7/7 PASS` |
| Current-origin public health | p95 `35.6952 ms <= 100 ms`, `50` samples, PASS |
| Current-origin public catalog | p95 `41.3740 ms <= 200 ms`, `50` samples, PASS |
| Permanent STOP-SHIP regressions | `7/7 PASS` |
| Owner-solo PR controls | `3/3 PASS` |
| Open P0 label/title counts across platform/client/Core | `0/0` for each repository |
| Aggregate STOP-SHIP | `BLOCKED` |

## Exact candidate and method

The run binds private signed candidate `pokrov-1.2.0-candidate.21`, app
`1.2.0+4050`, platform `e2608130e85d9a0f8fa4b920f46cf3d7679332c3`,
client `1e164586d741484b5ae8fb2ee267ef5dd813cadb` and Core
`cd8f0f4169d570d693992a959d81d17c2c44884d`. The exact platform/client/Core
worktrees are clean.

The Brain source probe uses the canonical deploy mapping and compares remote
hashes with exact Git blobs. Four files match raw bytes and `193` differ only
by CRLF-to-LF normalization; zero semantic mismatches and no remote content are
retained. The readiness and live-enabled-node probes are read-only and retain
only closed check states and node codes.

The current-origin collector disables proxy discovery and binds every request
to the same locally assigned physical Ethernet source used by the controlled-
origin method. Five warmups are discarded before each 50-sample run. The raw
sample records remain outside Git because they retain the local source address;
tracked evidence keeps only the environment fingerprint and aggregate values.

## STOP-SHIP boundary

All seven permanent source regressions and all three owner-solo PR controls
pass. Live branch state remains two `BLOCKED_BY_ACCESS` policies plus the
accepted unprotected Core branch. Independent review is not claimed. One
manual live gate is `NOT_RUN`. The read-only GitHub query finds no open issue
with a P0 label or P0 title in the platform, client or Core repository, but this
does not replace the final live no-open-P0/false-green/privacy attestation.

The aggregate remains `BLOCKED`; `candidate_proven=false`. No Gate F or
promotion credit is manufactured from the zero-issue query.

## Index and release decision

`FRKN_PLAN/W9-02` remains `I2` with current status
`CANDIDATE21_CURRENT_PUBLIC_AND_BRAIN_PASS_AUTHENTICATED_CLIENT_GENERAL_RU_OPEN`.
The Brain contour passes exact source, readiness and enabled delivery; the
current contour passes only public API budgets. Authenticated client egress,
general RU-origin, physical mobile/fixed and additional ASN coverage remain
open. WO-013EK's exact-Core RU-Pi AWG pass stays a separate protocol-specific
slice.

Gates D/E/F, `DOD-01` and `DOD-13` receive current-candidate replacement
evidence without level changes. Gate F remains `I3/NOT_RUN`; Gate G, tag,
public release, Store upload, stable pointer and promotion remain unauthorized.
Distribution stays `I4=7`, `I3=320`, `I2=19`, `I1=32`, `I0=0` across `378`
unique rows.

## Verification

- exact Brain deployed-source mapping: `197/197 PASS`;
- Brain readiness/subscription stability: `23/23` and `5/5 PASS`;
- live enabled delivery: `7/7 PASS`, three samples;
- current-origin health/catalog performance gates: `PASS/PASS`;
- candidate-bound STOP-SHIP verifier: `7/7` local and `3/3` solo controls,
  aggregate `BLOCKED` as expected;
- release/documentation contracts: `56 passed`;
- context audit, JSON/hash binding, ledger uniqueness/distribution,
  `git diff --check` and bounded sensitive-pattern scan: `PASS`.

## Evidence

- normalized record:
  `evidence/013EL-candidate21-current-brain-origin/013EL-candidate21-current-brain-origin.json`;
- normalized record SHA-256:
  `9dce798a3f11936528d82aa692980ee710a9505df5284204f14855b0d8d3039d`;
- external Brain source/readiness/delivery root:
  `E:/POKROV-tools/temp/candidate21-brain-origin`;
- external current-origin aggregate/private-sample root:
  `E:/POKROV-tools/temp/candidate21-current-origin`.

Tracked evidence contains no credential, private key, token, raw remote
content, response body, host/address, local source address or device identity.
