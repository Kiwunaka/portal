# Релиз 1.2.0: срез перед пересборкой плана

Дата: 2026-09-05. Статус выполнения: `OWNER_PAUSED_FOR_REPLANNING`.

По прямому запросу владельца результаты сохранены как есть. Старый план
не продолжается автоматически. Новых сборок, тестов устройств, деплоя,
покупок, публичной публикации или изменения видимости репозиториев нет.
Это остановка для перепланирования, не завершение mega-goal и не GO релиза.

## Откуда продолжать новый план

- [Индекс старого плана](INDEX.md): входные аудиты, решения и все work orders.
- [Построчный ledger](EXECUTION-LEDGER.csv): 378 ID с состоянием, индексом,
  доказательствами и следующим действием. На момент среза SHA-256 файла:
  `bb48dcd26e2400dab7415b79faa566a73cbd7c90d5ff0c63e250196fddd39815`.
- [Исходная формулировка goal](evidence/owner-freeze-2026-09-05/goal-objective.md)
  сохранена без переопределения; поздние решения и доказательства важнее её
  первоначальных формулировок.
- [Клиентский checkpoint](https://github.com/Kiwunaka/POKROV-app/blob/da1ad7395615837432615e0f150d7c0bf05322a4/docs/operations/cutover-readiness.md)
  и восемь очищенных отчётов AWG сохранены в `POKROV-app/main`, PR #93.
- [Проверка Git и локальных остатков](evidence/owner-freeze-2026-09-05/git-audit.json).

## Точный кандидат и решение

Последний кандидат — **приватный подписанный `pokrov-1.2.0-candidate.33`,
приложение `1.2.0+4053`**. Его байты не пересобирались для этого среза.
Сохранённый публичный релиз — `1.1.6`; candidate.33 не опубликован публично
и не продвинут в stable. Подпись release-manifest не является Windows
Authenticode: Windows остаётся без доверенной подписи с согласованным
предупреждением SmartScreen.

| Компонент кандидата | Замороженный commit |
| --- | --- |
| Platform | `f5300053026d32826e54c02202303e1f68c65bc1` |
| Client | `6ab1bcaf39c61a0ae0c9d8328e6c95382885735e` |
| Core | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Release index | `63993fba699b68641b7e972071ab7729fa9ec43c` |

Последний сохранённый [Gate F](evidence/013GV-candidate33-bounded-windows-android-runtime/013GV-candidate33-gate-f-decision.json):
**BLOCKED, 2 PASS / 17 non-PASS / 0 FAIL**, 19 проверенных ссылок,
0 ошибок валидации. Поздние частичные наблюдения не превращены в полный PASS
и не переписывают этот датированный результат.

## Что действительно получено

- Supply: подписанный manifest/receipt, SBOM/provenance, 6 артефактов,
  точное соответствие 11/11 Windows-файлов; [WO-013GT](WO-013GT-candidate33-signed-supply-windows-focus.md).
- Исходники и локальные проверки A–E, byte-identical откат на изолированных
  данных: [WO-013GU](WO-013GU-candidate33-gates-a-e-local-rollback.md).
  Это не live PostgreSQL/provider/production-проверки.
- Windows candidate.33: исправление второго запуска/фокуса; ограниченные
  synthetic TUN/DNS/DoH, восстановление после остановки службы и перезагрузки,
  удаление/переустановка, login/startup, synthetic saved-state migration.
  Границы каждого результата находятся в клиентском checkpoint и WO-013GV–HC.
- Android: точные байты на физическом устройстве, Wi-Fi и ограниченное
  наблюдение Beeline. LDPlayer: установка и cold-start UI; сеть через
  существующий туннель основной Windows не засчитана как независимый тест.
- Производительность: исправлена ошибочная трактовка отсутствующего CPU
  счётчика службы как нуля; свежий raw-WMI срез — отдельное доказательство.
  Cabinet rendering p95 `176.284 ms` — только localhost, exact export,
  synthetic API/session, не реальные авторизация и backend latency.
- На 2026-09-05 свежие npm audit трёх точных lockfile дали 0 известных
  advisory; это датированный dependency-результат, не общий security PASS.
- Последний AWG-заход: владелец выбрал fullTunnel; получена ревизия AWG3.1,
  connected UI, API DNS/HTTPS. После назначения AWG2 обычный reconnect
  сохранил старую ревизию, поэтому AWG2 не засчитан. По коду это повторное
  использование staged profile; штатный repair обновляет его, но проверка
  repair не выполнена — владелец остановил управление.
- После остановки временное назначение AWG2 снято: точный install readback
  `default`, `ok=true`, без cohort/allowlist. Последнее наблюдение ВМ —
  disconnected; проверка полного совпадения route/DNS baseline в этом заходе
  не выполнялась. Основная Windows/Hiddify не менялись.

## Индекс исполнения без процента «готовности релиза»

I1 — обследовано; I2 — реализовано; I3 — локально проверено; I4 — доказано
для точного кандидата; I5 — доказано после релиза. Записи REJECT/MONITOR и
архитектурные решения нельзя считать выпущенными функциями.

| Семейство ledger | Всего | I1 | I2 | I3 | I4 | I5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| REL + DoD + gates | 63 | 2 | 3 | 51 | 7 | 0 |
| OBS + DoD + PB | 134 | 3 | 5 | 125 | 1 | 0 |
| Operator Center | 30 | 1 | 1 | 28 | 0 | 0 |
| Frontend + PR + bugs | 78 | 8 | 4 | 66 | 0 | 0 |
| Marketing + stages | 17 | 1 | 2 | 14 | 0 | 0 |
| FRKN и протокольные решения | 56 | 17 | 4 | 35 | 0 | 0 |
| Всего | 378 | 32 | 19 | 319 | 8 | 0 |

## Что нельзя переносить в новый план как закрытое

Полный managed AWG3.1/AWG2 lifecycle, WARP/Smart DNS и профильная проверка
egress; RU-origin/Beeline, UDP/IPv6/MTU, handoff/OEM/endurance; полные
Windows/Android матрицы; live миграция/rollback, платёжный provider E2E,
operator OIDC/RBAC/action-intent, legal/commercial/pilot, полная performance
и release-health матрица, обязательный DoD и отсутствие открытых P0.
Детальные 19 строк и их статусы сохранены в Gate F, каждый ID — в ledger.

GitHub required job для нового клиентского PR #93 снова не исполнил ни шага:
job `101249235240`, `steps=[]`, причина — Billing/spending. Покупок нет,
merge выполнен по ранее разрешённому solo exception, не как зелёный CI.
DE-side SSH не проверен: старый helper выбирает недоверенный port alias,
а `pokrov-de` на port 22 сообщает изменившийся host key. Проверку доверия
не отключали; дальнейшая сверка требует независимого подтверждения ключа.

## Git, артефакты и что осталось локально

Текущий клиентский срез сохранён в `main` через PR #93 (`da1ad739...`).
Текущий platform-срез — этот документ и его commit/PR. Core и release-index
не менялись; их актуальные remote main на момент проверки:
`c1185faa998c69fd5164af415249c96c68ab61bd` и
`9169f272203ec690ab7b0e6a69e92dc2b6762cb4`.

Дополнительно 9 platform и 4 client старых релизных head сохранены на GitHub
под `codex/freeze-1.2.0-20260905/*`; SHA проверены через `ls-remote`.
Это архив точной истории, **не слияние старого кода в master/main**.

«Релизный срез запушен» не означает «все локальные папки чистые»:
в основном VPN checkout есть отдельные изменения private-chat/infra/docs,
FRKN raw-материалы; отдельно остаются post-1.2.0 и design/infra ветки,
изменённые generated registrants старых client worktree и `.obj`.
Они не включены в этот релизный freeze, не удалены и перечислены в Git audit.
Основные checkout могут отставать от remote; это не непушенные изменения.

Шесть собранных бинарников и локальные signing/supply-файлы остаются в
`E:/POKROV-tools/release-candidates/pokrov-1.2.0-candidate.33/`.
Свежие размеры и SHA-256 сохранены в
[инвентаре артефактов](evidence/owner-freeze-2026-09-05/local-artifacts.json).
Git push исходников не загружает эти APK/AAB/EXE. Временные evidence на E
не удалялись. GitHub signer artifact `9928470408` сейчас `expired=false`,
срок хранения — **2026-09-18 08:01:25 UTC**; перенос нового плана за эту дату
требует сохранить signing evidence, не рассчитывая только на Actions.

Старые post-1.2.0 планы не запущены и не включены автоматически в релиз.
Новый план должен явно определить, что оставить, убрать и какими точными
приёмочными проверками закрыть оставшиеся пункты.
