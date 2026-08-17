# Apple path and final product release

Status: in progress

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

- [ ] current-run before/after screenshots for public site, cabinet, bot, and Android
- [ ] focused bot, webapp, marketing, Caddy, Flutter, and Android-host tests pass
- [ ] full relevant release gates pass for the exact 1.1.2 source candidate
- [ ] production-signed split APKs and Windows direct artifacts are built and hash recorded
- [ ] exact APK update/install and launch pass on LDPlayer and the owner Huawei when ADB is available
- [ ] platform and client commits are pushed to `master` and `main`
- [ ] GitHub release and production runtime handoff are deployed and read back
- [ ] user-facing release notices are Russian and describe the Apple path without exposing a private key

## Evidence

Retain redacted screenshots and machine-readable summaries in `evidence/`.
Never retain Telegram IDs, personal subscription URLs, session tokens, or raw
provider material.
