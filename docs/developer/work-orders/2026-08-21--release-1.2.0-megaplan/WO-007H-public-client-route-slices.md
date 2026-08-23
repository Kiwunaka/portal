# WO-007H — Public and managed-client route slices

Status: `COMPLETE_PARTIAL_ARCHITECTURE_PROOF`
Classification: `ACTIVE_EXECUTION`
Phase: `05`
Lane: platform modular-monolith composition
Depends on: `WO-007G`, current public/client API routes
Production/external actions: `NOT_AUTHORIZED`

## Bounded outcome

Reduce the remaining oversized public route slice by separating stable public,
authentication and session-bootstrap transport from managed client feature and
runtime transport. Preserve one FastAPI process, one ordered route table, one
database authority and the legacy `api.*` compatibility surface.

This WO does not close all of `REL/ARCH-002`. The bounded but still
`8,365`-line `admin_action_intent_service.py` remains explicit architecture
inventory before a broad local `I3` claim.

## Implemented split

- The former `5,822`-line `api_public_routes.py` is now a `2,019`-line public
  bootstrap slice. It owns health, emergency/public catalog, authentication,
  client session/recovery bootstrap and route-policy transport.
- New `api_client_routes.py` is `3,980` lines. It owns managed client
  locations, subscription, devices, notifications, profile, node, runtime,
  WARP and Telegram transport, public promo-media delivery and the retained RUB
  compatibility use-case helpers.
- `api.py` remains the `9,594`-line composition root and loads the public slice
  immediately before the client slice. Commercial offer, payment,
  observability, surface, admin and subscription ordering is unchanged. The
  complete list now contains twelve explicit slices; there is no discovery or
  second router/runtime.
- Payment-return DB session ownership moved beside the other retained
  compatibility payment use-case helpers. `api_payment_routes.py` remains a
  transport-only `381`-line slice with no direct `SessionLocal` lifecycle.
- Architecture tests pin both size ceilings, exact slice order, representative
  route ownership and payment/mutation discovery across the new file.
- Canonical system and backend module maps name the new boundary and current
  source sizes.

## Reload defect found and fixed

The broad mixed-import regression exposed a real compatibility-loader defect.
Pytest fixtures can restore an older `api` module object after a newer object
with the same name has populated the slice registry. The loader previously
removed old owner exports only when their function identity matched the latest
registered slice. A restored function therefore survived into
`bootstrap_slice`, was marked inherited, and the freshly defined replacement
silently stopped being an owned export. On the next clean owner replacement,
`_synthetic_transport_node` disappeared from `api`.

`module_slices.py` now clears every registered export from the owner by the
recorded ownership set, independent of object identity. It also clears the
union of the current slice metadata and the registered prior-instance metadata
before reload. Stale-owner monkeypatch cleanup still cannot mutate the current
registry. A focused regression restores an old owner, reloads its slice and
then performs one more clean owner replacement; the export must remain owned
and callable through the composition root.

## Verification — 2026-08-22

- Public/client size, order, ownership and module-runtime regression: `PASS`.
- Payment DB/HTTP/bounded-context, module and mutation-policy focus: `25/25
  PASS`.
- Full network-rollout plus module regression after the final loader fix:
  `16/16 PASS`.
- Exact mixed nine-file API matrix in one process: `234 passed`, `12 subtests
  passed`, exit `0` in `959.26s`. This is the same sequence that previously
  exposed the stale-owner failure.
- Imported FastAPI table: `300` unique method/path pairs, zero duplicates.
- Changed Python compilation, focused Ruff format/check and scoped source checks:
  `PASS`.

Noncanonical diagnostics are retained rather than rewritten as passes:

- the first broad run exposed eight late network failures plus one stale source
  assertion (`225 passed`, `12 subtests passed`, `9 failed`);
- after the first stale-slice cleanup and source correction, the exact mixed run
  still failed eight network cases (`226 passed`, `12 subtests passed`,
  `8 failed` in `963.15s`), which isolated restored owner identity as the
  remaining cause;
- an exploratory broad Ruff format/check against legacy `api.py` exposed
  existing whole-file debt and was not used as a release gate. Its formatting
  noise was not retained; semantic dirty changes were preserved and the final
  file compiles and passes the affected regression matrix.

Machine evidence:
`evidence/007H-public-client-route-slices/007H-public-client-route-slices.json`.

## Ledger decision

`REL/ARCH-002` remains `I2`, with stronger implemented and locally verified
route-composition evidence. It cannot honestly advance while the remaining
action-intent service has no bounded owner split. Distribution remains
`I3=279`, `I2=33`, `I1=45`, `I0=20`; 98 of 377 rows remain below `I3`. The
below-I3 stage split remains `28/32/17/21` for
pre-freeze/candidate/external/deferred, including three external
pre-candidate blockers.

No candidate, deployment, server mutation, payment, signing, publication or
promotion occurred.

## Rollback

Recombine `api_client_routes.py` into the public slice at the same registration
position and remove the added loader/test/doc entries as one unit. Do not leave
duplicate decorators, revert the ownership-based reload fix independently, or
raise the public-slice ceiling as rollback.
