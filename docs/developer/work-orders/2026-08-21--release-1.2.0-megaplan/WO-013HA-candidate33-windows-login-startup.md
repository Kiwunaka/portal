# WO-013HA — candidate.33 Windows login startup

Status: `PASS_EXACT_CANDIDATE33_WINDOWS_LOGIN_STARTUP_HIDDEN_SINGLETON_ACTIVATION; GATE_F_BLOCKED`

Observed: `2026-09-04`

Production/public mutation: `NONE`

## Outcome

The cleanly reinstalled exact candidate.33 passed its real-login startup
boundary in the dedicated Windows 11 guest. The exact per-user Run value is the
quoted installed UI plus `--startup`. After guest reboot and interactive login,
Windows created one responsive session-1 POKROV UI process with no visible
window, UAC prompt, TUN or route/DNS drift.

An ordinary interactive-token activation returned `0` and exposed a main
window on the same original PID. It did not leave a second UI process or change
the LocalSystem service, route, DNS or TUN state. The temporary task, Run value
and UI were removed; the final network fingerprint exactly matched baseline.

This proves the exact installed `--startup` and singleton activation paths. The
Run value was staged directly in the real interactive user's hive, not through
the product preference toggle. Managed auto-connect, saved account/profile
state and delayed-network readiness therefore remain open.

## Exact boundary

| Fact | Exact value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.33`, app `1.2.0+4053` |
| Platform / client / Core / index | `f530005...5bc1` / `6ab1bca...735e` / `cd8f0f4...884d` / `63993fb...c43c` |
| Windows setup | `250622f7...3580`; installed `11/11` |
| Installed UI | `1b175a66...1d97` |
| Startup value | `"C:\Program Files\POKROV\pokrov_windows.exe" --startup` |
| Login process | PID `7236`, session `1`, responsive, main-window handle `0` |
| Ordinary activation | task result `0`; same PID `7236`; main-window handle `66164` |
| Network | TUN `0`; DNS `43a34dfb...5f2d`; routes `081b333e...9865` before, during and after |
| Cleanup | Run value absent, UI `0`, task removed, service Running/Auto/LocalSystem |

## Evidence

The external evidence index is:

```text
E:/POKROV-tools/release-evidence/1.2.0-candidate33-windows-startup-2026-09-04/candidate33-windows-login-startup-evidence-index.json
SHA-256 a0ba483a7dd87d12451ed8dcfdfd35f52caab6c7a298170983fa0ac48eb45090
```

The hidden-desktop screenshot SHA-256 is
`420cb3f713d6eb158ea2e727f16e4c87902fdc8957a3ff95e3b4496147059063`.
The visible same-process UI screenshot SHA-256 is
`575e235cdca627ab9f3a5129d5247c317f07ca56639c7c4f50de4e83fc59a49a`.

The first guest Run-dialog activation attempt retained a stale historical
command and did not reach POKROV; unchanged process/window state and retained
screenshots classify it as a harness-only miss. The successful activation used
a temporary `InteractiveToken` scheduled task, returned `0` and removed the
task before the final readback.

The platform-retained summary is
`evidence/013HA-candidate33-windows-login-startup/013HA-candidate33-windows-login-startup.json`,
SHA-256 `48be10b4155130a00a79e0ffc0e973982495feb02d340e1cad539a4719a524c5`.

## Release impact

`REL/WIN-005` receives exact-candidate startup-path evidence but remains `I3`
because the product preference toggle, managed auto-connect/saved state and
delayed-network readiness are unproved. Gate C and Gate F remain blocked; Gate
F stays `2/17/0`. No candidate bytes, deploy, public asset, Store object,
stable pointer, production account, server or host network changed.
