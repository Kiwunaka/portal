# Итоговый отчёт PORTAL

Обновлено: 7 марта 2026

## Что было сломано

- Channel guard пропускал revoke при `left/kicked`.
- FreeKassa invalid callback мог ломать последующий valid callback с тем же `external_id`.
- Public campaign checkout выдавал broken link без `checkout_ticket`.
- WebApp legal links вели во внутренние несуществующие маршруты.
- Admin panel плохо объясняла `403` и истёкшую сессию.
- Deploy chain мог не доставлять collector для `portal-node-metrics.service`.
- Opening bonus пересекался с state channel bonus.

## Что исправлено

- Добавлен compat env-флаг `SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED`.
- Subscription endpoint теперь явно контролирует numeric fallback и логирует его.
- FreeKassa callback persistence обновляет invalid event до valid, а не блокирует его.
- `claim_channel_bonus` теперь возвращает реальный `sync_ok` после panel sync.
- Marketing home переведён в `bot-first`.
- Admin campaign link builder возвращает safe fallback вместо broken checkout.
- WebApp legal links переведены на absolute marketing URLs.
- Admin layout получил понятные состояния доступа.
- Маркетинговые CTA и legal-экраны приведены к одному bot-first сценарию без тупикового checkout.
- Public checkout без `checkout_ticket` теперь работает как управляемый gateway, а не как сломанный disabled-flow.
- WebApp entry больше не показывает misleading кнопку открытия кабинета до браузерной авторизации.
- QR-код в кабинете теперь генерируется локально, без внешнего `qrserver`.
- Deploy script копирует `collect_node_metrics.py` в brain runtime path.
- Opening bonus больше не резервирует `channel_bonus_claimed_at`.
- Static deploy для `marketing` и `webapp` переведён на атомарную схему через versioned releases и переключение symlink, чтобы убрать короткие окна `404`.
- Post-deploy verify теперь проверяет не только доступность доменов, но и ключевые UI-маркеры bot-first сценария.
- Добавлен отдельный `ui_visual_smoke` для контроля CTA, checkout fallback и локальной генерации QR без внешнего сервиса.
- Bonus audit trail выровнен для `channel bonus`, `promo redeem` и `gift redeem` в API/WebApp и bot-flow.
- `events_service` переведён на динамический `SessionLocal`, чтобы события и аналитика не терялись при reload/test bootstraps.
- `/admin/dashboard` теперь показывает bonus success/denied breakdown за 24 часа для channel/promo/gift flow.
- `PORTAL` получил взрослое управление нодами:
  - `drain node`
  - `controlled resync users`
  - `disable node`
- Источником истины по фактическим назначениям пользователей на ноды теперь явно считается `user_nodes`, а не legacy-логика "все enabled ноды".

## Что подтверждено проверками

- `python -m pytest tests/test_api_payments_callbacks.py tests/test_api_auth_and_tickets.py tests/test_bot_paywall.py tests/test_worker_retention.py -q`
- `python scripts/check-links.py`
- `python scripts/ui_visual_smoke.py`
- точечные проверки bonus event trail для API/WebApp и bot-flow добавлены в `tests/test_api_auth_and_tickets.py` и `tests/test_bot_paywall.py`
- дополнительно: build/smoke зафиксированы в release artifacts этой волны

## Что осталось в backlog

- дополнительный audit trail для части старых бонусных путей, которые всё ещё опираются на best-effort логирование
- более тонкая типографическая и copy-полировка marketing/webapp после закрытия функциональных UX-разрывов

## Дополнение: последний инженерный слой

- `/admin/dashboard` теперь показывает не только ошибки и бонусы, но и отдельный блок по удержанию:
  - кто истекает в ближайшие 3 дня;
  - сколько пользователей уже истекло за 7 дней;
  - сколько retention-писем/касаний реально ушло за последние 24 часа.
- `/admin/broadcast` теперь позволяет редактировать retention-шаблоны без бота:
  - welcome
  - T-3
  - T-1
  - T0
  - reactivation
- В infra/docs закреплён canary-подход:
  - любые transport/network изменения сначала на ограниченной группе;
  - `single_point_risk` и `free_node_enabled` считаются операторскими warning-сигналами, а не мелочами.

## Статус релиза

- 6 марта 2026 выполнен production rollout из чистого snapshot `HEAD`.
- Подтверждено после выкладки:
  - `portal-api`, `portal-bot`, `portal-helpbot` и `portal-node-metrics.timer` активны
  - `https://kiwunaka.space/api/health` отвечает `200`
  - `https://portal-privacy.online/` и `https://portal-privacy.online/webapp/` отвечают `200`
  - post-deploy verify прошёл зелёно и подтвердил bot-first UI-маркеры marketing/checkout
- В `origin/master` допушены последние коммиты Wave 4, включая защиту `CampaignSend` от duplicate race.

## Дополнение: runtime-аудит 7 марта 2026

- Production runtime использует `Postgres`, а не локальный SQLite как primary storage.
- Enabled delivery nodes в production DB: `free`, `it`, `nl`, `pl`, `us`.
- `brain` остаётся control-plane host и x-ui compatibility host, но выключен из текущего delivery pool.
- На `brain` built-in sub server `x-ui` отключён и перенесён с `2096` на `2097`; portal-owned subscription endpoint остаётся хозяином `:2096`.
- Старый `pl:8443` (`PL Free Reality`) выведен из эксплуатации и больше не считается рабочим runtime-контуром.
- `/api/admin/metrics/status` требует реальную Telegram admin auth; старые инструкции с plain `X-Admin-Id` устарели.
