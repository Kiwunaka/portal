# Release Links And Final Handoff

Last updated: 2026-08-22

## Purpose

Use this runbook after client artifacts are published and before calling a release handoff complete.

This step exists so the app, bot, `webapp`, and `marketing` all resolve the same live Android and Windows URLs.

## Release Metadata Home

Active release metadata now lives under the canonical client repo:

- bridge-period metadata and mirrored bundles: `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/<version>/`
- next-client metadata and direct `POKROV-app` bundles after cutover: `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/<version>/`

Metadata rule:

- keep `release-handoff.json` in that versioned folder as the preferred operator input
- keep any compatibility `release-links.env` and the stamped JSON manifests produced by `release_handoff.ps1` beside it in the same versioned folder
- keep the stable pointer at `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/release-handoff.json`
- bind every pointer target by release identity and SHA-256 in `C:/Users/kiwun/Documents/ai/POKROV-app/config/release-rollback-catalog.seed.json`
- change the pointer only through the client `scripts/set-release-stable-pointer.ps1` dry-run plus explicitly authorized atomic apply; never hand-edit or overwrite a versioned handoff

## Stop Immediately If

Treat the release as blocked if any of these are missing:

- at least one working Android release URL
- at least one working Windows release URL
- `APP_DOCS_URL`
- a successful URL check run
- runtime env sync on `brain`
- static marketing rebuild and redeploy when public URLs changed

## Required Inputs

You need final public URLs for:

- `APP_ANDROID_PLAY_URL` or `APP_ANDROID_APK_URL` or `APP_ANDROID_MIRROR_URL`
- `APP_WINDOWS_EXE_URL` or `APP_WINDOWS_MIRROR_URL`
- `APP_DOCS_URL`

Minimum valid handoff input:

- at least one Android URL
- at least one Windows URL
- docs or install URL

## Step By Step

1. Publish the final Android and Windows artifacts.
2. Choose the versioned metadata home under `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/...`.
3. Generate `release-handoff.json`, then add any compatibility `release-links.env` and stamped manifest files in that versioned folder.

Bridge-period example:

```powershell
$version = "0.1.0-beta.3"
$releaseRoot = "C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/$version"

pwsh external/client-fork/scripts/release_handoff.ps1 `
  -AndroidApkUrl "https://github.com/<org>/<repo>/releases/download/<tag>/pokrov-android-universal.apk" `
  -WindowsExeUrl "https://github.com/<org>/<repo>/releases/download/<tag>/pokrov-windows-setup-x64.exe" `
  -DocsUrl "https://pokrov.space/install/" `
  -OutEnvPath "$releaseRoot/release-links.env" `
  -ManifestDir "$releaseRoot/release-manifests"
```

4. Verify the URLs from that same metadata file:

```powershell
python external/client-fork/scripts/check_release_urls.py --env-file "C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/<version>/release-links.env"
```

5. Apply the `APP_*` values to `brain` from that same metadata file:

```powershell
python scripts/remote_brain_apply_release_handoff.py `
  --brain-ip 82.21.114.104 `
  --metadata-file "C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/<version>/release-handoff.json"
```

Compatibility note:

- `remote_brain_apply_release_handoff.py` and `release_orchestrator.py` prefer the client-owned JSON handoff through `--metadata-file` / `--release-metadata-file`
- `release-links.env` remains a compatibility fallback and URL-check input when needed

6. If Android or Windows public URLs changed, rebuild and redeploy static `marketing` so `NEXT_PUBLIC_APP_*` matches the same release.
7. Re-check the download surfaces that read runtime values.
8. Add the exact candidate and retained previous stable target to the rollback
   catalog, validate it, and dry-run both the forward and reverse pointer IDs.
9. After explicit mutation authority, apply the pointer with an external backup
   and receipt, then verify exact readback. Runtime sync remains a separate
   authorized operation.
10. Run the reverse pointer/runtime drill for the same candidate and retain its
    readback; a local fixture is insufficient.
11. Only then write the final release handoff.

## Surface Notes

- public `marketing` download CTA depends on `APP_ANDROID_APK_URL` and `APP_WINDOWS_EXE_URL` for direct buttons; `Play`-only or mirror-only values do not give the same direct install path
- syncing `APP_*` on `brain` updates runtime app, bot, and authenticated `webapp`, but does not rebuild static `marketing`
- brain-local verify is useful after sync, but it does not replace separate `current-origin check` or `RU-origin check`

## Required Final Handoff Content

The final handoff should say:

- what changed
- what was verified
- what remains blocked, if anything
- whether the system is in a rollback-safe state

If origin-sensitive reachability appears in the same handoff, keep these as separate lines:

- `current-origin check`
- `brain-origin check`
- `RU-origin check`

Do not collapse them into one summary line.

## What To Send Back

Include:

- the exact `release-links.env` path used
- the URL-check command and exit code
- the `brain` sync command and exit code
- which services on `brain` were restarted
- whether `marketing` was rebuilt and redeployed
- evidence that app, bot, `webapp`, and `marketing` now resolve the same release URLs

## Common Blockers

- URLs exist but the checker fails
- runtime env was updated but `marketing` still shows old links
- only one surface was updated
- Android signing or physical-device audit is still open
- final signed Android or Windows artifacts are not yet confirmed as production-ready
- the handoff says `ready` but does not include origin-matrix evidence or release-URL evidence

## Related Instructions

- [Android Production Signing Handoff](C:/Users/kiwun/Documents/ai/VPN/docs/operations/android-production-signing-handoff.md)
- [Android Physical Device Audit Handoff](C:/Users/kiwun/Documents/ai/VPN/docs/operations/android-physical-device-audit-handoff.md)
- [RU Origin Probe Handoff](C:/Users/kiwun/Documents/ai/VPN/docs/operations/ru-origin-probe-handoff.md)
- [Deployment And Access](C:/Users/kiwun/Documents/ai/VPN/docs/operations/deployment-and-access.md)
