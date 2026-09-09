# Windows connected recovery — 2026-09-08

PASS_BOUNDED on the unchanged Win11 v3 lab package: client `6fc1e84`, Core
`8dc57a8`. Forced termination of the UI left the same running service PID and
TUN; relaunch observed the active connection. Graceful reboot while connected
to the temporary AWG3.1 assignment returned to safe disconnected state, restored
the exact route/DNS baseline and started the automatic LocalSystem service.
All 305 installed hashes matched before and after reboot.

[Source-bound evidence](evidence/windows-recovery-2026-09-08.json) points to
`E:/r12client/docs/operations/evidence/2026-09-08-r12-connected-recovery/`.
The receipt retains 21 observations/scripts and original/normalized hashes.
Diagnostic probe label `0218e89` identifies its own source, not the newer UI.

This does not close service-process crash, abrupt power loss or post-reboot
reconnect. The current guest token is not elevated; forced service termination
was not executed. `powercfg` reports no supported guest sleep/hibernate state,
so sleep remains BLOCKED_BY_ACCESS. Independent route proof, IPv6, WFP, Win10,
other protocols and the exact final candidate remain open. No protected
recovery-journal readback was collected in this slice.

Commands: scoped `lab-control.py` binding/restore, guest `ui-termination.ps1`,
`recovery-launch-ui.ps1`, `network.ps1`, `final-identity.ps1`, connected
`shutdown.exe /r /t 15`, final shutdown, then clone `--nic1 none` after poweroff
readback. Machine assertions verify the retained state and identity comparisons.
Full original rollout configuration restored; entitlement and endpoint material
unchanged. Host route/DNS hashes match the retained baseline. Source VM and
snapshot preserved; the disposable clone is off and offline.

No product code or release bytes changed. No build, new candidate, push, merge,
deployment, publication or payment. W01/W02/W04 receive bounded evidence only;
their parent status and the full plan remain active.

Client evidence commit: `6014b91`. Validation: client
`pwsh -NoProfile -File scripts/validate-seed.ps1 -PlatformRoot
C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start -CoreRoot
E:/r12core-implementation` PASS, including docs contract. Platform
`python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py
tests/test_agent_context_packet_audit.py -q` — 33 PASS;
`python -B scripts/agent_context_packet_audit.py --platform-context-root .` PASS;
work-order `validate_package.py` PASS (83 R12 IDs, 378 legacy IDs, 297 links).
`git diff --check` and all 21 retained Git evidence hashes PASS. A retained
power-state text's trailing blank line and LF normalization were corrected
before commit; original local bytes/hash remain recorded. Concurrent generated
files were excluded.
