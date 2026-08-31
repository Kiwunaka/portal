# WO-013DL — candidate.16 Windows current-host exact install proof

Status: `PASS_EXACT_CANDIDATE16_CURRENT_HOST_IDLE_SLICE; CONNECTED_NETWORK_OPEN`

Observed: `2026-08-31T20:31:26Z` through `2026-08-31T20:43:45Z`

## Scope

Bind the signed candidate.16 Windows setup to a guarded exact-candidate
current-host test, prove the non-network install/service/IPC/restart/uninstall
slice, and retain a clean rollback when connected state cannot be established.

This is an owner-current-host result with a clean POKROV application-state
baseline. It is not a clean Windows image or VM, and it does not replace live
TUN, connected DNS, egress, recovery, connected-uninstall, SmartScreen or
Windows 10/11 matrix evidence.

## Exact boundary

| Item | Value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.16`, `1.2.0+4049` |
| Platform/client/Core | `719e23d...` / `75ba7e7...` / `cd8f0f4...` |
| Release index | `54cfa03...` |
| Signed manifest SHA-256 | `ae1906e68df755b1e0ce6a77d6ede8256f923e72fe11da57f1cae89a82c4ffe6` |
| Windows setup SHA-256 | `0afaf6e1d73a7e72762d945557f48793646a9bdbf12bb8ca2e843d4b94df276c` |
| Windows setup size | `28,932,793` bytes |
| Authenticode | `NotSigned`; `SKIPPED_BY_OWNER` for direct beta only |
| Host | owner current Windows host; clean app state only |

The signed manifest and detached signature validate before the test. The
candidate tuple, setup digest and byte size match the reviewed exact input.

## Proved current-host slice

The elevated bounded run passes all of the following:

- exact setup install with exit code zero;
- `8/8` installed files match manifest size and SHA-256;
- the automatic LocalSystem service runs the exact installed binary and is
  bound to the install owner;
- the installed UI remains alive and the protected service journal records an
  accepted authenticated IPC session plus status request;
- SCM stop and restart complete;
- uninstall removes the service, installed files and owner registry record;
- route and DNS fingerprints remain unchanged across the idle test;
- no POKROV/Wintun adapter remains.

This result is
`PASS_EXACT_CANDIDATE_CURRENT_HOST_CLEAN_APP_STATE_INSTALL_SERVICE_IPC_RESTART_UNINSTALL_IDLE_NETWORK`.

## Connected attempt and rollback

The installed app reported that account preparation was incomplete and did
not enter connected state. No live connected probe was accepted. The guarded
harness was intentionally aborted instead of recording a false connected
result.

Rollback then independently confirms:

- service absent;
- install directory absent;
- owner registry record absent;
- zero tunnel adapters;
- route and DNS fingerprints restored.

The connected slice is `NOT_PROVED_CURRENT_HOST_ACCOUNT_NOT_READY`, not PASS.
Live TUN, DNS/leak, owned-profile egress, sleep/reboot/crash recovery and
uninstall while connected remain `MANUAL_OWNER_TEST`.

## Retained client gate

Client PR `Kiwunaka/POKROV-app#49` adds the candidate.16 gate binding and
guarded current-host authorization token. Implementation commit
`cbc4a1209da005d5e062d0a02bb7df766fd2c4b5` merges to `main` as
`8f41214fa346bd71701f7b9b7633631c33acac93`.

Focused release-v2, documentation and full seed validation pass against the
exact platform and Core sources. Hosted run `33438226147`, job `99639770629`,
contains `steps=[]` and is `HOSTED_CHECK_BLOCKED_BY_BILLING`; PR 49 merged
under `OWNER_SOLO_EXCEPTION`, not as a hosted PASS.

## Completion-index effect

No ledger row advances. `WIN-003` and `DOD-04` remain `I1` because their live
connected clean-host acceptance is open. `WIN-004`, `WIN-005`, `SEC-001` and
Gate C remain `I3` with stronger exact-candidate bounded evidence. Gate A and
Gate F/G do not advance.

The distribution remains `I4=5`, `I3=319`, `I2=20`, `I1=34`, `I0=0` across
`378` rows.

## Evidence and ceiling

- normalized evidence:
  `evidence/013DL-candidate16-windows-current-host/013DL-candidate16-windows-current-host.json`;
- normalized evidence SHA-256:
  `43e6f883bbbe8e7a7390dbbb00ff9dbe42557178e8bf2e9b8b7d61929afb7da3`.

The evidence ceiling is the exact candidate.16 owner-current-host idle slice.
It does not prove a clean OS, connected network behavior, trusted Windows
signing, public release, stable promotion or production readiness.

## Next action

Continue terminal-only checks while the owner uses the PC. Run interactive
connected state only when it will not take focus. Before I4, repeat on isolated
clean Windows 10 and 11 and retain TUN, DNS/leak, egress, recovery and
connected-uninstall evidence.
