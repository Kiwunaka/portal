# W04 Windows startup and teardown — 2026-09-07

Active partial evidence. [Receipt](evidence/w04-shell.json). Client source
`0f115d0` and `98c39d6`, Core `8dc57a8`; owned offline Win11 clone
`d5ae2f7a-96c3-48b5-a2ba-5e009948ee27`. Local portable UI with an unavailable
loopback API; no service install, managed VPN, installer or final channel.

Two observed defects are fixed: repeated `--startup` no longer reveals a hidden
existing window; native Flutter teardown no longer re-enters a destructing
controller. The same VM probe shows the original failure and final success.
Six activation/visibility checks pass on the final UI. Original exit is
`-1073740771`, fixed exit is 0; error events are 2 for red PID and 0 for green.
The real tray Exit item also closes the fixed PID with code 0 and no crash event.

Windows Flutter tests: 24 PASS; analyze PASS; native activation CTest 1/1 PASS;
Windows release build and explicit client/Core/platform seed validation PASS.
The first seed command used PowerShell 5.1 and failed on HashData; pwsh passed.
An incomplete local archive without CRT and non-activating tray input attempts
remain retained as rejected setup/collector evidence. They are not app PASS.
Autostart on/off was observed through UI and exact Run-key readbacks; actual
login boot and connected exit/proxy restoration remain open.

Final guest state: no POKROV UI/service, no up adapter, no POKROV Run key; two
fixture tasks exported and removed. Clone remains running offline for the
owner-authorized remaining tests. Original VM and snapshots are preserved.
Canonical client owner: `docs/operations/windows-release-readiness.md`, with
full client receipt under `docs/operations/evidence/2026-09-07-r12-w04-shell/`.
W04 becomes active I3 / NEEDS_RUNTIME_PROOF; W01–W06 and release remain open.
No push, merge, candidate, publication, production deployment or payment action.

Final documentation checks: client seed/docs PASS; platform docs 33 PASS;
context audit PASS; package 13 imports / 83 R12 IDs / 378 legacy IDs / 275 links
PASS; scoped diff check PASS. Final Windows bundle retains the same 305 files
as the startup-fix bundle; only `pokrov_windows.exe` differs. OS readback is
Windows `10.0.26200`, 64-bit.
