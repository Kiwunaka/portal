# POKROV owned Smart DNS laboratory

This directory contains source for a default-off, source-only Smart DNS
laboratory. It is not deployed and contains no runtime host, certificate,
private key, token, or retained DNS/SNI data.

The service owns one dedicated TCP/443 listener. TLS for the exact DoH hostname
is terminated locally at `/dns-query`; other ClientHello records are accepted
only when the normalized SNI matches the canonical AI or gaming-service suffix
policy. Application TLS is passed through without certificate replacement or
decryption. Missing, malformed, ambiguous, ECH-concealed, or non-allowlisted
SNI is closed before any origin connection.

The DoH endpoint is deliberately not recursive. An allowlisted `A` question
receives the owned proxy IPv4, `AAAA`, `HTTPS`, `SVCB`, and other allowed types
receive `NOERROR/NODATA`, and every question outside the allowlist receives
`REFUSED`. This prevents the service from becoming an open recursive resolver
without placing a bearer token in the client's persisted URL or profile.

The proxy resolves the real origin through one fixed authenticated DNS-over-TLS
upstream, never through its synthetic DoH path. It connects only to TCP/443 and
rejects non-public answers. Global, per-source, request, parser, handshake,
connect, idle, and lifetime limits are mandatory. Runtime logs contain startup
state and the policy digest only; request names, SNI, source addresses, and raw
payloads are not logged.

Local verification from this directory uses the pinned Go module:

```powershell
E:\path\to\go.exe test ./...
E:\path\to\go.exe build ./cmd/pokrov-smart-dns
```

`config.template.json` is not a runtime file. Render its placeholders outside
Git into `/etc/pokrov-smart-dns/config.json`, retain it with owner/group-only
permissions, and validate it with `-check` before any separately authorized
install. The TLS private key stays outside the release bundle.

No active POKROV delivery node currently has an unclaimed TCP/443 listener.
Deployment therefore requires a separate or deliberately freed owned public
IPv4, an exact candidate bundle, guarded PLAN/APPLY/ROLLBACK tooling, and owner
authorization. DNS reachability is not proof that ChatGPT, Gemini, Xbox, or a
game works end to end.
