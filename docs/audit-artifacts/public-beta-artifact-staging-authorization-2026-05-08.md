# Public Beta Artifact Staging Authorization

Generated: 2026-05-08

## Scope

This authorizes creating the GitHub prerelease assets only so the Android APK and Windows EXE URLs can be smoke-tested.

It is not final public launch approval. Do not sync runtime `APP_*` links, do not announce the release, and keep paid checkout unavailable while Lava.top proof is incomplete.

## Required Markers

ARTIFACT STAGING GO FOR RUNTIME SMOKE
NON-URL P0 GATES GREEN FOR ARTIFACT STAGING
ONLY REMAINING P0 GATE: RUNTIME APP-DOWNLOAD URL SMOKE
NO RUNTIME SYNC OR ANNOUNCEMENT

## Evidence Summary

- Current-origin full and quick gates are green in the dated release-gate reports.
- Brain-origin quick gate is green in the dated brain report.
- Android physical audit is operator-attested for this beta pass.
- Windows unsigned beta risk is accepted for this outside-store pass.
- RU-origin is operator-skipped and must not be claimed as verified.
- GitHub CLI auth is available through the local keyring.
- Staged client-app payload uses GitHub Releases `.apk` and `.exe` URLs and install docs under `https://pokrov.space/install/`.
- Paid checkout remains unavailable until the separate Lava.top evidence pack is green.

## Stop Conditions

- If GitHub upload fails, do not sync runtime links.
- If staged URL reachability fails, replace or withdraw the staged assets before any public handoff.
- If live runtime app-download smoke fails after URLs exist, keep runtime links unchanged and keep launch copy unposted.
