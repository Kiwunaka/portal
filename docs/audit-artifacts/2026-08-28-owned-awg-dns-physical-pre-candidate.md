# Owned AWG And DNS Physical Pre-Candidate Evidence

Date: `2026-08-28`

Registry class: `RETAINED_EVIDENCE`.

## Scope

This record covers current-origin physical Android sessions on Beeline and
Wi-Fi, one LDPlayer control, the owned DE AWG lab and the Brain control plane.
It contains no device serial, raw install/account identity, endpoint, key,
profile or packet address.

The tested client was production-signed working package `1.2.0+4044`, SHA-256
`7417191b9fab0469e2040ae535a5e51ca34821da9848e3af5a26aaf7a2f04f45`,
`101348658` bytes. Its certificate matched the local production-signing
metadata. `candidate_created=false`: this is not strict-v2 candidate or
promotion evidence.

## Results

| Surface | Result | Evidence boundary |
| --- | --- | --- |
| Owned app API ingress | `PASS_CURRENT_ORIGIN` | Physical Beeline refreshed the managed profile through the owned app ingress. |
| Android outer-socket protection | `PASS_WORKING_4044` | The host granted both observed Core socket-protection requests. |
| AWG2 live alignment | `PASS_BRAIN_NODE` | Alignment v2 passed keys, peer, port, address, S/H and header protection; padding/trailer defaults matched. |
| AWG3.1 live alignment | `PASS_BRAIN_NODE` | Alignment v2 passed the same fields plus `content_padding_addition=64-512` and randomized trailers. |
| AWG2 physical handshake | `BLOCKED_BY_NETWORK_CURRENT_ORIGIN` | Server observed both encrypted directions but no fresh handshake or inner packet. Guarded UDP control: server received/echoed `3/3`, phone received `0/3`. |
| AWG3.1 randomized physical handshake | `BLOCKED_BY_NETWORK_CURRENT_ORIGIN` | Same guarded UDP control result, `3/3` server receive/echo and `0/3` phone receive. Fixed-size handshake classification is inapplicable to randomized trailers. |
| AWG2 no-carrier policy readback | `PASS_BRAIN_CONTROL` | Guarded post-session readback resolved the exact current physical and LDPlayer device identities to `awg2_lab` with an explicit no-carrier context, then resolved both to the ordinary fallback after cleanup. This proves policy selection only. |
| AWG2 physical Wi-Fi activation | `FAIL_WORKING_4044_CLIENT_ACTIVATION` | Internet and DNS passed outside a VPN, but a bounded outer capture retained no handshake and zero AWG receive/send bytes. The app returned to disconnected state and Android exposed no VPN transport. |
| AWG2 LDPlayer activation | `FAIL_WORKING_4043_CLIENT_ACTIVATION` | After exact device-rank refresh and no-carrier lab readback, automatic connect showed connected without Android VPN transport and emitted no AWG traffic; explicit Frankfurt selection then failed as unavailable before tunnel start. |
| AWG3.1 Wi-Fi / LDPlayer repetition | `NOT_RUN_DUE_TO_PRECONDITION` | AWG2 never reached the cryptographic path in either control. Repeating the parallel profile would not distinguish AWG3.1 behavior until client managed-profile activation is fixed. |
| Direct HTTPS DoH | `PASS_CURRENT_ORIGIN` | Persisted state and runtime selected direct DoH; all `3/3` bounded AI/Games DNS queries returned valid DNS messages over HTTPS. |
| DNS-only service access claim | `NOT_IMPLEMENTED` | AI/Games application routes still target the active VPN. DNS success does not prove ChatGPT, Gemini or Xbox access without VPN. |
| Normal WARP after lab unbind | `PASS_WORKING_4044` | Exact device was absent from cohort and both lab allowlists; policy resolved the ordinary fallback, UI connected and independent IP plus DNS+egress probes passed. |
| Restored settings | `PASS_WORKING_4044` | DNS transport returned to VPN default; AdGuard, AI and Games remained enabled; runtime had no AWG final endpoint. |
| Phone cleanup | `PASS_WORKING_SESSION` | POKROV stopped, the exact device was removed from the cohort and both lab allowlists, policy returned to the ordinary fallback, Wi-Fi was restored off and Hiddify was foreground. Temporary phone/local diagnostics were removed. |
| LDPlayer cleanup | `PASS_WORKING_SESSION` | POKROV stopped, the exact emulator device was removed from the cohort and both lab allowlists, policy returned to the ordinary fallback and temporary emulator diagnostics were removed. |

## Interpretation

The Beeline result remains a reverse-UDP current-origin block: both profiles
reached the server, while their guarded echoes did not return to the phone. The
later Wi-Fi/no-carrier controls expose a separate earlier failure boundary.
Policy readback selected AWG2 for both exact devices, but neither installed
client emitted AWG traffic; LDPlayer also exposed a selected-location rejection.
That is a client managed-profile activation/fallback gap, not evidence about
AWG2 or AWG3.1 cryptography. It must be fixed before another protocol loop.

The direct-DoH control proves only encrypted DNS reachability and valid
resolution. Current product behavior remains split routing through the VPN for
AI/Games application traffic. A real Smart-DNS/no-VPN access product would need
a separate architecture and evidence lane.

## Remaining Gates

- Fix and retain the Android managed-profile activation path so an exact
  no-carrier lab selection reaches Core without cached legacy fallback or a
  selected-location rejection.
- Build and bind the exact strict-v2 replacement candidate.
- Re-run AWG2 on an origin that returns UDP, then AWG3.1, and prove handshake,
  tunnel DNS, decrypted egress and leak behavior on the exact candidate.
- Complete Android lifecycle, permission revoke, screen-off, Wi-Fi/LTE handoff,
  per-app modes, blocked UDP 53, MTU, endurance, backup/privacy and OEM checks.
- Keep current-origin, Brain-origin and RU-origin results separate.

No row in this file authorizes public publication or promotion.
