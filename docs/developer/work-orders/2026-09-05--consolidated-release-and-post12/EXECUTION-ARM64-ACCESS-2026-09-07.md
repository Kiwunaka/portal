# ARM64 physical update and truthful access status вЂ” 2026-09-07

Active evidence for D01/D04/D06 and F01/F07; not final release acceptance.
Client implementation `9334d46`, platform contract adjustment `01914f9`, Core
`8dc57a8`. The prior physical package/source remains retained separately.

## Package scope

The standard Direct pipeline already produces one-version universal, ARM64,
ARMv7 and x86_64 APKs using
`--target-platform android-arm,android-arm64,android-x64
--android-project-arg=pokrov.singleVersionSplitApks=true`.
The prior quick local `--target-platform android-arm64` command compiled only
ARM64 Flutter but still included extra AAR Core libraries. No Gradle fix was
needed. All retained packages are local test artifacts using the existing
owner-controlled signer, not published or promoted candidates.

The baseline build from `cb2694e` produced ARM64 101225939 bytes and universal
295227054 bytes (65.71% reduction). Separate native inventories contain exactly
Core, Flutter and Dart AOT for their ABI; universal contains all three ABIs.
Every Core SO matches the bound AAR, each per-ABI SO matches universal, and all
notice assets match. All four manifests are non-debuggable, package
`space.pokrov.pokrov_android_shell`, version 1.2.0+4053, minSdk24/targetSdk36.
Signer continuity was verified on all artifacts.

Huawei ADA-AL00U / Android12 / SDK31 accepted a same-version update to the real
universal APK and then the actual ARM64 APK. Both reached the app's confirmed
tunnel/DNS/VPN-egress state. Warsaw/whitelist, Russia-direct and WARP-off
preferences remained; the account session refreshed the subscription after
update. Installed ARM64 SHA-256 matched its retained artifact. No account or
device identifiers were exported. This verifies the local transition; a final
public-channel artifact and the full D04 updater-origin/upgrade matrix remain
separate. ADB same-version replacement is not in-app newer-version acceptance.

## Defect found and corrected

Before the API returned, a restarted premium account displayed
В«РџСЂРѕР±РЅС‹Р№ В· 5 РґРЅРµР№В» from the seed. The existing API-timeout regression was
extended with the visible account assertion and failed on that exact string.
The client now treats an absent/unrecognised subscription lane as unknown.
The mobile pill, desktop strip, profile value and subscription sheet no longer
invent trial days or active/renewal status. Zero remaining days does not reset
to the public trial length. Confirmed server lanes and positive remaining days
still display, and confirmed free-profile recovery presentation retains priority.
Runtime entitlement, the encrypted 24h offline cache and tunnel proof are
independent and unchanged by this presentation fix.

The unused trial-day account-copy getter was removed. The platform consumer
check still requires the generated trial duration in seed/onboarding and tests
its absence negatively; it no longer requires an unused account-copy fallback.
Price, reward, scope, legal URL and digest checks remain. The client product
contract is the canonical owner for the presentation rule.

## Source checks

- `flutter test test/pokrov_seed_app_test.dart --reporter expanded`: 187 PASS.
  After the last desktop unknown-label adjustment, five focused paid/unknown/
  zero-day/profile/responsive cases passed again. Existing paid and expired
  subscription checks remain covered.
- `flutter analyze`: PASS. An earlier run found the now-unused trial label;
  it was removed, then analysis passed.
- `scripts/validate-seed.ps1 -PlatformRoot <platform-worktree> -CoreRoot <Core-worktree>`:
  PASS after correcting the consumer location. The retained first failure
  reflects that stale requirement, not a fake successful check.
- Platform `python -B -m pytest -p no:cacheprovider tests/test_shared_surface_facts.py -q`:
  13 PASS; `tests/test_admin_design_guardrails.py`: 5 PASS.
- The first full widget pass while adjusting assertions had four failures:
  two stale seed-copy expectations, one assertion that also matched the separate
  Telegram offer, and the unknown mobile label still saying Renew. These were
  corrected and followed by the full 187-PASS run and final focused rerun.

## Final local package and device receipt

The [retained receipt](evidence/arm64-access-2026-09-07.json) binds all four
normal APKs to client `9334d461f38cb906ce1ae22a9aed126d7a3f903a` and Core
`8dc57a830bd1487389dd1b7c9190f094c31e13bc`. Normal ARM64 is 101225939 bytes,
SHA-256 `d849d27398d0fdb18b8fdf3975c0a24b9d419c642048502018d76738201e14d2`.
Universal is 295227054 bytes; the 65.71% difference comes from the existing
per-ABI delivery, without dropping runtime features or notices.

A separately identified same-source/signer ARM64 fixture used
`https://127.0.0.1:1`. Physical Huawei displayed the neutral Subscription pill
and unknown profile subscription instead of five trial days, while the saved
profile reached confirmed tunnel/DNS/VPN egress. This is controlled API
unavailability, not proof of actual carrier blocking or RU origin.

The ordinary API ARM64 APK was restored and its installed SHA-256 checked.
It also reached the app's confirmed tunnel/DNS/egress state. Final screen
confirms VPN disconnected, Wi-Fi enabled and location/routing/WARP preferences
retained. Android-shell Flutter tests: 8 PASS. Platform docs tests: 33 PASS;
context packet audit: PASS. Screenshot and log hashes are retained in the
receipt; raw artifacts remain in `E:/r12-device-20260907/access-label-fixed`.
Previous packages, screenshots and logs in the parent directory are preserved.

## Remaining scope

D01 still needs the final approved downloadable artifact/channel tuple; local
same-signer installation is not publication or owner go/no-go. D02/D03 network,
OEM/Doze and long-session matrices remain open. D04 unsupported transitions,
store install authority and actual updater delivery remain individually scoped.
No repository push, merge, production deployment, provider/payment mutation,
store upload or public candidate. Concurrent source changes are untouched.
