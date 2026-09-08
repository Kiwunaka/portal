# Текущие условия следующей приёмки

## Текущая очередь до выпуска — 2026-09-08

[Исправление явного запрета доступа](EXECUTION-INTEGRATED-ACCESS-DENIAL-2026-09-08.md)
client `f479fd4` принято в Windows VM: 304 hashes, очистка кэша и отключение,
offline отказ после UI restart PASS. Прежний комплект больше не содержит все
требуемые исправления. Следующий шаг — новый Android APK после общего Dart
изменения и затронутая device проверка; далее actual revocation/expiry нового
комплекта. Старый controlled-clock expiry не закрывает эти сценарии.

[Совместимость actual old/current backend](EXECUTION-INTEGRATED-BACKEND-COMPAT-2026-09-08.md)
для `16407b8` проверена на PostgreSQL: 25 HTTP assertions, пять SQL writes,
совместная работа и restart старого API после нового PASS. Предыдущие 197 файлов
сверены с работающим Brain; текущие 200 — с Git. Schema inputs и фактические
1690 columns / 734 indexes / 246 constraints одинаковы. Новой expand/contract
migration для этого exact pair нет; её искусственное добавление не требуется.
Production snapshot/volume/locks/recovery остаются отдельными gates.
Expiry/revocation остаются отдельными критериями связной приёмки; новый
результат явного запрета и следующий шаг указаны выше.

[Windows connected update текущего комплекта](EXECUTION-INTEGRATED-WINDOWS-UPDATE-2026-09-08.md)
прошёл с первого раза: 305 hashes, saved session/experience bytes, повторное
подключение и восстановление routes/DNS. Backend config восстановлен точным
guarded rollback после отказа entitlement selector; учётные данные/material не
менялись. VM off/NIC none, host network неизменна. Sleep VM не поддерживает;
полные Windows gates и actual expiry/revocation остаются открытыми.
Проверка совместимости backend выполнена в указанном выше локальном scope.

Последующее [AWG-прохождение текущего Huawei](EXECUTION-INTEGRATED-ANDROID-AWG-2026-09-08.md)
закрыло поиск exact identity и дало AWG3.1→AWG2→AWG3.1, server inner traffic и
Wi-Fi/mobile/Wi-Fi continuity. Backend configuration восстановлена, VPN off,
routes совпали; два policy-rule hashes изменились только из-за нового OS network
ID, остальной текст совпал с baseline. Следующая очередь — оставшаяся связная
Windows/backend-приёмка; новый candidate и выпуск ещё не выполнены.

[Текущий backend](EXECUTION-INTEGRATED-BACKEND-2026-09-08.md): 129 HTTP tests,
22 subtests и 9 PostgreSQL concurrency cases PASS на `16407b8`. Локальная
payment acceptance выполнена. Actual old/current compatibility дополнена выше;
deployed operator/runtime, реальные provider операции и оставшаяся Windows matrix открыты.

Обновление: [единый комплект и acceptance matrix](INTEGRATED-ACCEPTANCE-2026-09-08.md)
закреплены. Preflight `READY_LOCAL_FREEZE`, 15/15 local quality steps и четыре
Android ABI audit PASS. Новый ARM64 установлен на Huawei: два обычных
connect/disconnect с точным восстановлением routes/rules PASS_BOUNDED.
Продолжать связную приёмку этого комплекта; новый candidate/release не создан.

Ответ на вопрос владельца о глобальном прогрессе: программа всё ещё до нового
релизного кандидата. Реестр содержит 83 требования: 2 verified, 65 active,
3 blocked, 13 queued; это статусы критериев разного масштаба, не процент
готовности кода. У 65 строк есть I3, у одной I4. Postrelease-программа не начата.
Последние Android/Windows/Pi проверки дали новые результаты, но их дробление
не должно подменять выход из релизного этапа.

Следующая работа выполняется пакетами с конечным результатом. Исходные 83 ID,
378 legacy references, условный scope и отдельные разрешения сохраняются.

1. **Единая приёмочная сборка.** Закрепить фактический platform/client/Core
   source tuple, сверить оставшиеся изменения кода с текущими blockers и
   собрать согласованный локальный комплект. Выполненные checks переносить
   только при совпадении значимых inputs. Документы и Windows-only diff сами
   по себе не требуют повторной Android/Core сборки. Выход: один manifest
   исходников, пакетных bytes и необходимых проверок для этого комплекта.
   Публичная публикация и promotion этим шагом не разрешаются.
