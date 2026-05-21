# POKROV Growth And Competitor Notes

Last updated: 2026-05-19

## Purpose

This note captures the highest-leverage growth opportunities discovered during the `POKROV` rebrand, webapp cleanup, and current-state comparison against `https://perec.app/`.

Treat this file as a product support note for future landing-page, onboarding, and conversion work. Canonical product rules still live in [portal-vpn-product.md](C:/Users/kiwun/Documents/ai/VPN/docs/product/portal-vpn-product.md). The filename is legacy; the content follows the live `POKROV` canon.

## Current POKROV Strengths

- clear public brand with one canonical domain family: `pokrov.space`
- simpler app-first onboarding than Telegram-first competitors
- real `5-day` trial instead of decorative pre-auth screens
- Telegram still adds value through support, bonus claim, and feedback, but no longer blocks first launch
- public pricing and legal pages are now easier to reach before login

## Observed Competitor Snapshot

Observed on `2026-03-22` at `https://perec.app/`.

Public entry impression:

- user is pushed to `/login` quickly
- hero copy is short and clear, but the experience becomes auth-first almost immediately
- the first visible promise is speed and simplicity, not trust, proof, or transparent pricing
- privacy and terms are linked, but there is less pre-login explanation of what the product does and why it is safe to try

Observed on `2026-05-19` across Amnezia, Nord, Proton, Windscribe, Surfshark, Browsec, Dedmax, Batya, and Durev public pages:

- high-performing first screens put a concrete hook before mood copy: trial period, discount, platform, device count, guarantee, price, current country/status, or install action
- strong cards start with a number, status, or job-to-be-done, then explain what the user can do next
- weaker cards feel like abstract reassurance; `POKROV` should not lead with atmosphere when it can show `5 days`, `Android + Windows`, `+10 days`, `up to 5 devices`, `cabinet`, or `support`
- local Telegram-first competitors often make trial, price, and platform blocks visible immediately; `POKROV` should keep that directness while preserving beta/payment honesty and avoiding unsupported claims

## Where POKROV Can Win

### 1. Stronger pre-login trust

`POKROV` should keep leaning into the things an auth-first competitor hides too early:

- what the user gets in the first minute
- that the trial is real and immediately usable
- which platforms are supported
- where support lives
- what Telegram is used for and what it is not required for

### 2. Faster first success

The winning flow is:

1. open app or web entry
2. understand the value in a few seconds
3. start trial
4. connect

Every extra account wall before that reduces the advantage of the current app-first model.

### 3. More visible social proof

Homepage reviews and public feedback are a useful differentiator if they stay:

- short
- believable
- moderated
- privacy-safe through masked usernames such as `mikh****`

This is especially valuable because many VPN competitors look technically competent but emotionally generic.

### 4. More explicit support positioning

Support is already a real advantage for `POKROV`.

Growth opportunity:

- present support not as a rescue path only, but as part of the main promise
- keep the language human and calm
- make it obvious that a user can ask for help without understanding VPN jargon

### 5. Better checkout continuity

The best-performing public path should feel continuous:

- marketing page
- plan selection
- checkout
- cabinet
- support

Users should never feel like they have been dropped into a different product after clicking a CTA.

## Functional Gaps Already Closed In This Wave

- brand and domain drift reduced across backend, webapp, marketing, and scripts
- main public CTA paths aligned to `connect.pokrov.space`, `pay.pokrov.space`, and `api.pokrov.space`
- Telegram feedback flow upgraded so approved reviews can feed homepage proof safely
- new Telegram OAuth / OIDC login flow added while keeping a legacy fallback during transition
- public-facing copy rewritten to match actual product behavior instead of older `PORTAL` wording

## Next Growth Moves

### Near term

- complete production rollout of Telegram OAuth / OIDC and remove legacy widget dependency when stable
- add a short migration note for legacy users inside support, bot flows, and release notes
- keep polishing public reviews so the homepage shows fresh approved proof

### Medium term

- add a lightweight comparison block such as `why POKROV feels simpler on day one`
- add clearer device-specific landing variants for `Android` and `Windows`
- add a public support landing or support CTA strip if support volume remains a strong conversion lever

### Later

- test a more direct comparison page or FAQ against the most common user objections
- test a richer post-trial upgrade flow with stronger renewal framing and calmer urgency

## Recommendation

Do not copy the competitor's auth-first emphasis.

`POKROV` is better positioned when it stays:

- simple before login
- generous before commitment
- human in support
- transparent in checkout
- concrete about what works on day one

## 2026-05-19 Homepage Copy Pass

Implemented first-wave changes from the May 2026 competitor pass:

- rewrote the homepage hero around the concrete offer: `5 days`, no card, Android + Windows, cabinet, support, and Telegram bonus
- moved tariff visibility higher on the page and exposed `from 99 RUB` as the start extension hook
- added a value-card block for trial, platforms, devices, and Telegram bonus before the procedural onboarding steps
- rewrote the feature cards from internal surfaces (`app`, `cabinet`, `support`) into user outcomes: no manual profiles, one account for phone/computer, and support with context
- strengthened metadata around high-intent public wording such as `access`, `Android`, `Windows`, `5 days`, no card, devices, and Telegram support while preserving the no-direct-`VPN` public wording rule
- deliberately did not adopt competitor claims like `works in Russia`, unlimited devices, server/country counts, best/fastest language, or public-release certainty because those need current gate evidence

Second-wave consilium synthesis applied after OpenCode reviews with DeepSeek V4 Pro, Kimi K2.6, MiniMax M2.7, Mimo V2.5 Pro, and GLM 5.1:

- shifted the hero from a condition-first headline (`5 days without card`) to an outcome-first headline around YouTube/TikTok while keeping the trial, price, and device facts visible
- removed the repeated proof-strip pattern because the same facts already live in the hero hooks, value cards, and pricing
- rewrote value cards from feature labels into buyer reasons: free start without card, one-action app start, one account for phone/computer, and Telegram bonus/support
- added homepage FAQ UI and FAQ JSON-LD from the shared marketing FAQ list, then expanded the list with manual-profile and beta-availability objections
- kept `VPN` out of public POKROV copy and did not use unsupported availability, speed, rating, social-proof, audit, or guarantee claims

## 2026-05-21 Telegram Bot Onboarding Pass

Observed live Telegram competitor flows:

- PickVPN is strong at per-platform instructions, subscription status, and explicit plan/payment steps, but its first menu is crowded and raw subscription links are too visible.
- MORI is stronger at simplicity: the first menu is short, platform download choices are obvious, and `My key` is easy to understand. Its weakness is that raw keys/links are exposed too early and the copy relies on unsupported hype.

POKROV synthesis:

- keep the first layer short and action-led: cabinet, device connection, access status, help, support, and secondary actions
- add a `Я запутался` route that asks what the user has now: device to connect, activation code, personal connection link, or broken connection
- keep personal `connect.pokrov.space` links out of payment/gift success messages; show them only behind explicit `Ручная ссылка / QR`
- treat app install as the normal path, with manual compatible clients only as a beta/recovery fallback
- in the cabinet, add a visible `Я запутался` entry that routes to downloads, redeem, manual fallback, or support without requiring protocol knowledge
