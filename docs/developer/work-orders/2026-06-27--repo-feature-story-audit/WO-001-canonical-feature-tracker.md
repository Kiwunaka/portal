# WO-001 Canonical Feature Tracker

Last updated: 2026-06-27

## Status

- WO status: `executing`
- WO class: `mixed-discovery-with-platform-doc-output`
- Primary lane: `portal/master`
- Referenced client lane: `POKROV-app/main`

## Goal

Create and maintain one canonical table for POKROV feature/user-story status across backend/API, Telegram bots, WebApp/admin, marketing, and the active POKROV client app. The table must record expected behavior from code/canon, current test status, defects, fixes, retest status, and next action.

## Write Scope

- `docs/developer/pokrov-canonical-feature-tracker.md`
- `docs/developer/pokrov-canonical-feature-tracker.csv`
- `docs/developer/pokrov-entrypoint-inventory.csv`
- `docs/developer/pokrov-entrypoint-story-coverage.csv`
- `docs/developer/pokrov-entrypoint-story-coverage.md`
- `docs/developer/pokrov-backend-route-coverage.csv`
- `docs/developer/pokrov-script-workflow-coverage.csv`
- `docs/developer/pokrov-code-function-inventory.csv`
- `docs/developer/pokrov-code-function-inventory.md`
- `docs/developer/pokrov-symbol-coverage-audit.csv`
- `docs/developer/pokrov-symbol-coverage-audit.md`
- `docs/developer/pokrov-private-helper-coverage.csv`
- `docs/developer/pokrov-private-helper-coverage.md`
- `docs/developer/pokrov-coverage-policy-decision-guide.md`
- `docs/developer/pokrov-story-test-evidence-audit.csv`
- `docs/developer/pokrov-story-test-evidence-audit.md`
- `docs/developer/pokrov-defect-fix-retest-ledger.csv`
- `docs/developer/pokrov-defect-fix-retest-ledger.md`
- `docs/developer/pokrov-owner-gated-scenarios.csv`
- `docs/developer/pokrov-owner-gated-results.csv`
- `docs/developer/pokrov-owner-gated-scenarios.md`
- `docs/developer/pokrov-owner-gated-execution-guide.md`
- `docs/developer/pokrov-owner-answer-sheet.md`
- `docs/developer/pokrov-open-questions.csv`
- `docs/developer/pokrov-open-questions.md`
- `docs/audit-artifacts/current-origin-public-beta-preflight-2026-06-27.json`
- `docs/audit-artifacts/current-origin-runtime-app-download-smoke-2026-06-28.md`
- `docs/audit-artifacts/current-origin-public-beta-post-deploy-probe-2026-06-27.json`
- `docs/audit-artifacts/current-origin-public-host-reachability-2026-06-28.json`
- `docs/audit-artifacts/brain-runtime-app-download-smoke-2026-06-28.json`
- `docs/audit-artifacts/brain-deploy-state-2026-06-28.md`
- `docs/audit-artifacts/telegram-desktop-tooling-blocker-2026-06-28.md`
- `docs/README.md`
- `docs/developer/repository-map.md`
- `docs/developer/developer-guide.md`
- `scripts/manifest.yaml`
- `scripts/generate_code_function_inventory.py`
- `scripts/generate_private_helper_coverage.py`
- `scripts/generate_defect_fix_retest_ledger.py`
- `scripts/audit_story_test_evidence.py`
- `tests/test_code_function_inventory.py`
- `tests/test_email_relay_app.py`
- `tests/test_story_test_evidence_audit.py`
- `tests/test_marketing_story_contracts.py`
- `tests/test_telegram_story_contracts.py`
- `webapp/src/app/qa-overlay.tsx`
- `webapp/e2e/qa-overlay.spec.ts`
- `docs/developer/work-orders/2026-06-27--repo-feature-story-audit/**`
- `C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/pubspec.yaml`
- `C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/pubspec.lock`
- `C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/design_system_contract_test.dart`
- `C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart`

Client source is otherwise read as source evidence; this WO also adds focused POKROV-app package contract tests where source-symbol review showed public client API hardening gaps.

## Source Evidence Read

- `docs/README.md`
- `docs/product/portal-vpn-product.md`
- `docs/architecture/system-overview.md`
- `docs/architecture/app-first-and-bonus-flows.md`
- `docs/operations/deployment-and-access.md`
- `docs/operations/monitoring-and-visibility.md`
- `docs/developer/developer-guide.md`
- `docs/developer/repository-map.md`
- `webapp/README.md`
- `docs/operations/publishing-and-signing-guide.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/cutover-readiness.md`
- existing XLSX trackers for Telegram bots, WebApp/admin, marketing, and POKROV-app client
- `scripts/manifest.yaml`
- active root source under `portal_bot/`, `scripts/`, `shared/`, `webapp/`, and `marketing/`
- active client source under `C:/Users/kiwun/Documents/ai/POKROV-app/apps`, `packages`, `lib`, and `scripts`

## Current Output

