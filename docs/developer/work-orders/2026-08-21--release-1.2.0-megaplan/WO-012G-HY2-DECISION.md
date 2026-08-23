# WO-012G — Hysteria2 decision and transport monitor registry

- Decision date: 2026-08-22
- Decision: `NO_GO_FOR_1.2.0`
- Scope: local architecture and release-wave decision
- Production/external actions: `NOT_AUTHORIZED`

## Decision

Do not add, enable or advertise a Hysteria2 lane in POKROV 1.2.0. Keep it as
a future bounded selector/fallback candidate, never as the sole bootstrap.
The current wave already preserves the TCP/TLS-like
`legacy_reality_fallback` and has introduced one independent UDP-family
experiment through the disabled, typed `awg2_lab` endpoint in the existing
sing-box graph. Starting a second protocol experiment before exact AWG2
artifact/device/origin evidence would increase test and rollback surface
without an observed failure domain that requires it.

This is a release-scope NO-GO, not a claim that Hysteria2 is ineffective. No
owned current-origin, brain-origin or RU-origin comparison was run, and the
decision cannot be presented as protocol performance evidence.

## Reopen criteria

Create a separate future WO only when all of these are true:

1. exact-candidate AWG2 and VLESS/REALITY evidence identifies a repeatable
   reachability or performance gap attributable to the current transport
   families;
2. a POKROV-owned HY2 endpoint, lifecycle owner and server-side kill/rotation
   path are available;
3. the proposal defines a direct typed sing-box subset, immutable provenance,
   synthetic fixtures, safe telemetry and one host TUN owner;
4. reachability uses a short bounded budget and failure returns to an existing
   bootstrap path;
5. physical-device, battery/thermal and distinct-origin evidence is funded and
   owner-authorized before any cohort.

## Monitor-only registry

| Record | Owner | Observe | Reopen trigger | 1.2.0 action |
|---|---|---|---|---|
| `MONITOR-01` AWG 3 and later obfuscation generations | Core owner | Official upstream schema, dependency, license and stable sing-box support | Current pinned AWG2 subset has an owned, measured gap and a compatible typed migration exists | Monitor only; no code/product claim |
| `MONITOR-02` HY2 Gecko, Mimic and port hopping | Core + network owner | Official upstream capability and owned test results | Reopen criteria above are satisfied and one bounded selector addresses the measured failure | Monitor only; no implementation |
| `MONITOR-03` TrustTunnel/fptn | Architecture owner | Maintained upstream, license, security ownership and operational dependency | A concrete production dependency has an accountable owner and beats the existing stack on retained evidence | Monitor only; no dependency/fork |
| `MONITOR-04` XHTTP, REALITY and AWG blocking trends | Network/operations owner | Sanitized POKROV-owned evidence with current-, brain- and RU-origin kept separate | Repeated exact-candidate failures cross an owner-approved threshold and name the affected ASN/network class | Monitor only; no public effectiveness claim |

No public APK observation, third-party endpoint, user identity, credential or
raw provider payload qualifies as evidence for this registry.

## Evidence ceiling

- HY2 decision and ownership: `I1 VERIFIED_DEFERRED`.
- Monitor registry: `I1 VERIFIED_MONITOR_ONLY`.
- HY2 runtime, server, artifact, device, performance and RU-origin proof: not
  implemented or run.
- Candidate and promotion state: `NOT_REQUESTED`.
