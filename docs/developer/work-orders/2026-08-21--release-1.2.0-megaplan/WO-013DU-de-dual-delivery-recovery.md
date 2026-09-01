# WO-013DU — DE dual-delivery recovery and post-candidate rollout

Status: `PASS_CURRENT_RUNTIME_REQUIRES_SUCCESSOR_CANDIDATE`
Classification: `ACTIVE_EXECUTION_EVIDENCE`
Phase: `06/10/11`
Candidate: `POST_CANDIDATE_16`
Production/external mutation: `OWNER_AUTHORIZED_APPLIED`

## Outcome

The owner clarified that the two provider addresses belong to one physical DE
VM and requested that both remain available to VPN consumers as `Германия 1`
and `Германия 2`. The implementation keeps one canonical node, panel inbound,
capacity record, health record and user mapping. It does not create a duplicate
`de2` node or provision the same user twice.

Platform PR 149 adds normalized `delivery_endpoints[]` to a node transport
profile and renders the alternatives in sing-box, Happ, Clash, raw VLESS and
Xray compatibility output. Hosted CI passed before the owner-solo merge. The
merged platform revision is `a68280f38124a5aad7b8e481d54d5637e0d393a7`.

| Check | Result |
|---|---:|
| Local transport catalog | `9/9 PASS` |
| Local Smart Connect and RU-bridge regression | `15/15 PASS` |
| Backend/API router regression | `154 PASS`, `8 subtests PASS` |
| Documentation contract | `32/32 PASS` |
| Hosted cross-repository contract | `PASS` |
| Hosted repository guardrails | `PASS` |
| Brain deployed-source readback | `197/197 PASS` |
| Brain TCP/443 for both DE names | `2/2 OPEN`, three repeats |
| Authenticated VLESS/Reality egress from Brain | `2/2 PASS`, HTTP `204` |
| Live subscription rendering | `4/4 PASS` |
| DE user mapping cardinality | `1 PASS` |

No raw address, subscription token, UUID, Reality material, host key, provider
credential or response body is retained in tracked evidence.

## Node recovery

Owner-attested SSH access was restored after the provider replacement. The
server has one VM and two provider addresses. A persistent
`pokrov-de-secondary-ip.service` owns the secondary address plus its dedicated
source-routing table and rule before either AWG unit starts. The exact service
readback is active, while the main address and provider route remain unchanged.

The adjacent `private-chat` Caddy container previously owned TCP/443. It is now
stopped with restart disabled; its data and container remain retained for
rollback. The x-ui database bind was changed from one exact address to wildcard
with a guarded preimage, x-ui was restarted, and Xray now owns TCP/443 on both
addresses.

Both `pokrov-awg-lab@pokrovawg2.service` and
`pokrov-awg-lab@pokrovawg31.service` are active and enabled. Their UDP sockets
and UFW rules are present. This is server readiness only: no new exact-candidate
AWG client result is claimed by this work order.

## Production apply and rollback

The Brain backend was deployed from the merged revision through the guarded
staging/compile/backup/restart/readback path. Its retained backend rollback
snapshot is `/root/portal_bot.deploy-backups/20260901T015440Z-506660`.

The DE row was then updated under a row lock and exact preimage SHA-256 CAS. The
canonical VPN host and the legacy Reality profile now use the first DNS name;
that same profile contains exactly two stable delivery endpoint ids, DNS names
and Russian labels. Panel management identity and all user mappings were left
unchanged. The before/after catalog SHA-256 values are respectively
`88ccb2cb8f11a7cc8fc6f48b1894e783da5a2959eca48a0eecf7c177d4019650`
and `0ae5ffe162095e2e57816f5ddf87452006f487bc86e33b02cff921b6cc111e0f`.
The root-only row preimage is retained under
`/root/pokrov-de-dual-endpoint-receipts/20260901T015617Z`.

Rollback is explicit and not executed:

1. restore the DE row from the root-only preimage;
2. if code rollback is also required, restore the retained Brain backend
   snapshot and restart through the existing deploy guard;
3. remove the secondary-address service only if the provider address itself is
   being withdrawn;
4. do not restart `private-chat` while Xray owns TCP/443.

## Release decision

This closes the current-runtime DE dual-address and subscription-delivery
slice. It does not rewrite candidate.16. Candidate.16 remains immutable at
platform `719e23d...`, with Gate F `NO_GO 2/17/2`; the deployed platform now
contains post-candidate source. A successor signed candidate must bind the new
platform revision and repeat exact-candidate Brain, Android and Windows checks
before Gate F can be regenerated. Gate G remains unauthorized.
