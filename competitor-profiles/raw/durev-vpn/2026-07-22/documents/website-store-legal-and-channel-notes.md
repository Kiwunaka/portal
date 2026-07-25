# Durev VPN — Website, Stores, Legal and Channel Notes

**Observed:** 2026-07-22<br>
**Method:** official public surfaces first; store reviews are user reports, not verified product facts. Public links are recorded, while personalized tokens, raw VPN endpoints, QR payloads and personal registry identifiers are excluded.

## Official public destinations

- Product site: <https://durevpn.com/ru>
- English storefront: <https://durevpn.com/en>
- Privacy policy: <https://durevpn.com/ru/privacy-policy>
- Terms: <https://durevpn.com/ru/terms-and-conditions>
- Refund policy: <https://durevpn.com/ru/refunds-policy>
- Google Play: <https://play.google.com/store/apps/details?id=com.durevpn.durevvpn&hl=ru>
- Public Telegram news: <https://t.me/durevvpn>
- Public account/purchase bot: <https://t.me/DureVpnBot>
- Public support bot shown in store materials: <https://t.me/DureVpnSupportBot>
- Web support centre: <https://support.durev.support>
- Official Georgian business-registry search: <https://enreg.reestri.gov.ge/main.php?c=app&l=en&m=search_form>
- Official Kazakhstan open-data catalog: <https://data.egov.kz/>

The website also links a cabinet and purchase flow under the primary domain. The Telegram channel has published an alternate cabinet mirror for blocking resilience. Mirror details should live in an authenticated official-directory feature rather than be copied into product prose.

## Controlled email recovery check

With the owner’s authorization, the connected Gmail address was entered once in the native **Импортировать из почты** route. The app returned that no user with the address was registered and directed registration to the site or bot. No email was delivered, no code/magic link was generated and no account was created. The address and mailbox metadata were not retained.

The result clarifies the funnel: native email import recovers an existing paid/key-bearing account; it does not register a newcomer. The public trial is paid, so further signed-in access would require a transaction that was not authorized.

## Homepage claims and conversion

Current Russian claims:

- 50+ countries;
- up to 300 Mbps;
- up to 10 devices;
- major desktop/mobile/TV/browser platforms;
- crypto payment;
- video, calls, games and public Wi-Fi use cases;
- no logs/no hidden analytics;
- “best price among competitors”.

Pricing observed on the Russian surface: 17 ₽ trial, 459 ₽ monthly, 2,414 ₽/6 months, 3,864 ₽/year and 5,244 ₽/2 years. The one-year discount is rendered inconsistently as 37% or 38%. Older official Telegram material says the trial costs 15 ₽. English pricing was $0.19 trial, $5.22/month, $27.43/6 months, $43.91/year and $59.59/2 years.

The homepage’s “connected right now” number is not credible as a live metric. Six immediate server-rendered requests returned values between approximately 60.6K and 64.1K with thousand-user jumps. Treat it as randomized social proof. Testimonials are unsourced and include placeholder-style names.

FAQ headings cover the founder/brand story, how the VPN works, protocols, device count, purchase, Russian safety and speed/ping. The closed interactive accordions did not expose answer text in the server response, so headings—not unseen answers—are the accepted evidence.

## Google Play

Observed listing state:

- publisher label: `Cryptan Coder Llc`;
- 100K+ installs;
- rating around 3.8;
- roughly 5.6K reviews depending on localized slice;
- updated 5 July 2026;
- legal developer: Dmitrii Bratashev, Individual Entrepreneur, Georgia;
- Data Safety: declares no data collected and no data shared.

The description repeats ten devices, no logs/no hidden fees, crypto payment and broad platform support. Current official creatives advertise high-speed connection, 50+ servers/one-click country selection and 24/7 support with average response under ten minutes. Creatives containing raw endpoint/configuration or QR material were rejected from the audit evidence set.

Review clusters:

- positive: speed, simple connection and allow-list routes that work for some users;
- negative: repeated mobile disconnects, unstable allow-list bypass, selected server not retained, key refresh burden, high/unusable ping and task-specific server labels not delivering reliably;
- developer responses: refresh the key, use a named anti-blocking server and contact support.

Nearby store recommendations observed: Speedify, hidemy.name, Cure VPN, PureVPN, Windscribe and v2RayTun. These are algorithmic acquisition neighbors.

## Privacy policy

Effective date shown: 30 October 2024.

The policy says Durev does not record visited sites/apps, source IP, DNS queries, content or session start/end timestamps. It says it may process:

