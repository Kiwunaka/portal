# WO-013AR — Managed Hysteria2 owner lab

- Date: 2026-08-28
- Scope: Core, platform and active Android/Windows client source plus local
  Android pre-candidate, Linux server artifact and read-only owned-node
  deployment-preflight evidence
- Result: `LOCALLY_PROVED_SOURCE_AND_ARTIFACT`
- Execution index: `I3 VERIFIED_LOCAL`
- Production/external actions: `NOT_AUTHORIZED_NOT_RUN`
- Candidate/publication: `NOT_CREATED`

## Owner decision and boundary

The owner reopened the bounded Hysteria2 lane requested by the FRKN plan. The
implementation is a closed `hy2_lab`, not a public transport promise and not a
second VPN engine. It reuses the official sing-box `1.13.0` runtime already
embedded in POKROV Core with QUIC support and keeps the host-owned TUN model.

The lab is disabled and kill-switched by default. It is reachable only through
the authenticated managed-profile path after exact contract, active-device,
platform, user/install, node, server-owner/state, generation and fresh
encrypted-material checks. Token subscriptions, raw node catalogs and manual
exports cannot carry its endpoint material.

Accepted subset:

- contract `pokrov.hy2.outbound.v1` with SHA-256
  `c96b38e58ea33f838f23b80a65f3a9a264e932b7248f206798df9a0b8fa0fb98`;
- one Hysteria2 outbound in the existing sing-box graph and one host TUN owner;
- one server port, verified TLS/SNI, ALPN exactly `h3`, bandwidth bounded to
  `1..1000` Mbps and optional Salamander obfuscation;
- encrypted device-bound platform material under a separate runtime secret;
- L3 action-intent provisioning with preview/audit/result limited to safe
  metadata and fingerprints.

Rejected subset: raw `hysteria2://` / `hy2://` conversion, `server_ports`, port
hopping, Gecko, Mimic, insecure TLS, raw public material, a second engine and a
second TUN owner.

## Exact source tuple

| Repository | Branch | Commit | State |
| --- | --- | --- | --- |
| Platform | `codex/hy2-owned-lab` | `8d607369e92fbd459ff76c87f491504ea5aa8f43` | managed encrypted material, rollout, migrations, API and L3 guard committed locally |
| Platform operations | `codex/hy2-owned-lab` | `8a97b538094c49546c35e9c82414178c53d8063b` | deterministic server bundle builder, reviewed template/unit, verify and read-only install/rollback plans committed locally |
| Platform remote operations | `codex/hy2-owned-lab` | `4c65912e657781e1c20c44f84c6434b91925b65b` | guarded remote PLAN/APPLY/ROLLBACK, strict runtime-config validator, exact receipt binding and automatic rollback committed locally |
| Client | `codex/hy2-owned-lab` | `850d9e395cb6a0b4a668dfbf67f0239b8f741216` | strict runtime validator and exact Android Core binding committed locally |
| Core | `codex/hy2-owned-lab` | `e8eb7721fc6eaac6813d3a888ac90d0da1f541a1` | capability/schema, fail-closed converter, tests and Android artifact contract committed locally |

No merge to `master`/`main`, release tag, release candidate, deployment,
public asset or stable-pointer change is part of this WO.

## Verification

Core:

- focused converter package: `PASS`;
- full Core script gate including brand, ABI, observability, AWG2, AWG3.1,
  HY2, CI contract, `go test ./...`, sing-box daemon/libbox/TLS: `PASS`;
- HY2 JSON schema validation: `PASS`;
- two independent Android AAR builds: `PASS_BYTE_IDENTICAL_TWO_BUILDS`.

Platform:

- focused HY2 service tests: `14/14 PASS`;
- managed-profile/kill rollback integration: `PASS`;
- HY2 plus client API, action-policy and module-slice selection: `37/37 PASS`;
- network rollout, SQLite/PostgreSQL migrations and action intents: `58/58 PASS`;
- server bundle focused tests: `4/4 PASS`;
- guarded remote installer plus bundle/emergency/manifest focused slice:
  `21/21 PASS`;
- infrastructure/observability regression: `28/28 PASS`;
- release-script/manifest regression: `44 PASS`, `21 subtests PASS`;
- script manifest and dependency contract: `PASS`;
- Python compile and `git diff --check`: `PASS`.

Client:

