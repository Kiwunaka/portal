# WO-009J — Operator OIDC identity and step-up

Status: `COMPLETE_LOCAL_I3`
Phase: `07` (source ledger row `P07`)
Row advanced: `OC/OC-100`
Promotion: `NOT_REQUESTED`

## Outcome

Replace compatibility-first Operator Center entry with a purpose-bound
Telegram OIDC Authorization Code plus PKCE contract. Keep all session secrets
out of browser storage, refuse implicit operator creation or role grants, and
use the same verified identity for step-up while retaining a measurable,
explicitly disableable Mini App compatibility path.

## Implemented boundary

- `/api/admin/v2/auth/oidc/start` creates separate login and step-up
  transactions. The public signed state contains no PKCE verifier. A matching
  private transaction, including the verifier, is stored only in the
  short-lived `__Host-pokrov_admin_oidc` Secure/HttpOnly/SameSite=Strict
  cookie and signed with `ADMIN_OPERATOR_SESSION_SECRET`.
- `/api/admin/v2/auth/oidc/finish` requires the public state, private cookie,
  exact purpose, nonce and redirect to agree before provider exchange. Login
  and step-up states cannot be substituted for each other.
- Verified Telegram identity is mapped only to a preprovisioned active
  operator with an active role assignment in the exact environment. OIDC
  login never auto-creates an operator and never auto-grants superadmin or any
  other role.
- Successful login issues the existing opaque HMAC-hashed
  `__Host-pokrov_admin_session` cookie. Existing CSRF, idle and absolute
  expiry, `/session/me`, inventory/revoke, logout/Clear-Site-Data and audit
  boundaries remain authoritative.
- Step-up verifies the same Telegram identity as the active session and marks
  only that session. High-risk dialogs can initiate the OIDC step-up and
  return through the same callback boundary.
- AdminApp removes `code` and `state` from the visible URL before exchange,
  rejects a non-Telegram authorization origin and offers Mini App bootstrap
  only when live `initData` is actually present.
- `ADMIN_OPERATOR_LEGACY_BOOTSTRAP_ENABLED=false` rejects both the legacy
  bootstrap and compatibility empty-body step-up. The default remains enabled
  only for measured migration; exact-candidate cutover must disable it after
  real operators are provisioned.
- Deterministic OpenAPI and generated TypeScript cover 75 operations,
  including the dedicated OIDC transaction cookie security scheme.

## Index decision

`OC/OC-100` advances `I2 -> I3`. The pre-existing session owner already
provided opaque HttpOnly cookies, CSRF, idle/absolute expiry,
inventory/revoke/logout and backend authorization. This package closes the
remaining local primary identity and external step-up contract without
claiming live-provider or exact-candidate execution.

Distribution becomes `I3=302`, `I2=20`, `I1=40`, `I0=15`; `75` rows remain
below `I3`. Stage split becomes `4/33/17/21`.

## Local proof

- Backend identity, session, OpenAPI and Operator Center manifest matrix:
  `64/64` PASS.
- OIDC cases prove verifier privacy, dedicated signer use, cookie/state
  binding, preprovision-only login, same-identity step-up, audit records and
  fail-closed legacy disablement.
- OpenAPI and TypeScript generation: PASS, 75 operations, semantic digest
  `beebbea12e3c5168d0bb54cd96e752aeebf7768df15f5194d5f22bb94669531c`.
- AdminApp lint and production build: PASS, 30 static pages.
- Full AdminApp Playwright matrix: `78/78` PASS, including explicit
  compatibility entry and OIDC callback URL cleanup.
- Documentation and candidate-preflight contracts: `37/37` PASS; platform
  context audit: PASS. Read-only preflight remains expected `BLOCKED` with
  seven blockers, no candidate and exact pending split `4/33/17/21`.
- Targeted diff check: PASS with Windows line-ending warnings only.
- Scoped secret scan: PASS, zero matching files.

Machine evidence:
`evidence/009J-operator-oidc/009J-operator-oidc.json`.

## Evidence ceiling

This is local source/test/build evidence from a dirty development worktree.
BotFather was not changed, no live provider exchange or passkey ceremony ran,
no real operator was migrated, and the legacy flag remains enabled by default.
No exact candidate, hosted clean check, deployment, server mutation,
publication or promotion occurred. `OC/OC-100` still requires exact-candidate
authenticated login, step-up, session inventory, logout, audit readback and
legacy-off proof before `I4`.
