# Target Admin And Operator Journey

Last updated: 2026-04-23

## Basis

This target view is grounded in the existing admin navigation categories, the root canonical docs, and the already-live admin endpoint families.

It shows the preferred operator journey, not a speculative new route map.

```mermaid
flowchart TD
  ENTRY["Primary operator entry<br/>/admin/dashboard/ in webapp"]
  SNAP["Operator truth snapshot<br/>/api/admin/summary<br/>/api/admin/metrics/status<br/>/api/admin/nodes/health"]
  DECIDE{"What needs action?"}

  PEOPLE["People and account triage<br/>/admin/users/"]
  ACCESS["Access and growth controls<br/>/admin/bonuses/ and /admin/referrals/"]
  PAY["Payments and key-first commerce<br/>/admin/promos/"]
  NET["Network and rollout control<br/>/admin/nodes/ and /admin/network/"]
  MSG["Messaging and retention comms<br/>/admin/broadcast/"]
  FEED["Feedback and support queue<br/>/admin/tickets/"]

  USERCASE["User-level actions<br/>status, limits, keys, loyalty, message, safe test cleanup"]
  KEYFLOW["Access-key and promo actions<br/>issue key, manage promo slots, maintain plan catalog"]
  ROLLOUT["Network actions<br/>inspect health, drift, rollout policy, drain/resync, capacity review"]
  THREAD["Ticket continuation<br/>reply, status, carry one support thread across surfaces"]
  COMMS["Campaign actions<br/>broadcast, templates, campaigns, live updates"]
  LOOP["Return to diagnostics snapshot and verify effect"]

  FALLBACK["Telegram admin fallback<br/>emergency-only, not primary ops surface"]

  ENTRY --> SNAP
  SNAP --> DECIDE

  DECIDE --> PEOPLE
  DECIDE --> ACCESS
  DECIDE --> PAY
  DECIDE --> NET
  DECIDE --> MSG
  DECIDE --> FEED

  PEOPLE --> USERCASE
  ACCESS --> KEYFLOW
  PAY --> KEYFLOW
  NET --> ROLLOUT
  FEED --> THREAD
  MSG --> COMMS

  USERCASE --> LOOP
  KEYFLOW --> LOOP
  ROLLOUT --> LOOP
  THREAD --> LOOP
  COMMS --> LOOP
  LOOP --> SNAP

  FALLBACK -. emergency continuation only .-> THREAD
  FALLBACK -. fallback only .-> USERCASE
```

## Read Notes

- The target operator path is diagnostics-led, then task-based.
- The existing route families already support this target view; the missing piece is consistent explanation and usage discipline.
- Telegram admin remains in the picture, but only as fallback.
