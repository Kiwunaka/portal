# R08 Security, Privacy, Abuse, Compliance Research

Date: 2026-04-26
Worktree: `C:/Users/kiwun/.config/superpowers/worktrees/VPN/open-beta-v4`
Client worktree: `C:/Users/kiwun/.config/superpowers/worktrees/POKROV-app/open-beta-v4`
Role: R08, POKROV Open Beta v4 research wave

## Executive Summary

No confirmed P0 issue was found in this static research pass. The main launch risks are P1 privacy and abuse-control gaps around beta support uploads, local client secrets, payment callback payload retention, callback abuse throttling, and browser session-token handling.

The strongest existing controls are good: secret files are excluded by `.gitignore`, canonical docs prohibit secret exposure, payment callbacks verify provider signatures before fulfillment, FreeKassa also has an IP allowlist path, admin APIs consistently route through `_require_admin`, public beta auth/access/support endpoints have rate limits, and Telegram WebApp init data is HMAC-verified.

The beta release should still treat security readiness as incomplete until these gaps are closed: support attachments should not be public static files, app session tokens should not be stored as plaintext JSON, provider callback payloads and provider error bodies should be redacted/minimized, payment callback endpoints need abuse throttles, and the Android release-build localhost/control-surface audit remains a hard public-release gate. I did not run verification commands in this pass because the assigned output scope allows writing only this report file.

## Evidence Table

Allowed labels: `confirmed`, `probable`, `unknown`, `needs local run`, `blocked by missing access`, `deferred`.

