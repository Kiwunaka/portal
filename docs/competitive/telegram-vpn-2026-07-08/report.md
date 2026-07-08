# Telegram VPN competitor review, 2026-07-08

Scope: Telegram channels/posts for 2026-05-08..2026-07-08, public bot profiles, logged-in Telegram Web bot onboarding, visible menus, tariffs, trials, install flows, support hooks, and public web surfaces where relevant.

Evidence:

- Screenshots: `docs/competitive/telegram-vpn-2026-07-08/screenshots/`
- Contact sheet: `docs/competitive/telegram-vpn-2026-07-08/telegram-vpn-competitors-contact-sheet.png`
- Some raw screenshots contain trial subscription URLs or Telegram account IDs. Do not publish raw screenshots without redaction.

Primary source URLs:

- https://t.me/net4ebur_bot and https://t.me/net4ebur
- https://t.me/artvpn_bot
- https://t.me/MoriVpnOfficial and https://t.me/morivpnrobot
- https://t.me/neovpnbot and https://t.me/followNeo
- https://t.me/nashvpnnews and https://t.me/nash_vpn_bot
- https://lk.kosmosvpn.ru, https://kosmosvpn.ru, and https://t.me/kosmos2vpnbot
- https://t.me/opengatevpn_bot, https://t.me/opengate_community, and https://opengate.ink
- https://t.me/VPN_GROZA_BOT and https://t.me/VPN_GROZA_NEWS
- https://t.me/fenvpnrobot and https://t.me/fen_vpn

## Executive read

The market is openly aggressive. Almost every bot is surrounded by Telegram Ads from other VPNs with hooks like "3 days for 1 ruble", "from 25 rub", "blocks 95% ads", "white lists", "10 Gbit/s", "without blocks", "7 days free". Competitors are not being polite: they buy intent inside each other's bot surfaces.

Common pattern:

- fear trigger: blocks, RKN, App Store removals, mobile operator white lists, "usual VPNs no longer work";
- fast promise: 1-2 minute setup, all devices, no auto-charges, support in bot;
- low-friction trial: 24h, 48h, 3d, 7d, 14d, sometimes 1 rub / 10 rub;
- fallback client layer: Happ/INCY/Streisand/V2RayTun/V2RayNG for many bots;
- operational channel: incident posts, "update subscription", "change server", "tell us city + provider";
- aggressive claims: "impossible to block", "fastest/safest", "up to 25Gb/s", "state censorship off", "YouTube without ads".

POKROV should not copy the screaming. The winning angle is: app-first, honest beta gates, clear trial, one support route, visible app download/update status, and better incident UX. The market is noisy enough that a calmer, evidence-backed product can stand out.

## Competitive matrix

| Competitor | Bot/user scale | Trial | Visible price | Client layer | Strong move | Weak/risky move |
| --- | ---: | --- | --- | --- | --- | --- |
| 4ebur | 3,880 bot users; 7.2K channel subs | not confirmed in bot | 299/799/1500 publicly | Telegram Mini App/site + configs | server load colors, routing modes, Bypass | no-refund terms, "free VPN" SEO while paid |
| ArtVPN | public MAU not shown | 3 days | 250/650/1250 for 2 devices; 490/1290/2490 for 5 devices | Happ subscription link | instant free key, simple commands, Lava copy | "impossible to ban", full anonymity, no proof |
| MORI | 42,133 bot users; 91K channel subs | 1-3 days by public copy | 250/299 conflicting public copy | Mini App + MORI/Happ keys | strong educational posts, compensation during incidents | price/device/torrent conflicts between site and channel |
| NEO | 43,688 bot users; 39K channel subs | public sources mention 7 days | 222/mo; 111/2 weeks; 667/3mo; 1332/6mo; 2222/year | Vless, devices, protocol switch, proxy | balance/device/protocol architecture, proxy product | heavy anti-state tone, chaotic product voice |
| NashVPN | 113,130 bot users; 70K channel subs; app-store scale | 1 day public/site | 299/790/1390/2690 | Apps + bot key + install docs | huge proof, clear tariffs/locations/install menu | "update subscription daily" feels like a workaround |
| Kosmos | 42,669 bot users | 14 days | site: 240/490/790 monthly tiers | Own Kosmos VPN app + LK | strongest trial, own app, cabinet, Telegram login | bot says "enter email" but also activates without it |
| OpenGate | 61,717 bot users; 24K channel subs | 7 days | 169 personal/mo; 279 duo/mo; 439 family/mo | Happ/key flow + support center | best support/ops UX, honest white-list caveat | depends heavily on third-party client layer |
| GROZA | 39,227 bot users; 91K channel subs | 48h | not recovered in WebK | Happ/key flow + white-list locations | explicit mobile white-list product, limits explained | very high claims: 25Gb/s, anti-block protection |
| Fen | public MAU not shown; 13K channel subs | 24h | 299/mo for 1 device | subscription link + common clients | clean constructor, traffic counters, white-list GB | channel mostly crisis posts; thin public trust layer |

