# G03 — классификация и перенос по значимым входам

**VERIFIED / I3 для G03; release acceptance остаётся открытой.**
Проверен исходный DoD G03: классификация runtime/build/config/harness/docs,
инвалидация по зависимостям, обоснованный перенос только при совпадении входов.
Он не требует создания финального кандидата; его device/channel matrix относится
к Q01–Q05. [Предыдущий срез](EXECUTION-G03.md) сохранён.

## Исправленный дефект

`infra/owned-smart-dns/` содержал runtime и зависимости, но общий префикс
`infra/` классифицировал их как deployment. Теперь Go source — `core_runtime`,
`go.mod` — `packaged_dependency_toolchain`, две config templates —
`profile_policy`; unit file остаётся `deployment_migration`.
Имена README/tests по-прежнему обрабатываются раньше runtime.

До изменения четыре subcases дали FAIL; после все пять тестов PASS.
Сохранены [before](evidence/g03-input-review-20260909/before.log) и
[after](evidence/g03-input-review-20260909/after.log). Неизвестный путь требует
ручного разбора. Path hint не устанавливает полноту зависимостей.

## Применение к текущим данным

[Review](evidence/g03-input-review-20260909/review.json) сохраняет полные SHA,
95 изменённых путей и Git blob hashes относительно последнего общего local
quality tuple: platform `235e8a4` → `af146a3` (85), client `5760f41` → `de5d478`
(8), Core `02a091c` → `c7a11f7` (2). В platform/client изменены evidence,
документы и правила хранения их bytes; Core изменил Apple build oracle и
release owner. Эта карта committed inputs исключает текущую G03-правку и
чужие dirty/untracked файлы; hash текущего classifier записан отдельно.

Четыре retained quality files побайтно совпали с исходным receipt. Для
ограниченного offline replay прежних static samples два evaluator source
среза выполнены одним явно записанным Python. Artifact здесь — файл samples,
configuration — budget contract, oracle — evaluator, scope — только offline
расчёт; toolchain, environment и origin заданы отдельно.
Все значимые inputs совпали. Оба расчёта дали точно прежний JSON: 9/9 stop
checks PASS, пять target-значений не достигнуты. Перенос одобрен **только для
расчёта по сохранённым samples**. Нового asset collection или замера нет;
исходные source/environment/time в evidence не изменены.

Реальное изменение classifier проверено на одном и том же source inventory:
компаратор вернул `INVALIDATED`, единственная причина — `inputs.oracle`.
Прежнее имя файла и неизменный runtime не скрыли смену интерпретации.
Missing hashes/config/origin продолжают отказывать в переносе по существующим
regression tests. Равные declared inputs сами по себе никогда не дают release PASS.

Общий local-quality/preflight **не перенесён**: изменились docs/seed/release
inputs, а текущий Core HEAD отличается от закреплённого в client seed.
Device/runtime evidence также не перенесено без текущих server/config/device
и freshness inputs. Полнота зависимостей остаётся явной обязанностью review,
а не заявленным свойством эвристики путей.

## Команды и границы

```powershell
python -B -m unittest discover -s docs/developer/work-orders/2026-09-05--consolidated-release-and-post12 -p test_evidence_inputs.py -v
python -B E:/r12-g03-infra-classifier-20260909/review.py
```

Исходник [review.py](evidence/g03-input-review-20260909/review.py) и точные
команды двух evaluator executions сохранены в review JSON. Helper — receipt
конкретного аудита, не новый release gate. Продуктовый runtime не менялся;
сборка, устройства, production и публикация в этом срезе не запускались.

Repository checks PASS: `python -B -m pytest -p no:cacheprovider
tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q`
— 33 tests; `python -B scripts/agent_context_packet_audit.py
--platform-context-root .` — PASS; package `validate_package.py` — 83 R12,
378 legacy IDs, 424 links; `git diff --check` — PASS.
