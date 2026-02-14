# Payments Callback Runbook (Domain Split)

## Domain roles

- `portal-privacy.online`: marketing + `/webapp/`
- `kiwunaka.space`: `/api/*`, `/pay/*`, `/s8Kx2mP7qR4wT/*`

## URL matrix for validation

### Freekassa

- Notification URL: `https://kiwunaka.space/api/payments/freekassa/notify` (`POST`)
- Success URL: `https://kiwunaka.space/pay/success` (`GET`)
- Fail URL: `https://kiwunaka.space/pay/fail` (`GET`)

### Cardlink

- Store URL: `https://portal-privacy.online/`
- Success URL: `https://kiwunaka.space/pay/success`
- Fail URL: `https://kiwunaka.space/pay/fail`
- Result URL: `https://kiwunaka.space/api/payments/result/cardlink`
- Refund URL: `https://kiwunaka.space/api/payments/refund/cardlink`
- Chargeback URL: `https://kiwunaka.space/api/payments/chargeback/cardlink`

## Commission economics (RUB)

Net payout formula for gross price `P`:

`net = ((P * 0.935) - 2) * 0.965 = 0.902275 * P - 1.93`

Effective fee:

`fee = P - net = 0.097725 * P + 1.93`

Reference grid:

| Price (RUB) | Net (RUB) | Fee (RUB) |
|---:|---:|---:|
| 249 | 222.74 | 26.26 |
| 699 | 628.76 | 70.24 |
| 1199 | 1079.90 | 119.10 |
| 1399 | 1260.35 | 138.65 |
| 1499 | 1350.57 | 148.43 |

## Required env

- `PUBLIC_API_DOMAIN=kiwunaka.space`
- `PUBLIC_WEB_DOMAIN=portal-privacy.online`
- `PUBLIC_API_BASE_URL=https://kiwunaka.space`
- `WEBAPP_URL=https://portal-privacy.online/webapp/`
- `PAY_SUCCESS_URL=https://kiwunaka.space/pay/success`
- `PAY_FAIL_URL=https://kiwunaka.space/pay/fail`
- `PAY_RESULT_BASE_PATH=/api/payments/result`
- `PAY_REFUND_BASE_PATH=/api/payments/refund`
- `PAY_CHARGEBACK_BASE_PATH=/api/payments/chargeback`
- `CARDLINK_SIGNING_SECRET`, `FREEKASSA_SIGNING_SECRET`, `AAIO_SIGNING_SECRET`

## Smoke checks

1. `GET https://kiwunaka.space/pay/success` -> `200`
2. `GET https://kiwunaka.space/pay/fail` -> `200`
3. Signed callback to `POST /api/payments/result/freekassa` -> `ok=true`
4. Replay same callback -> `duplicate=true`
5. `https://portal-privacy.online/checkout` loads mock checkout page
