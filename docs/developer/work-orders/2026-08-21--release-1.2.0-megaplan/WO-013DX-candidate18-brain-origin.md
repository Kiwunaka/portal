# WO-013DX — Candidate 18 Brain-origin read-only refresh

Status: `PASS_EXACT_CANDIDATE18_BRAIN_ORIGIN_READ_ONLY`
Classification: `ACTIVE_EXECUTION_EVIDENCE`
Phase: `05/10/11`
Candidate: `pokrov-1.2.0-candidate.18`
Production/external mutation: `NONE`

## Outcome

Refresh the Brain-origin slice against the exact candidate.18 platform source
without deployment, restart, database write, host-key change or screen/input
control.

| Check | Result |
|---|---:|
| Exact selected source | `197/197 PASS` |
| Runtime readiness retry | `23/23 PASS` |
| Subscription stability | `5/5 PASS` |
| Enabled delivery TCP sample 1 | `7/7 PASS` |
| Enabled delivery TCP sample 2 | `7/7 PASS` |
| Enabled delivery TCP sample 3 | `7/7 PASS` |

The selected live payload matches exact candidate.18 platform revision
`d6898e63c5c9ab7dd267b9d5150b54196f99d967`: four files match raw bytes and
193 differ only by CRLF-to-LF normalization. There are zero semantic
mismatches and no remote content is retained.

All seven enabled delivery rows are open in every redacted sample, including
`de` and `ru_spb`. This supersedes candidate.16's historical `6/7` Brain
result; it does not transfer any client-session, physical-device or RU-origin
credit.

## Retry boundary

The first readiness attempt is retained as non-PASS. One of 23 checks lost its
individual management SSH connection before producing an application result;
the other checks and all five subscription samples completed. An immediate
isolated retry passes `23/23` with another five stable subscription samples.

This is classified as a transient management-path sample, not silently erased
and not counted as application failure. The final Brain-origin result is based
on the exact source pass, complete readiness retry and three independent `7/7`
delivery samples.

## Evidence

- normalized record:
  `evidence/013DX-candidate18-brain-origin/013DX-candidate18-brain-origin.json`;
- normalized record SHA-256:
  `ef9fb5da513246ff5d8bb247f7017f269ba72a62dae9eeb28625d769cdc087f2`;
- exact-source external report SHA-256:
  `f36036b2e089f3ad77f85e0ebd6f5908e150fc09f5d62056fbe819913e63bbfa`;
- initial readiness external report SHA-256:
  `b58d4587116da78a0157189c1cb661102016ab29bd33310093f9084afe1a8601`;
- passing readiness retry external report SHA-256:
  `1ae22aa504556d2675f75fffe1b4d22f2f17f5c36e94210e9ef4376a3000a80b`;
- delivery external report SHA-256 values:
  `376fb7a4303aa89cc5770341fbe82078b3c5888b3e8f6fa98f5947530304c37f`,
  `03e45ea6d9b1ea1f788b2091d18c1eeb0b8a8c02ca9986b22479f3ce5e233dce`,
  `e834db29ee1d58053807dd3c45f586d24215fe7e3150a5b7960f231978f31f04`.

Raw reports remain outside Git. Tracked evidence retains no address, hostname,
SSH alias, credential, key, token, remote file content or response body.

## Decision

Candidate.18 Brain-origin source, readiness and enabled-delivery slices pass.
`FRKN_PLAN/W9-02` remains `I2` because current-origin authenticated client and
RU-origin are separate and still open. `REL_GATE/GATE-D` and `GATE-F` gain
current evidence without index promotion. Gate F is not regenerated; physical
Android, connected Windows, current/RU origins, provider/Operator/legal,
comparable performance, runtime rollback and aggregate no-open-P0 evidence
remain open. Gate G and public/stable promotion remain unauthorized.
