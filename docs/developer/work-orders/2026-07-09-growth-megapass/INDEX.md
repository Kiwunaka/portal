# Growth Megapass Execution Index

Last updated: 2026-07-12

Status: ACTIVE_EXECUTION

## Source Classification

| Source | Classification | Use |
| --- | --- | --- |
| [00-decisions-analysis-and-next-work.md](00-decisions-analysis-and-next-work.md) | decision/background | Retained owner decisions and research context; resolve runtime truth through canonical owners. |
| [01-market-ready-cis-release-design.md](01-market-ready-cis-release-design.md) | owner-approved target, not runtime truth | Target behavior and release intent; do not present it as deployed or proven. |
| [02-market-ready-cis-implementation-workstreams.md](02-market-ready-cis-implementation-workstreams.md) | active execution map | Dependency-ordered workstream routing for the remaining bounded slices. |
| [03-account-foundation-slice.md](03-account-foundation-slice.md) | landed additive account-foundation evidence | Repository evidence for the additive foundation and its retained compatibility/manual gates. |

The four source files remain unchanged. This index supplies their current
execution status without promoting planning text to product or runtime canon.

## Current

- Additive account-foundation code and tests/test_account_foundation.py are
  landed in the platform baseline.
- The foundation is not production-deployed or production-proven.
- Public numeric account identity, stateless bearer auth, payment fulfillment,
  and entitlement authority remain legacy-compatible.
- The distributed client remains 1.0.0-beta; 1.0.0-rc.1 is a target and stable
  1.0.0 remains unproven.

## Next

1. Select the next bounded slice from the dependency order in
   [02-market-ready-cis-implementation-workstreams.md](02-market-ready-cis-implementation-workstreams.md).
2. Keep account, payment, entitlement, admin, client, and release changes
   anchored to their canonical owners below.
3. Before production promotion of the account foundation, record fresh
   PostgreSQL rehearsal, concurrency, rollback, and preservation evidence.

## Blockers And Gates

- Production PostgreSQL rehearsal and deployment evidence are absent.
- Concurrency, rollback, and preservation gates remain manual and open.
- Legacy-compatible identity, bearer, payment-fulfillment, and entitlement
  authority cannot be described as fully cut over.
- Physical-device, signing, store, provider, and origin evidence remains
  separate from repository implementation.
- No current evidence authorizes stable 1.0.0 claims.

## Canonical Owners

| Concern | Owner |
| --- | --- |
| Product and release-facing behavior | [Product overview](../../../product/portal-vpn-product.md) |
| Runtime and API ownership | [System overview](../../../architecture/system-overview.md) |
| Identity, app-first linking, bonuses, node pools | [App-first and bonus flows](../../../architecture/app-first-and-bonus-flows.md) |
| Deployment, database rehearsal, promotion | [Deployment and access](../../../operations/deployment-and-access.md) |
| Probe and origin evidence | [Monitoring and visibility](../../../operations/monitoring-and-visibility.md) |
| Client delivery and update behavior | [Client delivery plan](../../../operations/client-delivery-update-content-plan.md) |
| Developer routing and workflow | [Agent Context Map](../../agent-context-map.md) and [Developer Guide](../../developer-guide.md) |
| Active client code and docs | C:/Users/kiwun/Documents/ai/POKROV-app and POKROV-app/docs/ |

## Lane And Promotion State

- Platform implementation, tests, work orders, and root docs belong to the
  portal/master policy lane, mapped to origin/master.
- Active Android/Windows implementation, client docs, and current release
  artifacts belong to POKROV-app/main.
- Retired bootstrap/bridge material remains archive or evidence only and has no
  active promotion lane.
- Cross-repository work must retain separate commit, verification, and
  promotion evidence for each lane.
