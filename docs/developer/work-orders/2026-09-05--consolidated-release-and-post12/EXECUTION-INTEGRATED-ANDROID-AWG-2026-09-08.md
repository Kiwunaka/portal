# Текущий Huawei — связная AWG-приёмка

Последующий readback уточнил rule gap: **PASS_BOUNDED**. В обоих правилах
изменились только младшие 16 бит `fwmark` с 221 на 239; 239 — текущая active
default network Android. Обратная подстановка 221 воспроизводит прежние SHA-256
полных строк. Приоритеты, маски, targets и все остальные bytes совпадают.
Исходные FAIL/raw-hash observations сохранены; признака оставшихся VPN-правил
это различие не даёт. Client `rule-final-analysis.json` содержит проверку.

**PASS_BOUNDED_WITH_RULE_RESTORE_GAP**, 2026-09-08. Тот же интегрированный
ARM64 APK `88452b99…5850`, client `7ae931b`, Core `02a091c`, Huawei Android 12
/ SDK 31. Client owner:
`POKROV-app/docs/operations/evidence/2026-09-08-r12-integrated-android-awg/`.
Полный receipt сохранён в client repo; сводка дополняет
[общую матрицу](INTEGRATED-ACCEPTANCE-2026-09-08.md).

Текущая установка однозначно найдена по аккаунту приложения и обновлению
серверной записи при открытии списка устройств; exact install hash совпал,
last-seen — одна секунда. Предыдущее совпадение только по модели не использовано.
Разрешение владельца от 2026-09-08 на все тестовые профили сохраняется.

Готовые AWG-профили оказались старше семидневного срока (226,1 часа).
Штатное reprovision сохранило старые записи как rotated и создало по одной
ready-записи с прежним endpoint material. Entitlement не менялся. Временный
cohort включал только подтверждённую установку; перед каждой записью проверялись
исходная конфигурация, отсутствие других lab cohorts и общих lab defaults.

AWG3.1 → AWG2 → AWG3.1 применялись обычным reconnect. На каждом этапе
работали foreground VPN service/TUN, приложение подтверждало защиту, сервер
видел свежий handshake и двусторонний TCP payload. Обратное переключение
дало 62/56 payload packets за 25 секунд; AWG2 — 118/138 за 30 секунд.
Текущая сверка server/material прошла 11/11 checks для каждого протокола.
Это independent inner-tunnel traffic evidence, а не полный leak/egress audit.

На AWG3.1 выполнен Wi-Fi → MOBILE → Wi-Fi. PID, service, VPN agent и TUN
сохранились; защита подтверждена на мобильной сети и после возврата Wi-Fi.
Серверный 50-секундный замер покрывает весь переход, поэтому не засчитывается
как отдельный cellular-only packet capture. Первый parser failure сохранён
и исключён из PASS.

Исходная rollout configuration восстановлена полностью по hash; resolved
profile снова `legacy_reality_fallback`. Обычное подключение после возврата
работало. Телефон оставлен с VPN off, без TUN, Wi-Fi/mobile enabled и прежним
APK hash. Исходный route hash совпал. Два из 20 policy-rule hashes изменились
после handover; причина не установлена, **точное восстановление правил открыто**.
Первый промах по кнопке отключения во время закрытия sheet сохранён; повторное
нажатие по наблюдаемому экрану отключило VPN.

Client evidence commits `301d7e6` и `4707b63` (уточнение network-ID).
Client seed/docs checks, 31 retained file hashes, platform docs/context checks
(33 tests), package links/83 IDs, public-link check и `git diff --check` PASS.
`artifacts/releases/**` не менялись.

Локальные scripts/evidence retained в
`E:/r12-integrated-acceptance-20260908/android/awg`. Выполнены
`lab-control.py plan/switch/restore`, `reprovision.py`, `handover.py`, SDK ADB
network/UI/hash samples, `remote_count_owned_awg_packets.py --capture-scope inner`
и `remote_audit_owned_awg_alignment.py` для обоих labs с strict SSH trust.
Первый alignment запуск без явного credential path остановился до remote access;
исправленный запуск прошёл. Секреты и raw connection material не сохранялись.

Полные N/D/A parents, outage/expiry/revocation, rule restoration, независимые
DNS/IPv6/MTU/UDP53, energy/soak и final candidate остаются открытыми. Локальный
platform tuple не развёрнут: тест использовал существующий brain backend.
Нового кандидата, публичного включения AWG, push или deploy не было.
