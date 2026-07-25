# Pipster — Mobile App Competitor Profile

**Snapshot date:** 2026-07-22<br>
**Status:** `DEEP PASS COMPLETE WITH BLOCKERS`<br>
**Android package:** `com.vipin.pipster`<br>
**Installed version:** 2026.7.7<br>
**Install source:** Google Play

Evidence root: [`raw/pipster/2026-07-22/`](raw/pipster/2026-07-22/)

## Audit Checkpoint

- ExpressVPN and Android Chrome were force-stopped before this pass; both process IDs were absent, `tun0` was absent and Android had no always-on/lockdown VPN package.
- Only Pipster will be exercised during this pass; all other VPN competitors remain closed.
- Installed Google Play artifact: version 2026.7.7, code 174, `minSdk=27`, `targetSdk=35`; installed/updated 2026-07-22 02:16 local emulator time.
- No purchase, trial activation, public review/post, support submission or destructive account action is authorized.

## Cold Launch And Notification Gate

Pipster cold-launched directly into its portrait `MainActivity` in about 2.47 seconds. The first stable frame is the Android 14 notification permission dialog over a branded account-choice page, so notification access is requested before the user sees any VPN value or service explanation. Baseline process memory was approximately 108.1 MB total PSS / 232.1 MB RSS with no swap; `tun0` remained absent.

Behind the permission dialog the acquisition page already exposes two paths: **«Войти»** and outlined **«Продолжить без регистрации»**, plus the promise **«Самое время войти в приложение»**. Evidence: [cold launch](raw/pipster/2026-07-22/screenshots/01-isolated-launch.png), [UI tree](raw/pipster/2026-07-22/ui/01-isolated-launch.xml).

Notification access will be denied for this audit so the product can be inspected without granting a nonessential permission.

After denial, the branded welcome is a clean, low-density portrait screen: floating ninja mascot, large violet headline **«Добро пожаловать в приложение Pipster»**, primary **«Войти»** and equal-width outlined **«Продолжить без регистрации»**. There is no feature explanation, price, trial claim or trust proof before account choice. Evidence: [account choice](raw/pipster/2026-07-22/screenshots/02-account-choice.png), [UI tree](raw/pipster/2026-07-22/ui/02-account-choice.xml).

## Account Entry

The account selector offers three distinct methods:

1. **«Войти по Email»**;
2. **«Войти по QR-коду»**;
3. **«Войти с Яндекс»**.

The legal acknowledgement is passive copy at the bottom with separate links to the User Agreement and Privacy Policy; choosing a login method is treated as acceptance. Evidence: [account selector](raw/pipster/2026-07-22/screenshots/03-login-entry.png), [UI tree](raw/pipster/2026-07-22/ui/03-login-entry.xml).

Email entry is passwordless: Pipster asks for an email, then says it will send a verification code. The same form contains a collapsible acquisition field **«У меня есть реферальный код»**, accepting either a referral link or code before account creation. There is no separate “register” route; the email-code flow appears to unify sign-in and signup. The later authorized registration attempt reached the four-digit code screen; no address or code is retained in the repository. Evidence: [email entry](raw/pipster/2026-07-22/screenshots/04-email-entry.png), [referral field](raw/pipster/2026-07-22/screenshots/05-email-referral-expanded.png).

The QR route generates a five-minute sign-in code and instructs the user to scan it from another device where Pipster is already authenticated. The token-bearing QR image was intentionally not retained in the repository. The Yandex route opens Android Chrome at Yandex's OAuth authorization endpoint; no Yandex identity, credentials or permissions were accessed. Chrome was then force-stopped.

## Anonymous Entry And First Upsell

**«Продолжить без регистрации»** immediately opens a full-screen gradient upsell before the VPN home. It promises **«Полный доступ без ограничений»** and **«полный доступ ко всем функциям приложения всего за 30₽»**, with primary **«Попробовать»**, secondary **«Не сейчас»** and a separate close icon. The screen does not state what the 30 RUB buys, the term, renewal price, auto-renewal or trial conditions. No purchase flow was opened. Evidence: [first upsell](raw/pipster/2026-07-22/screenshots/06-first-upsell.png), [UI tree](raw/pipster/2026-07-22/ui/06-first-upsell.xml).

In this navigation sequence, the first dismissal unexpectedly exposed the prior email-entry screen and Back reopened the upsell before the app eventually reached Home. This is a concrete back-stack inconsistency, not a generalized crash claim. Evidence: [unexpected email return](raw/pipster/2026-07-22/screenshots/07-email-return-after-upsell.png).

## Anonymous Home

The free home makes the product model immediately legible:

- **0.5 GB** monthly/period quota shown as a progress bar (`0.0 GB` used);
- **+200 MB** for watching a video ad;
- **Автосервер** with a visible **«Сменить»** route;
- large stateful mascot, **«VPN выключен»** and primary **«Подключить»**;
- persistent red **«Купить»**, notification bell with an unread dot and menu/profile entry.

