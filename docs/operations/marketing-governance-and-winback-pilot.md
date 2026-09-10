# Marketing governance and winback pilot

- Classification: `CANONICAL` operational contract
- Current pilot state: `LOCAL_PACKAGE_READY_EXTERNAL_PILOT_NOT_AUTHORIZED`
- Candidate proof: `false`

## Authority

The marketing package has four distinct owners:

- `shared/product-facts.json` and `shared/tariff-catalog.json` own product and
  base-price facts;
- `shared/commercial-contract.json` owns the commercial revision, server price
  authority, seller/terms binding, capacity policy and launch block;
- `shared/contracts/marketing/marketing-governance.v1.json` owns approved claim
  IDs, evidence bindings, permitted profiles/surfaces and stale-claim rules;
- `shared/contracts/marketing/winback-pilot.v1.json` owns the bounded audience,
  offer, creatives, holdout, suppression, capacity and decision rules.

Generated files are derived evidence, not an approval mechanism. Repository
truth intentionally remains `state=draft_blocked`, legal launch false and
holdout percentage null. Editing a generated file, database row or frontend
payload cannot change those gates.

## Capacity and quality guard

The planning figures of 5,000 RUB/month and 300 active entitlement accounts are
owner inputs, not measured throughput or a spending authorization. The commercial
contract continues to own the 300-unit ceiling and 70% pause / strictly below
65% resume thresholds. Pending reservations are forecast only.

`commercial-capacity-owner-policy-v2` additionally uses existing paid-node
capacity policies and the production support queue. Warm CPU/throughput is an
expansion signal; drain, hard rejection or missing CPU/Mbps/loss telemetry stops
new campaign traffic. Resume requires healthy eligible paid nodes and cleared
support pressure as well as entitlement hysteresis. Open high/critical tickets
and overdue tickets not waiting on the customer stop acquisition and winback.
Renewal and recovery retain their exemptions. These gates apply to offers,
order binding, promo delivery and campaign activation immediately; the worker
records audited pause/hold/resume transitions.

The readback separates active entitlement accounts, per-node Mbps/CPU/loss,
connection hints and support counts. Concurrent devices remain `not_measured`;
IP addresses and panel mappings are not used to infer devices or people.

## Legal and seller review boundary

