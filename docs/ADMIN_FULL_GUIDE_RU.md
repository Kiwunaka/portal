# ADMIN FULL GUIDE (RU)

РћР±РЅРѕРІР»РµРЅРѕ: 4 РјР°СЂС‚Р° 2026

## 1. РђСЂС…РёС‚РµРєС‚СѓСЂР°

### 1.1 РљРѕРјРїРѕРЅРµРЅС‚С‹
- `portal_bot/bot.py` вЂ” РѕСЃРЅРѕРІРЅРѕР№ Telegram-Р±РѕС‚ (РїРѕР»СЊР·РѕРІР°С‚РµР»СЊСЃРєРёРµ Рё Р°РґРјРёРЅ-СЃС†РµРЅР°СЂРёРё).
- `portal_bot/api.py` вЂ” FastAPI backend: checkout/callbacks, WebApp API, admin API, subscription endpoint.
- `portal_bot/worker.py` вЂ” С„РѕРЅРѕРІС‹Рµ Р·Р°РґР°С‡Рё (retention, watchdog, channel bonus guard, free cycle reset).
- `portal_bot/control_panel.py` + `portal_bot/panel_client.py` вЂ” СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ РєР»РёРµРЅС‚РѕРІ СЃ 3x-ui/Xray РїРѕ РЅРѕРґР°Рј.
- `webapp/` вЂ” Telegram Mini App (Next.js static export), РІРєР»СЋС‡Р°СЏ `/admin/*`.
- `marketing/` вЂ” Р»РµРЅРґРёРЅРі Рё checkout UX-СЃС‚СЂР°РЅРёС†С‹.
- Р‘Р”: SQLite (`portal.db`) СЃ РјРёРіСЂР°С†РёСЏРјРё РІ `portal_bot/migrations.py`.

### 1.2 РќРѕРґРѕРІР°СЏ СЃС…РµРјР°
- Control plane (`brain`): API, bot, worker, helpbot, Caddy, Р‘Р”, orchestrator-СЃРєСЂРёРїС‚С‹.
- Data plane (`us`, `pl`, `it`, `free`): 3x-ui/Xray inbounds.
- Р›РѕРіРёРєР° СЃРѕРІРјРµСЃС‚РёРјРѕСЃС‚Рё: РµСЃР»Рё С‚Р°Р±Р»РёС†Р° `nodes` РїСѓСЃС‚Р°, СЂР°Р±РѕС‚Р°РµС‚ legacy single-node fallback.

### 1.3 РџРѕС‚РѕРє РґР°РЅРЅС‹С… (РѕСЃРЅРѕРІРЅРѕР№)
1. РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ РїСЂРёС…РѕРґРёС‚ РІ Р±РѕС‚ / WebApp.
2. API РІР°Р»РёРґРёСЂСѓРµС‚ Telegram initData / session token.
3. РџР»Р°РЅ/Р±РѕРЅСѓСЃ/РїСЂРѕРјРѕ РёР·РјРµРЅСЏСЋС‚ СЃРѕСЃС‚РѕСЏРЅРёРµ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ РІ Р‘Р”.
4. Control panel layer СЃРёРЅС…СЂРѕРЅРёР·РёСЂСѓРµС‚ РєР»РёРµРЅС‚Р° РІ 3x-ui (enable/disable/subId/token).
5. РљР»РёРµРЅС‚ РїРѕР»СѓС‡Р°РµС‚ РїРѕРґРїРёСЃРєСѓ С‡РµСЂРµР· `/s8Kx2mP7qR4wT/{token}`.

## 2. ENV-РїРµСЂРµРјРµРЅРЅС‹Рµ (РїРѕР»РЅС‹Р№ СЃРїРёСЃРѕРє)

РСЃС‚РѕС‡РЅРёРє РёСЃС‚РёРЅС‹: `portal_bot/.env.example`, `portal_bot/config.py`, С„Р°РєС‚РёС‡РµСЃРєРѕРµ РёСЃРїРѕР»СЊР·РѕРІР°РЅРёРµ РІ `portal_bot/*.py`, `webapp/src`, `marketing/src`.

### 2.1 Core / Bot / DB
- `BOT_TOKEN`
- `BOT_USERNAME`
- `HELP_BOT_TOKEN`
- `LEGACY_BOT_TOKEN`
- `BOT_MIGRATION_TARGET_URL`
- `ADMIN_ID`
- `DATABASE_URL`
- `WORKER_EMBEDDED`
- `PORT`

