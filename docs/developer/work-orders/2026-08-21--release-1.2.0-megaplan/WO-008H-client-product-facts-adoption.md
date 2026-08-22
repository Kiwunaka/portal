# WO-008H — Active-client product facts adoption

Status: `COMPLETE_I3`
Classification: `ACTIVE_EXECUTION`
Phase: `06`
Lane: platform shared facts / active client runtime consumer
Depends on: `WO-008A`, `WO-003H`
Production/external actions: `NOT_AUTHORIZED`

## Bounded outcome

Close `REL/CONTRACT-001` without creating a second commercial authority. The
platform remains the sole owner of shared product, public-URL, tariff and
commercial facts. The active client receives a generated, digest-pinned typed
projection, consumes it in its runtime seed and rejects drift in the standard
seed gate.

This work does not make the client authoritative for prices, promo terms,
referral account state, quota, orders, payments or entitlements. Those values
remain server responses under the commercial contract.

## Implemented boundary

- `scripts/sync_shared_surface_facts.py` now reads the generated commercial
  contract and projects its revision plus product/commercial/tariff digests
  into `config/product-contract.seed.json`.
- The same synchronizer generates
  `platform_product_facts.g.dart` with typed platform scope, engine, route,
  trial, Telegram reward, referral-policy, legal-path and support constants.
- `--check` is strictly read-only and fails if any owned JSON field or the
  generated Dart bytes drift. A negative temporary-fixture regression proves
  that rejection does not rewrite the target.
- `SeedAppContext` consumes generated platform/runtime/trial/reward/support
  facts. The client standard seed validator invokes the active platform
  synchronizer and also requires the runtime consumer markers.
- Platform and client canonical product docs describe the owner/projection
  boundary and the retained server authority. The platform product owner now
  names the current public `1.1.6+29` line; no `1.2.0` public-release claim was
  introduced.

The first generated-file integration used a Dart `part`. The existing client
presentation guard rejected the increase from 29 to 30 parts. The generated
module was converted to an ordinary imported library and the guard returned to
29 without raising or weakening the ceiling. That failure is retained as a
corrected diagnostic, not credited evidence.

## Verification — 2026-08-22

- Platform shared-facts/admin/commercial/revision matrix: `25/25 PASS`.
- Ruff check and format check for the synchronizer/tests: `PASS`.
- Active-client projection `--check`, including the negative no-write drift
  regression: `PASS`.
- Explicit-root client `validate-seed.ps1`: `PASS`; it reports product-facts,
  version, observability, logging, release-handoff v2, CI, hygiene, standard
  runner, presentation, performance and docs contracts green. The Core checkout
  remains honestly labelled `DIRTY_DEVELOPMENT_REPLACEMENT_PENDING`.
- `packages/app_shell` Flutter analyze: `PASS`, no issues.
- Combined client bootstrap/seed suite: `243/243 PASS` before the final proof
  assertions; the exact updated product-facts runtime assertion rerun passed
  `1/1`.
- Scoped/client diff checks, documentation/context/preflight regression, link
  check and JSON validation: `PASS`.

Machine evidence:
`evidence/008H-client-product-facts-adoption/008H-client-product-facts-adoption.json`.

## Ledger decision

- `REL/CONTRACT-001`: `I2 -> I3`, `LOCALLY_PROVED`.
- `FE/P12-024` and `ADOPT/ADOPT-07` remain `I2`: their exact-candidate and
  wider whole-product/device acceptance criteria are not collapsed into this
  one source-contract proof.

Current distribution: `I3=278`, `I2=34`, `I1=45`, `I0=20`; `99` rows remain
below `I3`. Stage split: `29/32/17/21`. Evidence ceiling is local `I3`; no
candidate, signing, deployment, payment, campaign, publication or promotion
occurred.

## Rollback

Revert the generated Dart file, runtime import/consumers, digest pins, read-only
sync gate and both owner-document additions as one unit. Do not replace them
with hand-maintained client constants or let generated facts override server
commercial responses.