- Canonical CSV rows: `525`
- Canonical story status rows: `524` `Retest passed`, `1` `Manual owner test`; empty canonical status/story contract fields: `0`
- Entrypoint inventory rows: `514`
- Imported verified story rows: `237`
- Backend API route-family rows: `165`
- Backend route direct test-reference mappings: `165/165`; scenario gaps: `0`
- Scripts/Ops workflow rows: `123`
- Script workflow direct test-reference mappings: `123/123`; scenario gaps: `0`
- Low-level code function inventory rows: `4827`; parser errors: `0`; token-level test-reference hints: `1580`
- Low-level entrypoint hints: `185` FastAPI route handlers, `1` FastAPI middleware, `171` Telegram handlers, `125` script CLI mains, `101` framework overrides, `1` Next.js page component; `portal_bot/bot.py` FastAPI mislabels: `0`
- Source symbol coverage audit rows: `4827`; expected-behavior notes: `4827`; entrypoint mapping gaps: `0`; story source refs: `3201`; story dependency refs: `707`; module test refs: `77`; direct token test refs: `249`; private inventory-only rows: `17`; private inventory public/entrypoint leakage: `0`; client platform manual-gate rows: `77`; client desktop tray manual-gate rows: `3`; platform/tray manual-gate rows with `manual_gate_refs`: `80`; client package public-API review rows: `0`; script CLI manifest review rows: `0`; script CLI deprecated rows: `2`; public symbol review rows: `0`
- Private helper coverage matrix rows: `17`; Q-001 owner-decision rows: `17`; high risk rows: `0`; medium risk rows: `2`; low risk rows: `15`
- Story evidence audit rows: `525`; direct file refs: `524`; imported-pass rows without direct file refs: `0`; manual owner gates: `1`; stale refs: `0`
- Story retest proof rows: `524` `direct_test_ref_passed`; `1` `manual_owner_gate_open`; weak/stale/imported/textual proof buckets: `0`
- Defect/fix/retest ledger rows: `18`; `closed_retested`: `16`; `closed_retested_no_product_change`: `2`; weak/open closure rows: `0`
- Owner-gated scenario matrix rows: `8`; owner-gated result ledger rows: `8`; required owner-gated scenarios still open: `2`; unresolved source-doc refs: `0`; Telegram WebApp gate is `BLOCKED_BY_ACCESS` because no callable desktop-control tool is exposed in this session
- Current-origin partial live-deploy/payment evidence recorded at `docs/audit-artifacts/current-origin-public-beta-preflight-2026-06-27.json`, `docs/audit-artifacts/current-origin-runtime-app-download-smoke-2026-06-28.md`, `docs/audit-artifacts/current-origin-public-beta-post-deploy-probe-2026-06-27.json`, and `docs/audit-artifacts/current-origin-public-host-reachability-2026-06-28.json`: public marketing, cabinet, API health, and checkout returned `200`, public email runtime and provider catalog checks passed, and current-origin `/api/client/apps` remains blocked without Telegram initData. Brain-origin signed runtime app-download smoke passed at `docs/audit-artifacts/brain-runtime-app-download-smoke-2026-06-28.json`; brain deploy-state passed at `docs/audit-artifacts/brain-deploy-state-2026-06-28.md`; real Telegram/current-origin authenticated app-session evidence, owner deploy approval, live email/invoice probes, and paid maturity evidence remain owner/operator gated
- Open questions ledger rows: `4`; blocking full-goal questions: `1`
- Coverage policy decision guide and private-helper coverage matrix exist and are linked from Q-001, the canonical tracker, developer navigation, and the open-questions/private-helper guards; Q-001 is answered as `ACCEPT_STORY_AND_SYMBOL_TIERS` on 2026-06-28
- Owner-gated execution guide exists and is linked from Q-004, the owner-gated summary, developer navigation, and the canonical tracker; every current owner gate ID and required result-ledger field is present in the guide
- Entrypoint story coverage rows: `514`; direct route refs: `165`; direct script refs: `123`; direct story refs: `226`; review gaps: `0`
- Canonical source-evidence file refs checked: `1089`; missing source refs: `0`
- Canonical line-number source refs checked: `352`; out-of-bounds line refs: `0`
- Canonical source-tracker refs checked: `525`; unresolved source-tracker refs: `0`; generated labels are backed by `portal_bot/api.py` and `scripts/manifest.yaml`
- Developer navigation docs and work-orders README link the canonical tracker, evidence audit, entrypoint map, function inventory, symbol coverage audit, owner-gated matrix/result ledger, open-questions ledger, completion audit work-order artifacts, and the active feature-story audit wave; wave-local imported coverage counts match canonical tracker subsystem counts; missing navigation artifact refs: `0`
- Generated artifact reproducibility guards now regenerate story evidence, entrypoint-story coverage, defect/fix/retest ledger, low-level code inventory, source-symbol coverage, and private-helper coverage into temp files and compare them byte-for-byte against the canonical files
- Markdown summary-count guards now compare the inventory, symbol coverage, private-helper coverage, story evidence, entrypoint coverage, wave index imported coverage, work-order current-output summary counts, and key inventory/symbol prose claims against their canonical CSV files
- Canonical tracker Markdown summary guard now compares the main tracker status, subsystem, backend route, script workflow, low-level inventory, symbol coverage, private-helper coverage, story evidence, entrypoint inventory, and entrypoint coverage counts against canonical CSV artifacts
- Backend focused verification: `158 passed, 12 warnings` on 2026-06-27
- Backend route-gap verification: `4 passed` on 2026-06-27
- Broad retest proof run IDs recorded in the canonical tracker: `ROOT-PYTEST-011`, `WEBAPP-FULL-002`, `MARKETING-RETEST-002`, `CLIENT-TEST-003`, and latest focused audit guard `COMPLETION-DISCREPANCY-EVIDENCE-001`
- Ops/script focused verification: `314 passed, 6 warnings` on 2026-06-27
- WebApp/admin verification: `npm.cmd run build`, `27/27` cabinet e2e, `19/19` admin e2e, `46/46` full e2e pack, `13/13` additional auth/email e2e, and `10/10` frontend copy guard tests passed on 2026-06-27; latest current-worktree refresh also passed `npm.cmd run build` and `npm.cmd run test:e2e` with `46/46`
- Marketing verification: `npm.cmd run build`, `npm.cmd run check:seo`, `npm.cmd run check:responsive`, and release/copy/story guard pytest tests passed on 2026-06-27; latest current-worktree refresh passed `23/23` pytest tests
- Telegram bot/support verification: `82` pytest tests plus `2` subtests passed; static app/bot parity smoke reported `7` pass, `0` fail, and `2` manual owner tests on 2026-06-27
- Active POKROV-app client verification: seed-layout, validate-seed, and `scripts/run-tests.ps1` passed in `C:/Users/kiwun/Documents/ai/POKROV-app` on 2026-06-27
- Full root retest after fixes: `650` pytest tests passed with `62` warnings and `2` subtests on 2026-06-27
- Full root retest after function-inventory and script-manifest sync: `712` pytest tests passed with `62` warnings and `2` subtests on 2026-06-27
- Full root retest after story evidence audit and function-inventory scope fix: `713` pytest tests passed with `62` warnings and `2` subtests on 2026-06-27
- Focused native inventory/evidence classifier retest: `2` pytest tests passed; inventory regenerated with `4320` symbols; story evidence audit regenerated with `331` direct file refs, `169` imported-pass rows, `1` manual owner gate, and `0` stale refs on 2026-06-27
- Focused direct story-evidence retest: `11` pytest tests passed; story evidence audit regenerated with `500` direct file refs, `0` imported-pass rows, `1` manual owner gate, and `0` stale refs on 2026-06-27
- Full root retest after direct story-evidence mapping: `720` pytest tests passed with `62` warnings and `2` subtests on 2026-06-27
- Focused entrypoint-hint retest: `1` pytest test passed; inventory regenerated with `4320` symbols, `170` Telegram handler hints, `174` FastAPI route-handler hints, and `0` `portal_bot/bot.py` FastAPI mislabels on 2026-06-27
- Full root retest after entrypoint-hint classifier fix: `720` pytest tests passed with `62` warnings and `2` subtests on 2026-06-27
- Focused entrypoint-story-coverage retest: `12` pytest tests passed; story evidence audit regenerated with `500` direct file refs, `1` manual owner gate, and `0` stale refs; entrypoint coverage regenerated with `490` direct mappings and `0` review gaps; low-level source inventory regenerated with `4334` symbols on 2026-06-27
- Full root retest after entrypoint-story coverage bridge: `721` pytest tests passed with `62` warnings and `2` subtests on 2026-06-27
- Focused source-evidence guard retest: `13` pytest tests passed; story evidence audit regenerated with `500` direct file refs, `1` manual owner gate, and `0` stale refs; entrypoint coverage stayed at `490` direct mappings and `0` review gaps; canonical source-evidence guard reports `0` missing source refs on 2026-06-27
- Full root retest after source-evidence guard: `722` pytest tests passed with `62` warnings and `2` subtests on 2026-06-27
- Focused symbol coverage retest: `15` pytest tests passed; low-level source inventory regenerated with `4346` symbols; symbol coverage audit regenerated with `4346` rows, `0` parser errors, and `0` entrypoint mapping gaps on 2026-06-27
- Full root retest after source symbol coverage audit: `724` pytest tests passed with `62` warnings and `2` subtests on 2026-06-27
- Focused script manifest status retest: `113` pytest tests passed; script workflow coverage regenerated with `119` active workflows; symbol coverage has `0` script manifest review rows and `2` deprecated FreeKassa CLI rows on 2026-06-27
- Focused module/dependency symbol evidence retest: `2` pytest tests passed; symbol coverage regenerated with `595` `story_dependency_source_file` rows, `83` `module_test_ref` rows, and `76` remaining public-symbol review rows on 2026-06-27
- Focused client platform symbol retest: `2` pytest tests passed; symbol coverage regenerated with `112` `client_platform_host_manual_gate` rows and `183` remaining public-symbol review rows on 2026-06-27
- Focused final symbol-triage retest: focused pytest pack `13` passed; WebApp build passed; marketing build passed; symbol coverage regenerated with `4362` rows, `0` `public_symbol_review` rows, `621` `story_dependency_source_file` rows, `109` `module_test_ref` rows, `77` client-platform manual-gate rows, `3` client desktop tray manual-gate rows, and `5` client package public-API review rows on 2026-06-27
- Focused client package API contract retest: Flutter `design_system_contract_test.dart` passed with `19` tests; focused root guard pack passed with `13` pytest tests; symbol coverage regenerated with `4362` rows, `172` direct-token refs, `108` `module_test_ref` rows, and `0` client package public-API review rows on 2026-06-27
- Full local POKROV-app client lane after app-shell public API contract coverage: `scripts/run-tests.ps1` passed on 2026-06-27
- Full root retest after client package API contract coverage: `738` pytest tests passed with `62` warnings and `2` subtests on 2026-06-27
- Current-worktree full local retest after tracker regeneration and broad frontend/client verification: root pytest passed with `765` tests, `62` warnings, and `2` subtests; WebApp build/full e2e, marketing build/SEO/responsive/text-story guards, POKROV-app `scripts/run-tests.ps1`, and the touched app-shell Flutter test files passed on 2026-06-27
- Focused manual-gate note guard: `3` story evidence audit tests passed after adding exact owner/current evidence requirements to `CLIENT_APP-US-067` on 2026-06-27
- Focused tracker status hygiene guard: targeted status/latest-result tests passed, full story evidence audit test file passed with `4` tests, focused tracker/inventory/manifest pack passed with `10` tests, and regenerated story evidence audit stayed at `520` direct file refs, `1` manual owner gate, and `0` stale refs on 2026-06-27
- Focused tracker story-contract/guardrail/code-evidence guard: targeted required-field, priority-only guardrail, and resolvable-code-evidence tests passed, full story evidence audit test file passed with `6` tests, focused tracker/inventory/manifest pack passed with `12` tests, and regenerated story evidence audit stayed at `520` direct file refs, `1` manual owner gate, and `0` missing refs on 2026-06-27
- Completion audit added at `docs/developer/work-orders/2026-06-27--repo-feature-story-audit/COMPLETION-AUDIT.md`; it maps the original objective to current evidence and keeps owner-only gaps separate from local completion claims.
- Completion audit count guard passed; focused tracker/inventory/manifest pack passed with `13` tests and regenerated story evidence audit stayed at `520` direct file refs, `1` manual owner gate, and `0` missing refs on 2026-06-27.
- Full root retest after script manifest status pass: `737` pytest tests passed with `62` warnings and `2` subtests on 2026-06-27
- Marketing/deploy post-fix retest: marketing build, SEO, responsive, and `25/25` deploy/UI/copy pytest tests passed on 2026-06-27
- Focused source-tracker provenance guard: full story evidence audit test file passed with `8` tests, focused tracker/inventory/manifest pack passed with `14` tests, and regenerated story evidence audit stayed at `520` direct file refs, `1` manual owner gate, `0` missing refs, and `0` unresolved source-tracker refs on 2026-06-27
- Focused owner-gated scenario matrix/result guard: `test_owner_gated_scenarios_are_explicit_and_resolvable` passed; the matrix has `8` source-linked owner/operator scenarios, `8` matching result rows, and `7` required still-open owner-gated scenarios for `CLIENT_APP-US-067`; every current manual canonical row is linked to the matrix on 2026-06-27
- Focused private-inventory tier guard: `test_generated_private_inventory_tier_contains_only_private_non_entrypoints` passed; current `private_inventory_only` rows have `0` public/entrypoint leakage on 2026-06-27
- Focused open-questions ledger guard: `test_open_questions_ledger_tracks_owner_blockers` passed; `pokrov-open-questions.csv` has `3` open questions, `1` answered question, and `1` blocking full-goal question after the 2026-06-28 owner answer
- Focused developer navigation guard: `test_canonical_audit_artifacts_are_linked_from_developer_navigation` passed; focused tracker/inventory/manifest pack passed with `18` tests after linking the canonical audit artifacts from `docs/README.md`, `docs/developer/repository-map.md`, and `docs/developer/developer-guide.md` on 2026-06-27
- Focused generated-artifact reproducibility guards passed: `test_generated_story_evidence_artifacts_match_canonical_files` regenerated story evidence and entrypoint-story coverage into temp files and matched the canonical CSVs; `test_generated_defect_fix_retest_ledger_matches_canonical_files` regenerated the defect/fix/retest ledger into temp files and matched the canonical CSV/Markdown; `test_generated_code_inventory_artifacts_match_canonical_files` regenerated low-level code inventory and symbol coverage into temp files and matched the canonical CSVs on 2026-06-27
- Focused tracker/inventory/manifest pack after generated-artifact reproducibility guards passed with `20` tests on 2026-06-27
- Focused line-number source-ref guard passed: `test_canonical_line_number_source_refs_are_in_bounds` checked `352` `path:line` refs across canonical tracker/owner/question ledgers and found `0` out-of-bounds refs on 2026-06-27
- Focused tracker/inventory/manifest pack after line-number source-ref guard and inventory regeneration passed with `21` tests on 2026-06-27
- Focused Markdown summary-count guards passed: inventory/symbol summary tests and story/entrypoint summary tests passed with `4` targeted tests on 2026-06-27
- Focused tracker/inventory/manifest pack after Markdown summary-count guards and inventory regeneration passed with `25` tests on 2026-06-27
- Focused canonical tracker summary guard passed: `test_canonical_tracker_markdown_summary_matches_csv_artifacts` passed on 2026-06-27
- Focused tracker/inventory/manifest pack after canonical tracker summary guard and inventory regeneration passed with `26` tests on 2026-06-27
- Focused owner-gated execution guide guard passed: `test_owner_gated_scenarios_are_explicit_and_resolvable` passed after adding `pokrov-owner-gated-execution-guide.md` on 2026-06-27
- Focused tracker/inventory/manifest pack after owner-gated execution guide passed with `26` tests on 2026-06-27
- Focused coverage-policy decision guide guard passed: `test_open_questions_ledger_tracks_owner_blockers` passed after adding `pokrov-coverage-policy-decision-guide.md` on 2026-06-27
- Focused tracker/inventory/manifest pack after coverage-policy decision guide and inventory regeneration passed with `26` tests on 2026-06-27
- Focused private-helper coverage matrix guard passed: `3` targeted tests passed after adding `pokrov-private-helper-coverage.csv` / `.md` and `scripts/generate_private_helper_coverage.py` on 2026-06-27
- Focused tracker/inventory/manifest pack after private-helper coverage matrix and active script mapping passed with `29` tests on 2026-06-27
- Focused canonical audit Markdown/CSV mojibake guards passed after cleaning the active tracker finding text; focused tracker/inventory/manifest pack passed with `31` tests on 2026-06-27
- Focused client first-launch storage retest passed: `flutter test test/design_system_contract_test.dart --reporter compact --name "file first-launch store"` passed with `2` selected tests after replacing a hanging method-channel mock with a `PathProviderPlatform` fake on 2026-06-27
- Private-helper matrix after first-launch storage coverage regenerated with `22` rows, `0` high-risk rows, `0` medium-risk rows, and `22` low-risk rows on 2026-06-27
- Focused client shared shell widget retest passed: `flutter test test/pokrov_seed_app_test.dart --reporter compact --name "renders premium shell v2|home uses raster brand mark|rules show selected-apps editor"` passed with `3` selected tests after linking shared shell widget private helpers to public UI scenarios on 2026-06-27
- Private-helper matrix after shared shell widget coverage regenerated with `10` rows, `0` high-risk rows, `0` medium-risk rows, and `10` low-risk rows on 2026-06-27
- Focused client sidebar/info-sheet retests passed: `flutter test test/design_system_contract_test.dart --reporter compact --name "desktop sidebar preserves"` passed with `1` selected test, and `flutter test test/pokrov_seed_app_test.dart --reporter compact --name "home status opens connection details|profile uses grouped MVP account sections"` passed with `2` selected tests on 2026-06-27
- Private-helper matrix after sidebar/info-sheet coverage regenerated with `5` rows, `0` high-risk rows, `0` medium-risk rows, and `5` low-risk rows on 2026-06-27
- Focused final app-shell implementation helper retest passed: `flutter test test/pokrov_seed_app_test.dart --reporter compact --name "renders premium shell v2|profile surfaces devices, notifications and subscription detail|P5 Windows shortcuts navigate tabs"` passed with `3` selected tests on 2026-06-27
- Private-helper matrix after final app-shell implementation helper coverage regenerated with `0` rows on 2026-06-27
- Full touched client test files passed after private-helper zero: `flutter test test/design_system_contract_test.dart --reporter compact` passed with `19` tests, and `flutter test test/pokrov_seed_app_test.dart --reporter compact` passed with `69` tests on 2026-06-27
- Current-origin public-beta preflight recorded `classification=BLOCKED_BY_ACCESS` on 2026-06-27; unauthenticated runtime app smoke returned `/api/health -> 200` and then stopped because real Telegram init data was not supplied. This is partial live-deploy evidence only and does not close `CLIENT_APP-US-067`.
- Current-origin dry post-deploy probe recorded `classification=BLOCKED_BY_ACCESS` on 2026-06-27; public email runtime config and provider catalog passed, while live email delivery, Lava.top invoice creation, and paid evidence remain blocked without owner env/evidence. This is partial payment/live-deploy evidence only and does not close `CLIENT_APP-US-067`.
- Current-origin public host reachability recorded `200` for `https://pokrov.space/`, `https://app.pokrov.space/`, `https://api.pokrov.space/api/health`, and `https://pay.pokrov.space/checkout/` on 2026-06-27. This is partial live-deploy evidence only and does not test authenticated app sessions, `connect.pokrov.space` token behavior, brain-origin, or RU-origin.

## Acceptance Criteria

- One canonical table exists in a diffable format.
- Existing subsystem trackers are imported without overwriting the XLSX sources.
- Backend API route decorators are inventoried as route-family user stories and mapped to direct scenario-test references.
- Active `scripts/manifest.yaml` workflows are inventoried as operator user stories and unmapped scripts are visible as scenario-test gaps.
- Open questions are recorded instead of blocking progress.
- Next test/fix/retest queue is explicit.

## Validation Plan

