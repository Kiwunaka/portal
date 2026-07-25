# MORI VPN — bundled UI/copy map

**Source:** installed `2.0.5` Flutter translation resources
**Russian corpus:** 31 top-level categories, 1,020 leaf strings
**English corpus:** 1,019 leaf strings

This file is a structured map, not a verbatim copy of the translation catalog. Bundled strings may describe disabled, old or server-gated screens.

## Two product generations are bundled

The resources contain both a broad three-tier product and a newer simplified `v2` experience.

### Newer `v2` shell

- Welcome promise: “Ваша свобода онлайн начинается здесь”.
- Navigation: Home, Servers, Devices, Profile, Settings.
- Access-code activation, “У меня нет кода”, invalid/expired-key states.
- Server search, favorites, premium tags and “Лучшие для вас”.
- Device pairing by QR, including instant TV login.
- One Premium tariff with 100+ countries, 3 simultaneous devices, VLESS, obfuscation, Kill Switch, TCP Socket Termination, unlimited speed, all platforms and zero-logs copy.
- Current embedded prices: `399 RUB` monthly; `3830 RUB` yearly; old yearly price `4788 RUB`; saving copy contains the typo `Економия 958 RUB`.
- Payment-declined, subscription-active, error-report and update-available states are designed.
- A stale example still displays “Версия 2.0.0” although the installed build is `2.0.5`.

### Older/full feature architecture

- Three packages: Basic, Premium and Maximum.
- Periods: 1, 3 and 6 months; 1 and 3 years.
- Device allowances: 1, 3 and 5 devices.
- Basic: standard VPN and standard servers.
- Premium: Kill Switch, TCP termination, TOR and Multi-Hop.
- Maximum: dedicated IP, 10 Gbps servers and post-quantum protection.
- Token-denominated prices: 50/100/150 MORI per month.
- Bank card, cryptocurrency and `$MORI` payment copy; `$MORI` promises a 50% discount.
- Browser checkout returns an activation code to re-enter in the app; Play Billing is also bundled.
- Bank-card copy explicitly says card payment is temporarily unavailable.

## Activation and account model

- Personal access code format: `MORI-XXXX-XXXX-XXXX`.
- The app says a code can be obtained free in Telegram.
- Pressing “Начать” is treated as acceptance of the terms.
- The broader resources nevertheless use both “account” and “no account” language.

## Advanced network features represented in copy

- adaptive connection for difficult network conditions;
- automatic anti-block routing;
- autoconnect;
- Kill Switch / traffic blocking on disconnect;
- TCP Socket Termination;
- TOR routing;
- Multi-Hop with entry, optional intermediate and exit servers;
- “triple protection” messaging;
- dedicated personal IPs positioned for banking, corporate services and streaming;
- 10 Gbps / 8K streaming claims;
- post-quantum / quantum-resistant encryption claims.

Compatibility rules are explicitly modeled: TOR and Multi-Hop cannot run together; adaptive connection and Multi-Hop cannot run together. Separate alerts say TOR, Multi-Hop and Kill Switch are “temporarily unavailable”, so presence in resources is not evidence of availability.

## Referral and gamification system

The bundled product includes:

- personal referral link;
- total and active referral counters;
- point accrual when a referral purchases;
- point milestones;
- balance, deductions and transaction history;
- achievements, expected rewards and recent activity;
- exchange of points for subscription levels.

The current website FAQ says the referral system will be added later, showing that this resource tree is ahead of, or disconnected from, the live product.

## Catalog scale

Translation category counts include 247 country labels and 128 city labels. These are localization entries, not proof of 247 live countries or 128 live server cities. Current `v2` marketing claims 100+ countries; the Play creative only shows a few example European cities.
