# Public Beta Completion Audit 2026-05-08

Generated: 2026-05-08, refreshed after `docs/audit-artifacts/public-beta-handoff-2026-05-08.md`.

Refreshed: 2026-05-09 after portal commit `023849b` and client commit `c5f40a6`.

## Objective Restated

Bring POKROV to a release-honest public beta outside app stores as far as current access allows: GitHub Releases APK/EXE distribution, deployed site/WebApp/backend/bot surfaces, email auth, Lava.top-only paid checkout policy, access keys/gift cards, support, admin release cockpit, docs/tests/deploy evidence, and a final handoff with exact safe public claims.

## Verdict

GOAL NOT COMPLETE. Public beta publication remains `NO-GO`.

The workspace is prepared as far as current access allows, but final publication is still blocked by missing operator/external evidence:

- runtime `APP_*` link sync approval and live `/api/client/apps` download smoke;
- live email delivery proof with a safe `EMAIL_PROBE_TO`;
- Lava.top live invoice/webhook/replay/failure/manual-review/reconciliation/paid access-key email evidence;
- final public publication `GO`.

## Prompt-To-Artifact Checklist

| Requirement | Evidence | Status | Gap / note |
| --- | --- | --- | --- |
| Work in current master workspace and preserve dirty changes | Local git tree remains dirty; no reset/checkout/revert of unrelated files | PASS | Changes are intentionally not mass-cleaned. |
| Use local canon first | `AGENTS.md`, `DESIGN.md`, `shared/*`, canonical docs, active `POKROV-app/docs/*` | PASS | Public claims remain release-honest and RU-first. |
| Use lane subagents where useful | Lane read-only audits returned backend/web/support/release findings | PASS | Remaining actionable findings were either already fixed in current code or not launch-blocking. |
| External DeepSeek/Kimi design/copy critique where useful | Earlier handoff/audit record Kimi copy critique of launch/payment ambiguity | PASS | External output treated as draft only; local canon won. |
| Site and install page deployed | `https://pokrov.space/`, `https://pokrov.space/install/`, static release `20260508220115` | PASS | Runtime app links still not live. |
| WebApp cabinet and admin deployed | `https://app.pokrov.space/`, `https://app.pokrov.space/admin/release/`, static smoke `200` | PASS | Admin auth screen rendered without Next overlay in unauthenticated browser check. |
| Backend API live | `https://api.pokrov.space/api/health` returned `200` / `{"status":"ok"}` | PASS | Does not prove runtime app links or paid checkout. |
| GitHub Releases APK/EXE distribution | `v0.2.0-beta.1` prerelease, APK SHA256 `1A369891641964A9A30A296E7D47111A07B6DDAAD5ABC293F7EF938A654DADB0`, EXE SHA256 `E340F36EC10149649373E0E7816C81B8C6873E9B95C7A85DC0F6AD708DB2C70D`, `POKROV-app/main` commit `c5f40a6` | STAGED_PASS | Published as prerelease staging, not final runtime download path; client docs/seeds now carry `OPERATOR_ATTESTED` Android and `UNSIGNED_BETA_RISK_ACCEPTED` Windows posture. |
| Exclude stores, Apple release, appcast, MSIX/ZIP first-layer public distribution | Handoff and launch copy keep outside-store APK/EXE path only | PASS | Windows EXE remains unsigned; do not claim trusted signing. |
| Runtime `/api/client/apps` exposes release APK/EXE/docs | `docs/audit-artifacts/runtime-app-download-smoke-brain-2026-05-08-post-handoff.json` | BLOCKED_BY_ACCESS | Live payload still has empty Android/Windows/docs URLs. |
| Runtime link sync guarded | `docs/audit-artifacts/runtime-link-sync-guard-2026-05-08.md`; dry-run passes, mutation requires GO evidence | PASS_AS_GUARD | Guard is green; sync itself is not authorized. |
| Full email auth: register, verify, login, recovery | `portal_bot/tests/test_email_auth.py`, WebApp auth/e2e coverage, live `/api/auth/email/status` | CONFIG_PASS | Live inbox delivery still needs `EMAIL_PROBE_TO`. |
| Paid access-key delivery by email | Payment callback/email tests and admin resend tests | LOCAL_PASS_BLOCKED_LIVE | Fresh live paid-key email proof is missing. |
| Lava.top-only paid checkout | Live `/api/payments/providers` returns blocked with `paid_checkout_launch_evidence_missing`; launch evidence JSON is blocked; bot RUB buttons now share the paid-checkout evidence/email delivery gate | POLICY_PASS_BLOCKED_LIVE | Correctly closed until Lava evidence is green, including Telegram bot payment CTAs. |
| Access keys and gift cards | Backend unified access-key endpoints, cabinet `/redeem/`, bot gift/access-key redeem coverage, admin promos/access-key issue UI | LOCAL_PASS | Human-pasted separators are normalized across API, bot, cabinet, admin promo lookup, and marketing checkout; live operator redemption smoke not rerun after final deploy. |
| Promo/checkout consistency | Backend order creation applies `promo_code` through pricing preview and records final/base amounts | LOCAL_PASS | Paid checkout still closed by evidence gate. |
| Account surface parity across site, cabinet, bot | Cabinet/dashboard/settings/redeem/support surfaces, marketing checkout access-key handoff, bot `/cabinet`, `/support`, `/redeem` | LOCAL_PASS | Actual one-tap connection remains app-side by design. |
| Telegram deprecated/expired login UX | `webapp/e2e/telegram-login-refresh.spec.ts`, `webapp/e2e/oidc-fallback.spec.ts`, `portal_bot/tests/test_telegram_oidc_auth.py`, backend/session refresh code | PASS | Focused Telegram e2e and backend OIDC tests passed; deprecated/expired OIDC provider responses are classified as refreshable auth errors. |
| Telegram bot buttons follow current Bot API fields | `portal_bot/telegram_buttons.py`, bot tests, official Bot API `InlineKeyboardButton` fields | PASS | Telegram supports `style` / `icon_custom_emoji_id`; arbitrary Material icon packs are not a bot API feature. |
| Support flow | API/ticket tests, cabinet/admin ticket pages, protected attachment handling, helpbot/main bot support entrypoints | LOCAL_PASS | Real user live ticket smoke not rerun. |
| Admin release cockpit | `webapp/src/app/(dashboard)/admin/release/page.tsx`, focused release cockpit e2e, live static deploy `20260508220115` | PASS | Shows exact operator blockers, copy buttons for GO/probe commands, and no permanent static runtime blocker. |
| Telegram launch copy prepared but not posted | `docs/launch/telegram-announcement.md` | PASS_DRAFT_ONLY | Copy says preparing limited beta; post only after final GO/runtime links. |
| Backend/payment/email focused verification | Latest handoff lists email/payment/access-key pytest passes, including the 257-test payment/email/bot matrix after the bot checkout-gate fix | PASS | Pytest Windows atexit cleanup warning was non-fatal. |
| Web admin/browser verification | `npm.cmd run test:e2e:admin -- --grep "release cockpit"` passed 3 tests | PASS | Full broad rerun was avoided to reduce churn. |
| Marketing/copy checks | `scripts/text_integrity.py docs/launch/telegram-announcement.md`; launch handoff text integrity | PASS | Public copy remains RU/release-honest. |
| Client build/preflight evidence | `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/release-handoff.json`, versioned handoff `0.2.0-beta.1+20260508`, versioned `README.md` / `SHA256SUMS.txt`, Windows packaging smoke with `-OfflinePubGet`, and GitHub release assets | STAGED_PASS | Physical Android audit is operator-attested; Windows unsigned risk accepted; client seed metadata was refreshed and validated. |
| Visual QA | Live Chromium sweep `.tmp/live-visual-sweep-2026-05-08T19-40-19-624Z/summary.json`; focused WebApp mobile e2e | PASS_WITH_SCOPE_LIMITS | Fresh sweep covered marketing home desktop/mobile/dark, checkout mobile, WebApp entry desktop/mobile-dark/Telegram-like with no JS/page errors or horizontal overflow; authenticated cabinet/admin mobile viewport coverage remains mocked e2e, not live operator-session browsing. |
| Current-origin and brain-origin gates | Launch decision reads current full/quick and brain quick gate artifacts | PASS_WITH_SCOPE_LIMITS | Green gates do not cover missing runtime links, Lava proof, or live inbox delivery. |
| GitHub Actions repo guardrails | Guardrails run `25583770912` on portal commit `023849b` | PASS_WITH_SCOPE_LIMITS | CI guardrails are green on the forced Node 24 actions runtime, but skip operator-only client/browser gates as `SKIPPED_CI_UNAVAILABLE` and are not public-release authorization. |
| Static/backend deploy | Static release `20260508220115`; backend deploy restarted `portal-api,portal-bot` after the bot RUB checkout gate; earlier deploys covered Telegram OIDC classification and access-key normalization | PASS | Runtime env link sync intentionally not applied. |
| RU-origin | `docs/audit-artifacts/ru-origin-skip-accepted-2026-05-08.md` | SKIPPED_BY_OPERATOR | Do not claim RU-origin Telegram readiness. |
| Release handoff | `docs/audit-artifacts/public-beta-handoff-2026-05-08.md` | PASS_NO_GO | Final output exists but says `NO-GO`. |
| External unblock packet | `docs/audit-artifacts/public-beta-unblock-packet-2026-05-08.md` | PASS | Current operator runbook points to 2026-05-08 handoff/completion audit and the post-handoff runtime smoke artifact. |
| Machine-readable decision | `docs/audit-artifacts/public-beta-launch-decision-2026-05-08.json` | NO_GO_EXPECTED | Correctly prevents accidental public launch claims. |

