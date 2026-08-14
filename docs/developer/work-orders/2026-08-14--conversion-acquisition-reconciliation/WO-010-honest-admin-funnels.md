# WO-010 — Honest Admin Funnels

Status: `COMPLETE`

## Outcome

Админка показывает, где теряются люди, не складывая разные идентичности и
пересекающиеся источники в фальшивую линейную конверсию.

## Required Views

### Acquisition

Eligible entry → actual download or bot intent → checkout start →
provider-confirmed paid. Filters: time range, source, campaign, platform and
entry path. Each card names its denominator and identity unit.

### Product

Account/app open → trial activation → first confirmed connect → returning
connect → paid conversion/expiry recovery. This funnel uses identified account
or installation lineage only.

## Semantics

- anonymous browser session, Telegram user, account and device are distinct;
- use cross-boundary lineage only after valid WO-004 handoff;
- no handoff is `unknown`, not inferred from timestamps/IP/UA;
- mutually exclusive step definitions prevent double counting;
- dashboard may show coverage percentage for linked vs unknown journeys;
- raw identifiers, campaign tokens and customer event rows are not exposed in
  aggregate UI or exports by default;
- paid/access truth comes from signed provider callbacks and entitlement data,
  never from funnel events.

## Checks

Deterministic fixture cohorts, numerator/denominator and overlap tests, timezone
boundary tests, admin API auth/redaction, responsive admin E2E and comparison of
aggregate totals to source queries on a sanitized production readback.

## Current Evidence

- `PASS_LOCAL`: `/api/admin/funnel/summary` returns separate `acquisition` and
  `product` cohorts; every downstream set is intersected with its preceding
  stage and duplicate Event/Stars/external-order evidence counts once.
- `PASS_LOCAL`: admin `/funnel` has explicit `Реклама` and `Продукт` views and
  does not receive raw session hashes, handoff tokens or customer ids.
- `PASS`: final admin regression and migration-order coverage passed; deployed
  API/admin surfaces are healthy. A fresh authenticated production visual
  comparison remains an optional operator follow-up, not cohort evidence.
