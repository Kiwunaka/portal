# WO-005G — Reopen the conditional Linux beta foundation

Status: `LOCALLY_PROVED_SOURCE_ONLY`
Phase: `03`
Client PR: `Kiwunaka/POKROV-app#28`
Candidate: `NOT_IN_CANDIDATE_3`
Deployment: `NOT_RUN_NOT_AUTHORIZED`
Recorded: `2026-08-27`

## Decision

The continuing 1.2.0 engineering goal reopens the bounded Linux foundation
after the earlier `WO-005E` non-shipment decision. This does not reverse the
public release boundary: Android and Windows remain the 1.2.0 public pair, and
candidate.3 contains no Linux artifact or Linux source claim.

The reopened lane is limited to one source-only fail-closed foundation:

- non-root Flutter UI;
- root systemd daemon activated through a typed Unix socket;
- kernel peer credentials plus polkit authorization for mutations;
- bounded profile storage and a closed secret-free journald envelope;
- sanitized daemon state projected into the shared runtime engine;
- one exact foundation matrix row, Ubuntu 24.04 LTS amd64 with systemd,
  NetworkManager, systemd-resolved, nftables and DEB;
- explicit rejection of live connect until Core/TUN and network transactions
  exist.

Fedora, RPM, package signing, clean desktop VM proof, suspend/recovery and the
live Core/TUN/NetworkManager/resolved/nftables lifecycle remain open.

## Exact source and verification

Client PR `#28` head
`5388fd3197e46170c88db59078758fe053af5bcd` applies the foundation to current
client `main` base `95afa0785633b40fe7ad94c014997ad9afd1d0fc`. The current
Windows-host standard client gate, release-v2 CI contract, docs contract,
cross-repository seed gate, Linux shell analyze/tests and runtime-engine
analyze/tests pass. `git diff --check` passes.

The local host cannot start WSL because virtualization support is unavailable,
so a new local real-Linux Go run is `BLOCKED_BY_HOST_CAPABILITY`. Hosted run
`32989022843`, job `98241915434`, passes the full client gate and
`Validate conditional Linux daemon foundation` at source
`0701806153048325bf35599709bdfe04ef63efe0`. `git diff` confirms no difference
between that hosted revision and PR `#28` for `apps/linux_shell/**` and
`packages/runtime_engine/lib/src/linux_daemon_runtime.dart`.

The new PR run `33050348883`, job `98444036229`, started zero steps and received
no runner. Its GitHub annotation names failed account payments or an
insufficient spending limit. It is `BLOCKED_BY_ACCESS_GITHUB_BILLING`, not a
source failure and not a pass.

## Evidence ceiling

The source/unit evidence can advance `REL/LNX-001` only to `I3` under WO-005.
It cannot advance any Linux row to `I4`, cannot satisfy signed-package or
clean-host matrix acceptance, and cannot enter candidate.3 retroactively.

Observed row decisions:

- `REL/LNX-001 -> I3`: the bounded daemon/non-root UI foundation and focused
  checks exist;
- `OBS/OBS-043 -> I2`: the closed journald writer exists, but no retained live
  journal-socket/rotation readback proves it locally;
- `OBS/OBS-044 -> I2`: peer identity, polkit authorization and packaging
  boundaries exist with focused tests, but the row's D-Bus trace is absent;
- `OBS/OBS-045 -> I1`: the host probe detects NetworkManager, resolved and nft,
  but transaction recording and rollback are not implemented;
- `OBS/OBS-046 -> I3`: typed bounded daemon snapshots are sanitized and parsed
  into the non-root UI runtime lane with focused tests;
- `REL_GATE/GATE-C -> I2`: shipped-host implementations plus the conditional
  Linux source foundation exist, while the exact platform matrices remain
  open;
- `REL_DOD/DOD-06 -> I2`: daemon and non-root UI exist, but signed packaging and
  the basic distro/network matrix do not.

## Retained boundary

The daemon returns `supports_live_connect=false`, `can_connect=false` and
`linux_live_connect_unavailable`. It does not mutate routes, DNS, TUN or nft.
This is the required fail-closed state, not a functioning Linux VPN claim.

If Linux is selected for release 1.2.0, the owner must authorize a replacement
candidate after merge and after signed-package plus clean-VM evidence. The
existing signed candidate.3 must never be relabeled as containing Linux.

Evidence:
`evidence/005G-linux-beta-foundation/005G-linux-beta-foundation.json`, SHA-256
`0beba81654136a17577427a265424a2511b341db333e0927d826f0a996afbd10`.

## Rollback

Do not merge PR `#28`, or disable the Linux build lane. No installed service,
network state, public asset, candidate pointer or stable pointer was mutated by
this work order.
