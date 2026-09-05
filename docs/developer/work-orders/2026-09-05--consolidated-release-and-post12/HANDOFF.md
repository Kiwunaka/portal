# R12 — текущий результат и граница исполнения

**На 2026-09-05: PARTIAL / RELEASE_BLOCKED. План целиком не завершён.**
Локальная реализация и проверки ниже выполнены; production, новый release
candidate и postrelease activation не выполнены. Ранние отчёты сохранены как
последовательные срезы. Точные команды, SHA логов и source tuple —
[evidence/handoff-local.json](evidence/handoff-local.json).

Последующий срез N05 — [наблюдения, новые Core bytes и проверки](EXECUTION-N05.md).
Он дополняет этот сохранённый срез от 2026-09-05.
Следом исправлен [лимит незавершённых Smart Connect probes — N06](EXECUTION-N06.md).

Дополнительно проверен [N08 — режимы маршрутизации и direct в VPN selectors](EXECUTION-N08.md).
Продолжение N08 (`5606fdc`): готовые Windows-профили применяют process/DNS-режимы с сохранением настроенных resolvers; локально 116 + 80 PASS, VM/device proof открыт.

Добавлено [C04/F01/F04 — остановка фоновых animation tickers и сверка presentation](EXECUTION-PRESENTATION.md): client `fa62f04`, 216 локальных тестов PASS; reference device performance открыт.

Исправлен [N01/N04 — repair против pending invalidation и смены режима](EXECUTION-N01-REPAIR.md): client `f024861`, 178 widget/lifecycle PASS.

Добавлен [A04 — согласованная выдача AWG material при ротации](EXECUTION-A04.md): 43 focused checks PASS; server revoke/expiry и interop OPEN.

## Изменения

- Core: correlated endpoint/selector proof; Android/Windows AAR/DLL собраны
  повторно с побайтным совпадением и привязаны к клиенту. ABI2 сохранён.
- Клиент: reconnect обновляет профиль; stage/start/proof связаны с digest и
  upstream revision. Windows и Android сохраняют прежний файл при отказе
  до atomic replacement. Delayed consent/probe не подтверждает другой профиль.
- Клиент: отдельный owner managed-profile lifecycle; ограниченный retry
  250/500 мс + jitter; future-dated/старше 24 ч cache запрещён. Это не новый
  offline entitlement lease и не доказанный durable LKG rollback.
- Checkout: server-signed quote, немедленная invalidation ввода, deadline,
  честный legacy return и same-intent recovery. Реальный disposable PostgreSQL
  дал 8 PASS; повторный счёт провайдера не создаётся в выполненных fixtures.
- Cockpit: `pokrov.operator-cockpit-gates/v1`, count и `gate_f_decision=NOT_EVALUATED`.
  11 operational checks отделены от 19 final Gate F checks; связка областей
  описана в canonical monitoring owner. Registry rollback не выдаётся за deploy.
- Marketing: catalog deadlines и контраст hero-подписей во время входа.

## Последние проверки

- PASS: Core race/full suites, native CTest 8/8, оба Android flavor JVM gates,
  client workspace tests/analyze/seed. Подробные команды и границы —
  [EXECUTION-CONTINUED.md](EXECUTION-CONTINUED.md).
- PASS: новый cache-clock test + gate suite 5; AWG contracts 32; commercial
  revision/capacity contracts 23; diagnostics/observability contracts 33.
- PASS: cockpit service/evidence/manifest 27 + focused API 1; admin lint,
  build и 78 browser cases. Ранее полный admin API набор — 52 PASS.
- PASS: marketing build/SEO/responsive/axe; девять checkout scenarios;
  copy/governance/docs 72; 9/9 static performance stop budgets.
  Несколько целевых performance targets остаются недостигнутыми.
- Общий quality gate сохранён как FAIL из-за одного contrast finding.
  После `bf72daa` затронутые marketing и web-static checks прошли повторно.
  Client/cabinet checks из общего прогона не изменялись этим UI diff.
