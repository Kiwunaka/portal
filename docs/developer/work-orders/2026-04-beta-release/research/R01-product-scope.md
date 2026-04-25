# R01 Product Scope

Status: [confirmed] complete

## Scope

- [confirmed] Product scope, beta definition, canonical docs conflicts, public copy guardrails, stale-label audit, and P0/P1/deferred split for the paid beta wave.
- [confirmed] This is a read-only research pass; only this R01 markdown file was updated.

## Files/docs inspected

- [confirmed] `AGENTS.md`.
- [confirmed] `docs/README.md`.
- [confirmed] `docs/product/portal-vpn-product.md`.
- [confirmed] `docs/architecture/system-overview.md`.
- [confirmed] `docs/architecture/app-first-and-bonus-flows.md`.
- [confirmed] `docs/user/portal-vpn-user-guide-ru.md`.
- [confirmed] `C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md`.
- [confirmed] `C:/Users/kiwun/Documents/ai/POKROV-app/docs/product/client-product-contract.md`.
- [confirmed] `C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/cutover-readiness.md`.
- [confirmed] Supporting beta wave docs inspected: `docs/developer/work-orders/2026-04-beta-release/00-orchestrator-context.md` and work orders `WO-001`, `WO-002`, `WO-003`, `WO-005`, `WO-006`, `WO-007`, `WO-009`, `WO-010`.
- [confirmed] Supporting source/fact files inspected or searched: `shared/product-facts.json`, `shared/public-urls.json`, `shared/portal-config.ts`, `shared/copy.ts`, `marketing/src/**`, `webapp/src/**`, `portal_bot/**`, and non-generated source/doc paths under `C:/Users/kiwun/Documents/ai/POKROV-app`.

## Current state

- [confirmed] Minimum paid beta product promise is invite-limited `POKROV` for `Android + Windows`, not stable production and not public store cutover.
- [confirmed] Canonical product model is `consumer-first`, `app-first`, with `Try free -> real subscription source -> route-mode choice -> Connect` as the core first-run path.
- [confirmed] Trial is `5 days`; Telegram reward is `+10 days`; free monthly fallback is `5 GB / 30 days / 1 device` on `NL-free`; paid access is unlimited traffic with up to `5 devices` on enabled non-free nodes.
- [confirmed] Commerce story is key-first: hosted checkout sells activation keys, then app or cabinet redeems into managed premium.
- [confirmed] Public acquisition belongs to `marketing`; authenticated continuation, support, redeem, renewals, downloads, and admin belong to `webapp`.
- [confirmed] Telegram remains optional for first launch and normal use, and stays secondary for linking, bonus, recovery, support fallback, feedback, and bot-side purchase continuation.
- [confirmed] Public wording must avoid direct-meaning `VPN`; `POKROV VPN` is legacy compatibility only.
- [confirmed] `iOS` and `macOS` are readiness/signing/package-prep only in this wave.
- [confirmed] Android public release remains blocked by physical-device release-build localhost/control-surface audit and production signing.
- [confirmed] Windows public approval remains blocked by trusted signing, installer or publication path, hosting, and handoff evidence.
- [confirmed] Paid beta may be framed as gated/internal beta only if Android APK and/or unsigned Windows artifacts are labeled with the limitations required by `WO-007` and `WO-010`.
- [confirmed] Public source search found no direct public `VPN` wording in `shared`, `marketing/src`, or `webapp/src` outside guardrail code and official Telegram handles such as `@pokrov_vpn`.
- [confirmed] `shared/copy.ts` contains a direct-meaning `VPN` guardrail and allowlists only legacy `POKROV VPN` and Telegram-handle cases.

## Gaps against beta

- [confirmed] Canonical doc conflict: `docs/product/pokrov-growth-and-competitor-notes.md` says the content is the live `POKROV VPN` canon, which conflicts with the current `POKROV` naming rule even though the same file points back to `portal-vpn-product.md` as canonical.
- [confirmed] Canonical/code conflict: `portal_bot/bot.py` gift help and gift preset still describe `trial` as `7 days`, while all current product/client/fact docs lock the trial at `5 days`.
- [probable] Bot paywall copy still mixes the trial with `5 GB` and `1 device`, which reads closer to the free monthly cap than the canonical premium-grade 5-day trial; this needs owner review before paid beta public messaging.
- [confirmed] Legacy bot names `swazist_bot` and `portal_service_bot` appear in living docs only as disabled legacy names, but archived flat docs still contain older active-bot claims.
- [confirmed] `shared/portal-config.ts` includes `portal_service_bot` under `LEGACY_PUBLIC_MARKERS`, which is acceptable as a stale-copy detector rather than a public promise.
- [confirmed] `POKROV-app` docs and source still include technical `Hiddify` residues tied to inherited runtime artifacts, macOS helper naming, framework headers, and tests.
- [probable] Remaining `Hiddify` references in client runtime internals are compatibility/provenance residue, but any user-visible UI, release metadata, package identity, installer text, or public artifact name containing `Hiddify` would violate the beta scope.
- [confirmed] Archive docs contain old Hiddify, old bot, and older `POKROV VPN` direction; these are historical and should not drive beta copy.
- [unknown] Live production payment provider category acceptance and webhook verification were not confirmed in this R01 pass.
- [unknown] Live production deploy state, node readiness, and current-origin/brain-origin/RU-origin reachability were not confirmed in this R01 pass.
- [needs local run] Full repo/static/client gate status must be re-run for this beta wave; prior docs cite an older green local snapshot as necessary but not sufficient.
- [blocked by missing access] Physical Android release-build audit, production signing verification, and live payment verification require local devices, signing material, or controlled production access outside this read-only research task.

