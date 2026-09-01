# WO-013EF — client Linux polkit/D-Bus authorization observability

Status: `PASS_SOURCE_AND_HOSTED_UBUNTU_BUILD_TEST; DESKTOP_SESSION_RUNTIME_OPEN`

Observed: `2026-09-01`

Production/public mutation: `NONE`

## Outcome

Close the source-level part of `OBS-044` without claiming a Linux package or
desktop-session runtime result. Client PR 57 merges as client `main`
`eceb130cc89c06c3a5e2f6448b5fecf2d7d8fd06`. The Linux daemon now classifies
authorization through two closed backends, `peer_credential` and
`polkit_dbus`, and records one bounded authorization decision for every
mutation before state can change.

The polkit path keeps the existing exact `pid,starttime,uid` process subject
and `space.pokrov.linux.manage` action. It distinguishes allow, deny, missing
agent, dismissed prompt, timeout, unavailable backend and invalid subject.
The caller still receives only `linux_authorization_denied`; journal output
does not contain PID, UID, process tuple, action detail, command output or raw
D-Bus error.

The socket lifecycle now separates a 12-second request-read deadline, the
60-second interactive authorization budget and a 5-second response-write
deadline. A completed authorization can therefore return its response instead
of inheriting an expired request-read deadline.

Linux live connect remains fail-closed. Candidate 20 artifacts do not contain
this post-candidate client change and receive no transferred runtime or release
credit.

## Verification

- local Windows-runnable Go journal/network suites: `PASS`;
- Linux `amd64` daemon/test cross-compilation: `PASS`;
- Flutter analyze: `PASS`;
- Linux shell contract tests: `5/5 PASS`;
- seed validation with explicit clean platform/Core roots: `PASS`;
- client PR run `33544192198`: `PASS` on source commit `943b029...`;
- its real Ubuntu step 14, `Validate conditional Linux daemon foundation`:
  `SUCCESS`, including `go test ./...` and daemon build;
- client post-merge run `33545657698` on exact merge `eceb130...`:
  `SUCCESS`; Linux step 14: `SUCCESS`.

## Ledger effect

`REL_DOD/DOD-06` and `OBS/OBS-044` receive current client-main source and
hosted Ubuntu evidence. Both remain `I2`. Distribution remains `I4=7`,
`I3=320`, `I2=19`, `I1=32`, `I0=0` across `378` rows.

Promotion to `I3` requires a clean Ubuntu desktop session with retained
allow/deny/dismiss/missing-agent/timeout D-Bus and journald readback. `I4`
additionally requires the signed package and the separate Linux beta runtime
matrix. Linux stays outside 1.2.0.

## Mutation boundary

Host VPN/routes/DNS, Windows VM, LDPlayer, phone, Pi, production, provider,
database, Operator, release assets, Store and stable pointers were not used or
changed. No Gate F record was generated.

## Evidence

- normalized record:
  `evidence/013EF-client-linux-dbus-observability/013EF-client-linux-dbus-observability.json`;
- normalized record SHA-256:
  `ce27a46b98a8c3dab70790c4579e390f9b363906ed2f60a3a5b69013887596fb`.

The record contains no credential, connection material, customer/provider
payload or device identifier.
