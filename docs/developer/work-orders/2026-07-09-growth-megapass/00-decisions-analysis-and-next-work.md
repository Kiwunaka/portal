# POKROV Growth Megapass: решения, находки и план на потом

Дата: 2026-07-09
Статус: planning snapshot, не реализация
Назначение: сохранить весь контекст конкурентного разбора, принятые решения владельца и список будущих доработок перед большим growth/product/technical прогоном.

Этот документ не заменяет канонические продуктовые документы. После реализации связанные правила нужно перенести в `docs/product/`, `docs/architecture/`, `docs/operations/`, `webapp/README.md`, `adminapp/README.md` и docs активного клиента `C:\Users\kiwun\Documents\ai\POKROV-app\docs\`.

Update `2026-07-10`: execution truth for the market-ready release is now
`01-market-ready-cis-release-design.md` plus
`02-market-ready-cis-implementation-workstreams.md`. Those files supersede
this snapshot where they differ: canonical account foundation runs first;
Android FCM is allowed only as a transport without Analytics/Ads; WARP is a
stable `1.0.0` gate; and promotion is `1.0.0-rc.1 -> 1.0.0` after evidence.

## База исследований

Основные отчеты:

- `docs/competitive/telegram-vpn-2026-07-08/full-bot-site-webapp-research.md`
- `docs/competitive/telegram-vpn-2026-07-09/final-competitor-comparison-and-pokrov-gap.md`
- `docs/competitive/telegram-vpn-2026-07-09/apk-competitor-static-analysis.md`
- `docs/competitive/telegram-vpn-2026-07-09/quattro-bot-channel-deep-dive.md`

Артефакты и скриншоты:

- `docs/competitive/telegram-vpn-2026-07-08/screenshots-wave2/`
- `docs/competitive/telegram-vpn-2026-07-08/screenshots-big/`
- `docs/competitive/telegram-vpn-2026-07-09/quattro/`
- `docs/competitive/telegram-vpn-2026-07-09/quattro/screenshots/`
- `docs/competitive/telegram-vpn-2026-07-09/quattro/web/live/`

The `2026-07-09/quattro/` tree is restricted local evidence and is ignored by
git because it contains PII and capability URLs. It is not part of the
portable repository baseline.

APK/static-analysis источники, которые использовались в выводах:

- Quattro 0.18.1: `C:\Users\kiwun\AppData\Local\Temp\opencode\quattro\`
- HiroVPN 1.17.1: `C:\Users\kiwun\AppData\Local\Temp\opencode\hirovpn\`
- ByeByeDPI 1.7.6: `C:\Users\kiwun\AppData\Local\Temp\opencode\byebyedpi\`
- POKROV beta reference: `C:\Users\kiwun\Documents\ai\POKROV-app\artifacts\releases\pokrov-app\1.0.0-beta+20260608-hotfix\`

## Что нашли у конкурентов

### Quattro

Quattro - главный эталон связки `канал -> бот -> кабинет -> APK -> support`.

Сильное:

- огромный Telegram-канал и регулярные release/update posts;
- обязательная подписка на канал перед полноценным bot UX;
- web cabinet с dashboard, subscription, servers, promo, referral, partner, instructions, settings;
- app на Flutter + native VPN core, в APK есть `libnpvpnBox.so`, sing-box/SagerNet-like следы;
- видимые app controls: quick tile, split tunneling, DNS settings, QR/import, traffic/subscription cards, server list, refresh/reissue;
- агрессивная, но понятная воронка: каждый пост ведет в bot/site/support/update.

Плохое / не копировать:

- Android debug signing в публичной линии;
- hardcoded local API token внутри APK;
- Firebase/Measurement/AD_ID surface;
- broad claims и сложность кабинета;
- raw technical power-user настройки не должны попадать в первый слой POKROV onboarding.

### Cats

Cats важен не масштабом, а recovery-механикой.

Сильное:

- short-code login;
- кабинет без почты/пароля;
- сайт как запасной вход, если Telegram недоступен;
- bot-to-site import;
- простая реферальная подача.

Вывод для POKROV:

- взять recovery code;
- не делать code-only identity;
- recovery code должен быть аварийным мостом, а не единственным замком аккаунта.

### Kosmos

Kosmos ближе всех к mainstream app-first/cabinet модели.

Сильное:

- сайт и личный кабинет;
- email/social login;
- own app;
- длинный trial и понятная mainstream-подача.

Вывод для POKROV:

- усилить кабинет как survival surface;
- держать email как запасной вход;
- не ломать app-first модель Telegram-стеной вне Telegram-бота.

### OpenGate и Nash

Сильное:

- лучший support/incident UX;
- понятные пункты: установка, не работает, низкая скорость, оплата, сервисная проблема;
- инциденты превращаются в доверие, а не просто в оправдание;
- посты объясняют, что случилось, кого касается, что нажать, когда ждать следующий апдейт.

Вывод для POKROV:

- сделать support-router в bot/app/cabinet;
- делать incident posts и notices по шаблону;
- добавлять redacted diagnostics, а не просить пользователя писать простыню.

### HiroVPN

Сильное:

- production Android/distribution stack;
- Google signing/SourceStamp;
- Play Billing / store presence;
- QR/ML Kit и тяжелый growth stack.

Плохое / не копировать:

- AdMob;
- Yandex Ads;
- AppMetrica;
- AppsFlyer;
- Firebase Analytics pile;
- Sentry/Crashlytics по умолчанию в privacy-продукте;
- `QUERY_ALL_PACKAGES` и широкие tracking surfaces.

Вывод для POKROV:

- можно стремиться к release trust/store lane;
- нельзя тащить рекламный attribution SDK-комбайн.

### ByeByeDPI

Сильное:

- чистый utility-подход;
- нет рекламной телеметрии;
- VpnService + proxy mode;
- quick tile;
- boot receiver;
- presets для обхода.

Вывод для POKROV:

- взять quick tile и простой technical-control UX;
- не становиться перегруженным config-конструктором в первом слое.

## Принятые решения владельца

### Общая стратегия

- Делаем один большой мегапрогон, а не мелкие волны.
- Внутри мегапрогона работу все равно раскладывать по подсистемам и зависимостям.
- Маркетинг: "как рынок", но без прямой грязи.
- Можно громко: urgency, дедлайны, боль, "бесплатный ВПН", промо, быстрый CTA.
- Нельзя: fake counters, "100% анонимно", "не блокируется", недоказуемый no-logs, unsupported store/trusted claims.
- Допустимый claim guard: "рынок, но без жести".

### Trial, Telegram gate и free

- В Telegram-боте подписка на канал обязательна.
- Без подписки бот функционально заблокирован.
- После подписки бот дает `5 дней` premium.
- Пользователи из app/site/store получают `5 дней` сразу, без Telegram.
- Пользователи из app/site/store получают `+5 дней` за Telegram + канал.
- После окончания premium/trial аккаунт откатывается на free tier.
- Free можно подавать громко как "бесплатный ВПН".
- Лимиты free показывать ниже/в деталях, не первым ударом.
- Текущая free база: `5 GB / 30 дней / 1 устройство / NL-free`.

### Цены и рефералка

- Текущую тарифную сетку не менять в первом мегапрогоне.
- Упаковку тарифов сделать агрессивнее.
- Текущие планы остаются из `shared/tariff-catalog.json`: `start_99`, `1_month`, `3_months`, `6_months`, `9_months`, `12_months`.
- Referral в первой версии: бонусные дни.
- Cash/TON/crypto payouts не делать до fraud ledger, reconciliation и ручной операционной готовности.

### Antiabuse и privacy

- IP и device context собирать нужно.
- Это должен быть first-party antiabuse, не сторонний рекламный tracking stack.
- Raw IP хранить до `72 часов`.
- После 72 часов хранить только HMAC/prefix/агрегаты.
- Device identity: app-generated `install_id`, не железный fingerprint.
- Antiabuse actions: soft -> lock.
- Сначала warning/cooldown/manual review/reissue.
- Hard lock только при явном фроде, шаринге или массовой накрутке.

Не собирать:

- AD_ID;
- Android ID/IMEI/MAC;
- список установленных приложений;
- DNS-запросы;
- посещенные сайты, SNI, URL;
- содержимое трафика;
- raw subscription URL в аналитике.

Не ставить:

- AppMetrica;
- AppsFlyer;
- AdMob;
- рекламные attribution SDK;
- Firebase Analytics по умолчанию.

### Recovery

- Целевой контур: app-first account + recovery code + email + Telegram.
- Recovery code формат: `PKR-XXXX-XXXX-XXXX`.
- Код показывается один раз.
- В базе хранится только hash/HMAC.
- Вход по recovery code дает limited session.
- Limited session позволяет:
  - увидеть статус;
  - продлить;
  - обратиться в поддержку;
  - привязать email/Telegram;
  - перевыпустить доступ;
  - восстановить управляемый доступ.
- Raw secrets/QR/subscription URL доступны только после fresh auth.

### Autoposting и дайджесты

- Автопубликация разрешена.
- Источники: широкий веб.
- Подключение источников через env endpoints: SearXNG/crawler API.
- LLM provider/model должен быть configurable.
- Токены не экономим: 5-10 проверочных прогонов допустимы.
- Нужны:
  - source score;
  - source quorum;
  - hallucination checks;
  - alert checks;
  - проверка, что проблема реально упала/восстановилась;
  - claim guard;
  - risk score;
  - kill switch;
  - история публикаций.
- Autopost surfaces:
  - public Telegram channel `@pokrov_vpn`;
  - in-app notices;
  - cabinet notices.
- Marketing/SEO страницы не должны автообновляться без отдельного правила.

### Notifications

- Native notifications нужны.
- Android использует FCM только как транспорт идентификатора notice.
- Стек: first-party notices + Android FCM/polling fallback + Windows tray polling/local toast.
- Firebase Analytics, Measurement, Crashlytics, Ads, AppMetrica и AppsFlyer запрещены.
- Сегменты:
  - trial ending;
  - trial expired;
  - payment abandoned;
  - update available;
  - incident active/resolved;
  - promo;
  - no first connect;
  - Telegram not linked.

### Client scope и release trust

- Клиентский scope: Android + Windows.
- iOS не входит в мегапрогон.
- Android production signing начать сейчас.
- Store lane начать сейчас.
- Public store/trusted claims разрешены только после фактических доказательств.
- Windows trust/readiness тоже не обещать без evidence.

## Где что лежит

### Root platform repo

Backend, bot, antiabuse, trial, referral, promo, notices:

- `portal_bot/api.py`
- `portal_bot/bot.py`
- `portal_bot/worker.py`
- `portal_bot/models.py`
- `portal_bot/migrations.py`
- `portal_bot/events_service.py`
- `portal_bot/pay_attempts_service.py`

Existing useful pieces:

- `install_id` and app-first session: `portal_bot/api.py`
- event tracking: `portal_bot/events_service.py`
- pay attempts: `portal_bot/pay_attempts_service.py`
- retention pings: `portal_bot/worker.py`
- channel bonus guard: `portal_bot/worker.py`
- promo/referral/admin endpoints: `portal_bot/api.py`
- broadcast dry-run/send: `portal_bot/api.py` + `adminapp`

Cabinet:

- `webapp/src/app/(dashboard)/`
- `webapp/src/components/`
- `webapp/src/lib/api.ts`
- `webapp/README.md`

Admin/content/autopost UI:

- `adminapp/src/components/ops-dashboard.tsx`
- `adminapp/src/lib/api.ts`
- `adminapp/src/lib/sections.ts`
- `adminapp/README.md`

Marketing/copy/pricing:

- `marketing/src/`
- `shared/copy.ts`
- `copy/catalog.ru.json`
- `shared/tariff-catalog.json`
- `shared/product-facts.json`
- `shared/public-urls.json`

Canonical docs to update after implementation:

- `docs/product/portal-vpn-product.md`
- `docs/architecture/app-first-and-bonus-flows.md`
- `docs/architecture/system-overview.md`
- `docs/operations/client-delivery-update-content-plan.md`
- `docs/architecture/client-downloads-flow.md`
- `docs/user/portal-vpn-user-guide-ru.md`

### Active client repo

Client code:

- `C:\Users\kiwun\Documents\ai\POKROV-app\apps\android_shell\`
- `C:\Users\kiwun\Documents\ai\POKROV-app\apps\windows_shell\`
- `C:\Users\kiwun\Documents\ai\POKROV-app\packages\app_shell\`
- `C:\Users\kiwun\Documents\ai\POKROV-app\packages\runtime_engine\`
- `C:\Users\kiwun\Documents\ai\POKROV-app\packages\support_context\`

Client docs:

- `C:\Users\kiwun\Documents\ai\POKROV-app\docs\README.md`
- `C:\Users\kiwun\Documents\ai\POKROV-app\docs\product\client-public-beta-prd.md`
- `C:\Users\kiwun\Documents\ai\POKROV-app\docs\implementation\client-release-backlog.md`
- `C:\Users\kiwun\Documents\ai\POKROV-app\docs\operations\android-release-audit.md`
- `C:\Users\kiwun\Documents\ai\POKROV-app\docs\operations\windows-release-readiness.md`
- `C:\Users\kiwun\Documents\ai\POKROV-app\docs\operations\cutover-readiness.md`

## Что делаем потом

### 1. Telegram bot gate

- Ввести обязательную подписку на канал для Telegram bot flow.
- До подписки не давать trial/access/pay/instructions/support flow.
- После проверки подписки выдать 5 дней premium.
- Логировать события:
  - `tg_gate_shown`;
  - `tg_gate_subscribe_clicked`;
  - `tg_gate_check_failed`;
  - `tg_gate_passed`;
  - `trial_granted_from_tg_gate`.
- Важно: юридические ссылки можно оставить на gate-экране как external links, но функциональный бот закрыт.

### 2. Trial/free/reward economy

- App/site/store: 5 дней premium сразу.
- Bot/TG: 5 дней premium после подписки.
- App/site/store: +5 дней за Telegram + channel.
- После окончания premium/trial: downgrade to free tier.
- Обновить copy:
  - "бесплатный ВПН";
  - "5 дней premium";
  - "после теста останется бесплатный доступ";
  - "Telegram нужен только для бонуса вне бота".

### 3. First-party antiabuse ledger

- Добавить отдельный ledger для trial/referral/promo/device/IP signals.
- Сохранять:
  - account/user id;
  - install_id;
  - device label/platform/app version/OS major;
  - raw IP до 72 часов;
  - HMAC full IP для короткого окна;
  - HMAC IP prefix для 30-90 дней;
  - event name/source/session;
  - referral/promo/payment linkage;
  - suspicious score/reasons.
- Использовать HMAC-SHA256 с backend-only secret/pepper.
- Не отправлять raw IP в общие admin lists.
- Raw/recent IP details разрешены только внутри individual user card для расследований.

### 4. Soft antiabuse rules

- Trial farming: много trial с одного IP prefix/install/device window -> cooldown/manual review.
- Promo abuse: много попыток промокода -> cooldown.
- Referral abuse: same prefix/device/payment/order cluster -> pending/manual review.
- Device sharing: частая смена устройств или превышение лимита -> warning -> reissue -> lock.
- Link leak: резкий рост sessions/IP/node spread -> предложить reissue.
- Free tier abuse: высокий traffic/session churn -> throttle/cooldown/manual review.

### 5. Recovery code and survival cabinet

- Recovery code `PKR-XXXX-XXXX-XXXX`.
- One-time display.
- Hash/HMAC only in DB.
- Rate limits by IP/account/install/email.
- Limited session:
  - status;
  - renew;
  - support;
  - link email/TG;
  - reissue access;
  - device revoke.
- Expired survival mode:
  - VPN access off or free-tier;
  - cabinet/bot/app renewal/support still available.

### 6. Device list and reissue

- Улучшить device list:
  - Android/Windows;
  - device name;
  - install_id preview;
  - last seen;
  - current/old app version;
  - revoke.
- Добавить self-service reissue:
  - rotate managed access/subscription material;
  - invalidate leaked link where applicable;
  - keep paid entitlement;
  - write audit event.

### 7. Content engine and autopost

- Новый backend content pipeline:
  - ingest;
  - normalize;
  - source score;
  - fact extraction;
  - draft;
  - multi-review;
  - risk score;
  - publish.
- Источники:
  - SearXNG env endpoint;
  - crawler env endpoint;
  - Telegram/TGStat competitor sources where available;
  - POKROV release notes;
  - POKROV alerts/incidents;
  - payment/funnel/free-tier/traffic summaries when useful.
- Проверки:
  - 5-10 model passes;
  - source quorum for external claims;
  - no unsupported claims;
  - no fake counters;
  - no raw secrets;
  - no panic-only post without action;
  - incident must be rechecked several times before "resolved".
- Outputs:
  - Telegram channel post;
  - app notice;
  - cabinet notice;
  - admin history.

### 8. Adminapp content UI

- Добавить section или расширить `broadcast`:
  - content queue;
  - sources;
  - extracted facts;
  - model check results;
  - risk score;
  - planned publish time;
  - published URL/message id;
  - pause/kill switch;
  - manual override;
  - failed check reasons.
- Использовать `adminapp`, не создавать новую админку.

### 9. Notices and local notifications

- First-party polling endpoint для notices.
- App/cabinet reads notices by segment/platform/status.
- Android FCM transport + local notifications + polling fallback.
- Windows tray polling + local toast; WNS later.
- Required notice types:
  - trial ending;
  - expired;
  - payment abandoned;
  - update available;
  - incident active;
  - incident resolved;
  - promo active;
  - Telegram bonus available;
  - no first connect.

### 10. Client technical parity

- Android:
  - quick tile;
  - FCM notification transport with polling fallback;
  - update center;
  - production signing;
  - route UX polish;
  - redacted diagnostics.
  - stable WARP with explicit baseline fallback and physical release proof;
- Windows:
  - notice/update parity;
  - support diagnostics parity where possible;
  - release trust readiness without unsupported claims.
- Both:
  - no ad SDK;
  - no AD_ID;
  - no raw secret telemetry;
  - no silent auto-update claim.

### 11. Store lane and release trust

- Start Android store lane.
- Close production signing story.
- Add release provenance/checksums/fingerprints.
- Keep outside-store delivery honest until store evidence exists.
- Do not claim:
  - Play Store available;
  - trusted Windows;
  - stable 1.0.0;
  - RU-origin readiness;
  - no-logs;
  - 100% anonymous;
  - unblockable.

### 12. Marketing and copy

- Перепаковать public/cabinet/bot copy под aggressive CIS funnel.
- Главный крючок: "бесплатный ВПН".
- Второй слой: "5 дней premium", "после теста останется free-доступ".
- Третий слой: "без рекламных SDK", "собираем только технический минимум для защиты от накрутки".
- Посты:
  - weekly digest;
  - incident;
  - release/update;
  - promo;
  - instruction;
  - referral;
  - "что делать если не работает".
- Каждый пост должен иметь CTA.

## Проверки и acceptance

Backend:

- pytest для bot gate;
- pytest для trial/reward/free downgrade;
- pytest для antiabuse HMAC/IP retention;
- pytest для recovery code limited session;
- pytest для referral-days flow;
- pytest для content engine dry-run/publish guards.

Bot:

- проверить locked pre-subscription state;
- проверить post-subscription 5-day grant;
- проверить, что functional paths до подписки закрыты.

Webapp:

- `npm.cmd run build`;
- e2e cabinet recovery/devices/notices;
- copy guardrails после visible copy changes.

Adminapp:

- `npm.cmd run build`;
- `npm.cmd run lint`;
- `npm.cmd run test:e2e`;
- e2e content queue/kill switch/broadcast dry-run.

Client:

- Flutter tests;
- Android Kotlin tests;
- Android manifest guard:
  - no AD_ID;
  - no QUERY_ALL_PACKAGES;
  - no ad SDK markers;
  - local notification permission expected;
  - quick tile manifest expected after implementation.
- signing/provenance checks.

Docs:

- update canonical docs only when behavior is implemented;
- keep this file as planning source until then.

## Нерешенное, но принято как later

- iOS не входит в этот мегапрогон.
- Cash/crypto partner payouts later only after fraud ledger and finance reconciliation.
- WNS and any non-FCM remote transport remain later; Android FCM transport is in `1.0.0`.
- Full SEO/marketing auto-updates later; first autopost target is channel + notices.
- Store/trusted claims later only after evidence.