| Evidence | Label | What it proves | What it does not prove |
| --- | --- | --- | --- |
| `AGENTS.md`, `docs/operations/deployment-and-access.md`, and `docs/operations/publishing-and-signing-guide.md` | confirmed | Secret locations and release reports must not print secret values; Android public release is blocked until the localhost/control-surface audit is green. | Whether production runtime logs and DB rows are currently redacted. |
| Platform `.gitignore` | confirmed | `.env`, nested `.env.*`, SSH key folders, merchant secrets, `ops-local/`, x-ui DB backups, local DBs, caches, and external client fork paths are excluded. | Whether historical commits or artifact bundles contain secrets. |
| Client `.gitignore` | confirmed | Flutter/build outputs, `config/local/*`, and runtime artifact cache are excluded. | Whether client app support directories or release artifacts contain raw runtime config after install. |
| `.env.example` | confirmed | Secret names are documented as placeholders only; payment callback tolerant mode defaults false. | It does not prove deployed env values are secret-manager backed or rotated. |
| `portal_bot/api.py:1422` | confirmed | Telegram WebApp init data is parsed and HMAC-verified using the bot token-derived WebApp secret. | It does not enforce `auth_date` freshness and uses ordinary string equality for this compare. |
| `portal_bot/api.py:2136` and `:2623` | confirmed | User auth accepts Telegram init data or web/app session bearer tokens; admin auth is gated by `_require_admin` and `ADMIN_ID`. | Single-admin policy may be too coarse for future beta operations. |
| `portal_bot/api.py:2186` and call sites at `:4379`, `:4464`, `:4740`, `:7035`, `:7060`, `:7250`, `:7273` | confirmed | Public beta auth, trial, access-key, ticket-create, and ticket-upload paths have per-minute in-process rate limits. | Multi-worker/restart durability and payment callback throttling are not covered. |
| `portal_bot/api.py:2825`, `:3246`, `:3284`, `:5323` | confirmed | Payment callback routes verify signatures, reject invalid signatures by default, and only apply paid access for non-duplicate signed `result` events with normalized `paid` status. | It does not prove invalid callbacks are cheaply throttled before body parsing and DB writes. |
| `portal_bot/api.py:3037`, `:3073`, `:3093` | confirmed | Raw provider callback payloads are stored in order/event JSON fields, truncated to 4k/16k. | It does not show field-level redaction/minimization of payer/provider data. |
| `portal_bot/payment_providers.py:176` and `:246` | confirmed | Provider create errors log up to the first 800 bytes of provider response bodies. | It does not prove those bodies cannot contain payer data, URLs, identifiers, or echoed secrets. |
| `portal_bot/api.py:1419`, `:3554`, `:3560`, `:3581`, `:7242` | confirmed | Support attachments are authenticated on upload, size-limited, name-sanitized, randomly named, and served from a FastAPI static mount. | URLs are public to anyone who obtains them; MIME checks are broad and no scan/magic-byte validation is evident. |
| `tests/test_api_auth_and_tickets.py` and `tests/test_api_payments_callbacks.py` | confirmed | Tests cover invalid Telegram signature rejection, admin guard, ticket upload behavior, invalid payment signature rejection, duplicate callback handling, and provider callback variants. | They do not cover upload malware/content sniffing, callback rate limits, payload redaction, or local client secret storage. |
| `webapp/src/lib/api.ts:1275`, `:1302`, `:1319`, `:1322` | confirmed | Web session tokens are stored in `localStorage`, sent as bearer and `X-Web-Auth-Token`, and can be consumed from URL query params. | It does not protect bearer tokens from XSS or pre-consumption URL/referrer exposure. |
| `webapp/src/app/(dashboard)/admin/layout.tsx:98` | confirmed | Admin UI checks `user.is_admin` client-side before showing admin routes. | Client-side checks are UX only; security depends on backend guards. |
| Client `packages/app_shell/lib/app_first_runtime_bootstrap.dart:259`, `:2297`, `:2307` | confirmed | App bootstrap persists `session_token` in JSON state using `writeAsString`. | It does not show platform secure storage for the app session token. |
| Client `packages/app_shell/lib/app_first_runtime_bootstrap.dart:367`, `:385`, `:405` | confirmed | Managed runtime config payload is fetched and materialized for runtime use. | No raw config print/debug output was found in this file, but file-system staging still carries sensitive routing material. |
| Client `apps/android_shell/.../RuntimeHostBridge.kt:143` and `:145` | confirmed | Android writes runtime `configPayload` to staged config files. | It does not prove file permissions, lifecycle cleanup, or support-export exclusion. |
| Client `apps/android_shell/.../PokrovRuntimeVpnService.kt:72`, `:133`, `:245` | confirmed | Android logs staged config paths and control-socket protection failures, not raw config content in the inspected lines. | Logcat may still expose local paths and runtime diagnostics; release log policy needs an explicit smoke check. |
| `marketing/src/app/privacy/page.tsx` and `marketing/src/app/offer/page.tsx` | confirmed | Legal pages exist and cover account/support/payment-provider concepts plus beta limitations. | They do not appear to enumerate client session tokens, local runtime config storage, observer/diagnostic retention, support attachment access model, or exact payment-provider data categories. |
| `docs/user/portal-vpn-user-guide-ru.md` | confirmed | User guide tells users not to send full configs, keys, secret links, topology, access links, or QR codes to support. | The product still needs technical enforcement so users cannot accidentally upload sensitive files into public static storage. |

## P0 Issues

No confirmed P0 issue was found in the inspected source and docs.

Release-gate note: Android public release remains blocked by the required physical-device localhost/control-surface audit. This is not a new R08 P0, but it is a standing public-release blocker that must stay visible in the beta handoff.

## P1 Issues

### P1-01: Support attachments are public static files after upload

Evidence: `portal_bot/api.py:1419` mounts `SUPPORT_UPLOAD_DIR` with `StaticFiles`; `api.py:7242` requires auth to upload but returns a file URL; `api.py:3560` accepts broad classes including any `image/*`, any `video/*`, `text/plain`, and `application/octet-stream`.

Risk: Support screenshots and diagnostics can contain access links, QR codes, app identifiers, emails, IPs, or payment evidence. Once uploaded, anyone with the random URL can fetch the file. Broad MIME acceptance also permits risky formats such as SVG or arbitrary binary content under the support host.

Required work: Move support files behind an authenticated download endpoint that checks ticket owner or admin role, bind uploads to a ticket before exposure, replace broad MIME checks with strict allowlists, reject SVG/HTML/scriptable content, validate magic bytes, add malware/content scanning where feasible, and add retention cleanup.

### P1-02: Client app session token is persisted as plaintext JSON state