- Static read of generated Markdown and CSV headers.
- Import CSV with PowerShell to confirm it parses.
- Check generated status counts against source workbooks.
- Focused backend/API suite passed after fixing test harness panel isolation.
- WebApp/admin browser stories passed through Playwright fallback because the Browser plugin is not available in this toolset.
- Additional WebApp auth/email specs were run explicitly because `npm.cmd run test:e2e` currently covers only `admin-gate` and `cabinet-flow`.
- Marketing static build, SEO checks, responsive browser smoke, and release/copy guardrails passed.
- Bot/support local behavior and app/bot/cabinet static parity passed; live Telegram account checks remain `MANUAL_OWNER_TEST`.
- Active client local scaffold, Flutter, and Android Gradle unit lanes passed; physical device install/connect, signing, store, and live account flows remain manual gates.
- First full root pytest run found `13` failures; fixes were applied and the final full root pytest pass is green.
- Post-inventory full root pytest rerun passed with `712` tests after the low-level function inventory generator and `app_bot_parity_smoke.py` manifest registration.
- Post-story-evidence full root pytest rerun passed with `713` tests after the evidence auditor, manifest registration, and function-inventory skip-rule fix.
- Post-direct-story-evidence full root pytest rerun passed with `720` tests after the Telegram and marketing story-contract tests plus direct evidence mappings.
- Post-entrypoint-classifier full root pytest rerun passed with `720` tests after the Telegram/FastAPI disambiguation fix.
- Post-entrypoint-story-coverage full root pytest rerun passed with `721` tests after the coverage bridge, stale client path fixes, and expanded Telegram story-contract markers.
- Post-source-evidence-guard full root pytest rerun passed with `722` tests after adding the canonical source-ref guard.
- Focused symbol coverage pytest passed after adding `pokrov-symbol-coverage-audit.csv` and email relay route tests.
- Post-symbol-coverage full root pytest rerun passed with `724` tests after adding the literal source-symbol audit and email relay route coverage.
- Post-script-manifest-status full root pytest rerun passed with `737` tests after adding 20 active script workflows, deprecating 2 legacy FreeKassa CLIs, adding manifest status guards, and hardening remote/postgres operator scripts.
- Post-client-package-API full root pytest rerun passed with `738` tests after adding app-shell package contract coverage and regenerating the source-symbol audit.
- Post-client-package-API full local POKROV-app lane passed through `scripts/run-tests.ps1`; physical device, signing, store, live Telegram, and provider/RU checks remain separate owner gates.
- Current-worktree goal-continuation refresh passed with `765` root pytest tests, WebApp production build plus `46/46` full e2e tests, marketing build/SEO/responsive plus `23/23` text/story guard tests, POKROV-app `scripts/run-tests.ps1`, and touched app-shell Flutter files with `19` and `69` tests; owner/device/provider/RU checks remain separate gates.
- Canonical tracker hygiene is guarded by `tests/test_story_test_evidence_audit.py`, including normalized statuses, non-empty status/story contract fields, manual owner notes, client app canon guardrails, no priority-only guardrails, resolvable `code_evidence` refs, and no stale fail/issue text in `latest_result` for `Retest passed` rows.
- Completion status must be audited through `COMPLETION-AUDIT.md` before any future goal-complete claim.
- `tests/test_story_test_evidence_audit.py::test_completion_audit_tracks_current_story_counts` keeps the completion audit synchronized with canonical tracker and story evidence counts.
- `tests/test_story_test_evidence_audit.py::test_canonical_audit_artifacts_are_linked_from_developer_navigation` keeps the canonical tracker/audit sidecars linked from developer navigation docs.
- `tests/test_story_test_evidence_audit.py::test_canonical_line_number_source_refs_are_in_bounds` keeps explicit `path:line` evidence refs inside current file bounds.
- `tests/test_story_test_evidence_audit.py::test_generated_story_evidence_artifacts_match_canonical_files`, `tests/test_story_test_evidence_audit.py::test_generated_defect_fix_retest_ledger_matches_canonical_files`, and `tests/test_code_function_inventory.py::test_generated_code_inventory_artifacts_match_canonical_files` keep generated canonical CSV/Markdown artifacts reproducible from current source and tracker inputs.
- `tests/test_story_test_evidence_audit.py::test_story_evidence_markdown_summary_matches_csv`, `tests/test_story_test_evidence_audit.py::test_defect_fix_retest_markdown_summary_matches_csv`, `tests/test_story_test_evidence_audit.py::test_entrypoint_coverage_markdown_summary_matches_csv`, `tests/test_code_function_inventory.py::test_code_inventory_markdown_summary_matches_csv`, `tests/test_code_function_inventory.py::test_symbol_coverage_markdown_summary_matches_csv`, and `tests/test_code_function_inventory.py::test_private_helper_coverage_markdown_summary_matches_csv` keep human-readable summary counts synchronized with canonical CSV artifacts.
- `tests/test_story_test_evidence_audit.py::test_canonical_tracker_markdown_summary_matches_csv_artifacts` keeps the main canonical tracker summary synchronized with the tracker and sidecar CSV artifacts.
- `tests/test_story_test_evidence_audit.py::test_canonical_audit_markdown_has_no_mojibake_markers` and `tests/test_story_test_evidence_audit.py::test_canonical_audit_csv_has_no_mojibake_markers` keep active canonical audit Markdown/CSV artifacts free of common UTF-8/CP1251 mojibake regressions.
- New backend routes must be added to the canonical CSV and either mapped to a direct scenario-test reference or left as `Needs scenario test` until a focused test is added.
- Active script/operator workflow rows are generated from `scripts/manifest.yaml`; direct test mappings are taken from `tests/` and `portal_bot/tests/`.
- Low-level source symbols are generated by `scripts/generate_code_function_inventory.py`; `test_ref_count` is a token-level triage hint, not dedicated private-helper behavior proof.
- Source symbol coverage tiers are generated by `scripts/generate_code_function_inventory.py`; `entrypoint_needs_mapping_review` must stay at `0`, `story_dependency_source_file` maps Python and TypeScript/TSX dependencies reachable from story-mapped source including symbol-free barrel/re-export modules, `module_test_ref` separates module-level automated evidence from direct symbol assertions, client platform/desktop tiers separate manual runtime verification scope and carry `manual_gate_refs`, Next/Telegram/QA/operator tiers separate framework/tooling surfaces, `client_package_public_api_review` is now `0`, generic `public_symbol_review` is now `0`, and `script_cli_manifest_review` is now `0` because every script CLI has an active/deprecated/archive/denylist status.
- Story evidence strength is generated by `scripts/audit_story_test_evidence.py`; imported workbook pass evidence is kept distinct from direct automated test-file mappings.
- Entrypoint story coverage is generated by `scripts/audit_story_test_evidence.py`; route/script/story evidence is kept distinct from token-level helper-name references.
- Native client host source under Kotlin, Swift, and C/C++ is included in the low-level source inventory; generated/build/test trees remain excluded as source rows.
- Aiogram bot handlers and FastAPI route handlers are disambiguated in the low-level source inventory; `router.*` alone is not treated as FastAPI.
- POKROV-app code-evidence paths in canonical rows now use the active `packages/app_shell/lib/src/features/...` layout for feature files.
- Canonical `code_evidence` file refs are guarded by `tests/test_story_test_evidence_audit.py::test_canonical_code_evidence_source_refs_exist`.
- Email relay `/healthz` and fail-closed `/email/deliver` secret behavior are covered by `tests/test_email_relay_app.py`.
- The focused ops/script packs passed for all 121 active scripts; 0 active scripts remain explicit `Needs scenario test` rows, and future unclassified CLI `main()` files fail `check_script_manifest.py`.

## Findings

