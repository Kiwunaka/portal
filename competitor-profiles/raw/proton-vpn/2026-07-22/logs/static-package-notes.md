# Proton VPN Android — Redacted Static And Release Notes

Snapshot: 2026-07-22<br>
Installed package: `ch.protonvpn.android`<br>
Installed build: `5.19.66.0` / `605196600`<br>
Source: Google Play early-access track

This file contains only redacted, reproducible findings. Pulled APK splits, decoded manifests, signatures and raw command output remain in the local sensitive quarantine outside the worktree. No account identifier, IP address, endpoint, token, certificate payload or raw VPN configuration is stored here.

## Installed artifact

- Split APK set observed on the emulator:
  - base: 29,159,220 bytes;
  - Russian locale split: 258,457 bytes;
  - x86_64 split: 7,943,030 bytes;
  - xhdpi resource split: 582,861 bytes.
- The four installed splits total about 37.9 MB. Google Play's visible `332 kB` value should therefore be treated as a displayed download/update estimate for this device state, not as the complete application size.
- `minSdkVersion 26` / Android 8+, `targetSdkVersion 35`.
- Production package is not debuggable.
- Entry flow is routed through `.RoutingActivity` rather than directly to the main VPN screen.

## Declared capabilities

Observed manifest permissions include:

- internet and network-state access;
- foreground-service execution, including the system-exempted foreground-service category used by the VPN service;
- boot completion for optional auto-connect behavior;
- wake lock;
- biometric/fingerprint authentication;
- camera access for cross-device QR login;
- notifications;
- Play Billing and Install Referrer integration;
- package visibility via `QUERY_ALL_PACKAGES`, consistent with the split-tunneling and post-connect app pickers.

No fine-location permission was declared. Location-like information visible in diagnostics can still be inferred from network/IP metadata and must not be mistaken for GPS collection.

## Components and feature surface

- ProTUN-backed Android VPN service and WireGuard wrapper/Go backend, both protected by Android's `BIND_VPN_SERVICE` permission.
- Quick Settings tile and home-screen widgets.
- Boot receiver for automatic connection behavior.
- Separate Android TV activities, TV settings and QR authentication flow.
- Session-fork / cross-device QR login activities.
- Play Billing, in-app update and in-app review components.
- Dedicated force-update and What's New activities.
- Promo and NPS-survey activities.
- Split-tunneling selectors for both installed apps and IP ranges.
- Telemetry settings, bug-report composer and in-app log viewer.

## Native code and dependencies

Observed x86_64 native libraries include:

- `libandroidvpnrust.so`;
- `libgojni.so`;
- `libjnidispatch.so`;
- `libsentry.so` and `libsentry-android.so`;
- `libdatastore_shared_counter.so`;
- `libandroidx.graphics.path.so`.

Package/class inventory confirms substantial ProTUN and WireGuard code, Sentry 7.22.5 modules, Google Play update/review APIs, Play Billing and Firebase encoders. No advertising-SDK package family was found in the inspected build. The presence of Sentry replay-related modules is only a dependency-level observation; it does not prove that session replay is enabled at runtime.

The installed UI offers Smart, WireGuard UDP, WireGuard TCP and Stealth. Static strings retain some OpenVPN references, but no OpenVPN engine package or native library was found. The current Google Play description still markets OpenVPN alongside WireGuard, which appears stale relative to both the observed runtime selector and package composition.

## Signing and provenance

- APK signature verifies with v2 and v3 schemes.
- A Google Play source stamp is present.
- Signer identity is Proton Technologies AG, Geneva.
- The installed signer's SHA-256 fingerprint exactly matches the fingerprint published in the official Android repository README.
- The official README states that Google Play, GitHub-direct and Amazon builds use the same signing key; F-Droid is the documented exception because F-Droid signs its own build.

## Public source and release channels

Primary sources:

- Android app: <https://github.com/ProtonVPN/android-app>
- Android Rust wrapper: <https://github.com/ProtonVPN/android-vpn-rust>
- ProTUN core: <https://github.com/ProtonVPN/protun>
- F-Droid package API: <https://f-droid.org/api/v1/packages/ch.protonvpn.android>

The Android app is GPL-3.0 and has been public since 2019-12-12. At this snapshot it had 3,814 GitHub stars and 487 forks. The public `master` branch and release channel were last updated on 2026-07-14.

Public Android release channels documented by Proton are Google Play, F-Droid and a direct GitHub APK. The latest GitHub and F-Droid build at the snapshot was `5.19.43.0`, published 2026-07-14. Its direct APK was 55,798,365 bytes and had 26,519 recorded GitHub downloads. Release notes added CIDR ranges to split tunneling.

The installed Play early-access build was already `5.19.66.0`, updated 2026-07-17, so Play beta was 23 development increments ahead of the public GitHub/F-Droid tag. This is channel staging, not evidence that the public repository is abandoned.

Across the latest 50 public GitHub releases, the observed gap was approximately:

- mean: 15.4 days;
- median: 11.8 days;
- minimum: 0.1 day, reflecting hotfixes;
- maximum: 52.3 days.

The practical cadence is usually two to four Android releases per month, with occasional same-day hotfixes.

## Versioning and release pipeline

The Android repository derives a four-part version name and an integer version code. The documented/source implementation constructs version code in an `AMMmmDDRR`-style layout from platform, major, minor, development and release increments. Git-derived development builds start from the latest semantic tag and add first-parent commit counts; this explains why an internal/Play beta such as `5.19.66.0` can precede the next public tag.

The public GitLab CI configuration reveals a controlled promotion path:

1. A manual release job starts from development or a hotfix lane and requires release notes.
2. CI calculates the version and creates a `release/<version>` branch.
3. Guest-hole bootstrap servers and F-Droid changelog/version metadata are refreshed.
4. CI builds a Google Play AAB, a vanilla/direct APK and an Amazon APK.
5. Artifacts go through centralized signing.
6. The public GitHub `master` branch is cleaned/re-written from the release branch.
7. A GitHub release is created only after signature verification of the direct APK.
8. A stable APK is also published to Proton's release storage; development builds can be pushed to Play's internal track.

The repository also contains a separate release-test application using UI Automator and Android Test Orchestrator. Documented suites cover smoke flows, end-to-end connection/performance SLI checks, Loki/Grafana measurements and anti-censorship controller scenarios. The orchestrator clears application data between test cases.

## ProTUN publication nuance

`ProtonVPN/android-vpn-rust` combines the Android Rust components and includes a `protun` gitlink whose relative URL reflects Proton's internal repository layout. That exact gitlink commit is not resolvable in the public `ProtonVPN/protun` history. However, ProTUN itself is publicly available under GPL-3.0 at `ProtonVPN/protun`; the latest public release at the snapshot was `v2.1.2`, published 2026-07-17. The correct conclusion is that the public wrapper mirror has a non-self-contained submodule reference, not that ProTUN is closed source.

## Competitive implications

- Proton uses public source, exact signing-key disclosure and signature-gated direct releases as a trust stack that smaller VPNs rarely match.
- Early-access Play builds let Proton collect private beta feedback while keeping public GitHub/F-Droid releases on a more stable cadence.
- One repository produces Play, direct, Amazon and F-Droid-compatible outputs, minimizing channel drift at the build-system level even though copy/UI can still drift.
- Release testing treats real connection quality and censorship paths as product SLI work, not only screen automation.
- POKROV can copy the operating model without copying Proton's complexity: publish a reproducible build/source map, disclose the signing fingerprint, keep one release manifest for every channel, and retain a small real-tunnel smoke suite for each promoted candidate.
