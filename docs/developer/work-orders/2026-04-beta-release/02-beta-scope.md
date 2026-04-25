# Beta Scope

Status: proposed beta cut after R01-R10 synthesis. This is a target scope, not a release approval.

## In Beta

- Paid, invite-limited beta on production domains after P0 gates pass or are explicitly accepted.
- Up to 25 active beta users.
- App-first account, 5-day trial, activation/redeem, paid entitlement, Telegram +10 day bonus, support ticket, managed profile delivery, and device/download handoff.
- Marketing acquisition that leads to real checkout, install, cabinet, and support paths.
- Continuation-first cabinet: overview, tariffs/payment, devices, downloads, support/diagnostics, profile, settings, redeem, checkout.
- Real admin operator surface: users, payments, access/subscriptions, devices, tickets, promo/plan visibility, nodes/routes, incidents/metrics, audit notes, emergency switches.
- Android internal APK for approved beta users only.
- Windows gated beta artifact; unsigned is acceptable only with explicit SmartScreen/unknown-publisher warning.
- Best-effort support target within 24h through cabinet ticket first, Telegram fallback second.

## Out Of Beta

- Public stable launch.
- Public Android store or APK approval unless signing plus physical localhost/control-surface audit pass.
- Public Windows trusted release approval unless signing, handoff, and runtime verification pass.
- iOS/macOS public promise.
- Production SLA.
- Public `Blocked only` routing.
- User-facing raw config or protocol controls.
- More than 25 active paid beta users without explicit orchestrator approval.
- Any checkout/download path that cannot be disabled quickly.

## Explicitly Deferred

- Apple TestFlight/App Store.
- macOS notarization.
- Full BI dashboard.
- Advanced DNS/routing UI.
- Public email auth launch unless sender and delivery gates pass.
- Public Android/Windows cutover.
- Public RU/DNS/leak guarantee.
- Automated referral/growth system.
- Store listing claims and production onboarding campaigns.

## Unsafe Claims

- Stable production release.
- Works everywhere guaranteed.
- 24/7 guaranteed support.
- Android store live before approval.
- Windows trusted signed before signing evidence.
- Public Apple availability.
- Direct public `VPN` positioning.
- Finished SLA, guaranteed uptime, or guaranteed node availability.
- Public `Blocked only` route mode.
- `AES-256`, `WireGuard`, raw protocol, or similar first-layer marketing claims unless backed by the actual current runtime contract and approved as technical/legal copy.
- Live downloads when artifact status is blocked, coming soon, or internal-only.

## User-Facing Beta Wording

Russian-first copy must explain:

- paid beta status
- limited invite access
- Android internal APK status
- Windows unsigned build warning
- best-effort 24h support target
- known limitations
- refund/manual support path
- no store/public cutover promise
- no production SLA
- cabinet-gated downloads

## Tester Onboarding

Each beta user receives:

- what POKROV beta is
- available platforms
- payment and activation steps
- cabinet-gated download instructions
- support path
- safe bug-report guidance
- known limitations
- refund/manual reconciliation path
- invite and access status
- payment success/failure next steps
- Android internal APK warning when applicable
- Windows unsigned build warning when applicable
- maintenance/pause message path

## Known Limitations

- Android is internal APK only until signing, handoff, runtime verification, and physical localhost/control-surface audit pass.
- Windows may be unsigned during beta; users must see the SmartScreen/unknown-publisher warning before download.
- Public store release is not approved.
- Support is best-effort within 24h, not guaranteed 24/7.
- Payment provider is not approved until category acceptance and webhook verification are complete or accepted as manual beta risk.
- Low-volume manual payment reconciliation is allowed only with admin audit note.
- Route modes in the public first layer are limited to `All except RU` and `Full tunnel`; advanced routing remains deferred.
- Selected apps MVP must be hidden or marked limited unless W07 proves it works.
- Email continuation remains unavailable/coming soon unless a separate gate proves it live.
- Admin metrics must show real data, backend-driven empty/unavailable states, or be excluded from beta gates.
- Live origin checks, backups, migration evidence, and rollback path must be captured before deploy.
