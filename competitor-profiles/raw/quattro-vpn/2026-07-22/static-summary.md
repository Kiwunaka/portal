# Quattro VPN — static Android summary

**Observed package:** `ru.quattrocloud.vpnapp`<br>
**Observed build:** `0.18.1` (`19`)<br>
**SDK range:** minimum 24, target 36<br>
**Scope:** local APK inspection only; no exploitation or active third-party probing

## Product architecture

The binary is a Flutter application built from an internal project named `npvpn_project`. Paths embedded in the application include a Windows build path under `D:/develop_work/Quattro-VPN/`, and every ABI ships a large `libnpvpnBox.so` core. The app also embeds the public domain `npvpn.com`.

The public npvpn site describes a white-label platform for launching and operating VPN brands, with infrastructure, applications, growth tooling and operational automation. Together, the internal namespace, native library name and embedded domain strongly support the inference that the Quattro service application is built on npvpn's white-label/infrastructure stack.

## Native product surface found in AOT/resources

- onboarding and activation by pasted subscription/config link;
- Home, Servers, Favorites, Profile and Settings;
- automatic server choice, latency tests and colored ping states;
- VLESS, VMess, Trojan, Shadowsocks, WireGuard and Hysteria2-related paths;
- custom DNS and IPv4/IPv6 strategy;
- split tunnelling by application and by URL;
- direct/VPN/blacklist routing and curated presets;
- own and third-party Xray-style server configurations;
- Quick Settings tile and Android `VpnService`;
- feedback, rating, language, theme and update flows;
- subscription/paywall, advertising abstraction, remote configuration, referral/share and paid-access configuration;
- Quattro Security: safe browser, breach lookup, URL scanner, password generator and event/history screens.

These are implementation/static signals. The observed runtime crash prevented verification that every route is live or server-enabled.

## Routing corpus

- `assets/json/urls.json` contains 233 curated service/domain presets, including ChatGPT, Gemini, OpenAI, YouTube, Telegram, Instagram, TikTok, Netflix, Discord, RuTracker, Flibusta and Mediazona.
- The APK bundles a large sing-box/SRS ruleset corpus: country GeoIP/GeoSite, Russian allow/direct lists, blocked resources, advertising, social networks and other categories.
- A settings asset specifies debug-level logging, Cloudflare remote DNS, Yandex direct DNS, mixed TUN mode, connectivity-test timing and a local control API. The bundled static local API token is intentionally redacted and is not retained in audit notes.

## Components, analytics and permissions

- Firebase Analytics, Firebase Crashlytics `19.4.4`, Firebase Sessions and WorkManager are present.
- Advertising ID and AdServices attribution/AD_ID permissions are declared.
- Other notable permissions include internet/network state, Wi-Fi state, change-network-state, notification, foreground/special-use service, wake lock, boot completed, vibration, biometrics/fingerprint and request-ignore-battery-optimizations.
- `allowBackup=false` is declared.
- Custom deep link: `quattro://auth`.
- App-owned VPN service and Quick Settings tile service are registered.

The Firebase/advertising footprint belongs to this installed service APK. It must not be conflated with the separate Google Play client `quattrovpn.app`, whose listing claims no ads, trackers or registration.

## Public domains embedded in the application

- `https://quattro.app`
- `https://npvpn.com`
- `https://blog.quattro-info.ru/Privacy-policy`
- Telegram support bot
- an authentication host under the `quattro-cloud.ru` service domain

Private API paths, tokens and connection material are intentionally omitted.
