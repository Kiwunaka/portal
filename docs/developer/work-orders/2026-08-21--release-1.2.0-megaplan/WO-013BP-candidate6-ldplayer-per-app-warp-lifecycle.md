# WO-013BP — candidate.6 LDPlayer per-app, WARP and lifecycle

## Outcome

Use the exact signed candidate.6 x86_64 APK to exercise Android per-app
configuration, WARP materialization, process-stop cleanup and false-green
recovery while the physical phone remained unavailable for an unlocked run.

Installed `1.2.0+4046` matches signed artifact SHA-256
`3d95d82d8290150fadd13600b79eca26326792407532f571909d8df224df6fa4`.
The baseline was stopped, WARP off, zero selected apps and `russia_direct`.

## Exact runtime slices

`selected_apps` with one locally selected system browser generated one mixed
TUN inbound with one include-package entry, no exclude-package entry and three
managed DNS servers. The private journal proves service start and TUN
establishment. A second connection was force-stopped only after both service
and TUN were observed; at one and five seconds both were absent, and relaunch
reported not protected with no service or TUN. There was no false-green state.

`excluded_apps` with the same local test app generated no include entry and
exactly two exclude entries: the selected test app and POKROV itself. The
private journal again proves TUN establishment, then failed egress, service
stop and service destroy. Raw package identity is absent from both bounded
journals; only `selected_app_count` values `0` and `1` are retained.

Owner consent then enabled WARP. The exact managed profile contains a native
`warp` endpoint, one mixed TUN inbound and three managed DNS servers. Service
and TUN both formed. LDPlayer's ADB transport temporarily reconnected during
full-tunnel operation while the emulator processes stayed alive and
responsive. The final bounded result is the same `EGRESS-001`/current-origin
failure already seen in the ordinary and AWG differentials, followed by
service stop and destroy. This is not a WARP protocol PASS or FAIL.

Android Private DNS remained at platform default with no explicit specifier.
System IPv6 is enabled, but the generated TUN profiles contain no IPv6 address,
so DNS-access and IPv6-leak claims remain open.

## Final restore and evidence ceiling

The selected app was removed, `russia_direct` restored and WARP disabled. The
final managed profile has no WARP or AWG endpoint, no include-package entry and
only POKROV's self-exclusion. Service and TUN are absent. Production, public
assets, stable pointer and the disconnected physical phone were untouched.

- `REL/AND-004`, `OBS/OBS-029`, `OBS_PB/PB-08` and
  `FRKN_PLAN/W6-02` remain `I3` with stronger exact-candidate LDPlayer proof.
- `REL_GATE/GATE-C` remains `I2`: physical Android protected egress,
  WARP/per-app traffic and leak, OEM/endurance plus Windows live parity remain
  open.
- `REL_GATE/GATE-F` remains WO-013BM's
  `3 PASS / 16 non-PASS / 0 FAIL`; emulator evidence cannot replace physical
  Android or any other manual gate.

Raw managed profiles and journal copies were parsed only for bounded fields
and then removed. The normalized evidence is
`evidence/013BP-candidate6-ldplayer-per-app-warp-lifecycle/013BP-candidate6-ldplayer-per-app-warp-lifecycle.json`;
its SHA-256 is
`166e2cc4167c8d0d1e43955a451810bdd9d38c1e9136f98de4f1203732134603`.
It contains no device serial, address, hostname, credential, key, raw config,
package identifier, customer data or provider payload.