This is stronger free-tier communication than a generic locked paywall: the remaining allowance and exact ad reward are visible before connection. Evidence: [anonymous Home](raw/pipster/2026-07-22/screenshots/08-anonymous-home.png), [UI tree](raw/pipster/2026-07-22/ui/08-anonymous-home.xml).

## Server Choice

The selector has search, a current **Автосервер / Самый быстрый сервер** card and the same automatic option at the top of “Все сервера.” The captured paid list contains Germany, Lithuania, Netherlands, Poland, Russia, Romania, USA, Singapore, Finland, Switzerland, Sweden and Estonia. Every named country shows a lock; the anonymous tier can select only Auto. Tapping a locked row did not open an upgrade explanation in this pass, wasting a high-intent conversion moment. Evidence: [server list](raw/pipster/2026-07-22/screenshots/09-server-list.png), [lower list](raw/pipster/2026-07-22/screenshots/10-server-list-lower.png).

## In-App Notifications And Growth

The bell is a persistent inbox independent of Android notification permission. Two server-driven messages were available to a fresh anonymous session:

- **«Что делаете сегодня вечером? 👉👈»** invites users to a Telegram-channel prize game for a chance at a free subscription and names `@pipster_channel`; the handle is plain, non-clickable text rather than a deep link.
- **«🔔 Продление подписки»** explains that Pipster moved payments to a new YooKassa store, existing auto-renewals will stop, subscriptions will simply expire, and customers must repurchase once in-app or in the personal cabinet to restore auto-renewal.

The second item is unusually honest operational communication and direct evidence of a payment-stack migration. The first is a lightweight giveaway/community retention loop but has a dead-end CTA. Evidence: [inbox](raw/pipster/2026-07-22/screenshots/13-notifications.png), [giveaway detail](raw/pipster/2026-07-22/screenshots/15-notification-evening-loaded.png), [YooKassa migration](raw/pipster/2026-07-22/screenshots/16-notification-renewal.png).

## Menu, Localization And Support

The anonymous menu contains:

- theme: System / Dark / Light;
- language: Russian, English, German, French, Portuguese and Spanish;
- support;
- destructive **«Завершить гостевую сессию»**;
- exact app version.

Support offers Email and Telegram. Telegram opens the public `@pipstervpnsupport` contact page in a Chrome Custom Tab; the page directs users to `@pipstervpn_bot` and states 08:00–21:00 Moscow support hours. No message was sent. The guest-session termination control was not used because it would destroy the current anonymous state. Evidence: [menu](raw/pipster/2026-07-22/screenshots/17-menu.png), [theme picker](raw/pipster/2026-07-22/screenshots/18-theme-picker.png), [language picker](raw/pipster/2026-07-22/screenshots/19-language-picker.png), [support chooser](raw/pipster/2026-07-22/screenshots/20-support-entry.png), [sanitized destination notes](raw/pipster/2026-07-22/logs/support-destination-notes.md).

The persistent **«Купить»** control does not reveal tariffs to an anonymous user; it routes back to the email-code account form. This creates an account wall between purchase intent and price discovery. Evidence: [Buy -> email gate](raw/pipster/2026-07-22/screenshots/21-buy-entry.png).

## Rewarded-Ad Path

The promised +200 MB opens a full-screen **Yandex Mobile Ads** rewarded placement. The captured unit was a 16+ Yandex Maps video with a ten-second countdown, persistent Download CTA, a second end-card page and a small top-right exit affordance; Android Back was blocked on both the video and end card. No advertiser CTA was clicked.

After the full video/end-card sequence was closed, Home still showed **0.5 GB**, not 0.7 GB, even after a refresh wait. Therefore the +200 MB reward was **not observed** in this exact guest-session run. This may be a callback/account-state defect rather than proof that rewards never work. Evidence: [reward video](raw/pipster/2026-07-22/screenshots/22-reward-ad-entry.png), [end card](raw/pipster/2026-07-22/screenshots/24-reward-ad-end.png), [unchanged quota](raw/pipster/2026-07-22/screenshots/26-home-after-reward.png).

## Registration Checkpoint

The authorized Gmail address reached the four-digit verification-code screen. A resend was requested after the first message did not arrive, but Gmail still exposed only an older Pipster code, which the current session did not accept. A later isolated retry ended the captured guest session, resubmitted the authorized address, waited through the resend cooldown and successfully triggered **«Отправить код повторно»**; Gmail still received no new message. No email address, one-time code, token-bearing screen or raw message is retained in the repository. Registration and account-gated pricing are therefore `BLOCKED_BY_DELIVERY`, not falsely marked passed.

## Controlled Free Connection

The first **«Подключить»** opens the standard Android VPN consent dialog. After approval Pipster does **not** connect immediately: it forces a Yandex Mobile Ads video with an initial 34-second countdown and a separate end card. Only after both are closed does Auto establish `tun0` and select Germany.