| Finding ID | Status | Type | Summary | Fix | Verification |
| --- | --- | --- | --- | --- | --- |
| API-TEST-001 | `closed` | test harness isolation | `portal_bot/tests/test_app_first_api.py` and `tests/test_network_rollout_api.py` could call the real `ControlPanel` during unit tests and time out on start-trial paths. | Installed default fake panel classes in each `_load_api()` helper. | `python -m pytest portal_bot/tests/test_app_first_api.py tests/test_portal_api.py tests/test_api_auth_and_tickets.py tests/test_smart_connect_api.py tests/test_network_rollout_api.py tests/test_api_payments_callbacks.py tests/test_lavatop_payment_providers.py tests/test_admin_payments_api.py -q --basetemp .tmp/pytest-backend-focused`: `158 passed, 12 warnings`. |
| WEBAPP-VERIFY-001 | `closed` | verification gap | The named `full` WebApp e2e suite does not include `oidc-fallback`, `settings-email-link`, or `telegram-login-refresh`, even though those are active user-story specs. | Ran the three omitted specs explicitly on a separate static-export Playwright port and recorded the separate run in the canonical tracker. | `npx.cmd playwright test e2e/oidc-fallback.spec.ts e2e/settings-email-link.spec.ts e2e/telegram-login-refresh.spec.ts` with `E2E_PORT=3104`, `PLAYWRIGHT_FRESH_SERVER=1`, `PLAYWRIGHT_SERVER_MODE=start`: `13 passed`. |
| API-TEST-002 | `closed` | test harness isolation | API lifecycle smoke leaked fake `ControlPanel` classes into later tests, causing bot wheel tests to import a fake panel without `update_client_traffic`. | Added fake `update_client_traffic` plus cleanup that restores or removes patched panel classes after the lifecycle smoke. | `python -m pytest -q --basetemp .tmp/pytest-full`: `650 passed, 62 warnings, 2 subtests passed`. |
| OPS-DEPLOY-001 | `closed` | static deploy safety | Static site deploy lacked the tested `--plan-only` dry run and validated old FreeKassa static files as required payload. | Restored local validation helpers, remote payload checks, post-deploy smoke commands, and `--plan-only`; validation now rejects legacy `fk-verify.html` and `fk-payment-theme.css`. | `tests/test_remote_deploy_brain_static_sites.py` passed as part of `ROOT-PYTEST-001` and `MARKETING-RETEST-001`. |
| NODE-CONTRACT-001 | `closed` | runtime/test compatibility | Existing helper constructors failed after `NodeRuntime` gained observability fields. | Added safe defaults for `cpu_percent`, `last_ok_at`, and `last_probe_at`. | `ROOT-PYTEST-001` passed. |
| CLIENT-CANON-001 | `closed` | canon drift in tests | Root tests still expected pre-beta client release strings that conflict with the current outside-store beta GO truth. | Updated tests to current Android/Windows outside-store beta wording and parsed release handoff seed JSON structurally. | `ROOT-PYTEST-001` passed. |
| MKT-UX-001 | `closed` | checkout copy precision | Checkout email validation referred to only `ключ`, which is less clear than the actual `ключ доступа` user flow. | Changed visible checkout copy to `ключа доступа`, added it to the UI smoke contract, and later cleaned the active canonical tracker finding text after detecting mojibake in the audit prose. | `npm.cmd run build`, `npm.cmd run check:seo`, `npm.cmd run check:responsive`, `25/25` post-fix pytest tests, and `AUDIT-TEXT-INTEGRITY-001` passed. |
| UI-SMOKE-001 | `closed` | smoke contract drift | UI smoke tests expected old marketing hero text, an exact FAQ JSX tag shape, and an outdated webapp entry marker. | Updated smoke contract/tests to current hero copy, stable FAQ class marker, and `pokrovBranding.cabinetName`. | `ROOT-PYTEST-001` passed. |
| BACKEND-MAP-001 | `closed` | scenario coverage gap | Thirteen backend route-family rows had no direct route-specific automated test mapping after the initial route import. | Added focused tests for public catalog, funnel/connect telemetry, admin funnel, broadcast, referrals, campaigns, node runtime, and node sync; refreshed `pokrov-backend-route-coverage.csv`. | `python -m pytest tests/test_backend_route_gap_coverage.py -q --basetemp .tmp/pytest-backend-route-gaps`: `4 passed`; backend coverage map has `0` rows with `test_ref_count = 0`. |
| REMOTE-CHECK-001 | `closed` | script logic | `remote_check_brain_panel.py` hard-coded a removed root `node_facts-20260207-004104.json` path and could fail before checking current facts. | Added `--facts`, latest `node_facts-*.json` discovery, and explicit fail-closed messages for missing file or missing `brain` entry. | `python -m pytest tests/test_remote_script_gap_batch.py -q --basetemp .tmp/pytest-remote-script-gap-batch`: `43 passed`; expanded ops/script pack passed. |
| SUB-INSPECT-001 | `closed` | script logic | `inspect_public_subscription_names.py` could fail with an implementation exception when the DB was missing or no active `sub_token` existed. | Added explicit missing-DB and no-token fail-closed messages aligned with `inspect_public_subscription_hosts.py`. | `python -m pytest tests/test_ops_script_gap_batch.py -q --basetemp .tmp/pytest-ops-script-gap-batch`: `14 passed`; expanded ops/script pack passed. |
| REMOTE-SUB-HOST-001 | `closed` | script logic | `remote_inspect_brain_subscription_hosts.py` returned success even when the remote subscription-host command failed. | Added fail-closed handling for non-zero remote command results while preserving token-redacted output. | `python -m pytest tests/test_remote_script_gap_batch.py -q --basetemp .tmp/pytest-remote-script-gap-batch`: `43 passed`; expanded ops/script pack passed. |
| REMOTE-HOSTS-DNS-001 | `closed` | script logic | `remote_brain_set_node_hosts_dns.py` ignored DB backup failures before applying node host updates. | Added fail-closed handling for the backup command so host updates do not run after a failed snapshot. | `python -m pytest tests/test_remote_script_gap_batch.py -q --basetemp .tmp/pytest-remote-script-gap-batch`: `43 passed`; expanded ops/script pack passed. |
| REMOTE-CONFIG-001 | `closed` | script output redaction | `remote_configure_brain_for_vless_443.py` printed the brain panel path while claiming it was not printed fully. | Changed the operator output to report only `path_len`, not the panel path value. | `python -m pytest tests/test_remote_script_gap_batch.py -q --basetemp .tmp/pytest-remote-script-gap-batch`: `43 passed`; expanded ops/script pack passed. |
| OPS-SCRIPT-MAP-001 | `closed` | scenario coverage gap | Active scripts from `scripts/manifest.yaml` did not all have direct automated scenario-test references. | Added generated canonical rows plus `pokrov-script-workflow-coverage.csv`; closed all active script scenario gaps with safe dry-run/unit/fake-SSH/fake-SFTP coverage, including the private-helper coverage and defect/fix/retest ledger generators. | `OPS-SCRIPT-FOCUSED-001`, `OPS-SCRIPT-MANIFEST-002`, `PRIVATE-HELPER-COVERAGE-001`, and `DEFECT-FIX-RETEST-LEDGER-001` cover all 121 active scripts; 0 remain `Needs scenario test`. |
| CODE-FUNCTION-INVENTORY-001 | `closed` | literal function inventory | The canonical feature tracker covered user-facing capabilities and external entrypoints, but not literal private helpers/class methods/source-level symbols. | Added `pokrov-code-function-inventory.csv`, a reusable generator, and a generator unit test; the inventory now covers root active source plus `POKROV-app` active source. | `python -m pytest tests/test_code_function_inventory.py -q --basetemp .tmp/pytest-code-function-inventory`: `1 passed`; regenerated CSV has `4320` unique symbols and `0` parser errors. |
| CODE-FUNCTION-INVENTORY-002 | `closed` | inventory scope bug | The low-level generator excluded active source files whose filename contained `test_` and, after broadening, could include e2e specs as source symbols. | The skip rule now excludes real `e2e`/test trees while keeping active `scripts/` source files with `test` in the name. | `tests/test_code_function_inventory.py` covers both cases; regenerated CSV includes `scripts/audit_story_test_evidence.py`, excludes `webapp/e2e` as source paths, and has `4320` symbols. |
| CODE-FUNCTION-INVENTORY-003 | `closed` | native host-source scope gap | The low-level inventory covered Python, TypeScript/TSX, and Dart but missed active Kotlin, Swift, and C/C++ host-shell source symbols in the client lane. | Added conservative Kotlin/Swift/C/C++ extraction and kept generated/build/test trees excluded from source rows. | `python -m pytest tests/test_code_function_inventory.py tests/test_story_test_evidence_audit.py -q --basetemp .tmp/pytest-native-inventory-audit`: `2 passed`; regenerated CSV includes 130 Kotlin, 92 Swift, 23 C++, and 5 C-header symbols. |
| CODE-FUNCTION-INVENTORY-004 | `closed` | entrypoint classification | The low-level generator treated every Python `router.*` decorator as FastAPI, so Aiogram handlers in `portal_bot/bot.py` were mislabeled as `fastapi_route_handler`. | Telegram bot files are classified first for Aiogram `router.message`, `router.callback_query`, and `router.pre_checkout_query`; FastAPI hints now require HTTP route decorators such as `app.get`, `app.post`, or `app.api_route`. | `python -m pytest tests/test_code_function_inventory.py -q --basetemp .tmp/pytest-entrypoint-hints`: `1 passed`; regenerated CSV has `0` `portal_bot/bot.py` FastAPI mislabels. |
| ENTRYPOINT-COVERAGE-001 | `closed` | entrypoint evidence mapping | Token-level function-name search produced false gaps for routes and handlers that were covered by scenario tests but did not mention the handler function name directly. | Extended `audit_story_test_evidence.py` to generate `pokrov-entrypoint-story-coverage.csv`, linking FastAPI routes to backend route coverage, scripts to script workflow coverage, and aiogram/Next/Flutter entrypoints to canonical story rows. | Latest regenerated entrypoint coverage has `512` direct mappings and `0` review gaps. |
| CLIENT-SOURCE-EVIDENCE-001 | `closed` | canonical source drift | Client story `code_evidence` still pointed at pre-`features/` paths such as `packages/app_shell/lib/src/home/home_surface.dart`, so feature-file entrypoints could not be matched to active source. | Updated 45 POKROV-app canonical rows to active `packages/app_shell/lib/src/features/...` and `src/assistant/...` paths without changing behavior or test refs. | `ENTRYPOINT-COVERAGE-001` passed; all `13` Flutter feature-file entrypoints now map to direct story evidence. |
| TELEGRAM-ENTRYPOINT-MAP-001 | `closed` | story mapping precision | Six Telegram handlers were present in source and covered by broad story tests but not explicitly named in canonical `route_or_trigger`/`code_evidence`: `noop`, `share_access`, `menu_more`, `handle_text_input`, helpbot `capture_ticket_reply`, and feedbackbot `fb_back_home`. | Updated the relevant Telegram story rows and static contract test markers so the mappings are explicit and machine-checkable. | `ENTRYPOINT-COVERAGE-001` passed; aiogram handler coverage has `172/172` direct story mappings. |
| SOURCE-EVIDENCE-PATHS-001 | `closed` | canonical source drift | A follow-up source-ref audit found stale paths for WebApp Telegram auth (`webapp/src/lib/telegram-auth.ts`) and two client doc refs that had moved to active `POKROV-app/docs` or current client closure docs. | Updated `WEBAPP-WEB-005`, `CLIENT_APP-US-066`, and `CLIENT_APP-US-067` source evidence, and added `test_canonical_code_evidence_source_refs_exist` to guard every canonical `code_evidence` file ref. | `python -m pytest tests/test_story_test_evidence_audit.py tests/test_telegram_story_contracts.py tests/test_code_function_inventory.py tests/test_marketing_story_contracts.py tests/test_check_script_manifest.py -q --basetemp .tmp/pytest-source-evidence-guard`: `13 passed`; full root `ROOT-PYTEST-007`: `722 passed, 62 warnings, 2 subtests passed`. |
| SYMBOL-COVERAGE-001 | `closed` | literal symbol status gap | The low-level function inventory listed every function/class/method, but every symbol did not yet have an explicit status tier beyond raw `inventory_only`. | Added `pokrov-symbol-coverage-audit.csv`, classifying all `4346` source symbols into entrypoint/story/test/private/public-review tiers; added route-path fallback coverage and focused email relay route tests. | `python -m pytest tests/test_email_relay_app.py tests/test_code_function_inventory.py tests/test_story_test_evidence_audit.py tests/test_telegram_story_contracts.py tests/test_marketing_story_contracts.py tests/test_check_script_manifest.py -q --basetemp .tmp/pytest-symbol-coverage-focused`: `15 passed`; full root `ROOT-PYTEST-008`: `724 passed, 62 warnings, 2 subtests passed`. |
| EMAIL-RELAY-ENTRYPOINT-001 | `closed` | route coverage gap | `portal_bot/email_relay_app.py::healthz` was a FastAPI route symbol with no direct route/story/script coverage signal. | Added `tests/test_email_relay_app.py` for `/healthz` readiness/auth metadata and fail-closed `/email/deliver` secret behavior. | `SYMBOL-COVERAGE-001` passed; `healthz` is now `entrypoint_route_test_ref`. |
| SCRIPT-MANIFEST-REVIEW-001 | `closed` | script status gap | 22 scripts exposed `main()` but were not in active script workflow coverage, deprecated, archive-only, or denylist status. | Classified 20 as active operator workflows with direct test refs, classified the 2 legacy FreeKassa CLIs as deprecated, and added a manifest guard for future unclassified CLI `main()` files. | `OPS-SCRIPT-MANIFEST-002` passed; symbol coverage has `0` `script_cli_manifest_review` rows and `2` `script_cli_deprecated` rows. |
| REMOTE-POSTGRES-CLI-001 | `closed` | script logic/safety | Newly active remote/postgres helpers accepted unsafe shell/SQL-shaped values for domain, db-name, identifiers, or plan-code arguments. | Added validation, shell quoting, SQL literal escaping, and fake SSH/SFTP tests for Postgres diagnostics, worker service install, cutover, and payment reconciliation. | `OPS-SCRIPT-MANIFEST-002` passed. |
| SOURCE-MODULE-COVERAGE-001 | `closed` | symbol evidence precision | `public_symbol_review` mixed truly untriaged public helpers with public symbols in story-reachable Python/TypeScript/TSX dependencies or modules/classes already referenced by automated tests. | Added `story_dependency_source_file` classification for local Python and TypeScript/TSX imports from story-mapped source files and `module_test_ref` classification based on source module/import path or parent type references in test files, while keeping direct symbol assertions and story mappings as stronger tiers. | `python -m pytest tests/test_code_function_inventory.py -q --basetemp .tmp/pytest-python-local-dependency`: `2 passed`; that pass had `595` `story_dependency_source_file` rows, `83` `module_test_ref` rows, and `76` remaining public review rows. |
| CLIENT-PLATFORM-SYMBOL-001 | `closed` | symbol status precision | Native Android/iOS/macOS/Windows host symbols were mixed into ordinary public-helper review even though they require platform/unit/simulator/device evidence before stronger runtime claims. | Added `client_platform_host_manual_gate` classification for public native client host symbols that do not already have stronger story/test/module evidence. | `python -m pytest tests/test_code_function_inventory.py -q --basetemp .tmp/pytest-client-platform-host-tier`: `2 passed`; that pass had `112` `client_platform_host_manual_gate` rows and `183` remaining public review rows. |
| PUBLIC-SYMBOL-TRIAGE-001 | `closed` | symbol evidence precision | The final `public_symbol_review` rows mixed framework route boundaries, Telegram WebApp bootstrap, QA/operator tooling, Windows tray callbacks, client package API symbols, stale frontend helpers, and parser visibility/import-graph artifacts. | Fixed TS/Dart visibility, multiline TS re-export/barrel dependency traversal, and generator self-test coverage pollution; removed unused `webapp/src/lib/pricing.ts` and `marketing/src/components/ui/fade-up.tsx`; added specialized Next/Telegram/QA/operator/client desktop/client package tiers; added direct FreeKassa ticket helper assertions. | `python -m pytest tests/test_code_function_inventory.py tests/test_freekassa_staging_smoke.py tests/test_story_test_evidence_audit.py tests/test_check_script_manifest.py -q --basetemp .tmp/pytest-symbol-triage-focused`: `13 passed`; WebApp and marketing builds passed; latest symbol coverage has `0` `public_symbol_review` rows and `0` entrypoint/script-manifest gaps. |
| CLIENT-PACKAGE-API-001 | `closed` | client package API evidence | Five public Flutter/Dart package APIs remained in the explicit `client_package_public_api_review` bucket after generic public-symbol review was closed. | Added focused `app_shell` contract tests for app-shell palette/motion/action-row/sidebar/first-launch and platform bootstrap public API contracts. | `flutter test test/design_system_contract_test.dart --reporter compact` in `POKROV-app/packages/app_shell`: `19` tests passed; focused root guard pack: `13 passed`; regenerated symbol coverage has `0` `client_package_public_api_review` rows. |
| TRACKER-STATUS-HYGIENE-001 | `closed` | tracker status, field, guardrail, and evidence hygiene | The canonical CSV still carried imported pass-status variants (`Pass`, `Retest Pass`, `Retested pass`), blank `fix_status` cells, seven `Retest passed` rows whose `latest_result` still described an initial fail/issue, blank `canon_guardrails` for 67 client app rows, 55 priority-only marketing guardrails, and three client rows with directory-level `code_evidence`. | Normalized all passing story rows to `Retest passed`, filled empty fix statuses, moved historical fail/issue text into defect notes, filled client app canon guardrails, converted marketing priorities into `Imported priority P*` plus public marketing canon guardrails, replaced directory-level client evidence with concrete files, and added canonical status/story-contract/source-evidence guards. | `python -m pytest tests/test_story_test_evidence_audit.py tests/test_code_function_inventory.py tests/test_check_script_manifest.py -q --basetemp .tmp/pytest-priority-only-guardrails-focused`: `12 passed`; regenerated story evidence audit stayed at `520` direct file refs, `1` manual owner gate, and `0` missing refs. |
| SOURCE-TRACKER-HYGIENE-001 | `closed` | tracker provenance hygiene | The 119 generated script/operator rows used `generated-script-manifest`, which was neither a resolvable source file nor one of the explicit generated-source labels guarded by pytest. | Normalized those rows to `generated from scripts/manifest.yaml` and added `test_canonical_source_trackers_are_resolvable` so future `source_tracker` values must resolve to existing source tracker files/paths or to backed generated-source labels. | `python -m pytest tests/test_story_test_evidence_audit.py tests/test_code_function_inventory.py tests/test_check_script_manifest.py -q --basetemp .tmp/pytest-source-tracker-focused`: `14 passed`; story evidence audit remains at `520` direct file refs, `1` manual owner gate, and `0` missing refs. |
| OWNER-GATE-MATRIX-001 | `closed` | manual-gate decomposition | The remaining `CLIENT_APP-US-067` manual owner gate was one broad row, so the next owner phase was not decomposed into atomic scenarios with expected behavior, required evidence, allowed statuses, source docs, latest result/fix/retest fields, and required-for-completion semantics. | Added `pokrov-owner-gated-scenarios.csv`, `pokrov-owner-gated-results.csv`, and `.md` covering Android physical exact-artifact smoke, Windows exact-artifact smoke, real Telegram WebApp session, payment maturity, signing/store trust, live deployed app-session proof, RU-origin probe, and conditional WARP runtime proof; added a pytest guard for required rows, fields, labels, source-doc refs, result ledger fields, bidirectional linkage to canonical manual rows, and required/conditional gate status semantics. | `python -m pytest tests/test_story_test_evidence_audit.py::test_owner_gated_scenarios_are_explicit_and_resolvable -q --basetemp .tmp/pytest-owner-gates-required-targeted`: `1 passed`. |
| OWNER-GATE-TRACEABILITY-001 | `closed` | owner-gate question traceability | The owner-gated scenarios were linked to `CLIENT_APP-US-067`, but each scenario did not carry a machine-readable blocking question and the summary table did not show canonical row/question context next to each gate. | Added `blocking_question_id=Q-004` to every scenario row, showed canonical row and blocking question in the owner-gated summary table, documented the scenario-matrix fields in the execution guide, and expanded the guard to require the row/question links. | Targeted owner-gate guard: `1 passed`; focused tracker/inventory/manifest pack: `37 passed`. |
| OWNER-ANSWER-SHEET-001 | `closed` | owner-question actionability | The open-question ledger and owner-gate guides tracked the blockers, but the owner still needed a compact sheet with exact answer codes and gate IDs for Q-001/Q-004. | Added `pokrov-owner-answer-sheet.md`, linked it from open questions, tracker, completion audit, and developer navigation, and expanded guards so the sheet must keep policy codes, gate IDs, result labels, and result-ledger recording rules. | Targeted owner-question/navigation/text guards: `3 passed`; focused tracker/inventory/manifest pack: `37 passed`. |
| OWNER-GATE-STATUS-SEMANTICS-001 | `closed` | owner-gate result semantics | The owner-gated result ledger had allowed status labels, but the guard did not enforce status-specific evidence/fix/retest semantics for future PASS, FAIL, access-blocked, skipped, and not-requested rows. | Added status-specific rules to `pokrov-owner-gated-execution-guide.md`, expanded the owner-gate guard to require matching evidence, defect, access, owner-skip, and retest context for each status, and regenerated source inventory artifacts after the new guard changed test-token references. | Targeted owner-gate guard: `1 passed`; focused tracker/inventory/manifest pack after regeneration: `37 passed`. |
| MANUAL-GATE-SYMBOL-REFS-001 | `closed` | source-symbol manual-gate traceability | Manual-tier client host/tray symbols were visible in the source-symbol audit, but the CSV did not identify the owner gate or not-current-beta scope marker for each low-level manual symbol. | Added generated `manual_gate_refs` to `pokrov-symbol-coverage-audit.csv`, mapped Android host symbols to the Android owner gate, Windows host/tray symbols to the Windows owner gate, iOS/macOS host symbols to `NOT_CURRENT_PUBLIC_BETA_TARGET`, documented the field, and expanded generator/summary guards. | Targeted symbol/generator/summary guards: `4 passed`; focused tracker/inventory/manifest pack: `37 passed`; `80` platform/tray manual-tier rows now carry refs. |
| MANUAL-GATE-REF-LEDGER-001 | `closed` | source-symbol owner-gate ref drift | Manual-tier symbol refs existed, but the test allowed list was separate from the real Q-004 owner-gated scenario ledger. | Changed the guard to load allowed `OWNER-GATE-*` values from `pokrov-owner-gated-scenarios.csv`, kept `NOT_CURRENT_PUBLIC_BETA_TARGET` as the only non-ledger scope marker, and documented the cross-ledger contract in the symbol audit and owner-gated execution guide. | Targeted symbol/manual-ref guards: `2 passed`; focused tracker/inventory/manifest pack: `37 passed`. |
| MANUAL-GATE-REF-SUMMARY-001 | `closed` | manual symbol aggregate visibility | Manual-tier symbol refs were machine-readable in the CSV, but the human-readable symbol audit did not show how many low-level symbols mapped to each owner gate or current-beta scope marker. | Added `Manual Gate Reference Counts` to `pokrov-symbol-coverage-audit.md` and extended the Markdown summary guard to compare that table to `manual_gate_refs` in the CSV. | Targeted symbol summary/manual-ref guards: `2 passed`; focused tracker/inventory/manifest pack: `37 passed`. |
| COMPLETION-AUDIT-CSV-001 | `closed` | completion audit machine readability | The goal-level requirement checklist existed only in `COMPLETION-AUDIT.md`, so requirement status, evidence refs, and blocking Q-001/Q-004 rows were not directly machine-checkable. | Added `COMPLETION-AUDIT.csv`, linked it from the completion audit and work-order index, included it in canonical CSV text-integrity checks, and added a guard for required rows, statuses, evidence refs, blocker IDs, and Markdown synchronization. | Targeted completion-ledger/text guards: `3 passed`; focused tracker/inventory/manifest pack: `38 passed`. |
| COMPLETION-BLOCKER-RELATIONSHIP-001 | `closed` | completion blocker semantics | `COMPLETION-AUDIT.csv` had `blocker_ids`, but the field mixed rows that directly block completion with locally proven rows that only carry Q-001/Q-004 context. | Added `blocker_relationship` values `blocking_requirement`, `related_context`, and `none`; updated the guard so blocking rows must carry `blocking_requirement`, contextual rows must carry `related_context`, and rows without blockers must carry `none`. | Targeted completion-ledger guards: `2 passed`; focused tracker/inventory/manifest pack: `38 passed`. |
| COMPLETION-LEDGER-SUMMARY-001 | `closed` | completion summary visibility | `COMPLETION-AUDIT.csv` held machine-readable completion status, but `COMPLETION-AUDIT.md` did not expose row/status/blocker-relationship counts for human review. | Added `Machine Ledger Counts` to `COMPLETION-AUDIT.md` and extended the completion ledger guard to compare both summary tables to the CSV. | Targeted completion-ledger guard: `1 passed`; focused tracker/inventory/manifest pack: `38 passed`. |
| COMPLETION-AUDIT-NAV-001 | `closed` | completion audit discoverability | `COMPLETION-AUDIT.md` and `COMPLETION-AUDIT.csv` were linked from the canonical tracker and work-order index, but not from top-level developer navigation docs. | Linked the completion audit artifacts from `docs/README.md`, `developer-guide.md`, and `repository-map.md`; expanded the navigation guard to require those work-order artifacts in developer navigation. | Targeted navigation/completion guards: `2 passed`; focused tracker/inventory/manifest pack: `38 passed`. |
| WORK-ORDER-WAVE-README-001 | `closed` | work-order wave discoverability | The active `2026-06-27--repo-feature-story-audit` wave had a local `INDEX.md`, but the work-orders landing README did not list the active wave. | Added an `Active Waves` section to `docs/developer/work-orders/README.md` and expanded the navigation guard to require the active audit wave and its `INDEX.md` link there. | Targeted work-order navigation guard: `1 passed`; focused tracker/inventory/manifest pack: `38 passed`. |
| WORK-ORDER-INDEX-COUNTS-001 | `closed` | wave index count drift | The wave-local `INDEX.md` still listed `119` active script/operator workflow rows, while the canonical tracker had `121` `Scripts and Ops` rows. | Updated the index count to `121` and added `test_work_order_index_imported_coverage_matches_tracker_csv` so all imported coverage counts in the wave index are checked against the canonical tracker CSV. | Targeted wave-index coverage guard: `1 passed`; focused tracker/inventory/manifest pack: `39 passed`. |
| WORK-ORDER-CURRENT-OUTPUT-COUNTS-001 | `closed` | work-order summary count drift risk | The `WO-001` current-output summary was a manually maintained resume surface with many canonical counts, but no guard checked those counts against the CSV artifacts. | Added `test_work_order_current_output_counts_match_csv_artifacts` to compare key `Current Output` rows against tracker, route, script, entrypoint, function, symbol, story-evidence, defect, owner-gate, and question CSVs. | Targeted work-order current-output guard: `1 passed`; focused tracker/inventory/manifest pack: `40 passed`. |
| WORK-ORDER-SOURCE-REF-COUNTS-001 | `closed` | work-order source-ref count drift | `WO-001 Current Output` still listed `881` canonical source-evidence refs, while the current canonical `code_evidence` parser checks `1072` refs; line-ref and source-tracker counts were also not covered by the work-order summary guard. | Updated the summary to `1072` and expanded `test_work_order_current_output_counts_match_csv_artifacts` to compare source-evidence refs, line refs, and source-tracker row counts against current CSV-derived values. | Targeted work-order source-ref count guard: `1 passed`; focused tracker/inventory/manifest pack: `41 passed`. |
| COMPLETION-SOURCE-REF-EVIDENCE-001 | `closed` | completion evidence coverage drift | `COMPLETION-AUDIT.md` and `COMPLETION-AUDIT.csv` still cited the older source-provenance guards, but did not surface the newer work-order source-ref/current-output guard or the current `1072`/`352`/`523` source-reference totals. | Added the work-order source-ref guard to `REQ-004`, exposed the guarded source-reference totals in the completion checklist, and extended `test_completion_audit_requirement_ledger_tracks_goal_scope` to require that evidence. | Targeted completion-ledger guard: `1 passed`; focused tracker/inventory/manifest pack: `41 passed`. |
| COMPLETION-DISCREPANCY-EVIDENCE-001 | `closed` | completion discrepancy evidence split | `COMPLETION-AUDIT.md` and `COMPLETION-AUDIT.csv` said new mismatches needed a finding and ledger row, but audit-only drift such as `COMPLETION-SOURCE-REF-EVIDENCE-001` is correctly tracked by closed findings rather than by the generated story-row defect ledger. | Updated `REQ-015` to cite both closed finding docs and the defect/fix/retest ledger, and clarified that story-row mismatches need defect-ledger rows while audit-only discrepancies need closed findings with verification. | Targeted completion-ledger guard: `1 passed`; focused tracker/inventory/manifest pack: `41 passed`. |
| COMPLETION-RETEST-EVIDENCE-001 | `closed` | completion retest evidence traceability | `REQ-016` summarized broad local retest evidence but did not require named run IDs or a work-order evidence ref, so the retest-after-fixes claim was weaker than the other completion requirements. | Added `WO-001` to `REQ-016` evidence refs, named the broad retest run IDs in the completion checklist and work-order summary, and expanded the completion ledger guard to require those run IDs in tracker, work-order, and completion audit sources. | Targeted completion-ledger guard: `1 passed`. |
| COMPLETION-REQUIRED-GENERATORS-001 | `closed` | completion required-command coverage drift | `COMPLETION-AUDIT.md` required regenerating story evidence, code inventory, and private-helper coverage after tracker/audit changes, but omitted `scripts/generate_defect_fix_retest_ledger.py` even though the defect/fix/retest ledger is canonical and guarded. | Added `python scripts/generate_defect_fix_retest_ledger.py` to required verification commands, added the generator to `WO-001` write scope, and extended the completion guard to require all canonical audit generator commands. | Targeted completion-ledger guard: `1 passed`. |
| WORK-ORDER-SCOPE-PARITY-001 | `closed` | work-order scope drift | `WO-001` linked and tested the canonical audit sidecars, but its write scope omitted `pokrov-defect-fix-retest-ledger.csv`, `pokrov-defect-fix-retest-ledger.md`, and `pokrov-owner-answer-sheet.md`, so a future continuation could miss artifacts that navigation and completion audit treat as canonical. | Added the missing sidecars to `WO-001` write scope and expanded `test_canonical_audit_artifacts_are_linked_from_developer_navigation` to require every `NAVIGATION_ARTIFACT` in the active work-order scope. | Targeted developer-navigation/work-order-scope guard: `1 passed`. |
| COMPLETION-REPRO-EVIDENCE-001 | `closed` | completion reproducibility evidence drift | `REQ-006` covered story evidence, code inventory, and private-helper reproducibility but omitted `test_generated_defect_fix_retest_ledger_matches_canonical_files`, even though the defect/fix/retest ledger is canonical, generated, and now part of required verification commands. | Added the defect/fix/retest reproducibility guard to `REQ-006`, updated completion/work-order prose to include that ledger, and expanded the completion ledger guard to require all reproducibility evidence refs. | Targeted completion-ledger guard: `1 passed`. |
| COMPLETION-SUMMARY-EVIDENCE-001 | `closed` | completion Markdown-summary evidence drift | `REQ-007` cited only the canonical tracker, code inventory, and symbol summary guards even though story evidence, defect/fix/retest, entrypoint, and private-helper summaries are also canonical and guarded. | Added every current Markdown summary guard to `REQ-007`, updated completion/work-order prose to include the defect/fix/retest and private-helper summaries, and expanded the completion ledger guard to require all summary evidence refs. | Targeted completion-ledger guard: `1 passed`. |
| COMPLETION-STATUS-EVIDENCE-001 | `closed` | completion canonical-status evidence drift | `REQ-003` described canonical tracker status counts and retest proof counts, but the machine-readable evidence refs only named the CSV artifacts and did not cite the guards that prove normalized status fields, direct/manual retest proof states, or defect/fix/retest closure. | Added the tracker-status, story-retest-proof, and defect-ledger closure guards to `REQ-003`, named those checks in `COMPLETION-AUDIT.md`, and expanded the completion ledger guard to require the evidence refs and defect closure counts. | Targeted completion-ledger guard: `1 passed`. |
| COMPLETION-INVENTORY-EVIDENCE-001 | `closed` | completion feature-inventory evidence drift | `REQ-001` stated the canonical tracker subsystem counts but its machine-readable evidence refs only named the tracker artifacts, not the guards that compare tracker summaries and work-order imported coverage counts against the CSV. | Added the canonical tracker summary and active work-order index coverage guards to `REQ-001`, named both checks in `COMPLETION-AUDIT.md`, and expanded the completion ledger guard to require the subsystem count fragments. | Targeted completion-ledger guard: `1 passed`. |
| COMPLETION-SYMBOL-EVIDENCE-001 | `closed` | completion source-symbol evidence drift | `REQ-008` and `REQ-009` stated low-level inventory and source-symbol classification counts, but the machine-readable evidence refs did not cite the guards that prove code-inventory summary parity, generated inventory reproducibility, expected-behavior notes, manual-gate refs, or private-tier leakage prevention. | Added source-inventory and symbol-coverage guards to `REQ-008` and `REQ-009`, named those checks in `COMPLETION-AUDIT.md`, and expanded the completion ledger guard to require the key symbol count and manual-gate evidence fragments. | Targeted completion-ledger guard: `1 passed`. |
| COMPLETION-OWNER-PACKET-EVIDENCE-001 | `closed` | completion owner-packet evidence drift | `REQ-010`, `REQ-013`, and `REQ-017` described Q-001/Q-004 owner packets and open-question tracking, but the machine-readable evidence refs did not cite the guards that prove policy codes, answer-sheet markers, guide fields, gate IDs, and private-helper decision-matrix linkage. | Added owner-question, owner-gate, and private-helper matrix guards to the relevant completion rows, named those checks in `COMPLETION-AUDIT.md`, and expanded the completion ledger guard to require the Q-001/Q-004 evidence fragments. | Targeted completion-ledger guard: `1 passed`. |
| COMPLETION-STORY-ENTRYPOINT-EVIDENCE-001 | `closed` | completion story/entrypoint evidence drift | `REQ-011` and `REQ-014` stated non-manual story evidence and entrypoint direct-mapping counts, but the machine-readable evidence refs did not cite the story summary, entrypoint summary, or generated story/entrypoint reproducibility guards. | Added story evidence, story retest proof, generated story/entrypoint reproducibility, and entrypoint summary guards to the relevant completion rows, named those checks in `COMPLETION-AUDIT.md`, and expanded the completion ledger guard to require the direct story and entrypoint mapping counts. | Targeted completion-ledger guard: `1 passed`. |
| COMPLETION-DEFECT-RETEST-EVIDENCE-001 | `closed` | completion defect/retest evidence drift | `REQ-015` and `REQ-016` had the right human-readable defect and broad retest evidence, but the machine-readable refs did not cite the defect-ledger closure/summary guards or the completion guard that requires broad retest run IDs across the completion audit, canonical tracker, and work-order tracker. | Added defect-ledger closure/summary guards to `REQ-015`, added the completion-ledger guard to `REQ-016`, and expanded the completion guard to require those evidence refs plus the broad-run-ID guard wording. | Targeted completion-ledger guard: `1 passed`. |
| COMPLETION-STORY-LINE-EVIDENCE-001 | `closed` | completion story-contract and line-ref evidence drift | `REQ-002` and `REQ-005` already named their primary guards, but the machine-readable evidence refs did not cite the canonical tracker CSV/MD story-contract source or the owner/question ledgers scanned by the line-ref guard. | Added the canonical tracker artifacts to `REQ-002`, added every line-ref source ledger to `REQ-005`, updated completion prose, and expanded the completion ledger guard to require these refs and count fragments. | Targeted completion-ledger guard: `1 passed`. |
| COMPLETION-OWNER-SCENARIO-EVIDENCE-001 | `closed` | completion owner-scenario evidence drift | `REQ-012` was the only completion requirement left without an explicit assertion block in `test_completion_audit_requirement_ledger_tracks_goal_scope`, and its evidence refs omitted the owner-gated Markdown summary. | Added `pokrov-owner-gated-scenarios.md` to `REQ-012`, updated completion prose to name the summary, and expanded the completion ledger guard to require the scenario/result/source-summary refs plus open-gate and bidirectional-linkage fragments. | Targeted completion-ledger guard: `1 passed`. |
| COMPLETION-TEST-SYMBOL-REFS-001 | `closed` | completion test-symbol evidence drift | The completion ledger resolved `.py` evidence files but did not generically prove that `tests/...py::test_*` anchors still existed after test renames. | Extended `test_completion_audit_requirement_ledger_tracks_goal_scope` to parse each Python evidence ref with `::`, load the target file, and require a matching test function definition. | Targeted completion-ledger guard: `1 passed`. |
| COMPLETION-ROW-PARITY-001 | `closed` | completion Markdown/CSV row drift | `COMPLETION-AUDIT.md` summarized the CSV counts, but the requirement checklist could still drift from `COMPLETION-AUDIT.csv` per row; several status/gap cells had already diverged in wording. | Normalized the checklist status/gap cells to the CSV labels and added row-level parsing to `test_completion_audit_requirement_ledger_tracks_goal_scope` for requirement order, status display, remaining gap, and non-empty evidence cells. | Targeted completion-ledger guard: `1 passed`. |
| COMPLETION-EVIDENCE-CELL-VISIBILITY-001 | `closed` | completion evidence-cell visibility drift | The Markdown checklist matched CSV rows, but a reviewer still had to open `COMPLETION-AUDIT.csv` to see some evidence refs because several Markdown evidence cells did not name their referenced artifact basename or test function. | Added generic visibility checks for every completion evidence ref and updated the Markdown evidence cells to mention missing basenames and test symbols. | Targeted completion-ledger guard: `1 passed`. |
| COMPLETION-GATE-TABLE-PARITY-001 | `closed` | completion manual-gate table drift | `COMPLETION-AUDIT.md` listed current blocking/manual gates by prose labels, but it omitted the Windows exact-artifact owner gate even though `pokrov-owner-gated-scenarios.csv` tracks it as a Q-004 scenario. | Replaced the prose-only gate table with explicit `OWNER-GATE-*` / `Q-001` identifiers, added the missing Windows install/connect row, and expanded the completion guard to compare the table against owner-gated scenarios and the Q-001 open question. | Targeted completion-ledger guard: `1 passed`. |
| INVENTORY-SYMBOL-PROSE-COUNTS-001 | `closed` | inventory and symbol-audit prose drift | `pokrov-code-function-inventory.md` still said source-symbol coverage covered `4577` symbols, and `pokrov-symbol-coverage-audit.md` listed `OWNER-GATE-LIVE-DEPLOY-APP-SESSION` as a manual symbol ref target even though no current `manual_gate_refs` row uses it. | Updated the prose to `4578` symbols, removed the unused live-deploy gate from the manual-ref interpretation, and expanded Markdown guards to check the prose count and documented owner refs against the CSV artifacts. | Targeted inventory/symbol Markdown guards: `2 passed`; focused tracker/inventory/manifest pack: `40 passed`. |
| AUDIT-HISTORY-WORDING-001 | `closed` | historical wording drift | Some historical run/finding rows used `current`, `now reports`, or `latest regenerated` around counts that were true for that pass but no longer current after later regenerated artifacts. | Reworded those rows to say `that run/pass/initial audit reported` while preserving the original historical counts; added a guard for exact stale-current fragments in canonical audit history docs. | Targeted stale-current wording guard: `1 passed`; focused tracker/inventory/manifest pack: `41 passed`. |
| PRIVATE-INVENTORY-TIER-001 | `closed` | symbol evidence precision | The audit used `private_inventory_only` for low-level helpers, but the real generated CSV was not guarded against a public symbol or entrypoint hint being silently classified as private inventory. | Added a repository-level generated-artifact guard that fails if any `private_inventory_only` row is not `visibility=private` or has an `entrypoint_hint`. | `python -m pytest tests/test_code_function_inventory.py::test_generated_private_inventory_tier_contains_only_private_non_entrypoints -q --basetemp .tmp/pytest-private-inventory-tier-targeted`: `1 passed`; current CSV has `0` public/entrypoint leakage in the private tier. |
| PRIVATE-HELPER-COVERAGE-001 | `closed` | Q-001 private-helper baseline | Q-001 had a policy guide, but the private-only symbols were not expanded into a concrete per-symbol expected-behavior/risk/proof-status matrix for the owner to use when choosing a stricter coverage policy. | Added `pokrov-private-helper-coverage.csv`, `.md`, and `scripts/generate_private_helper_coverage.py`; linked the matrix from Q-001, canonical tracker, code/symbol docs, and developer navigation; added pytest guards for row parity with `private_inventory_only`, source-path resolution, summary counts, and generator reproducibility. | `python -m pytest tests/test_code_function_inventory.py::test_private_helper_coverage_matrix_matches_private_inventory_only tests/test_code_function_inventory.py::test_private_helper_coverage_markdown_summary_matches_csv tests/test_code_function_inventory.py::test_generated_private_helper_coverage_artifacts_match_canonical_files -q --basetemp .tmp/pytest-private-helper-coverage-targeted`: `3 passed`. |
| PRIVATE-HELPER-HIGH-RISK-001 | `closed` | private-helper behavior coverage | High-risk private helpers in email relay and FreeKassa API probe were still only source-inventory rows, so their URL/auth/logo/message composition and remote JSON escaping behavior were not asserted directly. | Added direct helper tests for email relay config/secret/URL/logo/message/fail-closed behavior and FreeKassa remote Python command construction; isolated `WEBAPP_URL` in the email relay test fixture and kept Unicode probe input ASCII-safe. | `python -m pytest tests/test_email_relay_app.py tests/test_freekassa_api_probe.py -q --basetemp .tmp/pytest-high-risk-private-helpers-targeted`: `8 passed`. |
| TELEGRAM-WEBAPP-BOOTSTRAP-001 | `closed` | WebApp Telegram UX and coverage | Telegram WebApp bootstrap helpers were private-only rows, and `resolveBackFallback` missed the active `/settings` cabinet route, so Telegram BackButton on settings could navigate to `/` instead of the dashboard. | Added `/settings` to the dashboard fallback group; added Playwright coverage for Telegram CSS vars, safe area, viewport, theme preference migration, theme/viewport events, keyboard resize, haptic tap, BackButton haptic, and settings back navigation; fixed the source-symbol generator so `webapp/e2e` specs count as test evidence without becoming source symbols. | New e2e target: `1 passed`; production WebApp build passed; full `settings-email-link.spec.ts` on static export: `7 passed`; current regenerated symbol coverage has `0` private-inventory rows, `0` high-risk private rows, and `219` direct-token refs. |
| CLIENT-WINDOWS-TRAY-001 | `closed` | client private-helper behavior coverage | The Windows tray `_showWindow` helper restored/shown/focused the app window through plugin singletons, but it had no local behavior test and remained the only high-risk private-only helper. The Dart parser also missed multiline function signatures and could misread multiline call statements as declarations. | Extracted the show-window ordering into `pokrovWindowsShowWindow` with injected async callbacks, kept `_showWindow` as the production wrapper, added Windows shell tests for minimized and already-visible states, and hardened the Dart parser for multiline signatures plus statement-prefix false positives. | `flutter test test/widget_test.dart --reporter compact` in `POKROV-app/apps/windows_shell`: `3` tests passed; parser fixture test passed; current regenerated private-helper matrix has `0` high-risk rows. |
| WEBAPP-SERVE-EXPORT-001 | `closed` | webapp operator helper coverage | `webapp/scripts/serve_export.py` used private helpers for static-export SPA candidate normalization and root-confined file opening, but both helpers were only source-inventory rows. | Added focused unit coverage for root/index, trailing-slash, extensionless, query-string, and encoded traversal candidate normalization, plus successful file open, missing file, parent traversal, and symlink escape refusal. | `python -m pytest tests/test_serve_export.py -q --basetemp .tmp/pytest-serve-export-private-helpers`: `2 passed`; current regenerated private-helper matrix has `0` rows and no `webapp_operator_script_helper` rows. |
| CLIENT-FEATURE-LABELS-001 | `closed` | client feature label helper coverage | Fourteen client feature copy/label helpers for locations, profile access, route modes, and rules presets were still private-only rows even though they surface in existing home/profile/rules/locations UI scenarios. | Added an explicit private-helper coverage marker to `pokrov_seed_app_test.dart` and tied it to the existing premium shell, rules, and locations UI behavior checks, without exporting private helpers from the app shell library. | `flutter test test/pokrov_seed_app_test.dart --reporter compact --name "renders premium shell v2|rules show selected-apps editor|locations screen renders backend catalog cities"` in `POKROV-app/packages/app_shell`: `3` tests passed; current regenerated private-helper matrix has `0` rows and no `client_feature_copy_or_logic_helper` rows. |
| WEBAPP-QA-OVERLAY-001 | `closed` | WebApp QA tooling coverage and UX | QA overlay private helpers were private-only rows, and Browser smoke showed the dark overlay reused the light theme `--atlas-surface` for metric/button cells, making cyan text low-contrast in the default light cabinet theme. | Added stable QA overlay test ids, a focused Playwright spec for metrics, icon-only detection, hotkey/Escape handling, hitbox toggling, and internal-link scanning; changed overlay cells/buttons/results to dark translucent cyan surfaces with readable text. | `NEXT_PUBLIC_ENABLE_QA_OVERLAY=true npm.cmd run build` passed; `npx.cmd playwright test e2e/qa-overlay.spec.ts` passed; in-app Browser smoke showed readable panel text, no framework overlay, and no console errors/warnings; current regenerated private-helper matrix has `0` rows and no `qa_tooling_helper` rows. |
| CLIENT-NAVIGATION-SHELL-001 | `closed` | client navigation shell helper coverage | Fourteen medium-risk private navigation shell helpers for responsive mobile/desktop shells, lazy tab retention, sidebar, brand mark, and drawer behavior were still private-only rows despite existing Flutter UI scenarios covering those behaviors. | Added an explicit navigation-shell private-helper coverage marker to `pokrov_seed_app_test.dart` and tied it to existing lazy tab retention, P4 responsive width matrix, and narrow Windows drawer tests without exporting private app-shell widgets. | `flutter test test/pokrov_seed_app_test.dart --reporter compact --name "seed shell lazily builds tabs|P4 responsive width matrix|narrow windows shell uses a hamburger drawer"` in `POKROV-app/packages/app_shell`: `3` tests passed; current regenerated private-helper matrix has `0` rows and no `navigation_shell.dart` rows. |
| CLIENT-FIRST-LAUNCH-STORE-001 | `closed` | client first-launch storage coverage | `PokrovFileFirstLaunchStore._stateFile` was the last medium-risk private-only row, and a first attempt to mock `path_provider` through a method channel hung the focused Flutter test. | Replaced the channel mock with the upstream-supported `PathProviderPlatform` fake, added an explicit persistence behavior test for `isCompleted` / `markCompleted`, and declared `path_provider_platform_interface` as a direct dev dependency for the test package. | `flutter test test/design_system_contract_test.dart --reporter compact --name "file first-launch store"` in `POKROV-app/packages/app_shell`: `2` tests passed; post-first-launch regenerated private-helper matrix had `22` low-risk rows and `0` medium-risk rows. |
| CLIENT-SHARED-SHELL-WIDGETS-001 | `closed` | client shared shell widget coverage | Low-risk private shared shell widgets for section cards, backdrop, status pills, connect orb state/lifecycle, settle layer, and rim painter remained private-only even though existing public UI scenarios exercise them. | Added an explicit shared-shell-widget coverage marker to `pokrov_seed_app_test.dart` and tied it to premium shell, connect-disc visual, and rules selected-apps scenarios without exporting private widgets. | `flutter test test/pokrov_seed_app_test.dart --reporter compact --name "renders premium shell v2|home uses raster brand mark|rules show selected-apps editor"` in `POKROV-app/packages/app_shell`: `3` tests passed; post-shared-shell regenerated private-helper matrix had `10` low-risk rows and no `shell_widgets.dart` rows. |
| CLIENT-SIDEBAR-INFO-SHEET-001 | `closed` | client sidebar and info-sheet helper coverage | Low-risk private desktop sidebar and info-sheet helpers remained private-only even though public sidebar, home-details, and profile grouped-section tests exercise their visible behavior. | Added explicit sidebar/info-sheet coverage markers to `design_system_contract_test.dart` and `pokrov_seed_app_test.dart`, tied to desktop sidebar, home connection details bottom sheet, and profile grouped account sections. | Targeted Flutter runs passed: `desktop sidebar preserves width keys and destination taps` (`1` test) and `home status opens connection details|profile uses grouped MVP account sections` (`2` tests); post-sidebar/info-sheet regenerated private-helper matrix had `5` low-risk rows and no `pokrov_sidebar.dart` / `info_sheet.dart` rows. |
| CLIENT-APP-SHELL-IMPLEMENTATION-001 | `closed` | client app-shell implementation helper coverage | The final low-risk private-only helpers were app-shell shortcut intents, private motion scope, and key-value detail rows; each is exercised through existing public app-shell behavior. | Added an explicit app-shell implementation helper marker to `pokrov_seed_app_test.dart`, tied to premium shell motion policy, profile subscription detail rows, and Windows keyboard shortcuts for navigation/composer/send. | `flutter test test/pokrov_seed_app_test.dart --reporter compact --name "renders premium shell v2|profile surfaces devices, notifications and subscription detail|P5 Windows shortcuts navigate tabs"` in `POKROV-app/packages/app_shell`: `3` tests passed; current regenerated private-helper matrix has `0` rows. |
| SOURCE-EVIDENCE-CONCRETE-001 | `closed` | canonical source reference precision | `WEBAPP-ADM-006` used `webapp/src/components/admin/users/*` as directory-level source evidence, and `WEBAPP-ADM-007` used basename-only component refs. Both made source evidence less precise than the actual files implementing users search, filters, URL state, pagination, and detail diagnostics. | Replaced the wildcard and basename refs with concrete `/admin/users` source files; added `test_canonical_code_evidence_uses_concrete_source_refs` and tightened `test_canonical_code_evidence_source_refs_exist` so wildcard or unresolved `code_evidence` cannot return. | Targeted source-ref guards: `3 passed` with `0` unresolved refs; that pass regenerated story evidence with `523` rows and `522` direct refs, entrypoint coverage with `512` direct mappings, symbol coverage with `4577` rows, private-helper coverage with `0` rows, and focused tracker/inventory/manifest pack with `32` tests. |
| SYMBOL-EXPECTED-BEHAVIOR-001 | `closed` | low-level symbol expected behavior | Source-symbol rows classified every function/class/method, but the generated CSV did not yet expose a direct expected-behavior note for each low-level symbol. | Added generated `expected_behavior_from_code` to `pokrov-symbol-coverage-audit.csv`, with tier-specific behavior-preservation wording that does not convert manual/review buckets into false proof; added a guard requiring the field for every symbol. | Targeted generator/summary guards: `4 passed`; focused tracker/inventory/manifest pack: `33 passed`; that pass generated inventory and symbol coverage with `4577` rows and `4577` expected-behavior notes. |
| STORY-RETEST-PROOF-001 | `closed` | per-story retest proof | Story rows had `evidence_tier`, `has_pass_result`, and `owner_gate`, but no single generated status that separated local direct retest proof from owner-only gates. | Added `retest_proof_status` to `pokrov-story-test-evidence-audit.csv` and a guard requiring every non-manual story to be `direct_test_ref_passed` while the manual owner row remains `manual_owner_gate_open`. | Targeted retest proof guards: `2 passed`; current story evidence has `522` `direct_test_ref_passed`, `1` `manual_owner_gate_open`, and `0` weak/stale/imported/textual proof buckets. |
| DEFECT-FIX-RETEST-LEDGER-001 | `closed` | defect fix retest ledger | Defects and discrepancies were documented in canonical tracker rows and findings, but there was no generated ledger that listed only the affected stories with fix status, retest status, proof refs, and closure status. | Added `pokrov-defect-fix-retest-ledger.csv` / `.md` plus `scripts/generate_defect_fix_retest_ledger.py`; added guards for row parity with canonical `defects_or_issues`, summary counts, closure status, proof refs, and generator reproducibility. | Targeted defect ledger guards `3 passed`; focused tracker/inventory/manifest pack `37 passed`; current ledger has `18` rows, `16` `closed_retested`, `2` `closed_retested_no_product_change`, `0` weak/open closure rows, and all rows have `direct_test_ref_passed`. |
| OPEN-QUESTIONS-LEDGER-001 | `closed` | owner-question tracking | The owner questions existed only in the canonical tracker Markdown table, so blocking questions could drift from completion audit status. | Added `pokrov-open-questions.csv` / `.md` with `blocks_goal_completion`, default assumptions, required owner answers, actions, and source refs; added a pytest guard for Q-001 through Q-004, source refs, blocking count, and links from tracker/completion audit. | `python -m pytest tests/test_story_test_evidence_audit.py::test_open_questions_ledger_tracks_owner_blockers -q --basetemp .tmp/pytest-open-questions-targeted`: `1 passed`. |
| DOC-NAV-001 | `closed` | developer navigation drift | The canonical tracker sidecars, owner-gated ledgers, and open-question ledgers existed but were not discoverable from the top-level developer navigation docs. | Linked the audit artifact set from `docs/README.md`, `docs/developer/repository-map.md`, and `docs/developer/developer-guide.md`, and added a pytest guard that requires every canonical audit sidecar to exist and remain linked from repository-map/developer navigation. | `python -m pytest tests/test_story_test_evidence_audit.py tests/test_code_function_inventory.py tests/test_check_script_manifest.py -q --basetemp .tmp/pytest-doc-navigation-focused`: `18 passed`. |
| GENERATED-ARTIFACT-REPRO-001 | `closed` | generated artifact reproducibility | The audit generators could be run manually, but focused tests did not prove that the checked-in canonical generated CSVs were byte-for-byte reproducible from current source/tracker inputs. | Added reproducibility guards that regenerate story evidence, entrypoint-story coverage, defect/fix/retest ledger, low-level code inventory, and source-symbol coverage into temp files and compare them with the canonical CSV/Markdown artifacts. | `python -m pytest tests/test_story_test_evidence_audit.py::test_generated_story_evidence_artifacts_match_canonical_files -q --basetemp .tmp/pytest-story-repro-single`: `1 passed`; `python -m pytest tests/test_code_function_inventory.py::test_generated_code_inventory_artifacts_match_canonical_files -q --basetemp .tmp/pytest-code-repro-single`: `1 passed`; defect/fix/retest ledger reproducibility is now guarded by `test_generated_defect_fix_retest_ledger_matches_canonical_files`. |
| SOURCE-LINE-REF-001 | `closed` | source evidence freshness | Source refs with line numbers were only checked at file-path level, so a moved or shortened source file could leave stale `path:line` evidence in the canonical tracker without failing focused verification. | Added a guard that parses explicit `path:line` and `path:line,line,line` refs across the canonical tracker, owner-gated scenario/result ledgers, and open-question ledger, resolves repo/client paths, and fails on missing files or line numbers outside the current file. | `python -m pytest tests/test_story_test_evidence_audit.py::test_canonical_line_number_source_refs_are_in_bounds -q --basetemp .tmp/pytest-line-refs-single-fixed`: `1 passed`; current guard checks `352` line refs and finds `0` out-of-bounds refs. |
| MARKDOWN-SUMMARY-COUNTS-001 | `closed` | human-readable summary drift | Canonical generated CSV files were guarded, but Markdown summaries could drift from CSV counts after regeneration or evidence mapping changes. | Added summary-count guards for low-level inventory, source-symbol coverage, private-helper coverage, story evidence, defect/fix/retest ledger, and entrypoint coverage Markdown files. The guards parse summary tables and compare them to counts computed from the canonical CSV artifacts, including explicit zero review/missing buckets. | `python -m pytest tests/test_code_function_inventory.py::test_code_inventory_markdown_summary_matches_csv tests/test_code_function_inventory.py::test_symbol_coverage_markdown_summary_matches_csv -q --basetemp .tmp/pytest-inventory-summary-fixed`: `2 passed`; `python -m pytest tests/test_story_test_evidence_audit.py::test_story_evidence_markdown_summary_matches_csv tests/test_story_test_evidence_audit.py::test_entrypoint_coverage_markdown_summary_matches_csv -q --basetemp .tmp/pytest-story-summary-fixed`: `2 passed`; defect/private-helper summary guards are now included in completion evidence. |
| CANONICAL-TRACKER-SUMMARY-001 | `closed` | main tracker summary drift | The sidecar Markdown summaries were guarded, but the main `pokrov-canonical-feature-tracker.md` summary could still drift from the tracker and sidecar CSV artifacts. | Added a guard that checks the main tracker summary counts for subsystem/status totals, backend route status, script workflow status/category, low-level inventory, source-symbol coverage, story evidence, entrypoint inventory, and entrypoint coverage against the canonical CSV artifacts. | `python -m pytest tests/test_story_test_evidence_audit.py::test_canonical_tracker_markdown_summary_matches_csv_artifacts -q --basetemp .tmp/pytest-canonical-tracker-summary-parser-fixed`: `1 passed`. |
| OWNER-GATE-EXECUTION-GUIDE-001 | `closed` | owner-gated execution readiness | Q-004 had a scenario matrix and result ledger, but no owner-facing execution packet that translated each required gate into minimum evidence and result-ledger update rules. | Added `pokrov-owner-gated-execution-guide.md`, linked it from Q-004, owner-gated summary, canonical tracker, and developer navigation, and expanded the owner-gate guard so every gate ID, result-ledger field, status label, and first required-evidence phrase remains present in the guide. | `python -m pytest tests/test_story_test_evidence_audit.py::test_owner_gated_scenarios_are_explicit_and_resolvable -q --basetemp .tmp/pytest-owner-guide-targeted-fixed3`: `1 passed`. |
| COVERAGE-POLICY-GUIDE-001 | `closed` | coverage policy decision readiness | Q-001 had the low-level symbol inventory and coverage audit, but no owner-facing decision packet that separated current proven coverage from optional one-test-per-private-helper expansion. | Added `pokrov-coverage-policy-decision-guide.md`, linked it from Q-001, canonical tracker, and developer navigation, and expanded the open-question guard so the guide contains the three policy options and the private-helper test-matrix contract. | `python -m pytest tests/test_story_test_evidence_audit.py::test_open_questions_ledger_tracks_owner_blockers -q --basetemp .tmp/pytest-coverage-policy-question-fixed`: `1 passed`. |
| STORY-EVIDENCE-AUDIT-001 | `closed` | evidence classification | The canonical tracker did not distinguish direct automated file mappings from imported workbook pass evidence. | Added `pokrov-story-test-evidence-audit.csv`, a reusable auditor, and a unit test. | Latest regenerated audit has `523` rows, `522` direct file refs, `0` imported-pass rows without direct file refs, `1` manual owner gate, and `0` stale refs. |
| CLIENT-STORY-EVIDENCE-MAP-001 | `closed` | client evidence mapping | Non-manual POKROV client app imported rows still relied on retained workbook pass evidence even where Dart/Kotlin test files existed. | Added direct Dart/Kotlin test-file references to all 66 non-manual client rows and preserved the one physical-device/live gate as manual owner evidence. | `python scripts/audit_story_test_evidence.py` regenerated `331` direct file refs, `169` imported-pass rows, `1` manual owner gate, and `0` stale refs before the Telegram/WebApp/marketing mapping pass. |
| MARKETING-STORY-CONTRACT-001 | `closed` | marketing evidence mapping | Marketing rows had build/SEO/responsive command evidence, but most rows did not expose a direct pytest file reference in the canonical CSV. | Added `tests/test_marketing_story_contracts.py` to assert homepage navigation/mobile menu, public route/SEO/responsive scripts, checkout provider fallback/redeem/email flow, install/legal/machine files, and VPN/search-intent page contracts; mapped marketing rows to that and existing guardrail tests. | `python -m pytest tests/test_marketing_story_contracts.py -q --basetemp .tmp/pytest-marketing-story-contracts`: `4 passed`; full root `ROOT-PYTEST-004`: `720 passed, 62 warnings, 2 subtests passed`. |
| TELEGRAM-STORY-CONTRACT-001 | `closed` | Telegram evidence mapping | Telegram bot rows had source workbook pass evidence and focused bot tests, but did not expose direct per-row test-file references in the canonical CSV. | Added `tests/test_telegram_story_contracts.py` to assert all 57 Telegram story rows keep live `portal_bot/*.py` source refs and main/admin/support/feedback/legacy trigger contracts; mapped Telegram rows to it and existing bot/API/support tests. | `python -m pytest tests/test_telegram_story_contracts.py -q --basetemp .tmp/pytest-telegram-story-contracts`: `3 passed`; full root `ROOT-PYTEST-004`: `720 passed, 62 warnings, 2 subtests passed`. |
| WEBAPP-STORY-EVIDENCE-MAP-001 | `closed` | WebApp evidence mapping | WebApp/admin story rows referenced generic Playwright pack evidence but lacked direct e2e/API test-file refs in the canonical CSV. | Mapped cabinet rows to `webapp/e2e/cabinet-flow.spec.ts`, auth/linking rows to the specific auth specs, admin rows to `webapp/e2e/admin-gate.spec.ts`, and backend-backed rows to focused API tests. | `python scripts/audit_story_test_evidence.py` now reports `0` imported-pass rows; full root `ROOT-PYTEST-004` passed. |
| STORY-EVIDENCE-MAP-001 | `closed` | evidence hardening queue | Imported workbook story rows relied on retained workbook pass evidence without direct test-file references in the canonical CSV. | Mapped every non-manual imported story row to existing or newly added direct automated test files; retained the one owner-controlled client/device row as `manual_owner_gate`. | That mapping pass reported `500` direct file refs, `0` imported-pass rows, `1` manual owner gate, and `0` stale refs. |

