# POKROV Full Client Build Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Built-in subagents are disallowed for this project run; use OpenCode consilium only for external review. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the current Android/Windows MVP shell into a production-oriented POKROV client path with app-first account recovery, unified code redemption, cabinet handoff, support chat, bonus flows, routing controls, and release-ready build evidence.

**Architecture:** The backend remains the product authority. The Flutter client consumes app-first contracts and keeps advanced transport features behind backend-owned feature flags. Hiddify-core/WARP work is staged after the account, redeem, support, and profile contracts are proven.

**Tech Stack:** FastAPI, SQLAlchemy, pytest, Flutter/Dart, app_shell package, Android shell, Windows shell, OpenCode consilium.

---

## Source Of Truth

- Root platform repo: `C:/Users/kiwun/Documents/ai/VPN`.
- Active client repo: `C:/Users/kiwun/Documents/ai/POKROV-app`.
- Canonical root docs: `AGENTS.md`, `docs/product/portal-vpn-product.md`, `docs/architecture/app-first-and-bonus-flows.md`, `docs/architecture/system-overview.md`.
- Canonical client docs: `C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md`, `docs/product/client-product-contract.md`, `docs/implementation/2026-06-03-client-build-readiness-and-api-plan.md`, `docs/implementation/client-release-backlog.md`.
- OpenCode consilium packet: `C:/Users/kiwun/Documents/ai/VPN/.tmp/consilium/2026-06-03-full-build-packet.md`.

## Consilium Cadence

- Run OpenCode consilium before each major production slice.
- Use `opencode.cmd`, not `opencode` and not `E:/OpenCode/OpenCode.exe`.
- Temporary owner override (`2026-06-03`): use Fireworks provider models for consilium instead of the `opencode-go` lane until the owner switches routing back.
- Current Fireworks consilium set: `fireworks-ai/accounts/fireworks/models/deepseek-v4-pro`, `fireworks-ai/accounts/fireworks/models/glm-5p1`, `fireworks-ai/accounts/fireworks/models/kimi-k2p6`, `fireworks-ai/accounts/fireworks/models/qwen3p6-plus`, and `fireworks-ai/accounts/fireworks/models/minimax-m2p7`.
- Fast/taste fallback: `fireworks-ai/accounts/fireworks/routers/kimi-k2p6-turbo`.
- Never print API keys, bearer tokens, auth config, or raw request headers.
- Treat model output as critique only. Repo canon and tests decide.

## Files Planned For The First Production Slice

- Modify: `portal_bot/api.py`
  - Add app-facing `UnifiedRedeemIn` and `ClientCabinetTokenIn` models.
  - Add `POST /api/redeem` as a single app-facing code entry.
  - Add `POST /api/client/cabinet-token` for short-lived cabinet continuation.
  - Add `POST /api/auth/cabinet-handoff/exchange` for one-time webapp exchange.
  - Reuse existing promo, gift, access-key, dashboard, and auth helpers instead of duplicating business rules.
- Modify: `portal_bot/web_auth_service.py`
  - Add optional short TTL and purpose fields to web session tokens, if required by the cabinet token contract.
- Modify: `portal_bot/tests/test_app_first_api.py`
  - Add app-session tests for `/api/redeem`.
  - Add app-session tests for `/api/client/cabinet-token`.
- Modify later: `C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/lib/app_first_runtime_bootstrap.dart`
  - Add runtime methods for unified redeem and cabinet token.
- Modify later: `C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/lib/app_shell.dart`
  - Make the account/code entry use the native app contract instead of opening an external redeem page.
  - Make cabinet open through a short-lived token when the backend supports it.
- Modify docs:
  - `docs/architecture/app-first-and-bonus-flows.md`
  - `C:/Users/kiwun/Documents/ai/POKROV-app/docs/implementation/2026-06-03-client-build-readiness-and-api-plan.md`
  - `C:/Users/kiwun/Documents/ai/POKROV-app/docs/implementation/client-release-backlog.md`

## Task 1: Backend Unified Redeem Contract

**Files:**
- Modify: `portal_bot/api.py`
- Test: `portal_bot/tests/test_app_first_api.py`

- [x] **Step 1: Write failing tests**

Add tests that start an app trial, create a plan access key, call `POST /api/redeem` with `Authorization: Bearer <session_token>`, and assert:

