# WO-013EG — client Linux network transaction participants

Status: `PASS_SOURCE_AND_HOSTED_UBUNTU_BUILD_TEST; LIVE_NETWORK_NOT_RUN`

Observed: `2026-09-01`

Production/public mutation: `NONE`

## Outcome

Close the next source slice of `OBS-045` without enabling Linux traffic or
turning fixture tests into native network proof. Client PR 58 source
`9fa8c7615179cbcf97400a863c1cbcc8eb2766e6` merges as client `main`
`7ae2427026ef811e65e948e3a37262693e1d1f9e`.

The daemon now contains a dormant typed system transaction with one exact
owner for NetworkManager, systemd-resolved and nftables. The public IPC does
not accept command strings, interface names, rules or resolver material. The
internal plan requires a daemon-owned `pokrov*` tunnel link, one non-zero Core
routing mark and one to four validated IP resolver addresses.

Linux live connect remains fail-closed. Candidate 20 artifacts do not contain
this post-candidate client change and receive no transferred runtime or release
credit.

## Implemented transaction

The fixed checkpoint order is NetworkManager, resolved, nftables. The fixed
apply order is resolved, nftables, NetworkManager, so checkpoint destruction
commits only after DNS and firewall application succeed. Rollback is reverse:
nftables, resolved, NetworkManager.

- NetworkManager uses the system D-Bus `CheckpointCreate`,
  `CheckpointRollback` and `CheckpointDestroy` methods. It covers all devices,
  carries a 90-second automatic rollback timeout and tracks new connections,
  new devices and internal global DNS. Only the validated returned checkpoint
  object path is retained.
- resolved verifies the owned link, applies its DNS servers, `~.` routing
  domain and default-route ownership, then uses per-link `revert` for cleanup.
- nftables first verifies that the owned table does not already exist, checks
  the generated rules, then atomically creates only `inet pokrov`. Rollback
  deletes only that table; there is no global ruleset flush or restore.
- partial apply marks only possibly dirty participants. Reverse rollback
  continues after a participant failure, preserves the failed owner for an
  explicit retry and makes a completed restore idempotent.
- production execution uses fixed absolute command paths, no shell, a
  five-second budget per command, bounded stdout and discarded stderr. The
  NetworkManager host probe now requires the system-bus client used by the
  implementation.

The existing production `connect` path does not construct or invoke this
transaction. It still records three `checkpoint/unavailable` events and
returns `linux_live_connect_unavailable`.

## Verification

- local portable Go `test ./...` and `vet ./...`: `PASS`;
- local Linux/amd64 `vet ./...` and daemon cross-build: `PASS`;
- full client `scripts/run-tests.ps1 -OfflinePubGet`: `PASS`;
- client docs contract and seed validation with explicit clean platform/Core
  authority roots: `PASS`;
- `git diff --check`, secret-like scan and release-artifact delta: `PASS`;
- client PR run `33552898076`: `SUCCESS` on source `9fa8c76...`;
- PR Linux step 14, `Validate conditional Linux daemon foundation`: `SUCCESS`,
  including native Ubuntu `gofmt`, `go test ./...`, `go vet ./...` and daemon
  build; package `internal/networktxn` passes;
- client post-merge run `33554337590` on exact merge `7ae2427...`:
  `SUCCESS`; Linux step 14: `SUCCESS`.

These checks execute the command adapters against injected runners. They do
not call NetworkManager, resolved or nft on a live host and do not prove
route/DNS/firewall restoration.

## Ledger effect

`OBS/OBS-045` receives the merged source, injected checkpoint/partial-apply/
rollback fault coverage and hosted Ubuntu build/test evidence. It remains
`I2`. Distribution remains `I4=7`, `I3=320`, `I2=19`, `I1=32`, `I0=0` across
`378` rows.

Promotion to `I3` requires the exact Core/TUN plan, durable restart/suspend
recovery, clean Ubuntu 24.04 native D-Bus/journald readback and retained
route/DNS/nft partial-fault plus exact restoration evidence. `I4` additionally
requires a signed package and the separate Linux beta matrix. Linux stays
outside 1.2.0.

## Mutation boundary

Host VPN/routes/DNS, Windows VM, LDPlayer, phone, Pi, production, provider,
database, Operator, release assets, Store and stable pointers were not used or
changed. No Gate F record was generated.

## Evidence

- normalized record:
  `evidence/013EG-client-linux-network-transaction-participants/013EG-client-linux-network-transaction-participants.json`;
- normalized record SHA-256:
  `a92593f7741c7422f4b6a97a72fd9d1a17e62b1d849d69ce220c23bb07183fa1`.

The record contains no credential, connection material, customer/provider
payload or device identifier.