## Channels and posts

4ebur posted 5 times in-window: routing mode, server load indicators, Bypass/masking, Happ/App Store workaround, platform update. Their posts are practical, not daily. Best feature signals are load colors and explicit routing modes.

MORI posted heavily after outages: compensation, key replacement, Happ/Windows/Android updates, then long educational posts attacking free VPNs, cheap VPNs, Russian jurisdiction, "state VPN", DNS leaks, WebRTC and fingerprinting. They are turning incidents into content.

NEO posted less, but with strong voice: Matrix branding, "MAKE NEO GREAT AGAIN", attacks/blocks, protocol roadmap, free proxy. The brand is memorable but high-risk.

NashVPN had a dense incident cluster around 2026-06-24..2026-07-05: tech works, blocks, update subscriptions, UK location workaround, Poland works, 5-10% user impact, Google DNS/RKN explanation. This is a useful incident-channel template.

OpenGate had the best operational cadence: Happ migration, key update instructions, old-key shutdown, MTProto fallback, mobile servers, Belarus, Gemini, filtering traffic, App Store removal, new servers, AUTO UK. They explain what changed, who is affected, what to do.

GROZA posts are lower frequency but useful: 48h trial, promo codes, Durov/blocking news, Happ/INCY instructions, Telegram client retirement. Their repeated footer CTA is good.

Fen public channel is mostly crisis communication: attacks, hoster blocks, white-list servers, +3d compensation, then silence.

## Bot flows

### 4ebur

Start flow: `/start` -> visual welcome card -> "read news / support / instruction" -> button "Запустить". It is a mini-app-first bot, not a chat-first bot. In WebK the Mini App prompt appeared but launch did not render.

Useful idea: public bot profile links news and support; the chat itself pushes users into app/web UI.

### ArtVPN

Start flow: video instruction -> welcome copy -> 3 days free -> button "Получить бесплатный доступ". Trial activated without payment and generated a subscription URL. Platform buttons: iPhone, Android, MacOS, Windows. iOS/Android use Happ and copy/paste subscription import.

Bot commands:

- `/op` Оплатить VPN
- `/lk` Личный кабинет
- `/promo` Получить бонус
- `/help` Техподдержка
- `/bd` Получить бесплатный доступ
- `/bot` О боте

Tariffs:

- 2 devices: 30d 250, 90d 650, 180d 1250
- 5 devices: 30d 490, 90d 1290, 180d 2490
- Lava payments, no subscriptions/auto-charges.

### MORI

Start flow: `/start` -> large visual "MESH-net loading" card -> account status with active MORI keys and HAPP subscriptions -> "choose section below". Telegram Web showed only `/start` as command and profile button "Open App". Mini App launch prompt appeared, but content did not render in WebK.

Important observed issue: Telegram Ads from Secure.VPN appeared inside MORI's bot surface. Competitors are actively buying this intent.

### NEO

Start flow: Matrix-style anti-censorship copy -> language buttons -> device setup. Russian copy says users came because "they want to take your freedom", then promises to disable state censorship, encrypt traffic, hide IP, and try to remove ads.

Bot commands:

- `/menu` Main menu
- `/topup` TopUp balance
- `/devices` Connected devices
- `/proxy` Private Proxy
- `/invite` Invite friends

Tariff/topup:

- tariff NEO: 222/mo
- 111 for 2 weeks
- 222 for 1 month
- 667 for 3 months
- 1332 for 6 months
- 2222 for 1 year, -16%

Devices:

- plan 2 devices
- protocol Vless
- command `/protocol`
- advice: change protocol if VPN does not work or is slow
- private proxy only for paying/regular clients.

### NashVPN

Start flow: product intro -> main menu.

Menu:

- Получить VPN
- Доступные локации
- Пригласить
- Помощь
- Как установить?

Tariffs:

- 1 month 299
- 3 months 790
- 6 months 1390
- 1 year 2690

Locations:

- Austria, Czechia, Finland, France, Kazakhstan, Latvia, Netherlands, Poland, Russia, "white-list bypass", Sweden, Turkey, UK, USA.
- Claim: every location has at least 1Gbps channel.

Install menu:

- iPhone/iPad
- Android
- Mac
- Windows
- Android TV
- "Узнать о VPN"

### Kosmos

Start flow: greets Telegram account by display name, says email is required, but immediately activates a new account and grants 14-day free test. This is powerful but inconsistent.

Install flow:

- iPhone/iPad
- Android
- MacOS
- Windows 10-11

iPhone/iPad/Mac instruction:

- download "Космос VPN" from App Store;
- click "Подключить автоматически";
- fallback manual link import.

This is the closest to POKROV's app-first strategy. The 14-day trial is the most aggressive trial in the set.

### OpenGate

Start flow: pinned community-channel CTA -> main intro -> 7-day trial.

Menu:

- Протестировать бесплатно 7 дней
- Подключение
- Оплата (Тарифы)
- Поддержка
- Бонусная программа
- Инструкции по подключению
- Новости и обновления

Tariffs:

