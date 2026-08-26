# WO-013E — Android mobile/runtime matrix

Status: `PRE_CANDIDATE_PARTIAL_RUNTIME_EVIDENCE_RECORDED`
Phase: `11`
Candidate: `NOT_CREATED`
Recorded: `2026-08-26`
Production mutation: `PLATFORM_DEPLOY_PERFORMED_CLIENT_NOT_PROMOTED`

## Outcome

The current Android 1.2.0 direct APK was installed in place on one physical
Android device and on LDPlayer without changing package identity or production
signer. The physical Beeline slice proves that two whitelist variants connect,
while Saint Petersburg direct and whitelist type 3 fail closed on that mobile
origin. This is not evidence of a general type-3 server failure: the deployed
profile material matches the production rollout and independent full-chain
checks pass for both type 2 and type 3.

This is pre-candidate evidence. It does not advance any row to `I4`, does not
create an RC and does not prove the complete Android OEM, RU-origin, Wi-Fi/LTE,
Doze, payment, Operator Center or rollback matrices.

## Exact identities

| Surface | Exact identity | Evidence state |
|---|---|---|
| Platform source and deployed portal | `243dcbe4727041d62cc0a36e7d2fd5a8530c7c25` | `PASS` current source/deploy identity |
| Client source | `a74d2aea5aed62f5c31d3a0bbc258e408cebe3bd` | clean `main`; current Android source |
| Core source | `9b94e0bda7e454536e8fa9b4519f2281211798e0` | clean `main`; current AWG 3.1 lab source |
| Android artifact | `app-direct-release.apk`, 295018413 bytes, SHA-256 `1ba37463c9549a6d5ba128850e1bf5825187fe185a621e9f8dc62c7cde1a4158` | production signer; pre-candidate only |
| Android identity | `space.pokrov.pokrov_android_shell`, `1.2.0 (4031)`, min 24, target 36, arm64-v8a/armeabi-v7a/x86_64 | `PASS` package inspection |
| Android signature | APK Signature Scheme v2; certificate SHA-256 `0a0602a7df5d96a0b427909d004f3ddf26def86587634bf16694da8d654b2500` | `PASS`; one signer; not debuggable |
| Upgrade baseline | `1.1.6 (2029)`, SHA-256 `6ac6ac33d2fae7041b2d408a2c55b93eeddb7d50825c4068f8c9c6087f0d97ca` | same production certificate; temporary extracted APK deleted after verification |

The current tuple is newer than the retained `WO-013U` six-file set. The new
Android artifact must not be described as a member of that older set. A new
complete Android/Windows artifact set, handoff, SBOM, provenance and signed
release index are required before an RC can exist.

## Physical Android / Beeline matrix

The device serial and raw connection material were not retained. Carrier
identity is owner-attested; application state and the connection-proof UI were
observed on the device.

| Check | Result | Label and boundary |
|---|---|---|
| In-place `1.1.6 -> 1.2.0 (4031)` upgrade | package, data/session and production signer continuity preserved | `PASS` for this device/artifact pair |
| Saint Petersburg, direct | no verified egress; client stayed non-green/fail-closed | `OPERATOR_ATTESTED` Beeline-origin failure; not a global server verdict |
| Whitelist default variant | connected; verified protection state; later probe 396 ms | `OPERATOR_ATTESTED` physical mobile pass |
| Whitelist type 2 | connected; verified protection state; later probe 1451 ms | `OPERATOR_ATTESTED` physical mobile pass |
| Whitelist type 3 | no verified egress; client stayed non-green/fail-closed | `OPERATOR_ATTESTED` Beeline-origin failure |
| AI and Games/Xbox split-routing toggles | enabled and persisted over application restart | `PASS` preference/runtime persistence |
| AdGuard DNS setting | enabled and persisted | `PASS` preference persistence; this is not proof of a DNS-only bypass product mode |
| Gemini/ChatGPT/Xbox content reachability | no browser/content transaction retained | `NOT_RUN` |
| Wi-Fi to LTE handover | Wi-Fi was enabled while cellular remained the observed default; no controlled handover sequence retained | `NOT_RUN` |
| Doze, standby, process death, IPv6, Private DNS and OEM background matrix | not completed on the exact artifact | `MANUAL_OWNER_TEST` |

## LDPlayer boundary

- The canonical non-debuggable `1.2.0 (4031)` APK was restored after the
  diagnostic build and left foregrounded with VPN disconnected and the UI in
  `Не защищено` state.
- Direct Saint Petersburg connected and reached the proof-driven protected
  state on LDPlayer.
- Bridge attempts on the LDPlayer/debug-Core path are not valid device proof:
  the same path also failed when supplied with independently working type-2
  material. Type-2 and type-3 emulator failures therefore remain
  `DIAGNOSTIC_ONLY`, not production transport verdicts.
- All three temporary managed profiles containing connection material were
  deleted from LDPlayer and the Windows temp directory. The downloaded
  diagnostic `sing-box` directory and the saved APK copy were also deleted.

## Server and deployment reconciliation

- The portal backend was backed up and deployed from platform
  `243dcbe4727041d62cc0a36e7d2fd5a8530c7c25`. Five portal units and Caddy were
  active with zero observed restarts after deployment; health/subscription
  readback returned seven hosts and 33 outbounds.
- The type-2 and type-3 bridge services and their frontends were active. The
  Android type-3 profile fingerprint matched the production rollout.
- Independent full-chain checks from an owned Windows origin returned HTTP 204
  through both type 2 and type 3. This proves server-chain reachability from
  that origin only; it does not replace Beeline or exact Android evidence.
- Predeploy readiness for the separate DE node remains `BLOCKED_BY_ACCESS`
  because its trusted SSH host key is absent. No trust-on-first-use exception
  was made.
- AWG 3.1 backend support is deployed but disabled by default, kill-switched
  and has no isolated owned target. AWG 3.1 runtime proof remains
  `BLOCKED_BY_ACCESS`; no Brain, delivery or mini node was repurposed.

## Release decision

No execution-ledger row advances. `ANDROID_PHYSICAL_DEVICE`,
`ANDROID_OEM_MATRIX`, `CURRENT_ORIGIN`, `BRAIN_ORIGIN`, `RU_ORIGIN`, provider,
Operator, legal and rollback gates are not converted to `PASS`. The retained
single-device Beeline slice narrows the failure domain and proves fail-closed
behavior, but candidate creation remains false.

Next, freeze the branch heads after this evidence lands, rebuild the complete
direct-beta artifact set, validate its strict handoff and supply-chain records,
then repeat the required physical-device and origin matrix against those exact
bytes. Type 3 should be rechecked on a second real carrier/origin; server
changes are not justified by the current evidence.
