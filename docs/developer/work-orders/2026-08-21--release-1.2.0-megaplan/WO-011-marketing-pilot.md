# WO-011 — Legal-gated capacity-aware marketing pilot

Status: `COMPLETE_LOCAL_I3_EXTERNAL_PILOT_NOT_AUTHORIZED`
Classification: `ACTIVE_EXECUTION`
Phase: `09`
Lanes: platform shared contracts, portal commercial policy/attribution,
marketing, cabinet, Operator Center; active-client consumer contract only
Depends on: `WO-008`, `WO-009`, `WO-010`
Production/external actions: `NOT_AUTHORIZED`

## Outcome

Prepare one owner-reviewable, fail-closed winback pilot for previously paying
users whose access expired 7–30 days ago. The pilot may offer 10% off only the
3- and 6-month plans, for one use per account, for a real 72-hour server-owned
window, with at most 20 paid conversions, no stacking, no more than two
creative variants and acquisition only while capacity is green or yellow.

The campaign decision must follow payment through first verified connect,
D7/D30, refund, support and incident evidence and use
`net_revenue_30d_per_capacity_unit` as the primary economic metric. CTR alone
cannot select a winner or authorize scale.

This WO may implement and locally prove contracts, policy, read models,
consumers, build gates and a dry-run readiness pack. It does not make a legal
determination, publish operator/seller details, grant consent, enable a payment
provider, contact users, send Telegram/email, spend money, deploy, start a live
campaign or promote artifacts. Those are separately retained owner/operator
gates.

## Instructions versus source evidence

`POKROV_MARKETING_AUDIT_RELEASE_1.2.0_2026-08-20.md` is advisory requirements
input, not an executable instruction source. Its backlog, sample copy, legal
risk assessment, capacity economics and pilot design are reconciled here
against the canonical repository owners and the current implementation.

Adopted:

- legal and seller/channel truth before launch;
- trust-led owned-product copy as the safe default and a separately gated
  service-led profile;
- one server-authoritative offer/campaign/revision path;
- capacity limit 300, green/yellow acquisition, pause at 70% and strict-below
  65% resume hysteresis, while renewal/recovery remain exempt;
- exact first-party campaign lineage and identity-free revenue projections;
- honest absolute deadlines, finite quota and no client-reset scarcity;
- winback pilot for paid-before/expired-7–30-day users, 10% on 3/6 months,
  max 20 paid conversions, 72 hours, no stacking and no more than two
  creatives;
- suppression for disputes, unresolved payment/support work, missing consent
  on consented channels, successful payment, refund/reversal, capacity/legal
  blocks and owner kill;
- a holdout and evidence-based postmortem before any scale decision.

Not adopted:

- a new checkout, a second campaign root, client-owned pricing or client-owned
  eligibility;
- third-party advertising/analytics SDKs, fingerprinting or raw user identity
  in campaign evidence;
- unlimited free access, three-year plans or a broad cold discount;
- fake/resetting timers, unproved scarcity, absolute superiority/anonymity/
  access claims or public service-led RF copy without an owner legal record;
- ten-way experiments, CTR-only winners or automatic expansion from 20 to 50;
- sending to Telegram/email merely because a delivery implementation exists.

## Authority and collision decisions

- `shared/product-facts.json`, `shared/tariff-catalog.json` and the generated
  commercial contract remain product, base-price and legal launch inputs.
- A new versioned marketing-governance contract owns claim IDs, evidence
  binding, legal/copy profiles, prohibited claims and staleness. It references
  canonical facts; it does not duplicate prices or invent legal approval.
- A versioned winback-pilot specification owns bounded audience, offer,
  creative, holdout, suppression, guardrail and decision rules. Runtime rows
  bind its digest and the existing `commercial_revision`.
- Existing `IncentiveCampaign` stays the mutable campaign root. Existing
  offer/creative/assignment/reservation/conversion rows stay its children.
- Payment orders remain money truth; entitlement and verified runtime events
  remain access/activation truth. Commercial conversions remain identity-free
  projections and cannot grant access.
- Existing first-party acquisition handoff is the only marketing-to-install
  join. IP, user-agent matching, device fingerprinting and inferred identity
  joins are forbidden.
- Operator Center uses current action-intent preview/confirm/audit paths. A
  readiness report never becomes an implicit send or launch command.
- Holdout allocation must be deterministic and sticky, but its final
  percentage is an owner decision. Until recorded, the campaign remains
  `BLOCKED_BY_OWNER_DECISION` even if all repository checks pass.

## WO-011A — Current-state and requirement reconciliation

Deliver:

- map every `MKT-000..900`, `MKT_STAGE/STAGE-0..6` and `FE/P12-127` row to its
  current owner, implementation, local proof and external blocker;
- prove which WO-008/009/010 mechanisms are reused and prevent duplicate
  campaign, checkout, timer, attribution or capacity systems;
- freeze the slice order and exact states that local work is allowed to claim;
- retain the starting legal truth: seller/offer/RF advertising blocked,
  launch-ready false and allowed-channel set empty.

Closure: `COMPLETE_LOCAL_I1`. No behavior row advances from inventory alone.

