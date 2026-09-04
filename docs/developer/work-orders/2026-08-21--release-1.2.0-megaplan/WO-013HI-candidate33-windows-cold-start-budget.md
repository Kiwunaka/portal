# WO-013HI — candidate.33 Windows useful cold-start budget

Status: `PASS_EXACT_CANDIDATE33_WINDOWS_USEFUL_COLD_PROCESS_START; FULL_CANDIDATE_DEVICE_SCOPE_OPEN; GATE_F_BLOCKED`

Observed: `2026-09-04`

Production/public mutation: `NONE`

## Outcome

The exact candidate.33 Windows UI passes the owned useful cold-start target in
the dedicated headless Windows 11 VM. A limited interactive-session task
discards 3 warmups, then recreates the UI process for each of 20 retained
launches. The terminal is not a green label or process existence alone: the
exact `pokrov_windows.exe` must expose a responding `POKROV` window containing
at least one visible rendered UI Automation pane.

Nearest-rank p95 is `1499.404 ms`, below both the `2000 ms` optimization target
and `3500 ms` promotion stop. The offline performance validator returns
`PASS` for `client.windows.cold_start_useful_ui_ms`.

This is a cold process start with a warm operating system, not a cold OS boot.
It is one VM, not physical/comparable Windows evidence. Those boundaries stay
open and are not relabelled as PASS.

## Exact boundary

| Fact | Exact value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.33`, app `1.2.0+4053` |
| Platform / client / Core / index | `f530005...5bc1` / `6ab1bca...735e` / `cd8f0f4...884d` / `63993fb...c43c` |
| Installed UI | `192512` bytes; SHA-256 `1b175a66...1d97` |
| Environment | Windows 11 Enterprise Evaluation build `26200`; VirtualBox; 2 vCPU; `4274917376` bytes RAM; Balanced; session `1` |
| Sampling | 3 discarded warmups; 20 retained; ordinary limited-user launch; process recreated each time |
| Terminal | responding `POKROV` window plus visible rendered UIA pane |
| Timing | min/p50/p95/max `310.576/399.142/1499.404/1911.46 ms`; average `556.63 ms` |
| Budget | target `<=2000 ms`; stop `<=3500 ms`; `PASS` |
| Safety | crash events `0`; service Running; adapter Up `0`; UI process `0` after cleanup |

## Evidence

The external raw/normalized evidence index is:

```text
E:/POKROV-tools/release-evidence/1.2.0-candidate33-windows-cold-start-budget-2026-09-04/candidate33-windows-cold-start-evidence-index.json
SHA-256 d81fb1a0d32cf0de0eb4ef242d9ace4898468b31693778e57c5b7aebee307a6d
```

Client evidence is
`docs/operations/evidence/candidate33-windows-cold-start-budget.json`, SHA-256
`d0aa43172b469a47bf0cc3aaf7c19588ffcf06737e2727214af7da604f85cc9c`.
Client PR `88` merges the reconciliation at
`3a88044cc8c6dc49ac652bdf681a71e53f22c4d0`. Hosted run `33903440689`
terminates with `steps=[]` and remains `BLOCKED_BY_ACCESS_GITHUB_BILLING`, not
a product-test failure or PASS.

The platform-retained summary is
`evidence/013HI-candidate33-windows-cold-start-budget/013HI-candidate33-windows-cold-start-budget.json`,
SHA-256 `b8eb1684e4d587fa4c017ee5243e3e07d4d146fa4ef1109c66c4da3e244312da`.

## Release impact

`REL_DOD/DOD-13` gains an exact-candidate Windows useful cold-process start
PASS. Android cold start, Windows cold OS boot, physical/comparable Windows,
verified connect/reconnect/rollback, frame timing, Android idle,
battery/thermal/endurance, matching memory/artifact regression, authenticated
cabinet performance and post-promotion health remain open. The row remains
`I1` and Gate F remains `BLOCKED 2/17/0`.

No candidate bytes, deploy, public asset, Store object, stable pointer,
production account, control-plane state, host input or host network changed.
