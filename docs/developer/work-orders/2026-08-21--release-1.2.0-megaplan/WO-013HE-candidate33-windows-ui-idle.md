# WO-013HE — candidate.33 Windows fresh-process UI idle observation

Status: `PASS_EXACT_CANDIDATE33_WINDOWS_FRESH_PROCESS_UI_IDLE_NO_NETWORK_MUTATION; PERFORMANCE_BUDGET_NOT_DEFINED; GATE_F_BLOCKED`

Observed: `2026-09-04`

Production/public mutation: `NONE`

## Outcome

The exact installed candidate.33 Windows UI now has bounded warm-cache and
post-reboot fresh-process startup/idle observations from the dedicated headless
Windows 11 VM. The exact `pokrov_windows.exe` process starts in the ordinary
user session without host input, exposes a responsive window and remains
responsive for every retained sample in both runs.

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
| Post-reboot repeat | guest boot `2026-09-04T16:19:24.5Z`; responsive window `2560.474 ms`; 10/10 responsive over `45` seconds |
| Post-reboot CPU / working set | `0.9722%`; p50/p95 `99446784/99713024` bytes |
| Post-reboot private memory | p50/p95 `77172736/85934080` bytes; crash events `0` |
| Network safety | route/DNS fingerprint unchanged; POKROV/Wintun Up count `0`; connect not requested |
| Cleanup | UI process `0`; service Running/Auto/LocalSystem; route/DNS restored |

## Evidence

The external evidence index is:

```text
E:/POKROV-tools/release-evidence/1.2.0-candidate33-windows-idle-performance-2026-09-04/candidate33-windows-ui-idle-evidence-index.json
SHA-256 82fe9df648f3f4b9d01b77c3321696ea9f44406bbfa54e8e583581677b71c42a
```

The client-normalized evidence is
`docs/operations/evidence/candidate33-windows-ui-idle.json`, SHA-256
`6a0d1f81fec2cd8d4b7db5e4fb0de5b4d3ad3dbdd9b40a20f04af2ab40b6ce54`.
Client PR `85` merges the post-reboot reconciliation at
`82268d2ef086c879ce04bffd9eedee9737c923d8`. Hosted run `33895179510`
terminates with `steps=[]` and remains
`BLOCKED_BY_ACCESS_GITHUB_BILLING`, not a product-test failure or PASS.

Closing the main window follows the product tray contract and keeps the
process resident. The harness therefore force-stops only the UI after the
measurement. This is planned cleanup, not a crash; the service, route/DNS
fingerprint and inactive adapter state remain unchanged.

The platform-retained summary is
`evidence/013HE-candidate33-windows-ui-idle/013HE-candidate33-windows-ui-idle.json`,
SHA-256 `f2b17ec63cd2fcbb3141d299d50c393851c0515e4e2dbc326da0f0592d323b31`.

## Release impact

`REL/PERF-001`, Gate E, `REL_DOD/DOD-13` and `FE_PR/PR-09` gain stronger
exact-candidate descriptive evidence without level change. One warm-cache run
and one post-reboot repeat on the same 2-vCPU/4-GiB VM are not a controlled
cold-boot distribution, comparable-device or release performance-budget PASS. Connect latency,
physical Windows, Windows 10, battery/thermal/endurance, browser comparison and
post-promotion proof remain open. Gate F stays `BLOCKED 2/17/0`.

No candidate bytes, deploy, public asset, Store object, stable pointer,
production account, control-plane state, host input or host network changed.
