# WO-013EN — candidate.21 offline Gates A–E replay and build-dependency audit

Status: `PASS_EXACT_SOURCE_AND_LOCAL_QUALITY; GATES_A_E_BLOCKED_ON_LIVE_BOUNDARIES; BUILD_DEPENDENCY_PATCH_RECOMMENDED`

Observed: `2026-09-02`

Production/public mutation: `NONE`

## Outcome

Replay the source-owned parts of release Gates A–E against the exact signed
candidate.21 tuple without changing the host VPN, routes or DNS and without
using the VM, LDPlayer or phone. The platform, client, Core and release-index
trees remain clean at `e260813...`, `1e16458...`, `cd8f0f4...` and
`cae911e...`. Manifest `ce0b8586...`, signature `ef474e6e...` and receipt
`aaa027cc...` keep the replay tied to `pokrov-1.2.0-candidate.21` build 4050.

Gate B passes its focused matrices at `70/70` platform and `111/111` client
tests. Gate D passes the complete payment/provider/callback/HTTP/DB/outbox/
module matrix at `196/196 + 12 subtests` and the Action Intent/policy matrix at
`25/25`. These are local fixture tests: no real payment, provider, customer,
production database, outbox worker or Operator mutation ran.

The declared Node `22.14.0` local-quality gate passes all `15/15` steps. It
includes Flutter analyze, `413/413` client tests, cross-repository/version/
logging/rollback contracts, webapp lint/build, cabinet Playwright `69/69`,
marketing build/SEO/responsive/reduced-motion, the 75-operation admin API/SDK
contract and admin build. Static performance passes `9/9`.

A separate fresh dependency audit is deliberately not hidden behind the
functional PASS. Webapp reports zero findings and resolves `browserslist`
`4.28.8`. Adminapp and marketing each report one high finding for their same
transitive development-only `browserslist` `4.28.4` lock path. The two
2026-09-01 advisories affect versions through `4.28.6`; `4.28.7` is the first
patched release. The package is reached through `eslint-config-next`, has no
application-source import, is absent from both static exports and the
candidate SBOM, and is not an Android/Windows distributed component. No
distributed-runtime exposure is observed, so this does not retroactively
rewrite immutable candidate.21 or turn the functional gate into a failure.
The warning remains real and both active development locks require a separate
patch before the next candidate.

All five Gates A–E remain `BLOCKED`. The replay finds zero explicit source
failures, but it does not replace physical Android, remaining Windows
recovery/protocol, live provider/PostgreSQL/outbox/Operator, authenticated
origin, accessibility/device, comparable performance or post-promotion proof.

## Gate decisions

- Gate A: `BLOCKED/I1`. WO-013EI signed supply and WO-013EL current/Brain
  read-only evidence remain current. Two branch policies are access-blocked,
  Core main is accepted unprotected for the solo lane, trusted Windows signing
  and physical Android remain open, and the adminapp/marketing development
  locks require the recorded patch. The final live aggregate is non-PASS.
- Gate B: `BLOCKED/I3`. Exact candidate.21 source passes
  `70/70 + 111/111 + 413/413`; fresh in-place Windows service-restart recovery
  and remaining physical false-green/device boundaries stay open.
- Gate C: `BLOCKED/I3`. Local source/platform contracts and the existing
  Windows 11 default/upgrade slices pass. Physical Android, Windows 10/
  non-default/in-place lifecycle, packaged AWG, in-app Smart DNS and Store
  delivery stay open.
- Gate D: `BLOCKED/I3`. Exact source `196/196 + 12` and `25/25` passes; WO-013EL
  retains Brain source/readiness/delivery readback. Production provider
  callback, PostgreSQL locking/load, outbox delivery/reconciliation/reversal
  and real Operator rollback stay open.
- Gate E: `BLOCKED/I3`. Exact local quality `15/15`, cabinet `69/69`, client
  `413/413` and static performance `9/9` pass. WO-013EL retains current-public
  API budgets. Authenticated journeys, physical accessibility/OEM/scaling,
  comparable artifact/device/browser performance, support, general RU-origin
  and post-promotion evidence stay open.

Gate F is deliberately not generated while these manual/live boundaries
remain open. Gate G, public assets and stable promotion are unauthorized.

## Ledger effect

Gates B, D and E plus `DOD-03`, `DOD-08`, `DOD-11`, `DOD-13` and `DOD-14`
gain current candidate.21 local source evidence without level promotion. Gate
A records the build-dependency warning without converting it to a runtime
failure. Gate C retains current candidate.21 Windows plus local-quality
evidence. Distribution remains `I4=7`, `I3=320`, `I2=19`, `I1=32`, `I0=0`
across `378` unique rows.

No public asset, Store object, tag, stable pointer or production deployment is
created.

## Commands and results

- Gate B platform focused matrix: `70/70 PASS` in `0.75 s`;
- Gate B client focused matrix: `111/111 PASS` under Flutter `3.38.5` and Dart
  `3.10.4`;
- Gate D payment/HTTP/DB/outbox/module matrix:
  `196/196 + 12 subtests PASS` in `654.67 s`, with `20` retained deprecation
  warnings;
- Gate D Action Intent/policy matrix: `25/25 PASS` in `111.43 s`;
- declared-toolchain local quality: `15/15 PASS` under Node `22.14.0` and npm
  `10.9.2`;
- client widget suite: `413/413 PASS`;
- cabinet Playwright suite: `69/69 PASS`;
- static performance: `9/9 PASS`;
- dependency audit: webapp `0`; adminapp `1 high`; marketing `1 high`, where
  both high counts map to the same two development-lock advisories and one
  transitive package.

## Evidence

- normalized record:
  `evidence/013EN-candidate21-gates-a-e/013EN-candidate21-gates-a-e.json`;
- normalized record SHA-256:
  `fa50789c450fd4002823e00ef7768fecbe8ff4ad7f104158866f8a942c3ca773`;
- authoritative local-quality report SHA-256:
  `5b7b5d9ea0631ee53e78916b7a008f9f3f26d26a661aad0783a9a2cc3cb9a5fc`;
- static-performance evidence SHA-256:
  `4528e430ca5ed381535852705cdb536fed7003806cbbcee3d37ad43a955894ab`;
- static-performance gate SHA-256:
  `64fbce8fbedfe215fd59267cbaaed671411203d1e17af2eeb9d6d79b0c463f0d`;
- build-dependency audit SHA-256:
  `8db74c8dd946c38dd0ba8921bd47598f0fc55f784e8d70462a1dcb4d1ff84653`.

Private reports remain under
`E:/POKROV-tools/temp/candidate21-offline-gates/`. The normalized record
contains no credential, raw customer/provider payload or connection material.