Evidence: `packages/app_shell/lib/app_first_runtime_bootstrap.dart:259` writes JSON state; `:2297` serializes `session_token`; `:2307` restores it.

Risk: A local backup, debug pull, compromised desktop account, or rooted device can recover a bearer session token. That token can call user APIs and fetch managed config until expiry/revocation.

Required work: Store session tokens in platform secret storage: Android Keystore/EncryptedSharedPreferences and Windows DPAPI/Credential Locker. Keep non-secret state in the JSON file, rotate tokens on migration, and ensure support bundles and logs never include session token material.

### P1-03: Payment callback payloads and provider error bodies are over-retained

Evidence: `portal_bot/api.py:3037`, `:3073`, and `:3093` store callback payload JSON in order/event rows. `portal_bot/payment_providers.py:176` and `:246` log provider create error response bodies up to 800 bytes.

Risk: Callback payloads and provider error bodies can include payer identifiers, payment URLs, provider transaction IDs, signatures, card metadata fragments, emails, phone numbers, or other compliance-sensitive material. Storing and logging raw payloads expands breach impact and operator exposure.

Required work: Add a central redaction/minimization helper for payment payload storage and provider logs. Store allowlisted operational fields only, hash external identifiers where possible, remove signatures/tokens/payment URLs/payer contacts/card-like fields, and add regression tests that seeded sensitive keys are redacted from DB JSON and logs.

### P1-04: Payment callbacks have signature checks but no explicit abuse throttle

Evidence: beta rate limits exist for auth/trial/access-key/support paths, but no callback scope is visible at `/api/payments/result/{provider}`, `/refund/{provider}`, or `/chargeback/{provider}` before `_handle_payment_callback`.

Risk: Invalid callbacks should not grant access, but they can still consume request parsing, signature verification, DB event attempts, logging, and admin attention. Open beta increases the chance of callback endpoint probing.

Required work: Add shared rate limits for callbacks by provider, source IP, order hash, and invalid-signature count. Add request body size caps, cheap provider allowlist rejection before deeper parsing, invalid-signature circuit breakers, and alerts when callback failures spike.

### P1-05: Web session bearer tokens live in localStorage and URL query handoff

Evidence: `webapp/src/lib/api.ts:1319` stores web tokens in `localStorage`; `:1302` sends bearer auth; `:1322` consumes `web_session_token` or `web_session` from query params.

Risk: XSS can exfiltrate persistent bearer tokens. Query-token handoff can leak through browser history, screenshots, logs, extensions, and referrers before client-side cleanup runs.

Required work: Replace localStorage bearer persistence with an HttpOnly, Secure, SameSite cookie or a one-time handoff-code exchange that sets the cookie server-side. If bearer headers must remain for compatibility, shorten TTL, bind to device/session metadata, enforce CSP, and never put durable tokens in URLs.

## P2 Issues

### P2-01: Telegram WebApp init validation should enforce freshness and constant-time compare

Evidence: `portal_bot/api.py:1422` verifies the HMAC but does not check `auth_date`; the final comparison is `calculated_hash != check_hash`.

Risk: Replay windows are wider than necessary, and plain equality is weaker than the rest of the callback code that uses `hmac.compare_digest`.

Work: Use `hmac.compare_digest`, validate `auth_date` max age with a small configurable skew, and add tests for expired, missing, malformed, and valid init data.

### P2-02: Beta rate limiter is in-process only

Evidence: `_enforce_beta_rate_limit` is an in-memory dict. Current docs describe beta limits as in-process.

Risk: Multi-worker deployment, restart, or horizontal scale bypasses rate memory.

Work: Move open-beta public abuse scopes to Redis/Postgres-backed counters or an edge/WAF limiter, while preserving the local in-process fallback for development.

### P2-03: Client runtime logs and staged config paths need release-mode minimization

Evidence: Android logs staged config paths in `PokrovRuntimeVpnService.kt:72` and `:133`; app bootstrap builds runtime config payloads and sing-box log config exists in client seed/runtime paths.

Risk: No inspected line printed raw config, but release logcat and support exports can still reveal local config paths, runtime phases, network diagnostics, or control-socket details.

