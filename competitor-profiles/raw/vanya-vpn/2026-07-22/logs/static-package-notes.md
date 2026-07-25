# Vanya VPN — Static Package and Release Notes

Captured: 2026-07-22<br>
Scope: read-only comparison of the installed Google Play package, the public direct Android APK, public download metadata, and the Windows installer's signed metadata. No installer was run, no access key existed, and no raw binaries, credentials, endpoints, device identifiers, or tokens are retained in the repository.

## Android package identity

- Package: `com.vanyavpn.android.client`
- Version: `1.20.6` (`versionCode 1784673185`)
- Minimum / target / compile SDK: 29 / 36 / 36
- Installed Play delivery: base APK plus Russian-language, x86_64 and xhdpi splits
- Direct APK: universal package with arm64-v8a, armeabi-v7a, x86 and x86_64 libraries
- Default resource label: **Outline**; Russian system label: **ВПН**; primary in-app brand: **Дядя Ваня**

The public direct APK and installed Play build carry the same version/versionCode, the same app signer and Google source stamp, and byte-identical `main.js` and `classes.dex` payloads by SHA-256. The direct channel is therefore a repackaging of the same current Android core, not evidence of a separate newer build.

## Architecture and inherited product

The client is a Cordova/Polymer hybrid built on a heavily customized Outline client. The package contains a roughly 3.7 MB web bundle and a large Go native library. Static module strings identify Outline/Shadowsocks components; native logging and methods also reference sing-box behavior.

Visible plugins/components include:

- Outline native bridge and Android `VpnService`;
- QR scanning, clipboard, in-app browser, app review, device information, theme and vibration plugins;
- boot/package-replacement receiver, foreground service and Quick Settings tile;
- browsable links for `ss:`, `ssconf:` and `https://vanyavpn.app`.

Manifest capabilities include internet/network state, vibration, optional camera access, boot reception, foreground VPN service, install-referrer handling and a request for battery-optimization exclusion. Camera permission is requested just in time from the QR route in the observed app.

## Product surface present in the current bundle

Russian UI strings and control paths expose substantially more product depth than the no-key dashboard reveals:

- automatic reconnect with explicit copy that traffic should not escape outside the VPN while reconnecting;
- a guided **find a working server** recovery sequence that retests, regenerates an IP and, as a last resort, enables multihop, warning that the process can take up to two minutes;
- automatic multihop or routing through Russia, with copy explicitly positioning the Russian route as a way through allow-list restrictions;
- split tunneling by installed application plus manual IP, subnet and domain exclusions;
- fastest-location marking, location changes propagated to every device sharing the key, and optional automatic connection after a change;
- server/key regeneration, manual and automatic mirror selection, TV login by an eight-digit code, battery guidance and light/dark/system themes;
- Quick Settings tile, reconnect/auto-connect controls, referrals and a detailed connection-troubleshooting matrix.

The recovery engine is the strongest product lesson in the package: it turns a generic connection failure into a staged automatic repair flow with meaningful progress and an escalating fallback strategy. Several of these controls require a real subscription key and were not executed in this audit.

## Mirror and release control

The web bundle contains a rotating probe/mirror pool spanning neutral and deliberately provocative Russian-language domains. Representative public hosts include `berezochka.ru`, `fastvanya.com`, `opihta.ru`, `okartoshka.ru`, `oklubnika.ru`, `ochertopoloh.ru`, `vova.loan`, `onards.am`, `osobaka.ru`, `ointernet.ru`, `turkmenvibe.ru`, `olegofriend.ru`, `nearabird.ru`, `ododep.ru` and `obeshbarmak.kz`; another hostname family is generated from the current date.

Remote mirror metadata can replace the real/magic website domain and Telegram handle, alter connectivity-test/reconnect behavior, announce a latest version and provide an update destination. The main-screen update banner is therefore server-controlled rather than tied only to a store rollout. The public `bit.ly/vanyavpn` magic link currently resolves through a Google Cloud Storage bootstrap page that selects a working mirror while preserving the requested page path/hash.

Observed public asset timestamps, which may reflect re-uploading rather than a new release:

| Asset | Public Last-Modified evidence |
|---|---|
| Android direct APK | 2026-07-21 22:49 GMT |
| Android TV APK | 2026-07-19 |
| Windows installer | 2026-07-22 00:45 GMT |
| macOS DMG | 2026-07-22 02:06 GMT |
| Windows 7 alternative | 2024-02-21 |
| Linux AppImage | 2023-11-12 |

## Telemetry and disclosure conflict

The installed bundle's environment file contains an empty Sentry DSN. Sentry client code and licences remain in the package, and the official policy says diagnostics go to Sentry, but the inspected production configuration does not provide an active DSN. This is configuration evidence, not proof that no endpoint can ever be supplied remotely.

More importantly, static runtime paths show automatic first-party telemetry outside the crash-report wording:

- a notification/bootstrap request includes language, platform, app version, connection state, a device-scoped identifier, and an access-key identifier when a key exists;
- lightweight authentication uses the key-scoped token plus language;
- reconnect policy is refreshed periodically with key/location/app/device/OS context and a connectivity probe host;
- connect/disconnect events post device and key context, timestamps, duration, app/platform/OS versions, route decision and traffic-byte counts to the key's service domain.

No real identifier or access key was present or captured. Nevertheless, the code path materially conflicts with the first-run claim that technical data is anonymous and with the policy's suggestion that per-key server metrics are not sent by default or might only be sent someday. The product needs a field-by-field disclosure, purpose, processor, retention period and key/device pseudonymization explanation.

## Technical-information modal

The About route contains an internal diagnostic modal that can show manufacturer/model/OS, platform, processor count, memory, app version, mirror prefix, a prefix of the device identifier, user agent and captured console/native service logs. It supports copy, refresh and clear. The code attempts to redact UUID/host patterns in logs, but an identifier prefix and broad device fingerprint remain visible. The modal was not opened or captured because it could place identifying/runtime material in durable screenshots.

## Windows signer and trust-chain mismatch

The public Windows installer reports product version `1.20.6` and product name **VanyaVPN**. It was never executed. Windows reports a valid Authenticode signature from **KONDAKOV&GORIN LLC**, an Arizona/US entity name. This adds a third named operator to the public trust chain alongside UK site entity CODE ASSET LTD and the Play/App Store publisher identities. The accessible official Arizona record shows entity 23405407 as an active domestic LLC formed in 2022 with Vladimir Kondakov and Ilia Gorin as members, but its displayed search timestamp is November 2025 and the replacement live UI could not be refreshed. A valid code-signing certificate proves signing identity, not current good standing or customer-contract responsibility.

## Evidence boundary

- No paid/free key, customer account, temporary Apple account or TV code was requested.
- No connection test was possible without a key.
- No untrusted installer or APK was executed outside the already installed Play app.
- Raw APKs/installers and all potentially identifying runtime material remain outside the repository.