2. **Связная приёмка комплекта.** Один проход Android и Windows критического
   пути: сохранение данных при обновлении, обычное применение профиля,
   достоверная защита, outage/expiry/revocation, disconnect/recovery и
   применимые network сценарии. Backend: payment idempotency/reconciliation,
   текущие operator access/fingerprint и migration/rollback. Исправлять
   обнаруженные stop-ship дефекты; повторять только затронутые проверки.
   Выход: единая acceptance matrix с конкретными PASS/FAIL/manual/blocked,
   а не следующий набор несвязанных локальных отчётов.
3. **Условия выпуска.** Разрешённые локальные проверки выполнить самостоятельно;
   один актуальный список внешних ограничений сохранить отдельно. Сейчас
   существенны лицензированный Win10-стенд, точная привязка текущего Android
   для AWG, реальные provider операции, deployed operator proof, окончательные
   signing/channel и release решения. Решения владельца о пропуске платного
   GitHub и seller/receipt проверки сохраняются как SKIPPED_BY_OWNER, не PASS
   и не новый запрос на оплату. Выход: конкретный пакет для решения владельца
   с artifact hashes, окружением, rollout/rollback и оставшимися условиями.
4. **Разрешённый выпуск и наблюдение.** Только после применимых gates и
   конкретного разрешения: поставка тех же bytes, readback, observation,
   go/no-go и закрытие R12. Затем активируется предусмотренная очередь
   дополнений. Локальный успех не закрывает этот этап.

Не открывать дополнительные обзоры, оптимизации или повторные проверки ради
увеличения числа PASS. Для каждого следующего действия назвать незакрытый
критерий этого пакета и результат, который позволит перейти дальше.

### Последние новые факты

- DE доступен; exact server/Core Pi interop A02 verified/I4.
- [Новый ARM64 APK установлен на Huawei](EXECUTION-ANDROID-DEVICE-2026-09-08.md),
  обычный connect и handoff проверены. Телефон сейчас доступен; старые сообщения
  «0 устройств» не являются текущим blocker. AWG preview нашёл старую запись
  устройства и был отклонён до mutation; требуется точная текущая identity.
- Win11 evidence и Core tests уже сохранены; generic local PASS не заменяет
  отсутствующий Win10 и final candidate proof.

Ниже сохранены предыдущие датированные срезы. Их утверждения о доступе и
pending owner decisions читаются вместе с новыми фактами и
[решениями владельца](OWNER-DECISIONS-2026-09-07.md).

[Windows recovery 2026-09-08](EXECUTION-WINDOWS-RECOVERY-2026-09-08.md): аварийное
завершение UI сохраняет работающую службу и TUN; повторный запуск видит подключение.
Штатная перезагрузка при AWG3.1 возвращает безопасное отключённое состояние,
точные исходные маршруты/DNS и автоматическую LocalSystem-службу; 305 файлов
пакета неизменны. Конфигурация тестового cohort восстановлена, VM выключена
с NIC none. Падение службы, сон, повторное подключение после reboot, независимый
route proof, WFP/IPv6/Win10 и final candidate остаются открытыми.

[Установщик 2026-09-07](EXECUTION-WINDOWS-INSTALLER-2026-09-07.md): исправлен
реальный отказ clean install через UAC другой учётной записи. Отдельный
R12Standard подтверждён без прав администратора: install, 305 hashes, stock
UI/IPC, uninstall/reinstall и SCM autoboot до login PASS в локальном offline
scope. Полная network/connected-update/Win10/final-channel matrix открыта.
Новый installer clone `960ae449-036f-4166-b215-d8349145a4de` оставлен offline
с установленной auto-службой; прежний SCM clone и исходная VM сохранены.

[SCM 2026-09-07](EXECUTION-WINDOWS-SCM-2026-09-07.md): служба LocalSystem, IPC
под ограниченным токеном владельца, Initialize текущего Core и остановка PASS
в component scope. Отдельная standard-account UI/installer и managed-network
матрица остаются открытыми. Клон включён офлайн, служба оставлена stopped/manual.
Evaluation Windows выключается через `wlms.exe`; учитывать это в длительных runs.

[Проверки всех трёх сред 2026-09-07](EXECUTION-RUNTIME-SURFACES-2026-09-07.md):
Windows VM включена; [W04](EXECUTION-W04-SHELL.md) содержит исправления скрытого
запуска и падения при выходе с точным red/green proof. На Pi прошли AWG2/AWG3.1
для текущего Core. Huawei сохранил VPN при контролируемой смене сети и подтвердил
защиту; первое неполное наблюдение разрыва остаётся открытым. Доступность этих
трёх стендов подтверждена, а полная runtime/release matrix ещё не закрыта.

