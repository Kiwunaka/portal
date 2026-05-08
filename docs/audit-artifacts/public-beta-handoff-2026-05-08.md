# Public Beta Handoff 2026-05-08

Generated: 2026-05-08 21:22 MSK

Refreshed: 2026-05-09 after portal commit `023849b` and client commit `c5f40a6`.

## Verdict

`NO-GO` for broad public beta publication.

The release is prepared as far as current access allows: GitHub prerelease APK/EXE assets exist, static site/WebApp are deployed, backend is live, email auth runtime config is green, and the admin release cockpit exposes the remaining operator actions. Do not post the Telegram launch copy, do not claim public beta launch, and do not enable paid checkout.

## Deployed URLs

- Marketing: https://pokrov.space/
- Install/status page: https://pokrov.space/install/
- WebApp cabinet/admin: https://app.pokrov.space/
- Admin release cockpit: https://app.pokrov.space/admin/release/
- API health: https://api.pokrov.space/api/health
- GitHub prerelease: https://github.com/Kiwunaka/POKROV-app/releases/tag/v0.2.0-beta.1
- Android APK staged asset: https://github.com/Kiwunaka/POKROV-app/releases/download/v0.2.0-beta.1/pokrov-android-universal.apk
- Windows EXE staged asset: https://github.com/Kiwunaka/POKROV-app/releases/download/v0.2.0-beta.1/pokrov-windows-setup-x64.exe

## What Changed Since The Previous Handoff

- Client release metadata now points to the staged GitHub APK/EXE while keeping runtime sync, public announcement, and paid checkout blocked without explicit evidence.
- `POKROV-app/main` is pushed through commit `c5f40a6` (`Align client beta handoff posture`) with stable handoff `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/release-handoff.json`, versioned handoff `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/0.2.0-beta.1+20260508/release-handoff.json`, and retained `README.md` / `SHA256SUMS.txt`.
- GitHub prerelease notes for `v0.2.0-beta.1` were refreshed on 2026-05-08 to state `NO-GO`, runtime links closed, email proof pending, Lava.top proof pending, and no RU-origin readiness claim.
- Admin release cockpit no longer has a permanent static runtime-download blocker; it reads the live `/api/client/apps` gate.
- Admin release cockpit now shows the exact operator inputs needed next: runtime-link GO markers, `EMAIL_PROBE_TO`, and `LAVATOP_PROBE_EMAIL`.
- Operator unblock packet: `docs/audit-artifacts/public-beta-unblock-packet-2026-05-08.md`.
- Telegram launch drafts were tightened so the short copy says POKROV is preparing a limited beta, not already launching it.
- Completion audit was refreshed to `docs/audit-artifacts/public-beta-completion-audit-2026-05-08.md`, and the machine-readable launch decision now points to it by default.
- External access preflight was refreshed so its default handoff source is `docs/audit-artifacts/public-beta-handoff-2026-05-08.md`.
- External access preflight now uses the latest post-handoff runtime smoke artifact `docs/audit-artifacts/runtime-app-download-smoke-brain-2026-05-08-post-handoff.json`.
- External access preflight public-claim guardrails now emit Russian operator text.
- Machine-readable launch decision now emits Russian safe/unsafe public claims.
- Admin release cockpit now has copy buttons for the runtime-link GO text, email probe command, and Lava.top probe command.
- Public beta post-deploy probe and launch decision JSON were refreshed after the latest deploy/probe checks.
- GitHub Actions Guardrails are green on portal `master` at commit `023849b`; this is CI-safe repo evidence, not public-release authorization.
- Support/admin/redeem/promo/payment/email surfaces have the focused fixes and tests described below; platform tracked files are clean on `master`.
- Access-key and gift-card entry now tolerates common pasted separators (`U+2010..U+2014`, `U+2212`, underscores, and whitespace) across API, bot, cabinet redeem, admin promo lookup, and marketing checkout.
- Telegram OIDC finish now classifies `expired/deprecated` provider responses as refreshable auth errors instead of raw provider failures.
- Client cutover docs and seed metadata now reflect the accepted beta posture: Android `OPERATOR_ATTESTED`, Windows `UNSIGNED_BETA_RISK_ACCEPTED`, runtime sync still pending.
- Bot RUB payment buttons now follow the same paid-checkout launch evidence/email delivery gate as the API provider catalog: Lava.top is not rendered as `pay_rub:lavatop` until the shared gate is green.
- Bot paywall tests now reset DB/model-bound service modules between API and bot suites, preventing stale admin-test module state from breaking gift-card redemption coverage.

