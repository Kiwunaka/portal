# WO-002 — Event And Error Envelope

Status: `COMPLETED`

## Contract

First-party Event Envelope V1 records safe source/campaign/entry lineage,
occurred/received/start/duration timestamps, platform/version/surface,
subsystem/stage/result, normalized errors, retries and correlation IDs.
Unknown metadata fails closed. Raw product and funnel rows retain for 90 days.

## Implementation

- Backend storage/migrations and ingestion accept idempotent event IDs and clock
  skew state.
- Android emits bounded connect, update and lifecycle stages with route, node,
  attempt, duration and Wi-Fi/LTE class.
- Admin funnel shows error categories, stages, versions, affected events and
  rolling-seven-day active users.
- No visited site, destination, raw config, secret, provider payload, private
  chat text or raw identity is admitted to the envelope.
