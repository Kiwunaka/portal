# Competitor APK static analysis: Quattro, HiroVPN, ByeByeDPI

Дата: 2026-07-09
Фокус: Android APK/XAPK конкурентов, подпись, разрешения, native/core, SDK, backend URLs, продуктовые возможности, риски и выводы для POKROV.

## Status

Текущий статус: `STATIC_ANALYSIS_CAPTURED`.

POKROV statements in this report describe only the retained
`1.0.0-beta+20260608-hotfix` artifact, not newer source-tree or release-plan
state.

Проверено локально:

- `apkanalyzer apk summary`, `manifest permissions`, `manifest debuggable`, `manifest print`;
- `apksigner verify --verbose --print-certs`;
- JSON-отчеты из распаковки;
- Flutter assets, translations, settings/config JSON;
- DEX/native string dumps;
- APK file lists.

Ограничения:

- это статический разбор, без запуска приложений и без MITM;
- Dart source из Flutter AOT не восстановлен;
- сырые hardcoded tokens, Sentry DSN userinfo, payment/order IDs и похожие секреты в этот файл не перенесены;
- для HiroVPN анализ base APK и arm64 split смотрится вместе, потому что XAPK разнесен по split-артефактам.

## Разобранные копии

The `%TEMP%` paths below are historical local inspection locations, not
portable repository evidence. Raw APKs and extracted bundles are not committed;
the report records artifact/version observations only.