## Proxy Signal Limits

- Passing local or brain gates does not prove runtime `APP_*` links, live email inbox delivery, Lava.top payment evidence, RU-origin Telegram reachability, or final public authorization.
- Passing GitHub Actions repo guardrails does not prove operator-only client/browser gates or authorize public publication.
- GitHub prerelease asset reachability through the client handoff does not prove those links are live inside `/api/client/apps`.
- Email runtime config being green does not prove a real verify/reset/access-key message reached an inbox.
- A blocked payment provider catalog is correct launch honesty, not a paid-checkout launch.
- Admin release cockpit being deployed proves visibility, not operator approval.

## Remaining Concrete Inputs

Runtime link sync requires this exact operator text before mutation:

```text
RUNTIME LINK SYNC GO FOR APP-DOWNLOAD SMOKE
OPERATOR_APPROVED_RUNTIME_LINK_SYNC=true
STAGED GITHUB ASSET REACHABILITY GREEN
NO PUBLIC ANNOUNCEMENT
PAID CHECKOUT REMAINS CLOSED
```

Email proof requires a safe `EMAIL_PROBE_TO`.

Lava.top proof requires a safe `LAVATOP_PROBE_EMAIL` plus redacted evidence for invoice creation, authenticated webhook, replay/idempotency, failed payment, manual-review mismatch, reconciliation, and paid access-key email delivery.

## Safe Conclusion

POKROV is in public-beta preparation with staged GitHub prerelease APK/EXE assets, deployed public surfaces, green scoped gates, and an operator-facing release cockpit. It is not yet a public beta launch, live runtime app-download launch, or paid Lava.top checkout launch.