### 2.2 Domains / URLs
- `HOST_DOMAIN`
- `PUBLIC_API_DOMAIN`
- `PUBLIC_WEB_DOMAIN`
- `DOMAIN`
- `PUBLIC_API_BASE_URL`
- `WEBAPP_URL`
- `PAY_CHECKOUT_URL`
- `CHECKOUT_URL`
- `PAY_SUCCESS_URL`
- `PAY_FAIL_URL`
- `PAY_RESULT_BASE_PATH`
- `PAY_REFUND_BASE_PATH`
- `PAY_CHARGEBACK_BASE_PATH`

### 2.3 Panel / Node / VLESS
- `PANEL_URL`
- `PANEL_USER`
- `PANEL_PASS`
- `PANEL_PATH`
- `INBOUND_ID`
- `INBOUND_ID_BACKUP`
- `VLESS_PORT`
- `VLESS_SNI`
- `VLESS_PBK`
- `VLESS_SID`
- `VLESS_FP`
- `VLESS_FLOW`
- `LEGACY_NODE_CODE`
- `LEGACY_NODE_NAME`
- `PANEL_ONLINE_RECENT_SECONDS`

### 2.4 Checkout / FreeKassa / Callback Security
- `RUB_CHECKOUT_ENABLED`
- `BOT_RUB_BUTTON_ENABLED`
- `CHECKOUT_WIDGET_ENABLED`
- `PAYMENT_CALLBACK_TOLERANT_MODE`
- `CHECKOUT_TICKET_SECRET`
- `CHECKOUT_TICKET_TTL_SECONDS`
- `FK_SITE_SHOP_ID`
- `FK_SITE_API_KEY`
- `FK_SITE_SECRET_WORD_1`
- `FK_SITE_SECRET_WORD_2`
- `FK_BOT_SHOP_ID`
- `FK_BOT_API_KEY`
- `FK_BOT_SECRET_WORD_1`
- `FK_BOT_SECRET_WORD_2`
- `FK_API_BASE_URL`
- `FK_NOTIFY_IP_ALLOWLIST`
- `FREEKASSA_NOTIFY_URL`
- `CARDLINK_SIGNING_SECRET`
- `FREEKASSA_SIGNING_SECRET`
- `AAIO_SIGNING_SECRET`

### 2.5 Support / Public channels
- `SUPPORT_USERNAME`
- `SUPPORT_BOT_USERNAME`
- `PUBLIC_CHANNEL`
- `NEWS_CHANNEL_ID`
- `HELPBOT_START_MEDIA_PATH`
- `HELPBOT_START_MEDIA_TYPE`

### 2.6 Plans / Limits / Loyalty
- `FREE_LIMIT_IP`
- `PAID_LIMIT_IP`
- `FREE_TOTAL_GB`
- `FREE_SPEED_LIMIT_KBPS`
- `FREE_SPEED_BUMP_UNSUB_KBPS`
- `CHANNEL_SPEED_BUMP_ENABLED`
- `AUTO_FREE_DAYS`
- `FREE_CYCLE_DAYS`
- `REFERRAL_BONUS_DAYS`
- `REFERRAL_TIERS`
- `POINTS_MONTHLY_CAP`
- `POINTS_EXPIRY_DAYS`
- `POINTS_PLAN_CAP_RATIO`
- `TOTAL_DISCOUNT_CAP_RATIO`
- `STACK_TOTAL_DISCOUNT_CAP`

### 2.7 Campaign / Bonus flags
- `OPENING_PREMIUM_DAYS`
- `OPENING_PREMIUM_START_CODE`
- `OPENING_PREMIUM_CAMPAIGN_KEY`
- `FRIEND_GIFT_DAYS`
- `FRIEND_GIFT_CAMPAIGN_KEY`
- `CHANNEL_PREMIUM_DAYS`
- `CHANNEL_SUBSCRIBER_CAMPAIGN_KEY`
- `START99_WELCOME_ENABLED`
- `START99_WELCOME_MIN_HOURS`
- `START99_WELCOME_MAX_HOURS`
- `START99_WELCOME_DISCOUNT_PCT`
- `START99_WELCOME_DISCOUNT_CODE`
- `RETENTION_TEMPLATE_CACHE_TTL_SECONDS`