```python
assert response.status_code == 200
body = response.json()
assert body["ok"] is True
assert body["kind"] == "access_key"
assert body["result"]["access"]["access_state"]
assert body["result"]["provisioning"]["managed_profile_path"] == "/api/client/profile/managed"
```

Add a second test for raw subscription links:

```python
response = client.post(
    "/api/redeem",
    headers={"Authorization": f"Bearer {token}"},
    json={"code": "https://connect.pokrov.space/sub/example"},
)
assert response.status_code == 400
assert response.json()["detail"]["code"] == "subscription_link_not_redeem_code"
```

- [x] **Step 2: Verify tests fail**

Run:

```powershell
python -m pytest portal_bot/tests/test_app_first_api.py::test_app_session_can_redeem_access_key_through_unified_endpoint portal_bot/tests/test_app_first_api.py::test_unified_redeem_rejects_subscription_links -q
```

Expected: both tests fail because `/api/redeem` does not exist.

- [x] **Step 3: Implement the endpoint**

Implement `UnifiedRedeemIn` and `POST /api/redeem` in `portal_bot/api.py`.

Rules:

- require `_require_auth_user`;
- rate-limit with the existing access-key redeem scope for authenticated users;
- reject URLs and raw subscription links with a structured `400`;
- normalize code safely without logging the raw code;
- for this slice, support access keys through the same logic as `/api/access-keys/redeem`;
- return an envelope with `ok`, `kind`, `code_preview`, and `result`.

- [x] **Step 4: Run focused tests**

Run:

```powershell
python -m pytest portal_bot/tests/test_app_first_api.py::test_app_session_can_redeem_access_key_through_unified_endpoint portal_bot/tests/test_app_first_api.py::test_unified_redeem_rejects_subscription_links -q
```

Expected: pass.

## Task 2: Short-Lived Cabinet Token Contract

**Files:**
- Modify: `portal_bot/web_auth_service.py`
- Modify: `portal_bot/api.py`
- Test: `portal_bot/tests/test_app_first_api.py`

- [x] **Step 1: Write failing tests**

Add a test that starts an app trial, calls `POST /api/client/cabinet-token`, and asserts:

```python
assert response.status_code == 200
body = response.json()
assert body["ok"] is True
assert body["expires_in"] <= 120
assert body["token"]
assert body["handoff_url"].startswith("https://app.pokrov.space/")
assert "handoff_token=" in body["handoff_url"]
```

Then call `/api/auth/session` with that handoff token and assert it is rejected:

```python
session = client.get("/api/auth/session", headers={"Authorization": f"Bearer {body['handoff_token']}"})
assert session.status_code == 401
assert session.headers["x-pokrov-auth-error"] == "web_session_exchange_required"
```

Add an unsafe target-path test:

```python
response = client.post(
    "/api/client/cabinet-token",
    headers={"Authorization": f"Bearer {token}"},
    json={"target_path": "https://evil.example/"},
)
assert response.status_code == 400
```

- [x] **Step 2: Verify tests fail**

Run:

```powershell
python -m pytest portal_bot/tests/test_app_first_api.py::test_app_session_can_request_short_lived_cabinet_token portal_bot/tests/test_app_first_api.py::test_cabinet_token_rejects_external_target_path -q
```

Expected: fail because `/api/client/cabinet-token` does not exist or token TTL cannot be customized.

- [x] **Step 3: Implement token support**

Extend `create_web_session_token` with optional keyword-only parameters:

```python
ttl_seconds: int | None = None
purpose: str | None = None
```

Clamp custom TTL to `60..120` seconds for cabinet handoff. Include `purpose` in the signed payload and make `inspect_web_session_token` return it.

- [x] **Step 4: Implement endpoint**

Add `ClientCabinetTokenIn` and `POST /api/client/cabinet-token` in `portal_bot/api.py`.

Rules:

- require app/web auth through `_require_auth_user`;
- allow only relative target paths;
- default target path `/`;
- return `token`, `expires_in`, `handoff_url`, `target_path`, `auth_origin`, and `scope`;
- do not return subscription URLs or control-panel secrets.

- [x] **Step 5: Run focused tests**

Run:

```powershell
python -m pytest portal_bot/tests/test_app_first_api.py::test_app_session_can_request_short_lived_cabinet_token portal_bot/tests/test_app_first_api.py::test_cabinet_token_rejects_external_target_path -q
```

Expected: pass.

## Task 2B: One-Time Webapp Cabinet Exchange

