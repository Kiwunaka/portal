# Локальный gate исправленного комплекта

**PASS_LOCAL_ONLY**, 2026-09-08 14:03 UTC: platform `16407b8`, client
`f479fd4`, Core `02a091c`. Все три source worktrees чистые. [Итоговый gate](evidence/integrated-current-quality-20260908/retry/010I-local-quality-gate.json)
содержит 15/15 PASS, `candidate_proven=false` и
`promotion_status=MANUAL_OWNER_TEST`. Новый кандидат, push и deploy не выполнены.

Исправление client уже входит в [актуальные пять пакетов](evidence/integrated-acceptance-20260908/inputs-access-denial.json).
Этот запуск обновляет source-quality proof после изменения общего Dart-кода.
Он не переносит прежние device/network результаты на новые bytes.

Результаты: 473 app-shell Flutter tests, анализ без ошибок, client seed/docs,
69 cabinet E2E, webapp lint/build, marketing build/SEO/responsive/reduced-motion,
adminapp build и performance collection PASS. [Статический gate](evidence/integrated-current-quality-20260908/retry/010I-local-web-performance-gate.json)
прошёл 9/9 stop-пределов. Пять target-значений не достигнуты: JS всех трёх
поверхностей и images marketing/webapp. Regression с другим environment не
утверждается. [Чистый preflight](evidence/integrated-current-quality-20260908/preflight-clean.json)
для того же tuple: `READY_LOCAL_FREEZE`, 0 blockers, candidate не создан.

Первый preflight отказал из-за dirty tool worktree; повтор из чистого checkout
прошёл. Первый quality gate прошёл семь этапов и упал на webapp build:
Turbopack отверг node_modules junction за пределами checkout. Удаление junction
было отклонено автоматической проверкой (`blocked by policy`); исходные ссылки
сохранены. Создан отдельный чистый checkout с обычными каталогами зависимостей.
Оба первоначальных FAIL и успешный повтор сохранены в [receipt](evidence/integrated-current-quality-20260908/receipt.json).
Исправлений product source для этих двух ошибок окружения не потребовалось.

Установка `npm ci --no-audit --no-fund` использовала npm 11.7.0 / Node 24.15.0
и дала сохранённое предупреждение engines. Сам успешный gate выполнялся на
Node 22.14.0 / npm 10.9.2 с Flutter 3.38.5. Это фактический локальный toolchain,
не утверждение полного совпадения release toolchain или reproducible build.

Команда успешного повтора из `E:/r12-current-quality-platform-20260908`:

```powershell
python -B scripts/release_1_2_local_quality_gate.py --platform-root E:/r12-current-quality-platform-20260908 --client-root E:/r12-current-inputs-client-20260908 --core-root E:/r12core-implementation --evidence-dir E:/r12-integrated-acceptance-20260908/current-quality/retry
```

Windows actual revocation пока NOT_RUN. Отдельный clone сохранил 304 installed
hashes и прежние пользовательские данные, но первая установка завершилась
кодом 2 после UAC; наблюдался Enterprise Evaluation LicenseStatus 5 / grace 0.
Client evidence commit `5760f41`:
`POKROV-app/docs/operations/evidence/2026-09-08-r12-revocation-availability/`.
Владелец согласился подтвердить UAC вручную; повтор открыт и ожидает входа
в Windows. Результат первой попытки не заменяется будущим успехом. Android
denial на отдельном test login, actual revocation/expiry, оставшаяся network
matrix и внешние release gates остаются открытыми.

Проверки обновлённых документов: `tests/test_agent_docs_contract.py` и
`tests/test_agent_context_packet_audit.py` — 33 PASS; `agent_context_packet_audit.py`
— PASS; `validate_package.py` — 83 R12 IDs, 378 legacy IDs, 358 local links PASS.
Client seed/docs contracts PASS. `git diff --check` PASS в обеих ветках;
`artifacts/releases/**` не менялись. Runtime source совпадает с проверенным
tuple; коммиты этого шага содержат только документацию и retained evidence.