Work: Add a release log policy: default runtime logs disabled or warning-only, no raw config or profile URL logging, hash local path/profile IDs, and test logcat/support export for forbidden patterns.

### P2-04: Legal pages lag technical data inventory

Evidence: privacy/offer pages cover account/support/payment-provider concepts and beta limits, while docs/code show additional categories: app session token, runtime config staging, support attachment URLs, observer/diagnostic telemetry, Telegram linking, email auth, IP-derived abuse controls, and client logs.

Risk: Public privacy copy can be true but incomplete for beta operations.

Work: Update legal/copy after implementation decisions so it names high-level categories, purposes, retention, support attachment handling, payment-provider sharing, diagnostics/log minimization, and user removal/support contact paths without exposing implementation details.

### P2-05: Admin remains single-ID based

Evidence: `_is_admin_tg` authorizes only `Settings.ADMIN_ID`; admin UI checks `user.is_admin`.

Risk: This is simple and understandable for beta, but it does not provide role separation, emergency break-glass, or per-action approval for sensitive actions such as token rotation, refunds, node changes, campaign changes, and template edits.

Work: Keep single-admin acceptable for closed beta only. Before broader public operations, add role/permission tables, scoped audit, optional step-up confirmation for destructive actions, and admin session expiry.

## Proposed Implementation Work

1. Add authenticated support attachment storage and download.
   - Replace static mount with `/api/tickets/{ticket_id}/attachments/{media_file_id}`.
   - Check owner/admin, bind upload to ticket, generate short-lived admin/user download URLs if needed.
   - Strictly allow `image/png`, `image/jpeg`, `image/webp`, `application/pdf`, and optionally `text/plain`; reject SVG/HTML/scriptable types.
   - Add magic-byte detection, size limits per type, scanning hook, and retention cleanup.

2. Add payment redaction and callback abuse controls.
   - Implement `redact_payment_payload(provider, payload)` and use it for `ExternalOrder.meta_json`, `ExternalPaymentEvent.payload_json`, admin payload views, and provider error logs.
   - Add callback body-size cap and shared rate limits for invalid signatures by provider/IP/order hash.
   - Add tests with fake sensitive fields to prove no sensitive field is stored or logged.

3. Move web/app session secrets to safer storage.
   - Web: use HttpOnly Secure SameSite cookies or one-time handoff code exchange.
   - Android: use Keystore-backed encrypted storage for app session token.
   - Windows: use DPAPI/Credential Locker.
   - Add migration that removes plaintext `session_token` from app support JSON after moving it.

4. Harden Telegram and admin auth.
   - Use `hmac.compare_digest` and `auth_date` max-age validation for WebApp init data.
   - Keep backend admin guard mandatory on every admin route.
   - Add route inventory test that enumerates `/api/admin/*` routes and fails if any route lacks `_require_admin` or the shared admin dependency.

5. Add release privacy smoke checks.
   - Scan server logs, DB JSON payload fields, client logcat, client support exports, staged config directories, and generated release artifacts for forbidden patterns.
   - Keep the Android physical-device localhost/control-surface audit as a public-release blocker.

## Exact Verification Commands

Platform focused regression commands:

```powershell
Push-Location C:/Users/kiwun/.config/superpowers/worktrees/VPN/open-beta-v4
python -m pytest tests/test_api_auth_and_tickets.py -q
python -m pytest tests/test_api_payments_callbacks.py -q
python -m pytest tests/test_admin_payments_api.py -q
python -m pytest tests/test_app_first_api.py -q
python scripts/client_security_smoke.py
python scripts/release_gate_check.py --quick
npm.cmd --prefix webapp run build
npm.cmd --prefix webapp run test:e2e:admin
npm.cmd --prefix marketing run build
python scripts/check-links.py
Pop-Location
```

Client focused regression commands:

```powershell
Push-Location C:/Users/kiwun/.config/superpowers/worktrees/POKROV-app/open-beta-v4
powershell -ExecutionPolicy Bypass -File .\scripts\validate-seed.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1
Push-Location apps/android_shell
flutter test
Pop-Location
Push-Location packages/app_shell
flutter test
Pop-Location
Pop-Location
```