## FLOW_STATE

```json
{
  "version": 1,
  "wo_id": "WO-001",
  "state": "executing",
  "ordinary_fix_cycles": 1,
  "same_class_without_mechanism_change": {},
  "findings": [
    {
      "id": "STORY-EVIDENCE-MAP-001",
      "status": "closed",
      "class": "evidence-hardening"
    },
    {
      "id": "CODE-FUNCTION-INVENTORY-004",
      "status": "closed",
      "class": "inventory-entrypoint-classification"
    },
    {
      "id": "ENTRYPOINT-COVERAGE-001",
      "status": "closed",
      "class": "entrypoint-evidence-mapping"
    },
    {
      "id": "SOURCE-EVIDENCE-PATHS-001",
      "status": "closed",
      "class": "canonical-source-reference-drift"
    },
    {
      "id": "SYMBOL-COVERAGE-001",
      "status": "closed",
      "class": "literal-symbol-coverage"
    },
    {
      "id": "SCRIPT-MANIFEST-REVIEW-001",
      "status": "closed",
      "class": "script-status-triage"
    },
    {
      "id": "REMOTE-POSTGRES-CLI-001",
      "status": "closed",
      "class": "script-logic-safety"
    },
    {
      "id": "SOURCE-MODULE-COVERAGE-001",
      "status": "closed",
      "class": "symbol-evidence-precision"
    },
    {
      "id": "CLIENT-PLATFORM-SYMBOL-001",
      "status": "closed",
      "class": "client-platform-symbol-status"
    },
    {
      "id": "PUBLIC-SYMBOL-TRIAGE-001",
      "status": "closed",
      "class": "symbol-evidence-precision"
    },
    {
      "id": "CLIENT-PACKAGE-API-001",
      "status": "closed",
      "class": "symbol-evidence-precision"
    },
    {
      "id": "TRACKER-STATUS-HYGIENE-001",
      "status": "closed",
      "class": "tracker-status-hygiene"
    },
    {
      "id": "SOURCE-TRACKER-HYGIENE-001",
      "status": "closed",
      "class": "tracker-provenance-hygiene"
    },
    {
      "id": "OWNER-GATE-MATRIX-001",
      "status": "closed",
      "class": "manual-gate-decomposition"
    },
    {
      "id": "PRIVATE-INVENTORY-TIER-001",
      "status": "closed",
      "class": "symbol-evidence-precision"
    },
    {
      "id": "PRIVATE-HELPER-COVERAGE-001",
      "status": "closed",
      "class": "coverage-policy-decision-readiness"
    },
    {
      "id": "PRIVATE-HELPER-HIGH-RISK-001",
      "status": "closed",
      "class": "private-helper-behavior-coverage"
    },
    {
      "id": "TELEGRAM-WEBAPP-BOOTSTRAP-001",
      "status": "closed",
      "class": "webapp-telegram-ux-coverage"
    },
    {
      "id": "CLIENT-WINDOWS-TRAY-001",
      "status": "closed",
      "class": "client-private-helper-behavior-coverage"
    },
    {
      "id": "WEBAPP-SERVE-EXPORT-001",
      "status": "closed",
      "class": "webapp-operator-helper-coverage"
    },
    {
      "id": "CLIENT-FEATURE-LABELS-001",
      "status": "closed",
      "class": "client-feature-label-helper-coverage"
    },
    {
      "id": "WEBAPP-QA-OVERLAY-001",
      "status": "closed",
      "class": "webapp-qa-tooling-ux-coverage"
    },
    {
      "id": "CLIENT-NAVIGATION-SHELL-001",
      "status": "closed",
      "class": "client-navigation-shell-helper-coverage"
    },
    {
      "id": "CLIENT-FIRST-LAUNCH-STORE-001",
      "status": "closed",
      "class": "client-first-launch-storage-coverage"
    },
    {
      "id": "CLIENT-SHARED-SHELL-WIDGETS-001",
      "status": "closed",
      "class": "client-shared-shell-widget-coverage"
    },
    {
      "id": "CLIENT-SIDEBAR-INFO-SHEET-001",
      "status": "closed",
      "class": "client-sidebar-info-sheet-coverage"
    },
    {
      "id": "CLIENT-APP-SHELL-IMPLEMENTATION-001",
      "status": "closed",
      "class": "client-app-shell-implementation-helper-coverage"
    },
    {
      "id": "SOURCE-EVIDENCE-CONCRETE-001",
      "status": "closed",
      "class": "canonical-source-reference-precision"
    },
    {
      "id": "SYMBOL-EXPECTED-BEHAVIOR-001",
      "status": "closed",
      "class": "low-level-symbol-expected-behavior"
    },
    {
      "id": "STORY-RETEST-PROOF-001",
      "status": "closed",
      "class": "per-story-retest-proof"
    },
    {
      "id": "DEFECT-FIX-RETEST-LEDGER-001",
      "status": "closed",
      "class": "defect-fix-retest-ledger"
    },
    {
      "id": "OPEN-QUESTIONS-LEDGER-001",
      "status": "closed",
      "class": "owner-question-tracking"
    },
    {
      "id": "DOC-NAV-001",
      "status": "closed",
      "class": "developer-navigation-drift"
    },
    {
      "id": "GENERATED-ARTIFACT-REPRO-001",
      "status": "closed",
      "class": "generated-artifact-reproducibility"
    },
    {
      "id": "SOURCE-LINE-REF-001",
      "status": "closed",
      "class": "source-evidence-freshness"
    },
    {
      "id": "MARKDOWN-SUMMARY-COUNTS-001",
      "status": "closed",
      "class": "human-readable-summary-drift"
    },
    {
      "id": "CANONICAL-TRACKER-SUMMARY-001",
      "status": "closed",
      "class": "main-tracker-summary-drift"
    },
    {
      "id": "OWNER-GATE-EXECUTION-GUIDE-001",
      "status": "closed",
      "class": "owner-gated-execution-readiness"
    },
    {
      "id": "COVERAGE-POLICY-GUIDE-001",
      "status": "closed",
      "class": "coverage-policy-decision-readiness"
    }
  ],
  "next_action": "continue-next-story-test-fix-retest-loop",
  "stop_reason": null
}
```