Актуализация 2026-09-07: [решения владельца](OWNER-DECISIONS-2026-09-07.md)
снимают вопросы N02 и O03/V02. Защищённый офлайн-профиль и автоматическая
диагностика исходной сети реализованы; [новые проверки и границы](EXECUTION-OFFLINE-NETWORK-2026-09-07.md)
относятся к client `550329f` и platform `f103a7b`.
Huawei теперь доступен: Android 12 / SDK 31, физические Wi-Fi/mobile проверки
проведены. Старое наблюдение «0 устройств» больше не является блокером.

M01 seller/receipt и платные GitHub G04/G06 — `SKIPPED_BY_OWNER`.
Их общий release criterion остаётся незакрытым: skip не означает provider,
CI или enforcement PASS. Оплата GitHub и реквизиты сейчас не запрашиваются.
Полная Windows UI/SCM/network/Win10, Android matrix, exact release bytes, deployed
Android-to-API diagnostics и origin-specific acceptance остаются отдельными
незакрытыми проверками. Production/release rollout не выполнен.

Последующая [проверка ARM64 и статуса подписки](EXECUTION-ARM64-ACCESS-2026-09-07.md)
относится к client `9334d46`, platform `01914f9`, Core `8dc57a8`. Штатный ARM64
APK — 101,2 МБ против universal 295,2 МБ; подтверждены отдельные ABI, сохранность
Core/notice assets и локальный переход universal → ARM64 на Huawei. При
недоступном API больше не подставляется «Пробный · 5 дней», а сохранённый профиль
подключается и подтверждает защиту. Обычный APK восстановлен, его installed hash
совпал; VPN отключён. Полная D02/D03/D04 matrix и final channel остаются открыты.

[D03 Huawei](EXECUTION-D03-HUAWEI-2026-09-07.md): тот же ARM64 APK выдержал
120 секунд forced Doze и 60 секунд app standby; процесс и VPN-служба сохранены,
после каждого сценария защита повторно подтверждена. Android возвращён в обычный
режим, VPN отключён. Это частичная проверка; длительный сеанс, battery baseline,
остальные OEM/API и lifecycle-сценарии ещё открыты.

## Исторический readback до ответов владельца

Ниже сохранены прежние наблюдения. Упоминания ожидаемых N02/O03/M01/GitHub
решений относятся к их дате; для продолжения применяется актуализация выше.

После C03 выполнен [общий локальный gate](EXECUTION-LOCAL-CONVERGENCE.md):
2026-09-06 15:57 UTC, platform `272ef9a`, client `70907c0`, Core `8dc57a8`;
15/15 этапов PASS, 9/9 статических пределов PASS, пять целевых размеров не
достигнуты. Это текущая локальная проверка исходников. Внешняя доступность
повторно не проверялась; следующие наблюдения сохраняют время своего readback.

Последний [readback — 2026-09-06 14:39 UTC](EXECUTION-ACCEPTANCE-READBACK.md):
Android не подключён; SCM result отсутствует. Изолированный Windows-клон был
запущен только для чтения результата и снова выключен, NIC1 `none`. Последние
platform/client CI jobs имеют ноль steps; enforcement остаётся недоступным.
Текущий tuple: platform `afb2917`, client `c579708`, Core `8dc57a8`.
Ниже сохранены предыдущие наблюдения и ещё открытые owner decisions.

Последующий [Windows component lab](EXECUTION-WINDOWS-LAB.md): исходная VM
остаётся выключенной; из чистого snapshot создан и запущен отдельный linked
clone с NIC1 `none`. Семь native fixtures PASS; SCM-сценарий подготовлен,
ожидает ручного UAC. Таблица ниже сохраняет предыдущий readback до клонирования.

Readback: 2026-09-06. Platform source `0767c7d`, client `ded58b1`, Core `94dd310`.
Доказательства: [next-acceptance-access.json](evidence/next-acceptance-access.json).
Предыдущие source changes и [карта G03](EXECUTION-G03.md) сохранены.
Общий план не завершён; это перечень конкретных незакрытых условий.

## Свежая доступность сред

