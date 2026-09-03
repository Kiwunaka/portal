# WO-013FE — candidate.24 source Gates A–E and isolated rollback

Status: `PASS_EXACT_SOURCE_LOCAL_QUALITY_AND_ISOLATED_ROLLBACK; GATES_A_E_BLOCKED_ON_LIVE_BOUNDARIES`

Observed: `2026-09-03T00:57:48Z`–`2026-09-03T01:13:40Z`

Production/public mutation: `NONE`

## Outcome

Replay the source-owned portions of release Gates A–E against exact signed
candidate.24 and execute its real portal/client pointer mechanisms in an
isolated disposable fixture. No host VPN, route, DNS, VM, emulator, phone,
runtime pointer, provider, database, Operator, public asset or stable state is
changed.

Gate B passes `70/70` platform plus `111/111` client tests. Gate D passes the
payment/provider/callback/HTTP/DB/outbox/module matrix at `196/196 + 12
subtests` and Action Intent/policy at `25/25`. Declared Node `22.14.0` local
quality passes `15/15`, including client `413/413`, cabinet Playwright `69/69`,
web/admin/marketing builds, responsive/reduced-motion and static performance
`9/9`.

The signed manifest, receipt, detached signature and all four source revisions
validate before the disposable sequence:

```text
1.1.6+20260819 -> pokrov-1.2.0 candidate.24 -> 1.1.6+20260819
```

Portal state and the stable handoff restore byte-identically, receipts
validate, unrelated state survives and the temporary source snapshots are
removed. Focused rollback/PB-14 tests pass `16/16`.

## Dependency audit boundary

Fresh npm audit reports zero findings for adminapp and marketing. Webapp
reports one `moderate` finding in transitive `@humanfs/node 0.16.7` through
the root development-only ESLint `9.39.4` chain. `npm ls --omit=dev`, bounded
application-source search, static export search and candidate SBOM search find
no runtime inclusion. It is retained as a development-lock patch action, not
hidden and not mislabeled as distributed-client exposure.

## Gate decisions

- Gate A: `BLOCKED/I1`. Signed supply, exact STOP-SHIP source regressions,
  solo controls and hosted checks pass. Owner-skipped Windows signing, branch
  enforcement, physical Android, the dev-lock patch and final live aggregate
  remain non-PASS.
- Gate B: `BLOCKED/I3`. Exact source passes `70/70 + 111/111 + 413/413`.
  Installed candidate.24 Windows recovery plus remaining physical false-green
  and device boundaries stay open.
- Gate C: `BLOCKED/I3`. Exact source/contracts, signed packages and native
  tests pass. Candidate.24 installed Windows and Android, packaged AWG/Smart
  DNS, Windows 10/non-default lifecycle and Store delivery remain open.
- Gate D: `BLOCKED/I3`. Exact source passes `196/196 + 12` and `25/25`, while
  WO-013FD binds Brain source/readiness/delivery. Production provider,
  PostgreSQL locking/load, outbox delivery/reconciliation/reversal and real
  Operator rollback remain open.
- Gate E: `BLOCKED/I3`. Exact quality `15/15`, cabinet `69/69`, client
  `413/413`, static performance `9/9` and current-public API budgets pass.
  Authenticated journeys, physical accessibility/OEM/scaling, comparable
  artifact/device/browser performance, support, general RU-origin and
  post-promotion evidence remain open.

## Evidence and ceiling

- normalized record:
  `evidence/013FE-candidate24-source-gates-and-local-rollback/013FE-candidate24-source-gates-and-local-rollback.json`;
- rollback report:
  `E:/POKROV-tools/release-candidates/pokrov-1.2.0-candidate.24/rollback/candidate24-rollback-rehearsal.json`;
- quality and audit root:
  `E:/POKROV-tools/temp/candidate24-release-refresh`.

`REL_DOD/DOD-18` and `FE/P12-130` remain `I3` with candidate.24 replacement
evidence. Gates A–E remain blocked with zero new source failures. A guarded
runtime pointer/kill rollback and all named live/device boundaries still
require separate proof. No index level changes and no Gate G authorization.