## P0 blockers

- [confirmed] Block beta if payment does not create exactly one entitlement, duplicate payment/webhook can extend twice, failed payment grants access, or manual payment reconciliation is unavailable.
- [confirmed] Block beta if users cannot redeem/activate paid access into the app-first account or managed premium cannot refresh from the canonical backend contract.
- [confirmed] Block beta if both Android and Windows beta connect paths are unusable.
- [confirmed] Block beta if admin cannot inspect or manage users, payments, access state, devices, tickets, and manual reconciliation.
- [confirmed] Block beta if cabinet support cannot create or continue real ticket threads, or if support requires users to paste raw configs/secrets.
- [confirmed] Block beta if public/cabinet/client UI exposes raw configs, personal subscription links, public IPs, raw host:port topology, protocol jargon as first-layer UX, or local-control surfaces.
- [confirmed] Block public Android/store claims until release-installed physical-device localhost/control-surface audit passes and trusted signing/handoff evidence exists.
- [confirmed] Block public Windows approval until trusted signing or an explicitly accepted unsigned beta warning path, public hosting, and handoff evidence exist.
- [confirmed] Block public copy that promises stable production, public store availability, live email continuation, public Apple launch, `Blocked only` routing, finished RU/DNS leak behavior, or direct `VPN` positioning.
- [confirmed] Fix or explicitly quarantine `portal_bot/bot.py` 7-day trial gift path before any beta communication or operator flow can present it as current.
- [confirmed] Fix or explicitly risk-accept the `POKROV VPN` wording conflict in `docs/product/pokrov-growth-and-competitor-notes.md` before treating all living product docs as internally consistent.

## P1 beta polish

- [confirmed] Ensure all beta user communications say `POKROV`, `0.x.x-beta`, invite-limited, Android/Windows only, and truthful artifact status.
- [confirmed] Make checkout/install/cabinet next steps explicit: pay, receive key or entitlement, redeem/open app, download gated beta artifact, contact support.
- [confirmed] Keep public download language gated: Android APK internal beta if audit/signing are missing; Windows unsigned beta if code signing is missing.
- [confirmed] Align bot, site, cabinet, and app copy around `5 days`, `+10 days`, key-first redeem, and app-first recovery order.
- [confirmed] Keep Telegram bonus copy tied to explicit claim after Telegram link and channel membership.
- [confirmed] Keep support language ticket-backed and best-effort, not fake live chat.
- [confirmed] Keep routing copy to `All except RU` and `Full tunnel`; keep `Blocked only` internal/deferred.
- [confirmed] Keep direct-meaning `VPN` guardrail tests in the beta validation pack.
- [probable] Treat technical `Hiddify` runtime names as P1 only when they are hidden from users and release metadata, but as P0 if they leak into visible packaging.

## P2 defer

- [confirmed] Public `iOS` and `macOS` launch.
- [confirmed] TestFlight, App Store, notarization, and Apple public distribution.
- [confirmed] Public `Blocked only` route mode.
- [confirmed] Public email signup/login/recovery as a default continuation path.
- [confirmed] Raw subscription-link sharing, profile editing, JSON editors, protocol transport selection, and manual import as primary onboarding.
- [confirmed] Third-party ad SDKs or third-party ad monetization.
- [confirmed] RF reserve/mini ingress promotion and broader RU ingress experiments unless separately owner-approved.
- [confirmed] Native store billing; this wave uses hosted checkout/key-first continuation.
- [confirmed] Full internal package rename away from inherited runtime identifiers unless they leak into user-facing or release-facing surfaces.

## Technical debt

- [confirmed] Living docs still use legacy path names such as `portal-vpn-product.md`; this is documented as acceptable until a separate rename wave.
- [confirmed] `portal_bot/bot.py` retains legacy Telegram/admin-era trial semantics, including `TRIAL_10GB_7` and `/gift trial` as 7 days.
- [confirmed] Client runtime still inherits `Hiddify` provenance and helper names in readiness-only or low-level runtime paths.
- [confirmed] Archive docs contain old bot names and Hiddify direction that can confuse agents if they skip the docs index and living-doc rules.
- [probable] The public beta wave needs one owner-visible matrix that distinguishes internal beta artifact, public download, store artifact, and readiness-only platform states.