- user ID/email for authentication and subscription;
- aggregate transferred bytes for load management;
- optional device type/OS details in crash/support reports;
- payment confirmation through Apple Pay, Google Pay, cryptocurrency and other processors, without retaining full card details.

Account deletion is described as an email-to-support process. The documented first-party data conflicts with Play’s blanket “no data collected” declaration. The policy can support a narrow “no traffic-content/history logs” claim, not a blanket “no data”.

## Terms and traffic limits

Published terms include restrictions that materially change the “unlimited” value proposition:

- approximately 1 TB per 30 days overall;
- 70 GB per calendar month for allow-list-bypass traffic;
- 40 GB per month for the Gemini/Roblox category;
- extra traffic can be purchased;
- torrents are restricted to tagged servers and can otherwise be shaped, suspended or blocked;
- a key may be shared with close relatives, while broader sharing is prohibited.

The terms say paid funds are non-refundable, yet link to a separate refund policy offering a conditional guarantee. The product should resolve that conflict at checkout.

## Refund policy

The policy offers a 14-calendar-day guarantee only for the first purchase. It excludes:

- renewals, repeat purchases and upgrades;
- accounts exceeding 5 GB total traffic;
- cryptocurrency payments, which receive time credit only;
- issues attributed to the ISP, device or lack of user skills after support supplies instructions.

Requests are routed exclusively through Telegram support and require the account identifier, payment date/amount, receipt image/PDF and a reason. The stated decision window is seven business days. Traffic records are described as the sole proof for the usage threshold. This is substantially narrower than a normal unconditional 14-day promise.

## Legal-entity chain

Website legal documents name Kazakhstan LLP/TОО `CIT / СИТ`, BIN `220440014920`, as seller/controller/contact. Google Play names Dmitrii Bratashev, Individual Entrepreneur, in Georgia; its visible brand is `Cryptan Coder Llc`.

An exact Georgian-language name search in the official NAPR registry returned one matching individual-entrepreneur record with `Active` status on the snapshot date. The personal/identification number is intentionally excluded. A Latin-name search alone returned no result, so the localized query was necessary.

The Kazakhstan open-data dataset is current/published, but exact BIN lookup required an API key or authenticated cabinet during this pass. A third-party directory repeated the same 2022 incorporation details, but it is not authoritative proof of present status. Current Kazakhstan status remains `BLOCKED_BY_ACCESS`.

The unresolved issue is role mapping: no public page clearly says which party develops the app, contracts with each platform, processes payments, controls personal data and owes refunds.

## Telegram lifecycle and release evidence

The official channel dates back to October 2024. Early material offered roughly 30 servers in 25 countries and described Outline with VLESS fallback. Current marketing says 50+ countries and the present native bundle ships an Xray/Sing-derived engine.

Observed recurring playbook:

1. publish blocking/outage news;
2. frame Durev as the immediate workaround;
3. link bot/cabinet;
4. add promo codes, raffles, live draws and “last day” pressure;
5. extend deadlines when useful;
6. award referral revenue or VPN days for invited purchases.

The channel has advised users to bind email so account access survives a Telegram block. It also advertises web support, public status/help destinations and alternative clients.

Official post 236, dated 7 July 2026, announced Durev 2.0 with a redesign/optimization, Android and Windows releases, automatic updates and Google Play/Microsoft Store distribution. It said the iOS app was ready but still awaiting App Store review. Native iOS availability therefore remains unconfirmed despite the website platform claim.

Apple fallback recommendations have included Happ and Karing; historical/current posts also mention V2RayTun, V2Box and Streisand around store removals. This client-agnostic key strategy is resilient, but users need authenticity checks and an explicit explanation of third-party privacy/support boundaries.

Marketing statements that payment resembles ordinary ecommerce or that traffic masking avoids international-traffic billing were observed but not independently verified. They should be treated as high-risk claims, not product facts.

## Contradiction register

| Surface A | Surface B | Conflict |
| --- | --- | --- |
| Website current trial: 17 ₽ | Older official channel: 15 ₽ | Acquisition price drift |
| Site advertises iOS | 7 July release says App Store review pending | Platform availability |
| Play: no data collected | Policy: email/user ID, bytes, diagnostics | Data-safety declaration |
| Terms: funds non-refundable | Refund page: conditional 14-day guarantee | Refund entitlement |
| “Unlimited” marketing | 1 TB / 70 GB / 40 GB category limits | Service limits |
| Kazakhstan website seller/controller | Georgian Play developer + `Cryptan Coder Llc` brand | Responsibility chain |
| “Connected now” presentation | Randomized multi-thousand request-to-request jumps | Social-proof credibility |
