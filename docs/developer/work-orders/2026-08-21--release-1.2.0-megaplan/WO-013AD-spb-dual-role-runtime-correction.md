# WO-013AD — SPB dual-role bridge diagnosis and runtime correction

Status: `STALE_TYPE3_DISABLED_CLIENT_RECOVERY_MERGED_NEXT_CANDIDATE_OPEN`
Phase: `11`
Current signed candidate: `pokrov-1.2.0-candidate.2`
Next candidate: `NOT_CREATED`
Recorded: `2026-08-27`
Production mutation: `PERFORMED_BOUNDED_ROLLOUT_DISABLE`
Public/stable mutation: `NOT_PERFORMED`

## Outcome

The physical Beeline failure domain is now resolved more precisely than the
earlier 013E/013AC observations. `ru_spb` is one physical server with two
roles: a normal Saint Petersburg delivery exit and an advertised type-3 RU
bridge identity. The deployed self-hop guard correctly removes that bridge
when Saint Petersburg itself is selected, because
`client -> SPB bridge -> same SPB exit` would be a loop.

The separate type-3 identity advertised for foreign exits was stale on the
same physical server: DNS, SSH host identity and node ownership matched the
normal SPB host, but the advertised bridge identity did not match the active
normal delivery profile and had no matching active listener/service. This is
why direct SPB could work while foreign `type 3` failed closed.

The production rollout was corrected atomically by changing only
`ru_bridge_relay.endpoints[id=ru_spb].enabled` from `true` to `false` after a
protected rollback snapshot. The endpoint record was retained. The normal SPB
delivery profile, listener and direct route were not changed. Active bridge
ids are now `mini` and `ru`; type 1 and type 2 remain available.

Client PR 23 then fixed the follow-on state bug exposed by that server
correction. A successful catalog refresh now resets a removed or disabled
saved bridge variant on the still-selected city to available `direct`,
persists the change and uses the normal reconnect path. The compact Android
variant sheet also scrolls through four or more rows, and private variant
probes use the owned authenticated-egress marker instead of the previous
third-party HTTP probe.

## Exact runtime and source identities

| Surface | Exact identity | Evidence state |
|---|---|---|
| Current signed candidate | `pokrov-1.2.0-candidate.2`; client `e6c29d1201eded0d045a3e75f43beff8ae24bd8f` | remains current signed evidence basis; not rewritten |
| Exact candidate.2 Android arm64 APK | 101213906 bytes; SHA-256 `a1ac79a979b3f80036ad9b817790e3c3dd00f8c2483901215b74577381a5cbc9`; `1.2.0 (2030)` | production signer; physical Beeline slice below |
| Client correction | PR 23, head `86fa4660acf0cf94645250a33a979fc536c7d00c`, merged `main` `61ce563e6c09a3ab7aefbce6c4d292cd7eba5ff4` | PR/post-merge Release v2 runs `33027773832`/`33028498506` `PASS` |
| Local correction smoke APK | arm64, 101213906 bytes, SHA-256 `2e61e2e55f0cffb16f9234549ac8c05cc2c15120c29f7a8024ab4498f8b5e149` | production Android certificate, but non-candidate emergency-pin placeholder; deleted after test |
| Production rollout before | redacted canonical JSON SHA-256 `366a8266f38fc88939b89c2096e9aec5630581e91bdff2e0d71362394c3942e7` | protected rollback snapshot created |
| Production rollout after | redacted canonical JSON SHA-256 `7cf44878b55d4bba798fbc07baa28fd513db3822a09a36e370a1e386612d7512` | only `ru_spb.enabled=false`; active ids `mini`, `ru` |

No raw host, key, UUID, short id, SNI or provider payload is retained in this
work order or its evidence JSON.

## Physical Huawei / Beeline LTE matrix

Wi-Fi was disabled for the mobile slice. The POKROV protected state is reached
only after the host/Core selected-outbound probe succeeds, so a green
`Подключено` state is bounded evidence of TUN establishment, DNS resolution
and HTTPS egress for that selected route. EMUI denied raw-socket ping to the
ADB shell; that command is explicitly not counted as proof.

| Artifact / route | Result | Label and boundary |
|---|---|---|
| Exact candidate.2, Saint Petersburg direct | reached protected state | `PASS` for this exact APK/device/Beeline slice |
| Exact candidate.2, Saint Petersburg type 1 | reached protected state | `PASS` for this exact APK/device/Beeline slice |
| Local correction smoke, saved Frankfurt type 3 after catalog refresh | automatically persisted Frankfurt `direct`; no blank/stale selected row remained | `PASS` client recovery behavior; not candidate proof |
| Local correction smoke, Frankfurt direct | reached protected state | `PASS` for smoke source/device/Beeline only |
| Local correction smoke, Saint Petersburg type 2 | reached protected state as `Санкт-Петербург · Белые списки тип 2` | `PASS` for smoke source/device/Beeline only |
| Local correction smoke, Frankfurt type 3 before production disable | fail-closed after selected-outbound egress proof failed; VPN was stopped | `PASS` fail-closed behavior and reproduction; route availability failed |
| Live catalog after production disable | type 3 absent globally; SPB and foreign cities retain direct/type 1/type 2 | `PASS` sanitized UI/readback |

After testing, VPN was disconnected, the pre-test production-signed local lab
APK SHA-256 `1ba37463c9549a6d5ba128850e1bf5825187fe185a621e9f8dc62c7cde1a4158`
was restored as `1.2.0 (4031)`, Wi-Fi was re-enabled and temporary device/UI/
build artifacts were deleted. `flutter clean` removed 2358715588 bytes from
the temporary client worktree.

## Verification

- client `flutter analyze --no-pub`: `PASS`;
- focused variant, recovery and materialization tests: `PASS`;
- combined changed client suites: `246/246 PASS`;
- client PR/post-merge Release v2 gates `33027773832`/`33028498506`:
  `PASS`;
- production rollout canonical readback changed only the intended endpoint
  enable flag and retained a rollback snapshot: `PASS`;
- direct SPB and the remaining type-1/type-2 mobile routes above: `PASS` with
  the exact artifact boundaries shown in the table.

## Release decision

No execution-ledger row advances. Candidate.2 remains the current signed
evidence basis, but it is not promoted: the live type-3 rollout changed after
its freeze and its client source lacks the stale-variant recovery merged in
`61ce563...`. A new exact candidate must bind current platform/client/Core/
release-index heads, use the canonical emergency signing pin, rebuild all
artifacts, regenerate SBOM/provenance/handoff/signature and repeat the required
physical/origin gates.

Type 3 stays disabled until its separate identity is rebuilt on an isolated
owned listener, verified from at least the relevant mobile origin and then
re-enabled through a fresh rollout. Direct SPB and the working type-1/type-2
paths must not be repurposed for that experiment.

Public `v1.2.0`, six public assets and the stable pointer remain absent and
prohibited. Windows live TUN/DNS/rollback, full Android OEM/handover/Doze,
current/Brain/RU-origin aggregate, provider, Operator and legal gates remain
open.