## Security/privacy risks

- [confirmed] Android local-control/localhost exposure is a release gate and cannot be mitigated merely by app isolation features.
- [confirmed] User-facing diagnostics must not expose raw configs, keys, personal subscription links, public IP, host:port, or unnecessary topology.
- [confirmed] Payment/webhook evidence must not print secrets, tokens, card data, private webhook payloads, raw subscription links, full Telegram IDs, or personal payment data.
- [confirmed] Support flows must carry enough device/app context for diagnosis without asking users to paste secrets.
- [confirmed] Public UI must not imply signed/trusted artifacts when Android signing or Windows code signing is absent.
- [unknown] Live logs, screenshots, and payment records were not inspected in this R01 pass.

## Required implementation WOs

- [confirmed] `WO-001 Design System, Brand Assets, Visual Parity`: remove visible Hiddify residue, dev/demo labels, and forbidden `Premium VPN` subtitle usage.
- [confirmed] `WO-002 Marketing, Checkout, Install, Legal`: make public paid beta acquisition truthful and remove stale trial/bonus/pricing/artifact claims.
- [confirmed] `WO-003 User Cabinet`: make continuation, downloads, support, redeem, devices, and subscription state real and beta-labeled.
- [confirmed] `WO-005 Backend Contract Hardening`: prove trial, access state, node pools, managed profile delivery, route mode, device limits, and privacy-safe payloads.
- [confirmed] `WO-006 Payments, Keys, Telegram Bonus, Support/Feedback`: prove payment/key/bonus/support flows, idempotency, admin visibility, and safe logs.
- [confirmed] `WO-007 Android/Windows Beta Client`: prove Android/Windows beta artifacts, app-first onboarding, runtime connect path, safe diagnostics, and beta artifact warnings.
- [confirmed] `WO-009 Security, Privacy, Abuse, Compliance Audit`: audit auth, sessions, payment callbacks, admin RBAC, rate limits, local control surfaces, diagnostics, logs, attachments, and legal copy.
- [confirmed] `WO-010 Paid Beta Release Captain`: decide beta-ready, beta-ready with accepted limitations, or blocked after W01-W09 evidence exists.

## Validation commands

- [confirmed] Read-only anchor review was performed with `Get-Content` against the required docs.
- [confirmed] Stale-label/source scans were performed with PowerShell `Select-String` because `rg.exe` failed with `Access is denied` in this environment.
- [confirmed] Searched non-sensitive platform roots for `Hiddify`, `swazist_bot`, `portal_service_bot`, `7 days`, `7-day`, `14 days`, `30 days trial`, `POKROV VPN`, and direct `VPN`.
- [confirmed] Searched non-generated client source/doc roots for `Hiddify`, `POKROV VPN`, old bot names, old trial values, and old version labels.
- [needs local run] `python -m pytest tests/test_public_copy_guardrails.py -q`.
- [needs local run] `python -m pytest portal_bot/tests/test_app_first_api.py -q`.
- [needs local run] `python -m pytest tests/test_api_payments_callbacks.py tests/test_api_auth_and_tickets.py -q`.
- [needs local run] `cd marketing; npm.cmd run build`.
- [needs local run] `cd webapp; npm.cmd run build`.
- [needs local run] From `C:/Users/kiwun/Documents/ai/POKROV-app`: `powershell -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1`.
- [needs local run] From platform root: `python scripts/run_client_release_gate.py build --target windows` and `python scripts/run_client_release_gate.py build --target android-apk`.
- [blocked by missing access] Physical Android gate: `python scripts/android_localhost_audit.py` against a release-installed physical-device build with explicit serial.

## Evidence links

- [confirmed] Product canon: `docs/product/portal-vpn-product.md`.
- [confirmed] Platform architecture canon: `docs/architecture/system-overview.md`.
- [confirmed] App-first and bonus canon: `docs/architecture/app-first-and-bonus-flows.md`.
- [confirmed] User-facing RU canon: `docs/user/portal-vpn-user-guide-ru.md`.
- [confirmed] Client canon: `C:/Users/kiwun/Documents/ai/POKROV-app/docs/product/client-product-contract.md`.
- [confirmed] Client release gate reality: `C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/cutover-readiness.md`.
- [confirmed] Shared facts: `shared/product-facts.json`.
- [confirmed] Shared public URLs: `shared/public-urls.json`.
- [confirmed] Copy guardrail implementation: `shared/copy.ts`.
- [confirmed] Stale product-support doc conflict: `docs/product/pokrov-growth-and-competitor-notes.md`.
- [confirmed] Stale bot trial evidence: `portal_bot/bot.py` lines around `/gift [tg_id] trial` and `gift_presets`.
- [confirmed] Beta wave context and decision model: `docs/developer/work-orders/2026-04-beta-release/00-orchestrator-context.md` and `WO-010-paid-beta-release-captain.md`.
