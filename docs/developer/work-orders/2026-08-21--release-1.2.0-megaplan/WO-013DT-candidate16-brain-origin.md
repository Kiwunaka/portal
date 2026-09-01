# WO-013DT — candidate.16 Brain-origin read-only refresh

Status: `NON_PASS_ENABLED_DELIVERY_6_OF_7`
Classification: `ACTIVE_EXECUTION_EVIDENCE`
Phase: `09/11`
Candidate: `pokrov-1.2.0-candidate.16`
Production/external mutation: `NONE`

## Outcome

Refresh the exact Brain-origin slice without deployment, restart, host-key
acceptance or screen/input control. The Brain source and control plane are
current and healthy:

| Check | Result |
|---|---:|
| Exact selected source | `197/197 PASS` |
| Runtime readiness | `23/23 PASS` |
| Subscription stability | `5/5 PASS` |
| Enabled delivery TCP | `6/7 FAIL`, repeated three times |

The only non-open delivery row in all three samples is node code `de`. The
other six enabled rows, including `ru_spb`, are open in every sample. This is
therefore not stale Brain source and not a Saint Petersburg-specific failure.

## Datalix boundary

The `de` result aligns with the already retained Datalix boundary: the paid
service is owner-attested as restored, but the observed SSH host identity has
not been confirmed out of band. Strict host verification remains unchanged;
no replacement identity is accepted and no remote repair is attempted.

Because historical Brain-origin PASS requires all three slices — `197/197`,
`23/23` and `7/7` — candidate.16 Brain-origin stays non-PASS. The result is not
converted into a generic platform or client failure, and work does not remain
focused on `ru_spb`.

## Evidence

- normalized record:
  `evidence/013DT-candidate16-brain-origin/013DT-candidate16-brain-origin.json`;
- normalized record SHA-256:
  `166a79791daee61cd05cd4dcc090bef89cf5f2f8803d0a5e93cef3937c6f47d0`;
- exact-source external report SHA-256:
  `539c0b7a03b72629ad39d1b2e74d53a39c4f3bd9c0d73f3618b666ec9747c136`;
- readiness external report SHA-256:
  `cda74184fcccfaf2c428a61fdd42324be357e664823e50f1ac6e1dabe38889ba`;
- delivery external report SHA-256 values:
  `f842e2c40082f2a689342704993ae17acba5a04bd2fdc3c247e1c370d6753341`,
  `a0235b97dfb037d840232e9c9f3ba4a260058ef820094672cb859fd5a602b5b6`,
  `ae69a98031fe96257caf7a5b4405f61b27e3f6b1aa13875f63b1666c8ad7f939`.

Raw reports remain outside Git. No address, hostname, SSH alias, credential,
key, remote content or response body is retained in tracked evidence.

## Decision

`FRKN_PLAN/W9-02`, `REL_GATE/GATE-F` and the exact-candidate origin record gain
fresh bounded evidence without index promotion. Gate F is not regenerated:
its current signed decision remains `NO_GO 2/17/2`, while this later evidence
confirms that the Brain row still cannot become PASS. Gate G, deployment,
public assets and stable promotion remain unauthorized.
