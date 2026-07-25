# ExpressVPN 12.71.0 — Redacted Android Package Notes

Snapshot: 2026-07-22. Google Play split APKs were copied from the emulator into the audit's sensitive temporary area. Raw binaries, signing fingerprints, service/API hosts, credentials, account data, tunnel configurations and endpoint material are intentionally excluded from the repository.

## Package And Provenance

- Package: `com.expressvpn.vpn`
- Version: 12.71.0 (`versionCode 12710040`)
- Splits: base, Russian resources, x86_64 native code and xhdpi resources
- Installed split size: about 97.9 MB; base 56.2 MB, x86_64 35.4 MB, xhdpi 6.1 MB and Russian resources 0.27 MB
- `minSdkVersion`: 24
- `targetSdkVersion`: 36
- `debuggable`: false
- APK signature schemes v2 and v3 are present with one ExpressVPN signer; Google Play Source Stamp timestamp: `2026-07-10 08:42:05Z`
- `allowBackup=false`

The Google Source Stamp is Play distribution evidence, not evidence that Google operates ExpressVPN.

## Application Shape

- Large native Kotlin/Android application with 15 DEX files, Jetpack Compose plus retained XML/fragments, WorkManager/Hilt-style components, phone and Android TV/Leanback entry points.
- Home/navigation resources describe VPN, Add-ons, Connection Copilot, Help, Profile and Speed Test destinations. The exact bottom-tab set can be plan/feature/region controlled.
- MapLibre renders the connection/location map. Resources include Smart/Fastest/selected/current locations; Recommended/All tabs; favorites, recents, regional grouping, search, endpoint sorting and server-quality labels.
- A Quick Settings tile, Glance app widget, boot receiver and home-screen quick actions expose connection/location controls outside the main activity.
- User-facing support is native/Zendesk-backed, with live chat, articles, diagnostics consent, email templates and app/legal details.
- Google Play Billing is first-party monetization in this build; the observed onboarding paywall is native rather than a browser checkout.

## VPN Engines And Protocols

Customer-visible resources define:

- Automatic (recommended)
- Lightway UDP with post-quantum support
- Lightway TCP with post-quantum support and better compatibility on some networks
- OpenVPN UDP
- OpenVPN TCP
- WireGuard

Native libraries support separate Lightway, OpenVPN and WireGuard paths. The x86_64 split contains approximately:

- 41.6 MB Kape shared client/security SDK manager
- 14.2 MB ExpressVPN core client
- 10.8 MB MapLibre
- 6.0 MB Lightway mobile
- 4.1 MB WireGuard Go plus smaller WireGuard helpers
- 3.6 MB OpenVPN execution library
- 2.8 MB Helium VPN library

An `org.amnezia.awg` backend is bundled, but the audited customer string labels this route WireGuard. Static implementation packages are not proof that AmneziaWG is exposed or activated for customers.

## Connection And Utility Layer

Bundled product surfaces go well beyond a connect button:

- **Connection Copilot:** copy describes an AI-powered scan that evaluates network settings/connectivity to select the best VPN setup. It also owns app-update states such as check, download, install and store fallback.
- **Speed Test:** ISP and VPN phases, download/upload, latency, jitter and packet loss, plus VPN server/IP/protocol and provider/country detail.
- **Protection Summary:** on-device time protected plus original/replaced IP and IP-location messaging. Disabling it deletes the local summary.
- **Advanced Protection:** independent blocking for ads, trackers, malicious sites and adult sites.
- **Network Protection / kill switch:** reconnect blocking, Android Always-on/Block without VPN handoff and local-network access controls. The app warns that system-level Block without VPN disables split tunnelling and always blocks LAN devices.
- **Split tunnelling:** off, allow only selected apps through the VPN, or exclude selected apps.
- **Auto-connect:** startup, untrusted networks, trusted-network disconnect and per-network trust lists; this explains fine/background location permission use for Wi-Fi identity.
- **Shortcuts:** one-tap apps and website links displayed after connection.
- **GPS override:** while the VPN is active, report the selected VPN location as the device's GPS position. Setup copy requires Developer options and selection as the mock-location app.
- **Tools:** DNS leak test, IP checker, WebRTC leak test, password generator and TrustedServer education.
- **Dedicated IP:** location assignment, access-code save/confirmation/unlock, separate subscription state and protocol-compatibility warnings.

