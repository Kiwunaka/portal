# A04 — отдельный AWG-ключ для каждого устройства

**PASS_BOUNDED / I3; полный A04 остаётся открытым.** Выполнение 8 сентября,
сверка и сохранение результатов 9 сентября 2026 года. Source parent `9081b96`;
196 исполненных runtime/shared файлов совпали с рабочими файлами при сохранении.
[Receipt](evidence/a04-key-isolation-20260908/receipt.json) содержит их manifest,
хеши изменённого кода, 43 файла evidence и ссылки на сохранённые локальные архивы.

## Исправление

Операторский binder копировал последний доступный AWG-ключ чужого устройства
и повторно provisioned material при выборе профиля, обновляя его возраст.
Read-only Brain audit подтвердил shared keys: по одному ключу в каждом из
AWG2/AWG3.1 использовалось семью активными bindings. Production не изменялась.

Теперь replacement привязывает вычисленный X25519 public key к исходной паре
`tg_id/install_id` внутри протокола, включая сохранённую историю. Изменение
адреса или clamped private bit не обходит привязку. Отозванный ключ нельзя
выдать повторно даже тому же устройству. PostgreSQL advisory transaction lock
сериализует конкурирующую первую выдачу одного ключа разным устройствам.
Ciphertext и история сохраняются; schema и dependencies не меняются.

Binder выбирает только готовый материал точного устройства по текущей policy.
Общий, просроченный или отсутствующий ключ блокирует выбор до изменений.
Повторный выбор не выдаёт материал заново и не обновляет его срок. Default
cleanup сохранён. Binder требует backend с новым модулем; его полный remote
PLAN на прежнем Brain не выполнялся. Извлечённая production selector function
проверена с реальными SQLite, crypto и readiness functions.

## Доказательства

- Шесть исходных regression FAIL сохранены. Focused suite: 92 PASS и 12
  подтестов; backend suite: 175 PASS и 8 подтестов; auth/payment suite: 138
  PASS и 22 подтеста, 19 deprecation warnings; scripts router: 44 PASS и
  21 подтест. Полные команды двух долгих suites не записаны в их логах;
  результаты сохраняются как имеющиеся, команды задним числом не восстановлены.
- PostgreSQL 16.15 / READ COMMITTED: четыре гонки AWG2/AWG3.1 × commit/rollback.
  `pg_blocking_pids` подтвердил ожидание. После commit второй владелец получает
  `material_key_already_bound`; после rollback второй запрос создаёт единственную
  строку. Изменённый clamped bit и сохранность committed ciphertext проверены.
- Реальный ASGI API и отдельные PostgreSQL fixture accounts: 46 HTTP assertions.
  L3 guard, подтверждённая выдача, idempotent repeat, отказ чужому и отозванному
  ключу, device bearer manifest и HTTP revoke проверены. Повторная авторизация
  выполнялась fixture-вызовом source service, не внешним email flow.
- Exact Core `02a091c`, ARM64 binary `0f1d7356…482fb08`, owned RU Pi → owned DE:
  десять authenticated exchanges и четыре ожидаемых отказа старого ключа.
  Отзыв A не прерывает B; новый ключ C работает, старый A остаётся недоступным.
  HTTP-профиль A возвращает 401 до удаления peer тестовым контроллером.
  Проверен MTU 1280; полная MTU/device/origin matrix этим не закрывается.

Команды выполненного bounded сценария из `E:/r12-a04-key-isolation-20260908`:

```powershell
python -B prepare-pg-keys.py
python -B run-pg-keys.py
python -B run-http-peer-lifecycle-v3.py awg2
python -B run-http-peer-lifecycle-v3.py awg31
python -B audit-and-stop-lab.py
python -B retain.py
```

Focused command из platform root:

```powershell
python -B -m pytest -p no:cacheprovider tests/test_awg2_lab_service.py tests/test_awg31_lab_service.py tests/test_owned_awg_ops_gap.py tests/test_remote_bind_owned_awg_lab_device.py -q
```

## Ошибки fixture и очистка

V1 остановился из-за отсутствия `httpx2` для TestClient до выдачи материала.
Зависимости fixture взяты из текущего local environment в отдельный guest
каталог, с manifest; общий venv не менялся. V2 пропустил обязательный `now`
в вызове fresh auth после успешных первых шагов; частичный результат и cleanup
сохранены. V3 использовал новые fixture DB и завершил оба протокола. Старые
результаты не перезаписывались и не считаются успешными полными прогонами.

DE configuration files, исходные peers и counters до/после совпали. Временные
peers и Pi binary удалены. Guest runners отсутствовали, API/bot/worker inactive,
VM выключена. Сохранены пять новых fixture DB: успешные HTTP DB имеют ноль
active material; synthetic race DB и частичная V2 сохраняют свои строки.
Старые БД не пересоздавались. Секреты реальных peers передавались только в памяти
и stdin; raw material и captured Core output не сохранены, их hashes сохранены.

## Остаток

Это доказательство изоляции ключей и управляемого тестового lifecycle.
**Продукт ещё не удаляет peer автоматически после device revoke или expiry.**
Существующие общие lab keys требуют отдельной миграции перед selective revoke.
Installed Android/Windows revoke/expiry, integrated quality для нового source
и остальные условия выпуска открыты. Прежний quality PASS для `16407b8`
не переносится на новые runtime files. Push, deploy и новый candidate в этом
срезе не выполнялись.

После сохранения 9 сентября: `python -B -m pytest -p no:cacheprovider
tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q`
— 33 PASS; `python -B scripts/agent_context_packet_audit.py
--platform-context-root .` — PASS; `python -B
docs/developer/work-orders/2026-09-05--consolidated-release-and-post12/validate_package.py`
— 83 R12 IDs, 378 legacy IDs и 388 local links PASS; `git diff --check` — PASS.