- Personal, 3 devices: 169/mo, 449/3mo, 859/6mo, 1349/year
- Duo, 6 devices: 279/mo, 749/3mo, 1429/6mo, 2239/year
- Family, 10 devices: 439/mo, 1889/6mo, 2859/year

Notable copy:

- YouTube without ads and restrictions.
- White-list conditions are not guaranteed and are not grounds for refund.
- Renewal through "Мои подписки" / `/my_sub`.

Instructions:

- iPhone/iPad, Android, macOS, Windows, AndroidTV, Huawei, Linux
- "Не работает сервис"
- "Низкая скорость"

Best support UX in the group.

### GROZA

Start flow: high-claim intro -> trial/buy/proxy.

Claims:

- private servers with block protection;
- speed up to 25Gb/s;
- no ads/no crashes;
- all platforms;
- white-list 1-5 for mobile internet;
- trial key 48h.

Menu:

- Пробный период
- Купить VPN | Продлить
- Прокси Телеграм

Purchase text:

- 1 key = 1 device;
- 7 countries;
- no auto-charges;
- auto-select 1/2 recommended;
- Russia for YouTube without ads;
- white-list LTE locations for mobile internet;
- Wi-Fi 1000GB/mo;
- mobile white-list 100GB x10, where 1GB mobile = 10GB usage.

Prices were not visible in WebK after the long purchase message; likely lower inline buttons did not render in the captured viewport.

### Fen

Start flow: 24h trial -> "Забрать" -> subscription URL -> platform selection.

Trial:

- 24h
- 1 device
- expires 2026-07-09 16:48 MSK in captured session

Platforms:

- iOS
- Android
- Android TV
- Windows
- macOS

Main menu:

- Подключиться
- Устройства
- Докупить гигабайты
- Купить VPN
- Как подключить VPN
- Пригласить друзей
- Не работает VPN?

Subscription status:

- current plan blank during trial
- total traffic unlimited
- white-list traffic 10GB

Tariff constructor:

- period 1 month
- devices 1
- total 299
- controls: period, devices, promo code, continue/order.

## What to copy for POKROV

1. App-first proof like Kosmos, but cleaner: "download POKROV app -> login -> app shows current access/update". Keep our GitHub release truth and beta honesty.
2. OpenGate support menu: platform instructions plus "does not work" and "low speed" as first-class buttons.
3. Nash incident workflow: short updates, polls, city/provider collection, specific workaround, resolution post.
4. 4ebur load/routing UX: user-visible server load or simple "recommended/overloaded" status.
5. NEO protocol fallback UX: expose advanced protocol/fallback only when needed, not as the main happy path.
6. ArtVPN payment reassurance: Lava/card text, no card storage, no auto-charges, support route.
7. GROZA/Fen white-list accounting clarity if POKROV ever ships a similar mobile-operator mode: show separate limits and explain coefficient.
8. Repeated footer CTA in channels: bot, support, instructions, news.

## What to avoid

1. Unsupported "самый", "невозможно забанить", "до 25Gb/s", "полная анонимность", "защита от всех блокировок".
2. Contradicting site, channel, and bot pricing like MORI.
3. Hidden tariffs until after `/start` only. POKROV should show trial and current beta limits before the user commits.
4. Overdependence on third-party clients. This is where POKROV's native app can win.
5. Constant "update subscription daily" as a normal instruction. If update is needed, make app-led and explain why.
6. No-refund language without careful beta/support policy.
7. Publishing raw subscription links or user IDs in screenshots.

## POKROV action plan

Near-term:

- Add a public Telegram post template: incident / app update / install help / provider-specific issue.
- Add support bot quick replies mirroring OpenGate: install, not working, low speed, payment, account, app update.
- Add channel footer: main bot, support bot, install/update page, known issues.
- Add public "current app install/update status" post or page for Android/Windows beta.
- Add a competitor-safe pricing/trial block in bot welcome: 5-day trial, no auto-update claim, beta status.

Product:

- Consider a server health indicator in app/admin: recommended / busy / degraded.
- Consider an explicit advanced fallback section: sing-box default, xray only advanced.
- Consider provider/city collection in support flow.
- Keep app-first positioning: no endless third-party client instruction maze.

Copy:

- Use direct confidence, not fantasy claims: "works on supported routes", "we monitor failures", "we show what to do".
- Do not attack competitors legally. Talk about concrete user pain: blocked app, broken route, unclear support, hidden renewal.
- Turn POKROV's shorter 5-day trial into quality: "enough time to test on your real phone, home Wi-Fi, mobile network, and Windows".

## Notes and gaps

- Telegram WebK sometimes failed to render mini apps after launch: 4ebur and MORI.
- GROZA prices were not recovered inside WebK after the long purchase copy.
- Raw screenshots include trial keys/links for ArtVPN, Fen, Kosmos and a Telegram account ID in MORI. Treat raw evidence as private.
- Public channel post tables were built from t.me/t.me-s/TGStat/public pages plus bot evidence. Exact view counts are snapshot-time values.
