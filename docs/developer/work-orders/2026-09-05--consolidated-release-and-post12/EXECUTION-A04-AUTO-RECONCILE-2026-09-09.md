# A04 — автоматический отзыв и expiry серверных AWG peers

**PASS_BOUNDED / I3; полный A04 открыт.** Source parent `0e829c9`.
В существующий worker добавлена периодическая сверка AWG2/AWG3.1 для явно
настроенных owned targets. [Receipt](evidence/a04-auto-reconcile-20260909/receipt.json)
сохраняет исходные результаты, scripts и manifest 198 runtime/shared files.
Manifest снят при сохранении результатов, а не перед исполнением; независимой
pre-execution фиксации всего source в этом прогоне нет.

## Поведение

Device/account revoke, entitlement expiry и предельный возраст material
запрещают доступ в БД до сетевого вызова. Worker удаляет отдельный peer из
сохранённой конфигурации и live interface через strict SSH. При сетевом сбое
или рестарте worker повторяет удаление по сохранённым revoked rows. Старый
rotated key без активной копии также закрывается от повторной выдачи. Общий
ключ разных устройств блокирует selective removal до миграции.

Используются существующий process, material history и advisory transaction
lock producer; новых таблиц, очередей или зависимостей нет. Серверный helper
проверяет identity интерфейса, сохраняет root-only preimage и сначала пишет
конфигурацию без отозванного peer. При ошибке live removal этот запрет остаётся
на диске. Сам helper не перезапускает интерфейс. Подключение описано в
[canonical operations owner](../../../operations/deployment-and-access.md#owned-awg-peer-revocation-worker).

## Проверки

Из platform root:

```powershell
python -B -m pytest -p no:cacheprovider tests/test_awg_lab_peer_worker.py tests/test_awg2_lab_service.py tests/test_awg31_lab_service.py tests/test_owned_awg_ops_gap.py tests/test_remote_bind_owned_awg_lab_device.py -q
python -B -m pytest -p no:cacheprovider portal_bot/tests/test_app_first_api.py portal_bot/tests/test_app_first_service.py tests/test_api_auth_and_tickets.py tests/test_subscription_preview_api.py tests/test_worker_retention.py -q
python -B -m pytest -p no:cacheprovider portal_bot/tests/test_app_first_api.py::test_start_trial_rate_limits_fresh_installs_by_origin -q
```

- Focused: 99 PASS + 12 subtests. Backend: 179 PASS + 8 subtests, один FAIL.
  Сохранённая synthetic DB показала запросы в соседних minute buckets:
  `21:43:59.860291` и `21:44:00.250969`. Тест теперь закрепляет часы для своих
  запросов; отдельный recheck — 1 PASS. Runtime rate limiter не менялся.
  Исходный FAIL сохранён; полного повторного backend suite не было.
- PostgreSQL 16.15 / READ COMMITTED: четыре producer/scanner races с реальным
  наблюдением блокировки и четыре entitlement/material-age expiry retry cases.
  Отказ фиксируется до simulated network failure, retry использует тот же key,
  ciphertext сохранён.
- Реальный source worker loop с test targets и isolated PostgreSQL удалил peers
  на owned DE. Exact Core `02a091c`, ARM64 binary `0f1d7356…482fb08`, owned RU Pi:
  десять authenticated exchanges и шесть ожидаемых no-outer-response отказов.
  A отозван, B продолжает работать; после рестарта test lab interface A запрещён,
  B подключается. Expired B затем запрещён, новый ключ A после fixture reauth работает.
  Шесть worker cycles и два idempotent retries проверены. MTU 1280.
- Linux helper failure fixture: disk denial сохраняется при live-command error,
  retry и повторное удаление корректны; чужой peer сохранён, wrong server identity
  отвергнута. Хеш helper в этом fixture относится к CRLF bytes, отправленным
  Windows `subprocess(text=True)`; retention проверяет эту точную трансформацию.

Внешние bounded fixture commands из `E:/r12-a04-auto-reconcile-20260909`:

```powershell
python -B run-pg.py
python -B run-server.py awg2
python -B run-server.py awg31
python -B check-persistence-failure.py
python -B audit-lab.py
python -B retain.py
```

Live fixture использует source service для синтетических device/entitlement
операций, а не HTTP или внешний email flow. Rollout policy задана fixture;
job, transaction, SSH removal и server persistence исполняются настоящим кодом.
Это current-origin control plane → owned DE, с отдельным RU-origin Core oracle.

## Ошибки и сохранность

Первый server fixture получил host-key mismatch при попытке согласовать
неприкреплённый Ed25519 ключ локальной VM. До DB/server mutation он не дошёл.
Повтор использовал RSA-SHA2-512 с прежним закреплённым RSA host key; known_hosts
не менялся. Исходные script/result сохранены. Проверка host key не отключалась.

Исходные server binaries, config bytes, static live config и peer identities
восстановлены. PIDs, counters и handshake timestamps изменились из-за намеренного
рестарта test interface; их неизменность не заявляется. Root-only rollback
preimages остаются на owned DE. Временные peers/Pi files удалены, VM выключена,
API/bot/worker на fixture inactive. Успешные live DB имеют ноль active material;
race DB сохраняет synthetic active/rotated rows. Старые БД не пересоздавались.

## Остаток

Permanent Brain worker activation, миграция прежних общих lab keys и installed
Android/Windows actual revoke/expiry остаются открытыми. Runtime diff ещё требует
обновлённой integrated quality; прежний PASS `16407b8` на него не переносится.
Production backend deploy, push и новый release candidate в этом срезе не выполнялись.
