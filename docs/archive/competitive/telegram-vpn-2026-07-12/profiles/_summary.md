# Telegram VPN competitors — summary

**Generated:** 2026-07-12
**Depth:** deep market pass
**Primary reports:** original market report (external snapshot: `../docs/competitive/telegram-vpn-2026-07-12/final-market-report.md`), wave 2 Russian summary (external snapshot: `../docs/competitive/telegram-vpn-2026-07-12/telegram-vpn-wave2-summary-ru.md`), wave 2 technical appendix (external snapshot: `../docs/competitive/telegram-vpn-2026-07-12/telegram-vpn-wave2-and-apk-analysis.md`)

## Landscape

Quattro лидирует как экосистема; Cats — как privacy-first login; OpenGate и Kosmos — как service UX; Nosok, Platina и Luma — как дистрибуционные машины. В расширенной выборке HitVPN лидирует абсолютным Telegram-охватом, Sota и Lagom — текущим app-backed ростом, Batya — массовой связкой bot + cabinet + branded app, а MantaRay — реальной глубиной Android routing UX. Kubik показывает худший release/privacy контур: Android Debug-подпись и огромный ad-tech стек.

## Comparison

| Конкурент | Модель | Entry price | Trial | Главная сила | Главный риск |
|---|---|---:|---:|---|---|
| Quattro | App + bot + cabinet | 300 ₽ | Не подтвержден в свежем проходе | Полный экосистемный контур | Сложность, расхождения surfaces, APK risks |
| Cats | Bot + anonymous web | 149 ₽ | 3 дня | Короткий код и упаковка | Потеря кода без recovery |
| OpenGate | Bot-first service | 169 ₽ | 7 дней | Support diagnostics | Меньший distribution scale |
| Kosmos | App + cabinet | 240 ₽ | 14 дней | Длинный trial и rescue | Менее сильный brand loop |
| Nosok | Bot + site + fallback | 250 ₽ | 1 день | Масштаб, direct install и Telegram fallback | Iframe incompatibility, конфликтующая копия |
| MORI | Mini App + content | 250/299 ₽ | Источники расходятся | Бренд и education | Расхождения claims |
| Luma | Proxy funnel + VPN | 149 ₽ | 3 дня / 25 ГБ / 1 устройство | Proxy-to-paid acquisition и полный bot funnel | Метрики несопоставимы; destructive link reset |
| Platina | Bot + reseller engine | 189 ₽ | Тестовый 30 ГБ | Referral, gifts, franchise | Hourly spam и слабый QA |
| Nash | Bot + multi-platform | 299 ₽ | Не подтвержден | Incident comms | Частый канал при снижении подписчиков |
| NEO | 3-tier bot VPN | 222 / 333 / 444 ₽ | Не подтвержден | Devices, protocols, private proxy и 3 языка | Plan switch без confirmation; TGStat не индексирует канал |
| 4ebur | Mini App + stores | 299 ₽ | Не подтвержден | Store distribution и mascot | Небольшой канал |
| ArtVPN | Bot + lifecycle | 250 ₽ | 3 дня | Сильная expiry sequence | Давление и сложная affiliate copy |
| GROZA | Bot + mobile bypass | Цена не восстановлена | 48 часов | Trial reactivation | Агрессивные claims |
| Fen | Bot-first | 299 ₽ | 24 часа | Простая модель | Scheduler spam |
| HitVPN | Bot + massive channels + apps | В момент прохода bot maintenance | Не проверен | 4.61M channel / HitRay 10M+ | Prize traffic, control-plane outage, broken APK host |
| Shuka | Gated bot + site + MantaRay | 299 ₽ | 3 дня / 10 ₽ | 1.29M channel и сильный routing client | Mandatory gate; MantaRay не доказан как owned app |
| Atlanta | Bot + app beta + external clients | 199 ₽ | 3 дня | Time + GB + referral + partner monetization | Broken partner stats, fragmented client journey |
| Batya | Bot + cabinet + branded apps | 299 ₽ | 5 дней | Узнаваемый бренд и 1M+ Android app | Giveaway dependence, privacy/legal conflicts |
| Durev | Bot + email-linked site + app | 459 ₽ | 1 день / 17 ₽ | Recurring referral, gifts, deep help | Meme-token coupling and domain fragmentation |
| OverSecure | Subscription client APK | Provider-dependent | Нет | Focused client and split routing | Broad app visibility and sideload/update permissions |
| MantaRay | BYO configuration client | N/A | N/A | Best routing builder and diagnostics | Broad usage/package access; routing telemetry |
| Kubik | Free/ad-funded app | Site premium | 5 GB/month + 60-min sessions | Anonymous free entry | Debug cert and extreme ad/attribution stack |

## Positioning map

| Сегмент | Простые | Сложные |
|---|---|---|
| Низкая цена | Cats, OpenGate, Platina, NEO | Nosok, Luma |
| Средняя/высокая цена | ArtVPN, Nash | Quattro, Kosmos, MORI |
| Tool / non-subscription | ByeByeDPI | Quattro power-user app |

## Key takeaways