| Поверхность | Наблюдение | Следствие |
| --- | --- | --- |
| Android ADB | `devices -l`, exit 0: 0 устройств, 0 emulator, 0 physical ready | Физическая D/N matrix не выполняется без подключённого разрешённого устройства; новый emulator не заменит radio/OEM/Doze proof |
| Windows VirtualBox | `POKROV-Win11-Test`, Windows 11 64-bit, poweroff; snapshot pointer `ready-for-pokrov-tests`; 4 GB / 2 CPU | VM существует. Не обозначать её отсутствие как блокер. Нужны exact payload и проверка guest baseline перед текущим runtime run |
| VM isolation | NIC1 bridged, link on; clipboard/drag-and-drop disabled, VRDE off | Boot может включить сеть гостя. VM не запускалась, snapshot не восстанавливался, настройки не менялись; metadata не подтверждает чистоту текущего disk state |
| Hyper-V | CIM namespace недоступен, `0x8004100e` | Не является альтернативной проверенной VM surface |
| Platform/client Actions | Latest contract runs `completed/failure`, 0 job steps; annotations содержат billing/spending и job-not-started сообщение | Это ошибка запуска hosted jobs, не результат тестов. Новые локальные HEAD в этих runs не проверялись |
| Platform/client enforcement | Rulesets и branch protection API: HTTP 403 | Нельзя подтвердить required checks/bypass/enforcement текущими правами |
| Core enforcement | Rulesets API: пустой список; `main/protection`: HTTP 404 | Readback не подтверждает настроенную защиту; не приравнивать обычный CI PASS к enforcement |
| Core Actions | Последний доступный CI success для `c1185faa`, включая test и artifact reproducibility jobs | Старый source tuple; не доказательство CI для нового `94dd310` |

Исторические Windows WO подтверждают назначение `POKROV-Win11-Test` как POKROV
lab и retained clean snapshot. Они не доказывают текущую чистоту гостя или
приёмку нового source tuple. Current VM state не менялся; host VPN, routes,
DNS, учётные записи и настройки гипервизора не тронуты.

## Решения и данные, без которых нельзя завершить соответствующий критерий

1. **N02 — rollback authority.** Текущий канон требует свежий managed profile
   после dataplane failure; revision сам по себе не даёт права восстановить
   старый профиль. Открытый выбор: свежая серверная авторизация восстановления
   либо отдельно заданная signed offline authority. Не вводить новый offline
   grace, entitlement exception или silently accepted old revision.
2. **O03/V02 — источник индивидуальной диагностики.** Открытый выбор: существующий
   opt-in support bundle с UNKNOWN без него либо новый минимальный account-bound
   report с явно заданными consent/retention/access правилами. Operational
   release-health ingest не превращается в персональную телеметрию автоматически.
3. **M01/B06 — продавец и receipt/provider evidence.** Нужны утверждённые реквизиты,
   issuer/process реального чека, привязка к оферте и конкретной provider setup.
   Запрос владельцу отправлен; данные не получены. Actual payment/refund и
   reconciliation требуют предусмотренного отдельного разрешения на операции.
4. **G04/G06 — hosted CI/enforcement.** Владелец GitHub account должен устранить
   billing/spending блокировку и обеспечить readback enforcement либо явно
   оформленное допустимое исключение по действующему release contract. Никакой
   оплаты, смены visibility, bypass или изменения repository settings не было.
5. **D/W/A/Q — фактическая среда и final acceptance.** Physical Android,
   Windows 10/11 scope, owned server/profile/origin tuple, exact packaged bytes,
   signing/channel и наблюдение проверяются по их отдельным критериям. Наличие
   Win11 VM не закрывает Win10, guest sleep/IPv6, SmartScreen или network matrix.

Вопросы N02/O03 были поставлены ранее, M01 — в предыдущем этапе. Ответы на
момент readback не поступили. Это missing decisions/data, не blanket-запрет
на дальнейшие независимые локальные source/tests/builds.

## Порядок продолжения

- Сначала завершить зависящие от ответов N02/O03 source contracts и M01 binding
  в их собственных scopes; остальные локальные требования можно выполнять
  независимо. Не выбирать вместо владельца новую модель безопасности/сбора.
- Для Windows run использовать найденный POKROV lab, после идентификации
  конкретного payload и проверки безопасного guest baseline; сохранить return
  state и исходные snapshots. Не устанавливать тестовый VPN на пользовательский
  host и не переносить credentials в отчёты. Во время readback гость не запускался,
  установка не выполнялась.
- Для CI после восстановления доступа отправлять только согласованные source
  commits и запускать реальные требуемые workflows по release-процедуре.
  Текущие 0-step jobs повторно не запускались и не считаются ожидающими работами.
- После final tuple собрать dependency-bound acceptance из G03, затем отдельное
  решение по разрешённым production/release операциям. Никакой переход в
  Linux/HAPP/ATS/Smart Access/shortlink rollout не активирован этим списком.

Существующие artifact/VM/history receipts сохранены. Push, merge, deploy,
новый candidate, guest boot, платёж и внешняя коммуникация не выполнялись.