**Files:**
- Modify: `portal_bot/models.py`
- Modify: `portal_bot/migrations.py`
- Modify: `portal_bot/api.py`
- Modify: `webapp/src/lib/api.ts`
- Modify: `webapp/src/lib/session.tsx`
- Test: `portal_bot/tests/test_app_first_api.py`
- Test: `webapp/e2e/cabinet-flow.spec.ts`

- [x] **Step 1: Write failing tests**

Add tests proving that:

- `POST /api/client/cabinet-token` returns `handoff_token`;
- direct `/api/auth/session` use of that handoff token fails with `web_session_exchange_required`;
- `POST /api/auth/cabinet-handoff/exchange` returns a normal browser session token;
- replaying the same handoff token returns `409` with `cabinet_handoff_already_used`;
- exchange endpoint rate-limits with `scope=cabinet_handoff_exchange`;
- webapp consumes `handoff_token`, stores the exchanged browser session, removes the URL token, honors safe `target_path`, and shows localized copy for reused/expired/invalid/rate-limited handoffs.

- [x] **Step 2: Implement DB-backed exchange**

Add `web_cabinet_handoff_tokens` with `token_hash`, `tg_id`, `target_path`, `expires_at`, `used_at`, and `created_at`.

- [x] **Step 3: Wire webapp bootstrap**

Make `PortalSessionProvider` consume `handoff_token` before legacy `web_session_token` fallback.

- [x] **Step 4: Add failure UX and ledger retention**

Map backend handoff errors to `copy/catalog.ru.json`, keep an in-flight exchange guard, navigate to returned safe `target_path`, and clean old expired handoff ledger rows through `CABINET_HANDOFF_LEDGER_RETENTION_SECONDS`.

- [x] **Step 5: Run focused verification**

Run focused backend pytest, migration tests, webapp cabinet e2e, and app shell tests.

## Task 3: Client Runtime Adapter For Redeem And Cabinet Handoff

**Files:**
- Modify: `C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/lib/app_first_runtime_bootstrap.dart`
- Modify: `C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/app_first_runtime_bootstrap_test.dart`

- [x] **Step 1: Add failing adapter tests**

Add tests with a fake HTTP client proving that:

```dart
final result = await runtime.redeemCode('POKROV-ACCESS-2026');
expect(result.kind, 'access_key');
expect(result.ok, isTrue);
```

and:

```dart
final handoff = await runtime.createCabinetHandoff(targetPath: '/profile');
expect(handoff.expiresIn.inSeconds, lessThanOrEqualTo(120));
expect(handoff.handoffUrl.host, 'app.pokrov.space');
```

- [x] **Step 2: Implement adapter methods**

Add methods that reuse the persisted app session token and call:

- `POST /api/redeem`
- `POST /api/client/cabinet-token`

- [x] **Step 3: Run package tests**

Run:

```powershell
flutter test
```

from `C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell`.

Expected: pass.

## Task 4: Client Account UX Simplification

**Files:**
- Modify: `C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/lib/app_shell.dart`
- Modify: `C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart`

- [x] **Step 1: Simplify account screen content**

Keep first-layer account copy to:

- access status;
- previous-user code entry;
- Telegram bonus;
- cabinet/email actions;
- devices/support.

Move long explanations into dialogs or support.

- [x] **Step 2: Make code entry native**

Use the runtime adapter for code entry. Show success states with access days/status and refresh dashboard/profile after redemption.

- [x] **Step 3: Make cabinet handoff use token**

When the adapter returns a handoff URL, open it. If the endpoint is unavailable, fall back to the public cabinet URL with a degraded state message.

- [x] **Step 4: Run widget tests**

Run:

```powershell
flutter test test/pokrov_seed_app_test.dart
```

Expected: pass.

## Task 5: Support Chat Production Slice

**Files:**
- Modify: `portal_bot/api.py` only if ticket polling/reply contracts are missing.
- Modify: `C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/lib/app_first_runtime_bootstrap.dart`
- Modify: `C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/lib/app_shell.dart`
- Modify tests in both repos.

- [x] **Step 1: Confirm ticket endpoints**

Use `rg -n "/api/tickets|ticket" portal_bot/api.py portal_bot/tests tests`.

- [x] **Step 2: Add client polling/reply adapter tests**

Assert the native support chat can:

- create a ticket;
- list ticket messages;
- send another message;
- attach only redacted diagnostics.

