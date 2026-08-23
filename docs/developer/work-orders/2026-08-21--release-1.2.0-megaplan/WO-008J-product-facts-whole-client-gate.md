# WO-008J — Product-facts whole-client gate

Status: `COMPLETE_LOCAL_I3`
Phase: `06`
Row advanced: `FE/P12-024`
Promotion: `NOT_REQUESTED`

## Outcome

Complete the local whole-client product-facts gate without making the app a
price or eligibility authority. Platform shared facts own global trial,
reward and platform-scope values; server responses and the generated
commercial contract remain the only price/offer authorities.

## Implemented boundary

- The active client already digest-pins product facts, tariff catalog,
  commercial contract and public URLs. Generated Dart supplies trial/reward,
  Android/Windows public scope and iOS/macOS readiness-only scope.
- The consumer validator now requires the active seed context to consume all
  four values: trial, Telegram reward, public release targets and readiness-only
  targets.
- Subscription plans must continue to parse `plans[].price` from the client API
  and Profile must render `plan.price`. No local tariff calculator or price
  fallback was added.
- Production app-shell Dart now fails the shared-facts check when it contains a
  currency-tagged numeric price literal such as `299 RUB`, `299 ₽` or
  `299 руб.`. Tests/fixtures remain outside this production scan.
- Existing cross-surface gates continue to bind backend, marketing, cabinet,
  bot and active-client trial/reward values to the shared owners.

## Index decision

`FE/P12-024` advances `I2 -> I3`. The local acceptance boundary now covers
trial, reward, price-source and device-scope parity in the active client plus
the existing platform consumers. Exact Android/Windows bytes, physical devices
and public/server readback remain required for `I4`.

Distribution becomes `I3=297`, `I2=23`, `I1=40`, `I0=17`; `80` rows remain
below `I3`. Stage split becomes `9/33/17/21`.

## Local proof

- Commercial, public-copy, frontend-text and shared-facts contracts: `33/33`
  PASS.
- Shared-facts focused suite including price and device negative tests:
  `11/11` PASS.
- Active-client generated projection/consumer `--check`: PASS.
- Active-client public/readiness scope test: PASS.
- Active-client server-price parsing/API test: PASS.
- Focused Ruff and Python compile: PASS.

Machine evidence:
`evidence/008J-product-facts-whole-client-gate/008J-product-facts-whole-client-gate.json`.

## Evidence ceiling

This is dirty-worktree local source/test evidence. No exact candidate,
physical device, provider/public-origin readback, payment, campaign, deploy,
publication or promotion occurred. Price-source validation proves ownership,
not that a current deployed provider returned a particular offer.
