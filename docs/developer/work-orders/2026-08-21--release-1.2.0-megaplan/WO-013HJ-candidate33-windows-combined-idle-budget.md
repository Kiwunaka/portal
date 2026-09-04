# WO-013HJ — candidate.33 Windows combined UI/service idle budget

Status: `PASS_EXACT_CANDIDATE33_WINDOWS_COMBINED_UI_SERVICE_IDLE_CPU; MEMORY_BASELINE_RECORDED; FULL_CANDIDATE_DEVICE_SCOPE_OPEN; GATE_F_BLOCKED`

Observed: `2026-09-04`

Production/public mutation: `NONE`

## Outcome

The exact candidate.33 Windows UI and automatic service pass the owned combined
idle CPU budget in the dedicated headless Windows 11 VM. A limited interactive
task keeps the disconnected, responding UI open while the exact
`POKROVService/pokrov_service.exe` remains Running. The harness discards 30
one-second warmups and retains 60 one-second samples from both processes.

Nearest-rank combined CPU p95 is `0.749734%`, below the `1.0%` target and stop
boundary. The offline validator returns `PASS` for
`client.windows.idle_cpu_percent`. Combined UI-plus-service working-set p95 is
`108158976` bytes. Because this fuller process boundary has no comparable
approved predecessor, the memory result is `BASELINE_RECORDED`, not a
regression PASS and not a comparison with the earlier UI-only baseline.

Two setup attempts stopped before accepting samples because the external
Windows PowerShell harness assumed a process CPU property shape that was not
present. The corrected harness uses numeric process CPU seconds. Both rejected
attempts remain `HARNESS_FAILURE_NO_PRODUCT_RESULT`; candidate bytes and the
budget contract did not change.

## Exact boundary

| Fact | Exact value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.33`, app `1.2.0+4053` |
| Platform / client / Core / index | `f530005...5bc1` / `6ab1bca...735e` / `cd8f0f4...884d` / `63993fb...c43c` |
| Installed UI | `192512` bytes; SHA-256 `1b175a66...1d97` |
| Installed service | `188416` bytes; SHA-256 `b962d3d0...326b` |
| Environment | Windows 11 Enterprise Evaluation build `26200`; VirtualBox; 2 vCPU; `4274917376` bytes RAM; Balanced; session `1` |
| Sampling | 30 discarded warmups; 60 retained one-second samples; disconnected responding UI plus Running automatic service |
| CPU | min/p50/p95/max `0/0/0.749734/1.499068%`; average `0.137304%`; `PASS` at `<=1%` |
| Working set | min/p50/p95/max `107610112/108019712/108158976/108158976` bytes; `BASELINE_RECORDED` |
| Safety | crash events `0`; service Running; adapter Up `0`; route/DNS unchanged; UI process `0` after cleanup |

## Evidence

The external raw/normalized evidence index is:

```text
E:/POKROV-tools/release-evidence/1.2.0-candidate33-windows-combined-idle-budget-2026-09-04/candidate33-windows-combined-idle-budget-evidence-index.json
SHA-256 6c2434c1178b5f3fb61c1e5bb356c026142b822fd4c025a62b4b3382a06a44f2
```

Client evidence is
`docs/operations/evidence/candidate33-windows-combined-idle-budget.json`,
SHA-256 `cd7e4608e44d0465e1a063aad8f9518d4cf775627792ed31879613a9c1c29e95`.
Client PR `89` merges the reconciliation at
`c2d00d0520a35344740fa429fbe559a96bc0ed8c`. Hosted run `33906621241`
terminates with `steps=[]` and remains `BLOCKED_BY_ACCESS_GITHUB_BILLING`, not
a product-test failure or PASS.

The platform-retained summary is
`evidence/013HJ-candidate33-windows-combined-idle-budget/013HJ-candidate33-windows-combined-idle-budget.json`,
SHA-256 `7f88cc25f17b153d4c92bb7c70df472110be0f21b8b67620029244ff0246125b`.

## Release impact

`REL/PERF-001`, `REL_GATE/GATE-E`, `REL_DOD/DOD-13` and `FE_PR/PR-09`
gain exact-candidate combined Windows UI/service idle CPU PASS and its first
combined working-set baseline. Android cold start, Windows cold OS boot,
physical/comparable Windows, verified connect/reconnect/rollback, frame timing,
Android idle, battery/thermal/endurance, matching memory/artifact regression,
authenticated cabinet performance and post-promotion health remain open. Every
row retains its prior level, and Gate F remains `BLOCKED 2/17/0`.

No candidate bytes, deploy, public asset, Store object, stable pointer,
production account, control-plane state, host input or host network changed.
