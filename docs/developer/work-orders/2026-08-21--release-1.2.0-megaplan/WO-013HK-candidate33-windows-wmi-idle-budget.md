# WO-013HK — candidate.33 Windows raw-WMI combined idle

Status: `WINDOWS_VM_COMBINED_IDLE_CPU_PASS; MEMORY_BASELINE_RECORDED; GATE_F_BLOCKED`

## Exact scope

Fresh capture of candidate.33 (`1.2.0+4053`) installed UI and automatic
LocalSystem service, both SHA-256 checked before sampling. Client revision
`6ab1bcaf39c61a0ae0c9d8328e6c95382885735e`; platform normalizer/validator
`f5300053026d32826e54c02202303e1f68c65bc1`. Dedicated Windows 11 VM build
26200, two vCPUs, 4 GiB, Balanced power mode. No connection was requested.

WO-013HJ's unavailable-counter CPU result remains withdrawn. This is a new
capture, not a relabeling of the rejected run. No candidate bytes changed.

## Method and result

The ordinary account can read both process counters through
`Win32_PerfRawData_PerfProc_Process`, without elevating UI or collector.
Use raw `PercentProcessorTime` and matching `Timestamp_Sys100NS` deltas,
sum UI/service time, divide by elapsed time and two logical processors.
Subtract as decimals before floating-point division. Null counters, missing
processes, changed process-start identity, unequal timestamps and nonmonotonic
deltas fail the run. The formula follows
[Microsoft's counter calculation reference](https://learn.microsoft.com/en-us/windows/win32/perfctrs/calculating-counter-values).

Thirty warmups and 60 retained samples cover `62.5179899` retained seconds;
actual intervals are `1.0325312–1.0738546` seconds. Python independently
recomputes all 90 rows. The UI raw-WMI/native cumulative counters agree exactly
at every recorded observation; the service cumulative counter is nonzero and
readable (`0.21875` CPU seconds). No missing counter is converted to zero.

- CPU p95 `0.7511949889693326%`: offline validator `PASS` at `<=1%`.
- Working-set p95 `107057152` bytes: `BASELINE_RECORDED`, not regression PASS.
- Route/DNS fingerprints match before/after. Immediate cleanup still observed
  one exiting UI process; separate timestamped readback at
  `2026-09-04T19:10:13.3410903Z` proves UI `0`, service `Running`, tunnels `0`.
  Both observations are retained, without editing the raw result.

## Retained evidence

Client summary: `docs/operations/evidence/candidate33-windows-wmi-idle-budget.json`.
Raw report SHA-256:
`f25575eef269715a3da81929d3ecc40ea0620017d8b4c70e937ddf7397bd45f1`.

External index (12 files, including raw counters, cleanup readback, harness,
independent verifier, normalized arrays and validator reports):

```text
E:/POKROV-tools/release-evidence/1.2.0-candidate33-windows-wmi-idle-2026-09-04/evidence-index.json
SHA-256 8c09ee8710c396469222cbaaebad77656b648c97408071266939eb98ba66d63d
```

## Release boundary

Verification: external `verify-and-extract.py` recomputes 90/90 rows; all 12
indexed hashes/lengths match. Exact-source `new_performance_evidence.py` and
`performance_budget_gate.py` produce the CPU PASS and memory baseline above.
Platform performance-gate/normalizer tests pass 14/14; documentation/context/
candidate-preflight tests pass 57/57; context audit, link check and diff check
pass. Client `scripts/validate-seed.ps1` (explicit exact platform/Core roots),
including docs and collector contracts, passes. No `artifacts/releases` delta.
The 378 unique ledger rows retain `I1=32`, `I2=19`, `I3=319`, `I4=8`.

PERF-001, GATE-E, DOD-13 and PR-09 gain only this exact Windows VM idle slice.
All execution levels are unchanged. Physical/comparable Windows, Android,
managed connection/frame/battery/thermal, matching regression and authenticated
cabinet gates remain open. Gate F remains `BLOCKED 2/17/0`.
No host input/network, production, deployment, publication or signing change.
