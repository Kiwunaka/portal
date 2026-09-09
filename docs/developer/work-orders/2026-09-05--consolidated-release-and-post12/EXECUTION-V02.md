# R12-V02 — достоверная сводка диагностического пакета

Дата: 2026-09-06. Статус: **I3 / PARTIALLY_FIXED**.
Проверка выполнена на local Windows host, `current-origin`, с синтетическими
пакетами и SQLite. Точный source и результаты:
[evidence/v02-bundle-summary.json](evidence/v02-bundle-summary.json).
Source commit: `97a96eb`.

Проверки: 23 support-bundle/service PASS; 154 backend/API PASS и 8 subtests
PASS; 33 docs/context PASS; platform-context audit PASS. Валидатор пакета:
13 импортированных разделов, 83 R12 ID, 378 legacy ID, 159 ссылок PASS.

## Исправление

`_capture_operator_summary` заменял egress результат исходом последнего
служебного события. Поэтому успешная запись журнала могла превратить
`egress_state=failed` в `proof_outcome=succeeded`, а ошибка записи — скрыть
успешный egress. Три regression сценария воспроизвели эту подмену.

Теперь `proof_outcome` формируется только из `network/summary.json.egress_state`.
`unknown` остаётся `unknown`. Последние phase/error сохраняются отдельно из
событий; без событий они отсутствуют. Сокращённая схема не содержит attempt ID
или достоверного счётчика подключений: `observed_attempts=null`. Несколько
stage-start событий и недисконнектный snapshot не дают denominator.

Проверки проходят через обработку очереди, сохранение строки в БД и публичную
service projection для оператора. Отдельный summary-пакет без событий также
проверяет отсутствие выдуманного phase и счётчика.

Первый before-run и диагностический повтор отклоняли некорректную fixture:
последняя JSONL-запись не заканчивалась обязательным переводом строки. Они не
считаются подтверждением дефекта. После исправления JSONL второй before-run получил
три ожидаемых FAIL именно на ошибочном `proof_outcome`. Все логи сохранены.

## Граница результата

Это факты исторического opt-in пакета со слов клиента, а не live runtime proof.
Новый сбор данных и новая схема событий не вводились. Ранее сохранённые строки
БД не пересчитывались. Обновление существующих production данных не выполнено.

Общий V02 остаётся PARTIALLY_FIXED: полная correlation expected/effective/proven,
reason codes и live exact-candidate путь требуют дальнейшей проверки N01/N05 и
решения O03 об источнике допустимых per-device данных. Эти зависимости не
закрываются исправлением сводки.

Push, merge, deploy, новый release candidate и native builds не выполнялись.
Rollback — отмена scoped source commit; исторические evidence и candidate.33
сохранены. Concurrent marketing instruction files вне commit.
