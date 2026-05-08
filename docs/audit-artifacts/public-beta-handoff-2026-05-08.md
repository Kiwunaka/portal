# Public Beta Handoff 2026-05-08

Generated: 2026-05-08 19:10 MSK

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
- Admin release cockpit no longer has a permanent static runtime-download blocker; it reads the live `/api/client/apps` gate.
- Admin release cockpit now shows the exact operator inputs needed next: runtime-link GO markers, `EMAIL_PROBE_TO`, and `LAVATOP_PROBE_EMAIL`.
- Operator unblock packet: `docs/audit-artifacts/public-beta-unblock-packet-2026-05-08.md`.
- Telegram launch drafts were tightened so the short copy says POKROV is preparing a limited beta, not already launching it.
- Completion audit was refreshed to `docs/audit-artifacts/public-beta-completion-audit-2026-05-08.md`, and the machine-readable launch decision now points to it by default.
- External access preflight was refreshed so its default handoff source is `docs/audit-artifacts/public-beta-handoff-2026-05-08.md`.
- External access preflight now uses the latest post-handoff runtime smoke artifact `docs/audit-artifacts/runtime-app-download-smoke-brain-2026-05-08-post-handoff.json`.
- External access preflight public-claim guardrails now emit Russian operator text.
- Machine-readable launch decision now emits Russian safe/unsafe public claims.
- Public beta post-deploy probe and launch decision JSON were refreshed after the latest deploy/probe checks.
- GitHub Actions Guardrails are green on portal `master` at commit `417f418`; this is CI-safe repo evidence, not public-release authorization.
- Support/admin/redeem/promo/payment/email surfaces have the focused fixes and tests described in the current workspace diff.

## Verification Snapshot

- `npm.cmd run test:e2e:admin -- --grep "release cockpit"` -> PASS, 3 tests.
- `npm.cmd run test:e2e:admin -- --grep "release cockpit no-go"` -> PASS, 1 test, after RU-only admin release-cockpit copy refresh.
- `python -m pytest portal_bot\tests\test_email_auth.py tests\test_brain_payment_email_readiness.py tests\test_public_beta_post_deploy_probe.py -q` -> PASS, 23 tests.
- `python -m pytest tests\test_api_payments_callbacks.py -q -k "email_delivery or access_key_email or paid_access_key"` -> PASS, 1 test.
- `python -m pytest tests\test_paid_checkout_launch_evidence_check.py tests\test_public_beta_launch_decision.py -q` -> PASS, 13 tests.
- `python scripts\runtime_app_download_smoke.py --redact --apps-json docs\audit-artifacts\staged-client-apps-2026-05-07.json --require-release-handoff` -> PASS for staged APK/EXE/docs reachability.
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
- Telegram fallback-admin bot labels were kept RU-facing while preserving callback payloads; `python -m pytest tests\test_bot_paywall.py -q` -> PASS, 83 tests; helpbot/feedbackbot/menu tests -> PASS, 15 tests.
- `python scripts\remote_deploy_brain_portal_code.py --brain-ip 82.21.114.104 --restart portal-api,portal-bot,portal-helpbot,portal-feedbackbot` -> PASS; all requested services active.
- `python scripts\brain_telegram_bot_menu_check.py --brain-ip 82.21.114.104 --ssh-user root --ssh-port 29374 --output docs\audit-artifacts\telegram-bot-command-menu-brain-2026-05-08.json` -> PASS.
- `python scripts\verify_brain_ready.py --brain-ip 82.21.114.104 --ssh-user root --ssh-port 29374` -> PASS.
- `python scripts\text_integrity.py docs\audit-artifacts\public-beta-completion-audit-2026-05-08.md scripts\public_beta_launch_decision.py` -> PASS.
- `python scripts\text_integrity.py docs\launch\telegram-announcement.md` -> PASS.
- `python -m json.tool` on refreshed decision/probe JSON artifacts -> PASS.
- GitHub Actions Guardrails run `25570326956` on commit `417f418b89a85c3894e0e2a2aa4948d555c9fb93` -> PASS; CI release guardrails are scoped and skip operator-only client/browser gates as `SKIPPED_CI_UNAVAILABLE`.

## Live Status

- API health: PASS, `200`, status `ok`.
- GitHub Actions Guardrails: PASS, run `25570326956`, commit `417f418b89a85c3894e0e2a2aa4948d555c9fb93`.
- Backend deploy: latest portal code deploy restarted `portal-api`, `portal-bot`, `portal-helpbot`, and `portal-feedbackbot`; all are active.
- Email runtime status: PASS, public mode enabled, delivery URL and secret configured, debug echo off, no blocked reasons.
- Payment provider status: `BLOCKED_BY_ACCESS`; `/api/payments/providers` returns `blocked=true`, no providers, reason `paid_checkout_launch_evidence_missing`.
- GitHub release: published prerelease, not draft. APK and EXE assets are uploaded.
- Static deploy: latest static release id `20260508165715`; `https://app.pokrov.space/admin/release/` and `https://pokrov.space/install/` return `200`.

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
