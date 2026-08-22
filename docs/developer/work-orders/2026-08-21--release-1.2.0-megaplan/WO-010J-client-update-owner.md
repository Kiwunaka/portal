# WO-010J — Release-critical client update owner

Status: `COMPLETE_LOCAL_I3`
Classification: `ACTIVE_EXECUTION_EVIDENCE`
Phase: `08`
Lane: active client `POKROV-app`
Ledger row: `REL/ARCH-003`
Depends on: `WO-010B6`, `WO-010D1`, strict release-handoff v2
Production/external actions: `NOT_AUTHORIZED`

## Outcome

Close the remaining proved P0/P1 screen-ownership gap without mechanically
rewriting every retained Dart `part`. The release-critical update prompt had
check concurrency, release deduplication, presentation and progress rendering
inside the 6,324-line shell composition root. It now has one ordinary imported
feature owner while metadata access, installer execution, external handoff and
lifecycle/observability reporting remain injected shell responsibilities.

This is local source and regression proof. It does not create a candidate,
build or sign an APK/EXE, publish a release, exercise an OS installer on a
physical device or prove the public release index.

## Implemented boundary

- `src/features/update/client_update.dart` owns the public installer/progress
  types, `ClientUpdateCoordinator`, update bottom sheet, bounded size copy and
  progress dialog.
- `ClientUpdateCoordinator` serializes checks, suppresses an overlapping check,
  deduplicates the same platform/version/policy prompt, releases its gate after
  failure and accepts metadata/presentation/reporting callbacks.
- `seed_shell.dart` calls the coordinator with the existing release service and
  retains only composition-root work: metadata fetch, trusted handoff/installer
  execution and lifecycle/observability side effects.
- Update prompt/progress keys and the three raw mutable update-check fields are
  absent from `seed_shell.dart`; the architecture guard rejects their return.
- The feature is an ordinary library imported/exported by `app_shell.dart`.
  The guarded `part` ceiling stays at 29.
- `seed_shell.dart` falls from 6,324 to 6,121 lines. The new owner is 325 lines;
  no framework, process, API, state schema or product authority was added.

## Why this closes `REL/ARCH-003`

`WO-010B6` already moved Protection Center mutable disclosure/repair state
behind a focused feature controller. This work closes the next concrete P0/P1
ownership failure: the release/update screen and its check state. Home,
Locations, Rules, Profile, Rewards and Support already render from focused
feature files and injected callbacks; `WO-010H` found no acceptance failure
requiring a mechanical conversion of every remaining part into another public
library. The release architecture criterion is therefore locally proved
without crediting line-count churn as architecture.

Future extraction still requires a concrete ownership/testability failure. A
new state framework, shell rewrite or unconditional part-file migration remains
outside 1.2.0.

## Verification

- `flutter analyze --no-pub` in `packages/app_shell`: `PASS`, no issues.
- focused coordinator tests: `PASS`, `2/2`, including overlap/deduplication and
  failure-gate reset.
- focused existing update widget tests: `PASS`, `2/2`, including trusted Android
  installer progress and rejected untrusted metadata.
- complete `packages/app_shell` suite: `PASS`, `379/379`.
- `test/client-presentation-boundary.ps1`: `PASS`; five coordinators, update
  feature owner, no raw shell update state/widgets, 29 parts.
- `scripts/validate-seed.ps1` with the active platform and Core roots: `PASS`,
  including product/version, observability, logging, release-handoff, CI,
  hygiene, standard runner, presentation, performance and docs contracts.
- client `git diff --check`: `PASS`.

## Ledger and limitations

`REL/ARCH-003` advances from partial `I2` to local `I3`. Distribution becomes
`I3=279`, `I2=33`, `I1=45`, `I0=20`; 98 of 377 rows remain below `I3`. The
pre-freeze queue falls from 29 to 28; candidate/external/deferred counts remain
`32/17/21`.

Physical Android/Windows installer journeys, TalkBack/Narrator presentation,
exact-candidate artifacts and public release-index readback remain Phase 11
evidence before `I4` or higher. Candidate creation, signing, deployment,
publication and promotion remain unclaimed.
