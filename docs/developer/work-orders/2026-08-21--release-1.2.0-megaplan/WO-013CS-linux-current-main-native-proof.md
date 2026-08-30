# WO-013CS — Linux beta current-main adoption and native proof

## Outcome

Resolve the retained Linux beta branch against the current client promotion
line, prove its source on Windows and a real owned Linux host, and adopt it as
successor source without changing or claiming it for signed candidate.10.

## Exact boundary

| Item | Value |
|---|---|
| Signed release candidate | `pokrov-1.2.0-candidate.10` — unchanged |
| Candidate client source | `3459438f02bd774e722b1b858e7f7f16d57a9f5c` — unchanged |
| Client refresh base | `f14d48b50f3369720dc89a4c17dab23391174ae7` |
| Linux PR head | `646e94430fbf3e5c41486fe8c5cf202ae87a213f` |
| Client main merge | `30ccf4f1030e60f38617904a611b1ec392a2ead1` |
| Pull request | `Kiwunaka/POKROV-app#28` |
| Evidence time | `2026-08-30T07:48:10Z` |

`artifacts/releases/**` has no diff from the refresh base. No signed manifest,
artifact, tag, release, Store object, runtime deployment or stable pointer is
created or modified by this work order.

## Adopted source foundation

The refreshed client main now contains:

- a non-root Flutter Linux shell;
- a root systemd socket-activated Go daemon;
- bounded typed Unix-socket IPC with kernel `SO_PEERCRED` identity;
- exact PID/start-time/UID polkit authorization for profile and connection
  mutations;
- fixed private profile storage with bounded JSON and atomic promotion;
- allowlisted secret-free journald/fallback events;
- a typed NetworkManager/systemd-resolved/nftables transaction-event seam;
- one fail-closed Ubuntu 24.04 amd64 foundation row.

The source does **not** implement live Linux traffic. `connect` returns
`linux_live_connect_unavailable`, `supports_live_connect=false`, and records
only honest unavailable preflight checkpoints. It never emits synthetic
network apply or rollback success.

## Verification

The exact merge-result tree passes:

- full `scripts/run-tests.ps1`, including the Flutter workspace and Android
  direct/store Gradle lanes;
- `scripts/validate-seed.ps1` against the current platform release worktree and
  bound Core authority;
- Linux shell `flutter analyze` plus `4/4` tests;
- runtime-engine `flutter analyze` plus `70` tests and one expected
  exact-DLL host skip;
- documentation, release, seed and hygiene contracts;
- `git diff --check`.

An LF-preserving archive of the exact Linux daemon source was transferred to
an owned Ubuntu 22.04 x86_64 host. With the official Go `1.25.13` archive and
its published SHA-256 verified before use, `gofmt`, `go test ./...`,
`go vet ./...` and `go build -trimpath` all pass. The remote temporary directory
was removed after the run. This is native compile/test evidence, not Ubuntu
24.04 support-matrix, package-install or live-network evidence.

## Hosted and solo classification

GitHub run `33299917136`, job `99225988231`, ended before runner allocation
with `steps: []`, `runner_id=0` and an empty runner name. Under the approved
solo/no-paid-GitHub exception it is `SKIPPED_BY_OWNER`, not PASS and not a code
failure. PR 28 merges normally without force-push or branch deletion only after
the local/native gates above pass.

## Index and remaining gates

`REL/LNX-001` remains `I3`, now with current-main and native Linux evidence.
`OBS/OBS-045` remains `I2`: Linux tests execute, but real NetworkManager
checkpoint/rollback, resolved/nft mutations, partial-failure rollback and
journald readback do not exist. `OBS-043`, `OBS-044` and `OBS-046` do not
advance.

Before `I4` or any Linux availability claim: implement the live Core/TUN
lifecycle, real network transactions and recovery, suspend handling, signed
DEB, exact Ubuntu 24.04 desktop-session VM install/update/remove/rollback and
traffic/leak/egress evidence. Linux stays outside candidate.10 and release
1.2.0.

The physical phone is unavailable and untouched. A fresh direct check still
returns `NXDOMAIN` for `dns.pokrov.space` on all four delegated Timeweb
servers, so Smart-DNS ACME/runtime/server/frontend APPLY remains `NOT_RUN`.

Normalized evidence is retained in
`evidence/013CS-linux-current-main-native-proof/013CS-linux-current-main-native-proof.json`.
