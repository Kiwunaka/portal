# 2026-04-22--pokrov-global-rework Wave Index

> Orchestrator-owned execution tracker for the full POKROV global rework.
> This wave folder is the durable copy of the user-approved program so execution does not depend on chat memory.
> Retained as historical execution evidence; active client workflow truth now lives in `C:/Users/kiwun/Documents/ai/POKROV-app/docs/`.

## Wave Snapshot

| Field | Value |
| --- | --- |
| Wave id | `2026-04-22--pokrov-global-rework` |
| Wave objective | `Execute the full POKROV global rework from canon freeze through shared truth extraction, backend/access redesign, next-client alignment, marketing/webapp/admin cleanup, and cutover/deprecation alignment.` |
| Status | `closed` |
| Orchestrator | `Codex in-session execution` |
| Execution model | `dependency-first` |
| Canonical repo lanes in scope | `portal/master` / `POKROV-app/main` / `bridge main when required` |
| Primary scope roots | `AGENTS.md`, `docs/`, `shared/`, `copy/`, `portal_bot/`, `marketing/`, `webapp/`, `C:/Users/kiwun/Documents/ai/POKROV-app/`, `external/client-fork/app/docs/` |
| Start gate | `Wave 0 canon rewrite and approved cutover spec are in place.` |
| Closure gate | `All program waves are implemented or explicitly reduced to documented compatibility/deferred seams, with verification and residual risk recorded.` |
| Last updated | `2026-04-23` |

## Program Anchors

- User-approved program statement lives in the conversation under `POKROV Global Rework Plan`.
- Wave 0 design gate lives at `docs/superpowers/specs/2026-04-22-wave-0-client-canon-cutover-design.md`.
- This index is the durable execution spine for the remaining waves.

## Read Gate

- [x] Reviewed the mandatory root read order from `AGENTS.md`.
- [x] Reviewed the approved Wave 0 cutover design spec.
- [x] Captured current repo-lane truth, bridge-lane truth, and `app-next` bootstrap-source truth.
- [x] Captured hardcoded-facts inventory across `marketing`, `webapp`, `shared`, and `portal_bot`.
- [x] Captured `app-next` parity/drift status versus the legacy bridge client.

## Ordered WO Queue

| Order | WO id | Title | WO class | Primary write scope | Depends on | Active role | Status | Closure note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `1` | `WO-001` | `Wave 0 canon and routing freeze` | `mixed` | `AGENTS.md`, `docs/`, `app-next/docs/`, `external/client-fork/app/docs/` | `-` | `executor` | `complete` | `Canonical lane model rewritten around portal/master, POKROV-app/main, app-next bootstrap, and legacy bridge release truth.` |
| `2` | `WO-002` | `Wave 1 shared truth extraction` | `mixed` | `shared/`, `copy/`, `shared adapters`, `portal_bot/shared surface loaders`, consuming surface files | `WO-001` | `executor` | `complete` | `Shared tariff, access, and promo truth extracted and consumed across backend, marketing, and webapp.` |
| `3` | `WO-003` | `Wave 2 backend identity/access/key-first contracts` | `platform-only` | `portal_bot/`, backend tests | `WO-002` | `orchestrator` | `complete` | `Unified catalog/access-key/promo-slot contracts landed in portal_bot API and shared payload families.` |
| `4` | `WO-004` | `Wave 3 next-client Android+Windows alignment` | `mixed` | `POKROV-app/`, retained bootstrap references, root docs if contracts move | `WO-002`, `WO-003` | `orchestrator` | `complete` | `The new client shell, IA, hidden transport handling, and local Android/Windows verification were aligned to the new canon.` |
| `5` | `WO-005` | `Wave 4 marketing rebuild` | `platform-only` | `marketing/`, `shared/`, `copy/` | `WO-002`, `WO-003`, `WO-004` | `orchestrator` | `complete` | `Marketing now owns public pricing/acquisition and ships key-first checkout messaging on a green build.` |
| `6` | `WO-006` | `Wave 5 webapp continuation cleanup` | `platform-only` | `webapp/`, `shared/`, `portal_bot/` contracts when needed | `WO-002`, `WO-003`, `WO-005` | `orchestrator` | `complete` | `Webapp now behaves as continuation-only with hosted checkout continuation, redeem, and compatibility pricing alias cleanup.` |
| `7` | `WO-007` | `Wave 6 admin and backoffice` | `platform-only` | `webapp/src/app/(dashboard)/admin/`, `portal_bot/` | `WO-003`, `WO-006` | `orchestrator` | `complete` | `Admin surface now emphasizes access keys, promo-slot scheduling, tariff visibility, and recovery lookup.` |
| `8` | `WO-008` | `Wave 7 cutover and deprecation alignment` | `mixed` | `docs/`, `POKROV-app/` references, historical bootstrap evidence, `external/client-fork/app/docs/` | `WO-004`, `WO-005`, `WO-006`, `WO-007` | `orchestrator` | `complete` | `Canon/docs/work-order alignment now freezes the legacy fork as bridge compatibility only and retains bootstrap references as evidence instead of active workflow truth.` |

## Phase Plan

| Phase | Goal | Ordered WOs | Entry gate | Exit gate | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `Phase 1` | `Freeze governance and shared truth` | `WO-001, WO-002` | `Approved Wave 0 spec present` | `Shared tariff/access/promo canon is live and consumed by at least one backend and one frontend surface` | `complete` | `Governance freeze and shared truth extraction landed.` |
| `Phase 2` | `Unify access contracts and client shell` | `WO-003, WO-004` | `Shared truth extraction merged` | `Backend and the new client lane both speak the new access/account model` | `complete` | `Backend contracts and the new client shell now align on app-first/key-first canon.` |
| `Phase 3` | `Public and continuation surfaces` | `WO-005, WO-006, WO-007` | `Backend contracts stable enough for UI adoption` | `marketing`, `webapp`, and admin all align to the new commerce and surface split` | `complete` | `Marketing, webapp, and admin are all verified on the new surface split.` |
| `Phase 4` | `Cutover alignment and final consistency` | `WO-008` | `Earlier waves landed` | `Docs, bridge lane, and new lane are consistent with the new world` | `complete` | `Cutover/docs alignment is complete with residual bootstrap risk recorded explicitly.` |

## Execution Notes

### Locked decisions carried into execution

- `POKROV-app/main` is the new client development truth.
- `app-next/` was the bootstrap-source workspace at wave start and is now retained only as historical evidence.
- `external/client-fork/app/` was the retained bridge lane at wave start and is now retired archive evidence only.
- Public scope for this program is `Android + Windows`.
- Commercial flow is `buy key -> redeem key -> managed premium`.
- `marketing` owns public acquisition, pricing, and paywall.
- `webapp` becomes session-aware continuation, redeem, support, renewal continuation, and admin only.
- One logical location is public; hidden transport matrix stays behind auto/diagnostics/admin.

### Important known drift captured before execution

- Pricing/tariff/access facts are duplicated across `portal_bot`, `marketing`, and `webapp`.
- The successor client lane was not yet release-ready and still lagged the bridge client when this wave started; current active client guidance now lives in `POKROV-app`.
- Current bridge release docs/commands still point to `external/client-fork/app`, which is correct for bridge-period release truth and must remain explicit until formal cutover.

## Closure Summary

Completed across the platform repo, the retained bridge docs lane, and the newly bootstrapped local `C:/Users/kiwun/Documents/ai/POKROV-app` repo. Remaining risk has narrowed to formal release-lane promotion only: bridge packaging/signing still owns public release truth until signed/public cutover evidence is complete.
