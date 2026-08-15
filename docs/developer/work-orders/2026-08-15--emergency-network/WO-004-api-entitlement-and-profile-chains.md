# WO-004 — API, Entitlement And Profile Chains

## Metadata

| Field | Value |
| --- | --- |
| WO id | `WO-004-api-entitlement-and-profile-chains` |
| Title | Entitled RU clients receive safe catalog projection and exact reserve-first chains |
| Ceremony | `bounded_wo` |
| WO status | `done` |
| Orchestrator | `/root` |
| Repository lane | `platform` |
| Working branch or worktree | scoped platform branch after WO-001/002 |
| Intended promotion state | platform `master`; deploy in WO-007 |
| Created / updated | `2026-08-15` |

## Goal

Extend the authenticated locations/profile contract so active trial/paid RU
devices can select an active emergency reserve and one of three modes while
public/safe catalog responses never disclose connection material.

## Non-Goals

- Access for expired/unentitled users.
- Current-IP-only geofencing.
- WARP or arbitrary user-authored chains.
- Changes to POKROV Core source.

## Write Scope

- focused `portal_bot` locations, profile materialization and eligibility modules
- `shared/product-facts.json` only if a new product fact is required
- API/profile tests and canonical API/product docs

## No-Touch Scope

- raw emergency material in anonymous/public routes
- payment/trial grant duration and ledger authority
- core repository

## Authority Anchors

API-contract router row, product entitlement owner, existing RU bridge
materializer/tests, WO-002 active snapshot and exact Core 1.0.3 config schema.

## Acceptance Oracle

- Authoritative boundary: exact managed profile delivered to an authenticated device.
- Success observation: safe projection exposes stable metadata only; profile
  materializes exactly one selected reserve and one of:
  - `final=reserve`;
  - foreign outbound `detour=reserve`, final foreign;
  - foreign outbound `detour=owned-ru`, owned-RU `detour=reserve`, final foreign.
- Negative cases: free/expired, non-RU without cached/manual eligibility, stale or
  disabled reserve, wrong mode, missing hop, cycle, duplicate tag, >3 hops and
  WARP field are rejected without replacing current staged profile.
- Proof mechanism: API/auth tests, golden config shape, exact core validation in WO-006.
- Limitations: config shape alone does not prove egress or БС reachability.
- Triggered proof blocks: MREP, risk proof and mechanism adequacy.

## Docs Impact

`docs/architecture/api-contracts.md`, `docs/product/portal-vpn-product.md`,
client product/runtime owners when the consuming implementation lands.

## Validation And Evidence

Focused app-first/auth/locations/profile tests; config secret projection check;
entitlement/RU/manual-mode negative matrix; diff/secret scan.

## Status And Handoff

- Current WO status: `done`
- Dependencies: WO-001, WO-002
- Implemented: trial/paid entitlement, cached-RU plus explicit manual-mode
  eligibility, safe catalog projection and exact direct/two-hop/three-hop
  managed profiles. Profile validation locks auxiliary outbounds, DNS, RU
  ruleset origin, detour topology and no-WARP/no-foreign-direct invariants.
- Focused API/profile/eligibility/negative tests pass; actual tunnel egress stays
  owned by WO-006.
