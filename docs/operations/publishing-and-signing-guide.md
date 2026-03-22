# Publishing And Signing Guide

Last updated: 2026-03-22

## Document Status

This file is the canonical guide for `POKROV` client publishing, signing, store submission, and release-cost expectations.

## Release Scope

Current full public `v1` release target:

- `Android`
- `Windows`

Current Apple scope in this wave:

- `iOS`: readiness only
- `macOS`: readiness only

Do not present Apple store publication as shipped or guaranteed in this release wave.

## Distribution Strategy

Until store URLs are live, the canonical distribution source is:

- GitHub Releases for Android and Windows binaries

All public download surfaces must be wired from the same release handoff values:

- app
- webapp
- marketing site
- Telegram bot

## Artifact Canon

Current canonical release artifacts:

- `pokrov-vpn-android-universal.apk`
- `pokrov-vpn-android-market.aab`
- `pokrov-vpn-windows-setup-x64.exe`
- `pokrov-vpn-windows-setup-x64.msix`
- `pokrov-vpn-windows-portable-x64.zip`

## Android

### What to publish

- signed `APK` for direct distribution
- signed `AAB` for Google Play

### Minimum signing inputs

- `ANDROID_SIGNING_KEY`
- `ANDROID_SIGNING_STORE_PASSWORD`
- `ANDROID_SIGNING_KEY_PASSWORD`
- `ANDROID_SIGNING_KEY_ALIAS`

### Release steps

1. Build release artifacts in `external/client-fork/app/`.
2. Sign the Android release with the production keystore.
3. Upload the `AAB` to Google Play when store publication is ready.
4. Upload the universal `APK` to GitHub Releases for direct download.
5. Run release handoff and sync the final URLs into runtime env.

### Store notes

- Google Play submission is the preferred Android store path.
- Direct APK distribution remains valid while Play rollout is pending.
- Android package continuity should be treated as a fresh install path if package identity changed.

### Cost note

- Google Play Console requires a paid developer account.
- APK side-loading is operationally possible without store fees, but it does not replace Play review and trust signals.

## Windows

### What to publish

- signed `EXE` installer for direct distribution
- signed `MSIX` for Microsoft Store readiness
- portable ZIP when needed for fallback distribution

### Minimum signing inputs

- `WINDOWS_SIGNING_KEY`
- `WINDOWS_SIGNING_PASSWORD`

### Release steps

1. Build the Windows release.
2. Sign the installer and MSIX package.
3. Upload the signed `EXE` and optional ZIP to GitHub Releases.
4. Keep the `MSIX` ready for Microsoft Store submission.
5. Run release handoff and sync the final URLs into runtime env.

### Store notes

- Microsoft Store is the preferred public listing path for Windows.
- Direct signed installer distribution remains the default until the Store listing is live.

### Cost note

- Microsoft Store individual registration may be free or low-friction depending on current Microsoft program terms.
- Code signing certificates are usually paid unless already provisioned through existing signing material.
- Unsigned Windows installers should be treated only as smoke artifacts, not public release artifacts.

## Apple Readiness Only

### Current policy

For this wave, `iOS` and `macOS` stay in readiness mode only:

- bundle IDs and display names can be planned
- signing prerequisites can be documented
- store metadata can be prepared
- public ship promise must wait for a later release

### Required readiness checklist

- final bundle identifier plan
- final display name plan
- URL scheme and deep-link plan
- tunnel and network extension target inventory
- entitlement inventory
- provisioning profile inventory
- notarization path for macOS
- App Store / Mac App Store metadata draft

### Cost note

- Apple Developer Program is paid.
- iOS App Store and Mac App Store submission are not free paths.
- Developer ID signing and notarization for public macOS distribution also require Apple program participation.

## Cheapest Viable Path

If the goal is the lowest-cost legitimate public path in this wave:

1. publish signed Android `APK` and signed Windows `EXE` via GitHub Releases
2. prepare `AAB` for Google Play
3. prepare `MSIX` for Microsoft Store
4. keep Apple to readiness docs only until the paid program and platform work are approved

This keeps the real public ship on Android and Windows while avoiding an accidental Apple promise.

## Runtime Wiring

After every client release:

1. publish GitHub release artifacts
2. run release handoff
3. validate URLs with the release-link checker
4. update runtime env for all Android and Windows download links
5. verify the same links appear in app, webapp, marketing, and bot surfaces

## Public Mailboxes And PR Readiness

Recommended baseline public mailboxes for this release wave:

- `support@pokrov.space` for user help and store support contacts
- `noreply@pokrov.space` for transactional sender identity
- `press@pokrov.space` for PR, media, and partnership requests

Notes:

- mailbox setup is operationally useful before store submission, PR outreach, and TLS automation
- user-facing support should keep `support@pokrov.space` as the primary published address
- do not block Android or Windows release on `press@` if the mailbox is not yet live, but create it before active PR outreach

## TLS Certificates For Public Surfaces

Before public rollout, keep valid TLS on all current public hosts:

- `pokrov.space`
- `app.pokrov.space`
- `api.pokrov.space`
- `connect.pokrov.space`
- `pay.pokrov.space`

Practical guidance:

- the cheapest normal path is automated ACME via Caddy or another managed reverse proxy
- keep certificate automation tied to the real production domain rather than temporary migration hosts
- mail delivery, press outreach, and store verification are easier once the domain has stable DNS and valid TLS

## REALITY And Domain Note

For REALITY-style camouflage, the important part is not merely buying any domain for the VPN server. The critical requirement is that the configured handshake target and client `server_name` / SNI behave like a real public TLS site accepted by that target.

Operational rule for this repo:

- use a real, stable domain strategy for public surfaces and TLS
- when configuring REALITY or similar camouflage, verify the target domain actually presents a normal TLS handshake and accepted SNI values
- do not assume that attaching a random domain to the VPS automatically improves REALITY quality

## Verification

Minimum publishing verification:

- artifact names match canon
- Android and Windows builds install successfully
- signatures are present on public artifacts
- download links resolve from every public surface
- store metadata matches `POKROV VPN`
- Apple surfaces, if any, are clearly labeled as upcoming or waitlist-only
