# WO-013FQ — candidate.29 current/Brain origin and Gate F NO_GO

Status: `EXACT_CANDIDATE29_GATE_F_NO_GO_2_PASS_17_NON_PASS_1_FAIL`

Observed: `2026-09-03T10:32:04Z`–`2026-09-03T10:37:06Z`

Production/public mutation: `NONE`

## Outcome

Refresh the current-public and Brain-origin contours for exact private
candidate.29, keeping them separate from authenticated client egress and
general RU-origin proof. The API measurements meet their latency budgets, but
an already-active owner `tun0` prevents honest current-origin attribution and
is left untouched. Brain source and readiness pass, but the enabled `de` node
times out in three consecutive Brain samples while the other six nodes remain
open.

This is one explicit release failure. The successor Gate F decision is:

```text
NO_GO
required=19
pass=2
non_pass=17
fail=1
validation_errors=0
candidate_validation=PASS
gate_g_authorized=false
```

## Exact results

| Check | Result |
|---|---:|
| Brain deployed payload vs exact platform source | `197/197 PASS` |
| Brain runtime readiness | `23/23 PASS` |
| Brain subscription stability | `5/5 PASS` |
| Enabled delivery from Brain, sample 1 | `6/7`, `de=timeout`, FAIL |
| Enabled delivery from Brain, sample 2 | `6/7`, `de=timeout`, FAIL |
| Enabled delivery from Brain, sample 3 | `6/7`, `de=timeout`, FAIL |
| Source-bound API health measurement | p95 `41.1541 ms <= 100 ms`, `50` samples, no origin credit |
| Source-bound public catalog measurement | p95 `45.1495 ms <= 200 ms`, `50` samples, no origin credit |

The collector disables proxy discovery and binds every request to the physical
Ethernet source address. The host default route is nevertheless owned by an
already-active `tun0`; source-address binding alone does not prove that packets
bypassed it. The owner's tunnel, route, DNS and desktop input remain untouched,
so `current_origin` is `BLOCKED_BY_ACCESS`, not PASS. Private sample records
remain outside Git because they contain the local source address; tracked
evidence retains only the environment fingerprint, aggregates and hashes.

## DE diagnostic boundary

A direct read-only SSH diagnostic stops at strict host-key validation. The
saved keys for the two owner-declared IP addresses match one another, but the
currently presented key differs. No permissive override is used and
`known_hosts` is not changed. Direct administration therefore remains
`BLOCKED_BY_ACCESS_HOST_KEY_REVALIDATION` until the new host key is verified
through an independent trusted channel.

This does not change the Brain observation: its independent port probe already
reports three consecutive timeouts for the enabled `de` delivery endpoint.

## Gate F effect

`current_origin` changes from `NOT_RUN` to `BLOCKED_BY_ACCESS` without PASS
credit. `brain_origin` advances from `NOT_RUN` to explicit `FAIL`. The other
fifteen check values are unchanged, so the aggregate moves from WO-013FP
`BLOCKED 2/17/0` to `NO_GO 2/17/1`. The `non_pass` count includes the failing
row.

The failure is infrastructure availability, not a CLI build or signed-supply
failure. Candidate.29 bytes remain immutable and its signature remains valid.
No replacement candidate is warranted until a source or artifact change is
required.

## Verification

```text
remote Brain source probe -> 197/197 PASS
Brain readiness -> 23/23 PASS; subscription 5/5 PASS
enabled delivery -> 6/7 three times; de timeout three times
source-bound health -> 50 samples, p95 41.1541 ms, measurement PASS; origin BLOCKED
source-bound public catalog -> 50 samples, p95 45.1495 ms, measurement PASS; origin BLOCKED
release_1_2_gate_f.py -> expected NO_GO exit 2
candidate_validation=PASS; required=19; pass=2; non_pass=17; fail=1; validation_errors=0
```

## Evidence digests

| File | SHA-256 |
|---|---|
| `013FQ-candidate29-current-brain-origin.json` | `94fc4398d48985ce9cc1eadab993860e2533a2028a2a28c53ca38b2ac642a2c0` |
| `013FQ-candidate29-gate-f-evidence.json` | `4710779672029205bee1645a451ea85bb8e802b3e0244bb71991c9c8de4cf9bb` |
| `013FQ-candidate29-gate-f-input.json` | `da5cc0c70a087f34fad0e0b5db0f9f3129579079c7601235ba2ab89569d266a5` |
| `013FQ-candidate29-gate-f-decision.json` | `5e0c29ad7dde8aebce3bec5a30f944e16ccb3fe9e5c5a751b1fee57179b492a6` |

External raw reports are retained under
`E:/POKROV-tools/release-evidence/1.2.0-candidate29-current-brain-origin-2026-09-03/`.
Tracked evidence contains no credentials, tokens, private keys, response
bodies, addresses, device identifiers or presented host-key fingerprint.

No completion-index level changes. Gate G, public tag/assets, Store
submission, production deploy and stable promotion remain unauthorized.
