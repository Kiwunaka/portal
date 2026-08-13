# Artifact staging authorization — v1.0.3-beta.1

Date: 2026-08-13

Owner requested direct APK and Windows beta publication, deployment, commit, and push.

ARTIFACT STAGING GO FOR RUNTIME SMOKE

NON-URL P0 GATES GREEN FOR ARTIFACT STAGING

ONLY REMAINING P0 GATE: RUNTIME APP-DOWNLOAD URL SMOKE

NO RUNTIME SYNC OR ANNOUNCEMENT

This authorization permits creation of the public GitHub prerelease and upload of the exact locally verified Android split APKs and unsigned Windows beta installer. Runtime metadata sync follows only after anonymous exact-size and SHA-256 download verification. Huawei tunnel, WARP, per-app routing, Quick Settings, and notification proof remains a separate `MANUAL_OWNER_TEST` gate and is not represented as passed.
