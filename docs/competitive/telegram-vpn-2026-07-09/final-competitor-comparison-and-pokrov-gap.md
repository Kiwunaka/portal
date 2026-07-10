# Final competitor comparison and POKROV gap analysis

Method note: tiers and relative strengths below are qualitative observations
within the researched sample, not measured conversion causality. Current-state
POKROV references reflect the audit date; the owner-approved execution design
in `docs/developer/work-orders/2026-07-09-growth-megapass/01-market-ready-cis-release-design.md`
supersedes them for implementation.

Дата: 2026-07-09
База: Telegram/cabinet/site/app/APK research from `2026-07-08..2026-07-09`.

## Короткий вывод

POKROV стратегически выбран правильно: app-first, Telegram не нужен для старта, есть кабинет, честная beta-подача, 5 дней trial, +10 дней за Telegram, чистый APK без ad/attribution SDK. Но рынок выигрывает не "качеством VPN" в вакууме, а системой давления:

1. Канал каждый день создает ощущение движения.
2. Бот быстро превращает намерение в оплату, trial, подписку на канал или поддержку.
3. Кабинет становится спасательным контуром, если Telegram, App Store, Happ или маршрут ломаются.
4. Посты про RKN/DNS/App Store/обновления превращают аварии в доверие.
5. Рефералки, промокоды, дедлайны и пуши создают постоянный повод вернуться.
6. Свой APK/app-store presence дает больше доверия, чем raw subscription link.

POKROV сейчас уступает прежде всего в частоте касаний, громкости маркетинга, видимой продуктовой "живости", реферальной механике, emergency/support UX и Android signing. Не в базе продукта.

## Tier List Competitors

| Tier | Конкурент | Почему важен |
| --- | --- | --- |
| S | Quattro | Лучший эталон связки: огромный канал, бот, кабинет, APK, release posts, referral/partner/promo, инструкции. |
| A | HiroVPN | Самая зрелая distribution/SDK/store/billing surface среди разобранных артефактов, но privacy тяжелый. |
| A | Cats | Лучший web-cabinet/recovery паттерн: anonymous short-code login, сайт как fallback от Telegram. |
| A | OpenGate | Лучший support/ops UX: install, not working, low speed, service issue, autobalancer/protocol updates. |
| A | Kosmos | Ближе всех к mainstream app-first: сайт, LK, email/social login, own app, длинный trial. |
| B | Nosok | Масштаб, fallback narrative, сайт, сильная многоуровневая рефералка. |
| B | PLATINA | Агрессивный referral pressure: cash/TON payouts, быстрый рост, отдельные bot/sales/support surfaces. |
| B | Nash | Сильные incident posts: объясняет DNS/RKN/location workarounds простым языком. |
| B | MORI | Educational/security marketing: DNS leaks, WebRTC, cookies, browser fingerprinting, "дешевые VPN опасны". |
| B | 4ebur | Mascot/content cadence, app-store scale, визуальная запоминаемость, routing/update posts. |
| B | Luma | App-store/app-first signal + аномально высокий reach. |
| C | GROZA/NEO/Fen/ArtVPN | Полезны отдельными кусками: white-list limits, simple bot menus, constructors, cheap anchors. |

## Market Pattern

### 1. Канал

Сильные конкуренты используют канал не как новостную доску, а как acquisition engine.

Что делают:

- страх: `RKN`, `DNS`, App Store removal, Telegram blocking, "обычные VPN больше не работают";
- urgency: скидка сегодня, промокод, последний день, trial now;
- operational trust: "сломалось вот это, нажмите вот это, следующий апдейт тогда-то";
- release cadence: APK update, protocol update, locations, DNS, quick tile, pings;
- proof loop: screenshots, views, mascot/art, mini-guides, "мы уже починили";
- CTA per post: bot deep link, site partner tag, support, APK, instruction.

POKROV сейчас уступает: нет регулярной контент-машины, мало поводов возвращаться, слабее ощущение "продукт живой каждый день".

### 2. Бот

Лучшие боты не просто выдают ссылку. Они закрывают:

- trial/buy;
- install by platform;
- my access/subscription;
- support routing;
- channel/news CTA;
- referral/invite;
- emergency instructions;
- sometimes proxy/manual route.

