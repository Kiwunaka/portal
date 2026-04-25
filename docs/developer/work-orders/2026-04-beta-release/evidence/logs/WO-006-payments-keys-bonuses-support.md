# WO-006 Payments, Keys, Bonuses, Support Evidence

Status: first-pass payment callback hardening complete
Agent: W06
Date: 2026-04-25

## What I Checked

- Beta wave context, synthesis, TD-023, R07 provider research, W05 backend evidence, W09 security baseline, and WO-006.
- Current branch `codex/beta-release-platform`; dirty baseline included concurrent work outside W06 scope and was left intact.
- Payment callback/order code in `portal_bot/api.py`.
- Bot paywall, ticket repo, review masking, worker retention, and free-cycle focused tests.

## What I Found

- TD-023 was real: the payment callback suite still expected stale `POKROV VPN ...` payment description text while the catalog had moved to the current `Старт на 30 дней` plan label.
- Signed `result` callbacks were persisted before fulfillment, but fulfillment did not first require the normalized callback status to be `paid`.
- The generic FreeKassa callback path treated any signed `result` as `paid` when no SCI fields were present, which could turn failed, cancelled, or unknown states into access extension.
- Bot paywall test expectations had drifted behind current bot copy; the bot implementation already avoided Stars in the checked paywall text and used cabinet wording.

## What Changed

- Payment order descriptions sent to non-FreeKassa RUB providers now use `POKROV {plan_label}` instead of the legacy direct `POKROV VPN {plan_label}` wording.
- Callback status normalization now distinguishes `paid`, `failed`, `cancelled`, `refunded`, `chargeback`, `pending`, `pending_verification`, and `manual_review`.
- Callback fulfillment now extends access only for non-duplicate, signed `result` events whose normalized status is `paid`.
- Signed failed/cancelled/unknown result events are recorded on `ExternalOrder` / `ExternalPaymentEvent` for reconciliation without granting access; unknown signed states use `manual_review` and `processed_ok=false`.
- Payment callback tests now cover failed, cancelled, and manual-review result events.
- Bot paywall tests were aligned with current beta-safe bot copy and cabinet wording.
- Canonical architecture docs now state the payment callback fulfillment rule.

## Provider Candidate Status From R07

- Lava.top: blocked by missing merchant/category acceptance and live signed webhook proof. Public docs confirm payment and recurring webhooks, API-key/Basic webhook auth, retries, and subscription cancellation events; refunds do not emit webhooks, so refund reconciliation would need polling or manual ops.
- Tribute: blocked by missing category acceptance and live webhook proof. Public docs confirm digital-product purchase/refund webhooks, `trbt-signature` HMAC-SHA256, retry timing, and refund matching by purchase ID; no local adapter or verifier exists yet.
- Kassa.ai: blocked by missing API/webhook/signature/refund docs and merchant acceptance evidence. Too opaque for paid beta until provider supplies written integration terms.

No live provider writes or secret-bearing checks were run.

## How I Verified

Passing:

```powershell
python -m pytest tests/test_api_payments_callbacks.py -q --basetemp .tmp/pytest-w06-payments-green
python -m pytest tests/test_bot_paywall.py tests/test_tickets_repo.py tests/test_reviews_username_masking.py -q --basetemp .tmp/pytest-w06-bot-support-green
python -m pytest tests/test_worker_retention.py tests/test_free_cycle_service.py -q --basetemp .tmp/pytest-w06-worker-free-green
```

Red-first signal before the API fix:

```powershell
python -m pytest tests/test_api_payments_callbacks.py -q --basetemp .tmp/pytest-w06-payments-red
```

Result: expected failures for unsafe `POKROV VPN ...` provider description and missing normalized callback statuses for failed/cancelled/manual-review result events.

## What Remains / Risk

- No Lava.top, Tribute, or Kassa.ai adapter was implemented because R07 did not confirm category acceptance or live signed webhook behavior.
- Hosted paid callbacks still directly extend access for `paid` results; the preferred key-first fulfillment path remains a product/ops decision for a later payment-provider implementation pass.
- Refund and chargeback callbacks are admin-visible records but do not automatically revoke or shorten access in this pass.
- No live payment, refund, provider dashboard, or production-domain callback test was run.
- Marketing/webapp/shared copy was not edited; any public copy or checkout UI wording needs remain with W02/W03 unless a later backend contract change requires it.

## Changed File Paths

- `C:/Users/kiwun/Documents/ai/VPN/portal_bot/api.py`
- `C:/Users/kiwun/Documents/ai/VPN/tests/test_api_payments_callbacks.py`
- `C:/Users/kiwun/Documents/ai/VPN/tests/test_bot_paywall.py`
- `C:/Users/kiwun/Documents/ai/VPN/docs/architecture/system-overview.md`
- `C:/Users/kiwun/Documents/ai/VPN/docs/architecture/app-first-and-bonus-flows.md`
- `C:/Users/kiwun/Documents/ai/VPN/docs/developer/work-orders/2026-04-beta-release/evidence/logs/WO-006-payments-keys-bonuses-support.md`
