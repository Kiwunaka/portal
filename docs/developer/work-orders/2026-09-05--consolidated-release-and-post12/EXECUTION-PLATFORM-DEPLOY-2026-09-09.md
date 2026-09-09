# Публикация platform и support integration — 2026-09-09

**Backend и static deploy PASS_BOUNDED; OIDC login и выпуск 1.2.0 открыты.**
Действия выполнены по [решению владельца](OWNER-DECISIONS-2026-09-09.md).
Сохранены [receipt и hashes](evidence/platform-deploy-20260909/receipt.json).

## Исходники и проверки

Support source `327736186562fb61b447510c39bc651a06747ca4` из отдельной
задачи включён через signed exact tree `a153364bc2930fd347dcdd5f1f14f8387ad0e1c8`,
[PR #244](https://github.com/Kiwunaka/portal/pull/244). После squash master:
`7d37005e4260995ab44ec3adb14bbffa3d42738b`, tree
`948de00b12c0fdfcca541b6206dbe8de5212c7dc`, parent `0392052`.
Подпись и равенство tree проверены. PR contract `34310349863`, Guardrails
`34310349886`, обычные push contract `34311062854` и Guardrails `34311062866`
PASS. `release-base-isolation` неприменим к этому PR и SKIPPED.

Из clean `E:/r12-integrated-platform-20260909` выполнено:

```text
python -B -m pytest -p no:cacheprovider portal_bot/tests/test_app_first_api.py portal_bot/tests/test_app_first_service.py tests/test_api_auth_and_tickets.py tests/test_subscription_preview_api.py tests/test_support_case_context.py tests/test_helpbot_lifecycle.py -q
```

PASS: 164 tests и 8 subtests, 921.71 s. Новый payload: 204 файла,
6 263 247 bytes; девять runtime support deltas. Шесть schema/dependency inputs
не изменились относительно rehearsed baseline. Frontend/shared/copy inputs
идентичны `0392052`; сохранённые frontend builds относятся именно к нему.
Полный 15-step gate на `7d37005` заново не запускался; прежний PASS переносится
только на неизменные frontend inputs, backend проверен приведённой командой.

## Production backend

Из clean `7d37005` запущен `python -B scripts/remote_deploy_brain_portal_code.py
--brain-ip 82.21.114.104 --passwords <existing owner password file>
--backup-retain-count 50`: exit 0. Штатные staged compile/JSON/dependency/import,
promotion/restart и delayed health прошли. Backup:
`/root/portal_bot.deploy-backups/20260909T043813Z-38516`; прежние пять сохранены.
Все 204 installed file hashes совпали с payload. API, bot, helpbot, feedbackbot,
worker active, NRestarts=0. Rollback не потребовался.

На сервере инициализированы отсутствовавшие commercial HMAC key и отдельный
operator session key, production environment и exact admin origins/callback.
Исходные `.env` bytes сохранены, mode 0600; секреты не экспортировались.
Синтетический base quote прошёл проверку HMAC, TTL 600, private/no-store;
reservation, order и provider operation не создавались. Build identity API
закреплена за `7d37005` и фактическим временем deployment. Для активации metadata
API отдельно перезапущен: PID 4190076, active, NRestarts=0; четыре других PID
сохранились. `/api/admin/v2/meta` подтвердил commit и schema `admin-v2.1`.
DB schema/client/Core metadata поля остались null и не объявлены проверенными.

Support получает owner-bound context и очищенный локальный OCR, не исходные
attachments. [Проверки support](evidence/platform-deploy-20260909/support-checks/CHECKS.md)
и [live readback](evidence/platform-deploy-20260909/support-checks/live-smoke.json)
сохранены отдельно. Model schema/core facts PASS, но экспериментальная модель
добавила лишний совет повторного входа: полного semantic quality PASS нет.
End-user Telegram delivery — MANUAL_OWNER_TEST. Сообщения клиентам не отправлялись.

## Static sites и оператор

Перед штатным prune все пять прежних static releases сохранены в
`/root/backups/r12-static-20260909/static-releases-before-cutover.tar.gz`:
80 110 392 bytes, SHA-256
`c37e27b6d0cb84a1aa561ae5a9313c0cb67fc1a4c70862a04289d99ef7dcfacd`.
Проверены все archive members и исходные pointers.

Из clean `E:/r12-promoted-platform-20260909` (`0392052`) выполнены plan-only,
затем `python -B scripts/remote_deploy_brain_static_sites.py --brain-ip
82.21.114.104 --passwords <existing owner password file>`: exit 0.
Новый release `20260909045925`, 887 файлов / 34 921 034 bytes. Все remote hashes
совпали; три pointers переключены. `adminapp.rollback` указывает на прежний
`20260819120323/adminapp`. Старый admin не имеет identity manifests: формальный
`--rollback-adminapp` для него неприменим без отдельного guarded pointer rollback.

[Current-origin readback](evidence/platform-deploy-20260909/static-deployed-verified-v2.json)
подтвердил HTTP 200 и exact file hashes для marketing, checkout, canonical
`app.pokrov.space`, admin root, `__build.json`, `__routes.json`; HTML revalidate
headers и API health PASS. Первая проверка ошибочно ожидала cabinet по
`pokrov.space/webapp/`; её FAIL сохранён, canonical host проверен отдельно.

Существующий guarded bootstrap создал owner operator/production superadmin.
Проверены Secure/HttpOnly/host-only cookie, auth/me и meta 200, anonymous 401,
foreign-origin unsafe POST 403, logout и отзыв всех тестовых sessions. Первый
probe неверно ожидал 403 для GET; FAIL сохранён, исправлена только проверка.
Operator/role сохранены; bootstrap не является внешним OIDC proof.

В Chrome новый admin отображается и кнопка OIDC выполняет переход. Telegram
возвращает `redirect_uri required` при переданном `https://admin.pokrov.space/`;
callback кабинета с теми же shared credentials открывает login page.
[Provider readback](evidence/platform-deploy-20260909/oidc-provider-entry.json)
сохраняет только безопасную проекцию. Вероятная причина — Allowed URLs у бота,
но настройка провайдера недоступна и не проверена. По
[документации Telegram](https://core.telegram.org/bots/telegram-login) callback
требует регистрации. Владельцу отправлен запрос добавить admin URL в BotFather.
Actual OIDC login/step-up остаются BLOCKED_BY_ACCESS/MANUAL_OWNER_TEST;
legacy bootstrap не отключён.

## Оставшаяся работа

AWG peer worker установлен как source, но targets не активированы. Прежние
shared keys требуют миграции eligible owned devices и проверки peer bindings
до permanent activation. Новый client candidate, installed-client matrix,
RU-origin и полная release acceptance остаются открытыми. Этот deployment
не меняет public client version и не означает завершения сводного плана.
