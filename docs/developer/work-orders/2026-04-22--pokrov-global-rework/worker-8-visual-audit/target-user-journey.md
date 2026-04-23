# Target User Journey

Last updated: 2026-04-23

## Basis

This diagram reflects the target-state journey frozen by the current canon in:

- `docs/product/portal-vpn-product.md`
- `docs/architecture/system-overview.md`
- `docs/architecture/app-first-and-bonus-flows.md`
- `docs/operations/monitoring-and-visibility.md`

The path keeps only implemented route families and contract seams that already exist today, but reorders them into the preferred target story.

```mermaid
flowchart TD
  DISCOVER["Public discovery and pricing<br/>https://pokrov.space/<br/>/, /devices/, /mobile/, /telegram/, /checkout/"]
  CHOOSE{"What does the user need?"}

  INSTALL["Install app<br/>/install/ and runtime app links"]
  CONTINUE["Continue known session<br/>https://app.pokrov.space/"]
  UPGRADE["Buy managed premium<br/>/checkout/ -> pay.pokrov.space/checkout/"]

  APP["Android or Windows app"]
  START["POST /api/client/session/start-trial"]
  MANAGED["GET /api/client/profile/managed"]
  MODE["Choose route mode before first live activation<br/>all traffic or selected apps"]
  LIVE["Connect and use managed access"]

  SESSION["Browser continuation only<br/>Telegram web-login, app handoff, or /api/auth/email/*"]
  CABINET["Cabinet continuation routes<br/>/dashboard/, /subscription/, /redeem/, /devices/, /dashboard/downloads/, /support/"]
  STATUS["GET /api/dashboard<br/>GET /api/client/apps"]

  CHECKOUT["Hosted checkout issues activation key"]
  STATUSKEY["GET /api/access-keys/status/{key}"]
  REDEEM["Redeem in app or webapp<br/>POST /api/access-keys/redeem or /redeem/"]
  REFRESH["Managed premium refresh on same app-first account"]

  TELEGRAM["Telegram as secondary path only"]
  LINK["POST /api/client/telegram/link"]
  CLAIM["POST /api/channel/subscriber/check<br/>POST /api/bonuses/channel/claim"]
  FALLBACK["Support and recovery fallback<br/>@pokrov_supportbot and connect.pokrov.space"]

  DISCOVER --> CHOOSE
  CHOOSE --> INSTALL
  CHOOSE --> CONTINUE
  CHOOSE --> UPGRADE

  INSTALL --> APP
  APP --> START
  START --> MANAGED
  MANAGED --> MODE
  MODE --> LIVE

  CONTINUE --> SESSION
  SESSION --> CABINET
  CABINET --> STATUS
  CABINET --> REDEEM
  CABINET --> FALLBACK

  UPGRADE --> CHECKOUT
  CHECKOUT --> STATUSKEY
  STATUSKEY --> REDEEM
  REDEEM --> REFRESH
  REFRESH --> LIVE
  REFRESH --> CABINET

  LIVE --> LINK
  LINK --> CLAIM
  CLAIM --> LIVE
  LIVE --> FALLBACK

  TELEGRAM -. recovery, bonus, support .-> LINK
  TELEGRAM -. fallback .-> FALLBACK
```

## Read Notes

- The target story collapses public onboarding to `marketing -> install -> app-first trial -> connect`.
- `webapp` remains important, but only as continuation, renew, redeem, download, and support surface.
- Telegram stays in the journey, but only as a secondary lane.
