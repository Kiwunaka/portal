# Research Synthesis

Status: research complete; gate evidence updated 2026-04-26

This synthesis uses only written evidence from `research/R01-*.md` through `research/R10-*.md`. Hidden agent memory is not release evidence.

## Executive Summary

POKROV is not open-public-beta-ready from the current evidence. The inherited paid/invite beta candidate is locally stronger than the original baseline, but open public beta raises the bar: public checkout, trial, downloads, support, admin controls, artifact truth, deployment, origin checks, rollback, and communications must all be safe for arbitrary public users.

The local candidate has useful green evidence, including fresh public-copy guardrails and inherited local release reports. IC-003 also fixed the obvious local public-surface drift: stale paid/invite copy, checkout noindex, email signup wording, fake homepage connected timer, and downloads warning posture. IC-006 through IC-009 then closed or sharpened several operational unknowns: brain-origin gates now pass, RU-origin evidence exists, client builds pass, payment provider access reaches FreeKassa, and runtime/Android blockers are documented as token/device gated. That still does not clear public beta. Android remains public-blocked. FreeKassa merchant activation is blocking paid checkout. Runtime download handoff still needs a live token. RU-origin Telegram reachability failed from `mini`. Live deploy, backup/rollback, and emergency controls are not yet final signoff evidence.

Recommended decision: keep the public beta wave `blocked` until the P0 gates below are closed or the public claim is narrowed so the failed claim no longer exists.

## Post-Synthesis Local Remediation

IC-003 completed a safe local slice that does not require live credentials or artifact signing:

- Added guardrails for stale paid/invite beta copy, checkout noindex, homepage fake timer, and outdated email-signup wording.
- Changed `/checkout/` metadata from `noIndex: true` to `noIndex: false`.
- Replaced public landing status copy with public-beta wording instead of paid/invite-beta wording.
- Replaced the homepage mock `Подключено / 00:12:34` with a non-live beta preview label.
- Made cabinet downloads copy explicit about Android production signing plus physical release-build audit and unsigned Windows warnings.
- Replaced wildcard credentialed API CORS with an explicit production/dev allowlist and backend regression coverage.
- Fixed worktree node-access key lookup and produced a brain-origin quick release gate report with status `PASS`.
- Ran RU-origin probe from `mini`: canonical POKROV hosts and foreign delivery nodes pass, Telegram targets fail.
- Built Windows beta zip/manifest plus Android release APK/AAB.
- Probed FreeKassa from brain for `site` and `bot`: both reach the provider and both are blocked by `Merchant not activated`.

These fixes reduce public-copy risk but do not close live release gates.

## Confirmed Public Beta Blockers

| Area | Finding | Evidence |
|---|---|---|
| Product scope | Prior paid beta was already blocked; open public beta removes invite containment and makes checkout/trial/download/support safety P0. | R01, R10 |
| Android | Android is public-blocked by missing production signing and missing physical release-build localhost/control-surface audit. | R01, R08, R09, R10 |
| Windows | Windows has a local unsigned beta ZIP/manifest, but no trusted signing, public approval, final retained 0.2.0 checksums, or runtime handoff proof. The 0.2.0 beta zip/manifest build passed in IC-009. | R08, IC-009 |
| Release handoff | Stable client `artifacts/releases/release-handoff.json` still points at seed-era metadata with blank public URLs while 0.2.0 beta metadata exists separately. | R08 |
| Payments | Provider/category acceptance and live signed webhook proof are blocked by provider status: FreeKassa returns `Merchant not activated` for `site` and `bot`. | R07, R10, IC-008 |
| Payments | Paid callbacks extend access directly instead of issuing activation keys for key-first redemption. | R07 |
| Payments | Refund/chargeback/manual-review paths are reconciliation-only and do not adjust entitlement. | R07 |
| Marketing | Stale paid/invite-beta copy remained on public landing surfaces; locally fixed in IC-003. | R03, IC-003 |
| Marketing | `/checkout/` was `noIndex: true`; locally changed to indexable in IC-003. | R03, IC-003 |
| Marketing | Checkout copy implied public email signup; locally corrected to canonical `soon` wording in IC-003. | R03, IC-003 |
| Cabinet | Consumer payment history is an honest unavailable state, but paid users lack self-serve payment/receipt visibility. | R04 |
| Cabinet/visual | Downloads route needed Android/Windows limitation copy aligned with public beta status; locally hardened in IC-003. | R02, IC-003 |
| Marketing/visual | Homepage included a visually public fake connected timer/status mock; locally replaced in IC-003. | R02, IC-003 |
| Admin | Admin is materially stronger, but live admin login/data freshness and emergency controls are unverified. | R05 |
| Admin | Network rollout editor is raw JSON with high blast radius. | R05 |
| Backend | Live Postgres schema/migration state and live control-panel sync are blocked by missing access. | R06 |
| Backend | No first-class app session or multi-device table; exact per-device revoke/session lifecycle cannot be promised. | R06 |
| Backend | Fresh `install_id` trial abuse remains probable with only in-process origin rate limits. | R06 |
| Backend | Telegram OIDC start/finish endpoints are not throttled while docs describe Telegram auth beta surfaces as throttled. | R06 |
| Infra | Brain-origin quick gates pass; RU-origin from `mini` reaches canonical hosts and delivery nodes, but Telegram targets fail with network unreachable. | R09, R10, IC-006, IC-007 |
| Infra | Production Postgres backup/restore proof is unknown. | R09, R10 |
| Metrics | `/api/admin/metrics/status` does not fully match documented `ok/stale/missing/unavailable/failed` semantics. | R09 |
| Security/privacy | Wildcard credentialed CORS was locally fixed in IC-004; P1 hardening remains around `localStorage` bearer sessions, bearerless support-upload URLs, and SSH `AutoAddPolicy()`. | R09, IC-004 |
| QA | Current green reports are stale for final public signoff while the candidate is actively dirty. | R10 |
| Comms | Public launch communications are draft-only and not approved while signoff is blocked. | R10 |

