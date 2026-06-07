# Client Delivery, Update Check, And Dynamic Content Plan

Last updated: 2026-06-07

Status: active product/operations plan

Implementation note:

- `2026-06-07`: backend contract work that does not require owner action is
  implemented. `/api/client/apps` now returns prompt-mode update metadata, and
  `/api/client/promo-slots` supports safe banner fields such as placement,
  image URL, dismissibility, and scheduling. Client UI wiring, public GitHub
  release-surface visibility, and manual install/connect smoke remain separate
  gates.
- `2026-06-07`: shared app shell update prompt is implemented. On startup and
  resume, Android/Windows clients can call `/api/client/apps` with their current
  version and open the returned GitHub Releases asset through the normal
  platform handoff path when the backend returns `recommended` or `required`.
- `2026-06-07`: owner created the public release-only repository
  `Kiwunaka/pokrov`, and `v1.0.0-beta` assets were published there. Anonymous
  range smoke returned `206` for Android APK, Windows setup EXE, Windows
  portable ZIP, Windows manifest, and `SHA256SUMS.txt`.
- `2026-06-07`: Android public download was switched from one universal APK to
  split ARM APKs: `pokrov-android-arm64-v8a.apk` is the default app/API URL,
  and `pokrov-android-armeabi-v7a.apk` is exposed as the legacy ARMv7 variant.

This plan records the current owner decision for how the Android and Windows
client should be delivered, how the app should discover newer versions, and how
news/promo surfaces may change without shipping a new binary.

## Scope

- Public client binaries stay on GitHub Releases, not on a first-party download
  domain, CDN bucket, or committed repository file.
- The source repository may stay private. If anonymous users must download
  assets directly, the release assets must live on a public GitHub Releases
  surface; private GitHub release assets return `404` without authentication.
- App, cabinet, marketing, and support copy should consume release metadata from
  the platform runtime contract instead of hardcoding stale URLs.
- Startup update behavior is prompt-based: the app checks its version and asks
  the user to update when needed. It must not claim silent auto-update.
- Important posts, notices, and owner-approved promo slots are backend-owned
  JSON surfaces. The app must not render arbitrary HTML/JS or unreviewed ad SDKs
  from remote content.

## Delivery Decision

Use GitHub Releases as the public download surface.

Recommended release topology:

- keep `POKROV-app/main` as the active private development repository until the
  owner decides otherwise
- publish binaries to the dedicated public release-only repository
  `https://github.com/Kiwunaka/pokrov`
- attach binaries as release assets, not tracked git files
- keep checksums and release notes next to every binary

Canonical asset shape:

- `pokrov-android-arm64-v8a.apk`
- `pokrov-android-armeabi-v7a.apk`
- `pokrov-windows-setup-x64.exe`
- `SHA256SUMS.txt`
- optional `release-manifest.json`

Each public asset record should expose:

- platform
- channel
- version
- URL
- SHA-256
- size
- uploaded timestamp
- release notes URL or short release notes
- beta/stability warning when applicable

Current platform contract:

- `/api/client/apps` is the existing client download endpoint
- `/api/client/apps?platform=<android|windows>&current_version=<version>&channel=beta`
  returns prompt-mode update metadata for the requested platform
- `config/release-handoff.seed.json` in `POKROV-app` is the repo-owned handoff
  seed for current binary metadata
- unauthenticated GitHub release asset range smoke is the evidence required
  before a URL is treated as public-user-ready; current `v1.0.0-beta` public
  repo smoke is `PASS_PUBLIC_GITHUB_RELEASES_206`

## Startup Update Check

The app should check for updates on launch and resume. The first implementation
should extend `/api/client/apps` with update metadata instead of creating a
second source of truth.

Suggested update payload fields:

- `platform`: `android` or `windows`
- `channel`: `beta`, `stable`, or another explicit release lane
- `current_version`: sent by the client
- `latest_version`: returned by the backend
- `min_supported_version`: oldest version allowed without a required prompt
- `update_policy`: `none`, `optional`, `recommended`, or `required`
- `url`: public GitHub Releases asset URL
- `sha256`
- `size`
- `release_notes`
- `published_at`
- optional `rollout_percent`
- optional `force_after`

Current backend env/config fields:

- `APP_RELEASE_CHANNEL`
- `APP_ANDROID_VERSION`
- `APP_ANDROID_MIN_SUPPORTED_VERSION`
- `APP_ANDROID_SHA256`
- `APP_ANDROID_SIZE_BYTES`
- `APP_ANDROID_RELEASE_NOTES`
- `APP_ANDROID_RELEASE_NOTES_URL`
- `APP_ANDROID_PUBLISHED_AT`
- `APP_WINDOWS_VERSION`
- `APP_WINDOWS_MIN_SUPPORTED_VERSION`
- `APP_WINDOWS_SHA256`
- `APP_WINDOWS_SIZE_BYTES`
- `APP_WINDOWS_RELEASE_NOTES`
- `APP_WINDOWS_RELEASE_NOTES_URL`
- `APP_WINDOWS_PUBLISHED_AT`