- runtime-engine tests: `67 PASS`, one declared real-DLL skip;
- app-shell tests: `411/411 PASS`;
- runtime-engine, app-shell and Android-shell analysis: `PASS`;
- exact cross-repository seed/version parity: `PASS`.

## Exact Android artifacts

Core AAR bound into the client:

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| `pokrov-core.aar` | `107390782` | `7c392883ee8a09c15e414a0e9d70a4d4d3cb259032e51c5481cd14a571950745` |

Production-signed client build `1.2.0+4046`:

| APK | Size | SHA-256 |
| --- | ---: | --- |
| universal | `295299185` | `ed22bb08dc0c2b14e2f6c0cb1ba116c032ffbf0164c5bca54ec89f82b99fe0d6` |
| arm64-v8a | `101346230` | `383634d79480140edb160f02ba993ff5858e3ade61b926ed3f82f7f2180972c6` |
| armeabi-v7a | `90760708` | `d66c8dd5aedf2dff83b696a63b88424f87ef9580fae26d38168b1a2a1168c648` |
| x86_64 | `109930165` | `1695c0f1b18f4366cf4e917a49f5f46d0e0723ae2ed5c48313efb290129c5438` |

All four APKs passed the existing package/version/non-debuggable/ABI and
production-certificate verification helper. These are signed local
pre-candidate artifacts, not release assets.

Immutable Linux/amd64 server bundle built from exact Core source:

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| `pokrov-hy2-server-e8eb772.zip` | `15229012` | `6877d3f1d73cd7d493d8e4a178aeb78e6476715e95bee6791c2210ce05089332` |
| embedded `pokrov-sing-box-hy2` | `41701524` | `026066be82775af0fef6869f38442775b8737695f48f3bdf26d826a2638fcf5e` |

Two complete ZIP builds and the two Linux binary builds inside each run were
byte-identical. The builder also compiled a host checker from the same pinned
source/tag and passed `sing-box check` against a temporary synthetic TLS and
credential fixture. The retained ZIP contains only the ELF, exact contract,
placeholder-only config, inactive systemd unit, operations note and license
notices. Its manifest says `deploy_authorized=false`,
`deployment_performed=false` and `raw_runtime_material_included=false`.

## Read-only owned-node preflight

The guarded installer was executed without `--apply` against owned node `de`
using strict retained host keys and the exact immutable bundle. The sanitized
result was `PLAN`, `mutation_performed=false`, with:

- root and required tools ready;
- UFW installed and active, with no pre-existing HY2 rule;
- UDP `443` free;
- no existing HY2 release/current/config/certificate/key/unit target;
- service inactive and not installed;
- runtime material not present;
- raw host and runtime material absent from output.

The deployed Brain does not yet contain the branch-only HY2 rollout field, so
kill-switch readback is `unavailable`. The installer treats that as information
in `PLAN` and a hard failure in `APPLY`. No file, service, firewall, pointer,
Brain setting or client material was changed, and no external handshake ran.

## Physical Android boundary

The exact arm64 APK upgraded successfully on the returned physical phone.
Package/version readback, launch/resumed activity and the release-only
localhost audit passed with zero baseline and after-launch listeners. No fatal
package error was observed. Because the lab stayed disabled and no endpoint
material existed, no `tun0` appeared. The app was then force-stopped and
readback confirmed stopped state with no tunnel.

This proves install/launch and default-off safety for the exact local artifact.
It does not prove Hysteria2 configuration delivery, handshake, DNS, egress,
service access, battery/thermal behavior or mobile/RU-origin effectiveness.

## Evidence ceiling and next action

`FRKN_HY2/HY2-01` advances from `I1 VERIFIED_DEFERRED_1_2_0` to
`I3 LOCALLY_PROVED_SOURCE_AND_ARTIFACT`. `MONITOR-02` remains `I1` for Gecko,
Mimic and port hopping. Candidate.3 and every release gate remain unchanged.

Before `I4`, first deploy the exact HY2-aware platform control-plane while its
lab remains disabled and kill-switched, then materialize receipt-bound
root-only TLS/password state outside Git. Separately authorize installation of
the exact immutable server bundle and provision the client endpoint through
the guarded encrypted-material action. Then run a short bounded exact-build matrix for
managed delivery, handshake, traffic, DNS/leak, teardown, current-origin,
Brain-origin and RU-origin. Do not deploy or restart Brain or delivery-node
services without a separate explicit owner authorization.