### 2.8 Family / UX / Session / UI toggles
- `FAMILY_SLOT_STARS`
- `FAMILY_SLOT_DAYS`
- `FAMILY_SLOT_MAX`
- `WEBAPP_SESSION_SECRET`
- `WEBAPP_SESSION_TTL_SECONDS`
- `TELEGRAM_WEB_LOGIN_SECRET`
- `TELEGRAM_WEB_LOGIN_MAX_AGE_SECONDS`
- `WEBAPP_ENABLE_HAPTIC`
- `WEBAPP_ENABLE_LOTTIE`
- `WEBAPP_DEV_AUTH`
- `WEBAPP_DEV_TG_ID`
- `BOT_AUTO_DELETE_SECONDS`
- `TG_BTN_EMOJI_PRIMARY_ID`
- `TG_BTN_EMOJI_SUCCESS_ID`
- `TG_BTN_EMOJI_DANGER_ID`

### 2.9 WebApp / Marketing (frontend env)
- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_TELEGRAM_LOGIN_BOT`
- `NEXT_PUBLIC_ENABLE_QA_OVERLAY`
- `NEXT_PUBLIC_ENABLE_LEGACY_PORT_FALLBACK`
- `VITE_PUBLIC_API_BASE_URL`
- `VITE_TELEGRAM_LOGIN_BOT`
- `VITE_ENABLE_LEGACY_PORT_FALLBACK`
- `NEXT_PUBLIC_TELEGRAM_BOT_URL`
- `NEXT_PUBLIC_WEBAPP_URL`
- `NEXT_PUBLIC_CHECKOUT_PAGE_URL`
- `NEXT_PUBLIC_NEWS_CHANNEL`
- `NEXT_PUBLIC_CONTACT_TG_URL`
- `NEXT_PUBLIC_CONTACT_EMAIL`
- `NEXT_PUBLIC_CONTACT_FORM_URL`
- `NEXT_PUBLIC_ENTERPRISE_EMAIL`
- `NEXT_PUBLIC_APP_ANDROID_PLAY_URL`
- `NEXT_PUBLIC_APP_ANDROID_APK_URL`
- `NEXT_PUBLIC_APP_ANDROID_MIRROR_URL`
- `NEXT_PUBLIC_APP_WINDOWS_EXE_URL`
- `NEXT_PUBLIC_APP_WINDOWS_MIRROR_URL`
- `NEXT_PUBLIC_APP_DOCS_URL`

## 3. РЈРїСЂР°РІР»РµРЅРёРµ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏРјРё (Р±РѕС‚ + API)

### 3.1 Р‘Р°Р·РѕРІС‹Рµ РѕРїРµСЂР°С†РёРё
- РЎРѕР·РґР°РЅРёРµ/РѕР±РЅРѕРІР»РµРЅРёРµ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ РїСЂРѕРёСЃС…РѕРґРёС‚ С‡РµСЂРµР· bot-flow Рё API auth/session.
- РђРґРјРёРЅ-РѕРїРµСЂР°С†РёРё:
  - `GET /api/admin/users`
  - `GET /api/admin/users/{tg_id}`
  - `POST /api/admin/users/{tg_id}/extend`
  - `POST /api/admin/users/{tg_id}/block`
  - `POST /api/admin/users/{tg_id}/regenerate-token`

### 3.2 Manual users
- РЎРѕР·РґР°РЅРёРµ manual-РїРѕР»СЊР·РѕРІР°С‚РµР»РµР№: `POST /api/admin/users/manual`.
- РџСЂРѕРґР»РµРЅРёРµ/Р±Р»РѕРєРёСЂРѕРІРєР°/regenerate token:
  - `/api/admin/users/{tg_id}/manual/extend`
  - `/api/admin/users/{tg_id}/manual/block`
  - `/api/admin/users/{tg_id}/manual/regenerate-token`

### 3.3 Subscription token
- Endpoint: `/s8Kx2mP7qR4wT/{token}`.
- Р Р°Р±РѕС‡РёР№ СЃС†РµРЅР°СЂРёР№:
  - РѕСЃРЅРѕРІРЅРѕР№ lookup РїРѕ `sub_token`;
  - fallback РїРѕ `tg_id`, РµСЃР»Рё token С‡РёСЃР»РѕРІРѕР№;
  - РїСЂРё inactive-user РѕС‚РґР°РµС‚СЃСЏ РїСѓСЃС‚РѕР№ РѕС‚РІРµС‚.
- Р”Р»СЏ РґРёР°РіРЅРѕСЃС‚РёРєРё РІ Р»РѕРіР°С… РµСЃС‚СЊ fingerprint С‚РѕРєРµРЅР° (Р±РµР· СѓС‚РµС‡РєРё СЃР°РјРѕРіРѕ С‚РѕРєРµРЅР°).

## 4. РЈРїСЂР°РІР»РµРЅРёРµ РЅРѕРґР°РјРё

### 4.1 РќРѕРґРѕРІС‹Рµ РѕРїРµСЂР°С†РёРё API
- `GET /api/admin/nodes/health`
- `POST /api/admin/nodes/sync`
- `GET /api/admin/nodes/traffic?from&to`

### 4.2 РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ РїРѕР»СЊР·РѕРІР°С‚РµР»РµР№ РІ panel
- РџСЂРёРЅС†РёРї: DB `sub_token` = panel client `subId`.
- РќР° create/renew/regenerate/panic РїСЂРёРЅСѓРґРёС‚РµР»СЊРЅРѕ СЃРёРЅС…СЂРѕРЅРёР·РёСЂСѓРµС‚СЃСЏ `subId`.
- РџСЂРё mismatch panel-РєР»РёРµРЅС‚ РѕР±РЅРѕРІР»СЏРµС‚СЃСЏ СЃ `subId` РёР· Р‘Р”.

### 4.3 Р РµРєРѕРјРµРЅРґСѓРµРјС‹Рµ РѕРїРµСЂР°С†РёРѕРЅРЅС‹Рµ РєРѕРјР°РЅРґС‹
- РџСЂРѕРІРµСЂРєР° РЅРѕРґ: `python scripts/remote_brain_nodes_sanity.py --brain-ip <ip>`
- РРЅСЃРїРµРєС†РёСЏ subscription hosts: `python scripts/remote_inspect_brain_subscription_hosts.py --brain-ip <ip> --domain <domain>`
- РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ РїРѕР»СЊР·РѕРІР°С‚РµР»РµР№: `python scripts/remote_sync_users_to_nodes.py ...`

## 5. РџР»Р°С‚РµР¶Рё (FreeKassa + Stars)

### 5.1 РћСЃРЅРѕРІРЅС‹Рµ РјР°СЂС€СЂСѓС‚С‹
- РЎРѕР·РґР°РЅРёРµ Р·Р°РєР°Р·Р° (auth): `POST /api/payments/freekassa/orders/create`
- РЎРѕР·РґР°РЅРёРµ Р·Р°РєР°Р·Р° (public СЃ checkout-ticket): `POST /api/payments/freekassa/orders/create-public`
- Callback: `POST|GET /api/payments/freekassa/notify`

### 5.2 РљР»СЋС‡РµРІС‹Рµ РїСЂР°РІРёР»Р°
- РџСЂРѕРІР°Р№РґРµСЂ RUB: FreeKassa (primary), Stars (secondary).
- РРґРµРјРїРѕС‚РµРЅС‚РЅРѕСЃС‚СЊ callback РѕР±СЏР·Р°С‚РµР»СЊРЅР°.
- Pending discount Р±РѕР»СЊС€Рµ РЅРµ СЃРїРёСЃС‹РІР°РµС‚СЃСЏ РЅР° СЌС‚Р°РїРµ create-order (С‚РѕР»СЊРєРѕ РїСЂРё СѓСЃРїРµС€РЅРѕР№ РѕРїР»Р°С‚Рµ).
- Р”Р»СЏ callback РґРѕРїСѓСЃРєР°РµС‚СЃСЏ РёР·РІР»РµС‡РµРЅРёРµ `us_tg_id` / `us_plan_code` РёР· notify payload (fallback).

### 5.3 Referral РІ РїР»Р°С‚РµР¶РЅРѕРј РїРѕС‚РѕРєРµ
- Р”Р»СЏ РїРµСЂРІРѕРіРѕ РїР»Р°С‚РЅРѕРіРѕ RUB-РїР»Р°С‚РµР¶Р° РїСЂРёРјРµРЅРёРј referral-discount.
- РџРѕСЃР»Рµ РїРµСЂРІРѕРіРѕ paid-РїР»Р°С‚РµР¶Р° СЃСЂР°Р±Р°С‚С‹РІР°РµС‚ bonus РґР»СЏ РёРЅРІР°Р№С‚РµСЂР°.

## 6. Р‘РѕРЅСѓСЃРЅР°СЏ СЃРёСЃС‚РµРјР°

### 6.1 Channel bonus
- Claim: `POST /api/bonuses/channel/claim`
- Guard РІ worker:
  - `left`, `kicked`, `not_member` РЅРѕСЂРјР°Р»РёР·СѓСЋС‚СЃСЏ РІ `not_member`.
  - revoke РІС‹РїРѕР»РЅСЏРµС‚СЃСЏ С‚РѕР»СЊРєРѕ РїСЂРё `normalized_reason=not_member`.
  - transient РѕС€РёР±РєРё Telegram/API РЅРµ РІС‹Р·С‹РІР°СЋС‚ revoke.
- РЎС‚СЂСѓРєС‚СѓСЂРЅС‹Рµ Р»РѕРіРё: `user_id`, `raw_status`, `normalized_reason`, `action`.

### 6.2 Referral / Welcome links / Campaign links
- Start links: `GET/POST/PATCH/DELETE /api/admin/start-links`
- Campaign links builder: `POST /api/admin/campaign-links/build`
- РћРіСЂР°РЅРёС‡РµРЅРёРµ Telegram payload: РјР°РєСЃРёРјСѓРј 64 СЃРёРјРІРѕР»Р°, СЃ РІР°Р»РёРґР°С†РёРµР№.

### 6.3 Promos / Gift
- Promo CRUD: `GET/POST/PATCH/DELETE /api/admin/promos`
- Gift codes: `GET/POST /api/admin/gift-codes`
- РСЃРїСЂР°РІР»РµРЅРёСЏ:
  - unlimited promo (`uses_left=-1`) СЂР°Р±РѕС‚Р°РµС‚ РєРѕСЂСЂРµРєС‚РЅРѕ;
  - use-limit decrement СЃРґРµР»Р°РЅ СѓСЃР»РѕРІРЅС‹Рј Рё Р±РµР·РѕРїР°СЃРЅС‹Рј;
  - РґРѕР±Р°РІР»РµРЅ СѓРЅРёРєР°Р»СЊРЅС‹Р№ РёРЅРґРµРєСЃ РЅР° `promo_usage(tg_id, promo_code)`.

### 6.4 Wheel
- РљРѕРЅС„РёРі: `GET/PUT /api/admin/wheel-config`
- Cooldown С…СЂР°РЅРёС‚СЃСЏ РІ С‡Р°СЃР°С… (`cooldown_hours`, СЃС‚Р°РЅРґР°СЂС‚ 168h).
- Spin РІС‹РїРѕР»РЅРµРЅ Р°С‚РѕРјР°СЂРЅРѕ СЃ guard РїРѕ `last_wheel_spin`.

## 7. РџРѕРґРґРµСЂР¶РєР° (С‚РёРєРµС‚С‹ / helpbot)

### 7.1 API
- `POST /api/tickets`
- `GET /api/tickets`
- `GET /api/tickets/{ticket_id}`
- `POST /api/tickets/{ticket_id}/reply`

### 7.2 РђРґРјРёРЅСЃРєРёРµ РѕРїРµСЂР°С†РёРё
- `GET /api/admin/tickets`
- `POST /api/admin/tickets/{ticket_id}/reply`
- `POST /api/admin/tickets/{ticket_id}/status`

### 7.3 Bot/helpbot
- Helpbot РёСЃРїРѕР»СЊР·СѓРµС‚СЃСЏ РєР°Рє РѕС‚РґРµР»СЊРЅР°СЏ С‚РѕС‡РєР° РІС…РѕРґР° РґР»СЏ РёРЅС†РёРґРµРЅС‚РѕРІ Рё FAQ.
- РћРїРµСЂР°С‚РѕСЂСЃРєР°СЏ РѕС‡РµСЂРµРґСЊ РґРѕСЃС‚СѓРїРЅР° РІ Р°РґРјРёРЅ-СЃС†РµРЅР°СЂРёСЏС… Р±РѕС‚Р°.

## 8. Р”РµРїР»РѕР№ Рё РѕР±РЅРѕРІР»РµРЅРёРµ

### 8.1 РћР±С‰РёР№ РїРѕСЂСЏРґРѕРє (Р±РµР· remote-exec)
1. Р›РѕРєР°Р»СЊРЅРѕ: `python scripts/release_orchestrator.py --gates-only`.
2. Upload/release РєРѕРґРѕРІРѕР№ С‡Р°СЃС‚Рё РЅР° brain.
3. Р РµСЃС‚Р°СЂС‚ СЃРµСЂРІРёСЃРѕРІ: `portal-api`, `portal-bot`, `portal-helpbot`.
4. Р”РµРїР»РѕР№ static (`webapp/out`, `marketing/out`).
5. Sanity checks (СЃРј. СЂР°Р·РґРµР» 9.4).

### 8.2 РљРѕРјР°РЅРґС‹ (СЂСѓС‡РЅРѕР№ Р·Р°РїСѓСЃРє РЅР° brain)
- `systemctl status portal-api --no-pager`
- `systemctl status portal-bot --no-pager`
- `systemctl status portal-helpbot --no-pager`
- `curl -fsS https://<api-domain>/api/health`

