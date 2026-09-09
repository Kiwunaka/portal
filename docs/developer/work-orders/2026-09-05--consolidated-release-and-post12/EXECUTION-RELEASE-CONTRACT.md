# R12 — синхронизация release contract после N05

Дата: 2026-09-06. Source: `aff9653`. Результат: **PARTIAL / LOCAL PASS**.
Команды, source hashes и логи:
[evidence/release-contract-sync.json](evidence/release-contract-sync.json).

При переходе к G05/G07 обнаружено нарушение dependency-aware обновления G03:
после `9f48273` каталог ошибок изменился, но strict-v2 JSON Schema и текущая
synthetic fixture всё ещё содержали старый SHA. Валидатор правильно отклонял
старый digest; schema и fixture расходились с canonical owner. Before-run:
21 FAIL / 29 PASS, включая явную проверку schema/validator drift.

Обновлены только два текущих digest pin и инструкция canonical owner о совместном
обновлении. Валидация не ослаблена. После исправления release-handoff, remote
apply fixtures, release gate/orchestrator и script-manifest tests: **102 PASS,
21 subtests PASS**. Offline CLI принимает synthetic v2 fixture, exit 0.

Не изменены версия каталога, старые candidate handoffs, receipts и бинарники.
PASS synthetic fixture не означает создания кандидата. G03/G05/G07 целиком
не закрыты: metadata owners, exact binary provenance/license, hosted CI,
signing и release acceptance сохраняют свои gates. Push/merge/deploy нет.
Rollback — scoped source commit; сохранённая история остаётся неизменной.
