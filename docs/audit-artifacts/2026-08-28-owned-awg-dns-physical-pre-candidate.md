# Owned AWG And DNS Physical Pre-Candidate Evidence

Date: `2026-08-28`

Registry class: `RETAINED_EVIDENCE`.

## Scope

This record covers one current-origin physical Android session on Beeline, the
owned DE AWG lab and the Brain control plane. It contains no device serial, raw
install/account identity, endpoint, key, profile or packet address.

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
| Direct HTTPS DoH | `PASS_CURRENT_ORIGIN` | Persisted state and runtime selected direct DoH; all `3/3` bounded AI/Games DNS queries returned valid DNS messages over HTTPS. |
| DNS-only service access claim | `NOT_IMPLEMENTED` | AI/Games application routes still target the active VPN. DNS success does not prove ChatGPT, Gemini or Xbox access without VPN. |
| Normal WARP after lab unbind | `PASS_WORKING_4044` | Exact device was absent from cohort and both lab allowlists; policy resolved the ordinary fallback, UI connected and independent IP plus DNS+egress probes passed. |
| Restored settings | `PASS_WORKING_4044` | DNS transport returned to VPN default; AdGuard, AI and Games remained enabled; runtime had no AWG final endpoint. |
| Phone cleanup | `PASS_WORKING_SESSION` | POKROV stopped, test package absent, Wi-Fi enabled and Hiddify foreground. Temporary phone/local diagnostics were removed. |

## Interpretation

The symmetric failure across two ports and two AWG profiles, combined with
successful phone-to-server delivery and missing server-to-phone echo, isolates
this session to reverse UDP on the current Beeline path. It does not support a
claim that POKROV cryptography, key alignment, Android socket protection or AWG
globally is broken. It also does not prove that AWG will work on another mobile,
Wi-Fi or RU origin.

The direct-DoH control proves only encrypted DNS reachability and valid
resolution. Current product behavior remains split routing through the VPN for
AI/Games application traffic. A real Smart-DNS/no-VPN access product would need
a separate architecture and evidence lane.

## Remaining Gates

- Build and bind the exact strict-v2 replacement candidate.
- Re-run AWG on an origin that returns UDP, then prove handshake, tunnel DNS,
  decrypted egress and leak behavior on the exact candidate.
- Complete Android lifecycle, permission revoke, screen-off, Wi-Fi/LTE handoff,
  per-app modes, blocked UDP 53, MTU, endurance, backup/privacy and OEM checks.
- Keep current-origin, Brain-origin and RU-origin results separate.

No row in this file authorizes public publication or promotion.
