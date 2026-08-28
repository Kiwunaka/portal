# WO-013AU — Candidate.5 signing, Brain AWG route and physical runtime

Date: 2026-08-28

Status: `SIGNED_CANDIDATE_RUNTIME_EVIDENCE_GATES_OPEN`

## Objective

Bind the promoted platform/client/Core tuple to one immutable replacement
candidate, retain its hosted release-index signature, deploy only the already
reviewed Brain managed-profile correction, and run a bounded exact-candidate
physical Android control without converting missing AWG, Smart-DNS service
access, Windows, origin or provider evidence into a release PASS.

## Authority and scope

- Platform promotion source: `6ea08e9222dff67c93ffa0bb9585a57c5ffe220c`.
- Client promotion source: `6b596cefbc043c2da30b31007789cea7e30fc336`.
- Core product source embedded by the client:
  `e8eb7721fc6eaac6813d3a888ac90d0da1f541a1`.
- Candidate input release-index source:
  `1d1b7eec05f311aad3044249982ed6fa0f3ace0d`.
- Later release-index evidence-only merge:
  `22db1f6002057fc3d27f037295f75ea4f8eed10e`.
- Runtime deploy window remains frozen to Brain baseline
  `e5ef03ac7ab013d8810cc9c6ea9ccc40cebd11db` and reviewed one-file AWG source
  `83502f1cb9a54ce7ae088a36ed2f9e696c90d841`.

This WO records candidate, deployment and device evidence only. It does not
authorize a public GitHub Release, a stable pointer, repository publication,
HY2/Smart-DNS server installation, a marketing launch or a Gate G mutation.

## GitHub policy decision

The owner declined paid GitHub features and branch protection. Platform and
client promotion therefore use `OWNER_SOLO_EXCEPTION`; independent review is
not claimed. Branch protection was removed from the public Core and
release-index promotion branches. The private platform/client hosted runs that
GitHub did not start remain historical `BLOCKED_BY_ACCESS`, not PASS.

Repository visibility was not changed in this slice. A future public-source
transition still requires a separate secrets/history/generated-artifact audit
and an explicit visibility mutation.

## Exact candidate artifacts

`pokrov-1.2.0-candidate.5` contains six canonical artifacts:

| Artifact | Bytes | SHA-256 | Signing state |
|---|---:|---|---|
| Android universal APK | 295299185 | `2825a832a43404d7f16b42fbaf6f5e1f443505cca6a9ac8bf4e93e5ae46cbebb` | production Android certificate |
| Android arm64-v8a APK | 101346230 | `d3dcad53c40dd04f31152a0b45c59c2ba03a6d4dcf127f753448b3cdde63f5b6` | production Android certificate |
| Android armeabi-v7a APK | 90760708 | `ff830bdf8b5f8395f29c821be9d805b2cddae20e39c165d719727f6c7d935127` | production Android certificate |
| Android x86_64 APK | 109930165 | `d6678702b2d9844433e7f1cb2b9342cadf229eb4d8ed10e70788ab9acbf6d4d5` | production Android certificate |
| Android market AAB | 126256131 | `d4c00669ef5c551f6fb849cc34078b452a6fa43ba79b9f10f5c698fb007fd2d8` | production Android certificate |
| Windows x64 installer | 28913774 | `81c2a86ec3234162e85399ac348e36fcea413ee87e33b71b260533bdc1e6277f` | `NotSigned`; owner-accepted SmartScreen beta exception |

Android certificate SHA-256 is
`0a0602a7df5d96a0b427909d004f3ddf26def86587634bf16694da8d654b2500`.
The unsigned Windows exception is
`OWNER_ACCEPTED_UNSIGNED_WINDOWS_BETA_1_2_0`; it is not trusted-signing proof.

Supply-chain evidence:

- artifact-set digest:
  `488f5dfe059f46f91e9ffb25bc70f4082130f2901f7a3def8116f3d676586463`;
- CycloneDX 1.5 SBOM: 347 components, SHA-256
  `cc89624d7def361b6bbc676d081d6b8f3e4a8d3cbfb7be6def283745164c9790`;
- SLSA v1 provenance with six subjects, SHA-256
  `4359280476c14b834ec80fe7afc91f5eca1ec4b0d0b669030357292c2a11b72f`;
- support-pin embedding evidence, SHA-256
  `c233b1c1042d2ff0b9e38b738d5cbb32a92f5868d795a24f78d45f8601e012eb`;
- strict-v2 handoff, SHA-256
  `93f31532e033244e2082711b245ece5635e891e4cad99d14406017b40584afcd`.

The handoff is `valid_v2` but retains 14 manual gates, 10 blocking. A valid
handoff is not a GO decision.

## Hosted signature evidence

Public release-index source-contract run `33190227686` passed before the
candidate input merged. Manual signer run `33190309331` passed and emitted an
Actions-artifact-only manifest, detached signature and receipt:

- manifest SHA-256:
  `1f8d6ba056f66dc3f8ea76df16e42f5481fc17b111ea759f191eb4ad4af3c263`;
- detached signature SHA-256:
  `56ed2afe249491546d4e21f1c66490daa6ee376af9b94b53b7a7ea680cf3e874`;
- receipt SHA-256:
  `d39ad982b14c55e9e395753f73a9c3d6570ac912e3d8a967a15aac5a0d05060b`;
- signing key id: `pokrov-release-2026-01`;
- public-key validation: `READY_SIGNED_MANIFEST`;
- promotion authorized: `false`.

No tag, GitHub Release, public asset, store object or stable pointer was
created.

## Brain managed-profile route deploy

