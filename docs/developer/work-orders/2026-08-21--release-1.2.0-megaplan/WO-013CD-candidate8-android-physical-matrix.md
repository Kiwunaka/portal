# WO-013CD — candidate.8 physical Android matrix continuation

## Outcome

Continue the exact physical Android release matrix on signed
`pokrov-1.2.0-candidate.8` without rebuilding the APK or mutating backend,
server, profile or public release state. Retain the WARP fallback, per-app,
network/lifecycle, Private DNS, IPv6 differential, privacy and final-restore
facts without device identifiers or raw runtime material.

The exact ARM64 APK passes the defined WARP fallback/revoke path, selected-app
traffic plus excluded-control bypass, mobile/Wi-Fi handoff, screen-off,
Quick Settings and notification lifecycle, forced deep Doze, forced app
standby and strict Private DNS interaction. Active WARP traffic is not proven,
the available Wi-Fi path has no usable IPv6 in either VPN-on or VPN-off
control, and the broader Android matrix remains incomplete. Gate F therefore
stays `BLOCKED` at `4 PASS / 15 non-PASS / 0 FAIL`.

## Exact identity

| Component | Revision or digest |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.8` |
| Platform source | `241a83b4dca00799b39696a4ae0c3c97e087ec39` |
| Client artifact source | `3459438f02bd774e722b1b858e7f7f16d57a9f5c` |
| Client evidence-doc merge | `6ee1c2612965e621f10bdb91fca472f4ddff95bf` |
| Core source | `a45d69e40ed7d892619a2b5c4592a527f630665e` |
| Signed release-index source | `b242e0a3060b04f9b71641a0524bf251a75ce2a8` |
| Manifest SHA-256 | `f0006cec90c84e401e9920d9098102c7f50ab5ace5242e0d7683c3df709a6fbc` |
| ARM64 APK SHA-256 | `9278c09fd8fa5768d3260cf796b4230db5acb0a092187aae00c441d717cfc572` |
| ARM64 APK size | `101366934` bytes |

The installed base APK already matched the retained ARM64 artifact byte for
byte. The client evidence update is documentation only and does not change the
candidate artifact source.

## WARP result

Three observed WARP attempts, including one unintended extra re-enable during
navigation, reached the same explicit paused/ordinary fallback. The client did
not present active WARP as proven. The representative controlled attempt moved
through apply and next-connect state, then settled on ordinary fallback after
about 36 seconds. The terminal generation retained app-confirmed tunnel, DNS
and selected egress.

Consent revoke cleared the local enabled state, and a WARP-disabled ordinary
control passed. Classification:
`PASS_EXACT_CANDIDATE_FALLBACK_PATH; ACTIVE_WARP_TRAFFIC_NOT_PROVEN`.

## Per-app result

The UI selected one ordinary installed test app in `Только выбранные` mode.
Android's active VPN UID range matched the selected app UID and excluded the
POKROV host UID. A six-second idle window produced `0/0` TUN bytes. Launching
the selected app produced `2391111` received and `2485252` transmitted TUN
bytes. After stopping it, an excluded shell control retained internet access
with `0/0` additional TUN bytes.

This proves selected-app traffic and bypass for the exact candidate on this
device. It does not prove the separate excluded-app mode or a multi-app/OEM
matrix.

## Network, lifecycle and DNS result

- mobile/Wi-Fi/mobile/Wi-Fi retained `Подключено` on every leg;
- a 15-second screen-off interval retained the VPN service and connected state;
- Quick Settings stop/start and notification disconnect matched service state;
- forced deep Doze reached `IDLE` for ten seconds and forced app standby reached
  `Idle=true` for eight seconds; the service survived both and the UI remained
  connected after restoring `ACTIVE` / `Idle=false`;
- strict Android Private DNS retained tunnel, DNS and egress confirmation; the
  public test resolver name is not retained;
- IPv4 worked with and without VPN on the same Wi-Fi path. IPv6 worked in
  neither control, so the result is `BLOCKED_NO_UNDERLYING_IPV6`, not leak PASS
  or FAIL.

Blocked UDP 53, external MTU and external IPv6/leak checks remain unrun.

## Privacy and restore

User-facing protection status and history exposed no endpoint hostname,
address, key, raw profile, subscription URL or token. Device serial, network
identifier, raw runtime material, screenshots and UI dumps are not retained.

Final state is `Всё устройство`, zero selected apps, WARP off and no POKROV
service. Wi-Fi is restored off, mobile data remains enabled, Private DNS mode
and its prior specifier are restored, animation scales are `1.0`, stay-awake
remains `2`, deep idle is `ACTIVE` and app standby is false. Remote test temp
and local personal screenshot counts are both zero.

## Client evidence and hosted boundary

Client PR `35` merges the canonical Android audit, WARP checklist and client
release queue at `6ee1c261…95bf`. Its private hosted run `33271351440` ended
with zero steps under the GitHub billing boundary. The owner-solo exception
permits merge without a purchase or protected branch, but the run is retained
as `SKIPPED_BY_OWNER`, not PASS.

## Gate F effect

The new exact-device facts advance named Android subchecks but do not close the
whole `android_physical_device` row. Active WARP, external IPv6/leak, blocked
UDP 53, external MTU, excluded-app mode, broader OEM coverage, 100-cycle/
battery endurance, backup/exposed-port review and public/store delivery remain
open.

Gate F stays `BLOCKED` at `4/15/0`; Gate G, tag, public assets, stores and the
stable pointer remain unauthorized. No completion-index level advances to
`I4`.

## Evidence

Machine evidence is retained under
`evidence/013CD-candidate8-android-physical-matrix/`:

| Evidence | SHA-256 |
|---|---|
| physical Android matrix | `dbb964663fa8760f3ea40ddfcebcffbab4b1e81787df9d69a3798f23f0e18e6c` |

## Verification

```text
Client docs contract: PASS
Client seed/cross-repository contract against exact candidate.8 platform/Core: PASS
JSON parse/schema-shape review: PASS
Platform docs/link/agent-context checks: PASS
git diff --check: PASS
```

No APK build, production deploy, payment action, repository visibility change,
public release, store submission, stable pointer mutation or Gate G
authorization occurred.