| App | APK/XAPK path | Extracted path |
| --- | --- | --- |
| Quattro 0.18.1 | `C:\Users\kiwun\AppData\Local\Temp\opencode\quattro\quattro.apk` | `C:\Users\kiwun\AppData\Local\Temp\opencode\quattro\apk\` |
| HiroVPN 1.17.1 | `C:\Users\kiwun\AppData\Local\Temp\opencode\hirovpn\hiro.xapk` | `C:\Users\kiwun\AppData\Local\Temp\opencode\hirovpn\apk\`, `arm64_out\`, `xapk\` |
| ByeByeDPI 1.7.6 | `C:\Users\kiwun\AppData\Local\Temp\opencode\byebyedpi\bbd.apk` | `C:\Users\kiwun\AppData\Local\Temp\opencode\byebyedpi\apk\` |
| POKROV beta reference | `C:\Users\kiwun\Documents\ai\POKROV-app\artifacts\releases\pokrov-app\1.0.0-beta+20260608-hotfix\pokrov-android-arm64-v8a.apk` | APK file list only |

## Executive Summary

Самый сильный коммерческий APK по production/distribution: `HiroVPN`. У них Google Play App Signing, SourceStamp, Play Billing, Huawei link, QR/ML Kit, Firebase/Auth/Messaging, Pairip license check, Sentry, AppsFlyer, AppMetrica, Yandex Ads, AdMob. Это зрелый acquisition/monetization комбайн, но privacy story слабая.

Самый полезный продуктовый APK для копирования фич, но не практик безопасности: `Quattro`. Внутри не просто кнопка "connect", а полноценный клиент: свой сервер, DNS, split tunneling по URL/app, blacklist, QR scanner, subscription refresh, traffic, referral, Telegram/email login. Но APK подписан Android Debug certificate, тянет Firebase/Measurement и содержит hardcoded local API token для `127.0.0.1:16756`.

Самый чистый по telemetry: `ByeByeDPI`. Это не коммерческий VPN, а DPI-bypass utility: VpnService, local SOCKS/proxy mode, Quick Settings tile, BootReceiver, 60 стратегий обхода и site lists. Нет Firebase, рекламы, AppMetrica, AppsFlyer, Sentry. Риски другие: self-signed distribution, broad storage/package permissions, низкая commercial packaging.

POKROV сейчас выигрывает у Hiro/Quattro по чистоте разрешений и отсутствию ad/analytics SDK в текущем beta APK. Но текущий `1.0.0-beta` APK тоже подписан Android Debug certificate. Это надо закрыть до любых сильных публичных claims про доверенную Android-дистрибуцию.

## Comparison Matrix

| Dimension | Quattro | HiroVPN | ByeByeDPI | POKROV beta reference |
| --- | --- | --- | --- | --- |
| Package | `ru.quattrocloud.vpnapp` | `com.hiro.vpn` | `io.github.romanvht.byedpi` | `space.pokrov.pokrov_android_shell` |
| Version | `0.18.1` / code `19` | `1.17.1` / code `78` | `1.7.6` / code `1760` | `1.0.0-beta` / code `2001` |
| Target SDK | `36` | `36` | `34` | parsed APK ok; manifest permissions verified |
| Debuggable | `false` | `false` | `false` | `false` |
| Signing | v2 only, Android Debug cert | base v2+v3+SourceStamp, Google Inc cert; arm64 split also v1 | v1+v2, self-signed developer certificate | v2 only, Android Debug cert |
| Main core | Flutter + `libnpvpnBox.so`, sing-box/SagerNet traces | Flutter + `libv2jni.so`, Xray/V2Ray stack + `libhev-socks5-tunnel.so` | native `libbyedpi.so` + `libhev-socks5-tunnel.so` | Flutter + `libbox.so` |
| VPN service | yes | yes | yes | yes |
| Quick Settings tile | yes | not observed in manifest | yes | not observed in current APK |
| Boot/autostart | `RECEIVE_BOOT_COMPLETED` present | not primary finding | `BootReceiver` present | not observed |
| Permissions count | 19 | 24 | 14 | 7 visible permissions |
| Query all packages | no | yes | yes | no |
| AD_ID | yes | yes | no | no |
| Billing | no Play Billing in base findings | Play Billing | no | no native billing in current APK |
| Telemetry/ads | Firebase/Measurement/Crashlytics signals | AdMob, Yandex Ads, AppMetrica, Firebase, AppsFlyer, Sentry | none found | none found in APK file list/source scan |
| Backend URLs | `auth.quattro-cloud.ru`, `quattro.app`, `npvpn.com` | `api.hirovpn.com`, `api.hellohiro.ru`, download/legal/storage domains | only donation/support URLs | POKROV first-party API/cabinet by product docs |
| Biggest strength | mature client controls + cabinet | distribution, billing, tracking, app-store stack | clean utility, presets, no tracking | clean app-first model, minimal APK surface |
| Biggest risk | debug signing + hardcoded local API token | tracking/SDK load + local gRPC/control surface exposure | self-signed + broad legacy permissions | debug signing in beta artifact |

## Quattro 0.18.1

### Identity

- Package: `ru.quattrocloud.vpnapp`
- App name: `Quattro VPN`
- Version: `0.18.1`, version code `19`
- min SDK: `24`
- target SDK: `36`
- main activity: `ru.quattrocloud.vpnapp.MainActivity`
- debuggable: `false`

### Signing

`apksigner` result:

- verifies: yes;
- v1: false;
- v2: true;
- v3/v3.1/v4: false;
- signer DN: `C=US, O=Android, CN=Android Debug`;
- SourceStamp: false.

Вывод: пользовательская сводка про Android debug-key подтверждена. Это сильный release-trust риск: прямой APK можно поставить, но Play/App Integrity и нормальная долгосрочная supply-chain история выглядят слабо.

### Permissions And Components

Permissions: 19.

Notable:

- `android.permission.INTERNET`
- `android.permission.FOREGROUND_SERVICE`
- `android.permission.FOREGROUND_SERVICE_SPECIAL_USE`
- `android.permission.ACCESS_NETWORK_STATE`
- `android.permission.ACCESS_WIFI_STATE`
- `android.permission.CHANGE_NETWORK_STATE`
- `android.permission.POST_NOTIFICATIONS`
- `android.permission.RECEIVE_BOOT_COMPLETED`
- `android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`
- `android.permission.USE_BIOMETRIC`
- `android.permission.USE_FINGERPRINT`
- `com.google.android.gms.permission.AD_ID`
- `com.google.android.finsky.permission.BIND_GET_INSTALL_REFERRER_SERVICE`
- `com.google.android.providers.gsf.permission.READ_GSERVICES`

Services:

- `ru.quattrocloud.vpnapp.bg.VPNService`
- `ru.quattrocloud.vpnapp.bg.QSTileService`
- Firebase/Google measurement/job/session services
- AndroidX WorkManager services

Providers:

- `com.google.firebase.provider.FirebaseInitProvider`
- share/file providers

### Native And Runtime

Native libs:

- `libapp.so`
- `libflutter.so`
- `libnpvpnBox.so`
- `libdartjni.so`
- `libdatastore_shared_counter.so`

`libnpvpnBox.so` contains sing-box/SagerNet traces:

- `sing-box.sagernet.org`
- `SagerNet/sing-tun`
- connectivity checks: Google `generate_204`, Cloudflare captive portal `generate_204`
- local host marker: `http://127.0.0.1:`

