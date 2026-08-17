# Apple path and final product release

Status: complete with explicit manual-device gates

## Outcome

Ship one coherent user contract across the site, cabinet, Telegram bot, and
POKROV 1.1.2 clients:

- Android installs and updates through official APK files.
- Windows installs and updates through the official EXE.
- iPhone, iPad, and Mac keep a visible authenticated manual path using the
  existing personal key/QR in compatible Apple apps. This is not a native Apple
  release claim.
- consumer surfaces do not expose observer/runtime/bootstrap vocabulary.
- the Telegram cabinet WebApp opens inside Telegram while remaining blocked
  from unapproved framing origins.
- the Android protection sheet uses plain recovery language.

## Acceptance

- [x] current-run screenshots for public site, cabinet, redacted bot main menu, and Android are retained
- [x] focused bot, webapp, marketing, Caddy, Flutter, and Android-host tests pass
- [x] relevant release gates pass for the exact 1.1.2 source candidate with the explicit manual gates below
- [x] production-signed split APKs and Windows direct artifacts are built and hashes recorded
- [x] exact signed APK update/install and launch pass on LDPlayer; Huawei is `MANUAL_OWNER_TEST` because ADB did not enumerate it
- [x] platform and client commits are pushed to `master` and `main`
- [x] GitHub release and production runtime handoff are deployed and read back
- [x] user-facing 1.1.2 release notes are Russian and describe the Apple path without exposing a private key

## Evidence

Retain redacted screenshots and machine-readable summaries in `evidence/`.
Never retain Telegram IDs, personal subscription URLs, session tokens, or raw
provider material.

Current-run evidence includes the 1.1.2 Android Home/protection states, public
site/install and cabinet login pages, and a cropped bot main-menu screenshot.
Production readback separately proves required 1.1.2 Android/Windows update
metadata, eight public assets, healthy runtime services, and Telegram-only
cabinet framing.

## Manual gates retained

- exact 1.1.2 arm64 install and carrier/RU-origin proof on the owner Huawei
- Windows connected TUN/DNS proof without the host Hiddify dependency
- trusted Windows publisher signing
- exact-final WARP/per-app/uplink endurance and encrypted keystore backup
