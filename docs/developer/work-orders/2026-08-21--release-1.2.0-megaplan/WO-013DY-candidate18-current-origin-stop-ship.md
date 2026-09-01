# WO-013DY — Candidate 18 current-origin API and STOP-SHIP slice

Status: `PASS_CURRENT_ORIGIN_PUBLIC_API; STOP_SHIP_LOCAL_7_OF_7; AGGREGATE_BLOCKED`
Classification: `ACTIVE_EXECUTION_EVIDENCE`
Phase: `01/08/11`
Candidate: `pokrov-1.2.0-candidate.18`
Production/external mutation: `NONE`

## Outcome

Run the source-bound public API budgets and current STOP-SHIP/P0 checks against
the exact candidate.18 source tuple without starting a client tunnel, changing
routes or DNS, controlling a screen, deploying code or changing release state.

| Check | Result |
|---|---:|
| Current-origin health | `43.5854 ms p95 <= 100 ms`, `50` samples, PASS |
| Current-origin public catalog | `43.7925 ms p95 <= 200 ms`, `50` samples, PASS |
| Permanent STOP-SHIP regressions | `7/7 PASS` |
| Owner-solo PR controls | `3/3 PASS` |
| Open GitHub issues with `P0` label | `0` |
| Open GitHub issues with `P0` in title | `0` |
| Aggregate STOP-SHIP | `BLOCKED` |

The API collector disables proxy discovery and binds every socket to the same
assigned physical Ethernet source used by the prior controlled-origin method.
The ambient tunnel-like default route is excluded from the evidence path. Five
warmups are discarded before each 50-sample measurement. No literal source
address is retained in Git.

## STOP-SHIP boundary

Exact candidate.18 platform `d6898e63...`, client `820ca101...` and Core
`cd8f0f41...` worktrees are clean. All seven permanent regression anchors
pass. Current hosted controls remain two `BLOCKED_BY_ACCESS` and one
`FAIL_UNPROTECTED`, matching the owner's no-paid-branch-protection policy.
Three reviewer checks retain explicit `OWNER_SOLO_EXCEPTION`, and the three
compensating PR controls pass without claiming independent review.

One manual live gate remains open. Zero queried P0 issues is therefore not the
final no-open-P0/false-green/secret-leak attestation. The aggregate stays
`BLOCKED`; no Gate F or promotion credit is manufactured from this slice.

## Evidence

- normalized record:
  `evidence/013DY-candidate18-current-origin-stop-ship/013DY-candidate18-current-origin-stop-ship.json`;
- normalized record SHA-256:
  `5dc4585ab92e760b3563fd744c629236bc043b0435fdf6587ef29424ed2c69f0`;
- health gate SHA-256:
  `e28107e244c9d0e0453dccc116394bb01db615d7318ae4c98265f6c19b7e38b8`;
- public-catalog gate SHA-256:
  `90b93e4e95fcffaf4dfed097c304cf4db80f0a0d19d4ddc21451d9381faad986`;
- private health sample record SHA-256:
  `93ec118835980920e58dd16956bb3d5b4d5f3b80d41ebf5d6b882c2b5cd0e9d6`;
- private public-catalog sample record SHA-256:
  `352241e4e4e1ea79f782aee89c33c0142c6a6f51d3ca1e191ffa5431b9299cd5`;
- STOP-SHIP report SHA-256:
  `c77a45085cff744b0f2e1c728175743b49d2bf89acae55a3f9b8c101b69d0a1b`.

Private sample records remain outside Git because they contain the local
source address. Tracked gate summaries retain only the environment fingerprint,
candidate source, sample counts, thresholds and results.

## Decision

Candidate.18 current-origin public API performance and permanent STOP-SHIP
regressions pass. Authenticated client egress, live-device privacy/false-green
attestation and the one manual gate remain open. `PERF-001`, `DOD-01`,
`DOD-13`, Gate E and Gate F gain current evidence without index promotion.
Gate F remains `NOT_RUN`; Gate G and public/stable promotion remain
unauthorized. Distribution stays `I4=5`, `I3=319`, `I2=20`, `I1=34`, `I0=0`
across `378` rows.