- Browser review: localhost 3187/3188, marketing 1180×820 и 390×844,
  admin 1440×900; непустые страницы, правильные title/URL, без overlay/page errors.
  Смена кандидата сохраняет заметку о незагруженном Gate F. Synthetic API,
  внешние запросы заменены fixtures. Скриншоты: `E:/r12-ui-review/`.

## Что требуется для продолжения обязательной цепочки

| Условие | Связанные пункты | Фактическое состояние |
| --- | --- | --- |
| Источник operator profile/proof данных | O03/V02/V04 | NEEDS_CONTEXT: pending выбор opt-in support bundle либо нового минимального account-bound отчёта. Новый сбор не включён. |
| Exact source tuple, candidate и hosted CI/signing lane | G04/G06/G07/C05/Q01 | Source commits локальные; нового кандидата нет; private rules readback вернул 403. Финальный license/privacy scan требует новых packaged bytes. |
| Разрешённая Windows VM и exact package | W01–W06/N01–N03/N08/F07 | MANUAL_OWNER_TEST: host VPN не заменялся; clean VM и installed-package proof не выполнены. |
| Физический Android и primary ARM64 APK | D01–D06/N01–N03/N08/F05/F07 | ADB readback: 0 устройств. JVM и desktop screenshot не заменяют physical/Doze/radio proof. |
| Owned lab/server + независимые origins | A02/A04–A09/N07/Q02 | Новый artifact/server/profile tuple и runtime/origin матрица не выполнены. 32 local AWG tests не являются interop PASS. |
| Provider, restore/deploy rehearsal и operator identity | B06/B08/O01/O02/O04/O06/M01 | Реальные payment/refund, DB recovery, OIDC и deployed fingerprint не проверены. Local API/browser fixtures ограничены I3. |
| Exact candidate acceptance и owner release decision | Q01–Q05 | Отдельное решение Gate F ещё невозможно; public rollout, channel, cohort и observation требуют конкретного разрешения после gates. |

N02 остаётся PARTIALLY_FIXED: исправлен сбой завершения recovery journal
после `recovered`, client commit `20b997a`, native 9/9 PASS.
[Новый срез N02](EXECUTION-N02.md) сохраняет regression/evidence и вопрос
политики rollback. Durable last-known-good с entitlement/expiry ещё не доказан.
N05/N06/C03/C04/F04 и другие оставшиеся source/optimization
части не объявлены завершёнными из соседних PASS; их не требуется механически
переписывать без проверенного дефекта или измеренного узкого результата.
Полный текущий статус всех 83 строк сохранён в [реестре](R12-REGISTER.csv).

Linux beta, новый ATS/Broker, Smart DNS/HAPP и `/t/` остаются в условной/postrelease
очереди по исходной последовательности. Release 1.2.0 не закрыт, owner не менял
activation gate. Внешний маркетинговый пилот, spend и публикации не запускались.

## Git и rollback

Platform feature branch: `codex/consolidated-plan-start-20260905` — product
commits `917612f`, `5577bb7`, `bf72daa`, `7e8beab`.
Client feature branch: `codex/r12-client-implementation` — `8176c3b`,
`cebbe851`, `61d1838`, `4dbe2c6`, `20b997a`.
Core feature branch/HEAD — в source tuple, commits `9476df5`, `3f52efd`.
Push, merge, deploy и новый candidate: **NOT_PERFORMED**.

Rollback source — отмена соответствующего scoped commit в своей feature branch;
UI/service identity protocol возвращать согласованной парой. Candidate.33 и
historical receipts сохранены; прежние release artifacts не переписаны.
Основной dirty checkout и чужие файлы не включены. Generated instruction files
marketing/AGENTS.md и CLAUDE.md и четыре line-ending-only client registrants
оставлены вне commit. Временные browser servers этой проверки остановлены;
логи и скриншоты сохранены.
