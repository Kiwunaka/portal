# WO-009H — Generated Admin API v2 contract and runtime boundary

Status: `COMPLETE_LOCAL_I3`
Phase: `07` (source ledger row `P07`)
Row advanced: `OC/OC-120`
Promotion: `NOT_REQUESTED`

## Outcome

Close the remaining local Admin API v2 contract gap without creating a second
API authority or expanding the legacy compatibility surface. The live modular
FastAPI router must generate one deterministic OpenAPI artifact, the AdminApp
must consume a generated TypeScript operation table, and contract drift must
fail both the clean build and the browser runtime boundary.

## Implemented contract

- `AdminV2ContractRouter` applies one strict Pydantic success envelope and the
  common structured errors to every JSON v2 endpoint. Unexpected top-level
  response fields fail validation. The governance CSV export and encrypted
  support-attachment download are the only explicit binary exceptions.
- The deterministic OpenAPI generator imports the composed application,
  includes only `/api/admin/v2/*`, requires exact coverage of the canonical
  `ROUTE_PERMISSIONS` matrix, rejects duplicate or unstable operation IDs and
  retains only referenced schemas. Every operation records permission,
  cookie-session security and CSRF metadata.
- The checked-in contract contains 73 unique operations: 71 JSON envelopes and
  two binary responses. Query list limits are bounded to at most 1000; payment
  and FREE-archive offsets are bounded to `0..100000`.
- The dependency-free TypeScript generator emits exact operation method/path,
  path/query/body types, response kind, permission and CSRF requirements. Its
  exact generation check runs with `npm run check:sdk`, and AdminApp `prebuild`
  requires that check before compilation.
- The browser client rejects any v2 method/path absent from the generated table
  with `admin_v2_contract_mismatch`. It rejects a successful JSON response
  whose top-level keys or meta do not match the generated envelope with
  `admin_v2_envelope_invalid`, before a feature can display the payload.
- Legacy `/api/admin/*` reads remain outside the generated v2 contract. The
  package does not add a legacy capability, alternate auth flow, new service or
  network boundary.

## Index decision

`OC/OC-120` advances `I2 -> I3`. Stable domain read/action models were already
migrated in `WO-009D..009F4`; this package adds the missing generated OpenAPI,
generated TypeScript consumer, exact permission/CSRF coverage, response
validation, bounded offset checks and fail-closed runtime drift behavior.

## Local proof

- Deterministic OpenAPI generation/check and TypeScript SDK generation/check:
  PASS; contract semantic digest
  `5177721e0c8dad91d8196fa35416b751639101bb0688ce0d8f841c1d0889812d`.
- Full Admin API/contract/command-center backend matrix: `59/59` PASS.
- AdminApp lint and production build: PASS; the build regenerated 30 static
  pages and required the SDK clean check through `prebuild`.
- Full AdminApp Playwright matrix: `76/76` PASS. The retained negative scenario
  proves that malformed HTTP 200 v2 data is rejected and cannot produce a
  false healthy state.
- Relevant Python modules compile; both generator `--check` modes pass.
- Regenerated candidate preflight remains expected `BLOCKED`, with
  `candidate_created=false`; distribution becomes `I3=292`, `I2=27`,
  `I1=41`, `I0=17`, and below-I3 stage split is `15/32/17/21`.

Machine evidence:
`evidence/009H-admin-v2-generated-contract/009H-admin-v2-generated-contract.json`.

## Evidence ceiling

This is local source/test/build evidence from a dirty development worktree. No
clean hosted check, frozen revision, published exact-candidate schema, SDK
package publication, authenticated staging/production readback, deployment,
server mutation or promotion occurred. `OC/OC-120` requires those retained
candidate/runtime facts before `I4`.