POKROV должен сохранить app-first, но bot fallback надо сделать практичнее: не raw-link-first, а `Доступ / Установить / Не работает / Продлить / Бонус / Поддержка / Ещё`.

### 3. Сайт И Кабинет

Сайт стал survival surface.

- Cats: short-code login без почты/паролей.
- Nosok: сайт + contacts + fallback after expiry.
- Kosmos: LK с email/Google/Yandex.
- Quattro: mature cabinet with payment, referral, promo, servers, instructions, settings.
- OpenGate: public surface + Telegram-first route.

POKROV имеет `pokrov.space`, `app.pokrov.space`, `pay.pokrov.space`, но слабее упаковывает это как преимущество: "Telegram не нужен, приложение и кабинет останутся".

### 4. App/APK

Quattro app сильнее по видимым controls:

- split tunneling by URL/app;
- DNS: DoH/DoT/DoQ/DoH3/UDP;
- own server;
- QR/import;
- quick settings tile;
- traffic/subscription cards;
- server/ping/location controls;
- referral/support/Telegram/email login.

Hiro сильнее по distribution:

- Google signing + SourceStamp;
- Play Billing;
- App Store / Huawei / Play links;
- QR/ML Kit;
- license check.

ByeByeDPI сильнее как bypass utility:

- VpnService + proxy mode;
- quick tile;
- boot receiver;
- 60 strategies;
- Telegram/YouTube/Discord/social site lists;
- no telemetry SDK.

POKROV выигрывает по чистоте APK, но уступает по visible controls and release trust: текущий beta APK debug-signed.

## Aggressive Marketing Mechanics

### Какие механики они систематически используют

These patterns are visible in the sample; their individual conversion lift was
not available for measurement.

1. Forced channel gate. Quattro заставляет подписаться до полноценного bot UX. Рост канала покупается трением.
2. Discount urgency. Купон, последний день, скидка, промокод.
3. Incident pressure. "Если не работает YouTube/TikTok/Telegram, это не вы, это RKN/DNS, вот кнопка".
4. Update pressure. "Скачайте APK 0.18.1, иначе power button/маршрут/подписка может работать хуже".
5. App Store panic. "Happ исчез/вернулся, фейки в поиске, ставьте по ссылке".
6. Referral greed. 50% forever, multi-level 50/25/15, cash/TON payouts.
7. Partner dashboard. Человек видит заработок, клики, конверсии, payouts.
8. Visual memory. Mascot, beach/summer posts, big cards, app screenshots.
9. Multi-surface CTA. В каждом посте bot + site + support + instruction.
10. Push-like cadence. Даже без native push канал работает как push layer.

### Что POKROV нельзя копировать напрямую

- mandatory channel gate before trial;
- fake counters;
- "100% anonymous", "no logs", "unblockable" без evidence;
- panic-only tone;
- cash/crypto referrals before anti-abuse/finance ledger;
- ad SDKs and attribution SDK pile;
- raw subscription URL as first-layer UX.

### Как сделать POKROV-версию агрессивнее, но чище

Позиция: не "орем громче", а "каждый пост дает действие".

Пост всегда должен отвечать:

- что случилось;
- кого касается;
- что нажать;
- где проверить статус;
- где получить помощь;
- когда будет следующий апдейт.

## POKROV Strengths

Относительные сильные стороны POKROV в исследованной выборке:

1. App-first identity. Не надо начинать с Telegram.
2. Trial без карты: `5 days`.
3. На дату аудита Telegram reward был `+10 days` и optional; approved target is
   a bot-only new-lead gate plus additive `+5 days` for app/site-origin users.
4. Собственные public surfaces: site, cabinet, API, checkout.
5. Cleaner APK: нет найденных AdMob/AppMetrica/AppsFlyer/Sentry/Billing markers in current beta APK.
6. Более честная release story: beta, signing/manual gates не замазаны.
7. Нормальная стратегическая recovery order: app -> cabinet -> Telegram fallback.
8. Product docs уже запрещают third-party ad SDKs and unsafe remote content.

Это хороший фундамент. Но фундамент сейчас не достаточно громкий.