## Public Beta Scope Recommendation

Do not call the current candidate an open public Android+Windows beta.

Acceptable narrowed states:

- Public site can explain public beta status, limitations, and support paths.
- Checkout can remain unavailable/maintenance until live provider/webhook/idempotency evidence exists.
- Android must remain internal-only, coming soon, or blocked until signing and physical audit pass.
- Windows can remain a gated unsigned beta candidate only with visible SmartScreen/unknown-publisher warning, checksum metadata, and runtime handoff proof.
- Email continuation remains `soon`.
- Apple remains readiness-only.
- Support is cabinet ticket first with Telegram fallback and best-effort wording only.

## P0 Gate Classification

| Gate | Current status | Required next evidence |
|---|---|---|
| Public copy guardrail | local PASS after IC-003/IC-004 | rerun before promotion |
| Public checkout | provider-blocked | activate FreeKassa merchant or configure an approved active provider; rerun live order + webhook proof |
| Payment entitlement | partial local evidence | rerun payment tests and decide key-first versus direct extension |
| Trial | local code present | abuse/rate-limit review plus live managed profile proof |
| Managed profile | local code present | live control-panel/profile smoke |
| Android public | build pass, physical audit blocked | production signing plus physical release-build audit |
| Windows public | beta build pass, public risk open | final metadata/checksums, warning UX, runtime smoke, signing or accepted unsigned risk |
| Cabinet support | local code present | fresh E2E for thread/reply/upload plus live storage/session proof |
| Admin | partial | local admin gates plus live admin data/emergency-control verification |
| Observability | partial | live `/api/admin/metrics/status`, node health, RU Telegram fallback/risk decision |
| Deploy/rollback | blocked | deploy plan, backup/rollback proof, previous deployed version |
| Communications | draft | public-beta-specific copy approved after final scope |

## Work Order Routing Notes

- W01 should continue visual evidence checks; initial fake connected timer and beta-warning copy were fixed locally in IC-003.
- W02 should continue install/legal/public checkout verification; initial paid/invite-beta copy, `/checkout/` indexing, and email `soon` wording were fixed locally in IC-003.
- W03 should continue payment-history/support/artifact truth; initial cabinet downloads warning copy was hardened locally in IC-003.
- W04 should focus on emergency controls, payment/reconciliation clarity, network-rollout guardrails, and live admin verification notes.
- W05 should address Telegram OIDC rate-limit drift, document session/device limitations, and keep live Postgres/control-panel proof as blockers.
- W06 should decide key-first fulfillment alignment, add activation-key endpoint coverage, and keep live provider proof as a P0 blocker.
- W07 should update client release-handoff metadata, package/audit command alignment, Windows artifact retention/checksums, and Android blocked state.
- W08 should classify backup/rollback/origin evidence and metrics semantics.
- W09 should track security/privacy P1s and decide which must be fixed before any public traffic.
- W09 locally closed wildcard credentialed CORS in IC-004; remaining P1s need explicit fix or risk acceptance.
- W10 should own final signoff, gate reruns, blocked decision, and promotion/deploy record.

## Validation Already Run In This Wave

```powershell
python -m pytest tests/test_public_copy_guardrails.py -q
```

Initial result: `5 passed in 0.19s`.

After IC-003:

```powershell
python -m pytest tests/test_public_copy_guardrails.py -q
npm.cmd run check:seo # in marketing/
npm.cmd run build # in marketing/
npm.cmd run build # in webapp/
npm.cmd run test:e2e # in webapp/
python -m pytest tests/test_api_auth_and_tickets.py -q
```

Results: copy guardrails `6 passed`, marketing SEO passed, marketing build passed, webapp build passed, webapp E2E `31 passed`, auth/tickets API tests `58 passed`.

Default release-gate reporter:

```powershell
python scripts/release_gate_check.py --output docs/audit-artifacts/public_beta_release_gate_report.md
```

Result: local current-origin gate set passed.

Additional 2026-04-26 evidence:

```powershell
python scripts/release_gate_check.py --quick --brain-ip 82.21.114.104 --web-domain pokrov.space --passwords <root PASSWORDS.txt> --output docs/audit-artifacts/public_beta_release_gate_report_brain.md
python scripts/render_ru_probe_report.py --input docs/audit-artifacts/ru_probe_2026-04-26.json --output docs/audit-artifacts/ru_probe_2026-04-26.md
python -m pytest tests/test_api_payments_callbacks.py tests/test_admin_payments_api.py tests/test_freekassa_api_probe.py -q
python scripts/run_client_release_gate.py build --target windows
python scripts/run_client_release_gate.py build --target android-apk
python scripts/run_client_release_gate.py build --target android-aab
```

Results: brain-origin quick gate `PASS`; RU canonical hosts and delivery nodes pass with `telegram_reachability_problem`; payment/admin/probe tests `25 passed`; client platform builds pass. Public beta remains blocked by provider activation, Android physical audit, runtime app-download token smoke, RU Telegram reachability/fallback decision, and deploy/rollback/promotion proof.
