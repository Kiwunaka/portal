# R12-C03 — support conversation owner

2026-09-06. Client extraction `e91b85d`, subsequent polling correction
`70907c0`, Core `8dc57a8`. **I3 / PARTIALLY_FIXED**, full C03 remains OPEN.
[Receipt, logs and committed blob hashes](evidence/c03-support.json).

## Accepted local boundaries

| Slice | Current evidence | Limit |
| --- | --- | --- |
| Managed profile lifecycle | [Earlier C03A](EXECUTION-CONTINUED.md#c03a--standalone-managed-profile-lifecycle-owner) | Runtime/device acceptance remains separate |
| Account summary | [C03 account](EXECUTION-C03-ACCOUNT.md), client `988414d` | Server/readiness authority unchanged |
| Connection/presentation | Existing `ConnectionCoordinator`, reducer/presenter and typed intents; 14 standalone tests rerun here | No new split, performance or installed-runtime claim |
| Support conversation | New standalone controller; 5 isolated tests plus existing widget/polling checks | AI sheet, encrypted bundle, dialogs and consent retain their existing owners |
| Checkout | Not yet accepted for full C03 | Client delegates to cabinet/handoff; marketing checkout state needs separate boundary reconciliation |

`SupportConversationController` now owns ticket identity/version, projected
messages, load/refresh/send/error state, initial selection, message/feedback
operations and polling eligibility. The view retains composer/focus/scroll,
dialogs, attachment selection and encrypted bundle actions. Existing draft
preservation, feedback, ticket reuse and late-response disposal behavior is
covered without constructing a widget in the controller tests.

The pure extraction was committed first. `seed_shell.dart` remains 6482 lines;
29 parts remain. The support view shrinks 2687 → 2277 lines; the library entry
adds one export. These counts describe placement, not speed or memory.

## Separate observed failure and fix

The controller test exposed an omission already present in the previous widget:
the failed read cleared `refreshing` but left polling ineligible. Automatic
backoff stopped while the UI still showed offline and explicit retry.
The product contract already requires bounded retries for an open foreground
ticket. On exact extraction commit `e91b85d`, both controller and widget red
oracles failed: zero active timers; two reads where the widget expected three.

Commit `70907c0` restores eligibility after the failed read before the existing
polling coordinator applies its backoff. No new timer policy, interval or
transport is introduced. Deterministic tests prove 16/32-second failure delays,
8-second cadence after successful explicit retry, background cancellation and
the actual widget's next read after failure.

## Verification and retained state

- Extraction: **203** existing shell/connection/polling tests + **5** controller
  tests PASS; root analyze and explicit-root seed/docs PASS.
- Before correction: `flutter test test/support_conversation_controller_test.dart
  test/pokrov_seed_app_test.dart --name 'poll fail'` — two expected failures.
- Final: `flutter test test/support_conversation_controller_test.dart
  test/pokrov_seed_app_test.dart test/support_polling_test.dart
  test/connection_experience_test.dart` — **208 PASS**. Test cwd is client
  `packages/app_shell`.
- Final root `flutter analyze`, explicit-root `validate-seed.ps1`, subsequent
  `test/docs-contract.ps1` and `git diff --check` PASS. Exact commands and
  intermediate failed attempts are retained in the client report and receipt.

Archive `E:/r12-c03-support-evidence.zip` contains 11 verified logs. Four previous
generated registrants retain their hashes and remain outside commits. Native
Core binaries, packages and retained release artifacts are unchanged. No build,
install, host VPN, external support message, signing, push, merge, deploy,
publication or new candidate occurred. Rollback is the separate scoped commits.

Client canonical owners were updated in `package-boundaries.md`,
`in-app-ai-assistant-contract.md` and `client-product-contract.md`.
Physical/SCM/provider/CI/final-candidate gates remain OPEN; this local support
result does not close the [overall acceptance prerequisites](NEXT_ACCEPTANCE.md).

Platform handoff PASS: docs/context pytest 33;
`agent_context_packet_audit.py --platform-context-root .`;
`validate_package.py` — 13 import hashes, 83 R12 IDs, 378 legacy IDs,
250 local links; `git diff --check`. Receipt binds ten committed client blobs.
