# WO-002 - Wave 1 Shared Truth Extraction

## WO Snapshot

| Field | Value |
| --- | --- |
| WO id | `WO-002` |
| Title | `Extract tariffs, access rules, and promo slots into shared source-of-truth files and start consuming them across platform surfaces.` |
| Status | `complete` |
| Draft confidence | `grounded` |
| Priority | `P0` |
| WO class | `mixed` |
| Primary repo lane | `portal/master` |
| Secondary repo lane | `legacy bridge main` |
| Primary write roots | `shared/`, `copy/`, `portal_bot/`, `marketing/`, `webapp/` |
| Secondary write roots | `external/client-fork/app/docs/` only if bridge docs need the new shared-truth note |
| Dependencies | `WO-001` |
| Orchestrator | `Codex in-session execution` |
| Created | `2026-04-22` |
| Last updated | `2026-04-22` |

## Goal

Create the first real shared-truth layer for tariffs, access policy, and approved promo slots so backend, marketing, and webapp stop inventing competing versions of the same product facts.

## Why This WO Exists

The hardcoded-facts inventory found real pricing and access drift across `portal_bot`, `marketing`, and `webapp`. Wave 2+ cannot safely redesign access and commerce while plan codes, caps, pricing, and promo semantics still live in multiple fallbacks.

## Non-Goals

- Full backend key-redemption contract redesign belongs to `WO-003`.
- Full marketing rebuild belongs to `WO-005`.
- Full webapp continuation cleanup belongs to `WO-006`.

## Current Code Anchors (Must Read)

| Path | Why it matters | Read status | Notes |
| --- | --- | --- | --- |
| `shared/product-facts.json` | current locked facts and existing shared-json pattern | `done` | `Need to keep only locked facts here.` |
| `shared/portal-config.ts` | cross-surface TS adapter entrypoint | `done` | `Will likely host new adapters.` |
| `portal_bot/shared_surface_facts.py` | backend shared-json loader pattern | `done` | `Natural extension point for new shared files.` |
| `copy/catalog.ru.json` | current public/cabinet copy source | `done` | `Needs expansion, not replacement.` |
| `portal_bot/api.py` | current fallback plan and access payload shaping | `done` | `Contains duplicated plan/access logic.` |
| `webapp/src/lib/pricing.ts` | pricing fallback drift in webapp | `done` | `Likely first TS consumer to replace.` |
| `webapp/src/lib/access-policy.ts` | access-rule drift in webapp | `done` | `Likely first access consumer to replace.` |
| `marketing/src/app/checkout/checkout-client.tsx` | public pricing drift in marketing | `done` | `Needs shared catalog consumption.` |

## Acceptance Criteria

- [x] `shared/tariff-catalog.json` exists and captures plan codes, durations, prices, labels, and related commercial metadata that are currently duplicated.
- [x] `shared/access-matrix.json` exists and captures access states, free caps, device limits, node-pool intent, downgrade rules, and recovery/redeem semantics needed across surfaces.
- [x] `shared/promo-slots.json` exists and defines approved slot IDs plus the first-party promo/reward catalog needed for later remote-config waves.
- [x] TypeScript and Python loaders exist for the new shared files.
- [x] At least one backend consumer and both public-facing frontend stacks stop using their current local pricing/access fallbacks where the new shared truth can replace them safely.
- [x] Canonical docs mention the new shared truth files and their purpose.

## Validation Plan

- Focused backend tests around shared-facts loading and any touched API payload shaping.
- `npm.cmd run build` in `marketing/`.
- `npm.cmd run build` in `webapp/`.
- Grep-based drift checks to confirm the first replaced fallbacks are gone or narrowed.

## Completion Notes

This WO landed as the base layer for every later wave. The shared tariff/access/promo truth is now consumed by backend payload shaping plus both public-facing frontend stacks, so later waves no longer depend on scattered hardcoded product facts.
