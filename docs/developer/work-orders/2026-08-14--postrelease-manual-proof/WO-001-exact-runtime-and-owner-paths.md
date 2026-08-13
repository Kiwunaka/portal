# WO-001 — Exact Runtime And Owner Paths

Status: `READY`

## Goal

Produce retained, exact-target evidence for six owner-deferred post-release
checks without mixing them with new product work.

## Exact Baseline

- Public release: `https://github.com/Kiwunaka/pokrov/releases/tag/v1.0.4-beta.1`
- Android target: `1.0.4+2013`, ARM64 SHA-256
  `48EAC0BE655D4D85D31134908E7A8CAEC881ED91AAE049FB7CF72206EFD99E6C`
- Windows portable SHA-256:
  `E25A3E7CAF900D8B8DFE14A4AE58DCDB40B3EBC61B2C631916E7F3BD42B28ADD`
- Windows setup SHA-256:
  `AD93F7F307552210BE4A8E6263382D4D221E993D8D743CEB6809D774DA007095`
- Android signing-certificate SHA-256:
  `0A0602A7DF5D96A0B427909D004F3DDF26DEF86587634BF16694DA8D654B2500`

If a newer candidate replaces this baseline, start a superseding WO. Do not
silently transfer these acceptance results to another hash.

## Scope And Acceptance Oracle

| Gate | Current result | PASS oracle | Retained evidence |
| --- | --- | --- | --- |
| Huawei endurance and lifecycle | `MANUAL_OWNER_TEST` | At least 20 connect/disconnect cycles on the exact APK; manual/auto location, WARP, per-app routes, background, lock, process kill and reboot retain correct UI/runtime state; no new crash/ANR and teardown is clean | Timestamped ADB bundle, redacted logs, screenshots and cycle summary |
| Wi-Fi → LTE → Wi-Fi | `MANUAL_OWNER_TEST` | The exact APK preserves or honestly recovers tunnel, DNS and requested route policy across both uplink changes; leak/egress checks retain only country/result and hashes, never raw IP | Before/during/after network and app-state evidence |
| Isolated Windows TUN/DNS | `MANUAL_OWNER_TEST` | On a channel where stopping Hiddify cannot sever the operator session, the exact public setup and portable each start POKROV's own runtime, establish the expected TUN/DNS/route state, connect, disconnect and restore the baseline cleanly | Process/adapter/route/DNS snapshots, redacted logs, UI captures and teardown diff |
| Real Telegram user journey | `MANUAL_OWNER_TEST` | A real owner-controlled Telegram account completes bot → sign-in → correct Android/Windows download → cabinet session; Apple remains the documented compatible-client/key path | Redacted screenshots and signed-session route summary; no chat IDs or tokens |
| Independent RU-origin probe | `MANUAL_OWNER_TEST` | From a genuinely Russian origin, preferably phone LTE with POKROV off, the approved probe records origin class, route/DNS result and timestamp without retaining raw public IP | RU-origin evidence record kept distinct from current-origin and brain-origin |
| Encrypted offline keystore copy | `MANUAL_OWNER_TEST` | A verified encrypted copy of the production keystore and recovery metadata exists on owner-provided external media; restore/read verification succeeds without printing or committing secrets | Redacted inventory, media label, ciphertext hash and restore-verification result |

## Safety And No-touch Scope

- Do not stop Hiddify on the current operator PC; it carries the live session.
- Do not use, request or bypass a phone PIN/password.
- Do not retain raw public IPs, credentials, Telegram identifiers, provider
  payloads, private keys or decrypted keystore material.
- Do not mutate production payments or delete real users while proving these
  gates.
- LDPlayer may provide regression coverage only; it cannot replace Huawei
  physical-device evidence.

## Execution Order

1. Confirm exact candidate identity and capture clean baselines.
2. Run Huawei endurance and uplink suites while the owner leaves the phone
   unlocked and available.
3. Run Windows on an isolated channel or second machine without touching the
   operator's Hiddify session.
4. Run the real Telegram journey and independent RU-origin probe.
5. Copy and restore-check the encrypted keystore backup after the owner attaches
   external media.
6. Record each result as `PASS`, `FAIL`, `MANUAL_OWNER_TEST` or
   `BLOCKED_BY_ACCESS`; never infer a pass from an older build.

## Promotion And Product Impact

This WO is evidence-only unless a check finds a defect. A defect starts a
separate scoped fix/release task with its own version, tests, artifact hashes
and promotion evidence. Passing this WO alone does not republish artifacts.

## Handoff

Next action: owner supplies an unlocked Huawei for the 20-cycle/uplink pack, an
isolated Windows network path, a real Telegram session and external backup
media when ready. Independent parts may be executed in any order, but results
remain tied to the exact baseline above.
