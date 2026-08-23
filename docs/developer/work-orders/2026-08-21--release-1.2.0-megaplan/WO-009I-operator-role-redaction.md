# WO-009I — Operator role usability and field redaction

Status: `COMPLETE_LOCAL_I3`
Phase: `07` (source ledger row `P07`)
Row advanced: `OC/OC-110`
Promotion: `NOT_REQUESTED`

## Outcome

Close the local RBAC usability gap without preserving the legacy superadmin
surface as a hidden back door. Domain operators receive the minimum legacy
read bridge needed by their workspace, sensitive fields are removed before
serialization and before sensitive database queries, and real high-risk
routes require both the domain permission and a fresh step-up session.

## Implemented boundary

- The retained `/api/admin/*` bridge uses the resolved FastAPI route template
  plus HTTP method. User list/card, investigation, typed search, promo-slot read
  and staged promo-media upload have explicit permissions. Every unlisted
  legacy route requires `legacy.admin.access` and therefore fails closed for
  domain roles.
- Legacy global search accepts only result domains visible to the current
  role. L1 support cannot search e-mail, linked identities, installation or
  device identifiers, key UUIDs or panel e-mail. Disallowed user, node, order
  and key queries are not executed.
- User list/card responses contain an explicit `field_access` map. Linked
  Telegram identity, install/device identity, application events, payment
  orders, administrator audit and legacy commands are independently governed.
  Redacted collections are not queried, and key-history operator identity is
  removed without the audit permission.
- The v2 user-360 projection requires an explicit diagnostics flag. L1 support
  receives the safe account/ticket projection and a `field_redacted` warning;
  installation, session, attempt, fingerprint and raw event queries are not
  executed without `support.sensitive.read`.
- AdminApp maps each field-access decision and renders a permission state
  instead of a false empty-data message. It hides legacy user commands and
  labels device/search limitations for a redacted role.
- Domain operator roles that own mutations have both `session.step_up` and
  `command.high_risk`. The action policy still also requires the matching
  domain write permission. Readonly, L1/L2 support and security-auditor roles
  cannot request high-risk execution.
- Promo-slot updates are classified as money actions, so payments operators
  can use the native money Action Intent boundary. Existing environment-scoped
  assignments, JIT expiry, break-glass expiry/reason and governance review
  remain the single retained role-governance authority.

## Index decision

`OC/OC-110` advances `I2 -> I3`. Static roles, environment-scoped assignments,
deny-by-default authorization and governance review were already implemented.
This package closes the remaining local field-redaction, retained-bridge,
domain-role usability and real high-risk route integration gaps. Production
identity, passkey/IdP step-up and exact-candidate assignment/readback remain
outside local proof.

## Local proof

- Full Admin API, generated-contract, command-center, support-work and manifest
  backend matrix: `75/75` PASS.
- Focused role/redaction/high-risk backend matrix: PASS, including L1 search
  side-channel rejection, query-suppressed diagnostics, network L3 step-up and
  payments L2 intent preparation.
- Deterministic OpenAPI check: PASS, 73 operations, semantic digest
  `5177721e0c8dad91d8196fa35416b751639101bb0688ce0d8f841c1d0889812d`.
- AdminApp lint and production build: PASS; 30 static pages generated and the
  SDK drift check ran through `prebuild`.
- Full AdminApp Playwright matrix: `77/77` PASS. A dedicated L1 browser case
  proves that redacted identity, diagnostics, money, audit and legacy actions
  are shown as permission states, not empty datasets.
- Documentation/preflight contract tests: `37/37` PASS. Regenerated candidate
  preflight remains expected `BLOCKED`, with `candidate_created=false`;
  distribution becomes `I3=293`, `I2=26`, `I1=41`, `I0=17`, and below-I3
  stage split is `14/32/17/21`.

Machine evidence:
`evidence/009I-operator-role-redaction/009I-operator-role-redaction.json`.

## Evidence ceiling

This is local source/test/build evidence from a dirty development worktree. No
production IdP/passkey challenge, real operator assignment/readback, external
step-up, clean hosted check, frozen exact candidate, deployment, server
mutation, publication or promotion occurred. `OC/OC-110` requires those
retained exact-candidate/runtime facts before `I4`.
