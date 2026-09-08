# Текущий backend — совместная работа и откат API

**PASS_CURRENT_LOCAL_API_COMPATIBILITY**, current platform `16407b8`.
[Receipt, команды, source manifests и hashes](evidence/integrated-backend-compat-20260908/receipt.json).
Это применимая локальная compatibility-часть B08 для текущего комплекта;
production recovery и весь B08 не объявляются пройденными.

## Реальный предыдущий состав

Read-only проверка Brain установила PostgreSQL runtime и состав 197 файлов:
196 source-equivalent файлов из `f530005`, а `control_panel.py` из `1207b63`.
Единого deployed Git SHA нет. Между этими вариантами `control_panel.py` менялось
сохранение частичного provisioning progress; новая версия не разворачивалась.
Проверка исходников учитывает смешанные CRLF/LF, не скрывая различия байтов.
Экспорт каждого старого файла сначала подтвердил эквивалентность публичному
Git source, затем точный raw SHA работающего файла. Конфигурация, секреты и
данные пользователей не экспортировались. Текущий архив содержит 200 файлов
из Git objects `16407b8`; оба архива сохранены вне Git.

Шесть schema/bootstrap/dependency inputs (`models.py`, `migrations.py`, `db.py`,
`requirements.txt`, account foundation и support ownership backfills) совпадают
между фактическим старым составом и текущим. **Новой expand/contract migration
для этой пары нет**. Поэтому destructive contraction не добавлялась ради
формального PASS. Канонический rollback сохраняет additive schema и evidence.

## Исполненная проверка

В сохранённой Ubuntu VM создана отдельная PostgreSQL БД
`portal_b08_integrated_20260908_rehearsal` из прежней восстановленной synthetic
базы. Старые БД/архивы/VM не пересоздавались. Настоящие `uvicorn api:app`
выполнили imports, migrations и lifespan на `127.0.0.1:18083/18084`; systemd
ограничил доступ loopback. Provider I/O не выполнялся. Python 3.12.3 и общий
лабораторный venv; `pip check` PASS, без новой установки зависимостей.

| Фаза | Результат |
| --- | --- |
| Старая версия до новой | Health/plans 200, unauth ticket 401, authenticated ticket read/event write 200 |
| Старая и новая одновременно | Те же пять HTTP assertions на каждой версии, обе записи подтверждены SQL |
| Новая остановлена | Старая продолжает те же read/write paths без перезапуска |
| Старая перезапущена после новой | Новый PID, те же HTTP/SQL проверки, `NRestarts=0` |

Итого **25 HTTP assertions и пять отдельных event writes PASS**. Ticket и
attachment rows сохранены. Все **197 + 200 source hashes** совпали после прогона.
Схема после старого startup, нового startup и rollback одинакова: **1690 columns,
734 indexes, 246 constraints**. Сравнение с ORM-only восстановленной fixture
показало прежние 93 additive indexes и пять defaults уже при старом startup;
это существующий bootstrap, не schema delta новой версии.

Оба API остановлены; VM штатно выключена, SSH forwarding остался привязанным
только к `127.0.0.1`. Все source archives, БД и evidence сохранены. Production
изменений, deploy, push, нового кандидата или публикации не было.

## Оставшиеся границы

Actual old/current API compatibility на этой схеме больше не является
недостающей локальной проверкой. При новом schema-input diff её нужно оценить
заново. Исторические worker/poison/restore/deploy-failure результаты сохраняют
свои точные границы; generic «старое приложение на expanded schema» не требует
выдумывать отсутствующую миграцию для текущего rollout.

Открыты реальные объёмы/DDL locks, точный production process/dependency tuple,
actual production snapshot/attachment recovery, применимые bot/worker/provider
и финальные release gates. Brain read-only source identity не равна исполнению
current API на Brain; `RU-origin` этим стендом не подтверждён.

Документация: `python -B -m pytest -p no:cacheprovider
tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q`
— 33 PASS; `python -B scripts/agent_context_packet_audit.py
--platform-context-root .` — PASS; work-order `validate_package.py` — 83 ID,
378 legacy references и 344 local links PASS. Проверены 32 retained и пять
external файлов: SHA/size и JSON parsing PASS. Для evidence задано точечное
побайтное хранение Git, `git diff --check` PASS. Product code не менялся.