This looks like a SagerNet/sing-box-derived mobile core wrapped by Flutter.

### Static Config

Key asset:

`apk\assets\flutter_assets\assets\json\settings_config.json`

Confirmed values:

- `logLevel`: `debug`
- `remoteDns`: `1.1.1.1`
- `directDns`: `77.88.8.8`
- `tunImplementation`: `mixed`
- `urlTestInterval`: `3`
- `clashApiPort`: `16756`
- `clashApiToken`: present, hardcoded, redacted in this report
- `paddingRange`: `[5500, 12000]`
- `geoSiteUrl`: empty
- `geoIpUrl`: empty
- `isMobile`: `true`

Risk: static hardcoded auth token for a localhost Clash-style API is bad hygiene even if bound to loopback. If any WebView, local app, malicious profile, or exposed local listener can hit it, the token is extractable from the APK.

### Product Capabilities From Assets

Quattro app has a real "power user" surface in strings/assets:

- connect/disconnect status;
- subscription status, expiry, renewal, refresh;
- traffic card and exhausted-traffic paywall;
- server list, selected server, favorite servers;
- add own server;
- QR code scanner;
- DNS settings: DoH, DoT, DoQ, DoH3, UDP;
- own DNS;
- split tunneling by apps and URLs;
- include/bypass modes for selected apps/sites;
- blacklist and URL blocking;
- autoconnect;
- support contact;
- feedback with email reply;
- Telegram login/link;
- email login and email OTP;
- referral/invited friends;
- "1 month free" invitation reward text.

Important: this is broader than the Telegram bot. Their app gives the user agency and advanced controls while the bot/cabinet handles acquisition and payment.

### URLs And External Surfaces

Confirmed product/backend URLs in `libapp_strings.txt`:

- `https://auth.quattro-cloud.ru`
- `https://quattro.app`
- `https://npvpn.com`
- `https://blog.quattro-info.ru/Privacy-policy`
- `https://t.me/Quattro_support_bot`
- DNS endpoints: Cloudflare DoH, Google DoH, Quad9 DoH

Confirmed measurement/SDK signals:

- Firebase Analytics
- Firebase Crashlytics strings
- Google app measurement
- Play services measurement
- AD_ID permission
- install referrer permission

### Quattro Assessment

Strengths:

- best directly reusable feature map for POKROV Android: DNS, split tunneling, QR/import, own server, traffic/subscription, quick tile;
- one ecosystem across bot, web cabinet, app, support, instructions;
- strong "control" feeling inside APK.

Weaknesses:

- Android Debug signing in distributed APK;
- hardcoded local control token;
- release config still has `logLevel=debug`;
- Google/Firebase measurement stack undercuts privacy positioning;
- a raw VLESS-looking sample string appears in translation assets, which is poor secret hygiene if live.

What to copy:

- visible but safe route controls;
- quick tile;
- clear traffic/subscription state;
- QR/import only as advanced/recovery;
- split tunneling copy that explains "through VPN" vs "bypass VPN".

What not to copy:

- debug signing;
- static localhost API token;
- raw config strings in app assets;
- default debug log level in release APK.

## HiroVPN 1.17.1

### Identity

- Package: `com.hiro.vpn`
- App name: `HiroVPN`
- Version: `1.17.1`, version code `78`
- min SDK: `24`
- target SDK: `36`
- main activity: `com.hiro.vpn.SplashActivity`
- app class: `com.pairip.application.Application`
- debuggable: `false`

### Signing And Distribution

Base APK:

- verifies: yes;
- v1: false;
- v2: true;
- v3: true;
- SourceStamp: true;
- signer DN: `CN=Android, OU=Android, O=Google Inc., L=Mountain View, ST=California, C=US`.

arm64 split:

- verifies: yes;
- v1: true;
- v2: true;
- v3: true;
- SourceStamp: true;
- same Google signer family.

Вывод: Hiro looks like real Google Play App Signing / bundle split distribution. Это сильнее Quattro и текущего POKROV beta по supply chain.

### Permissions And Components

Permissions: 24.

Notable:

