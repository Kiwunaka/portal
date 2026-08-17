# Client Downloads Flow

Last updated: 2026-06-07

## Runtime Source

The canonical runtime source for authenticated update metadata is
`/api/client/apps`. The bounded anonymous release projection is
`/api/public/client-apps`; it exposes only allowlisted public GitHub release
assets with a valid SHA-256 and positive bounded size.

The app should check this runtime metadata on launch or resume and ask the user
to update when the backend marks a newer version as optional, recommended, or
required. The current beta contract is prompt-based; do not claim silent
auto-update.

Current request shape:

```http
GET /api/client/apps?platform=android&current_version=1.0.5&channel=stable
X-Telegram-Init-Data: <redacted>
```

The response keeps the legacy URL fields and adds metadata under
`android.update` / `windows.update` plus a top-level `update_check` summary.
For Android split APK delivery, `android.apk_url` remains the default
`arm64-v8a` APK for backward compatibility, while `android.apk_variants[]`
lists the default `arm64-v8a` file and the legacy `armeabi-v7a` file with URL,
SHA-256, and size metadata. The backend returns `update_policy: none` unless
the client sends a matching `platform` and `current_version`.

The main bot follows the same consumer hierarchy: its primary Android button
uses `APP_ANDROID_APK_ARM64_URL` when present, then the compatibility
`APP_ANDROID_APK_URL`. Configured ARMv7 and universal URLs appear as clearly
secondary buttons. The x86_64 artifact remains available through the cabinet/API
for emulator use and is not promoted to normal phone users.

Platform delivery is explicit: Android uses an APK, Windows uses the EXE, and
iPhone/iPad/macOS use the authenticated manual Apple path until a signed native
Apple release exists. Raw subscription keys are not offered from Android or
Windows install screens.

The static marketing export uses build-time exact release URLs when present and
refreshes them from `/api/public/client-apps` in the browser. Missing or invalid
runtime metadata produces an explicit temporary-unavailable state and the
public Releases/checksum help link; it never falls back to authenticated
`/downloads/`.

## Handoff Source

Client release metadata lives in
`C:/Users/kiwun/Documents/ai/POKROV-app/config/release-handoff.seed.json` and
retained release evidence under
`C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/`.

Public download URLs must not be invented in platform docs; they must come from
approved client handoff evidence and the active runtime config.

## Public Delivery Surface

The current owner-approved delivery direction is GitHub Releases:

- keep APK/EXE files as release assets, not tracked git files
- avoid a first-party download domain for public binaries unless the owner
  deliberately changes this policy
- if the development repository stays private, publish public-user binaries to a
  public GitHub Releases surface; current release-only surface is
  `https://github.com/Kiwunaka/pokrov`
- private GitHub release assets return unauthenticated `404`; authenticated CLI
  proof alone is not public-user download proof

See
`C:/Users/kiwun/Documents/ai/VPN/docs/operations/client-delivery-update-content-plan.md`
for the active delivery/update/content plan.

## Verification

Use:

```powershell
$env:TELEGRAM_INIT_DATA="<redacted live init data>"
python scripts/runtime_app_download_smoke.py --redact --check-providers --require-release-handoff
```

Do not pass raw init data directly on the command line in retained evidence.
