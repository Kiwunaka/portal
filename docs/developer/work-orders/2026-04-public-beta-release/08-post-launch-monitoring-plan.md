# Post-Launch Monitoring Plan

Status: draft

## First 60 Minutes

Every 10 minutes:

- API health
- checkout status
- webhook status
- payment success/failure/manual_review counts
- cabinet login/open
- download availability
- managed profile delivery
- node health
- support tickets
- admin access

## First 24 Hours

Every 1-2 hours:

- payment conversion
- entitlement creation
- failed access activation
- downloads
- client connect failures
- support volume
- node overload
- incidents

## First 7 Days

Daily:

- bugs
- refunds/manual reconciliation
- payment provider issues
- support median response
- active users
- expired/failed trials
- node capacity
- public copy feedback
- release gate regressions

## Origin Labels

- `current-origin check`: operator workstation.
- `brain-origin check`: control-plane host `82.21.114.104`.
- `RU-origin check`: `mini` or replacement external RU probe.

