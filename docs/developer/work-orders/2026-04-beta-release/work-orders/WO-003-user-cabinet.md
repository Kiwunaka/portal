# WO-003 User Cabinet

Status: draft
Lane: platform

## Scope

Make `webapp` a continuation-first paid beta cabinet for account status, tariffs/payment, devices/downloads, support, profile, settings, redeem, and checkout continuation.

## Assigned Paths

- `webapp/src/app/**`
- `webapp/src/components/**`
- `webapp/src/lib/api.ts`
- `webapp/e2e/cabinet-flow.spec.ts`
- `webapp/README.md`
- canonical docs if UX contract changes

## Required Changes

- Dashboard shows real account/access/device/support status or real unavailable/empty states.
- Tariffs/payment page aligns with current tariff catalog.
- Payment history is visible when backend exposes it.
- Devices page shows active sessions safely.
- Downloads page is cabinet-gated and beta-labeled.
- Support creates/continues real tickets with safe diagnostics.
- Telegram bonus card reflects real claim state.
- Redeem and checkout continuation provide clear next steps.
- Normal UI never exposes raw configs, personal subscription links, local-control surfaces, public IPs, or protocol jargon.

## Validation

- `cd webapp; npm.cmd run build`
- `cd webapp; npm.cmd run test:e2e`
- `python -m pytest tests/test_public_copy_guardrails.py -q`

## Handoff Format

- What I checked
- What I found
- What I changed
- How I verified
- What remains / risk