## Verification Snapshot

- `npm.cmd run test:e2e:admin -- --grep "release cockpit"` -> PASS, 3 tests.
- `npm.cmd run test:e2e:admin -- --grep "release cockpit no-go"` -> PASS, 1 test, after RU-only admin release-cockpit copy refresh.
- `python -m pytest portal_bot\tests\test_email_auth.py tests\test_brain_payment_email_readiness.py tests\test_public_beta_post_deploy_probe.py -q` -> PASS, 23 tests.
- `python -m pytest tests\test_api_payments_callbacks.py -q -k "email_delivery or access_key_email or paid_access_key"` -> PASS, 1 test.
- `python -m pytest tests\test_paid_checkout_launch_evidence_check.py tests\test_public_beta_launch_decision.py -q` -> PASS, 13 tests.
- `python scripts\runtime_app_download_smoke.py --redact --apps-json ..\POKROV-app\artifacts\releases\release-handoff.json --require-release-handoff --timeout 20` -> PASS for client handoff APK/EXE/docs reachability; GitHub release-asset redirect query strings are printed as `<redacted-query>`.
- `python scripts\brain_runtime_app_download_smoke.py --brain-ip 82.21.114.104 --ssh-user root --ssh-port 29374 --output docs\audit-artifacts\runtime-app-download-smoke-brain-2026-05-08-post-handoff.json` -> expected `BLOCKED_BY_ACCESS`; live `/api/client/apps` still lacks Android/Windows/docs URLs.
- `python scripts\public_beta_post_deploy_probe.py --brain-live-probe-json docs\audit-artifacts\brain-post-deploy-live-probe-2026-05-08.json --output docs\audit-artifacts\public-beta-post-deploy-probe-2026-05-08.json` -> expected `BLOCKED_BY_ACCESS`; email runtime config is PASS, live delivery and Lava invoice probes need operator inputs.
- `python scripts\public_beta_launch_decision.py --output docs\audit-artifacts\public-beta-launch-decision-2026-05-08.json` -> expected `NO_GO`.
- `python -m pytest tests\test_public_beta_launch_decision.py -q` -> PASS, 10 tests.
- `python -m pytest tests\test_public_beta_external_access_preflight.py tests\test_public_beta_launch_decision.py -q` -> PASS, 29 tests.
- `python -m pytest tests\test_public_beta_external_access_preflight.py -q` -> PASS, 21 tests.
- `python -m pytest tests\test_marketing_release_readiness.py -q -k public_beta_docs_pin_current_brain_truth_and_unblock_packet` -> PASS, 1 test.
- `python -m pytest tests\test_public_beta_launch_decision.py -q` -> PASS, 10 tests.
- `python scripts\public_beta_external_access_preflight.py --output docs\audit-artifacts\public-beta-external-access-preflight-2026-05-08.json` -> expected `BLOCKED_BY_ACCESS`.
- `python scripts\public_beta_launch_decision.py --output docs\audit-artifacts\public-beta-launch-decision-2026-05-08.json` -> expected `NO_GO`.
- `python scripts\text_integrity.py docs\audit-artifacts\public-beta-unblock-packet-2026-05-08.md docs\audit-artifacts\public-beta-handoff-2026-05-08.md docs\audit-artifacts\public-beta-completion-audit-2026-05-08.md` -> PASS.
- `python scripts\remote_deploy_brain_static_sites.py --brain-ip 82.21.114.104 --ssh-user root --ssh-port 29374` -> PASS, static release id `20260508163952`.
- `Invoke-WebRequest https://app.pokrov.space/admin/release/` -> `200`; `Invoke-WebRequest https://pokrov.space/install/` -> `200`.
- Public legal contact labels were kept RU-only; `python -m pytest tests\test_public_copy_guardrails.py -q` -> PASS, 6 tests; `npm.cmd run build` in `marketing/` -> PASS.
- `python scripts\remote_deploy_brain_static_sites.py --brain-ip 82.21.114.104 --ssh-user root --ssh-port 29374` -> PASS, static release id `20260508164448`.
- Admin user/payment operator copy was kept RU-facing; `npm.cmd run test:e2e:admin` -> PASS, 25 tests.
- `python scripts\remote_deploy_brain_static_sites.py --brain-ip 82.21.114.104 --ssh-user root --ssh-port 29374` -> PASS, static release id `20260508165120`.
- Admin payment nav label was kept RU-facing; `npm.cmd run test:e2e:admin` -> PASS, 25 tests.
- `python scripts\remote_deploy_brain_static_sites.py --brain-ip 82.21.114.104 --ssh-user root --ssh-port 29374` -> PASS, static release id `20260508165406`.
- Admin release cockpit operator blocker copy was kept RU-facing; `npm.cmd run test:e2e:admin -- --grep "release cockpit no-go"` -> PASS, 1 test.
- `python scripts\remote_deploy_brain_static_sites.py --brain-ip 82.21.114.104 --ssh-user root --ssh-port 29374` -> PASS, static release id `20260508165715`.
- Telegram deprecated OAuth callback now auto-restarts one fresh Telegram OIDC attempt instead of exposing raw `deprecated_token`; `npx.cmd playwright test oidc-fallback.spec.ts telegram-login-refresh.spec.ts --reporter=line` -> PASS, 7 tests; `npm.cmd run build` in `webapp/` -> PASS; GitHub Actions Guardrails run `25573819924` on commit `56f13c7152651b20e0403bdd0ace680854174bed` -> PASS.
- `python scripts\remote_deploy_brain_static_sites.py --brain-ip 82.21.114.104` -> PASS, static release id `20260508190122`; post-deploy static smoke and `python scripts\verify_brain_ready.py --brain-ip 82.21.114.104` -> PASS.
- Live Chromium visual sweep for `https://pokrov.space/`, `https://pokrov.space/checkout/`, and `https://app.pokrov.space/` across desktop/mobile/dark/Telegram-like viewports -> PASS, 7 scenarios, no JS/page errors, no horizontal overflow, summary `.tmp\live-visual-sweep-2026-05-08T19-40-19-624Z\summary.json`.
- `npx.cmd playwright test cabinet-flow.spec.ts admin-gate.spec.ts --grep "narrow mobile viewport|admin pages clickable" --reporter=line` -> PASS, 2 tests, authenticated cabinet/admin mobile overflow coverage via mocked e2e.
- `npx.cmd playwright test cabinet-flow.spec.ts --grep "access keys|promo codes" --reporter=line` -> PASS, 2 tests for cabinet gift/access-key and promo redemption.
- `python -m pytest tests\test_bot_paywall.py -q -k "modern_button_fields or public_bot_cabinet or access_key_button or main_menu"` -> PASS, 18 tests for modern bot button fields and public bot menu/account surfaces.
- Current official Telegram Bot API docs confirm `style` and `icon_custom_emoji_id` on `KeyboardButton` / `InlineKeyboardButton` as Bot API 9.4 fields; local aiogram field probe returns `style`, `icon_custom_emoji_id`, and `copy_text`, and the focused modern-button bot test above remains PASS. Arbitrary Material icon packs are still not a Bot API field.
- Admin release cockpit operator command copy buttons: RED then GREEN `npx.cmd playwright test admin-gate.spec.ts --grep "release cockpit no-go" --reporter=line`; focused `npx.cmd playwright test admin-gate.spec.ts --grep "release cockpit" --reporter=line` -> PASS, 3 tests; `npm.cmd run build` in `webapp/` -> PASS.
- `python scripts\remote_deploy_brain_static_sites.py --brain-ip 82.21.114.104 --ssh-user root --ssh-port 29374` -> PASS, static release id `20260508195049`; `python scripts\verify_brain_ready.py --brain-ip 82.21.114.104 --ssh-user root --ssh-port 29374` -> PASS; live browser check of `https://app.pokrov.space/admin/release/` had 0 console errors/warnings and no horizontal overflow on the unauthenticated entry.
- GitHub Actions Guardrails run `25576322253` on commit `ac5ad12f62d7e772e9eba893a685e920603d159e` -> PASS; CI release guardrails remain scoped and are not public-release authorization.
- `python -m pytest tests\test_api_auth_and_tickets.py -q -k "access_key_status_and_redeem_normalize"` -> PASS, 1 test; `python -m pytest tests\test_bot_paywall.py -q -k "redeem_gift_card_normalizes_human_key_input or redeem_gift_card_respects_campaign_segment_restrictions"` -> PASS, 2 tests; `npx.cmd playwright test cabinet-flow.spec.ts --grep "access keys" --reporter=line` -> PASS, 1 test; `npm.cmd run build` in `webapp/` and `marketing/` -> PASS.
- `python -m pytest portal_bot\tests\test_telegram_oidc_auth.py -q` -> PASS, 5 tests; `npx.cmd playwright test telegram-login-refresh.spec.ts oidc-fallback.spec.ts --reporter=line` -> PASS, 7 tests; `python -m pytest tests\test_api_auth_and_tickets.py -q -k "web_login_rejects_expired_payload or auth_session_prefers_valid_web_session or auth_session_uses_telegram_init_data_when_web_session_is_expired or auth_session_rejects_stale_signed_telegram_init_data or auth_session_rejects_expired_web_session"` -> PASS, 5 tests.
- `python scripts\remote_deploy_brain_portal_code.py --brain-ip 82.21.114.104 --ssh-user root --ssh-port 29374 --restart portal-api,portal-bot` -> PASS after access-key separator normalization; `python scripts\remote_deploy_brain_static_sites.py --brain-ip 82.21.114.104 --ssh-user root --ssh-port 29374` -> PASS, static release id `20260508220115`; `python scripts\verify_brain_ready.py --brain-ip 82.21.114.104 --ssh-user root --ssh-port 29374` -> PASS.
- `python scripts\remote_deploy_brain_portal_code.py --brain-ip 82.21.114.104 --ssh-user root --ssh-port 29374 --restart portal-api` -> PASS after Telegram OIDC classification; `python scripts\verify_brain_ready.py --brain-ip 82.21.114.104 --ssh-user root --ssh-port 29374` -> PASS.
- `python -m pytest tests\test_bot_paywall.py -q -k "hides_lavatop_until_checkout_gate_is_green"` -> RED then PASS, 1 regression test proving the bot hides Lava.top while checkout evidence/email delivery gate is not green.
- `python -m pytest tests\test_bot_paywall.py -q` -> PASS, 88 tests after bot checkout-gate and module-isolation updates.
- `python -m pytest tests\test_lavatop_payment_providers.py tests\test_paid_checkout_launch_evidence_check.py tests\test_payment_email_readiness_smoke.py tests\test_api_payments_callbacks.py -q` -> PASS, 42 tests.
- `python -m pytest portal_bot\tests\test_telegram_oidc_auth.py portal_bot\tests\test_email_auth.py tests\test_api_auth_and_tickets.py tests\test_api_payments_callbacks.py tests\test_admin_payments_api.py tests\test_bot_paywall.py tests\test_lavatop_payment_providers.py tests\test_payment_email_readiness_smoke.py tests\test_paid_checkout_launch_evidence_check.py tests\test_public_beta_external_access_preflight.py tests\test_public_beta_post_deploy_probe.py tests\test_public_beta_launch_decision.py -q` -> PASS, 257 tests; 11 existing deprecation warnings and a non-fatal Windows pytest temp cleanup warning.
- GitHub Actions Guardrails run `25581649885` on portal commit `479dd1b` -> PASS; run `25581858872` on portal commit `23e894e` -> PASS; run `25583770912` on portal commit `023849b` -> PASS.
- `python scripts\remote_deploy_brain_portal_code.py --brain-ip 82.21.114.104 --ssh-user root --ssh-port 29374 --restart portal-api,portal-bot` -> PASS after the bot RUB checkout gate; `python scripts\verify_brain_ready.py --brain-ip 82.21.114.104 --ssh-user root --ssh-port 29374` -> PASS; live `/api/payments/providers` remained `blocked=true` with reason `paid_checkout_launch_evidence_missing`.
- `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate-seed.ps1` in `C:/Users/kiwun/Documents/ai/POKROV-app` -> PASS after client posture metadata refresh; `python -m json.tool` on `config/release-handoff.seed.json` and `config/cutover-readiness.seed.json` -> PASS; `c5f40a6` pushed to `POKROV-app/main`.
- Telegram fallback-admin bot labels were kept RU-facing while preserving callback payloads; `python -m pytest tests\test_bot_paywall.py -q` -> PASS, 83 tests; helpbot/feedbackbot/menu tests -> PASS, 15 tests.
- `python scripts\remote_deploy_brain_portal_code.py --brain-ip 82.21.114.104 --restart portal-api,portal-bot,portal-helpbot,portal-feedbackbot` -> PASS; all requested services active.
- `python scripts\brain_telegram_bot_menu_check.py --brain-ip 82.21.114.104 --ssh-user root --ssh-port 29374 --output docs\audit-artifacts\telegram-bot-command-menu-brain-2026-05-08.json` -> PASS.
- `python scripts\verify_brain_ready.py --brain-ip 82.21.114.104 --ssh-user root --ssh-port 29374` -> PASS.
- `python scripts\text_integrity.py docs\audit-artifacts\public-beta-completion-audit-2026-05-08.md scripts\public_beta_launch_decision.py` -> PASS.
- `python scripts\text_integrity.py docs\launch\telegram-announcement.md` -> PASS.
- `python -m json.tool` on refreshed decision/probe JSON artifacts -> PASS.
- `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate-seed.ps1` in `C:/Users/kiwun/Documents/ai/POKROV-app` -> PASS.
- `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\bootstrap-workspace.ps1 -OfflinePubGet` in `C:/Users/kiwun/Documents/ai/POKROV-app` -> PASS.
- `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build-windows-release.ps1 -SkipAnalyze -SkipTests -SkipBuild -OfflinePubGet` in `C:/Users/kiwun/Documents/ai/POKROV-app` -> PASS, unsigned setup EXE and portable ZIP staged locally.
- `python scripts\remote_brain_apply_release_handoff.py --brain-ip 82.21.114.104 --metadata-file ..\POKROV-app\artifacts\releases\release-handoff.json --dry-run` -> PASS, validates staged `APP_*` values without SSH write or restart.
- GitHub Actions Guardrails run `25571494051` on commit `62da31eed21feaafaf1dc1c580be70d274b5f4d3` -> PASS; CI release guardrails are scoped, force the Node 24 actions runtime, and skip operator-only client/browser gates as `SKIPPED_CI_UNAVAILABLE`.