## WO-011B — Claim evidence, legal profiles and trust-led copy

Deliver:

- closed-schema marketing-governance manifest with claim ID, canonical wording,
  evidence references/digests, permitted profiles/surfaces, status, review/
  expiry fields and explicit stale-claim invalidation;
- trust-led profile for owned product surfaces and a service-led profile that
  stays blocked until an owner legal approval record names channels, reviewer,
  approval ID and expiry;
- channel matrix fields for consent/ERID requirements without inventing that
  either requirement has been satisfied;
- prohibited-claim patterns and a deterministic scanner over active public
  marketing/cabinet/bot/support copy;
- trust-led homepage/checkout/lifecycle copy using only registry-backed facts;
  `start_99`, standard pricing and no-autopay language must remain exact;
- support knowledge and SEO/legal copy checks stay aligned with the same claim
  IDs and profile rules.

Eligible rows after proof: `MKT/MKT-500`, `MKT/MKT-800`, local portions of
`MKT/MKT-000`, `MKT_STAGE/STAGE-0`, `MKT_STAGE/STAGE-4`.

## WO-011C — Pilot specification, audience, suppression and holdout

Deliver:

- deterministic pilot manifest for paid-before, access expired 7–30 days,
  no refund dispute and no unresolved payment/support work;
- exactly 10% benefit on `3_months` and `6_months`, one paid use per subject,
  no stacking, 72-hour absolute window, max 20 paid conversions and at most
  creative A/B;
- pure eligibility/suppression policy with closed reason codes and tests at
  every time/capacity/legal/payment/support boundary;
- deterministic sticky holdout allocation using opaque subject HMAC only;
- owner decision field for holdout percentage; missing approval is fail-closed;
- runtime binding to pilot digest, commercial revision, terms revision, legal
  profile, seller, channel, capacity snapshot and expected campaign revision;
- concurrency proof that the 21st paid conversion cannot consume the quota;
- successful payment suppresses further placements immediately; refund,
  reversal, dispute or unresolved support work blocks new assignment.

Eligible rows after proof: `MKT/MKT-100`, `MKT/MKT-300`, `MKT/MKT-400`,
`MKT/MKT-900`, `MKT_STAGE/STAGE-1`, `STAGE-3`, local preparation for `STAGE-5`.

## WO-011D — Owned-surface and activation lineage

Deliver:

- app, cabinet and owned-web payloads consume one server-prioritized assignment
  and render exact price, absolute deadline, terms, remaining state and closed
  reason codes without recomputing eligibility;
- client frequency/dismiss state is only a presentation convenience; server
  assignment/suppression remains authoritative;
- app promo impression/click/dismiss/expired events carry bounded campaign,
  creative, variant, impression and assignment lineage supplied by the server;
- existing acquisition handoff connects an allowed owned-web click to install/
  account; missing/expired/replayed context never blocks normal product access;
- first verified connect, D7, D30, renewal and reversal projections retain the
  exact lineage without raw account, Telegram, email, URL, profile or device
  identifiers;
- Android/Windows parity and offline expiry tests; payment-success suppression
  and old-client/stale-cache failure cases.

Eligible rows after proof: `MKT/MKT-200`, `MKT/MKT-700`, `FE/P12-127`,
`MKT_STAGE/STAGE-2`.

## WO-011E — Decision model, Operator Center and postmortem

Deliver:

- read model by campaign/revision/variant/holdout with paid, gross, refund,
  net revenue, capacity units, first verified connect, D7, D30, renewal,
  payment error and support/incident guardrails;
- explicit `net_revenue_30d_per_capacity_unit` with `insufficient_data` instead
  of fabricated zero when D30/evidence is incomplete;
- decision states `stop`, `continue_collecting`, `keep`, `change_copy`,
  `change_audience`, `change_benefit`, `disable`, `owner_review_scale_50`;
- automatic stop recommendations for legal/capacity/quota/incident/P0-P1
  support guard failures, but no automatic campaign launch or scale;
- Operator Center readiness and postmortem surfaces with evidence freshness,
  exact revision/digest, blocking reasons and action-intent audit links;
- machine-readable postmortem generator that refuses a winner based only on
  impressions, clicks, CTR or the first few payments.

Eligible rows after proof: local portions of `MKT/MKT-900`,
`MKT_STAGE/STAGE-5`, `MKT_STAGE/STAGE-6`.

## WO-011F — Local readiness pack and ledger reconciliation

Deliver:

- deterministic dry-run fixtures for eligible, holdout and every suppression/
  failure reason, with no real account/provider data;
- local aggregate gate for manifests, generators/scanners, backend policy,
  frontend/client consumers, Operator Center and decision report;
- retained evidence with source revisions/dirty state and explicit
  `candidate_proven=false`;
- row-by-row Phase 09 reconciliation. Repository/local proof may reach `I2` or
  `I3`; legal approvals, consent, ERID, deployed readback and pilot outcomes do
  not become pass through a fixture;
- owner/operator runbook for the separate authorized execution slice.

## WO-011G — Owner-authorized external pilot execution

