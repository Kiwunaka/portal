# Admin API v2 generated contract

`admin-v2.openapi.json` is the checked-in, deterministic contract for the
platform-owned `/api/admin/v2/*` surface. It is generated from the imported
FastAPI application and the canonical `ROUTE_PERMISSIONS` matrix; it is not a
hand-maintained description of the API.

The artifact contains only the Admin API v2 paths and their referenced
schemas. Every operation has a stable method/path-derived `operationId`, an
exact permission, session-cookie security metadata and an explicit CSRF flag.
JSON success responses use the exact `data/meta/sources/warnings` envelope.
The audit CSV and encrypted support attachment responses are declared as
binary and are not passed through the JSON envelope.

Regenerate and verify from the repository root:

```powershell
python scripts/generate_admin_v2_openapi.py
node adminapp/scripts/generate-admin-v2-sdk.mjs
python scripts/generate_admin_v2_openapi.py --check
node adminapp/scripts/generate-admin-v2-sdk.mjs --check
```

The TypeScript consumer is generated at
`adminapp/src/lib/admin-api/generated/admin-v2.ts`. `npm run check:sdk` checks
both artifacts, and `npm run build` runs that check before compiling the UI.
The browser client also matches every v2 method/path against the generated
table and rejects a malformed success envelope before returning data to a
feature.

Local generation, tests and builds are source evidence only. Publication of
this exact schema with an exact candidate, authenticated staging readback and
hosted clean-check evidence remain release gates.
