# WO-013BE — AWG endpoint default-resolver correction and physical pass

## Outcome

The common Android AWG selected-endpoint failure from WO-013BD is corrected on
new source-bound pre-candidate bytes. Core `a45d69e...` makes its owned AWG
endpoint resolve the inner FQDN through the configured default domain-resolver
transport and strategy instead of empty DNS query options. It preserves the
authenticated hostname, official upstream cryptography and fail-close, and
pins no provider IP.

Production-signed client `68779c4...` plus that Core passes AWG2 and AWG3.1 on
LDPlayer and on one physical Huawei/Android 12 device over Beeline with Wi-Fi
disabled. Both physical profiles reach green connected state and retain it
beyond the endpoint-probe window; the prior exact terminal category
`egress_probe_dns_lookup` does not return. This closes the diagnosed common
resolver defect. It does not create or prove a replacement candidate.

## Exact source and artifact contract

| Item | Exact identity | Result |
|---|---|---|
| Platform | `9281b401fe0ad58c7adbb2bd2316fbbb40c59977` | clean `master`; exact local aggregate owner |
| Client release truth | `f500728ce1fef54a32573263999652383cd86ad2` | clean and equal to `origin/main` |
| Client runtime binding | `68779c4dc806c2153d415ca8ca186c9130502f21` | Core artifacts and machine contract bound |
| Core | `a45d69e40ed7d892619a2b5c4592a527f630665e` | clean and equal to `origin/main` |
| Android AAR | `107425409` bytes; `ce82f54b…54dd` | two byte-identical builds; four ABIs |
| Windows DLL | `55426048` bytes; `53b5e82a…4652` | two byte-identical builds; 15 exports; proxy-only `100/100` |
| ARM64 APK | `101366934` bytes; `b583205d…7296` | `1.2.0+4046`; release; non-debuggable; production signer; exact install/readback |
| x86_64 APK | `109952213` bytes; `3d95d82d…fa4` | `1.2.0+4046`; release; non-debuggable; exact LDPlayer install/readback |

The embedded ARM64 Core entry matches the bound AAR entry. Android and Windows
still use one exact Core source revision; no second engine or app-side crypto
fork was added.

## Root cause and correction boundary

The preceding diagnostic client retained `egress_probe_dns_lookup` for both
AWG2 and AWG3.1. Their tunneled resolver transports differed, so the shared
failure was below those resolver definitions. The Core AWG endpoint itself
resolved its inner hostname with empty query options, bypassing the profile's
`route.default_domain_resolver` and the Android default-network DNS transport.

The correction loads the NetworkManager default domain-resolve options and
binds the configured resolver transport for both endpoint dial and packet
listen paths. Focused AWG tests prove the explicit strategy propagates, and the
full Core test script passes. Resolver or endpoint-probe failure remains
terminal and cannot manufacture green state.

## Runtime results

### LDPlayer

- exact x86_64 production APK install/readback: `PASS`;
- exact root-verified lab identity selection: `PASS`;
- AWG2 retained connected state after the probe window: `PASS`;
- AWG3.1 retained connected state after a fresh retry and probe window: `PASS`;
- final default bind and stopped POKROV state: `PASS`.

This is emulator evidence only and does not substitute for mobile-origin proof.

### Physical Android / Beeline

- exact ARM64 production APK install/readback: `PASS`;
- Wi-Fi disabled and mobile data active for both runs: `PASS`;
- AWG2 green connected state beyond the probe window: `PASS`;
- AWG3.1 green connected state beyond the probe window: `PASS`;
- prior `egress_probe_dns_lookup` terminal category absent: `PASS`;
- final default bind, POKROV stop, network-state restore and prior foreground
  restore: `PASS`.

The UI still showed asynchronous location-copy as checking; this does not
promote broader location, leak or origin claims. The verified connection state
remained green and the old fail-close path did not fire.

## Cross-repository local quality

The exact clean tuple platform `9281b40...`, client `f500728...` and Core
`a45d69e...` passes the bounded local-quality aggregate `15/15`. Client analyze,
413 widget tests, seed/docs contracts, webapp lint/build/69 cabinet E2E tests,
marketing build/SEO/responsive checks, admin build and all static performance
stop budgets pass. The report correctly retains `candidate_proven=false` and
`promotion_status=MANUAL_OWNER_TEST`.

## Release interpretation and next work

- Phase 10 remains `I3`; source-bound physical proof cannot become `I4` without
  exact replacement-candidate binding and the remaining matrix.
- Candidate.5 remains immutable `REJECTED_FOR_REPLACEMENT`; its frozen Gate F
  result is not rewritten.
- `W3-02`, `W3-03`, `W9-05` and `UNCERT-02` receive corrected status/evidence
  text but no index advancement.
- Windows live app/service/TUN/DNS/AWG, Android WARP/per-app/network-change/
  Doze/Private-DNS/IPv6/leak/lifecycle/endurance, compatible Smart-DNS service
  access and attribution, RU-origin and comparable metrics remain open.
- No tag, replacement candidate, Gate F rerun, public asset, store object,
  stable pointer or promotion occurred.

The next transport task is live Windows parity on the same Core DLL, followed
by the remaining Android and Smart-DNS matrices. Only then may a new immutable
candidate bind the exact Android/Windows bytes and repeat the required device
and Gate F checks.

## Evidence

Machine-readable evidence:
`evidence/013BE-awg-default-resolver-physical/013BE-awg-default-resolver-physical.json`.
Its SHA-256 is
`276ca83625957de8e2357b8eb20bd3086043e776693abc7100055b54105cfe07`.

The sanitized external phone/LDPlayer evidence remains outside Git and is
digest-bound from the machine record. No raw endpoint, address, key, config,
device serial, install ID or account identifier is retained here.
