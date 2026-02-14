# Tariff Economics and Break-even (2026-02)

Updated: `2026-02-14`

## 1. Purpose

This document defines a simple model to evaluate:

- minimal viable price for each plan;
- break-even threshold for `Start 99`;
- margin impact of processor fees and promo discounts.

## 2. Input Variables

For period `T` (usually month):

- `P`: retail price (RUB).
- `f`: payment fee rate (fraction), example `0.10`.
- `c_fix`: fixed payment fee per transaction (RUB).
- `d`: average discount rate applied to paid orders (fraction).
- `S`: infra cost per active paid user for plan period (RUB).
- `A`: CAC/attribution cost per paid order (RUB), optional.
- `R`: expected refunds/chargeback reserve per order (RUB), optional.

Net revenue per order:

`net = P * (1 - f) - c_fix - (P * d)`

Contribution margin per order:

`cm = net - S - A - R`

Break-even condition:

`cm >= 0`

## 3. Start 99 Break-even

For `start_99`:

- `P = 99`
- Plan duration = 30 days
- Hard limits: 1 device, NL-only routing profile

Break-even threshold on infra for zero CAC model:

`S_max = P * (1 - f) - c_fix - (P * d) - R`

Interpretation:
- if real `S <= S_max`, plan is profitable or neutral;
- if real `S > S_max`, compensate by upsell conversion to higher plans.

## 4. Upsell-Corrected Break-even

If a share of `start_99` users upgrades, use:

- `u`: conversion from Start to higher paid plans (fraction).
- `cm_up`: average contribution margin from one upgraded user.

Then effective margin for one Start order:

`cm_effective = cm_start + (u * cm_up)`

Operational target:

`cm_effective > 0` while keeping Start as low-friction entry offer.

## 5. RUB Plan Grid (Current)

- `start_99`: `99`
- `1_month`: `249`
- `3_months`: `699`
- `6_months`: `1199`
- `9_months`: `1399`
- `12_months`: `1499`

Use one spreadsheet tab per plan:

1. Input fee assumptions (`f`, `c_fix`, `d`).
2. Input infra/user cost (`S`) by region profile.
3. Compute `net`, `cm`, and required conversion uplift for target margin.

## 6. Practical Operator Rule

1. Keep `Start 99` intentionally tight (already constrained by device and country profile).
2. Monitor weekly:
   - Start paid count,
   - upgrade conversion `u`,
   - 30-day refund rate,
   - blended margin.
3. If blended margin drops below target:
   - reduce discount depth,
   - tighten promo scope,
   - or adjust Start limits before changing headline price.

## 7. Data Sources

Suggested internal metrics to connect:

- orders and refunds from `external_orders` / provider reports;
- plan conversion from bot and WebApp events;
- infra cost from node invoices and active-user distribution.