### 8.3 Rollback-safe С‚РѕС‡РєРё
- Р”Рѕ РјРёРіСЂР°С†РёР№ Р‘Р”.
- РџРѕСЃР»Рµ backend deploy, РґРѕ static deploy.
- РџРѕСЃР»Рµ РІРєР»СЋС‡РµРЅРёСЏ/РёР·РјРµРЅРµРЅРёСЏ timer/metrics.

## 9. РњРѕРЅРёС‚РѕСЂРёРЅРі Рё РґРёР°РіРЅРѕСЃС‚РёРєР°

### 9.1 Node metrics
- Collector: `scripts/collect_node_metrics.py`
- Timer/service:
  - `infra/portal-node-metrics.service`
  - `infra/portal-node-metrics.timer`

### 9.2 Р’РєР»СЋС‡РµРЅРёРµ С‚Р°Р№РјРµСЂР°
- `python scripts/remote_install_node_metrics_timer.py --brain-ip <ip>`
- Р—Р°С‚РµРј РЅР° brain:
  - `systemctl is-enabled portal-node-metrics.timer`
  - `systemctl is-active portal-node-metrics.timer`
  - `systemctl list-timers portal-node-metrics.timer --all`
  - `journalctl -u portal-node-metrics.service -n 50 --no-pager`

