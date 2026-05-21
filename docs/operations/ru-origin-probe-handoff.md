# Передача для RU-origin probe

Last updated: 2026-04-15

## Зачем нужен этот файл

Используйте эту инструкцию, когда для релиза или разбора инцидента нужно реальное подтверждение доступности из RU-origin.

Предпочтительный RU probe host сейчас `mini` / `RFMINI`: это канонический RU-origin operator sandbox. Если TCP до `mini` есть, но SSH auth не проходит, фиксируйте `RU-origin check: BLOCKED_BY_ACCESS`, а не отсутствие RU-origin.

## Когда сразу останавливаемся

Сразу считаем RU-origin visibility degraded, если нет хотя бы одного пункта:

- рабочего внешнего RU-host
- возможности запустить probe именно с этого хоста
- сырого JSON-результата probe
- короткого отчёта для оператора

Нельзя писать `RU-origin check: pass`, если probe реально не запускался с рабочего RU-host.

## Что нужно получить от вас

- имя RU probe host:
  - обычно `mini`
  - если его нет, тогда имя заменяющего RU-host
- публичный IP probe host, если вы его знаете
- reserve host, сейчас это `rf1.pokrov.space`
- путь, куда сохранять JSON-отчёт

## Что делать по шагам

1. Проверьте, жив ли `mini` / `RFMINI`.
2. Если TCP до `mini` есть, но SSH auth не проходит, зафиксируйте `RU-origin check: BLOCKED_BY_ACCESS` и обновите credential/authorized_keys.
3. Если `mini` недоступен, сразу зафиксируйте, что RU-origin observability degraded, и укажите replacement host, если он есть.
4. Запустите probe:

```powershell
python scripts/ru_probe_runner.py --reserve-host rf1.pokrov.space --probe-host mini --out ops-local/ru-probe.json
```

4. Соберите короткий операторский отчёт:

```powershell
python scripts/render_ru_probe_report.py --input ops-local/ru-probe.json
```

5. Прочитайте отчёт до того, как писать handoff.
6. Правильно классифицируйте результат:
   - проблема probe host
   - проблема canonical host
   - проблема foreign edge
   - проблема EU-node
7. Из того же самого запуска запишите `xhttp_alive` и `hysteria_alive`.

## Что probe обязан показать

Из отчёта должно быть понятно:

- может ли RU-host открыть `google.com`
- открываются ли текущие публичные поверхности `POKROV`, если это нужно в проверке
- доступны ли целевые delivery nodes
- доступен ли reserve contour

Желательно сохранить и технические стадии:

- `DNS`
- `TCP/443`
- `TLS`
- HTTPS с большим телом ответа

## Что нужно прислать мне обратно

Пришлите:

- имя probe host
- его публичный IP, если известен
- путь к сырому JSON
- путь к готовому отчёту или сам короткий summary
- открывался ли `google.com`
- краткий итог по нодам
- статусы `xhttp_alive` и `hysteria_alive`
- итоговую `probe_classification`

## Как именно писать итог в handoff

Используйте одну из этих форм:

- `RU-origin check: pass`
- `RU-origin check: fail`
- `RU-origin check: unavailable`

Если `unavailable`, сразу дописывайте причину:

- `mini down`
- `no replacement RU host`
- `probe host could not reach google.com`

## Частые причины блокировки

- `mini` не работает и нет замены
- RU-host не открывает `google.com`
- probe запускали локально или с `brain`, а не из RU
- есть только сырой JSON, но никто не собрал и не прочитал summary
- кто-то пытается делать вывод по RU из `current-origin` или `brain-origin`, не имея реального RU probe

## Связанные инструкции

- [Monitoring And Visibility](C:/Users/kiwun/Documents/ai/VPN/docs/operations/monitoring-and-visibility.md)
- [Передача по финальным ссылкам и релизному handoff](C:/Users/kiwun/Documents/ai/VPN/docs/operations/release-links-and-final-handoff.md)
- [Deployment And Access](C:/Users/kiwun/Documents/ai/VPN/docs/operations/deployment-and-access.md)