The resulting session passed a controlled ICMP connectivity check. Android routing used `tun0`; the app reported **VPN подключен**, and an external exit check resolved to Frankfurt am Main, Germany (AS58212 / dataforest GmbH). Tunnel MTU was 1400; the advertised DNS set was local tunnel resolver `[IPv4 address omitted]` plus `[IPv4 address omitted]` and `[IPv4 address omitted]`. The exact exit IP is not retained in the repository. Evidence: [Android consent](raw/pipster/2026-07-22/screenshots/27-connect-consent-or-state.png), [34-second pre-connect ad](raw/pipster/2026-07-22/screenshots/28-connect-pre-roll-ad.png), [connected Home](raw/pipster/2026-07-22/screenshots/31-post-connect-ad-state.png), [runtime notes](raw/pipster/2026-07-22/logs/tunnel-runtime-notes.md).

Connected Home adds **«Не работает?»** and **«Попытаться исправить (1/4)»**, suggesting a four-stage self-repair ladder. In the actual run, tapping stage 1 immediately tore down `tun0` and launched another Yandex ad with a **98-second** countdown before explaining or applying any repair. That ad was aborted by force-stopping Pipster to conserve resources; stages 2–4 remain unexecuted. Evidence: [98-second repair ad](raw/pipster/2026-07-22/screenshots/32-repair-action-98s-ad.png).

The free tier is therefore functional but aggressively ad-gated: one long ad before the first tunnel, a separate ad-reward surface whose promised quota failed to appear, and an even longer ad in the troubleshooting path. This is monetization at the point of greatest urgency and a major trust/retention risk.

## Public Product, Commercial And Legal Surface

The current Russian landing page shows monthly Lite/Silver/Gold/Diamond offers at 249/499/649/1,199 RUB for 1/3/5/10 devices and a three-day 30-RUB trial. The Android anonymous upsell exposes only **30 RUB** and omits the three-day term, follow-on price and renewal. The public agreement fills in the missing commercial mechanics: paid plans renew every 30 days, debit 24 hours before renewal, require cancellation at least 24 hours before period end and do not refund prior periods. It also confirms that a full-screen Yandex video is mandatory before every free connection, matching runtime.

Pipster has a deeper growth cabinet than its anonymous app reveals: referral code/link, invited-friend benefit, percentage revenue share, friend/accrual/balance statistics, support-mediated withdrawal and server-fed payout minimum. Subscription controls include pause/resume/switch, device removal, immediate full-price upgrades without prorating and deferred downgrades that remove devices. Exact referral percentages and payout minimum remain account/server gated.

The public surface has material trust debt. Its privacy policy headlines “only email” but later permits website IP/geography, usage metadata, support metadata, diagnostics, analytics, cookies, advertising and international processing. The account web bundle initializes Yandex Metrika/Webvisor, appends a Yandex client ID to download links and contains a first-party **Lead** conversion endpoint that accepts user email; no authenticated conversion request was executed, so downstream delivery is not claimed. Policy/footer addresses for both Russian OOO PROMDEVELOPMENT and Kazakhstan LLP ViPiN are stale against current registry data, while the payment memo still names TipTop Pay Kazakhstan despite the in-app YooKassa migration notice.

Distribution is broad and deliberately tracked: Google Play, direct APK, iOS, Windows EXE, macOS and Chrome/Edge/Firefox all pass through AppMetrica redirects. The English macOS button currently ends at a different, missing App Store listing (HTTP 404), while the Russian macOS route is live. Details and retained source files: [public-surface notes](raw/pipster/2026-07-22/logs/public-surface-notes.md).

Google Play creatives use a coherent violet/black system with the robot mascot and oversized glossy shield/trophy/rocket props, but mix old and new product states. Portrait cards still push account creation and imply open country choice, while a landscape set shows the newer guest path; none communicates the real ad/quota gate. Six unique assets (plus store duplicates) are retained under [`store-creatives/`](raw/pipster/2026-07-22/store-creatives/).

The current Firefox package reveals a second free model: 30-minute anonymous proxy sessions and 60-minute authenticated sessions, after which the extension clears the proxy and requires reconnection. It performs PAC-based split routing so Russian domains bypass the proxy, warns about competing proxy extensions and requires explicit private-window access before connecting. The store's ad-blocker/anti-tracking promise was not corroborated by a local blocking listener or bundled filter list in the inspected package; server-side filtering was not tested.

## Completion And Blockers

`PASS`: anonymous onboarding, menu/localization/support, notifications, server selection, rewarded-ad path, Android VPN consent, controlled free tunnel, exit geography, repair-entry behavior, static APK/package review, public pricing/policies/payment memo, legal entities, account-web structure, store creatives, release history, redirect mapping and Firefox package review.

`BLOCKED_BY_DELIVERY`: authenticated mobile/cabinet pricing and live referral values because two current email-code attempts plus resend produced no current message. The prior stale code was rejected.

`BLOCKED_BY_ACCESS`: paid tunnel/server behavior, paid billing checkout, destructive account deletion, repair stages 2–4 and an authenticated referral payout view. Purchases, trials and external messages were intentionally not executed.

Final hygiene: 89 retained Pipster files, 33 runtime screenshots, 27 non-sensitive UI dumps and 15 store creatives; zero zero-byte files and zero broken local Markdown links. Pipster and Android Chrome were force-stopped, `tun0` was absent, no always-on/lockdown VPN was configured, and a repository scan found no retained authorized Gmail address.
