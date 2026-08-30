# WO-013CW — candidate.11 LDPlayer AWG runtime and quarantine fix

## Outcome

Bind the exact signed candidate.11 Android bytes to fresh AWG 3.1, AWG2 and
ordinary profiles; prove which profile Core actually received; retain
address-free traffic evidence; and reject the candidate if a repeatable client
state defect can prevent the lab profile from reaching Core.

## Exact boundary

| Item | Value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.11`, immutable, internal only |
| Version | `1.2.0+4047` |
| Platform source | `01cf5de682c01bffbead7703db901450ca7fb1fb` |
| Client source | `348de306fc1f2243d022157b54fa7f09ffd2840b` |
| Core source | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Signed release-index source | `8c314a10893bb6260f59f171ecab296103c0e0c1` |
| Receipt-recording release-index source | `8adeed137b4778a84f32bd8f7d2284dabd640be6` |
| Signed manifest | `22ea88cb7679510d51af6b35a7d31e65ec654fb17806ddf9ebd71c7da350a29f` |
| Android artifact | production-signed universal APK, `706c546e…e1a`, `295370161` bytes |
| Runtime | LDPlayer 9 `emulator-5554`, Android 9/API 28, current origin |

The installed `base.apk` SHA-256 equals the exact candidate universal APK.
The physical phone was not addressed by any command and supplies no evidence
for this work order.

## Fresh-profile results

AWG 3.1 first passed from a deliberately fresh managed-profile fetch. Safe
runtime inspection found the `pokrov-awg31-lab` final route and exactly one
typed AWG endpoint. Android established its TUN, Core changed the mandatory
egress state from required to verified, and the application completed the
connection attempt as succeeded. A separate 60-second inner-interface capture
returned no addresses and counted `117` packets: `68` from the client, `48` to
the client, `116` TCP packets and `48` TCP payload packets. Latest handshake
age was `32` seconds.

AWG2 then ran once as a compatibility and profile-switching control, not as
the primary protocol. Its fresh profile had the `pokrov-awg2-lab` typed
endpoint, TUN and mandatory egress passed, and a separate address-free
60-second capture counted `63` packets, `37` from client, `25` to client and
`19` TCP payload packets. This proves that the candidate switched profiles
rather than continuing on the preceding AWG 3.1 or ordinary cache.

After guarded `default` restore and cache separation, ordinary Auto fetched a
non-AWG VLESS/selector profile and independently passed TUN plus mandatory Core
egress. These three exact attempts are
`PASS_LDPLAYER_CURRENT_ORIGIN_FRESH_PROFILE`. They are emulator/current-origin
proof only and do not close physical Android, Windows, RU mobile, leak,
handover, OEM or endurance gates.

## False-green and release blocker

The server-side binder proves policy selection only. An early attempt showed
that a fresh local ordinary profile could still run after an AWG 3.1 bind. It
is excluded from the AWG result. Platform PR 113 adds a root-ADB verifier that
validates the app-private runtime path, classifies only the normalized profile
and type counts, emits no endpoint/config/key/identifier, and exits nonzero on
an expected/observed mismatch. Its deliberate default-as-AWG3.1 control exits
`1`; focused tests pass `14/14`.

A later exact candidate.11 repeat exposed a separate deterministic defect.
When an ordinary Auto failure had placed nodes into the bounded automatic
quarantine, the bootstrapper applied those exclusions while resolving an
owner-lab envelope. Two AWG 3.1 retries stopped before profile staging with
the visible result `NO_AVAILABLE_AUTOMATIC_LOCATION` and safe operational code
`API-008`. Both server captures had zero attributable client inner packets;
the prior handshake age was stale. This is
`FAIL_EXACT_CANDIDATE_11`, before cryptography, and candidate.11 must not be
promoted.

Client PR 41, merged as `afcdcde5824202eb6df45f9e60865f33d8b7a529`,
clears Smart Connect from the typed `awg2_lab`, `awg31_lab` and `hy2_lab`
payloads and skips the resolver when no Smart Connect profile exists. The full
bootstrap file passes `86/86`, `flutter analyze` passes, and the exact
cross-repository seed/docs/contract gate passes locally. Hosted client and
platform jobs again contained zero steps and remain `SKIPPED_BY_OWNER` under
the accepted solo/no-purchase exception; they are not PASS.

## Cleanup and decision

The exact device is bound back to `default`; `legacy_reality_fallback` resolves,
AWG2/AWG3.1 material and lab membership are absent, all test-created private
profile backups are gone, the UI is disconnected and Android reports no
connected VPN. No tag, public release, Store object, stable pointer or Gate G
action occurred.

Candidate.11 is `REJECTED_FOR_REPLACEMENT`. Its successful attempts remain
valid bounded evidence, but the successor client fix changes source bytes and
requires a new signed candidate plus exact AWG 3.1 repeat. Hysteria2 benefits
from the same source fix but still has no candidate runtime handshake and is
not advanced.

Normalized secret-free evidence is retained at
`evidence/013CW-candidate11-ldplayer-awg-runtime/013CW-candidate11-ldplayer-awg-runtime.json`,
SHA-256 `9ca50ac0887518855ce9868b2bbe5a677bae148cd1450c068280ef14adfb9f0c`.