- `android.permission.BIND_VPN_SERVICE`
- `android.permission.CAMERA`
- `android.permission.QUERY_ALL_PACKAGES`
- `android.permission.READ_EXTERNAL_STORAGE`
- `android.permission.POST_NOTIFICATIONS`
- `android.permission.ACCESS_ADSERVICES_AD_ID`
- `android.permission.ACCESS_ADSERVICES_ATTRIBUTION`
- `android.permission.ACCESS_ADSERVICES_TOPICS`
- `com.android.vending.BILLING`
- `com.android.vending.CHECK_LICENSE`
- `com.google.android.gms.permission.AD_ID`
- `com.google.android.c2dm.permission.RECEIVE`
- Huawei common data permission
- Samsung maps/game-agent style permission

Activities:

- Google Ads activities;
- Yandex Ads activity and debug panel;
- Firebase Auth IDP/Recaptcha;
- Play Billing proxy activities;
- Pairip license activity;
- TV splash activity.

Services/providers:

- `com.hiro.vpn.VpnService`
- `dev.amirzr.flutter_v2ray_client.v2ray.services.V2rayVPNService`
- `io.appmetrica.analytics.internal.AppMetricaService`
- Firebase Messaging/Session services
- ML Kit component discovery
- Sentry providers
- AdMob integrity provider
- Yandex ads provider

### Native And Runtime

arm64 split native libs:

- `libapp.so`
- `libflutter.so`
- `libv2jni.so`
- `libhev-socks5-tunnel.so`
- `libbarhopper_v3.so`
- `libsentry.so`
- `libsentry-android.so`
- image/surface utility libs

Native strings show:

- `xray-core@v1.260327.1...`
- `reality`
- `wireguard`
- `utls`
- `grpc@v1.80.0`
- gRPC/control API endpoints like `/api/inbounds_*` and `/api/stats_*`

Interpretation: a Flutter shell around a V2Ray/Xray runtime, with local runtime control/stats machinery and split-tunnel/socks support.

### SDK Load

Confirmed from manifest/assets/dex/native markers:

- Google AdMob;
- Yandex Mobile Ads;
- AppMetrica;
- Firebase Analytics/Auth/Crashlytics/Messaging/Sessions;
- AppsFlyer;
- Sentry native + Android replay/performance providers;
- Play Billing;
- Google Play Pairip license check;
- ML Kit barcode scanning / `libbarhopper_v3.so`;
- Huawei AppGallery link;
- Samsung permission marker;
- TV mode activity.

This is the heaviest tracking/monetization stack in the set.

### Backend, Bot, Legal, Growth URLs

Product/backend URLs found:

- `https://api.hirovpn.com`
- `https://api.hellohiro.ru`
- `https://downloadhiro.app`
- `https://dev.downloadhiro.app`
- `https://files.downloadhiro.app/public`
- `https://hirovpn.com`
- `https://hiroearn.com/`
- `https://hirovpn.onelink.me`
- `https://chatwoot.wollebuy.com`
- `https://storage.googleapis.com/hirovpn`
- `https://storage.googleapis.com/hirovpn/offer.pdf`
- `https://storage.googleapis.com/hirovpn/terms_of_service.pdf`
- `https://storage.googleapis.com/hirovpn/user_agreement.pdf`
- `https://storage.googleapis.com/hirovpn/start.html`
- `https://storage.googleapis.com/hirovpn/start.html?path=/purchase`

Telegram surfaces:

- `https://t.me/HiroVpnBot`
- `https://t.me/HiroVpnSupportBot`
- `https://t.me/hirovpnblog`
- Telegram share URL

Embedded growth/news/earn domains:

- `moscownews24.ru`
- `newlenta24.online`
- `pitertv24.ru`
- `rocketnews.site`
- `sportvideo24.ru`
- `tvnews7.ru`
- `infomagazine.space`

Sentry DSN-like URLs are present in native strings; userinfo is redacted here.

### Hiro Assessment

Strengths:

- strongest production distribution posture;
- rich monetization and tracking stack;
- Play Billing and license-check infrastructure;
- multi-store funnel hints: Play, Huawei, App Store link;
- barcode/QR import capability;
- clear Telegram bot/support/blog ecosystem;
- legal docs hosted and linked.

Weaknesses:

- extremely heavy privacy footprint;
- `QUERY_ALL_PACKAGES`, `CAMERA`, AD_ID, ads, AppMetrica, AppsFlyer, Firebase, Sentry are a bad fit for a privacy-first VPN claim;
- local Xray gRPC/control API endpoints increase attack surface if not tightly isolated;
- partner/news domains look like built-in earn/traffic routing, not pure VPN product.