1. Побеждает связка app + cabinet + bot, а не бот сам по себе.
2. Бесплатный fallback удерживает лучше обычного купона.
3. Короткий код Cats — лучший вход, но recovery надо проектировать сразу.
4. Двусторонняя referral reward понятнее MLM и franchise.
5. Notification governor — конкурентное преимущество: рынок реально спамит.
6. Proxy-funnel Luma эффективен, но его охват нельзя выдавать за обычную аудиторию канала.
7. Текущий Nosok — одноуровневые 50%; Luma — 20% баллами. Старое 50/25/15 для Nosok больше не является текущей bot-механикой.
8. Огромная аудитория не заменяет резервный control plane: HitVPN был недоступен прямо во время прохода.
9. MantaRay задаёт новый benchmark для routing presets, rule builder и local diagnostics.
10. Нужен release guard против debug-сертификатов и неожиданного роста SDK/permissions: Kubik проваливает оба пункта.
11. Batya доказывает силу человеческого brand voice, но розыгрыши и бонусы за отзывы портят качество growth/store signals.
12. Atlanta хорошо монетизирует время, трафик и referral, но раздробленность surfaces и сломанная partner analytics делают модель рискованной.
13. Versioned first-party APK + hash + signing fingerprint должны быть обязательным каналом, а не mutable `latest.apk` или Telegram document.

## Logged-in TGStat Snapshot

- Quattro: +51 999 за месяц — максимальный абсолютный прирост.
- Nosok: +24 913; в июле TGStat показывает 97 упоминаний в 14 каналах и охват размещений 568 765.
- Platina: +13 536 при почти пустой публичной таблице привлечения; вероятны bot/referral/off-platform источники.
- Cats: +9 752, примерно +94% к восстановленной базе начала окна — самый быстрый относительный рост среди обычных каналов, но mandatory gate и cross-promo не позволяют назвать его чисто органическим.
- Luma: +12 127, примерно +200% к начальной базе, но ERR 638.5% и охват выше базы в 6.4 раза делают метрики отдельным proxy/repost классом.
- MORI: −2 940; Nash: −996; 4ebur: −41. Это чистая динамика подписчиков канала, не churn платящих VPN-клиентов.
- Пол, возраст и география в TGStat закрыты для конкурентов даже после логина: раздел доступен только подтвержденному владельцу канала.

## Public TGStat Widget — Wave 2

- HitVPN: 4 607 596 subscribers, +386 200/month, average reach 2 236 043, ERR 48.5%.
- Sota: 794 820, +105 221/month; roughly +15.3% and the fastest large app-backed channel in the wave.
- Lagom: 167 392, +21 990/month; roughly +15.1%, backed by a 5M+ Android app.
- Shuka: 1 291 350, +53 455/month; reach fields in the widget are invalid/empty and must not be interpreted.
- Atlanta: 801 930, +40 909/month, while its own Android beta remains at only 1K+ installs.
- Batya: 185 479, +11 776/month, average reach 81 710.
- Durev: 58 109, +2 205/month; bot MAU is much larger than channel size.
- BlancVPN: +547/month and −287/week — mature reach, nearly stalled growth.
- GenVPN: −301/month; current channel/app momentum is weak despite very high posting cadence.
- The public widgets expose summary metrics but not demographics, full growth-source tables or subscriber quality.

## Gaps for POKROV

- Нет полноценного web cabinet уровня Quattro.
- Нет короткого privacy-first login уровня Cats.
- Нужны symptom-based support flows уровня OpenGate.
- Нужен fallback для восстановления и продления.
- Нужны dedupe, quiet hours и suppression для lifecycle.
- Нужен публичный продуктовый changelog.

## Profiles

- [Quattro](quattro-vpn.md)
- [Cats VPN](cats-vpn.md)
- [Nosok VPN](nosok-vpn.md)
- [VPN Platina](platina-vpn.md)
- [Luma VPN](luma-vpn.md)
- [4ebur](net4ebur.md)
- [ArtVPN](artvpn.md)
- [MORI](mori-vpn.md)
- [NEO](neo-vpn.md)
- [NashVPN](nashvpn.md)
- [Kosmos VPN](kosmos-vpn.md)
- [OpenGate](opengate-vpn.md)
- [GROZA](groza-vpn.md)
- [Fen VPN](fen-vpn.md)
- [HiroVPN app](hiro-vpn.md)
- [ByeByeDPI app](byebye-dpi.md)
- [HitVPN](hitvpn.md)
- [Shuka VPN](shuka-vpn.md)
- [Atlanta VPN](atlanta-vpn.md)
- [Batya VPN](batya-vpn.md)
- [Durev VPN](durev-vpn.md)
- [FineVPN](finevpn.md)
- [OverSecure app](oversecure.md)
- [Kubik VPN app](kubik-vpn.md)
- [MantaRay app](mantaray.md)
- [Sota VPN](sota-vpn.md)
- [Lagom VPN](lagom-vpn.md)
- [BlancVPN](blancvpn.md)
- [GenVPN](genvpn.md)

## Evidence

- Full report (external snapshot: `../docs/competitive/telegram-vpn-2026-07-12/final-market-report.md`)
- Saved broad pass (external snapshot: `../docs/competitive/telegram-vpn-2026-07-08/full-bot-site-webapp-research.md`)
- Quattro deep dive (external snapshot: `../docs/competitive/telegram-vpn-2026-07-09/quattro-bot-channel-deep-dive.md`)
- APK report (external snapshot: `../docs/competitive/telegram-vpn-2026-07-09/apk-competitor-static-analysis.md`)
- Wave 2 bot/channel/APK analysis (external snapshot: `../docs/competitive/telegram-vpn-2026-07-12/telegram-vpn-wave2-and-apk-analysis.md`)
- Wave 2 Russian summary (external snapshot: `../docs/competitive/telegram-vpn-2026-07-12/telegram-vpn-wave2-summary-ru.md`)
- Wave 2 redacted session ledger (external snapshot: `raw/market-wave2/2026-07-12/scrapes/session-notes.md`)
