# Current Admin And Operator Journey

Last updated: 2026-04-23

## Basis

This diagram is built from the implemented admin route tree in `webapp/src/app/(dashboard)/admin/`, the admin navigation model in `webapp/src/app/(dashboard)/admin/nav.ts`, and the live admin endpoints exposed by `portal_bot/api.py`.

```mermaid
flowchart TD
  ENTRY["Primary operator surface<br/>https://app.pokrov.space/admin/"]
  START{"Current task"}

  DIAG["Diagnostics routes<br/>/admin/ and /admin/dashboard/"]
  PEOPLE["People routes<br/>/admin/users/"]
  ACCESS["Access routes<br/>/admin/bonuses/ and /admin/referrals/"]
  PAY["Payments routes<br/>/admin/promos/"]
  NET["Network routes<br/>/admin/nodes/ and /admin/network/"]
  MSG["Messaging routes<br/>/admin/broadcast/"]
  FB["Feedback routes<br/>/admin/tickets/"]

  SUMMARY["Summary and health APIs<br/>/api/admin/summary<br/>/api/admin/metrics/status<br/>/api/admin/metrics/timeseries<br/>/api/admin/nodes/traffic"]
  USERAPI["User operations APIs<br/>/api/admin/users*<br/>manual extend, block, message, risk, loyalty, key history"]
  ACCESSAPI["Access and growth APIs<br/>/api/admin/bonuses via page data<br/>/api/admin/referrals/*<br/>/api/admin/wheel-config<br/>/api/admin/start-links"]
  PAYAPI["Commercial APIs<br/>/api/admin/access-keys/issue<br/>/api/admin/promos*<br/>/api/admin/plans*<br/>/api/admin/promo-slots*<br/>/api/admin/gift-codes"]
  NETAPI["Network APIs<br/>/api/admin/nodes/health<br/>/api/admin/nodes/drift<br/>/api/admin/nodes/sync<br/>/api/admin/nodes/{code}/drain|enable|disable|resync<br/>/api/admin/network-rollout-config"]
  MSGAPI["Messaging APIs<br/>/api/admin/broadcast<br/>/api/admin/campaigns*<br/>/api/admin/templates*<br/>/api/admin/live-updates*"]
  FBAPI["Support APIs<br/>/api/admin/tickets<br/>/api/admin/tickets/{ticket_id}/reply<br/>/api/admin/tickets/{ticket_id}/status"]

  FALLBACK["Fallback operator lane<br/>Telegram admin actions remain emergency tooling"]

  ENTRY --> START
  START --> DIAG
  START --> PEOPLE
  START --> ACCESS
  START --> PAY
  START --> NET
  START --> MSG
  START --> FB

  DIAG --> SUMMARY
  PEOPLE --> USERAPI
  ACCESS --> ACCESSAPI
  PAY --> PAYAPI
  NET --> NETAPI
  MSG --> MSGAPI
  FB --> FBAPI

  SUMMARY --> PEOPLE
  SUMMARY --> NET
  USERAPI --> FB
  USERAPI --> PAY
  NETAPI --> SUMMARY
  FBAPI --> USERAPI

  FALLBACK -. only when web admin is insufficient .-> USERAPI
  FALLBACK -. emergency ops .-> FBAPI
```

## Read Notes

- The implemented admin surface already covers the full operator breadth needed by the canon.
- The current route tree is page-complete, but the operator story still reads as many separate surfaces rather than one deliberate task sequence.
- The API surface under `/api/admin/*` is already richer than the route tree alone suggests.
