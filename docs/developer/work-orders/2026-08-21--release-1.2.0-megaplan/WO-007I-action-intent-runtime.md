# WO-007I — Action Intent domain/runtime boundary

Status: `COMPLETE_LOCAL_ARCHITECTURE_PROOF`
Classification: `ACTIVE_EXECUTION`
Phase: `05`
Lane: platform modular-monolith guarded mutation boundary
Depends on: `WO-007H`, current Operator Center Action Intent policies
Production/external actions: `NOT_AUTHORIZED`

## Outcome

Close the last declared `REL/ARCH-002` local inventory by separating domain
policy from generic persistence/execution mechanics without creating a second
policy registry, backend, route table, database authority or compatibility
surface.

## Implemented boundary

- `admin_action_intent_service.py` is now `6,488` lines. It owns domain payload
  normalizers, entity state builders, previews, challenges, audit projections
  and the only `ACTION_POLICIES`/`ACTION_POLICY_ROUTES` registries.
- New `admin_action_intent_runtime.py` is `2,034` lines. It owns generic UUID
  and target validation, confirmation hashing, intent persistence/status,
  version snapshots, write/overlap locks, idempotency, replay, external timeout,
  uncertain-state reconciliation, bounded result normalization and terminal
  audit finalization.
- The runtime accepts `Mapping[str, ActionPolicy]` explicitly in its policy
  lookup, prepare, validation and execute entrypoints. It does not import the
  domain service, declare `ACTION_POLICIES`, register HTTP routes or discover
  policies dynamically.
- Thin wrappers in the domain service pass the exact live registry and preserve
  the established `ActionIntentError`, confirmation/fingerprint helpers and
  prepare/execute/status imports used by the FastAPI composition root,
  Operator Center v2, jobs and tests.
- The constant-time confirmation comparator remains injected by the wrapper,
  preserving the existing observable security regression without runtime
  monkeypatch coupling.
- Architecture ceilings are reduced from one `8,500`-line inventory guard to
  `7,000` lines for domain policy and `2,300` for generic runtime. A source
  contract rejects a second registry, a runtime-to-domain circular import or
  removal of explicit policy injection.

## Verification — 2026-08-22

- Domain Action Intent, policy coverage and architecture contract: `33/33
  PASS` in `83.41s`.
- Emergency catalog, Operator Network, backend route gaps, release actions,
  support work and full admin/Operator Center API regression: `68/68 PASS` in
  `255.58s`.
- Operator Center manifest and Core/catalog/endpoint/Linux emergency probe
  contracts: `32/32 PASS` in `18.01s`.
- Independent FastAPI import: twelve slices, `300` unique method/path pairs,
  zero duplicates.
- Both changed Python modules compile. Full Ruff passes on the new runtime and
  architecture test; focused unused-import lint passes on the retained legacy
  domain service. Scoped diff check: `PASS`.

Machine evidence:
`evidence/007I-action-intent-runtime/007I-action-intent-runtime.json`.

## Ledger decision

`REL/ARCH-002` advances `I2 -> I3`. The explicitly declared public/admin/action
inventory is now split into bounded owners with current local behavioral and
source proof. This is not exact-candidate or deployed proof: production load,
PostgreSQL lock behavior, operator action execution and rollback remain `I4`
gates.

Distribution becomes `I3=280`, `I2=32`, `I1=45`, `I0=20`; 97 of 377 rows
remain below `I3`. The below-I3 stage split becomes `27/32/17/21` for
pre-freeze/candidate/external/deferred, including three external
pre-candidate blockers.

No candidate, deployment, server mutation, operator production action,
payment, signing, publication or promotion occurred.

## Rollback

Move the generic runtime definitions back into the domain service and remove
the wrapper/import/test/doc entries as one unit. Do not retain a second policy
mapping, duplicate execution code or a runtime import cycle as rollback.
