# WO-013CE — Smart DNS egress architecture and isolated RU fixture

## Outcome

Close the ambiguity between a working selective DNS/SNI relay and an exit that
can actually change service reachability. The current owned Smart DNS server
resolves an allowed application hostname through fixed authenticated DoT and
opens TCP/443 directly from the machine running the service. It has no outbound
proxy, WARP or foreign-hop setting.

Therefore a fronted install on an RU delivery node would make the destination
see RU-node egress. It may prove the server mechanics, but it is a `NO_GO` for
the intended DNS-only geo/access bypass. No RU, RU-SPB, Brain or foreign node is
selected and no production mutation is authorized by this work order.

## WARP topology clarification

Candidate.8 uses client-local WARP materialization, but the default local mode
is `warp_over_proxy`. The endpoint is instantiated inside POKROV Core on the
device while its transport detours through the selected POKROV outbound. The
logical path is:

```text
device/Core -> POKROV transport -> owned node -> Cloudflare WARP -> destination
```

This is not a server-installed WARP daemon. It also cannot carry traffic from a
DNS-only client that is not running the POKROV tunnel, so it does not repair an
RU Smart DNS deployment by itself.

## Source conclusion

Exact source review of `infra/owned-smart-dns/internal/smartdns/server.go` and
`resolver.go` proves the following path:

1. visible allowlisted SNI is accepted;
2. the real origin is resolved through the configured authenticated DoT
   resolver;
3. `net.Dialer` opens the resolved public IPv4 on TCP/443 directly;
4. TLS bytes are relayed opaquely without certificate replacement;
5. no configurable detour or alternate egress exists.

The safe preferred topology is a colocated foreign owned frontend and Smart
DNS backend. It preserves the reviewed loopback-only PROXY-v2 trust boundary
and makes the foreign node the real application egress. None of the currently
reviewed foreign nodes has the applicable owned HAProxy frontend, so this path
needs a new guarded transport-frontend bootstrap/migration PLAN before any
APPLY.

Two alternatives remain deliberately unselected:

- RU frontend to a remote foreign backend would replace the loopback trust
  boundary with a new authenticated inter-node transport and rollback problem;
- process-specific WARP on RU would add namespace/routing/lifecycle ownership
  not present in the current server contract.

Neither should be improvised during the 1.2.0 release gate.

## Isolated terminal fixture

The owner-provided trusted `pokrov-mini` terminal target reports `x86_64`, not
ARM64. The exact Linux/amd64 bundle from platform component source `650dc3f...`
therefore ran in a fresh validated `/tmp` directory without installing a
service, changing a firewall, publishing DNS or retaining runtime material.

The fixture used loopback TCP/18443, strict PROXY protocol v2 and an ephemeral
self-signed DoH certificate. It proved:

- exact bundle config check: `PASS`;
- fronted loopback listener: `PASS`;
- missing PROXY v2 rejected: `PASS`;
- PROXY-v2 + TLS + DoH selected answer: HTTP `200`, one answer, configured
  proxy match;
- verified application TLS passthrough through the service for one AI-chat,
  one AI-assistant and one gaming-policy representative: `PASS`;
- bounded HTTP statuses: `403`, `200` and `301` respectively;
- listener/process and remote temporary-directory cleanup: `PASS`;
- production mutation: `false`.

These HTTP responses prove verified TLS/SNI carriage only. They do not prove a
logged-in application session, gameplay, account availability or geographic
unblocking. The target origin remains `OPERATOR_ATTESTED` RU terminal evidence,
not exact-candidate RU-origin proof.

## Release interpretation

`FRKN_SMART_DNS/SMARTDNS-01` remains `I3` with status
`POST_CANDIDATE_ISOLATED_TLS_PASSTHROUGH_PROVED_RU_DIRECT_EGRESS_NO_GO_FOR_ACCESS_BYPASS`.
The result prevents an incorrect RU APPLY and strengthens the source/runtime
evidence without moving the row to `I4`.

Signed `pokrov-1.2.0-candidate.8`, its six artifacts and its Gate F decision are
unchanged. Gate F remains `BLOCKED` at `4 PASS / 15 non-PASS / 0 FAIL`. No tag,
public release, stable pointer, server deploy, DNS publication or runtime
material was created.

## Required next evidence

1. inventory one foreign owned node's current TCP/443 service and exact
   rollback shape without mutation;
2. implement a guarded PLAN/APPLY/ROLLBACK operation that places the existing
   transport behind an owned HAProxy frontend on that same foreign node;
3. rerun both server and frontend PLANs against exact runtime material;
4. only after explicit target/APPLY authorization, prove real DoH, SNI relay,
   actual service sessions, DNS/SNI attribution, leak/privacy, lifecycle and
   rollback from distinct current, Brain and RU origins;
5. keep Android Private DNS separate: the current server is DoH, while Android
   system Private DNS requires a separately proved DoT-compatible path.

## Evidence boundary

Normalized evidence is retained under
`evidence/013CE-smart-dns-egress-architecture/` with SHA-256
`c789c235991f49236ecf4d4a6efc7134659d0c8f0d6b8f4d2323b4140dda04d6`.
It contains component hashes, bounded status codes, architecture, booleans and
decision labels only. It contains no address, hostname, key, certificate,
device identifier, raw SNI, runtime configuration or provider payload.
