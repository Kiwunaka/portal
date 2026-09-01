# WO-013ED — candidate.20 offline Gates A–E replay

Status: `PASS_EXACT_SOURCE_AND_LOCAL_QUALITY; GATES_A_E_BLOCKED_ON_LIVE_BOUNDARIES`

Observed: `2026-09-01`

Production/public mutation: `NONE`

## Outcome

Replay the source-owned parts of release Gates A–E against the exact immutable
candidate 20 tuple without using the host VPN, routes or DNS and without
starting the VM, LDPlayer or phone. The exact platform, client and Core source
trees remain clean at `d6898e6...`, `8ab9815...` and `cd8f0f4...`.

Gate B passes its comparable focused matrices at `70/70` platform and `111/111`
client tests. Gate D passes the complete payment/provider/callback/HTTP/DB/
outbox/module matrix at `196/196 + 12 subtests` and the Action Intent/policy
matrix at `25/25`. These are local fixture tests: no real payment, provider,
customer, production database, outbox worker or Operator mutation ran.

The complete local-quality gate passes all `15/15` steps on the declared Node
`22.14.0` toolchain. This includes Flutter analyze, `413/413` client tests,
cross-repository/version/logging/rollback contracts, webapp lint and build,
cabinet Playwright `69/69`, marketing build/SEO/responsive/reduced-motion,
adminapp build and static performance `9/9`.

All five Gates A–E remain `BLOCKED`. This replay finds zero explicit source
failures and does not require candidate replacement, but it does not replace
physical Android, remaining Windows recovery/protocol, live provider/
PostgreSQL/outbox/Operator, authenticated origin, accessibility/device,
comparable performance or post-promotion proof.

## Environment failure chain

The fail-first history is retained instead of being relabeled:

1. The first gate attempt failed because exact source worktrees intentionally
   lacked materialized frontend dependencies.
2. Offline `npm ci` succeeded for webapp, marketing and adminapp with zero
   reported vulnerabilities. The next attempt passed every non-browser step
   but could not launch the required Playwright Chromium revision `1228`.
3. After installing that exact browser revision, the full matrix passed on
   host Node `24.15.0`. Because the three frontend projects declare
   `22.14.x`, this is retained only as diagnostic evidence.
4. The authoritative replay prepended the existing portable Node `22.14.0`
   only to the child process PATH and passed `15/15`. System PATH and the host
   Node installation were not changed.

The browser ran headless. No interactive window, mouse/keyboard control or
host network configuration was used.

## Gate decisions

- Gate A: `BLOCKED/I1`. WO-013EA signed supply and Windows default-path proof,
  WO-013EB STOP-SHIP/source controls and WO-013EC artifact privacy remain
  current. Branch policy, trusted Windows signing, physical Android and the
  final live aggregate remain non-PASS.
- Gate B: `BLOCKED/I3`. Exact source `70/70 + 111/111` passes; exact connected
  recovery and remaining physical false-green/device boundaries stay open.
- Gate C: `BLOCKED/I3`. Local source/platform contracts pass and WO-013EA's
  Windows 11 default slice remains valid. Candidate 20 physical Android,
  Windows 10/non-default/recovery and Store delivery stay open.
- Gate D: `BLOCKED/I3`. Exact source `196/196 + 12` and `25/25` passes.
  Production provider callback, PostgreSQL locking/load, outbox delivery/
  reconciliation/reversal and real Operator rollback stay open.
- Gate E: `BLOCKED/I3`. Exact local quality `15/15`, cabinet `69/69`, client
  `413/413` and static performance `9/9` pass. Authenticated journeys,
  physical accessibility/OEM/scaling, comparable device/browser performance,
  support, named RU-origin and post-promotion proof stay open.

Gate F is deliberately not regenerated. Candidate 20 Android installed
identity is still required before guarded rollback rehearsal, and the final
aggregate should not be produced while that boundary remains absent.

## Ledger effect

Gate B, Gate D, Gate E, `DOD-03`, `DOD-08`, `DOD-11`, `DOD-13` and `DOD-14`
gain current candidate source evidence without level promotion. Gate A and
Gate C retain their current candidate 20 evidence and levels. Distribution
remains `I4=7`, `I3=320`, `I2=19`, `I1=32`, `I0=0` across `378` unique rows.

No public asset, Store object, tag, stable pointer or production deployment is
created.

## Commands and results

- Gate B platform focused matrix: `70/70 PASS` in `0.60 s`;
- Gate B client focused matrix: `111/111 PASS`;
- Gate D payment/HTTP/DB/outbox/module matrix:
  `196/196 + 12 subtests PASS` in `1013.39 s`, with `20` retained deprecation
  warnings;
- Gate D Action Intent/policy matrix: `25/25 PASS` in `94.45 s`;
- declared-toolchain local quality: `15/15 PASS` under Node `22.14.0` and npm
  `10.9.2`;
- client widget suite: `413/413 PASS`;
- cabinet Playwright suite: `69/69 PASS` with Playwright `1.61.1` and Chromium
  revision `1228`;
- static performance: `9/9 PASS`.

## Evidence

- normalized record:
  `evidence/013ED-candidate20-gates-a-e/013ED-candidate20-gates-a-e.json`;
- normalized record SHA-256:
  `efe4c1f435af8cd9682f6ad94aefb26f89e12440e00838fed3fdf502acf77818`;
- authoritative local-quality report SHA-256:
  `1bbe6d799d020b1ac483422a7acac80421a34bf38592c52a0900add0846508be`;
- static-performance evidence SHA-256:
  `04429a425ab2eda8b4aa0a4eff27544d4f839b54a6de2e51aef14502e159c2e2`;
- static-performance gate SHA-256:
  `c3d3ce72eed6d8e5e4b7d881efe7a62148619b51b80464c7395f2319cdb888c1`;
- fail-first missing-dependency report SHA-256:
  `47b2c64aa7c37909dfca07b6811bc435f06e346214d8bc87a34c1d59ecf800b9`;
- missing-browser report SHA-256:
  `1821422982e7307dab26d3ce7b938fb83f2184e63da8bf4eb35ea906e2f5bec2`;
- diagnostic Node 24 pass report SHA-256:
  `58fafdd3c18e543b7ed5fdd408fdd2c36ae5560d674b47e6b439dde8e84ef6a6`.

The private reports remain under
`E:/POKROV-tools/temp/candidate20-offline-gates/`; the normalized record
contains no credential, raw customer/provider payload or connection material.