The effective date of part 10.8 of article 5 of the Russian Advertising Law
is **2025-09-01**. Article 1(1) of Federal Law No. 332-FZ of 2025-07-31 added
that provision; article 2(2) sets its separate effective date. The law's general
2026-01-01 date does not apply to part 10.8. Source text:
[article 1](https://www.consultant.ru/document/cons_doc_LAW_511149/3d0cac60971a511280cbba229d9b6329c07731f7/),
[article 2](https://www.consultant.ru/document/cons_doc_LAW_511149/b004fed0b70d0f223e4a81f8ad6cd92af90a7e3b/).
These provisions were checked on 2026-09-06; they do not constitute approval
of any POKROV campaign or channel.

An owned website, in-app slot, cabinet, email or lifecycle message is not
automatically cleared by its surface or audience. Before an external launch,
retain a current review of the actual content, audience, channel and applicable
restrictions. Consent and technical delivery readiness do not replace that
review. A channel decision must not be inferred from a generated contract.

The published offer, checkout/provider page and actual payment receipt must be
checked against the owner's approved seller identity and terms revision.
The current source contract still reports `seller_publication_status=blocked_unpublished`
and `offer_review_status=blocked_unapproved`. `payment_access_key` email contains
an access key and order information; it is not evidence of fiscal receipt
issuance or delivery. A payment webhook acknowledgement is not such evidence
either. Receipt issuer, applicable receipt process, seller details and delivery
must be established for the actual provider setup before claiming that gate
passed. Do not invent seller details or relabel these open items as approval.

## Local package

The locally implemented pilot is limited to users who paid before, have no
current access and expired 7–30 days ago. It excludes refunds/disputes,
unresolved payment/support work, already consumed payment, owner suppression,
missing consent on consented channels, holdout, legal/channel blocks, non-live
campaigns and exhausted paid quota.

The only offer is 10% off `3_months` (669 → 602 RUB) or `6_months`
(1199 → 1079 RUB), once per subject, with an immutable 72-hour server window,
at most 20 paid conversions, no stacking and no more than creative A/B.
Capacity must be green or yellow and below the existing 70% pause boundary.

App and cabinet receive at most one assignment. The payload carries server
price, deadline, terms, conservative remaining quota and exact pilot,
commercial, campaign, offer, creative, variant, assignment, impression and
click lineage. A server checkout ticket repeats that binding. Missing, partial,
stale or subject-conflicting lineage fails closed. Presentation dismissal or
frequency state never replaces server eligibility or suppression.

## Decision rule

The primary metric is `net_revenue_30d_per_capacity_unit`, computed only from
mature server payment/reversal and capacity evidence. No matured denominator
means `insufficient_data`, not zero. Impressions, clicks and CTR are advisory;
they cannot select a winner. First payments alone cannot select a winner.

The decision pack may recommend `stop`, `continue_collecting`, `keep`,
`change_copy`, `change_audience`, `change_benefit`, `disable` or
`owner_review_scale_50`. Legal/capacity/quota/incident/P0–P1 support failures
produce a stop recommendation. The system never launches or scales a campaign
automatically. Scale beyond the 20-payment pilot is capped at 50 and still
requires a separate owner decision after the 30-day observation and ready
holdout evidence.

The API exposes a winner only after the observation window closes, holdout is
ready, every configured creative has a mature primary metric and no stop guard
is active. A missing variant keeps the result at `continue_collecting`; equal
values return `keep` with no winner. The same restriction applies to the raw
decision pack shown by Operator Center and the generated postmortem. A unique
maximum is a descriptive pilot result, not proof of statistical significance.

Operator Center exposes this read model in the promo workspace. The
machine-readable postmortem refuses a winner until the primary metric, holdout,
observation window and stop guards are all ready.

## Local verification

Run from the platform worktree with the active client worktree named
explicitly:

```powershell
python scripts/release_1_2_marketing_pilot_gate.py `
  --client-root C:\path\to\POKROV-app-worktree `
  --evidence-dir docs\developer\work-orders\2026-08-21--release-1.2.0-megaplan\evidence\011F-local-marketing
```

The gate checks generated contracts, claim scanning, every deterministic
suppression vector, backend offer/order/attribution/decision paths, app,
cabinet, marketing and Operator Center consumers, builds and documentation.
Its report always writes `candidate_proven=false`; a local `PASS` is not a live
pilot or release pass.

## Separate owner-authorized execution

The following procedure is a retained runbook, not current authorization.
Before any contact, send, spend, deploy or campaign transition, the owner must
name the exact clean candidate, campaign revision, audience, channels, maximum
scope and allowed external mutations. Retain, for that same revision:

1. non-expired legal approval and permitted channel/profile record;
2. published seller, offer and terms evidence;
3. production payment-provider readiness;
4. deployed commercial, governance and pilot digest readback;
5. fresh green/yellow capacity, worker, alert and admin readback;
6. approved holdout percentage and channel-specific consent evidence;
7. support on-call, owner kill and rollback rehearsal;
8. explicit send/spend ceiling.

If any item is missing or stale, keep the campaign non-live. If separately
authorized, expose only the approved cohort, never exceed 20 paid conversions,
never reset the 72-hour deadline, and monitor legal/capacity/quota/incident/
support stop guards. After the window, collect D30, refund, support and incident
evidence, generate the postmortem and return to the owner for a new decision.
No local fixture may be substituted for this evidence.

## External status labels

- legal/channel approval: `BLOCKED_BY_OWNER_DECISION`;
- seller/terms, provider, deployed readback and live capacity:
  `BLOCKED_BY_ACCESS`;
- holdout percentage: `BLOCKED_BY_OWNER_DECISION`;
- support/consent/rollback: `MANUAL_OWNER_TEST`;
- send, spend, launch and outcome collection: `NOT_AUTHORIZED`;
- commit, push, deploy and promotion: `NOT_REQUESTED`.
