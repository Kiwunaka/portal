# Apple Account And iOS Installation Sources

Checked: 2026-07-23

Status: `PUBLIC_PAGE_REVIEW_ONLY`

POKROV did not sign in with third-party credentials, make a test purchase or
verify post-payment delivery. “Page available” and “account works” are
different facts.

## Source Matrix

| Route | Type | Public state observed | Published terms | Product decision |
| --- | --- | --- | --- | --- |
| [Apple Support](https://support.apple.com/ru-ru/108647) | Own Apple Account | Official creation guide is available and allows choosing a country or region | Free; Apple may require email, phone verification and optional billing data | Primary route. User owns password, recovery and updates. |
| [VanyaVPN iOS](https://vanyavpn.app/ios) | Free temporary US App Store account from a VPN competitor | The official page currently exposes a “Получить данные временного аккаунта” action and allows downloading unrelated apps | Provider states exclusive access for about 15 minutes, password rotation, automatic phone unlinking and termination of a mistaken iCloud session | Surface as the first live competitor-supplied option. Link to the current page; never request, copy, cache or republish its credentials. POKROV did not test the login. |
| [FamilyPro shared Apple ID](https://familypro.io/shared-apple-id) | Free shared account | Public shared-account page is available and warns that the account may be temporarily unavailable | App Store only; no availability or replacement SLA | Surface as the first free best-effort source. Never copy credentials into POKROV. |
| [iZakStore](https://izakstore.ru/) | Free shared entries plus paid subscription | Homepage currently contains a periodically updated free-account section and a catalog with more than 2,000 listed apps | Trial plan shown as 399 ₽ for 7 days; other plans start at 599 ₽ for 7 days | Surface with caution. The provider’s own page also contains a complaint about paid access not appearing in the cabinet, so availability must be checked before payment. |
| [Happ Доступ](https://happplus.com/) | Paid installation guidance for Happ | Current page offers a link, guide and support for installation on the user’s own Apple Account | 490 ₽; provider claims delivery by email and refund if installation fails for its fault; service identifies ИП Эльмурзаев, ИНН 201103340623, ОГРНИП 317203600022433 | Surface for users who need exactly Happ. Label as an independent consultation service, not an official Happ representative. |
| [AppStops catalog](https://appstops.ru/catalog) | Paid account containing a selected app | Current catalog is populated, including Shadowrocket and other paid apps | Provider states immediate email delivery after payment, guaranteed access for 3 days and a separate charge for later updates | Surface as a paid catalog. Keep separate from the inactive free giveaway. |
| [WokerHome US Apple Account](https://wokerhome.com/shop/products/55) | Paid private regional account | Current product page offers an exclusive US account | 1 USDT; provider claims fast email delivery and 48-hour support; no Russian legal entity was visible in reviewed pages | Surface as a tertiary crypto-payment option with an explicit no-control-purchase warning. |
| [AppStops free giveaway](https://appstops.ru/accounts/) | Free shared giveaway monitor | Page explicitly says there is no active account and asks users to wait for a new giveaway | No current inventory | Do not present as available. Keep only a visibly inactive status monitor. |

FamilyPro also publishes a
[private US Apple ID product](https://familypro.io/en/products/apple-id), but
it is the same provider as the free source and is not shown as a separate
competitor card.

## Not Surfaced

- A current Dimikeys marketplace listing advertised a shared account at a low
  price, but the listing had zero reviews in the indexed result and its direct
  page returned HTTP 403 during review. Evidence is too weak for a POKROV link.
- Random pages that publish raw credentials without stable terms, ownership or
  support are excluded.
- Unofficial Shadowrocket download sites and IPA mirrors are excluded. They
  mix installation advice with unverifiable “official” claims and expand the
  device-security risk.

## Guardrails

- Never store, mirror, screenshot, test or search a third-party Apple Account
  login or password.
- Never call or parse a competitor credential-issuance endpoint and never proxy
  the returned login or password through POKROV infrastructure. Availability
  checks may inspect only public non-secret page state.
- Shared accounts are App Store-only. Never instruct the user to enter one in
  system Apple Account/iCloud settings.
- Never claim that a visible page proves a working login or successful
  post-payment delivery.
- POKROV does not handle vendor payment, refund, replacement or account
  recovery.
- Recheck availability and published terms before changing a user-facing
  status.
