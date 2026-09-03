# WO-013FM — candidate.25 Windows direct-only TUN/DNS and connected reboot

Status: `PASS_EXACT_CANDIDATE25_DIRECT_ONLY_TUN_DNS_AND_CONNECTED_REBOOT_RESTORE`

Observed: `2026-09-03T07:04:35Z`–`2026-09-03T07:25:16Z`

Production/public mutation: `NONE`

## Outcome

Exercise the exact installed candidate.25 Windows service and Core inside the
isolated Windows 11 VM without taking control of the owner's desktop. A
secret-free synthetic direct-only profile passes the complete service-owned
TUN/DNS lifecycle and a connected guest reboot restores the exact baseline.

This proves the candidate.25 Windows dataplane substrate, authenticated local
IPC, Core startup, TUN creation, DNS ownership, release-health endpoint access,
disconnect rollback and guest-reboot rollback. It does not prove a managed
subscription, selected POKROV node, DE/AWG egress, Smart DNS or the complete
`windows_live_network` Gate F row.

## Exact boundary

| Item | Identity |
|---|---|
| Candidate | private signed `pokrov-1.2.0-candidate.25`, app `1.2.0+4053` |
| Windows setup | SHA-256 `ffc9b07c59f75372b48c5c1e94551d6d9af710ac0287cd1352142b0964707fb3`, `29139238` bytes |
| Installed snapshot | `candidate25-clean-installed-ipc-20260903`, exact `11/11` predecessor proof |
| Client/Core source | `54259b0f84e16c58e2d1f5f04b369af4fd0834b2` / `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Direct fixture | SHA-256 `b829c67b06339fc5ae2671ad7b1818964a8063d9c114b4b0acd0ea840da16272`, `1364` bytes, no connection material |
| VM network | bridged physical Ethernet; the owner's host tunnel and network settings remain untouched |

## Endpoint reconciliation

The earlier WO-013FL baseline used `portal.pokrov.space` as a DNS sentinel and
incorrectly described its failure as a control-plane prerequisite. The active
client's canonical control plane is `api.pokrov.space`; `connect.pokrov.space`
owns delivery and `dns.pokrov.space` owns Smart DNS. In the exact VM all three
names resolve, TCP 443 to the API succeeds, `/api/health` returns `200`, and
the public egress proof returns `204` with the expected fixed proof header.

The candidate UI opens normally in interactive guest session 1 and shows the
first-run choice between a free trial and an activation code. No account,
trial, code, entitlement or production record is created. The managed-profile
path therefore remains a separate action-time owner gate.

## Headless service and direct-only result

The production `POKROV.Service.v1` pipe accepts the installation owner through
protocol v1 and runtime-control capability negotiation. Initialization moves
from `artifact_ready` to `initialized`. A connect request without a profile is
rejected as `profile_not_staged`, preserving fail-closed behavior.

The secret-free direct-only profile then passes:

- profile stage: `config_staged`, `can_connect=1`;
- connect: `running=1`, `core_egress_validated=1`, `dns_ready=1`;
- tunnel adapters: `0 -> 1`;
- route and DNS fingerprints change while connected;
- ordinary DNS resolution and `api.pokrov.space/api/health` return successfully;
- public egress is observed but remains unchanged, as required for a direct
  fixture; neither raw address is retained;
- disconnect removes the tunnel and restores the exact baseline route and DNS
  fingerprints while the LocalSystem service remains running.

## Connected reboot and harness reconciliation

The same direct fixture reconnects to a verified running state, then the guest
performs a real Windows reboot. Guest Control returns a non-zero transport code
because its session terminates during restart; authoritative guest boot time
changes to `2026-09-03T07:23:15.5Z` and proves the reboot occurred.

After boot, the service is `Running`, `Automatic`, `LocalSystem`; the tunnel is
absent; route and DNS fingerprints equal the pre-connect baseline; API DNS and
health pass. The runtime correctly stays lazy at `artifact_ready`,
`core_ready=0`, `running=0`, `failure=none` after the clean shutdown path.

The first post-check required `phase=initialized` and therefore emitted a
false harness `FAIL` despite every recovery invariant passing. That record is
retained. The corrected verifier accepts either clean lazy `artifact_ready` or
clean `initialized`, reruns against the same post-reboot state and passes.

## Release effect and cleanup

This slice closes direct-only Windows TUN/DNS/disconnect and connected-reboot
uncertainty for candidate.25. It does not satisfy managed-node egress,
packaged AWG3.1/AWG2, Smart DNS, connected uninstall, IPv6/leak, sleep/crash or
Windows 10. Gate F therefore remains exact `BLOCKED 5 PASS / 14 non-PASS / 0
FAIL`; no completion level changes.

The VM is powered off and restored to the original
`candidate23-retained-before-candidate25-20260903` snapshot. No host process,
service, route, DNS, adapter, mouse or keyboard state is changed. No tag,
public asset, Store object, stable pointer or production state is changed.

## Evidence

- `evidence/013FM-candidate25-windows-direct-tun-reboot/013FM-direct-tun.json`,
  SHA-256 `86762e3a5b724e8613ff461447943875299ad3f0965346461d36dd9ed3f88c16`;
- `evidence/013FM-candidate25-windows-direct-tun-reboot/013FM-connected-reboot-pre.json`,
  SHA-256 `8088573304d973b6cc0f667b031c8a16f92084c97dc3ce11b9dc6b40929661e2`;
- `evidence/013FM-candidate25-windows-direct-tun-reboot/013FM-connected-reboot-post-initial-harness.json`,
  SHA-256 `cca7e51d87fee0729e05f1b3b74245f94a5e4bf9fe1bdda469769724034419b8`;
- `evidence/013FM-candidate25-windows-direct-tun-reboot/013FM-connected-reboot-post.json`,
  SHA-256 `84bb465eee5e9e7d6e8e1d33637e65b558eb1c9eff463d4e1de59bf9967b7f6b`;
- external sanitized harnesses and fixture:
  `E:/POKROV-tools/release-evidence/1.2.0-candidate25-windows-direct-tun-reboot-2026-09-03/`.
