# Текущие условия следующей приёмки

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