## Residual Risk

- The literal helper/class-method inventory now has symbol coverage tiers, and the current private-helper matrix has `6` low-risk private inventory-only rows. Q-001 is answered as `ACCEPT_STORY_AND_SYMBOL_TIERS`; future stricter one-test-per-helper coverage requires a new owner decision.
- `pokrov-coverage-policy-decision-guide.md` and `pokrov-private-helper-coverage.csv` now give Q-001 an owner-facing decision packet and current private-helper baseline under the accepted policy.
- `private_inventory_only` is guarded as a private non-entrypoint tier; it is not a hidden public/entrypoint review bucket.
- Generic `public_symbol_review` and `client_package_public_api_review` are now `0`; remaining stronger runtime claims still require manual-gate/platform/provider evidence where the audit labels them as such.
- `SCRIPT-MANIFEST-REVIEW-001` is closed locally: every detected script CLI `main()` now has active/deprecated/archive/denylist status, and active rows have direct test refs.
- No non-manual imported story row remains without a direct test-file reference. The one remaining `manual_owner_gate` is an owner-controlled client/device/live verification gate, not a local evidence-mapping gap.
- No source entrypoint currently remains without route/story/script evidence mapping. This does not convert local tests into live Telegram/provider/device/RU-origin proof.
- No canonical `source_tracker` value currently remains unresolved; generated backend/script labels are backed by current source files and guarded in pytest.
- `CLIENT_APP-US-067` is now decomposed into 8 owner-gated scenarios with required evidence, allowed result labels, required-for-completion classification, and matching latest-result/fix/retest ledger rows. After the 2026-06-28 owner skips, 2 required scenarios remain open: real Telegram WebApp/session and live deployed app-session proof.
- `pokrov-owner-gated-execution-guide.md` now gives Q-004 an owner-facing execution packet, but it does not replace actual device/provider/deploy/RU evidence.
- Current-origin partial artifacts prove only that public marketing/cabinet/API/checkout hosts returned `200`, public email runtime config passed, provider catalog exposes Lava.top, and authenticated/live probes remain access-gated without owner inputs; they do not close live deploy, real app-session, brain-origin, device, payment maturity, provider dashboard, `connect.pokrov.space` token behavior, or RU-origin gates.
- Open questions are now tracked in a CSV ledger; Q-001 is answered, and Q-004 remains blocking full-goal completion until the remaining Telegram/live-deploy gates are executed, skipped, blocked, or owner-attested with evidence.
- `CLIENT_APP-US-067` is the remaining explicit `Manual owner test` row. The owner skipped Android, Windows, payment maturity, signing/store, and RU-origin gates for this audit; brain-origin signed runtime app-download smoke and brain deploy-state passed on 2026-06-28. Real Telegram WebApp/session evidence is `BLOCKED_BY_ACCESS` without a callable desktop-control tool, and current-origin live app-session/owner deploy approval still remain before Q-004 can close.
- `COMPLETION-AUDIT.md` currently classifies the local repo audit as materially advanced but not a full goal completion while owner-only gates remain open.
- Canonical source-evidence file refs and explicit `path:line` bounds are now guarded locally; semantic line freshness is still a lighter-weight aid than behavior proof and should be refreshed when touched.
- Existing XLSX files are treated as source audit artifacts. The CSV/Markdown tracker is the ongoing status source unless the owner wants binary workbook status to be canonical.
- Live/device/provider/RU checks are not inferred from this inventory and must be recorded separately when tested.
- No active script/operator workflow remains as a local scenario-test gap. Live SSH/provider/device/RU execution evidence remains owner-gated and should be recorded separately when performed.
