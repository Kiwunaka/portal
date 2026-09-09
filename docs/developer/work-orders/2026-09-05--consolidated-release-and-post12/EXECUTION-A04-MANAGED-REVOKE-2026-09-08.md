# A04 — отозванное устройство не восстанавливает lab material

**IMPLEMENTATION_VERIFIED / I3; обязательные router gates PASS.**
Исправлена database-часть device revoke и account lockdown для AWG2/AWG3.1/HY2.
Полный A04 остаётся открытым: удаления уже выданного server peer этот commit
не выполняет и не доказывает.

## Воспроизведённые дефекты

Пять отрицательных проверок до исправления:

- три protocol cases оставляли material активным после device revoke;
- account lockdown также сохранял активный material отозванного устройства;
- L3 material intent возвращал HTTP 200 для отозванного canonical device,
  если его install ID совпадал с оставшимся `User.app_install_id`.

Теперь device revoke и lockdown блокируют и помечают активные material rows
для соответствующего account/install как `revoked` в той же транзакции.
Ciphertext, hashes и прежние записи ротации сохранены; другие устройства и
аккаунты не затрагиваются. Повторный fresh login может восстановить доступ
к аккаунту, но не активирует отозванный материал. Повтор revoke сохраняет
первый timestamp. Откат транзакции откатывает также invalidation material.

Для canonical account операторский intent требует активную, неотозванную
запись `AccountDevice`. Совпадение с legacy-полем её не заменяет. Legacy
операторский случай без canonical account не менялся; consumer managed
issuance по-прежнему требует действующий device claim.

HY2 включён в исправление, поскольку тот же отрицательный тест воспроизвёл
тот же разрыв на общей границе отзыва устройства. WARP, entitlement dates,
protocol parameters, Core и client packages этим изменением не менялись.
Новых таблиц, endpoints, зависимостей или сетевых management services нет.

## PostgreSQL: отзыв против замены material

В прежней owned Ubuntu VM создана отдельная пустая БД
`portal_r12_a04_20260908_rehearsal`. Сохранённые БД и rollback archives не
пересоздавались. Тест использовал текущие `revoke_device`, material replacement
functions и operator intent state builders, отдельные DB connections и
реальные `pg_blocking_pids` readbacks.

Все шесть сценариев PASS: по два порядка для каждого из трёх протоколов.
При `revoke_first` выдача ждёт row lock, затем отклоняется с `invalid_target`.
При `replace_first` revoke ждёт, затем отзывает уже записанную новую generation.
Ciphertext прежних строк сохранён, повторный вход не оживляет material.

Первый запуск остановился до создания таблиц: isolated source archive не
содержал пакет `admin_v2`. Отдельным архивом добавлены шесть пропущенных файлов;
перед повтором проверено отсутствие таблиц в уже созданной fixture DB. Это
ошибка упаковки fixture, не результат product race. Исходный exit 1 и оба
source manifests сохранены.

Итоговый audit сверил 195 runtime/shared source files и 21 material row:
18 `revoked`, три `rotated`, ноль active. Других сессий этой fixture DB нет,
lab API/bot/worker не запущены, VM штатно выключена. SSH forwarding остаётся
на `127.0.0.1:55228`; protocol server DE и пользовательские устройства в
этих сценариях не использовались.

## Проверки и оставшаяся работа

Локальные auth/recovery/action-intent suites: **41 PASS**. Backend router:
**154 PASS и 8 подтестов**; auth/payment/lab router: **171 PASS и 22 подтеста**.
Docs contract suites: **33 PASS**; `agent_context_packet_audit.py
--platform-context-root .` — PASS. Точные команды, source hashes, исходные
пять ожидаемых FAIL и результаты PostgreSQL сохранены в
[receipt](evidence/a04-managed-revoke-20260908/receipt.json) и 24 файлах evidence.
Auth/payment suite выдала 19 deprecation warnings; ошибок нет.
Все 24 evidence-файла сохранены в Git побайтно. Runtime source hashes относятся
к исполненным рабочим файлам; Git нормализует CRLF в LF. Оба изменённых runtime
файла точно совпали с index после этой нормализации; оба SHA сохранены в receipt.

Canonical owners обновлены: `api-contracts.md` и
`app-first-and-bonus-flows.md`. Новая source-версия ещё не входит в ранее
проверенный integrated platform `16407b8`; его 15-step quality receipt не
считается проверкой этого изменения.

Следующий недостающий A04 результат — связь отзыва/expiry с фактическим
удалением уже выданного peer, вместе с device-bound server material и
installed-client реакцией. [Прямой server primitive](EXECUTION-A04-PEER-LIFECYCLE-2026-09-08.md)
проверен отдельно; изменение флага в БД не заменяет server enforcement.
Публичный scope, новый offline lease и release gate не расширялись.
Push, merge, production deploy, новый candidate и публикация не выполнялись.
