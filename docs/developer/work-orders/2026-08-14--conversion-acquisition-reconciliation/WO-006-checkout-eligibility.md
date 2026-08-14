# WO-006 — Checkout Eligibility

Status: `IN_PROGRESS`

## Outcome

Пользователь узнаёт, доступен ли `start_99`, до создания счёта; backend remains
the authority and compact checkout remains the approved UI.

## Acceptance

- public anonymous visitor may see and choose the welcome offer;
- authenticated account receives authoritative per-plan eligibility/reason;
- account with successful paid history cannot select `start_99`; UI explains
  `Приветственная цена уже использована` and defaults to normal 1 month;
- race or stale UI is still rejected before provider invoice creation;
- `start_99` never stacks promo/referral/pending discounts;
- all eligible six plans remain in the compact picker, one primary pay action,
  payment method and disclosures preserved;
- source/campaign snapshot from WO-004 reaches order creation.

## Checks

Eligibility API tests, payment state-machine tests, public/auth checkout E2E,
already-paid race, no-provider-call assertion on rejected order and responsive
visual regression.

## Current Evidence

- `PASS_LOCAL`: anonymous `start_99` stays available; provider-confirmed paid
  history, including normalized prior-paid email, makes it unavailable before
  invoice creation.
- `PASS_LOCAL`: the authenticated eligibility response provides a signed
  ordinary-month replacement and the checkout switches to it while preserving
  the acquisition ticket.
- `PASS_LOCAL`: all six plans remain available in checkout and `start_99`
  ignores referral, promo and pending discounts.
- `PENDING`: final checkout E2E/regression and post-deploy current-origin proof.
