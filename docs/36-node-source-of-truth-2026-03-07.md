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
| `free` | отдельный free-пул | `enabled=true` | `443` | физически это `NLfree`, но логически это отдельный free-контур |
| `it` | paid delivery | `enabled=true` | `443` | рабочая нода |
| `nl` | paid delivery | `enabled=true` | `443` | отдельная premium-нода в NL |
| `pl` | paid delivery | `enabled=true` | `443` | рабочая нода |
| `us` | paid delivery | `enabled=true` | `443` | рабочая нода |

## Что считать legacy

- `pl:8443` с remark `PL Free Reality` был legacy/manual contour на сервере `pl`.
- На 2026-03-07 он выведен из эксплуатации:
  - inbound `id=2` отключён;
  - UFW-правила на `8443/tcp` удалены.
- До финального удаления из `x-ui.db` его считаем disabled legacy row, а не рабочим контуром.

## Важное про free-ноду

- В текущем runtime free-контур живёт как код `free`.
- Физически free-хост размещён в NL на отдельном сервере `NLfree`.
- Это не меняет runtime-модель: для control-plane и подписок это отдельная нода `free`, а не `pl_free`.

## Физическая карта серверов

| Физическое имя | Логический код | Страна | Назначение |
|---|---|---|---|
| `BRAINnode` | `brain` | DE | control-plane |
| `PLnode` | `pl` | PL | premium delivery |
| `ITnode` | `it` | IT | premium delivery |
| `NLnode` | `nl` | NL | premium delivery |
| `USnode` | `us` | US | premium delivery |
| `FREENLnode` | `free` | NL | free delivery |

## Операторский доступ

- `brain`, `pl`, `it`, `us` и `free` подтверждённо доступны локальным ops-скриптам через key-based auth.
- Для `free` старый пароль из inventory больше не считается основным способом доступа.
- В локальных скриптах добавлен key-fallback по `.ppk`, чтобы `free` не выпадала из диагностики.
- `nl` как отдельный premium-server остаётся в runtime-реестре, но его direct local SSH-path стоит перепроверить отдельно, если понадобится ручной root-доступ именно с этой машины.

## Что больше не считать актуальной схемой

- `pl_free` как текущую штатную запись в `nodes`
- `brain` как активную delivery-ноду
- SQLite как production source of truth
- встроенный subscription server `3x-ui` как источник пользовательских подписок