## Where POKROV Lags

### 1. Marketing Cadence

Уступаем:

- Quattro постит обновления как продуктовый медиа-канал.
- Nash/OpenGate/MORI превращают инциденты в доверие.
- 4ebur/Quattro визуально запоминаются.
- PLATINA/Nosok/Cats агрессивнее гонят referral.

POKROV сейчас выглядит спокойнее, но менее живым.

Нужное состояние:

- 3-5 постов в неделю минимум;
- отдельный incident template;
- weekly digest;
- release/update posts for every app/backend-visible change;
- bonus/referral post every week;
- educational lane 1 раз в неделю.

### 2. Push / Notification / Retention

Уступаем:

- Конкуренты используют Telegram channel как push-layer.
- У Quattro каждый update post ведет в APK/bot/site.
- У многих есть bot-triggered reminders around payment/trial/support.
- POKROV пока не выглядит как система касаний по trial lifecycle.

Что нужно:

- in-app notice center from backend JSON;
- Telegram channel post mirror inside app/cabinet;
- opt-in push/notification events for Android/Windows where available;
- trial lifecycle reminders:
  - day 0: installed + first connect;
  - day 3: "2 дня осталось";
  - day 5: expiry/renew;
  - expired: recovery + free mode + paid continuation;
- payment reminders:
  - before expiry;
  - payment failed;
  - successful renewal;
- incident pushes:
  - route degraded;
  - update available;
  - switch mode/location;
  - resolved.

Важно: никаких массовых spam pushes. Нужна segmentation.

Segments:

- fresh trial, no first connect;
- fresh trial, connected;
- trial expires soon;
- expired;
- paid active;
- Telegram linked/unlinked;
- Android/Windows;
- app version outdated;
- incident affected route/platform.

### 3. Bot UX

Уступаем:

- OpenGate/Nash/Fen проще ведут пользователя по проблемам.
- Quattro агрессивнее закрывает payment.
- Конкуренты чаще показывают install instructions прямо из bot.

Нужное меню:

- `Мой доступ`
- `Установить`
- `Не работает`
- `Низкая скорость`
- `Продлить`
- `Бонус +10 дней`
- `Пригласить`
- `Кабинет`
- `Поддержка`
- `Ещё`

Raw link/QR только внутри `Ещё / Ручная настройка / Восстановление`.

### 4. Cabinet / Webapp

Уступаем Quattro/Cats/Kosmos:

- Quattro: payment configurator, referral, partner, promo, servers, instructions, settings.
- Cats: short-code recovery pattern.
- Kosmos: mainstream login.
- Nosok: website as fallback.

POKROV needs cabinet to feel like control surface:

- current access;
- devices;
- downloads/update;
- support thread;
- referral/bonus history;
- promo activation;
- recovery code;
- app version/update state;
- incident/status strip;
- "Telegram не нужен для старта" visible.

### 5. App Features

Уступаем Quattro/ByeByeDPI/Hiro:

- no visible Quick Settings tile in current beta;
- weaker visible route controls;
- no visible QR/import recovery path;
- no visible DNS controls;
- less server/ping/status surface;
- no explicit app-side update/news center;
- no named emergency/bypass mode.

Priorities:

1. Android production signing.
2. Update/status/notice center.
3. Quick tile.
4. Split tunneling apps/sites.
5. Route mode clarity: all traffic, all except RU, selected apps/sites, emergency mode.
6. DNS screen only if product support is real.
7. QR/manual import only in recovery/advanced.

### 6. Technical Trust

Уступаем Hiro:

- Hiro APK signed with Google Inc cert, v2+v3, SourceStamp.
- POKROV beta APK is v2 with Android Debug cert.
- Windows still has unsigned/SmartScreen honesty gate.

У Quattro тоже debug cert, но они компенсируют масштабом. POKROV не должен играть в "и так сойдет": trust is part of positioning.

Must fix:

- production Android signing;
- release certificate documentation;
- checksums visible;
- update metadata in app;
- remove any debug/release ambiguity;
- do not claim store/trusted/stable until evidence exists.

### 7. Technical Product Surface

Уступаем:

