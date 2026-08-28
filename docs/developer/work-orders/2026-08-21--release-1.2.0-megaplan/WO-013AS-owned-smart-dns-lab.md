# WO-013AS — Owned selective Smart DNS laboratory

Status: `IMPLEMENTED_SOURCE; LOCAL_ARTIFACT_AND_DEVICE_PROOF_PENDING`

Date: 2026-08-28

Release effect: none. This work order does not create a candidate, deploy a
resolver/relay, change production routing, publish an artifact, or advance any
row beyond local source evidence.

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
Deployment remains forbidden until a dedicated owned IPv4, guarded installer,
rollback receipt, live limits and an explicit owner authorization exist.

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
- cross-repository byte-parity owner:
  `scripts/check_smart_dns_policy_parity.py`;
- active client copy: `POKROV-app/config/smart-dns-policy.v1.json`;
- active client materializer:
  `POKROV-app/packages/app_shell/lib/client_routing_preferences.dart`.

The bundle excludes runtime listener address, DoH hostname, certificate,
private key and upstream resolver coordinates. The systemd unit is packaged
inactive and non-root with only the low-port bind capability.

## Local evidence retained before commit

| Check | Result | Ceiling |
|---|---|---|
| `go test ./...` | `PASS` | server unit/source behavior only |
| `go vet ./...` | `PASS` | server static analysis only |
| focused platform bundle/parity tests | `4 passed` | builder and parity contracts only |
| script manifest check | `PASS` | inventory ownership only |
| focused Ruff check | `PASS` | Python source only |
| platform/client policy parity | `PASS`, exact SHA above | source bytes only |
| app-shell focused routing tests | `17/17 PASS` | client materialization/persistence only |
| Go race detector | `NOT_RUN_TOOLCHAIN_MISSING` | Windows host has no C compiler; never counted as PASS |

These results are working-tree evidence. Exact source revisions, immutable
bundle identity, full client aggregate, Android package/signature and device
readback are intentionally pending until the scoped diffs are reviewed and
committed.

## Required next evidence

1. commit and push the platform and client source lanes independently;
2. from the exact clean platform commit, build twice and verify the deterministic
   Linux bundle, then retain bundle/binary/member SHA-256 values;
3. complete the guarded PLAN/APPLY/ROLLBACK installer contract without choosing
   or mutating an active delivery node;
4. run the full app-shell and release-seed checks on the exact client revision;
5. build the production-signed `1.2.0+4046` APK and verify install, signer,
   default-off persistence and safe invalid-endpoint behavior first on LDPlayer,
   then on the returned owner phone;
6. separately authorize a dedicated-node install and retain DoH/SNI/limits/
   rollback evidence before any service-access test;
7. keep service-access, DNS leak, lifecycle, current-origin, Brain-origin and
   RU-origin evidence distinct; none may be inferred from source or install.

## Completion index

- `FRKN_SMART_DNS/SMARTDNS-01`: `I2 IMPLEMENTED_SOURCE` in this worktree;
- `I3` requires exact clean commits, immutable bundle verification, full client
  regression and package/device default-off proof;
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
