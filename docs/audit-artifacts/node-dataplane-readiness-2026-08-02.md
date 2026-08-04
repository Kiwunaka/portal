# Node Dataplane Readiness Evidence 2026-08-02

Status: retained diagnostic evidence; not a deployment or production GO.

## Scope

This run investigated the owned POKROV node pool and performed the deepest
guarded dataplane canaries on `PL`. It used no customer identity or customer
traffic. Production signing, store publication, payments, public promotion,
and `RU-origin` claims were outside this evidence.

No endpoint address, UUID, REALITY key, short id, subscription URL, token, or
raw provider payload is retained here.

## Candidate and safety boundary

- The live `PL` baseline remained one active VLESS/TCP/REALITY inbound on
  public `443`, one managed Xray process/listener, and 76 configured clients.
- Every live mutation was bounded to one node, preserved an exact preimage,
  had an automatic recovery path, and required the full baseline to match
  after cleanup.
- The separate `RU` and `RU_SPB` bridge path was not mutated.
- Test clients were dedicated canary material. Marker responses contained no
  user or account data.

## Observations

| Check | Origin/path | Result | What it proves |
| --- | --- | --- | --- |
| Managed services and listener inventory | node-local | `PASS` | The panel, managed Xray process, client inventory, and public listener were present and internally consistent. |
| Current live REALITY connection | current Windows origin to public `443` | `FAIL` | TCP reached the exact managed Xray. The server returned a bounded REALITY fallback response and closed before authenticated marker transfer. |
| Current Windows host route attribution | current Windows origin | `CONFOUNDED/NOT_RUN` | No target-specific WFP or socket-route attribution was retained. The host Hiddify TUN state can affect the observed origin path, so this failure is not provider or upstream causality. Target-specific attribution remains an owner-approved manual check. |
| Pinned stable Xray guarded swap | current Windows origin to public `443` | `FAIL`, automatic rollback `PASS` | Replacing only the Xray binary did not repair the public path. The original binary, service, listener, config, and client inventory were restored. |
| Pinned stable Xray through an SSH-forwarded loopback path | current Windows origin through node loopback | `PASS` | The same canary material completed REALITY and returned the owned empty `204` marker through the stable binary. The binary and server material are viable when the public path is removed from the equation. |
| Client fingerprint/fragment variants | current Windows origin to public `443` | `FAIL` | The observed failure is not resolved by the bounded uTLS or fragmentation variants tried in this run. |
| Direct owned marker route | node/direct service path | `PASS` | The marker service itself was available and returned the expected response. |
| Host redirect inventory | node-local | `PASS` | No node-local NAT, redirect, or TPROXY rule was found taking public `443` away from the managed listener. |
| Isolated pinned-stable canary on `9443` | current Windows origin to node | `capture_inconclusive` | During a complete 30-second interface capture there was no inbound SYN, payload, SYN/ACK, or RST on the expected interface. This traffic did not reach the node NIC, so the result cannot diagnose REALITY. |
| Canary rollback and cleanup | node-local | `PASS` | No `9443` listener, UFW token rule, runtime directory, helper, recovery root, or systemd unit remained. The live `443` baseline and 76-client inventory matched the pre-canary state. |
| Brain authenticated probe | brain-origin to public `443` | `BLOCKED_BY_ACCESS` | No dedicated canary identity or authenticated-egress adapter material was available to run an authenticated probe without a new live mutation or protected-material access. |
| Deployed authenticated-egress schema and adapter | brain control plane | `MANUAL_OWNER_TEST` | Local migrations and tests define the contract but do not prove that the deployed schema, protected adapter contract, or canary store is present. |

The first cleanup attempt exposed an inactive-static-unit recovery edge case
after UFW and listener cleanup had already succeeded. The recovery helper was
corrected, resealed, and its timer then removed every remaining canary object.
The final inventory above is the authoritative post-cleanup state.

## Classification

- `PL current-origin public REALITY`: `FAIL`.
- Current Windows host route attribution: `CONFOUNDED/NOT_RUN`; Hiddify TUN can
  affect this origin, and target-specific WFP/socket attribution remains an
  owner-approved manual check.
- `PL node-local stable REALITY and owned marker`: `PASS`.
- `PL alternate-port reachability`: `BLOCKED_BY_ACCESS` before the node NIC;
  it is not a transport PASS or FAIL.
- `PL live baseline restoration`: `PASS`.
- Fleet-wide binary rollback or upgrade as a fix: `NOT_APPLIED`; the guarded
  A/B test contradicted that hypothesis.
- HAProxy/gRPC/XHTTP transport-front rollout: `MANUAL_OWNER_TEST`; repository
  design exists, but the current helper does not provide the complete backend
  provisioning plus transactional rollback required for a safe live cutover.
- Authenticated-egress monitoring rollout: `MANUAL_OWNER_TEST`; deploying the
  fail-closed smart-connect gate without protected canary material and the
  adapter would intentionally leave no eligible nodes.
- Brain authenticated probe: `BLOCKED_BY_ACCESS`; no existing dedicated
  canary identity or adapter material was available without protected-material
  access or a new live mutation.
- Deployed authenticated-egress schema and adapter: `MANUAL_OWNER_TEST`;
  local migrations and tests are not deployed proof.
- `RU-origin`: `NOT_REQUESTED` by this run and must stay distinct from the
  current-origin and brain/node-local observations.

## Conclusion

The evidence rules out a simple dead service, wrong listener, broken marker,
or Xray-version-only regression on `PL`. It is consistent with alteration or
policy on the current-origin public path before REALITY authentication, while
the separate `9443` attempt is independently stopped before the node NIC.
The current Windows result remains current-origin evidence only: its Hiddify
TUN route attribution is `CONFOUNDED/NOT_RUN`, so it does not establish
provider or upstream causality. That is an inference, not provider-side proof.

There is no confirmed node-local repair that is safe to copy across the fleet.
The next live change must be a separately authorized, fully rollbackable
transport-front canary with both backends provisioned first, or a provider/path
investigation that can observe the traffic before it reaches the node. Until
then, basic TCP/TLS reachability must not be treated as authenticated VPN
egress health.
