# WO-013HG — candidate.33 Windows idle performance budget

Status: `PASS_EXACT_CANDIDATE33_WINDOWS_UI_IDLE_CPU; MEMORY_BASELINE_RECORDED; FULL_CANDIDATE_DEVICE_SCOPE_OPEN; GATE_F_BLOCKED`

Observed: `2026-09-04`

Production/public mutation: `NONE`

## Outcome

The exact candidate.33 Windows UI now has a contract-valid idle CPU result in
the dedicated headless Windows 11 VM. The canonical client collector runs
under PowerShell Core `7.6.5`, discards 30 one-second warmups and retains 60
one-second samples from the exact `pokrov_windows.exe` process.

Idle CPU p95 is exactly `1.0%`, meeting both the `1.0%` target and stop
boundary. The offline validator therefore returns `PASS` for
`client.windows.idle_cpu_percent`. Working-set p95 is `98693120` bytes. Because
the memory budget is observation-first and has no matching approved baseline,
the validator returns `BASELINE_RECORDED`, not a regression PASS.

Two initial harness attempts stop at the collector's explicit PowerShell Core
guard. A later forced Windows PowerShell 5 run is preserved only as
`INVALID_METHOD` and excluded from the normalized gate. It is not a product
failure and does not influence the accepted PowerShell Core result.

## Exact boundary

| Fact | Exact value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.33`, app `1.2.0+4053` |
| Platform / client / Core / index | `f530005...5bc1` / `6ab1bca...735e` / `cd8f0f4...884d` / `63993fb...c43c` |
| Installed UI | `pokrov_windows.exe`; `192512` bytes; SHA-256 `1b175a66...1d97` |
| Environment | Windows 11 Enterprise Evaluation build `26200`; 2 vCPU; `4274917376` bytes RAM; Balanced; interactive session `1`; headless VM |
| Collector | exact client `collect-client-performance-samples.ps1`; PowerShell `7.6.5`; 30 warmups; 60 retained samples; 1-second interval |
| CPU | min/p50/p95/max `0/0/1/1%`; average `0.083333%`; `PASS` |
| Working set | min/p50/p95/max `98660352/98693120/98693120/98693120` bytes; `BASELINE_RECORDED` |
| Runtime safety | UI responsive; matching crash events `0`; service Running; adapter Up `0`; route/DNS hashes unchanged |
| Cleanup | UI process `0`; temporary guest QA directory and portable PowerShell removed |

## Evidence

The external raw/normalized evidence index is:

```text
E:/POKROV-tools/release-evidence/1.2.0-candidate33-windows-idle-budget-2026-09-04/candidate33-windows-idle-budget-evidence-index.json
SHA-256 db39ed2cd619ff84b618f43a9dc43c09cf5b1693ff3a0856557ee99a458353c6
```

Client evidence is
`docs/operations/evidence/candidate33-windows-idle-budget.json`, SHA-256
`b4040fc455f48e08893a4fb2ed61f758228490e6b9ddbbb9040a462bc01981be`.
Client PR `86` merges the reconciliation at
`9a1c3b9b6fb58354a91066b1c812a2076b759990`. Hosted run `33899926514`
terminates with `steps=[]` and remains `BLOCKED_BY_ACCESS_GITHUB_BILLING`, not
a product-test failure or PASS.

The platform-retained summary is
`evidence/013HG-candidate33-windows-idle-budget/013HG-candidate33-windows-idle-budget.json`,
SHA-256 `60684b7dde961b6a3ce35c15fc8469332051971efa618c11acc3d86c4c84218a`.

## Release impact

`REL/PERF-001`, Gate E, `REL_DOD/DOD-13` and `FE_PR/PR-09` gain the first exact
candidate.33 Windows idle CPU budget PASS and an explicit working-set baseline
without level change. This is one VM and one UI process. It does not prove a
physical/comparable Windows distribution, service-combined idle consumption,
cold start, connect/reconnect/rollback, frame, battery/thermal/endurance,
browser/cabinet completion or post-promotion performance. Gate F stays
`BLOCKED 2/17/0`.

No candidate bytes, deploy, public asset, Store object, stable pointer,
production account, control-plane state, host input or host network changed.
