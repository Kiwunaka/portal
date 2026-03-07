# Source of Truth по нодам и inbound'ам (2026-03-07)

Обновлено: 7 марта 2026

Этот файл — короткая актуальная правда по runtime-состоянию. Если dated-doc ниже в репозитории говорит иначе, для текущего production приоритет у этого файла, `docs/08-node-inventory.md` и `docs/35-node-runtime-and-panel-audit-2026-03-07.md`.

## Текущее состояние

- control-plane: `brain`
- delivery pool: `free`, `it`, `nl`, `pl`, `us`
- `brain` не участвует в пользовательской выдаче как delivery node
- основной пользовательский профиль один: `VLESS + TCP + Reality`
- основной рабочий inbound для delivery: `443`

## Таблица ролей

| Код | Роль сейчас | Статус в runtime DB | Основной inbound | Комментарий |
|---|---|---|---|---|
| `brain` | control-plane | `enabled=false` | `443`, но не используется для текущей выдачи | FastAPI, bot, worker, panel-control |
| `free` | отдельный free-пул | `enabled=true` | `443` | это отдельный runtime-код, а не `pl_free` |
| `it` | paid delivery | `enabled=true` | `443` | рабочая нода |
| `nl` | paid delivery | `enabled=true` | `443` | рабочая нода |
| `pl` | paid delivery | `enabled=true` | `443` | рабочая нода |
| `us` | paid delivery | `enabled=true` | `443` | рабочая нода |

## Что считать legacy

- `pl:8443` с remark `PL Free Reality` — это legacy/manual contour на сервере `pl`.
- Он не является текущим primary source of truth для пользовательской выдачи.
- Если он нужен дальше, его надо либо:
  - вернуть в runtime DB и sync policy как полноценный контур,
  - либо удалить как legacy после отдельной проверки, что на него никто не опирается.

## Важное про free-ноду

- В текущем runtime free-контур живёт как код `free`.
- Если физически free-хост размещён в NL, это инфраструктурный факт размещения, но не меняет runtime-модель: для control-plane и подписок это всё равно отдельная нода `free`, а не `pl_free`.

## Что больше не считать актуальной схемой

- `pl_free` как текущую штатную запись в `nodes`
- `brain` как активную delivery-ноду
- SQLite как production source of truth
- встроенный subscription server `3x-ui` как источник пользовательских подписок