- [x] **Step 3: Implement chat adapter and UI states**

Keep support Telegram-centric internally, but app UX must be an in-app chat window.

- [x] **Step 4: Run backend and client tests**

Run focused pytest and Flutter package tests.

## Task 6: Bonuses And Telegram Link Slice

**Files:**
- Modify app runtime/UI and docs. Modify backend only when a summary endpoint is missing.

- [x] **Step 1: Add `GET /api/client/bonuses/summary` only if existing `/api/bonuses` and dashboard data cannot support the app view.**

Fireworks consilium and local API inspection agreed that a new summary endpoint
is not needed for this slice. The client uses the existing
`/api/client/telegram/link`, `/api/channel/subscriber/check`, and
`/api/bonuses/channel/claim` contracts.

- [x] **Step 2: Keep wheel/calendar hidden behind feature flags.**

Widget regression now asserts roulette and activity-calendar actions are absent
from the MVP profile tree.

- [x] **Step 3: Wire Telegram `+10 days` status and redeem button into the account/profile screen.**

Profile/Account now has stateful Telegram reward rows for backend-generated bot
link, channel check, and `+10 days` claim.

- [x] **Step 4: Prove bonus state with tests.**

Verified with app-shell adapter/widget tests and focused backend API tests for
Telegram link, read-only subscriber check, and channel bonus claim.

## Task 7: Routing, Smart Connect, And WARP Staging

**Files:**
- Modify app runtime/UI, then runtime_engine only after core proof.

- [x] **Step 1: Keep route modes backend-owned and visible as simple choices.**

Public app route choices now remain simple: `Все, кроме РФ` and
`Все устройство`. Low-level selected-apps route-policy plumbing remains tested,
but it is no longer exposed as a selectable public mode.

- [x] **Step 2: Add selected-apps UI only when OS enforcement is proven per platform.**

Current MVP keeps `Приложения · Скоро` as a staged row only. Android/Windows
still have the technical capability flag, but `RouteMode.selectedApps` is not
in public `supportedRouteModes` until package/process picker, persistence, and
OS-level enforcement proof exists.

- [x] **Step 3: Keep WARP on the main screen as a disabled/explained feature until Hiddify-core WARP proof exists.**

Home keeps the WARP/enhanced privacy tile as disabled/info-only and widget
regression now verifies tapping it opens copy that says WARP is not active and
does not expose a toggle.

Additional staging landed: managed-profile bootstrap parses backend
`smart_connect` metadata into passive client metadata, without UI balancer
claims or RTT upload.

- [ ] **Step 4: After Hiddify-core proof, integrate WARP through the same managed-profile feature flag model.**

Still pending by evidence: active WARP requires runtime proof, backend profile
policy, safe account/config storage, Android/Windows failure-mode tests, and
support diagnostics.

## Task 8: Verification And Release Evidence

**Files:**
- Modify release docs and evidence notes after actual verification.

- [x] **Step 1: Run root backend focused tests.**

```powershell
python -m pytest portal_bot/tests/test_app_first_api.py -q
python -m pytest tests/test_api_auth_and_tickets.py -q
```

Fresh `2026-06-03` run:

- `portal_bot/tests/test_app_first_api.py`: `18 passed`
- `tests/test_api_auth_and_tickets.py`: `65 passed`
- pytest emitted a Windows atexit temp-cleanup `PermissionError` after
  `test_app_first_api.py`, but the command exited `0`.

- [x] **Step 2: Run client package and shell tests.**

```powershell
flutter analyze
flutter test
```

Run in:

- `C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell`
- `C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell`
- `C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell`

Fresh `2026-06-03` run:

- `packages/app_shell`: `flutter analyze` clean, `flutter test` `49 passed`
- `apps/android_shell`: `flutter analyze` clean, `flutter test` `4 passed`
- `apps/windows_shell`: `flutter analyze` clean, `flutter test` `2 passed`
- additional touched-package guards:
  - `packages/runtime_engine`: `flutter analyze` clean, `flutter test`
    `11 passed`
  - `packages/core_domain`: `dart analyze` clean

- [x] **Step 3: Build artifacts.**

```powershell
flutter build windows --release
flutter build apk --debug
```

Fresh `2026-06-03` run:

- `flutter build windows --release` built
  `apps/windows_shell/build/windows/x64/runner/Release/pokrov_windows_beta.exe`
  with `libcore.dll` present in the same release bundle
