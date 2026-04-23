# Current User Journey

Last updated: 2026-04-23

## Basis

This diagram reflects the implemented route and contract surface currently visible in:

- `marketing/src/app/`
- `webapp/src/app/`
- `webapp/README.md`
- `portal_bot/api.py`
- `shared/public-urls.json`

```mermaid
flowchart TD
  MKT["Marketing entry routes<br/>/, /mobile/, /tiktok/, /youtube/, /devices/, /telegram/"]
  INTENT{"User intent"}

  INSTALL["Install help route<br/>/install/"]
  CHECKOUT["Public checkout route<br/>/checkout/"]
  CABINET["Cabinet entry route<br/>https://app.pokrov.space/"]
  TG["Telegram surfaces<br/>@pokrov_vpnbot, @pokrov_supportbot, @pokrov_vpn"]

  APP["Android or Windows app"]
  TRIAL["POST /api/client/session/start-trial"]
  PROFILE["GET /api/client/profile/managed"]
  ROUTE["GET/POST /api/client/route-policy"]
  CONNECT["Managed connect path<br/>app imports profile and connects"]

  CATALOG["GET /api/public/catalog<br/>GET /api/access-keys/status/{key}"]
  HOSTED["Hosted checkout<br/>https://pay.pokrov.space/checkout/"]
  REDEEM["POST /api/access-keys/redeem"]

  AUTH["Browser continuation and auth<br/>/, Telegram web-login, /api/auth/email/*"]
  DASH["Cabinet routes<br/>/dashboard/, /subscription/, /devices/, /dashboard/downloads/"]
  RENEW["Renewal continuation<br/>/subscription/checkout/"]
  SUPPORT["Support routes<br/>/support/, /support/thread/"]
  TICKET["Ticket APIs<br/>/api/tickets, /api/tickets/{ticket_id}, /api/tickets/{ticket_id}/messages"]
  LEGACY["Compatibility continuation<br/>/pricing/ alias and manual/recovery link handling"]

  LINK["POST /api/client/telegram/link"]
  BONUS["POST /api/channel/subscriber/check<br/>POST /api/bonuses/channel/claim"]
  RECOVERY["Recovery and manual delivery<br/>connect.pokrov.space canonical host"]

  MKT --> INTENT
  INTENT --> INSTALL
  INTENT --> CHECKOUT
  INTENT --> CABINET
  INTENT --> TG

  INSTALL --> APP
  APP --> TRIAL
  TRIAL --> PROFILE
  PROFILE --> ROUTE
  ROUTE --> CONNECT
  CONNECT --> RECOVERY

  CHECKOUT --> CATALOG
  CATALOG --> HOSTED
  HOSTED --> REDEEM
  REDEEM --> DASH

  CABINET --> AUTH
  AUTH --> DASH
  DASH --> RENEW
  DASH --> SUPPORT
  SUPPORT --> TICKET
  DASH --> LEGACY

  TG --> LINK
  LINK --> BONUS
  BONUS --> DASH
  TG --> SUPPORT
  TG --> RECOVERY
```

## Read Notes

- The implemented public journey is already split across `marketing`, app-first bootstrap, `webapp`, and Telegram.
- The current state still carries several active continuation seams rather than one single happy path.
- `connect.pokrov.space` is already the canonical connect host, but it still belongs to recovery/manual delivery rather than public acquisition.
