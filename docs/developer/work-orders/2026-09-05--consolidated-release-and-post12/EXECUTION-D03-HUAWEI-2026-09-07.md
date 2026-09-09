# D03 Huawei forced idle and standby — 2026-09-07

Active partial device evidence. [Receipt](evidence/android-lifecycle-2026-09-07.json).
Source client `9334d46`, Core `8dc57a8`; normal ARM64 1.2.0+4053 SHA-256
`d849d27398d0fdb18b8fdf3975c0a24b9d419c642048502018d76738201e14d2`.
The [package binding](EXECUTION-ARM64-ACCESS-2026-09-07.md) was checked on the same
physical Huawei ADA-AL00U, Android 12 / API31. Current-origin only; geographic
origin is not independently attested. No source or APK changed in this slice.

## Executed

- After confirmed protection, Home sent the app to background.
  `adb shell cmd deviceidle force-idle deep` reached IDLE. Samples at 0/30/60/90/120
  seconds retained the same app PID, foreground VPN service and forced IDLE.
  `cmd deviceidle unforce` returned ACTIVE/force=false.
- A TUN auxiliary probe had malformed `sh -c` quoting and is UNKNOWN in every
  affected sample. Its original output is preserved locally. A separate
  `adb shell ls -d /sys/class/net/tun0` check succeeded during IDLE. This is
  point-in-time TUN evidence, not continuous external traffic proof.
- On foreground return, the protection refresh completed with confirmed
  tunnel/DNS/VPN egress.
- `adb shell am set-inactive space.pokrov.pokrov_android_shell true` reached
  `Idle=true` with the app in background. Samples at 0/30/60 seconds retained
  the same process, foreground service and TUN. Setting inactive false restored
  `Idle=false`; foreground protection refresh again confirmed tunnel/DNS/egress.
- Final readback: deep ACTIVE, force=false, app standby false, Wi-Fi enabled,
  no POKROV VPN service after the ordinary Disconnect action. No idle exemption,
  permission, battery simulation, power settings, reboot or device data reset.

Commands ran through the retained `check-doze.py` and `check-standby.py` in
`E:/r12-device-20260907/access-label-fixed`. Hashes and timed observations are in
the receipt. Raw dumps containing unrelated device state were not exported.

## Scope left open

D03 moves from unreviewed to active I3/NEEDS_RUNTIME_PROOF. USB remained attached;
forced idle is not natural screen-off, long-session or battery baseline proof.
Minimum/current Android API, Samsung/Pixel or approved subset, permission revoke,
lockdown, process-kill/reboot, endurance, final delivery channel and each required
network condition remain separate. Earlier force-stop tests are in the offline
receipt and do not make this whole matrix pass. No push, merge, deployment,
public candidate or store action occurred.