### 9.3 Admin metrics API
- `GET /api/admin/metrics/status`
- `GET /api/admin/metrics/timeseries?from=YYYY-MM-DD&to=YYYY-MM-DD`
- `GET /api/admin/nodes/traffic?from=YYYY-MM-DD&to=YYYY-MM-DD`

### 9.4 Post-deploy sanity checklist
1. `/api/health` = 200.
2. `/s8Kx2mP7qR4wT/{token}` СЂР°Р±РѕС‚Р°РµС‚ РїРѕ Р°РєС‚СѓР°Р»СЊРЅРѕРјСѓ token.
3. Checkout create + notify callback Р·Р°РІРµСЂС€Р°СЋС‚ Р°РєС‚РёРІР°С†РёСЋ.
4. Ticket flow (create/reply/status) СЂР°Р±РѕС‚Р°РµС‚ E2E.
5. `/admin/*` РјР°СЂС€СЂСѓС‚С‹ WebApp РґРѕСЃС‚СѓРїРЅС‹ С‚РѕР»СЊРєРѕ РїСЂРё `is_admin=true`.
6. `python scripts/admin_webapp_smoke.py` РїСЂРѕС…РѕРґРёС‚ Р±РµР· РѕС€РёР±РѕРє.

### 9.5 SLO/SLA Рё alert policy
- РћРїРµСЂР°С†РёРѕРЅРЅС‹Рµ SLI/SLO Рё РїСЂР°РІРёР»Р° СЌСЃРєР°Р»Р°С†РёРё: `docs/34-monitoring-slo-sla-2026-03.md`.

