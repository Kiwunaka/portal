# WO-013FK — Windows CTest configuration correction

Status: `PASS_LOCAL_TEST_HARNESS_CORRECTION_HOSTED_BLOCKED_BY_BILLING`

Recorded: `2026-09-03T05:34:40Z`

Production/public mutation: `NONE`

## Outcome

Correct the false Release-native failure observed during WO-013FJ's fresh CLI
rehearsal. The service integration executable is intentionally Debug-only
because it launches the service through its Debug console/test-pipe entrypoint.
Its prior CMake declaration placed `CONFIGURATIONS Debug` through
`set_tests_properties`, but CMake 3.29 confirms that `CONFIGURATIONS` is an
`add_test` option, not a test property. CTest therefore ignored the intended
restriction and attempted the SCM service binary as a console process in
Release, yielding SCM code `1063`.

Client successor source now declares the restriction on `add_test`. A fresh
multi-configuration generation lists eight Debug tests including integration
and seven Release tests without it. Both executable matrices build and pass.

## Source and candidate boundary

| Item | Identity |
|---|---|
| Immutable candidate | `pokrov-1.2.0-candidate.25`, client `54259b0f84e16c58e2d1f5f04b369af4fd0834b2` |
| Successor correction | client `f59373b313b8d4e7805c8aa4703489a8ff01758e` |
| Client merge | `ed74928a88ead8053a845f9d8e294d1298b83a6a` on `main` |
| Pull request | POKROV-app `#71` |
| Scope | CMake test registration plus canonical Windows readiness wording |

No service, UI, Core, tunnel, DNS or packaging product source changes. No
`artifacts/releases/**` file changes. Candidate.25 bytes, signed manifest,
source tuple and Gate F decision remain immutable; the correction receives no
candidate.25 runtime or hosted-CI credit.

## Local verification

- CMake `3.29.5-msvc4` fresh configure: `PASS`;
- Debug enumeration: eight tests including `pokrov_service_integration`;
- Release enumeration: seven tests excluding integration;
- Debug native CTest: `8/8 PASS`;
- Release native CTest: `7/7 PASS`;
- client docs contract: `PASS`;
- client `validate-seed.ps1` under PowerShell Core with exact clean Core and
  platform roots: `PASS`;
- `git diff --check`: `PASS`;
- release-artifact delta: `NONE`.

The task-owned Debug/Release binaries were removed through the generated CMake
clean targets. The retained configuration is `1463609` bytes. No foreground
UI, mouse, keyboard, installed service or host network mutation was used.

## Hosted boundary

POKROV-app run `33719302139` is `BLOCKED_BY_ACCESS`, not failed test evidence.
GitHub allocates no runner and executes zero steps because the account reports
a payment or spending-limit restriction. No purchase is performed. PR #71 is
merged under the standing `OWNER_SOLO_EXCEPTION` with the exact local evidence
recorded in the PR; independent review and hosted PASS are not claimed.

Phase 03 remains `I3`. Gate F remains exact `BLOCKED 5 PASS / 14 non-PASS /
0 FAIL`; this test-harness-only correction does not satisfy any connected
Windows acceptance criterion and does not warrant Gate F regeneration.

## Evidence

- normalized record:
  `evidence/013FK-windows-ctest-configuration-correction/013FK-windows-ctest-configuration-correction.json`;
- normalized SHA-256:
  `a0eb08fd5495159292287eafe30bf6722d1e7484260bd9e35c9b416adb2aa61f`;
- hosted run `33719302139`: `BLOCKED_BY_ACCESS`, zero executed steps;
- release effect: `NONE`.
