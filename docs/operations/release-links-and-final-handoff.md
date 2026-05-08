# Release Links And Final Handoff

Last updated: 2026-05-07

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
- keep the stable pointer at `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/release-handoff.json` when you intentionally want one canonical handoff source

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

- `APP_ANDROID_APK_URL` or `APP_ANDROID_MIRROR_URL`
- `APP_WINDOWS_EXE_URL` or `APP_WINDOWS_MIRROR_URL`
- `APP_DOCS_URL`

Minimum valid handoff input:

- at least one Android `.apk` URL from GitHub Releases
- at least one Windows `.exe` URL from GitHub Releases
- `https://pokrov.space/install/` or a child install-docs URL

Outside-store beta handoff rule:

- keep `APP_ANDROID_PLAY_URL` empty until a separate store-publishing wave explicitly opens it
- `remote_brain_apply_release_handoff.py` validates URL role before touching `brain`: APK/EXE artifacts must be `https://github.com/.../releases/download/...` links with matching file extensions, and docs must stay under `https://pokrov.space/install/`

## Step By Step

1. Prepare and review the non-mutating GitHub Release plan:

```powershell
python scripts/prepare_github_release_plan.py --tag v0.2.0-beta.1 --title "POKROV 0.2.0-beta.1"
```

This prints staging commands, the prerelease `gh release create` command, SHA256 values, `gh` availability, and expected `APP_*` URLs without publishing or uploading anything. The staging commands rename raw build outputs to canonical GitHub asset filenames (`pokrov-android-universal.apk`, `pokrov-windows-setup-x64.exe`) before upload. If `tooling.gh.classification` is `BLOCKED_TOOL_MISSING`, install/authenticate GitHub CLI before the publish step.

2. If `gh` is unavailable, prepare the repo-owned REST publisher in dry-run mode:

```powershell
python scripts/publish_github_release_assets.py --tag v0.2.0-beta.1 --title "POKROV 0.2.0-beta.1"
```

This prints the canonical upload names, SHA256 values, expected `APP_*` URLs, token presence, and execute requirements without creating a release or uploading assets. `--execute` requires a `GITHUB_TOKEN` or `GH_TOKEN`, or authenticated GitHub CLI, plus `--go-evidence-file` pointing to a handoff that contains `GO for public beta publication` and does not contain `NO-GO`, unless a separate artifact-staging authorization includes `ARTIFACT STAGING GO FOR RUNTIME SMOKE`, `NON-URL P0 GATES GREEN FOR ARTIFACT STAGING`, `ONLY REMAINING P0 GATE: RUNTIME APP-DOWNLOAD URL SMOKE`, and `NO RUNTIME SYNC OR ANNOUNCEMENT` without unresolved blocker markers.

3. Upload Android and Windows artifacts only after the release handoff is `GO`, or under the narrower artifact-staging authorization described in the unblock packet. Artifact staging creates a public prerelease for smoke only: do not sync `APP_*`, rebuild static download surfaces, or announce the release until URL-only smoke has passed against the staged payload and runtime app-download smoke has passed after sync.
4. Choose the versioned metadata home under `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/...`.
5. Generate `release-handoff.json`, then add any compatibility `release-links.env` and stamped manifest files in that versioned folder.

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

6. Verify the URLs from that same metadata file:

```powershell
python external/client-fork/scripts/check_release_urls.py --env-file "C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/<version>/release-links.env"
```

7. Before applying `APP_*`, validate the exact client-owned handoff JSON. This validates shape and URL policy only; it does not prove the artifacts are reachable:

```powershell
python scripts/runtime_app_download_smoke.py --redact --apps-json "C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/release-handoff.json" --require-release-handoff --policy-only
```

After artifact-staging is authorized and the GitHub APK/EXE URLs are reachable, repeat the same handoff check without `--policy-only` before syncing runtime env:

```powershell
python scripts/runtime_app_download_smoke.py --redact --apps-json "C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/release-handoff.json" --require-release-handoff
```

8. Apply the `APP_*` values to `brain` from that same metadata file:

```powershell
python scripts/remote_brain_apply_release_handoff.py `
  --brain-ip 82.21.114.104 `
  --metadata-file "C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/release-handoff.json"
```

Compatibility note:

- `remote_brain_apply_release_handoff.py` and `release_orchestrator.py` prefer the client-owned JSON handoff through `--metadata-file` / `--release-metadata-file`
- `release-links.env` remains a compatibility fallback and URL-check input when needed

9. If Android or Windows public URLs changed, rebuild and redeploy static `marketing` so `NEXT_PUBLIC_APP_*` matches the same release.
10. Re-check the download surfaces that read runtime values.
10. Only then write the final release handoff.

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
