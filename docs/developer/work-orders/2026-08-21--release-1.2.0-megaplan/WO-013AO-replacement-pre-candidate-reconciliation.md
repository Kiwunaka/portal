# WO-013AO — Replacement pre-candidate reconciliation

Date: `2026-08-28`

Status: `LOCALLY_PROVED_PRE_CANDIDATE / HOSTED_CHECKS_BLOCKED`

## Objective

Reconcile the current post-candidate source line after the Gate B correction,
owned AWG/DNS lab work and Android Core rebinding without transferring any of
that evidence into signed `candidate.3` or creating a replacement candidate.

## Exact source tuple

| Lane | Revision | Branch / PR | State |
| --- | --- | --- | --- |
| Platform | `e5ef03ac7ab013d8810cc9c6ea9ccc40cebd11db` | `codex/awg-owned-lab-deploy`, PR `#58` to `master` | clean and pushed |
| Client | `c196dff6bf72c325d5bba675fe19342cd3821f61` | `codex/release-1.2.0-candidate-8-source`, PR `#33` to `main` | clean and pushed |
| Core | `f44dbe89d6b89954032a1a798c2209d8c0aff90d` | `codex/fix-egress-event-subsystem`, PR `#6` to `main` | clean and pushed |

This tuple is `PRE_CANDIDATE_LOCAL`. It is not signed, promoted, public or
stable. Signed private `candidate.3` remains the exact-candidate authority and
remains `NO_GO`.

## Android Core provenance reconciliation

Core Android was built twice from `f44dbe89d6b89954032a1a798c2209d8c0aff90d`.
Both AARs were byte-identical with SHA-256
`ca391059b6676de5a2cfbf582395fd7ab0b0b5979c8a0c40faaa7208b79178e5` and
size `107394593` bytes. The bytes also match the client AAR previously built
from `54e76bbb...` because the intervening Core commit changes tests only.

The client seed, validation fixtures and canonical client release documents
now bind Android source provenance to `f44dbe89...`; no runtime binary changed.
Windows remains bound to its separately declared Core revision and artifact.

## Current local quality evidence

The aggregate local gate ran with exact Node `22.14.0` and the clean tuple
above. All `15/15` steps passed:

- performance contract and `30/30` contract tests;
- Flutter analysis and `400/400` app-shell tests;
- client seed, release-v2, documentation and repository-hygiene contracts;
- WebApp lint/build and `69/69` cabinet Playwright tests;
- marketing build, SEO, responsive, accessibility and reduced-motion checks;
- AdminApp production build;
- local static performance collection and required gate `9/9 PASS`.

The private local report `010I-local-quality-gate.json` has SHA-256
`facc6b09b7ad94768c59f946d7164adbc7c229a6de605fa958bdc20bb5599e6e`.
It explicitly records `candidate_proven=false`, `local_status=PASS` and
`promotion_status=MANUAL_OWNER_TEST`. Exact candidate/device performance,
artifact comparison, selected browser lab, authenticated controlled-origin
API work and signing/device/origin proof remain non-PASS manual lanes.

## Owned AWG and DNS physical slice

The retained
[physical pre-candidate record](../../../audit-artifacts/2026-08-28-owned-awg-dns-physical-pre-candidate.md)
binds production-signed working Android package `1.2.0+4044` without treating
it as a candidate.

- AWG2 and randomized-trailer AWG3.1 live server/client alignment pass.
- On physical Beeline, both guarded UDP controls reached the server and were
  echoed `3/3`, while the phone received `0/3`. Both handshakes therefore stay
  `BLOCKED_BY_NETWORK_CURRENT_ORIGIN`; this is not a cryptographic failure or
  universal transport verdict.
- Direct HTTPS DoH returned valid responses for the bounded AI/Games set.
  Product routes still require the VPN, so DNS-only ChatGPT/Gemini/Xbox access
  remains `NOT_IMPLEMENTED` and would be a separate Smart-DNS architecture.
- Normal WARP plus independent IP and DNS egress passed after exact lab unbind.

## Hosted PR evidence

Platform PR `#58` and client PR `#33` are mergeable, but their required jobs
received zero execution steps. GitHub reports failed account payments or a
spending-limit block. They are `BLOCKED_BY_ACCESS_GITHUB_BILLING`, not product
test failures and not passes. `OWNER_SOLO_EXCEPTION` does not waive them.

Core PR `#6` passes `test`, Android artifact reproducibility, Windows artifact
reproducibility and Apple source build. Its `release-contract` job fails
closed because client `main` still binds the prior Core source; the current
client PR contains the exact `f44dbe89...` binding but is not merged.

No PR is merged while these required checks are unresolved. No deploy,
candidate creation, public asset, stable pointer or production mutation occurs
in this work order.

## Ledger decision

`FRKN_PLAN/W3-01` advances `I1 -> I3`: the isolated POKROV-owned lab now has a
retained server record, exact alignment readback, default-off policy and
guarded kill/unbind path. This does not claim a successful tunnel or cohort.

The tuple also strengthens existing `I3` local evidence for `REL/PERF-001`,
`REL_GATE/GATE-E`, `FRKN_PLAN/W3-02`, `W3-03` and `W6-02`, and narrows the
`UNCERT-02` boundary without advancing it. Exact signed candidate,
device/origin matrix and promotion evidence required for `I4/I5` are absent.

Distribution becomes `I4=4`, `I3=313`, `I2=19`, `I1=40`, `I0=1`.

## Next action

1. Restore private-repository Actions through Billing & plans, or obtain an
   explicit owner instruction before changing repository visibility.
2. Require successful platform/client app-bound checks on the exact PR heads.
3. Merge the client binding under the solo PR control, rerun Core
   `release-contract`, then promote Core and platform only with their required
   checks green.
4. Freeze and sign a replacement exact candidate from the promoted tuple.
5. Run the candidate-bound Android/Windows, current/Brain/RU-origin, provider,
   Operator, legal and performance matrices before any Gate F `GO` or Gate G.
