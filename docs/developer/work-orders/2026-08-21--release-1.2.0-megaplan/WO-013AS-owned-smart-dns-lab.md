# WO-013AS — Owned selective Smart DNS laboratory

Status: `I3 LOCALLY_PROVED_SOURCE_ARTIFACT_AND_DEVICE_STATE`

Date: 2026-08-28

Release effect: local pre-candidate evidence only. This work order does not
create a candidate, deploy a resolver/relay, change production routing, publish
a public artifact, or prove live DNS/service access.

## Outcome

Create one bounded, default-off Smart DNS laboratory for selected AI and gaming
service web/API domains without adding another client VPN core or inventing a
new cryptographic protocol.

The resulting architecture is deliberately narrow:

1. the existing client sing-box TUN remains the only route/DNS owner;
2. only DNS questions for a user-selected allowlist are sent to the configured
   HTTPS `/dns-query` endpoint through the existing direct outbound;
3. the owned DNS service is non-recursive and returns its owned public proxy
   IPv4 only for allowlisted `A` questions;
4. the same dedicated public TCP/443 listener forwards application TLS only
   when one visible, canonical SNI matches the same allowlist;
5. TLS remains opaque end to end: there is no certificate injection, TLS
   interception, payload decryption, custom crypto, second Xray, or second TUN;
6. selected application connections are direct from the device to the relay,
   so the user's ISP-visible address is not hidden and Android may still show a
   VPN system surface for split-policy ownership.

This can assist only the bounded web/API/catalog/login surfaces represented by
the policy. It does not promise gameplay, UDP matchmaking, console protocols,
account eligibility, region eligibility, QUIC/ECH compatibility, or access to
any named service.

## Architecture and trust boundaries

| Boundary | Accepted input | Fail-closed rule |
|---|---|---|
| Client persisted preference | custom HTTPS URL, direct DNS transport, AI and/or gaming-service purpose group | require exact `/dns-query`, port 443, no query/fragment/token; invalid restored state disables the lab and direct construction fails before staging |
| Client DNS materialization | selected policy suffixes only | add one route-to-server DNS rule and preserve the existing final resolver for all other names |
| Public DoH listener | one IN-class DNS question | allowlisted `A` gets the owned proxy IPv4; other allowlisted types get `NOERROR/NODATA`; outside names get `REFUSED`; recursion is never available |
| Public TLS relay | bounded TLS ClientHello with one visible canonical SNI | missing, malformed, ambiguous, ECH-concealed or non-allowlisted SNI closes before origin connect |
| Origin resolution | fixed authenticated DNS-over-TLS server on public IP:853 | reject private/special/self addresses, bound CNAME traversal, connect only to TCP/443 |
| Runtime capacity | public client source address | enforce global/per-source connection, request, parser, timeout, lifetime and byte ceilings; do not log source address, question, SNI or payload |

The public SNI relay has no safe per-client authentication channel in the
current client contract. It is therefore a bounded public owner-lab relay, not
an authenticated production proxy. Exact allowlists, public-address rejection
and resource limits reduce abuse surface but do not create client identity.
Deployment remains forbidden until a dedicated owned IPv4, a successful
no-mutation installer PLAN, receipt-bound runtime material and an explicit
owner authorization exist. Live limits and rollback still require separate
runtime proof.

## Exact source contract

- canonical policy:
  `shared/contracts/network/smart-dns-policy.v1.json`;
- policy schema/state: `pokrov-smart-dns-policy-v1` /
  `owner_lab_default_off`;
- current policy SHA-256:
  `b6977f6f6a5ee48898116820d1db252b5b670cb7b86959c78f7bdbc7de90e0fa`;
- owned server source: `infra/owned-smart-dns/`;
- server implementation: Go `1.25.13`, `github.com/miekg/dns v1.1.72`,
  Linux/amd64, CGO disabled for the retained bundle;
- build/verify owner: `scripts/build_owned_smart_dns_server_bundle.py`;
- guarded remote operation owner:
  `scripts/remote_install_owned_smart_dns_lab.py`;
- cross-repository byte-parity owner:
  `scripts/check_smart_dns_policy_parity.py`;
- active client copy: `POKROV-app/config/smart-dns-policy.v1.json`;
- active client materializer:
  `POKROV-app/packages/app_shell/lib/client_routing_preferences.dart`.

The bundle excludes runtime listener address, DoH hostname, certificate,
private key and upstream resolver coordinates. The systemd unit is packaged
inactive and non-root with only the low-port bind capability.

## Exact local evidence

Source identity:

- platform commit `2d18fd7641ec6c90286f333ae24a6f1ac794f78a`;
- client commit `75e82b061cd3f127ae640733cfb4fc1a6aef2e62`;
- both commits are pushed to their separate `codex/hy2-owned-lab` branches;
- Core is unchanged for this slice.