Android physical release-build gate:

```powershell
Push-Location C:/Users/kiwun/.config/superpowers/worktrees/VPN/open-beta-v4
$env:ANDROID_AUDIT_SERIAL="<physical-device-serial>"
python scripts/android_localhost_audit.py --serial $env:ANDROID_AUDIT_SERIAL --connect-wait-sec 30 --disconnect-wait-sec 15
Pop-Location
```

Manual redaction/smoke commands to add after implementation:

```powershell
Push-Location C:/Users/kiwun/.config/superpowers/worktrees/VPN/open-beta-v4
python -m pytest tests/test_payment_payload_redaction.py -q
python -m pytest tests/test_support_upload_security.py -q
python -m pytest tests/test_auth_route_inventory.py -q
python scripts/security_redaction_smoke.py --no-secrets --db-url $env:DATABASE_URL
Pop-Location
```

```powershell
Push-Location C:/Users/kiwun/.config/superpowers/worktrees/POKROV-app/open-beta-v4
flutter test packages/app_shell/test/session_secret_storage_test.dart
flutter test packages/app_shell/test/support_export_redaction_test.dart
Pop-Location
```

## Threat Model

Assets:

- Bot tokens, payment provider credentials, signing material, DB credentials, panel credentials.
- App/web session tokens, Telegram init data, email auth tokens, checkout tickets.
- Subscription URLs, managed runtime config, activation keys, QR/access links.
- Payment orders/events, provider transaction IDs, payer contact data, refund/chargeback data.
- Support ticket messages, uploaded attachments, client diagnostics, client logs.
- Admin API, node-management API, rollout configuration, payment reconciliation controls.

Actors:

- Anonymous internet users probing public endpoints.
- Authenticated beta users and app installs.
- Payment callback forgers or high-volume callback abusers.
- Upload abusers hosting malicious or private content.
- XSS/browser-extension attackers against the cabinet.
- Local malware or another user on the same Windows/Android device.
- Mistaken operators pasting secrets or raw configs into logs/docs/tickets.
- Compromised or over-broad admin session.

Trust boundaries:

- Browser/app to public API.
- Telegram WebApp/Login/OIDC to backend identity.
- Payment provider to callback endpoints.
- Support upload API to file storage/download path.
- Backend to database/logs/admin UI.
- Client app to local filesystem, logcat, runtime engine, and support export.
- Admin webapp to backend admin routes.

Primary failure modes:

- Secret value committed, logged, stored in DB JSON, or copied into support/legal docs.
- Forged or replayed callback/auth payload grants access or causes incident noise.
- Attachment or client logs expose raw config/access links.
- Browser or local-device compromise steals bearer session tokens.
- Admin route or UI action bypasses backend guard.

## Abuse Controls

Existing controls:

- Secret-bearing local files and directories are ignored by platform and client `.gitignore`.
- Telegram WebApp init data is HMAC-verified.
- Admin backend routes inspected route through `_require_admin`.
- Payment callbacks verify provider signatures and only apply paid access on signed paid result events.
- FreeKassa path includes provider-specific signature/IP checks.
- Public beta paths for auth, email auth, trial, access-key status/redeem, ticket upload, and ticket create have rate-limit scopes.
- Ticket upload names are sanitized, byte-size limited, randomly named, and upload requires auth.
- User guide tells users not to send raw configs, keys, QR codes, access links, or topology.

Missing or incomplete controls:

- Callback endpoint rate limiting and invalid-signature circuit breaker.
- Shared/durable rate limiter for multi-worker open beta.
- Authenticated support attachment download and upload-to-ticket ownership binding.
- Strict MIME allowlist, magic-byte validation, content scanning, and attachment retention.
- Payment payload/log redaction before DB/log storage.
- Secure client app session-token storage.
- Web token handoff that avoids durable URL/localStorage bearer exposure.
- Explicit release logcat/support-export scan for raw config, access links, session tokens, and staged config paths.
- Role-separated admin permissions and step-up confirmation for sensitive actions.

## Privacy Checklist