## 10. Troubleshooting

### 10.1 РЎРёРјРїС‚РѕРј: В«РѕС€РёР±РєР° РѕР±РЅРѕРІР»РµРЅРёСЏВ» РїСЂРё РѕР±РЅРѕРІР»РµРЅРёРё РїРѕ РєР»СЋС‡Сѓ
РџСЂРѕРІРµСЂРёС‚СЊ:
1. Р•СЃС‚СЊ Р»Рё `sub_token` Сѓ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ РІ Р‘Р”.
2. РЎРѕРІРїР°РґР°РµС‚ Р»Рё panel `subId` СЃ DB `sub_token`.
3. Р›РѕРіРё `control_panel.py`/`panel_client.py` РЅР° mismatch Рё forced sync.
4. Endpoint `/s8Kx2mP7qR4wT/{token}` РїРѕ С‚РµРєСѓС‰РµРјСѓ С‚РѕРєРµРЅСѓ.

### 10.2 РЎРёРјРїС‚РѕРј: channel bonus РЅРµ РѕС‚РєР°С‚С‹РІР°РµС‚СЃСЏ
РџСЂРѕРІРµСЂРёС‚СЊ:
1. Р›РѕРіРё worker (`raw_status`, `normalized_reason`, `action`).
2. РќРѕСЂРјР°Р»РёР·Р°С†РёСЋ `left/kicked -> not_member`.
3. Р§С‚Рѕ revoke РЅРµ Р±Р»РѕРєРёСЂСѓРµС‚СЃСЏ transient Telegram-РѕС€РёР±РєРѕР№.

