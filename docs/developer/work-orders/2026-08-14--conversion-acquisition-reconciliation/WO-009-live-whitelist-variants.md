# WO-009 — Live `Белые списки` Variants

Status: `IN_PROGRESS`

## Outcome

Пользователь видит `Обычный` и безопасные `Белые списки` варианты там, где они
реально доступны, и выбранный вариант меняет точный runtime path.

## Investigation Chain

Prove each boundary on the same account/cohort and exact build:

1. production `ru_bridge_relay` policy and `bridge_endpoints[]` are enabled for
   the intended cohort, with valid allowlist/exclusion and transport support;
2. deployed code/config hashes match local owners;
3. authenticated `GET /api/client/locations` returns stable safe `variants`
   without hosts, keys, ports or hidden tags;
4. client refresh/cache does not erase a non-empty live variants list and shows
   an explicit refresh/error/unsupported state;
5. selection persists per device, triggers fresh managed-profile fetch when
   required and materializes the exact selector/detour;
6. reconnect/location change uses the selected variant, not stale staged data;
7. failure remains fail-closed: direct/ordinary stays available, unsupported
   WARP+whitelist is blocked honestly, no silent fake success.

## Acceptance Scenarios

- at least one eligible non-US city exposes `Обычный` plus configured whitelist
  variants with short labels;
- excluded/invalid/unsupported/US cities remain direct-only;
- refresh updates measurements and variants without layout overflow;
- selected variant survives app restart and is cleared or explained if rollout
  later removes it;
- exact logs/config prove chosen outbound/detour without secrets;
- production current-origin API and exact public client UI both pass. A local
  fixture alone is not PASS.

## Checks

Backend projection/allowlist tests, client model/cache/widget/materialization
tests, production redacted readback, exact build install and bounded runtime
proof. The separate 20-cycle/Wi-Fi-LTE stress wave remains deferred.

## Current Evidence

- `PASS_PRODUCTION_REDACTED_READBACK` on `2026-08-14`: active rollout exposes
  safe endpoint ids `mini`, `ru`, and `ru_spb`; current eligible `de`, `ru`,
  `ru_spb`, `it`, `pl`, and `nl` nodes project `direct` plus those variants,
  while `us` remains direct-only. No host, port, key, tag, or raw config was
  printed or retained.
- `PASS_LOCAL`: backend allowlist/projection tests and client cache, sheet,
  persistence, selector/materialization, refresh and fail-closed WARP gates.
- `PASS_LOCAL`: every city with variants now advertises `Обычный / Белые
  списки` directly in the location row instead of hiding the capability behind
  an unexplained variant count; compact Huawei-width widget regression passes.
- `MANUAL_OWNER_TEST`: refresh the exact public app on the owner's phone,
  confirm visible `Обычный`/`Белые списки`, select one, reconnect and retain
  redacted runtime proof. The phone was not ADB-visible at the last check, so a
  fixture is not being promoted to production UI proof.
