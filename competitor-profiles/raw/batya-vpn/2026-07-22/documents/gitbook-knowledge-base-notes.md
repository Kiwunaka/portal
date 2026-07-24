# Батя VPN GitBook Knowledge Base — Audited Notes

**Captured:** 2026-07-22<br>
**Public root:** https://batyavpn.gitbook.io/guidance/<br>
**Machine-readable index:** https://batyavpn.gitbook.io/guidance/llms.txt<br>
**Machine-readable full corpus:** https://batyavpn.gitbook.io/guidance/llms-full.txt<br>
**Full-corpus snapshot fingerprint:** 44,868 UTF-8 bytes; SHA-256 `decc487dc149f4236b6944b70e0070d22ddcef55c6e4c1acea00cfb4c651eca5`; HTTP ETag `6d45f080bec1d30a02555236d19a54bf`.

These are paraphrased product/audit notes. Live access keys, user IDs and private invite tokens are not retained.

## Information Architecture

The public knowledge base contains thirteen indexed pages:

1. root/intro;
2. bot menu/navigation;
3. subscription payment;
4. Android setup;
5. iOS/iPadOS setup;
6. Windows setup;
7. macOS setup;
8. Android TV setup;
9. tariffs;
10. referral system;
11. FAQ;
12. User Agreement;
13. Privacy Policy.

The **Menu and navigation**, **Referral system** and **FAQ** pages currently have headings but no substantive body. The root promises step-by-step device setup, FAQs and usage recommendations, so those empty destinations are a clear documentation dead end.

Persistent outbound destinations:

- purchase/setup bot: `https://t.me/MyBatyaVPN_bot`;
- support: `https://t.me/batyavpnhelp`;
- generic client project: `https://v2raytun.com/`;
- Android client: Google Play package `com.v2raytun.android`;
- iOS/macOS client: App Store item `id6476628951`.

The current native Android app and in-app legal hub use other support/account destinations, so this GitBook represents an older Telegram-key distribution model still exposed from Google Play.

## Purchase Flow

The payment guide sends users to the Telegram bot and instructs them to:

1. press **Купить подписку**;
2. select 1 month, 3 months, 12 months or lifetime;
3. confirm and leave Telegram for a payment page;
4. pay by Visa/Mastercard/MIR, SBP, Mir Pay, SberPay or T-Pay;
5. wait a few seconds for automatic activation;
6. press **Настроить VPN** and continue into device instructions.

The page shows 249 / 599 / 1,599 / 3,490 RUB. Its separate tariffs page instead shows **1,499 RUB** for one year. The current native app and current VPN-specific offer show 1,599 RUB, making the tariffs page stale.

## Device Setup Instructions

### Android

Requirement: Android 7.0+.

The guide does not install the current native Батя app. It tells users to choose Android in the Telegram bot, install third-party **v2RayTun** from Google Play, return to Telegram, press **Продолжить настройку VPN**, follow **Установить ключ VPN**, land back in v2RayTun and press its center connect button. First-use Android VPN consent is acknowledged.

### iOS and iPadOS

Requirement: iOS 16.0+.

The same Telegram flow installs v2RayTun from Apple item `id6476628951`. **Подключить в приложении VPN** deep-links the key into v2RayTun; the user then presses its center button and accepts the system VPN permission.

### Windows

Requirement: Windows 8.1+.

The page offers both a GitBook-hosted `.exe` and `v2raytun.com`. It tells users to install v2RayTun, change the shortcut compatibility setting so the client always runs as administrator, copy their access key from Telegram, choose **Import from clipboard** under the plus menu and press the center connect button. The audit did not download or execute the public installer.

### macOS

The page points to the same App Store v2RayTun item and `v2raytun.com`, then repeats the clipboard-import flow. Its requirement line incorrectly says **Windows 8.1 or newer**, and the final import illustration is reused from the Windows instructions. This is a visible copy/paste quality failure on a security-sensitive setup path.

### Android TV

The Android TV page documents the newer first-party app:

- install **Батя VPN — Быстрый VPN** from Google Play by searching for “Батя”;
- if Play is unavailable on an Android-based television, download a GitBook-hosted APK and sideload it by USB/Downloader/ADB;
- choose Telegram login, scan the TV QR from a phone and confirm in the bot to transfer an active subscription; or continue as guest for a three-day trial;
- use the central switch to connect, **Смени сервер** to retry/change route, and Settings for generated ID, tariff, support, privacy and logout;
- purchase 1 / 3 / 12 months or lifetime from the Subscription tab.

The compatibility matrix separates Android TV/Google TV brands, Fire OS devices that permit sideloading, and closed systems such as Samsung Tizen, LG webOS and Hisense VIDAA where the APK cannot run. This explains the QR scanner found in the current phone app. The direct APK path is convenient but adds a second distribution channel whose signing/update provenance should be made explicit.

## Tariffs and Referral Content

The tariffs page says every plan covers all devices and claims no connection-count limit on the monthly plan. It lists 249 RUB/month, 599 RUB/3 months, **1,499 RUB/year**, and 3,490 RUB/lifetime. The current app shows 1,599 RUB/year and the current offer recommends no more than five simultaneous devices, so both price and device-limit framing drift across sources.

The indexed referral page is empty. The only functional explanation currently lives inside the app cabinet, where both inviter and invited user are promised 30 days after the friend's first payment.

## Agreement and Privacy

The GitBook User Agreement names no company. It describes access keys/configuration, requires Telegram, says only Telegram ID is collected, permits refunds when service was not delivered or was inadequate, and gives support up to three working days to review a refund request. Contacts claim support from 09:00–23:00 Moscow time with an average response up to ten minutes.

The GitBook Privacy Policy likewise says only Telegram ID is collected, denies collection of browsing history and traffic contents, allows payment-processor transfer, promises deletion within 30 days after service use ends, and gives users deletion/withdrawal rights.

These live claims conflict with other current surfaces:

| Topic | Google Play / GitBook | Current app / HelpDesk offer |
| --- | --- | --- |
| Data collected | Play: none; GitBook: Telegram ID only | generated device/account ID, optional email, device/subscription/payment state, AppMetrica-labeled events |
| Data deletion | Play says no deletion mechanism | GitBook promises deletion within 30 days and explicit deletion rights |
| Provider | Play: F2P, ООО; GitBook: no legal entity | VPN offer: UNI PLAN TRADING LIMITED, Hong Kong |
| Support | GitBook: 09:00–23:00, average ≤10 min | app says 24/7; offer allows up to two working days |
| Support handle | GitBook: `@batyavpnhelp` | current app/legal surface also exposes `@batyavpnhelp_bot` |
| Trial | Android TV guide: 3 days | current app/store/offer: 5 days; reviews also mention 2 and 7 |
| Annual tariff | GitBook tariff page: 1,499 RUB | payment guide/app/offer: 1,599 RUB |

The result is not one canonical support/legal truth but at least three generations of it: legacy GitBook/Telegram-key instructions, current native-app/cabinet behavior, and the newer HelpDeskEddy legal set.
