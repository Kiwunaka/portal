# WO-013HE — candidate.33 Windows fresh-process UI idle observation

Status: `PASS_EXACT_CANDIDATE33_WINDOWS_FRESH_PROCESS_UI_IDLE_NO_NETWORK_MUTATION; PERFORMANCE_BUDGET_NOT_DEFINED; GATE_F_BLOCKED`

Observed: `2026-09-04`

Production/public mutation: `NONE`

## Outcome

The exact installed candidate.33 Windows UI now has a bounded fresh-process
startup and idle observation from the dedicated headless Windows 11 VM. The
exact `pokrov_windows.exe` process starts in the already active ordinary user
session without host input, exposes a responsive window and remains responsive
for every retained sample.

The sample deliberately does not connect. Route/DNS fingerprints stay
unchanged, the retained hidden POKROV adapter is never Up, the LocalSystem
service remains Running/Auto and the Application event log contains no matching
crash. Cleanup removes only the UI process and preserves the service/network
baseline.

## Exact boundary

| Fact | Exact value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.33`, app `1.2.0+4053` |
| Platform / client / Core / index | `f530005...5bc1` / `6ab1bca...735e` / `cd8f0f4...884d` / `63993fb...c43c` |
| Installed UI | `pokrov_windows.exe`; `192512` bytes; SHA-256 `1b175a66...1d97` |
| Environment | Windows 11 Enterprise Evaluation; 2 vCPU; `4274917376` bytes RAM; interactive session `1`; headless VM |
| Startup | fresh process with warm guest file cache; process `75.107 ms`; responsive window `376.835 ms` |
| Idle window | 10 samples every 5 seconds; retained duration `45` seconds; all responsive/window-present |
| CPU | `1.9097%`, normalized across two logical processors |
| Working set | p50 `94621696`; p95 `95019008` bytes |
| Private memory | p50 `76607488`; p95 `81367040` bytes |
| Threads / handles | `15–22` / `378–404` |
| Crash events | `0` matching Application Error / Windows Error Reporting events |
| Network safety | route/DNS fingerprint unchanged; POKROV/Wintun Up count `0`; connect not requested |
| Cleanup | UI process `0`; service Running/Auto/LocalSystem; route/DNS restored |

## Evidence

The external evidence index is:

```text
E:/POKROV-tools/release-evidence/1.2.0-candidate33-windows-idle-performance-2026-09-04/candidate33-windows-ui-idle-evidence-index.json
SHA-256 d176d3c08df91366e055626c012a8304a0c6e535e0f49bcb285c8411f679d68a
```

The client-normalized evidence is
`docs/operations/evidence/candidate33-windows-ui-idle.json`, SHA-256
`b993ee6d7f2ed572c41b12e0bff5b3cff4185eb71f9392365eb81ecf7641d5cc`.
Client PR `84` merges that reconciliation at
`ec67ef86b03ff316a33b048142ece73e6256ce8a`. Hosted run `33893847234`
terminates with `steps=[]` and remains
`BLOCKED_BY_ACCESS_GITHUB_BILLING`, not a product-test failure or PASS.

Closing the main window follows the product tray contract and keeps the
process resident. The harness therefore force-stops only the UI after the
measurement. This is planned cleanup, not a crash; the service, route/DNS
fingerprint and inactive adapter state remain unchanged.

The platform-retained summary is
`evidence/013HE-candidate33-windows-ui-idle/013HE-candidate33-windows-ui-idle.json`,
SHA-256 `d242d05b99fca9efbd5203c7bb1085bbed80eec19d79218c22617b04aa725b80`.

## Release impact

`REL/PERF-001`, Gate E, `REL_DOD/DOD-13` and `FE_PR/PR-09` gain stronger
exact-candidate descriptive evidence without level change. This one
warm-file-cache, 45-second, 2-vCPU/4-GiB VM sample is not a cold-boot,
comparable-device or release performance-budget PASS. Connect latency,
physical Windows, Windows 10, battery/thermal/endurance, browser comparison and
post-promotion proof remain open. Gate F stays `BLOCKED 2/17/0`.

No candidate bytes, deploy, public asset, Store object, stable pointer,
production account, control-plane state, host input or host network changed.
