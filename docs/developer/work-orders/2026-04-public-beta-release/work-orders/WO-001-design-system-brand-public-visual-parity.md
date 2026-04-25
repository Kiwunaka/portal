# WO-001 Design System, Brand, Public Visual Parity

Status: draft
Agent: W01
Lane: platform
Priority: P0/P1

## Goal

Make public beta visual language consistent across marketing, cabinet, and admin without reintroducing forbidden `VPN` public wording or fake claims.

## Write Scope

- `shared/design-tokens.json`
- `shared/design-tokens.ts`
- `shared/copy.ts`
- `copy/catalog.ru.json`
- `marketing/src/**`
- `webapp/src/**`
- `docs/developer/work-orders/2026-04-public-beta-release/**`

## Acceptance

- Public beta labels are visible where expectation setting matters.
- Public copy stays POKROV-first and avoids direct `VPN` product wording.
- No fake counters, fake reviews, fake success states, or unsupported security claims.
- Marketing/cabinet/admin style is coherent and uses real states.

## Validation

```powershell
python -m pytest tests/test_public_copy_guardrails.py tests/test_ui_visual_smoke.py -q
python scripts/ui_visual_smoke.py
cd marketing; npm.cmd run build
cd ../webapp; npm.cmd run build
```

