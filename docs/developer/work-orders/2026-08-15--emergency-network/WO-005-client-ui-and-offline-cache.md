# WO-005 — Client UI And Offline Cache

## Metadata

| Field | Value |
| --- | --- |
| WO id | `WO-005-client-ui-and-offline-cache` |
| Title | Android/Windows expose a clear emergency surface and signed offline continuation |
| Ceremony | `bounded_wo` |
| WO status | `done` |
| Orchestrator | `/root` |
| Repository lane | `active_client` |
| Working branch or worktree | scoped client branch from `main@95dc49d` |
| Intended promotion state | client `main`; exact release only in WO-007 |
| Created / updated | `2026-08-15` |

## Goal

Add `Экстренная сеть POKROV` under Locations with compact reserve cards, status,
refresh, route-mode choice, first-use disclosure, manual limited-network mode,
signed bootstrap/LKG cache and honest offline/error states.

## Non-Goals

- A broad locations redesign.
- `публичный`/`внешний` badges on every card.
- Hiding the direct-exit disclosure entirely.
- WARP or emergency-specific per-app routing.
- Showing raw host, UUID, SNI or keys.

## Write Scope

- `C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/`
- bounded Android/Windows host bridge only if signed catalog verification needs it
- client fixtures/tests and canonical client docs

## No-Touch Scope

- POKROV Core source/artifact version
- unrelated Profile/Rewards/Support UI
- release metadata until an exact candidate exists

## Authority Anchors

Active-client router row; client product/UI direction; platform API contract;
existing locations/variant cache/materialization and host secure-storage patterns.

## Acceptance Oracle

- Authoritative boundary: visible UI selection plus persisted exact staged profile.
- Success observation: entitled cached-RU/manual-mode user can discover up to 20
  reserves, understand status/freshness, accept disclosure, choose a mode and
  reconnect with the same stable ID; restart/offline uses the last valid signed
  cache without leaking entitlement.
- Negative cases: invalid signature, expired entitlement, disabled/stale snapshot,
  API error and unknown mode show an honest state and never start a stale/unsafe profile.
- Proof mechanism: model/store tests, focused widget tests, Android/Windows host
  verification tests and screenshots at phone/desktop dimensions.
- Limitations: widget and cache proof do not prove network egress.
- Triggered proof blocks: MREP, risk proof, reviewability, manual device gate.

## Docs Impact

Client product contract, UI direction, bootstrap workflow and affected host docs;
platform API owner remains canonical for server fields.

## Validation And Evidence

`flutter analyze`, focused then full `flutter test`, client seed/docs contracts,
host-focused tests, diff/secret check and retained compact screenshots.

## Status And Handoff

- Current WO status: `done`
- Dependency: WO-004
- Implemented and pushed in `POKROV-app/main@ed8405d`: nested Locations surface,
  4–20 compact rows, refresh/status/proof levels, manual limited-network mode,
  three route choices, first-use disclosure, encrypted device-bound signed LKG
  and exact fail-closed profile validation on Android/Windows.
- Flutter analyze, 294 full tests, client docs/seed contracts and production
  Android/Windows builds pass. LDPlayer showed the exact predeploy surface; a
  raw HTTP `Not Found` state found there was redacted before the final rebuild.