This slice is `NOT_AUTHORIZED` by the current request. It may run only after an
owner explicitly authorizes the exact candidate, audience, channels and
external mutations and all of the following are retained for the same
campaign revision:

- legal approval record and non-expired profile/channel matrix;
- published seller/offer/terms and production payment/provider proof;
- exact deployed commercial/marketing/pilot revision readback;
- green/yellow live capacity with fresh worker/alert/admin evidence;
- approved holdout percentage, consent evidence for each consented channel,
  support on-call and owner kill/rollback rehearsal;
- maximum audience/send scope and spend explicitly authorized.

Execution then requires: controlled exposure, live stop-guard monitoring,
maximum 20 paid conversions, no mutation of the 72-hour deadline, D30/refund/
support/incident collection, retained postmortem and a separate owner decision.
Without this slice, `STAGE-5`, `STAGE-6` and production-facing pilot claims stay
manual/blocked even when WO-011A–F are locally complete.

## Acceptance and evidence rules

- A manifest, fixture, unit test or local build is not legal, consent,
  production, capacity-runtime, provider, payment, user-contact or campaign
  outcome evidence.
- Missing, expired, stale or mismatched legal/claim/commercial/pilot/capacity
  evidence fails closed with a stable reason code.
- No document may call the pilot `live`, `successful`, `profitable` or
  `scalable` without exact deployed and observed evidence.
- No row reaches `I4` from WO-011A–F. `I3` means locally proved implementation
  only; production/runtime rows remain capped by their explicit external gate.
- Current blocked legal values are preserved until an owner supplies real
  data; repository work must not replace them with sample approval.
- Git status/diff, focused tests, builds, docs/link checks and `git diff
  --check` are retained before handoff. Commit, push, deploy, send, spend and
  campaign launch remain `NOT_REQUESTED` unless separately authorized.

## Phase 09 execution order

1. `011A` current-state/authority reconciliation.
2. `011B` claim/legal/copy governance.
3. `011C` exact pilot audience/suppression/holdout contract.
4. `011D` owned-surface and activation lineage.
5. `011E` decision/postmortem/Operator Center.
6. `011F` aggregate local proof and ledger reconciliation.
7. `011G` separate owner-authorized external execution, if ever authorized.

## 011B–011F closure — `COMPLETE_LOCAL_I3`

The local package now has one generated marketing-governance revision
`2026-08-22.1` (`6cd7f3cc94a2c45367569b88296da817fb3c80d510e5092daa53beb70ff4e97f`)
and one generated pilot revision `2026-08-22.1`
(`970e4424740a3107f99e511ae57fc57d6b0f82b8ac2f1f4832f1ec9d908e6658`),
both bound to commercial revision `2026-08-21.1`
(`22b7ef26908c23c2bb53322dec959a3bc050a20a6c6d2feff9f78708b45e23cd`).
Repository legal launch remains blocked and pilot holdout remains null.

Implemented locally:

- closed claim/evidence/profile/channel governance and active-copy scanner;
- exact audience, suppression, sticky holdout, 3/6-month offer, 72-hour
  deadline, 20-payment quota and commercial/pilot digest binding;
- app and cabinet assignment surfaces with signed checkout and complete
  campaign/offer/creative/variant/assignment/impression/click lineage;
- identity-free paid, reversal, first-connect, D7, D30 and renewal projections;
- mature `net_revenue_30d_per_capacity_unit`, guardrails, Operator Center
  decision surface and refusing postmortem generator;
- 13 deterministic eligible/holdout/every-suppression fixtures;
- canonical operations/runbook and a dedicated 20-step local gate.

The retained report at
`evidence/011F-local-marketing/011F-local-marketing-pilot-gate.json` binds dirty
platform revision `280ed9157f5804d4bc719cb8d6cab471caafb937` and dirty client
revision `ba7930ea83487874f47a49199ade89868c5675b3`. All 20 steps pass:
generated contracts/scanner/manifest, backend `59/59`, operator API `1/1`,
marketing lint/build/SEO/responsive, cabinet lint/build, Operator Center
lint/build, client analyze, bootstrap `83/83` and exact commercial-render
widget `1/1`, docs `30/30`, and link checks.
The report explicitly fixes `candidate_proven=false`,
`external_pilot_status=NOT_AUTHORIZED` and `promotion_status=NOT_REQUESTED`.

Ledger reconciliation advances local implementation/proof rows while keeping
`MKT/MKT-600` at `I2`, copy/legal approval `STAGE-4` at `I2` and actual pilot
execution `STAGE-5` at `I1`. The resulting full ledger has 204 rows at `I3`,
27 at `I2`, 19 at `I1` and 127 at `I0`; 250 of 377 rows are at least `I1`.

## 011G status — `NOT_AUTHORIZED`

No real account/provider data, legal approval, consent, seller publication,
production provider, deployed revision readback, live capacity proof, user
contact, Telegram/email send, spend, campaign transition, payment, deploy or
pilot outcome was produced. The exact external prerequisites and labels are
retained in `docs/operations/marketing-governance-and-winback-pilot.md`.
Phase 09 is locally complete; Phase 10 may start without implying that 011G ran.