- [x] Public repo ignores known secret files, env files, SSH key folders, merchant secret folders, local DBs, and generated caches.
- [x] Canonical docs prohibit printing secret values in docs/reports.
- [x] Payment callbacks reject invalid signatures by default.
- [x] Admin APIs are backend-gated by Telegram admin identity in inspected routes.
- [x] User docs warn users not to submit raw config/access artifacts to support.
- [ ] Support attachments are private to ticket owner/admin after upload.
- [ ] Support attachment MIME and file content are strictly validated.
- [ ] Payment callback payloads are minimized/redacted before DB persistence.
- [ ] Provider error bodies are redacted before logs.
- [ ] Web sessions avoid localStorage and URL-borne durable bearer tokens.
- [ ] App session tokens use platform secret storage.
- [ ] Client support bundles exclude session token, raw runtime config, subscription URLs, QR/access links, and staged config files.
- [ ] Release logcat/server-log smoke checks scan for forbidden sensitive patterns.
- [ ] Legal pages describe support attachment handling, diagnostics/log categories, payment-provider sharing, and retention/removal contact paths at a high level.

## Legal / Copy Mismatch List

1. Privacy copy should explicitly cover support file uploads as user-submitted files, including who can access them, how long they are retained, and how users request deletion.
2. Privacy copy should describe app/client diagnostics and logs at a category level, including that raw access configs, keys, QR codes, and secret links should not be sent and should not be collected by default.
3. Privacy copy should include app session/account identifiers, app install identifiers, Telegram identifiers, email identifiers where enabled, IP-derived abuse-control telemetry, payment order/event metadata, and node/observer health telemetry categories.
4. Payment/legal copy should say external payment providers process only the payment data required for checkout, refund, dispute handling, reconciliation, and support; POKROV should not claim to store no payment data at all if callback order/event metadata is retained.
5. Offer/beta copy should continue to state Android public release is blocked until signing/handoff/physical localhost-control audit is complete and Windows beta may be unsigned until signing is closed.
6. Public wording should keep avoiding direct-meaning product descriptions that conflict with the POKROV wording rule; unavoidable technical/legal mentions should remain contextual rather than marketing copy.
7. Legal copy should avoid promising no logs unless the client and server redaction tests enforce that promise; use narrower language about data minimization and no raw config/support secret collection by default.

## Test / Smoke Plan

Phase 1, platform unit and API tests:

- Add tests for support upload private download, unauthorized download denial, owner/admin download success, MIME allowlist, SVG/HTML rejection, magic-byte mismatch rejection, size cap, and retention cleanup marker.
- Add tests for payment redaction in `ExternalOrder.meta_json`, `ExternalPaymentEvent.payload_json`, admin payment payloads, and provider error logs.
- Add tests for callback rate limiting, invalid-signature burst behavior, body-size rejection, and provider allowlist rejection.
- Add tests for Telegram init data compare/freshness: valid, expired, future-skewed, missing `auth_date`, malformed user JSON, and bad hash.
- Add route inventory test for `/api/admin/*` guard coverage.

Phase 2, web security tests:

- Add auth handoff tests proving durable tokens are not accepted from URL after code exchange and are not stored in `localStorage`.
- Add CSP/security-header smoke if the app keeps any bearer compatibility path.
- Keep `npm.cmd --prefix webapp run test:e2e:admin` as the browser admin gate.

Phase 3, client tests:

- Add app-shell tests for secret storage abstraction and migration from plaintext JSON state.
- Add Android integration smoke confirming staged runtime config files are app-private, excluded from support export, and cleaned/rotated when replaced.
- Add logcat/support-export scanner for forbidden patterns: session token field names, bearer tokens, subscription URLs, QR/access links, raw config outbound fields, and provider/API secret names.

Phase 4, release smoke:

- Run the exact platform and client commands listed above.
- Run Android physical-device localhost/control-surface audit on a release build.
- Run a production-like callback abuse smoke against a non-production provider secret using only fake payloads and verify `401/429` behavior plus redacted logs.
- Run a support upload smoke with fake sensitive-looking content and verify the file is private, redacted from logs, and deleted/retained according to policy.