| Check | Result | Ceiling |
|---|---|---|
| `go test ./...` | `PASS` | server unit/source behavior only |
| `go vet ./...` | `PASS` | server static analysis only |
| focused platform bundle/parity tests | `4 passed` | builder and parity contracts only |
| script manifest check | `PASS` | inventory ownership only |
| focused Ruff check | `PASS` | Python source only |
| platform/client policy parity | `PASS`, exact SHA above | source bytes only |
| app-shell focused routing tests | `17/17 PASS` | client materialization/persistence only |
| complete app-shell tests | `412/412 PASS` | exact client source regression only |
| Flutter analysis | `PASS` | exact client source only |
| cross-repository release-seed validation | `PASS` with explicit platform/client/Core roots | pre-candidate source consistency only |
| deterministic Linux/amd64 bundle build | `PASS`, two builds byte-identical | local server artifact only |
| bundle self-verification | `PASS_LOCAL_IMMUTABLE_BUNDLE` twice | no server install or runtime claim |
| guarded remote installer tests | `7/7 PASS` | PLAN/APPLY/ROLLBACK source contract only; no SSH or mutation |
| Android production package verification | `PASS` for universal and three split APKs | working pre-candidate artifacts only |
| LDPlayer install/readback and Smart-DNS state machine | `PASS_4046_LDPLAYER_EXTERNAL_SMART_DNS_STATE_MACHINE` | no DNS transaction, tunnel or access claim |
| physical Huawei install/readback and default-off gate | `PASS_4046_PHYSICAL_EXTERNAL_SMART_DNS_DEFAULT_OFF` | no setting mutation, DNS transaction, tunnel or access claim |
| Go race detector | `NOT_RUN_TOOLCHAIN_MISSING` | Windows host has no C compiler; never counted as PASS |

Retained server artifact:

- ZIP: `pokrov-smart-dns-server-2d18fd7.zip`, `2911894` bytes;
- ZIP SHA-256:
  `d7ef558dc071852d942cf3001b16f2c2125c7c777db7a79b575ea0eae06d0195`;
- embedded Linux/amd64 binary: `7118996` bytes, SHA-256
  `f0ac013f5a320989cd9696e83bee4a9b83988064bf81081a22a75e3d923248e5`;
- bundle policy SHA-256 matches the canonical/client value above;
- two independent builds from the exact platform commit produced the same ZIP
  SHA-256 and both passed bundle verification.

Retained working Android artifacts from the exact client commit:

| ABI | Size | APK SHA-256 | Device readback |
|---|---:|---|---|
| universal | `295299185` | `4beff678b2e0d5fcad8d84cc94b50ac56e48e44d87e95000e032593b0dbbd10e` | package verification only |
| arm64-v8a | `101346230` | `c7e21ca3aa5baff575e515d22937c1a6b431068afdd0dad5fb6955b966cea6f9` | exact bytes installed/read back on Huawei `ADA_AL00U` |
| armeabi-v7a | `90760708` | `db0805e4ccd6c80e5dbea02c2d6e3911ca86989e095ce50586756cb3463ce60a` | package verification only |
| x86_64 | `109930165` | `4beebad0f2efeef03b6c6a9ea7634c7c90515d5ec3f7bcdf4a8b74adcc83cd4b` | exact bytes installed/read back on LDPlayer |

Every APK is release/non-debuggable, package
`space.pokrov.pokrov_android_shell`, version `1.2.0+4046`, and signed by
certificate SHA-256
`0a0602a7df5d96a0b427909d004f3ddf26def86587634bf16694da8d654b2500`.
The production build bound public emergency key ID `emg-20260815-v1`; no
private key was copied into the repository or retained evidence.

LDPlayer proved the complete UI gate without starting a connection: Smart DNS
was unavailable before custom exact-path DoH plus direct DNS were selected,
remained off by default when prerequisites became valid, could then be enabled,
showed the explicit visible-IP/compatible-server warning, and returned to
automatic DNS/off. The physical phone proved exact APK installation and the
existing safe default-off gate with AdGuard/direct DNS off; no preference was
changed. Cleanup left no POKROV service on either device and returned the phone
to its prior Chrome foreground.

## Required next evidence

1. allocate a separate owned public IPv4, stage receipt-bound root-only runtime
   material and retain a sanitized, no-mutation installer PLAN;
2. separately authorize that exact dedicated-node install and retain
   DoH/SNI/limits/
   rollback evidence before any service-access test;
3. keep service-access, DNS leak, lifecycle, current-origin, Brain-origin and
   RU-origin evidence distinct; none may be inferred from source or install.

## Completion index

- `FRKN_SMART_DNS/SMARTDNS-01`:
  `I3 LOCALLY_PROVED_SOURCE_ARTIFACT_AND_DEVICE_STATE`;
- `I3` is satisfied by exact pushed source commits, reproducible immutable
  server artifact, full client regression, production-signed working packages
  and two-device default-off/state-machine proof;
- `I4` requires exact-candidate dedicated-node DNS/SNI/rollback and required
  physical/origin matrices;
- `I5` requires separately authorized immutable promotion and observation.

## Rollback

Client rollback disables or removes only the persisted external Smart DNS
preference and restages the existing managed profile; normal final DNS and VPN
routes remain the baseline. Server rollback must first disable client selection,
stop the exact receipt-bound service, prove TCP/443 absent, restore only the
recorded previous pointer/config/unit/firewall state and retain the failed
release. No rollback step is authorized by this document.
