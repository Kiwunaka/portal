# WO-013CQ — candidate.10 LDPlayer Smart-DNS configuration replay

## Outcome

Bind the Smart-DNS client path to exact signed candidate.10 bytes, prove its
visible prerequisites and persistence on the owned emulator, then restore the
previous state without starting a tunnel. This closes no server or physical
device gate.

## Exact boundary

| Item | Value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.10` |
| Client source | `3459438f02bd774e722b1b858e7f7f16d57a9f5c` |
| Installed package | release `1.2.0+4046` |
| Installed APK SHA-256 | `ec07ba17e9a5c697fcf46ccd193970fa3666eeeb3b9e345876aa8ee1d45a2627` |
| Candidate byte match | `PASS` |
| Client evidence merge | `f14d48b50f3369720dc89a4c17dab23391174ae7` |
| Environment | owned LDPlayer, not physical Android |

The signed candidate, source tuple and artifact set are immutable. No build,
install, backend, profile, server, DNS-zone or release-pointer mutation occurs.

## Replay

Initial readback shows no connected Android VPN, no `tun` interface,
`DNS Автоматически`, `Настроено: 2` and an empty crash buffer. UI-tree-derived
coordinates drive only the user-visible path:

1. `Правила -> Редкие настройки -> DNS`;
2. the allowlisted custom HTTPS DoH hostname with exact `/dns-query` path;
3. `DNS напрямую · лаборатория`;
4. `Внешний Smart DNS · лаборатория`;
5. existing selected `AI-сервисы` and `Игровые сервисы` purposes.

The UI explicitly states that selected application traffic is direct and the
external IP is not hidden. Custom DoH, direct transport, external Smart DNS
and both purposes survive force-stop/relaunch. The crash buffer remains empty.

## Evidence ceiling

This is
`PASS_EXACT_CANDIDATE10_LDPLAYER_SMART_DNS_CONFIG_PERSISTENCE_AND_CLEANUP`.
It is not a resolver, DoH, service-access, leak or physical-device result.

All four authoritative Timeweb servers still return no A record for the
authorized hostname. Certificate, root-only runtime material, Smart-DNS server
APPLY and frontend route APPLY remain `NOT_RUN`. No connection, DoH request,
ChatGPT, Gemini or Xbox access attempt runs against the absent service.

## Cleanup

The client returns to `DNS Автоматически`; the custom URL and external
Smart-DNS state are cleared, DNS transport returns to VPN, and
`Настроено: 2` is restored. Final readback shows no connected VPN or `tun`.
POKROV is force-stopped and all emulator-side temporary capture files are
removed. The physical phone is unavailable and untouched.

## Verification

Client `main` receives PR 39 under the owner-authorized solo exception. The
full PowerShell Core seed validator, cross-repository parity, observability,
release contracts, repository hygiene and docs contract pass. No
`artifacts/releases/**` delta exists. The hosted cross-repository job has an
empty runner and `steps: []`; it is retained as `SKIPPED_BY_OWNER`, not PASS.

The tracked normalized record is
`evidence/013CQ-candidate10-ldplayer-smart-dns/013CQ-candidate10-ldplayer-smart-dns.json`.
Its source evidence copy SHA-256 is
`f1dd9f7dc8e4f549ee993f26c037e06cd97e16a76c8a7fda0ff3a8964c2e3ea2`.

`FRKN_SMART_DNS/SMARTDNS-01` remains `I3`. Candidate.10 Gate F remains
`NO_GO 6 PASS / 13 non-PASS / 1 FAIL`; Gate G and public/stable promotion remain
unauthorized.
