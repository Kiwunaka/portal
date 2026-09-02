# WO-013EO — frontend build-lock refresh after candidate.21 audit

Status: `PASS_ACTIVE_DEVELOPMENT_LOCKS_PATCHED; CANDIDATE21_IMMUTABLE`

Observed: `2026-09-02`

Production/public mutation: `NONE`

## Outcome

Close the active development-line dependency action recorded by WO-013EN
without rewriting signed candidate.21. Only `adminapp/package-lock.json` and
`marketing/package-lock.json` change. Both transitive development paths now
resolve `browserslist` `4.28.8`, above the first patched `4.28.7`; no direct
dependency or production dependency is added and both package manifests remain
byte-identical.

Fresh Node `22.14.0` / npm `10.9.2` materialization reports zero audit findings
for both surfaces. Adminapp lint, its `75/75` API/SDK contract and production
build pass. Marketing lint, production build and its 30 export-segment copies
pass. The focused dependency/local-quality/admin/marketing contract suite
passes `28/28`.

WO-013EN remains immutable evidence that the signed candidate.21 source locks
contained `browserslist` `4.28.4` in these two build-development paths. This
patch changes only the successor development line. Candidate.21 bytes,
manifest, SBOM, provenance and Gate results do not change; a successor
candidate must be built and signed before the refreshed locks can receive
candidate credit.

## Diff and validation

- changed tracked files: exactly two package locks;
- `adminapp/package-lock.json`: `d36f87f... -> ce55397a...`;
- `marketing/package-lock.json`: `30779360... -> b7545ef3...`;
- `browserslist`: `4.28.4 -> 4.28.8` on both surfaces;
- `npm ci --ignore-scripts`: PASS on both surfaces;
- `npm run lint`: PASS on both surfaces;
- `npm run build`: PASS on both surfaces;
- `npm audit --omit=optional`: zero total/high/critical on both surfaces;
- focused platform suite: `28/28 PASS` in `0.94 s`.

The lock resolver also refreshes only the target package's compatible browser
data helpers. The admin lock receives npm's `dev: true` metadata normalization
for optional `fsevents`; no shipped source or runtime behavior changes.

## Ledger effect

`DEP-001` keeps `I4`: candidate.21 supply provenance remains intact while the
active development-line audit action becomes locally closed. Gate A and Gate E
remain at `I1` and `I3`; their device, signing, branch-policy, authenticated
journey and final-live boundaries are untouched. Distribution remains
`I4=7`, `I3=320`, `I2=19`, `I1=32`, `I0=0` across `378` unique rows.

No runtime, host network, VM, phone, provider, database, Operator, public asset,
Store object, tag or stable pointer is changed. Gate F remains `NOT_RUN` and
Gate G remains unauthorized.

## Evidence

- normalized record:
  `evidence/013EO-frontend-build-lock-refresh/013EO-frontend-build-lock-refresh.json`;
- normalized record SHA-256:
  `e6ee83226493fb9d7f53b15ecc7b05eb893f60d487a4b41e33b1f9d1199fe88e`;
- source audit record SHA-256:
  `8db74c8dd946c38dd0ba8921bd47598f0fc55f784e8d70462a1dcb4d1ff84653`.

The normalized record contains no credential, raw customer/provider payload or
connection material.
