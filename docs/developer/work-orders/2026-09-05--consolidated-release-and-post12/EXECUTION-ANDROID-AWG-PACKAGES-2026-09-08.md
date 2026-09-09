# A03/D01 — подготовлены Android APK с новым Core

**LOCAL_PACKAGE_PREPARATION / PASS**, client `76614b1`, Core `02a091c`,
`1.2.0+4053`, current-origin build. [Receipt](evidence/android-awg-packages-2026-09-08.json)
связывает исходники с клиентским evidence и хешами локальных APK.

ARM64 — **101 229 131 байт**, universal — **295 231 078 байт**; также собраны
ARMv7 и x86_64. `apksigner verify` и `aapt dump badging` PASS: прежний signer,
package/version, SDK и non-debuggable; ABI соответствуют вариантам. Core SO
побайтно совпали с привязанным AAR, native binaries и notices split/universal
совпадают. ARM64 меньше universal на 65,71%. Четыре APK перепроверены по SHA-256.

Команды и исходные receipts сохранены в `E:/r12-android-awg-crossfield-20260908`.
Это source tuple до Windows-only correction `68a44e5`; новая метка HEAD к
старым APK не подставлялась. Подпись существующим ключом не означает новую
release-авторизацию или опубликованный candidate.

Физическая установка этих bytes — **BLOCKED_BY_ACCESS**: телефон не был
подключён. Exact ARM64 update/account continuity, Wi-Fi/LTE/IPv6 и runtime
приёмка остаются открытыми. Доказательства старого пакета не переносятся на новый.
Публичные download/pointer и retained release artifacts не изменялись.