Client behavior:

- `none`: no UI
- `optional`: quiet row or small sheet
- `recommended`: launch-time sheet with a normal dismiss path
- `required`: blocking sheet until update or exit

Android beta behavior:

- ask the user to download/open the APK
- rely on the Android system installer
- do not claim store-style background updates

Windows beta behavior:

- ask the user to download/open the installer
- preserve unsigned/SmartScreen honesty until signing changes
- a full Windows updater may be planned later, but is not the current beta claim

## Notices And Telegram-Sourced Updates

Important posts and operational updates should be available in the app without a
binary update.

Existing platform surface:

- `/api/public/live-updates` exposes active update cards
- admin live-update endpoints already exist for creating/updating/deleting rows
- `live_updates` can store Telegram channel linkage through `channel_username`
  and `post_id`

Allowed notice categories:

- incident
- maintenance
- release
- billing
- support
- promo

Allowed client actions:

- open Telegram post
- open support
- open account/cabinet
- open download/update
- dismiss local notice when the notice is not mandatory

## Promo Slot And Banner Policy

The owner wants flexible banner space in the app, including the option to show a
partner or advertising-style placement later. Treat this as a constrained
backend-managed promo slot, not as an unbounded ad integration.

Existing platform surface:

- `/api/client/promo-slots?surface=app`
- `/api/admin/promo-slots`
- app-safe slots are allowlisted in `shared/promo-slots.json`

Allowed first version:

- title
- short body
- image URL or icon token
- CTA label
- CTA URL/action
- placement
- priority
- active start/end
- dismissibility
- audience targeting by access state or surface

Runtime safeguards now enforced:

- slot IDs and content IDs must be allowlisted
- `cta_href` and `image_url` accept only `https://` or `tg://`
- scheduled slots are hidden before `starts_at` and after `ends_at`
- unsupported unsafe URLs are dropped in client runtime payloads and rejected in
  strict admin writes

Suggested placements:

- `home_corner`
- `home_banner`
- `account`
- `rewards`
- `support`
- `global_banner`

Forbidden until a deliberate product-policy change:

- arbitrary HTML/JS
- tracking pixels
- third-party ad SDKs
- unsafe redirect chains
- hidden keyword stuffing
- unsupported stable/store/trusted/RU-readiness claims
- remote content that can change routing, billing, account state, or security
  behavior without the normal API contracts

## Implementation Phases

### P0: Release Surface And Metadata

- choose the public GitHub Releases surface: complete, `Kiwunaka/pokrov`
- upload current split APK/EXE/checksums there: complete for `v1.0.0-beta`
- update release-handoff metadata and `/api/client/apps` runtime values:
  complete; brain-local signed `/api/client/apps` smoke returns split APK
  variants, hashes, sizes, Windows EXE, and docs URL
- prove anonymous public download with unauthenticated range smoke: complete,
  `206`

### P1: App Update Prompt

- send current app version/platform/channel from the client
- return update policy and asset metadata from backend: implemented
- show optional/recommended/required update UI: implemented for app shell
- open APK or Windows installer through the platform-safe path: implemented via
  existing download handoff

### P2: In-App Notices

- show active public live updates on the client home/support surfaces
- keep Telegram post linkage where available
- support incident and maintenance priority states

### P3: Promo Slots

- expand promo-slot placement/targeting if current schema is too narrow:
  implemented for app banner placements
- add admin controls for placement, priority, dismissibility, and scheduling:
  backend contract implemented
- render a muted, polished, dismissible app slot: existing rewards promo rows
  consume the extended model; first-screen home/global banner placement remains
  a UI taste decision for a later pass if needed

### P4: Release Ops

- verify public GitHub asset range smoke: complete for public release repo
- verify `/api/client/apps` points to the same public assets
- keep owner manual install/connect tests as the final local gate

## Remaining Manual Gates

- owner install/connect smoke for exact APK/EXE artifacts
- real app-session smoke for `/api/client/apps`
- update prompt smoke on Android and Windows
- WARP runtime proof only when making stronger public WARP claims
- signing, store, trusted Windows, and RU-origin checks only when those claims
  are being made

## Safe Public Claims

Allowed after P1 implementation:

- the app checks for updates at launch
- the app asks the user to update when a newer beta is available
- downloads are served through GitHub Releases

Not allowed unless separately implemented and evidenced:

- silent auto-update
- store auto-update
- trusted signed Windows installer
- production-stable `1.0.0`
- RU-origin readiness