The guarded PLAN rechecked all `193/193` frozen live payload paths, found zero
mismatches and retained `runtime_mutated=false`. PLAN report SHA-256 is
`f9d04a3885504f7eaf0b855f66dffd326869bcaff3c6aebe41749192a4a35219`.

The owner-authorized APPLY then:

1. repeated the `193/193` baseline immediately before promotion;
2. staged, backed up and compiled only
   `portal_bot/api_client_routes.py`;
3. verified the old live target digest before replacement;
4. restarted only `portal-api`;
5. passed delayed service/public-health verification;
6. read back `193/193` reviewed candidate payload paths;
7. retained the backup and required no rollback.

The sanitized APPLY report SHA-256 is
`5610826930cb5c84d243dfd019b750bff90d9c40b4f5222a213bd102bdb57038`.
This proves the exact one-file Brain source deployment and health only. It does
not by itself select a device, decrypt a lab endpoint, start Core or prove a
tunnel.

## Exact physical Android evidence

The production-signed universal candidate installed byte-identically on the
physical Huawei. Version is `1.2.0+4046`; launch and crash-buffer checks pass.
The existing premium entitlement remained active.

An ordinary Frankfurt baseline produced:

- active `PokrovRuntimeVpnService`;
- Android `VpnTransportInfo` with `sessionId=sing-box`;
- validated VPN network state;
- DNS plus ICMP success for Cloudflare, ChatGPT, Gemini and Xbox;
- clean disconnect with no POKROV service, VPN transport or TUN.

This is physical exact-candidate ordinary-tunnel evidence. It is not HTTP
service access, selected-route attribution, RU-origin or AWG proof.

## Owned AWG boundary

The public location sheet correctly continued to show only `Обычный`,
`Белые списки` and `Белые списки тип 2`. AWG2/AWG3.1 are authenticated,
device-bound managed profiles and must not appear as public location variants.

A fresh Huawei binder PLAN found exactly one historical device identity,
matched the previously retained target install SHA-256
`52027bc09d91725fa7431165fbf2596fe11100ebafcf34402c9ce23e8da805ce`,
and confirmed source material availability without returning raw identifiers.

The first APPLY and two later PLAN retries failed before the remote helper:
SSH ended at protocol-banner/timeout. No policy/helper mutation occurred, no
AWG endpoint reached the client and neither AWG2 nor AWG3.1 Core was started.
Classify the exact-candidate AWG device matrix as `BLOCKED_BY_ACCESS`, with
`crypto_verdict=NOT_TESTED`. Do not reuse earlier pre-candidate Beeline UDP
observations as candidate.5 proof.

## External Smart DNS control

The candidate's existing default-off state machine was exercised with the
public Cloudflare DoH endpoint as a control, not as a claimed compatible
unblocking resolver:

- custom HTTPS `/dns-query` input accepted;
- direct DoH became available only after the custom endpoint was valid;
- external Smart DNS became available only after direct DoH plus selected AI
  or Games groups;
- UI explicitly stated that selected AI/Xbox traffic is direct and the public
  IP remains visible;
- Video and Social stayed separate and VPN-routed.

The first ordinary Amsterdam attempt ended at the canonical fail-closed egress
boundary and removed its service/VPN state. A single retry on the previously
proved Frankfurt baseline produced an active validated POKROV VPN and DNS plus
ICMP success for Cloudflare, ChatGPT, Gemini and Xbox. Android shell had no HTTP
client, and no resolver-path attestation was available. Record this as
`PASS_TUN_DNS_ICMP_ONLY`; actual ChatGPT/Gemini/Xbox web/API access, compatible
resolver behavior, DNS/SNI attribution, leak/privacy and origin proof remain
open.

Final cold readback restored:

- Frankfurt / ordinary profile;
- AdGuard DNS;
- direct DNS lab off;
- external Smart DNS normalized off and hidden because prerequisites are off;
- AI and Games selected through VPN;
- no POKROV service or VPN transport.

The secret-free physical runtime report SHA-256 is
`e4054d6da64e269c2892b72f66b819b0c1af41b7c624cb67bd4ae4dee06f3a20`.

## Completion-index effect

- `REL/REL-001` remains `I3`: candidate.5 has a signed manifest and solo
  source-control evidence, but public same-byte assets, exact final gates and
  stable promotion are absent.
- `REL_GATE/GATE-F` remains `I3`: the prior candidate.3 `NO_GO` is historical;
  Gate F has not yet been rerun for candidate.5.
- `FRKN_PLAN/W3-02` remains `I3`: the managed route is deployed, but exact
  candidate device binding is access-blocked before AWG Core start.
- `FRKN_SMART_DNS/SMARTDNS-01` remains `I3`: exact-candidate TUN/DNS/ICMP is
  stronger evidence, but there is no compatible owned resolver or service
  access/leak/rollback/origin proof.

No original or derived ledger row advances in this WO.

## Next actions

1. Restore trusted Brain SSH access, rerun the sanitized device PLAN and bind
   exact candidate.5 to AWG2; require client managed-profile readback, app-owned
   TUN, Core handshake, DNS/egress/leak and cleanup before AWG3.1.
2. Run AWG3.1 only after AWG2 reaches Core on a returning origin; cleanup must
   return the exact install to `default` even after failure.
3. Allocate an owned dedicated Smart-DNS IPv4 or approve a compatible service,
   then run guarded PLAN/APPLY/rollback and exact service-access/leak/origin
   evidence. Public Cloudflare DoH is only a control.
4. Execute the remaining candidate.5 Windows, provider/PostgreSQL/outbox,
   Operator, accessibility/performance and current/Brain/RU-origin gates.
5. Rebuild the Gate F decision from candidate.5 evidence. Public/stable
   promotion stays prohibited until it returns GO and a separately authorized
   Gate G operation is ready.