## Live Status

- API health: PASS, `200`, status `ok`.
- GitHub Actions Guardrails: PASS, latest portal run `25583770912`, commit `023849b`.
- Backend deploy: latest portal code deploy restarted `portal-api` and `portal-bot` after the bot RUB checkout gate; previous deploys restarted `portal-api` after Telegram OIDC classification and `portal-api,portal-bot` after access-key separator normalization; all services are active in brain readiness.
- Email runtime status: PASS, public mode enabled, delivery URL and secret configured, debug echo off, no blocked reasons.
- Payment provider status: `BLOCKED_BY_ACCESS`; `/api/payments/providers` returns `blocked=true`, no providers, reason `paid_checkout_launch_evidence_missing`; the Telegram bot also hides Lava.top RUB payment CTAs behind the same gate.
- GitHub release: published prerelease, not draft. APK and EXE assets are uploaded; release notes now explicitly say `NO-GO` and keep runtime links/payment/public announcement closed.
- Static deploy: latest static release id `20260508220115`; `https://app.pokrov.space/admin/release/`, `https://app.pokrov.space/`, and `https://pokrov.space/checkout/` return `200`.

## Remaining Blockers

- Runtime APP links: `BLOCKED_BY_ACCESS` until explicit runtime-link sync GO is provided and live `/api/client/apps` smoke passes.
- Email delivery proof: `BLOCKED_BY_ACCESS` until a safe `EMAIL_PROBE_TO` recipient is provided and verify/reset/payment-access-key email probes pass.
- Lava.top payment: `BLOCKED_BY_ACCESS` until invoice creation, authenticated webhook, replay/idempotency, failed-payment no-fulfillment, manual-review mismatch, reconciliation, and paid access-key email delivery evidence are green.
- Public handoff policy: `BLOCKED_BY_POLICY`; current decision remains `NO_GO`.
- RU-origin check: `SKIPPED_BY_OPERATOR`; do not claim RU-origin readiness.
- Windows signing: unsigned beta risk accepted for this outside-store pass; do not claim trusted signing.

