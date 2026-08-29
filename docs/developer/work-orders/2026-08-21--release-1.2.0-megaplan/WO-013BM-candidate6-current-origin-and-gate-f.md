# WO-013BM — candidate.6 current-origin and Gate F

## Outcome

Add exact candidate.6 current-origin evidence, preserve Brain and RU as
separate origins, and regenerate Gate F without rewriting WO-013BL.

The public health and catalog probes ran from a clean detached checkout of
platform `5713324c1c0c2566befadf527bc09ec0ecf84a4e`. Both used the current
workstation direct-network profile, five warmups and 50 retained samples:

| Budget | p95 | Limit | Result |
|---|---:|---:|---|
| current-origin health | `65.3908 ms` | `100 ms` | `PASS` |
| current-origin public catalog | `67.553 ms` | `200 ms` | `PASS` |

The temporary exact-source worktree was removed after capture. The four raw
report/gate artifacts remain outside Git with SHA-256 values
`9e6f0baec6c4476b5ffc6eaf12a8fa71ba7a6ef540158cf47de2cfe509798135`,
`1d2a910992520b2382c8db6c4b147021e14d9e166fb0b04dcf2ba079eea3c700`,
`18acb1a4a604997fda1ec2baafc8044d093585c094c1784029eae03b8aab3de6`
and `9cb1f13ee3be7ba8d718bf012c5e24c979b331ae7c3b8109a8824560e9343283`.

## Brain boundary

The read-only Brain source probe tried both address candidates in the owner's
Brain inventory section. Both rejected the previously trusted key and retained
password candidates. No authenticated session, source report, remote content,
deploy, restart or runtime mutation occurred. Candidate.6 Brain-origin is
therefore `BLOCKED_BY_ACCESS`, not PASS and not a runtime mismatch. RU-origin
remains separately `NOT_RUN`.

## Gate F result

The successor candidate.6 Gate F validates all 19 evidence pointers with zero
validation errors and returns `BLOCKED`: `3/19 PASS`, `16/19 non-PASS`,
`0 FAIL`. Supply chain, release-doc/manifest binding and current-origin pass.
Physical Android, isolated Windows, Brain and RU origins, authenticated client
egress, provider, Operator, legal/commercial, comparable performance,
post-promotion health and other manual rows remain non-PASS. Hosted private
checks remain zero-step `SKIPPED_BY_OWNER` under `OWNER_SOLO_EXCEPTION`.

- `REL_GATE/GATE-F` remains `I3` with
  `SIGNED_CANDIDATE6_GATE_F_BLOCKED_3_PASS_16_NONPASS`.
- `FRKN_PLAN/W9-02` remains `I1`: current-origin passes, Brain access is
  blocked and RU-origin is not run.
- `FRKN_PLAN/W9-05` remains `I1`: exact cross-platform and transport metrics
  are incomplete.
- No ledger row advances; distribution remains `I4=4`, `I3=316`, `I2=21`,
  `I1=37`, `I0=0`.
- No tag, public release, store object, stable pointer, deploy or Gate G
  authorization occurred.

Machine evidence is under
`evidence/013BM-candidate6-current-origin-and-gate-f/`. Evidence/input/decision
SHA-256 values are respectively
`7fb7402344ad3053bd96b91013c4e1fc7f56ac8fdbf2e339110caf6e4f9ed5e9`,
`49e8eb5d12fdfb72e25bf37f050dca3770909bc05528636f71933e651f7329b2`
and `21d959959332678a0dd05ac2aa14b8fcf05b33fcc541735a5b0ae1b868641cdf`.
It contains no address, hostname, device serial, credential, key, customer
data, remote payload or raw provider response.
