# WO-013AP — Linux network transaction observability

Date: `2026-08-28`

Status: `IMPLEMENTED_SOURCE_ONLY / LINUX_RUNTIME_NOT_RUN`

## Objective

Close the source-level `OBS-045` gap without pretending that the conditional
Linux beta can carry traffic. Add a closed NetworkManager/systemd-resolved/
nftables checkpoint/apply/rollback event producer, wire the current unavailable
connect path to honest preflight evidence and keep all actual network mutation,
clean-host restoration and Linux publication claims fail-closed.

## Exact source

Client PR `#28` head
`583e04a63c6511ea42f24394c185d11dc9a9d76b` on
`codex/linux-beta-foundation-current` owns this slice. It remains a separate
conditional-Linux branch against `POKROV-app/main`; it is not the build-4046
Android/Windows working source, a signed candidate or a public Linux artifact.

The branch-basis seed check used platform head
`64d68b0284d8bd0084ceda8c532f958317bc41bd` and the exact detached Core
authority `344b317a7a09eca7943a93866b193553538bd8f6`, matching the branch's
declared `1.2.0+30` pre-candidate contract. This does not rebase or relabel the
later build-4046 client lane.

## Implementation

The daemon's existing `pokrov-linux-operational-v1` writer is split into a
portable closed encoder plus the Linux journald transport. Existing events keep
their prior fields. The additive `network_transaction` event requires:

- one bounded transaction ID and request correlation ID;
- the current profile generation;
- exactly one subsystem: `network_manager`, `resolved` or `nftables`;
- exactly one stage: `checkpoint`, `apply` or `rollback`;
- only `pass`, `unavailable` or stage-specific `reject` outcomes;
- only the closed `linux_network_unsupported`,
  `linux_network_checkpoint_failed`, `linux_network_apply_failed` or
  `linux_network_rollback_failed` error code where applicable.

Command strings, arguments, paths, interfaces, addresses, resolver contents,
nft rules, destinations and raw errors have no event or fallback field.
Malformed identifiers, unknown enum values, incompatible outcome/error pairs
and transaction fields attached to an unrelated event are rejected before the
native or fallback writer.

The typed recorder exposes checkpoint/apply/rollback methods for all three
owners. The current production service path is also wired: an authorized
`connect` attempt emits three `checkpoint/unavailable` records, then preserves
the existing `linux_live_connect_unavailable` response. It does not emit a
synthetic checkpoint success, apply success or rollback success while actual
NetworkManager/resolved/nft operations do not exist.

## Verification

- exact Go toolchain: `go1.25.13 windows/amd64`;
- portable Go tests pass for journal, transaction recorder, profile and
  protocol packages;
- changed Go files pass exact `gofmt` readback;
- Linux/amd64 `go vet ./...` passes;
- Linux/amd64 daemon cross-build passes;
- all `9` Linux package test binaries compile, including the Linux-only service
  wiring test; they were not executed on this Windows host;
- Linux Flutter analysis passes with no issues and Linux shell tests pass
  `4/4`;
- client docs contract and full branch-basis seed validation pass;
- staged diff check, secret-like scan and `artifacts/releases/**` delta pass.

The whole-tree Windows `gofmt -l` result is not used because existing unchanged
Go files are checked out with CRLF and appear dirty to gofmt on Windows. Only
the changed Go files were formatted and verified. Hosted PR execution remains
separate: exact-head run `33145424445` completed as failure with `steps=[]`, so
it is `BLOCKED_BY_ACCESS_GITHUB_BILLING`, not a product-test failure or pass.

## Ledger decision

`OBS/OBS-045` advances `I1 -> I2` as `IMPLEMENTED_SOURCE_ONLY`: the typed event
producer, closed encoder, unavailable preflight wiring and focused portable
tests exist. It does not reach `I3` because Linux-only tests have not executed
on a Linux host and no real NetworkManager checkpoint, resolved/nft mutation,
journald readback or clean-host rollback has occurred.

The journal encoder/rejection tests strengthen `OBS/OBS-043`, but that row
remains `I2` pending native journald socket/fallback/rotation readback. No D-Bus
trace was added, so `OBS/OBS-044` remains `I2` unchanged.

Distribution becomes `I4=4`, `I3=314`, `I2=20`, `I1=39`, `I0=0`; `318/377`
rows remain at or above `I3`, while `59/377` remain below.

## Remaining proof

1. Execute the full Go suite on the exact Linux source under a real Linux host.
2. Implement the actual Core/TUN lifecycle and NetworkManager checkpoint,
   resolved and nft participants using this recorder without accepting raw IPC
   commands.
3. Inject checkpoint, partial-apply and rollback faults and retain native
   journald plus sanitized UI readback.
4. Prove route/DNS/nft restoration on a clean Ubuntu 24.04 desktop session,
   then repeat on every declared matrix row before `I4`.
5. Keep Linux conditional and absent from public `1.2.0` until signed packaging,
   candidate binding and the full platform matrix are separately proven.

No merge, package publication, deploy or runtime network mutation occurred.