These are bundled capabilities. The unpaid runtime session could not establish which tiles, protocols or add-ons were enabled for this account/region.

## Security-Suite Expansion

The Add-ons dashboard calls itself a “complete security suite” and contains resources for:

- **Advanced Protection** — block ads, trackers and more
- **ExpressAI** — private AI chat with multiple models
- **Identity Defender** — ID alerts, data protection and more
- **ExpressKeys** — separate password-manager app for unlimited passwords and credit cards
- **ExpressMailGuard** — mail-security tile
- **Dedicated IP**

The bundled Kape identity-protection SDK contains Array.com-oriented account, identity-alert, credit-score, financial-account, neighbourhood-watch and data-broker-removal workflows. Those classes show shared-suite capability; they do not prove availability outside supported regions/plans or that a VPN-only user supplies the corresponding identity data.

Migration resources say the old built-in Keys feature was discontinued on March 31, 2026 in favour of the separate ExpressKeys app. Retained migration strings are not a current release announcement by themselves.

## Permissions And Privacy/Measurement Surface

The manifest requests 29 permissions. Notable groups:

- fine/coarse/background location and mock-location capability;
- network/Wi-Fi state, boot, wake lock, notifications and foreground-service types;
- biometric/fingerprint access;
- Google Play Billing, Install Referrer, advertising ID and AdServices attribution;
- legacy storage permissions constrained to older Android versions;
- Huawei/Samsung store/device-integration permissions.

Bundled or manifest-verified integrations include AppsFlyer attribution, Braze messaging/content cards, Firebase Analytics/Measurement, Crashlytics and FCM, Zendesk messaging, Google Play Billing/review infrastructure, MapLibre and Keycloak sign-in. No evidence from package names inspected in this pass established RevenueCat, Adjust, Sentry, Facebook SDK, Amplitude or Mixpanel.

The first-run consent promises that non-essential collection can be disabled. Settings resources allow accepting, customizing or rejecting non-essential data use and separately mention crash reports, feedback and in-app screenshot capture. SDK presence does not prove that every collection path is enabled for every user.

## Components And Security Notes

- Main aliases, Keycloak callbacks, deep-link dispatcher and a quick-smart-location Home action are exported.
- VPN services are protected by Android's `BIND_VPN_SERVICE` and are not exported.
- The Quick Settings tile is protected by `BIND_QUICK_SETTINGS_TILE`.
- An exported credentials provider is guarded by the app-defined `com.expressvpn.vpn.permission.ACCESS_PROVIDER` permission.
- WorkManager/ProfileInstaller diagnostic receivers require the system `DUMP` permission.
- Cleartext networking is permitted only for two captive-portal/connectivity-check hosts in the declared network-security config; no broad cleartext opt-in was observed.

No deep-link injection, provider access, component invocation, traffic interception, certificate bypass or configuration extraction was attempted.

## Release Signals

- Installed Play build has Play Billing, Google Source Stamp and user-facing update/status strings.
- Connection Copilot can represent checking, downloading and installing an update, with a store fallback. Static resources alone do not establish whether the Play flavor downloads its own APK or delegates to Play.
- The installed package includes several launcher aliases/themes and phone/TV code in one artifact family.
- Public store, direct-APK and release-history verification remains a separate source pass.

## Evidence Boundaries

- Raw APKs, DEX/native code, signing digests, API/update hosts, credentials, configurations and endpoint material remain outside the worktree.
- Feature/resource presence is evidence of bundled capability, not proof that a feature flag, entitlement, region or server path was active.
- The unpaid session never reached Home and no VPN service was started.
