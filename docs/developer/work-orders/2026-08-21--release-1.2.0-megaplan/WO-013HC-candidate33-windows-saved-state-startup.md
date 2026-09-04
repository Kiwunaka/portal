# WO-013HC — candidate.33 Windows synthetic saved-state startup

Status: `PASS_EXACT_CANDIDATE33_SYNTHETIC_SAVED_STATE_MIGRATION_OFFLINE_STARTUP_AND_NETWORK_APPEARANCE_NO_AUTOCONNECT; GATE_F_BLOCKED`

Observed: `2026-09-04`

Production/public mutation: `NONE`

## Outcome

The exact installed candidate.33 now passes a bounded synthetic saved-state
startup slice. A dedicated temporary Windows user received synthetic v0
account/profile state and the exact product-generated quoted UI plus
`--startup` Run value. Existing `pokrovtest` session files were not read, moved
or copied.

The guest started with only its VirtualBox adapter cable off. At login, the app
migrated state to schema v1, moved the synthetic token to secure storage, left
no plaintext `session_token` field and stayed hidden on one responsive PID.
The Automatic LocalSystem service remained running; no consent process, Core
process or POKROV TUN appeared.

Restoring only the guest adapter cable kept the same hidden PID and unchanged
state, secure-store and experience fingerprints. Ethernet became available,
but no automatic connection occurred. That is the current 1.2.0 contract:
startup registration owns a hidden UI launch, not managed auto-connect. This
evidence therefore does not prove a valid saved account, managed-profile fetch
or managed connection timing.

## Exact boundary

| Fact | Exact value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.33`, app `1.2.0+4053` |
| Platform / client / Core / index | `f530005...5bc1` / `6ab1bca...735e` / `cd8f0f4...884d` / `63993fb...c43c` |
| Windows setup | `250622f7...3580`; installed `11/11` |
| Installed UI | `1b175a66...1d97`; PID `6884` |
| Offline startup | hidden UI `1`; consent/Core/TUN `0/0/0`; service Running/Auto/LocalSystem; Ethernet Disconnected |
| Saved state | v0 → schema v1; secure token storage; plaintext token field absent |
| Network appearance | same hidden PID; state/secure-store/experience unchanged; consent/Core/TUN `0/0/0`; Ethernet Up |
| Cleanup | SYSTEM removes fixture user/profile/ProgramData/task/public files; `pokrovtest` restored with Run/UI/Core/TUN absent |
| Guest updates | `Stopped/Disabled`, `NoAutoUpdate=1`; dedicated VM only |

## Evidence

The external evidence index is:

```text
E:/POKROV-tools/release-evidence/1.2.0-candidate33-windows-saved-state-startup-2026-09-04/candidate33-windows-saved-state-startup-evidence-index.json
SHA-256 43a7e7372e1765d826fb6cf00c465e907a7fdd3f31b2d6df4cd6e4b3c1fb3bb7
```

The retained offline and network-restored records hash to
`7c7dbc31...24e9d` and `5a5f2863...c211`. The same UI PID `6884` remains
hidden, saved-state and secure-store fingerprints remain unchanged, and both
records show zero Core/TUN. The SYSTEM cleanup receipt hashes to
`2c58687a...b600`; post-cleanup verification hashes to `236147d2...270b`.

The post-cleanup DNS and route fingerprints differ from the earlier connected
baseline after a full guest reboot and DHCP renewal. The retained adapter/route
inventory contains only loopback plus physical Ethernet and no POKROV adapter,
Core or TUN, so no exact-baseline claim is manufactured. The initial
password-policy and Public-folder ACL misses are retained as harness issues,
not product failures.

Client PR `82` merges the readiness reconciliation at
`34eeea77b97c65e1147ccbb9ef8d3542a463658c`. Its client docs contract and full
seed validation pass. Hosted run `33887022416` terminates with `steps=[]` and
remains `BLOCKED_BY_ACCESS_GITHUB_BILLING`, not a product-test failure or PASS.

The platform-retained summary is
`evidence/013HC-candidate33-windows-saved-state-startup/013HC-candidate33-windows-saved-state-startup.json`,
SHA-256 `defa5bb8a85965b4d8270a8afdf7671a93a61c722d301bca628d4b125f556035`.

## Release impact

`REL/WIN-005` remains `I3`. Synthetic migration, offline hidden startup and
later network appearance are exact-candidate proven, but a valid saved
account/profile, managed-profile refresh and managed auto-connect/service
readiness timing are not. Gates C and F remain blocked; Gate F stays
`2/17/0`. No candidate bytes, deploy, public asset, Store object, stable
pointer, production account, server, host input or host network changed.
