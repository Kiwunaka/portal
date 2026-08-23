# WO-007G — Admin domain slices

Status: `COMPLETE_PARTIAL_ARCHITECTURE_PROOF`
Classification: `ACTIVE_EXECUTION`
Phase: `05`
Lane: platform modular-monolith composition
Depends on: `WO-007F`, current Operator Center/admin routes
Production/external actions: `NOT_AUTHORIZED`

## Bounded outcome

Repair the live composition-size regression without raising a ceiling and make
one meaningful domain split inside the existing FastAPI modular monolith. Keep
one process, one route table, one database authority and the legacy `api.*`
surface.

This WO does not claim all of `REL/ARCH-002`: the public slice and the focused
but still large action-intent service remain explicit inventory.

## Implemented split

The pre-change architecture guard failed because `api_admin_routes.py` had
grown to `7,237` lines against its `7,100` ceiling. The limit was not raised.

- `api_admin_routes.py` now retains ordinary admin transport/read-model work and
  is `4,336` lines.
- `api_admin_action_routes.py` owns the contiguous guarded action-intent policy
  adaptation, DB/external orchestration, compatibility response shaping and
  prepare/status bindings (`2,774` lines).
- `api_admin_network_routes.py` owns emergency-network stage/promote/disable/
  rollback and node disable/resync HTTP bindings (`153` lines).
- `api.py` loads base admin, guarded action and guarded network slices in that
  exact order before subscriptions. `module_slices.py` keeps re-export and
  legacy patch mirroring; no auto-discovery or second runtime was added.
- Static contracts require every guarded mutation in both new files to remain
  covered by the action-policy registry, assert route ownership/non-duplication
  and cap the remaining `8,365`-line action-intent service at `8,500` until its
  later bounded split.
- Canonical system/module documentation names all eleven ordered API slices and
  current size evidence.

## Verification — 2026-08-22

- Initial size guard: `FAIL`, `api_admin_routes.py 7,237 > 7,100`; retained as
  the defect that triggered this WO.
- Composition size/order/re-export regression after the split: `4/4 PASS`.
- Exact action-intent/emergency/network/route-gap matrix: `33/33 PASS`.
- Mutation policy, emergency probe and Operator Center manifest matrix:
  `16/16 PASS` after adding both new route files to mutation discovery.
- Router-required backend/API matrix: `154 passed + 8 subtests passed` in
  `637.61s`.
- Imported FastAPI table: `300` unique method/path pairs, zero duplicates.
- Changed Python compilation, focused lint/format checks and scoped diff check:
  `PASS`.

Machine evidence:
`evidence/007G-admin-domain-slices/007G-admin-domain-slices.json`.

## Ledger decision

`REL/ARCH-002` remains `I2`, now with stronger implemented and locally tested
admin/action composition evidence. The row cannot honestly reach `I3` while the
remaining large public/action-service inventory has no completed bounded
decision. Distribution and stage split stay `278/34/45/20` and
`29/32/17/21`.

No candidate, deployment, server mutation, payment, publication or promotion
occurred.

## Rollback

Recombine the two new files after the base admin slice and remove their ordered
loader/test/doc entries as one unit. Do not keep duplicate decorators or raise
the former size limit as rollback.
