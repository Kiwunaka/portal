# CyberGhost runtime notes — 2026-07-22

## Isolation

- Package: `de.mobileconcepts.cyberghost`
- Version: `8.40.0`
- Launcher: `de.mobileconcepts.cyberghost/.view.app.AppActivity`
- Cold launch: `TotalTime 792 ms`, `WaitTime 796 ms`
- First memory sample: approximately `105358 KB PSS`, `213304 KB RSS`, `0 KB swap`
- No `tun0` before first-run interaction.
- One VPN app at a time. Android Chrome was used only for outbound legal links and is stopped before the next in-app step.

## Screen 01 — isolated launch

- `Welcome to CyberGhost`
- `I hereby confirm I have read and accept the Terms of Service.`
- `We value your privacy`
- Data-collection explanation says nonessential collection can later be disabled in Profile settings.
- Single primary CTA: `Continue`.
- Terms/privacy are inline links; no visible acceptance checkbox.

## Screen 02 — Terms destination

- Full Android Chrome tab.
- Destination: `https://www.cyberghostvpn.com/terms?utm_medium=client&utm_source=android_app`
- Visible sections include Terms and Conditions, Refer A Friend Terms and Conditions, Imprint, and General Business Terms for CyberGhost Products.
- Visible revision date: 2025-09-10.
- Visible US binding-arbitration notice.
- Promotional banner and Live Chat remain on the legal page.

## Screen 03 — Privacy destination

- Full Android Chrome tab.
- Destination: `https://www.cyberghostvpn.com/privacypolicy?utm_medium=client&utm_source=android_app`
- Hero: `Here at CyberGhost, we’ve always followed the Privacy by Design principle.` attributed to CTO Timo Beyel.
- Visible claims: browsing history, traffic destination/content/search preferences are not monitored, recorded, logged or stored; no connection logs tied to IP, timestamp or session duration; payment data is not connected to tunnel activity.
- Live Chat remains visible.

## Confidence

All statements above are direct observations from retained screenshots/UI dumps except memory/timing, which came from the Android runtime. Public-page claims are recorded as CyberGhost claims, not independently verified facts.

## Screen 04 — paywall

- Hard paywall immediately after onboarding consent.
- Three-day annual trial, then `3,590 RUB/year`.
- Alternative `699 RUB/month`.
- Claims: 38M+ customers, encryption, 100+ countries, seven devices, 24/7 support.
- Auto-renew/cancellation copy present.

## Screen 05 — existing-user login

- Email or username, password, disabled Login until completed.
- Account recovery.
- Settings gear available before authentication.
- `New user?` returns to the paywall; it does not expose an independent registration form.

## Screens 06–09 — General and privacy

- General defaults: domain substitution off, troubleshooting-network-data sharing off, haptic feedback on.
- Privacy categories: Essential locked on; Analytics and Marketing on when first opened.
- Analytics provider: Google Analytics for Firebase.
- Marketing providers: AppsFlyer and Firebase.
- Analytics and Marketing were switched off and `Confirm Selection` was used.

## Screens 10–17 — VPN controls

- Connection check, dedicated-IP token input, protocol selection, small MTU, random port, content blocker and app split tunneling.
- Protocols: Auto, OpenVPN and WireGuard.
- Defaults: small MTU off, random port on, content blocker off.
- Split tunneling is an installed-app checkbox list; selected apps bypass the VPN tunnel.

## Screens 18–21 — Wi-Fi controls

- Wi-Fi protection visually on by default; unknown networks default to Ask.
- Actions: Ask, Protect, automatic stop, Ignore.
- Location permission and active location services are required for Wi-Fi automation. Location was not granted.
- Android notification permission appeared during this route and was denied.

## Screens 24–25 — article catalog

- Six titles target streaming, saving money, public Wi-Fi, gaming, school networks and workplace freedom.
- First article returned an unavailable-content screen. No article body was inferred.

## Screens 26–27 — support form

- Chrome Custom Tab, CyberGhost Zendesk support domain.
- Email, device, OS, country, subject, description, reference, optional diagnostics and attachment fields.
- No message was submitted.
- The lower form contained a prefilled diagnostic instance identifier. Its unredacted screenshot and UI dump were quarantined outside the worktree; the value is intentionally not retained in these notes.

## Screens 30–31 — imprint

- Chrome Custom Tab on CyberGhost site.
- Operator displayed as CyberGhost S.R.L., Bucharest, Romania.
- Trade register `J40/1278/2011`; VAT `RO28003392`; EUID `ROONRC.J40/1278/2011`.
- Legal page includes promo banner, live chat, cookie consent, money-back CTA and Trustpilot claim.

## Screen 34 — checkout boundary

- Annual CTA opened Google Play billing.
- Google Play reported that its payment system is suspended in Russia.
- No trial or purchase was started; paid/authenticated product screens remain `BLOCKED_BY_PAYMENT_RAIL` for this environment.
