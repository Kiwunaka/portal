# POKROV 1.0.5-beta.1 artifact-staging authorization

Owner authorization: the current conversion-first goal explicitly authorizes
commit, push, public prerelease publication and production deploy.

ARTIFACT STAGING GO FOR RUNTIME SMOKE

NON-URL P0 GATES GREEN FOR ARTIFACT STAGING

ONLY REMAINING P0 GATE: RUNTIME APP-DOWNLOAD URL SMOKE

NO RUNTIME SYNC OR ANNOUNCEMENT

Exact candidate inputs:

- platform source: `5be63e641252ffabed6b3828d2cd15436c6730a8` plus the release-notes-only follow-up;
- client source: `48d52b913917bdbeb67d9b700208c6578b3c78da`;
- Android version: `1.0.5+14`, four production-signed APK variants;
- Windows version: `1.0.5-beta.1+14`, setup and portable bundle;
- exact quick release gate: PASS after the reward-policy and UI-smoke corrections;
- full client Flutter/Gradle checks, Windows bundle, marketing, webapp and admin gates: PASS.

This authorization permits only creation of the public prerelease assets needed
for anonymous URL/hash verification. Production runtime synchronization and
announcement remain separate steps after the exact public-asset smoke passes.
