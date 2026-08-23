# WO-008I — Product-copy and public-truth consumers

Status: `COMPLETE_LOCAL_I3`
Phase: `06`
Rows advanced: `FE/P12-129`, `FRKN_ADOPT/ADOPT-07`
Promotion: `NOT_REQUESTED`

## Outcome

Close the remaining local product-fact drift without making the active client,
marketing copy or Telegram bot a second commercial authority. The platform
shared facts remain the only non-account product owner; commercial prices and
final offer state remain server-contract authority.

## Implemented boundary

- `shared/public-urls.json` is now SHA-256-pinned beside product, tariff and
  commercial contracts in the active-client seed. The generated Dart
  projection carries full offer, privacy and official-release URLs.
- Client fallback trial/Telegram text is assembled in one helper from generated
  facts. Production Dart is checked for the known hardcoded reward/trial forms.
  Account-specific reward and referral values continue to render server data.
- Profile consumes the generated offer, privacy and official-release URLs; a
  widget test proves the exact canonical handoffs.
- Web cabinet trial math uses `getSharedProductFacts()` instead of a local `5`.
- Economy, public API and Telegram bot trial, current/grandfathered channel
  reward, referral friend/referrer, hold and pre-payment-cap constants bind
  `shared/product-facts.json`. The unused worker referral default and bot copy
  literals were removed.
- Marketing Telegram copy no longer requires a first payment. Its live landing,
  homepage reward and trial facts use shared facts or copy-catalog variables.
  The static rendered route says `Без оплаты` and retains the canonical values.
- Prices, promo results, deadlines, payment methods, account referral state and
  entitlement outcomes remain server responses or the generated commercial
  contract. No client-side price or eligibility evaluator was added.

## Index decision

- `FE/P12-129`: `I2 -> I3`. The active client and live platform consumers no
  longer own duplicated runtime constants; copy-owner artifacts have derived
  contract tests, and consumer drift fails locally.
- `FRKN_ADOPT/ADOPT-07`: `I2 -> I3`. Price, referral, privacy and release truth
  now have explicit owners plus active local consumers across platform/client.

Current distribution: `I3=295`, `I2=24`, `I1=41`, `I0=17`; `82` rows remain
below `I3`. Stage split becomes `12/32/17/21`.

## Local proof

- Shared facts/copy guardrails: `23/23` PASS.
- Trial/referral/channel backend matrix: `86/86` PASS.
- Bot referral/admin-gift focus: `2/2` PASS; Telegram rich copy: `5/5` PASS.
- Marketing lint/build: PASS, 35 static routes.
- WebApp lint/build: PASS, 40 static routes.
- Active-client generated projection `--check`: PASS.
- Active-client Profile URL widget: PASS; app-shell analyze: PASS.
- Focused Ruff/compile and scoped diff checks: PASS, with Windows CRLF warnings
  only.
- Explicit-root seed validation proved client/Core parity, cross-repository
  product facts, version truth, observability, logging and release-v2 contracts,
  then stopped in the pre-existing repository-hygiene wrapper because Git CRLF
  warnings were treated as command output. This run is not recorded as PASS.

Machine evidence:
`evidence/008I-product-copy-truth/008I-product-copy-truth.json`.

## Evidence ceiling

Local source/test/build evidence comes from dirty development worktrees. No
clean freeze, exact candidate, device/browser-lab run, deployed origin readback,
legal approval, payment, campaign, server mutation, publication or promotion
occurred. Generated URLs prove source ownership, not current public availability.