- `flutter build apk --debug` built
  `apps/android_shell/build/app/outputs/flutter-apk/app-debug.apk`
- Android build warnings remain follow-up work: Gradle `8.3.0`, Android Gradle
  Plugin `8.1.1`, Kotlin `1.8.22`, and SDK XML version mismatch

- [x] **Step 4: Update docs with exact claims only.**

Do not claim store release, trusted Windows signing, raw Android physical audit, RU-origin readiness, or production WARP until the evidence exists.

Fresh docs updated:

- `POKROV-app/docs/implementation/2026-06-03-client-mvp-shell-implementation.md`
- `POKROV-app/docs/implementation/client-release-backlog.md`
- `POKROV-app/docs/operations/cutover-readiness.md`

## Final Local Handoff Pack

After Task 8, a local non-public MVP handoff pack was retained at:

`C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/0.2.0-beta.1+20260603-local-mvp/`

Included:

- Android debug APK smoke artifact
- Windows unsigned setup EXE
- Windows portable ZIP
- Windows packaging manifest
- `SHA256SUMS.txt`
- `README.md`
- `release-handoff.json`

Verified:

- every hash in `SHA256SUMS.txt` matches the retained file
- `release-handoff.json` parses as JSON
- `release_state=local_engineering_handoff_not_public_release`
- `runtime_sync_allowed=false`

This pack is the final local engineering handoff for inspection/testing only.
It is not store readiness, trusted Windows signing, raw Android audit proof,
RU-origin readiness, public hosting approval, or production WARP proof.

## Task 9: Staged Local Release Candidate

**Files:**
- Update release docs and retained handoff artifacts after exact-candidate
  builds.

- [x] **Step 1: Run client release preflight.**

```powershell
python scripts/run_client_release_gate.py preflight
```

Fresh `2026-06-04` run passed.

- [x] **Step 2: Build Android release-smoke artifacts.**

```powershell
python scripts/run_client_release_gate.py build --target android-apk
python scripts/run_client_release_gate.py build --target android-aab
```

Fresh `2026-06-04` run built:

- `apps/android_shell/build/app/outputs/flutter-apk/app-release.apk`
- `apps/android_shell/build/app/outputs/bundle/release/app-release.aab`

These remain internal beta/release-smoke artifacts until production signing and
physical-device release audit gates are green.

- [x] **Step 3: Rebuild Windows unsigned beta package.**

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-windows-release.ps1 -SyncRuntime -SkipTests -SkipAnalyze
```

Fresh `2026-06-04` run produced the unsigned setup EXE, portable ZIP, and
manifest under `apps/windows_shell/build/release_bundle/`.

- [x] **Step 4: Retain and verify local RC pack.**

Retained at:

`C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/0.2.0-beta.1+20260604-rc-local/`

Verified:

- `SHA256SUMS.txt` matches every retained file
- `release-handoff.json` parses as JSON
- Windows manifest parses as JSON
- `release_state=local_release_candidate_not_public_release`
- `runtime_sync_allowed=false`

- [ ] **Step 5: Operator public-release gates.**

Still manual or blocked by external access:

- Android physical-device release-build localhost/control-surface audit
- public artifact upload and public download smoke
- live `/api/client/apps` handoff smoke
- real-user Telegram/WebApp check
- RU-origin probe when RU reachability is claimed
- runtime `APP_*` sync approval

Owner decision on `2026-06-04`: production Android signing and trusted Windows
signing are accepted skips for the current `0.2.0-beta.1` outside-store beta.
This does not authorize store, trusted-signing, SmartScreen reputation, or
stable-release claims.

GitHub prerelease upload on `2026-06-04`:

- `v0.2.0-beta.1` was refreshed with `pokrov-android-universal.apk` and
  `pokrov-windows-setup-x64.exe`
- current-origin range smoke returned `206` for both public asset URLs
- `gh release download` returned files whose SHA-256 values match the local RC
- brain-origin `/api/client/apps` smoke passed; runtime `APP_*` mutation was not
  required because URLs stayed stable
- public-beta external-access preflight passes publication policy and runtime
  checks, but remains `BLOCKED_BY_ACCESS` for missing email/Lava live probe env

## Current Execution Choice

Inline execution is selected for this run because the owner explicitly requested immediate full-build progress and prohibited built-in subagents. OpenCode consilium remains the review lane.