## Operator Inputs Needed

For runtime app-download smoke only, provide this exact authorization text:

```text
RUNTIME LINK SYNC GO FOR APP-DOWNLOAD SMOKE
OPERATOR_APPROVED_RUNTIME_LINK_SYNC=true
STAGED GITHUB ASSET REACHABILITY GREEN
NO PUBLIC ANNOUNCEMENT
PAID CHECKOUT REMAINS CLOSED
```

For email proof, provide a safe probe mailbox and run:

```powershell
python scripts\brain_payment_email_readiness.py --brain-ip 82.21.114.104 --ssh-user root --ssh-port 29374 --post-deploy-live --email-probe-to <probe-email> --output docs\audit-artifacts\brain-post-deploy-live-probe-2026-05-08.json
```

For combined email plus Lava invoice proof, provide a safe buyer email and run:

```powershell
python scripts\brain_payment_email_readiness.py --brain-ip 82.21.114.104 --ssh-user root --ssh-port 29374 --post-deploy-live --email-probe-to <probe-email> --lavatop-probe-email <buyer-email> --output docs\audit-artifacts\brain-post-deploy-live-probe-2026-05-08.json
```

## Safe Public Claims

- POKROV готовит ограниченную бета-проверку для Android и Windows вне магазинов.
- APK и EXE подготовлены как предварительные GitHub-артефакты для проверки; они еще не являются рабочим путем загрузки в кабинете или приложении.
- Оплата пока закрыта до финальной проверки Lava.top, вебхуков, сверки и доставки ключей доступа на email.
- Email-вход включен по конфигурации, но живая доставка писем должна быть подтверждена отдельной проверкой.
- Android-кандидат принят оператором как проверенный для этой волны; это не магазинная публикация.
- Windows EXE остается неподписанной beta-сборкой и может показывать предупреждение неизвестного издателя.

## Unsafe Public Claims

- Публичная бета уже запущена.
- GitHub Releases уже являются рабочим путем загрузки в кабинете или приложении.
- Оплата Lava.top работает в бою.
- Email-доставка писем уже доказана живой проверкой почтового ящика.
- Windows-сборка подписана доверенным сертификатом.
- RU-origin доступность Telegram проверена.