What to copy:

- polished distribution pipeline;
- QR import scanner;
- legal/download/start pages;
- support routing;
- app-store install confidence.

What not to copy:

- ad SDKs;
- broad package visibility;
- AppsFlyer/AppMetrica stack;
- hiding a growth/earn network inside a privacy product.

## ByeByeDPI 1.7.6

### Identity

- Package: `io.github.romanvht.byedpi`
- App name: `ByeByeDPI`
- Version: `1.7.6`, version code `1760`
- min SDK: `21`
- target SDK: `34`
- main activity: `io.github.romanvht.byedpi.activities.MainActivity`
- debuggable: `false`

### Signing

`apksigner` result:

- verifies: yes;
- v1: true;
- v2: true;
- v3/v4: false;
- signer DN identifies the public project developer; personal DN fields are
  omitted from this commit-safe report;
- self-signed, valid 2024-09-30 to 2049-09-24.

### Permissions And Components

Permissions: 14.

Notable:

- `android.permission.INTERNET`
- `android.permission.FOREGROUND_SERVICE`
- `android.permission.FOREGROUND_SERVICE_DATA_SYNC`
- `android.permission.FOREGROUND_SERVICE_SPECIAL_USE`
- `android.permission.FOREGROUND_SERVICE_SYSTEM_EXEMPTED`
- `android.permission.POST_NOTIFICATIONS`
- `android.permission.RECEIVE_BOOT_COMPLETED`
- `android.permission.QUICKBOOT_POWERON`
- `android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`
- `android.permission.QUERY_ALL_PACKAGES`
- `android.permission.MANAGE_EXTERNAL_STORAGE`
- `READ_EXTERNAL_STORAGE`
- `WRITE_EXTERNAL_STORAGE`

Services:

- `ByeDpiVpnService`
- `ByeDpiProxyService`
- `QuickTileService`

Receivers:

- `BootReceiver`

Native libs:

- `libbyedpi.so`
- `libhev-socks5-tunnel.so`
- all four ABI groups: `arm64-v8a`, `armeabi-v7a`, `x86`, `x86_64`

### Presets And Site Lists

`assets/proxytest_strategies.list` contains 60 non-comment strategy lines.

Site lists:

- `proxytest_cloudflare.sites`: 4 domains;
- `proxytest_discord.sites`: 21 domains;
- `proxytest_general.sites`: 6 domains;
- `proxytest_googlevideo.sites`: 19 host patterns;
- `proxytest_social.sites`: 16 domains;
- `proxytest_telegram.sites`: 52 domains;
- `proxytest_türkiye.sites`: 8 domains;
- `proxytest_youtube.sites`: 13 domains.

DEX URLs:

- donation: `https://pay.cloudtips.ru/...`
- Telegram donation bot: `https://t.me/romanvht_donate_bot`
- plus Android/Gson schema/docs URLs.

Native URL-like hit:

- Android toolchain source URL only.

No Firebase, AppMetrica, AppsFlyer, Sentry, AdMob, Play Billing, Yandex Ads found in this pass.

### ByeByeDPI Assessment

Strengths:

- cleanest trust story on telemetry;
- explicit utility UX: VPN mode, proxy mode, quick tile, boot receiver;
- strong presets for Telegram/YouTube/Discord/social/Cloudflare;
- multi-ABI native coverage.

Weaknesses:

- not a full commercial VPN product;
- self-signed APK distribution;
- broad package/storage permissions;
- no account, billing, support, cabinet, referral, retention loop.

What to copy:

- quick tile;
- boot/autostart as explicit setting;
- named route/preset packs;
- small "utility-first" mental model for emergency bypass mode.

What not to copy:

- broad storage permissions unless absolutely needed;
- support/donation-only monetization if POKROV is a consumer subscription product.

## POKROV Beta Reference

Static reference APK:

`C:\Users\kiwun\Documents\ai\POKROV-app\artifacts\releases\pokrov-app\1.0.0-beta+20260608-hotfix\pokrov-android-arm64-v8a.apk`

### Identity

- Package: `space.pokrov.pokrov_android_shell`
- Version: `1.0.0-beta`, version code `2001`
- debuggable: `false`

### Signing

`apksigner` result:

- verifies: yes;
- v1: false;
- v2: true;
- v3/v4: false;
- signer DN: `C=US, O=Android, CN=Android Debug`;
- SourceStamp: false.