### 10.3 РЎРёРјРїС‚РѕРј: СѓСЃС‚Р°СЂРµРІС€РёРµ РјРµС‚СЂРёРєРё
РџСЂРѕРІРµСЂРёС‚СЊ:
1. `portal-node-metrics.timer` enabled/active.
2. `journalctl -u portal-node-metrics.service`.
3. `GET /api/admin/metrics/status` (fresh/stale).

### 10.4 РЎРёРјРїС‚РѕРј: deep-link РєР°РјРїР°РЅРёСЏ РЅРµ СЃСЂР°Р±Р°С‚С‹РІР°РµС‚
РџСЂРѕРІРµСЂРёС‚СЊ:
1. Р”Р»РёРЅР° Telegram start payload <= 64.
2. Р”РѕРїСѓСЃС‚РёРјС‹Рµ СЃРёРјРІРѕР»С‹: `[A-Za-z0-9_-]`.
3. Р РµР°Р»СЊРЅС‹Рµ Р·РЅР°С‡РµРЅРёСЏ `promo/campaign` РІ checkout context.

### 10.5 РЎРёРјРїС‚РѕРј: `Bot domain invalid` РїСЂРё РІС…РѕРґРµ С‡РµСЂРµР· Telegram Login Widget
РџСЂРѕРІРµСЂРёС‚СЊ:
1. Р’ `@BotFather` РґР»СЏ `@portal_privacy_bot` РІС‹РїРѕР»РЅРµРЅ `/setdomain` РЅР° Р°РєС‚СѓР°Р»СЊРЅС‹Р№ РґРѕРјРµРЅ (`portal-privacy.online`).
2. Р’РµР±-РІС…РѕРґ С‡РµСЂРµР· deep-link СЂР°Р±РѕС‚Р°РµС‚: `https://t.me/portal_privacy_bot?start=weblogin`.
3. РЎСЃС‹Р»РєР° РёР· Р±РѕС‚Р° РѕС‚РєСЂС‹РІР°РµС‚ WebApp СЃ `web_session_token` Рё Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРё Р»РѕРіРёРЅРёС‚ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ РІ Р±СЂР°СѓР·РµСЂРµ.

---

## РџСЂРёР»РѕР¶РµРЅРёРµ A: Admin WebApp MVP (`/admin/*`)
- `/admin/dashboard`
- `/admin/users`
- `/admin/nodes`
- `/admin/tickets`
- `/admin/promos`
- `/admin/broadcast`
- `/admin/referrals`
- `/admin/bonuses`

Gate: РЅРµ-Р°РґРјРёРЅС‹ СЂРµРґРёСЂРµРєС‚СЏС‚СЃСЏ РІ РїРѕР»СЊР·РѕРІР°С‚РµР»СЊСЃРєРёР№ dashboard.

## РџСЂРёР»РѕР¶РµРЅРёРµ B: Smoke-РєРѕРјР°РЅРґС‹ СЂРµР»РёР·Р°
- `python -m unittest discover tests`
- `cd webapp && npm.cmd run build`
- `python -m unittest tests.test_worker_retention`
- `python -m unittest tests.test_api_auth_and_tickets`

