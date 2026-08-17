# POKROV 1.1.2 — final user product audit

Date: 2026-08-17

Verdict: `PASS` for the current direct stable Android/Windows release and the
authenticated Apple compatibility path. Stronger physical-device, clean
Windows-network, store, and trusted-publisher claims remain explicit manual
gates.

## User contract

- Android: install and update the official POKROV APK.
- Windows: install and update the official POKROV EXE.
- iPhone, iPad, and Mac: use a compatible Apple client with the personal
  authenticated key/QR until native POKROV Apple clients ship.
- Raw subscription material is not offered as the normal Android or Windows
  path.

## Surface audit

| Surface | Result | Current user outcome |
| --- | --- | --- |
| Public site | PASS | One primary promise, Android/Windows direct install, trial and price facts stay visible without technical internals. |
| Install page | PASS | APK and EXE are primary; Apple remains visible as a separate compatible-client path. |
| Cabinet | PASS | Login and account copy are consumer-facing; observer/runtime/bootstrap language is removed from the first layer. |
| Telegram bot | PASS | The first response is a compact entry window: connect device, code login, help, activation, and cabinet. The manual key is Apple-only. |
| Telegram cabinet | PASS | `app.pokrov.space` can be framed only by Telegram web origins; other sites retain frame denial. |
| Android app | PASS on LDPlayer | Exact signed 1.1.2 x86_64 update preserved the session; Home and protection states launch without crash and use plain Russian copy. |
| Huawei | MANUAL_OWNER_TEST | The phone was not enumerated by ADB during the exact 1.1.2 pass, so no physical claim is inferred from LDPlayer. |
| Windows app | PARTIAL | Exact setup/portable artifacts and hashes pass; trusted publisher signing and clean TUN/DNS proof remain manual. |

## Release and production proof

- GitHub `v1.1.2` is public, stable, latest, and contains eight expected assets.
- All eight assets accept anonymous range downloads; GitHub sizes and SHA-256
  values match the exact local staging metadata.
- Android split APKs are production-signed, non-debuggable, and versioned
  1.1.2; the LDPlayer install is the exact public x86_64 APK.
- Production returns `latest=min_supported=1.1.2` and `required` for older
  Android and Windows clients, with Russian release notes.
- Portal services, binary rule sets, public site, cabinet, checkout, and
  repeated subscription fetches pass the post-deploy brain readiness check.
- The production framing readback shows Telegram-only CSP on the cabinet and
  `DENY`/`frame-ancestors 'none'` on the public site.

## Current visual evidence

- `evidence/06-app-112-home.png`
- `evidence/07-app-112-protection.png`
- `evidence/08-site-production-desktop.png`
- `evidence/09-install-production-desktop.png`
- `evidence/10-cabinet-production-login-desktop.png`
- `evidence/12-bot-main-production.png`

## Non-blocking follow-ups

- exact 1.1.2 arm64 Huawei install plus RU-origin/carrier run
- exact-final WARP, per-app, Wi-Fi/LTE, lock/reboot, and endurance repetition
- Windows connected TUN/DNS/teardown without relying on host Hiddify
- trusted Windows publisher signing
- encrypted Android keystore recovery copy on owner media
- optional guarded Telegram mass notice for 1.1.2; the in-app required-update
  prompt and Russian release notes are already live