This is acceptable only as beta/operator artifact truth. It should not be used for claims like store-grade signing, Play Integrity, trusted Android distribution, or "production-ready APK".

### Permissions And SDK Surface

Visible permissions:

- `android.permission.FOREGROUND_SERVICE`
- `android.permission.FOREGROUND_SERVICE_SPECIAL_USE`
- `android.permission.INTERNET`
- `android.permission.ACCESS_NETWORK_STATE`
- `android.permission.CHANGE_NETWORK_STATE`
- `android.permission.POST_NOTIFICATIONS`
- dynamic receiver permission

Manifest service:

- `PokrovRuntimeVpnService` with `android.permission.BIND_VPN_SERVICE`

APK file list scan:

- native libs: `libflutter.so`, `libapp.so`, `libbox.so`
- no Firebase/AppMetrica/AppsFlyer/Sentry/AdMob/Billing/Yandex/Pairip/MLKit markers in file list scan.

Source/docs contract:

- default runtime core: `sing-box`;
- `xray` fallback only in advanced compatibility;
- app-first identity;
- 5-day trial;
- Telegram reward +10 days;
- no third-party ad SDKs; only backend-owned first-party promo slots.

### POKROV Position Against These APKs

POKROV wins:

- cleaner permissions than all three commercial-ish surfaces;
- no ad/attribution SDK pile;
- app-first account/trial model is strategically better than Telegram-only or raw-link-first;
- release honesty and GitHub release/checksum posture can beat Quattro if signing is fixed;
- support/cabinet/product-doc story is cleaner than ByeByeDPI and less invasive than Hiro.

POKROV loses today:

- production signing is not solved in the current beta APK;
- fewer visible Android power controls than Quattro;
- no visible Quick Settings tile in current APK;
- no visible QR/import scanner in current APK;
- weaker commercial-store trust than Hiro until signing/store lane is closed;
- less "aggressive product proof" inside the app than Quattro/Hiro: competitors show more concrete knobs, statuses, servers, instructions.

## Risk Ranking

### Privacy/Data Leakage Risk

1. `HiroVPN`: highest. Ads, Yandex/AppMetrica, Firebase, AppsFlyer, Sentry, Billing, Pairip, broad permissions.
2. `Quattro`: medium. Firebase/Measurement/Crashlytics, AD_ID, install referrer, hardcoded local API token.
3. `POKROV beta`: low SDK risk, but release signing risk remains.
4. `ByeByeDPI`: lowest telemetry risk in this set.

### Release/Supply-Chain Trust

1. `HiroVPN`: strongest, Google signing + SourceStamp.
2. `ByeByeDPI`: self-signed but identifiable maintainer certificate and v1/v2.
3. `Quattro`: debug certificate, v2 only.
4. `POKROV beta`: debug certificate, v2 only.

This ranking is about APK trust only, not product quality.

### Product Feature Depth

1. `Quattro`: richest direct app controls for consumer VPN.
2. `HiroVPN`: broad commercial stack plus QR/import and store/billing.
3. `POKROV beta`: clean app-first shell, but fewer visible advanced client controls.
4. `ByeByeDPI`: deep bypass utility, not a paid VPN app.

## What This Means For POKROV

### Must Fix

1. Production Android signing. Current beta APK is debug-signed. This blocks strong trust claims.
2. Keep the "no ad SDKs" line. Hiro shows how ugly the opposite looks in a VPN app.
3. Do not ship static local-control tokens. If POKROV exposes any localhost/runtime API, use per-install random token, least privilege, strict loopback, no asset-embedded secret.
4. Keep debug logs out of release artifacts.
5. Keep raw subscription links/QR behind manual recovery or advanced paths, not first-layer onboarding.

### Should Copy

1. Quattro-style visible state: subscription, traffic, selected server/location, refresh, support, instructions.
2. Quattro-style route controls, but safer: split tunneling by apps/sites, "through VPN" vs "bypass VPN", DNS mode.
3. ByeByeDPI quick tile and boot/autostart pattern as explicit opt-in.
4. Hiro-style QR scanner/import for recovery and migration, not as default public identity.
5. Hiro-style legal/download/start pages, but without tracker-heavy SDK bundle.
6. Incident-to-content loop: app update, route mode, protocol, outage, workaround should become channel posts and in-app notices.

### Should Avoid

