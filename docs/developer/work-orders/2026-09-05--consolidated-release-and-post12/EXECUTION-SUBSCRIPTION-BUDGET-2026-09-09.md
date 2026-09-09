# Ответ подписки при медленной статистике

PR #247 установлен на Brain: backend `d9b25839e4c9e1b816091af6701b3723d75aa8c7`.
Предыдущий запрос подписки занял 16,102 с при клиентском лимите 15 с. Маршрут
ожидал статистику панелей до возврата доступа, срока и привязанных аккаунтов.

Теперь необязательная статистика ограничена тремя секундами. При её отсутствии
ответ сохраняет данные подписки из БД и отдаёт `usage.source=unavailable`.
Отсутствующие счётчики не записываются как новое нулевое потребление free-доступа.
Новый запрос того же owned admin account: HTTP 200 за **3,215 с**, paidUnlimited,
положительный оставшийся срок и Telegram linked. Это brain-origin API readback;
повторная проверка физического Huawei пока BLOCKED_BY_ACCESS — телефон отключён
от ADB. Запрос не выдаётся за ответ bearer-сессии конкретного устройства.

## Проверка и поставка

- `python -B -m pytest -p no:cacheprovider portal_bot/tests/test_app_first_api.py portal_bot/tests/test_app_first_service.py tests/test_api_auth_and_tickets.py tests/test_subscription_preview_api.py tests/test_client_ui_api_additions.py -q`: **173 tests + 8 subtests PASS** за 902,94 с.
- Фокус на подписке: 3 PASS; документация: 33 PASS, context audit и diff check PASS.
- Два обязательных PR checks и два checks после слияния PASS. Подписанное дерево
  merge совпало с проверенным исходником. Skip release-base-isolation сохранён
  отдельно от этих четырёх успешных проверок.
- Штатный `remote_deploy_brain_portal_code.py --brain-ip 82.21.114.104 --backup-retain-count 50 --restart portal-api` с существующим закрытым password-файлом: exit 0.
  Backup `/root/portal_bot.deploy-backups/20260909T071838Z-24416` сохранён.
- До поставки 204 файла совпали с `876e78d`; после — с новым payload. Из runtime
  изменён только `portal_bot/api_client_routes.py`. Шесть входов схемы/зависимостей
  и frontend-входы не изменились. Миграция и выкладка статики не требовались.
- API health PASS; build metadata подтвердили новый commit. Остальные четыре
  units сохранили PID и остаются active с NRestarts=0. Bootstrap metadata session
  завершена logout; это не новая проверка внешнего OIDC.

[Receipt, команды и результаты](evidence/subscription-budget-20260909/receipt.json)
сохраняют исходные hashes и нормализацию CRLF→LF для Git. Локальный общий quality
проход из 15 шагов не повторялся для этого изменения. Новый client candidate,
публичный релиз и завершение всего плана этим результатом не объявляются.
