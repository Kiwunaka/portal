# Quattro VPN — bundled UI and copy map

**Source:** Russian Flutter/AOT strings in installed `0.18.1` APK<br>
**Reachability:** unverified because the installed `x86_64` build crashes before Flutter UI

## Positioning and onboarding

- Product title: `Quattro VPN`.
- Hero promise: `100% безопасное соединение`.
- Security-suite onboarding: `Добро пожаловать в Quattro Security! Приватность, скорость и уверенность...`.
- Onboarding feature cards name a safe browser, breach search, password generator and URL scanner.

This is broader positioning than a one-button VPN: the intended product is a VPN plus consumer security toolbox.

## Connection and server UX

- automatic/optimal server selection;
- ping current server, ping lists and color-coded latency;
- favorites and sorting;
- subscription refresh;
- connection errors, retries and VPN-state copy;
- VLESS, VMess, Trojan, Shadowsocks and WireGuard protocol labels;
- custom DNS and automatic/manual IPv4/IPv6 modes;
- selected-apps-through-VPN, selected-apps-outside-VPN and blacklist concepts;
- URL/service routing presets and custom URLs.

## Monetization copy

Bundled paywall strings advertise:

- global coverage;
- streaming access;
- no browsing logs;
- five devices;
- 1/3/6/12-month plans;
- payment by card or SBP;
- `7 дней бесплатно`;
- `Подписка. Отмена в любой момент`;
- `Посмотреть рекламу и подключиться`.

This bundled paywall is not the same as the observed July 2026 web cabinet, which sells 30/90-day plans with LTE traffic packages. No trial, ad or payment was started during the audit.

## Referral copy

Static strings state that inviter and invitee receive one free month and that inviting ten users can unlock permanent access. The current web referral page instead renders an incomplete reward sentence with missing numbers, while the public March 2026 channel says both parties receive seven days after a qualifying purchase. Treat the APK wording as stale/configurable until observed live.

## Privacy and terms copy

Bundled privacy language says browsing history is not logged; the session IP may be used for approximate location and then deleted. It describes anonymous device/model/settings/network data, diagnostics, connection state, speed and latency collection. Bundled terms are generic and do not name the current legal operator.

## Design signals

- Inter typography;
- dark and light themes;
- black/red/white Quattro identity;
- dedicated onboarding, rating, settings, server/favorite, activation, status and security-tool assets;
- adaptive/large-screen layouts referenced by release notes;
- functional density closer to a power-user client than a minimal one-button VPN.

The visible runtime evidence is limited to the black splash with the centered white/red Q. Store/cabinet screenshots are the only reachable UI evidence in this environment.
