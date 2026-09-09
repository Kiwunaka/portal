# R12-C03 — владелец обновления аккаунта

2026-09-06. Client `988414d`, Core `8dc57a8`. **I3 / PARTIALLY_FIXED**,
полный C03 открыт. [Receipt и Git blob hashes](evidence/c03-account.json).
Предыдущий [profile-lifecycle slice](EXECUTION-CONTINUED.md#c03a--standalone-managed-profile-lifecycle-owner)
сохранён; этот этап продолжает выделение владельцев состояния.

`AccountSessionCoordinator` вынесен из profile UI part в самостоятельный модуль.
Он владеет прежними account/access/subscription полями, общей in-flight future
и последовательностью subscription → bonus → inbox. Shell передаёт готовые
read/UI callbacks и `mounted`; после закрытия оболочки следующие чтения не
запускаются, завершение или ошибка освобождают future для следующего refresh.

Это отдельный refactoring после [F07](EXECUTION-F07.md): readiness, auth,
per-read error handling, Telegram verification, навигация и payment authority
сохранены. Новый retry или способ подтверждения оплаты не вводился.

**PASS:** `flutter test test/account_session_coordinator_test.dart
test/pokrov_seed_app_test.dart` — **188 tests**, cwd client `packages/app_shell`.
Standalone tests напрямую импортируют coordinator; проверены порядок и
coalescing, handled/unhandled failures с повтором, остановка после subscription
и bonus. Existing shell tests сохраняют Android/Windows cabinet-return,
welcome, concurrent refresh и offline/recovery regressions.

**PASS:** client-root `flutter analyze`; explicit-root `validate-seed.ps1`;
`pwsh -NoProfile -ExecutionPolicy Bypass -File test/docs-contract.ps1
-PlatformRoot C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start`;
`git diff --check`. Точные seed arguments и локальные логи указаны в client
`docs/operations/evidence/2026-09-06-r12-c03-account/`. Performance collector
в seed использует fixture, не reference-device measurement.

`seed_shell.dart`: 6494 → 6482 строки; 29 parts сохранены. Library entrypoint
получил import/export (+2), profile UI part сократился на 27 строк. Эти числа
описывают границу ответственности, не выигрыш скорости. Канон обновлён в
client `docs/architecture/package-boundaries.md`.

Три лога сохранены в проверенном `E:/r12-c03-account-evidence.zip`. Четыре
прежних generated registrants совпали с retained SHA-256 и не вошли в commit.
Native Core bytes, packages и retained release artifacts не менялись.
Нет install, signing, push, merge, deploy, payment, публикации или нового
candidate. Rollback — scoped client commit; предыдущие evidence сохранены.

Полная последовательность connection/presentation/support/checkout C03 требует
отдельной приёмки; соседние I3 не закрывают её автоматически. Условия devices,
SCM, CI/enforcement и final candidate сохраняются в [NEXT_ACCEPTANCE](NEXT_ACCEPTANCE.md).

Platform handoff PASS: docs/context pytest 33;
`agent_context_packet_audit.py --platform-context-root .`;
`validate_package.py` — 13 import hashes, 83 R12 IDs, 378 legacy IDs,
246 local links; `git diff --check`. Receipt закрепляет восемь client Git blobs.