- Quattro has rich client controls and local runtime integrations.
- Hiro has QR, Billing, multi-store, legal/start pages.
- ByeByeDPI has clear bypass presets.
- OpenGate/Nash have strong ops/status messaging.

POKROV should not add complexity blindly. But it should expose enough proof:

- route mode is active;
- selected location/mode;
- app version;
- update available;
- service status;
- support diagnostics redacted;
- current trial/paid/free state;
- last successful connect;
- safe fallback path.

### 8. Referral / Promo / Partner

Уступаем:

- Cats: 50% forever.
- Nosok: 3-level referral.
- PLATINA: cash/TON payouts.
- Quattro: referral + partner + promo dashboard.

POKROV near-term should not start cash payouts. Better:

- invite link;
- bonus days earned;
- invited/confirmed/paid states;
- referral history;
- campaign code support;
- promo code activation;
- anti-abuse ledger before payouts.

### 9. Support And Incident Comms

Уступаем OpenGate/Nash:

- better "not working / low speed / install / service issue" menu;
- clearer incident posts;
- stronger follow-up after resolution.

POKROV should ship:

- public status strip;
- bot support router;
- app support diagnostics;
- incident template;
- postmortem-lite post after incident.

## Technical Red Flags From Competitors

Use these as "do not do this":

- Quattro: Android Debug certificate in public APK.
- Quattro: hardcoded localhost control token.
- Quattro: release asset with debug config/log level.
- Hiro: huge ad/tracking SDK load inside VPN app.
- Hiro: `QUERY_ALL_PACKAGES`, AD_ID, AppsFlyer/AppMetrica/Sentry/AdMob stack.
- ByeByeDPI: broad storage permissions in a utility app.

POKROV's technical line should be:

- no ad SDKs;
- no third-party attribution SDKs unless explicitly approved;
- no hardcoded runtime secrets;
- no raw connection bearer material in first-layer UI;
- signed releases and checksums;
- first-party analytics only, minimal, documented.

## What To Do Next

### P0: Immediate

1. Android production signing plan and execution.
2. Final public trust copy: beta honesty, checksum, signer status, no fake claims.
3. Channel content calendar for 14 days.
4. Bot menu rewrite around `Доступ / Установить / Не работает / Продлить / Бонус / Поддержка`.
5. Cabinet hero/strip: `Telegram не нужен для старта. Если Telegram недоступен, откройте приложение или кабинет.`
6. Trial lifecycle notices in app/cabinet/bot.
7. Promo/referral minimal dashboard: invite link, earned days, history.

### P1: Product Pass

1. In-app notice center backed by backend JSON.
2. App update prompt with release notes.
3. Quick Settings tile.
4. Route mode screen: all traffic, all except RU, selected apps/sites.
5. Recovery code / backup code.
6. Support diagnostics with redaction.
7. Incident/status API for app/cabinet/channel copy.

### P2: Evidence-Dependent

1. Public speed/ping/location claims.
2. White-list/ad-filter routing product.
3. Cash/partner payouts.
4. App store claims.
5. Native push beyond Telegram and in-app notices.

## Content Calendar Skeleton

Week loop:

- Monday: product update or app tip.
- Tuesday: educational/security post.
- Wednesday: support/recovery post.
- Thursday: bonus/referral post.
- Friday: incident/status digest or route health.
- Any incident: publish within 15-30 minutes, update every 1-2 hours if unresolved, resolution post after.

Post template:

```text
Title: one concrete thing

Что происходит:
Кого касается:
Что нажать:
Где проверить:
Если не помогло:
Следующий апдейт:
```

## Final Strategic Position

POKROV should not become another noisy Telegram VPN. The winning lane is:

- trust cleaner than Hiro;
- product controls clear enough to compete with Quattro;
- recovery/cabinet stronger than Cats/Nosok;
- support/incident UX as clear as OpenGate/Nash;
- content cadence aggressive enough to stay visible;
- no fake claims, no ad SDKs, no raw-link-first UX.

The biggest gap is not "we lack one magic feature". The gap is operating rhythm. Competitors touch users constantly: posts, bot prompts, app updates, referrals, incidents, discounts. POKROV needs that loop, but implemented with first-party, evidence-backed, app-first discipline.