1. Hiro's ad/tracking stack.
2. Hiro's `QUERY_ALL_PACKAGES` unless a specific Android route feature strictly requires it and is explained.
3. Quattro's debug certificate distribution.
4. Quattro's hardcoded local API token.
5. ByeByeDPI's broad storage permissions unless POKROV has a real file-access feature.

## Tactical Backlog Ideas

High priority:

- close Android release signing and document the signer/checksum story;
- add a "trust strip" in install docs: version, SHA256, GitHub Release, signer status once production signing exists;
- make split-tunneling UI more concrete: apps/sites, through/bypass, DNS note;
- add Quick Settings tile if runtime supports it safely;
- add "manual import / QR" in recovery, hidden from first-layer purchase/onboarding;
- add app-side "route preset" cards: all traffic, all except RU, selected apps/sites, emergency mode when ready.

Medium priority:

- add in-app release/update notes from backend JSON, tied to Telegram posts;
- add a support diagnostics screen that redacts runtime material by contract;
- add app/cabinet "if Telegram is unavailable" recovery copy;
- publish competitor-safe posts that explain why POKROV does not use ad SDKs.

Low priority:

- partner/referral app screen after core trust/signing is fixed;
- optional QR scanner if import/migration becomes a meaningful support load;
- named DPI preset packs only if product policy approves this route.

## Evidence Index

Quattro:

- `C:\Users\kiwun\AppData\Local\Temp\opencode\quattro\manifest_out.txt`
- `C:\Users\kiwun\AppData\Local\Temp\opencode\quattro\dex_strings2.txt`
- `C:\Users\kiwun\AppData\Local\Temp\opencode\quattro\libapp_strings.txt`
- `C:\Users\kiwun\AppData\Local\Temp\opencode\quattro\npvpnbox_strings.txt`
- `C:\Users\kiwun\AppData\Local\Temp\opencode\quattro\apk\assets\flutter_assets\assets\json\settings_config.json`
- `C:\Users\kiwun\AppData\Local\Temp\opencode\quattro\apk\assets\flutter_assets\assets\json\urls.json`
- `C:\Users\kiwun\AppData\Local\Temp\opencode\quattro\apk\assets\flutter_assets\assets\translations\ru-RU.json`
- `C:\Users\kiwun\AppData\Local\Temp\opencode\quattro\apk\assets\flutter_assets\assets\translations\en-US.json`

HiroVPN:

- `C:\Users\kiwun\AppData\Local\Temp\opencode\hirovpn\main.json`
- `C:\Users\kiwun\AppData\Local\Temp\opencode\hirovpn\arm64.json`
- `C:\Users\kiwun\AppData\Local\Temp\opencode\hirovpn\dex_strings.txt`
- `C:\Users\kiwun\AppData\Local\Temp\opencode\hirovpn\natives_strings.txt`
- `C:\Users\kiwun\AppData\Local\Temp\opencode\hirovpn\xapk\com.hiro.vpn.apk`
- `C:\Users\kiwun\AppData\Local\Temp\opencode\hirovpn\xapk\config.arm64_v8a.apk`

ByeByeDPI:

- `C:\Users\kiwun\AppData\Local\Temp\opencode\byebyedpi\bbd.json`
- `C:\Users\kiwun\AppData\Local\Temp\opencode\byebyedpi\dex_urls.txt`
- `C:\Users\kiwun\AppData\Local\Temp\opencode\byebyedpi\natives_strings.txt`
- `C:\Users\kiwun\AppData\Local\Temp\opencode\byebyedpi\apk\assets\proxytest_strategies.list`
- `C:\Users\kiwun\AppData\Local\Temp\opencode\byebyedpi\apk\assets\proxytest_*.sites`

POKROV reference:

- `C:\Users\kiwun\Documents\ai\POKROV-app\artifacts\releases\pokrov-app\1.0.0-beta+20260608-hotfix\pokrov-android-arm64-v8a.apk`
- `C:\Users\kiwun\Documents\ai\POKROV-app\apps\android_shell\android\app\src\main\AndroidManifest.xml`
- `C:\Users\kiwun\Documents\ai\POKROV-app\packages\app_shell\pubspec.yaml`
- `C:\Users\kiwun\Documents\ai\POKROV-app\packages\runtime_engine\pubspec.yaml`
- `C:\Users\kiwun\Documents\ai\VPN\docs\product\portal-vpn-product.md`
- `C:\Users\kiwun\Documents\ai\VPN\docs\architecture\app-first-and-bonus-flows.md`
