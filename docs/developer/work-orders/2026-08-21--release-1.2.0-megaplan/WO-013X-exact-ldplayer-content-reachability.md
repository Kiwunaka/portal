# WO-013X — Exact LDPlayer content reachability

Status: `EXACT_LDPLAYER_CONTENT_REACHABILITY_RECORDED`
Phase: `11`
Rows: `REL_DOD/DOD-15`
Candidate: `NOT_CREATED`
Deployment: `NOT_REQUIRED_NOT_RUN`
Recorded: `2026-08-26`

## Goal

Exercise the already installed byte-identical 1.2.0 (4030) x86_64 artifact on
LDPlayer through Saint Petersburg direct, retain the configured DNS/AI/Games
state and classify bounded public-service probes without turning network
reachability into account, product-functionality or physical-device proof.

## Scope and no-touch boundary

The test target was only ADB device `emulator-5560`, an LDPlayer Android 14
x86_64 emulator. No physical phone was visible to ADB, no APK was replaced,
no production deployment or configuration mutation was performed, and no raw
profile, account, response body or private connection material was retained.
The installed package remained `space.pokrov.pokrov_android_shell`, version
`1.2.0` code `4030`; its base APK SHA-256 was
`7d7a22b23a33811326c452fdd23d19bbb02aae0b3f6bd74a6753e38f222675ed`,
identical to the staged production-signed x86_64 artifact recorded by 013V.

## VPN-path proof

Saint Petersburg direct was selected from the app UI and the connection was
retried. The observed exact state was:

- the app showed `Подключено` for Saint Petersburg, Russia direct;
- `tun0` existed with MTU 1280;
- Android reported a connected, validated VPN network;
- the IPv4 default path used `tun0`;
- IPv6 had no usable default path, so dual-stack support is not proved;
- the shell UID used for the probes was inside the VPN-routed UID range, while
  the VPN owner app UID was excluded as expected.

This is emulator VPN-path evidence. It is not current-origin, Brain-origin,
RU-origin or physical Beeline evidence.

## Persisted controls

The Rules UI tree reported the AI services, Games/Xbox and AdGuard controls as
enabled, with the DNS preset shown as `DNS / AdGuard`. The state persisted for
the test. This proves presentation and persistence on the exact installed
bytes; it does not by itself prove every domain-classification decision or
support a DNS-without-VPN product claim. These controls remain active-VPN
routing features.

## Bounded reachability probes

The retained results contain only status, redirect count and elapsed time:

| Target | HTTP | Redirects | Elapsed | Classification |
|---|---:|---:|---:|---|
| Owned API health | `200` | `0` | `0.229 s` | `PASS` for bounded endpoint reachability |
| Google connectivity | `204` | `0` | `0.125 s` | `PASS` for bounded connectivity |
| ChatGPT | `403` | `0` | `0.178 s` | DNS/TCP/TLS/HTTP path reached; service functionality `NOT_PASS` |
| Gemini | `200` | `0` | `0.455 s` | `PASS_REACHABILITY_ONLY`; login and chat were not tested |
| Xbox | `200` | `1` | `0.316 s` | `PASS_REACHABILITY_ONLY`; login and gaming were not tested |

The ChatGPT response is compatible with service-side automation or edge
policy denial, but the cause was not proved. It must not be represented as
successful ChatGPT access. An initial malformed curl attempt with an
incorrectly split user-agent was discarded and receives no evidence credit;
the table contains only the corrected repeat. No response page body was
recorded.

## Retained screenshots

- `evidence/013X-exact-ldplayer-content-reachability/connected-spb-direct.png`
  shows the connected Saint Petersburg direct UI and has SHA-256
  `59eddb2a239062310700cac623e9978ae25f8cddf08883e9d32c3f17de471c24`.
- `evidence/013X-exact-ldplayer-content-reachability/final-disconnected.png`
  shows the final disconnected UI and has SHA-256
  `5995424af858ae74d3e1b8ab6a96d7dae7a1ede87cf07f55a57105562a030ee6`.

After the probes the app was returned home and disconnected. `tun0` was absent,
the UI showed `Не защищено` / `Подключить`, and the crash buffer was empty.

## Deployment and ledger decision

No backend deploy is required. The deployed backend runtime remains
`243dcbe4727041d62cc0a36e7d2fd5a8530c7c25`; the newer relevant platform delta
is release documentation/evidence, while owned health already returned 200.
A redeploy would not change the tested client bytes or resolve the ChatGPT 403.

No execution-ledger row advances. `REL_DOD/DOD-15` remains `I2` because this
is an emulator-only pre-candidate slice: the signed public candidate, exact
physical Beeline/OEM proof, Windows clean-host run, aggregate origins,
provider, Operator, legal and rollback gates remain open. Distribution remains
`I3=309`, `I2=17`, `I1=37`, `I0=14`; 68 rows remain below `I3`, split
`0/33/14/21` across pre-freeze, candidate, external and deferred stages.

## Next action

Run the same 4030 bytes on the physical Beeline phone when it is visible in
ADB. Use an interactive browser/app session for ChatGPT, Gemini and Xbox if
functional support is to be claimed; the emulator curl probes are not a
substitute. Candidate signing/publication and stable promotion remain separate
owner-authorized actions.
