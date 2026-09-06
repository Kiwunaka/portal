# Windows 11 — isolated component lab

2026-09-06. **PASS component fixtures; SCM MANUAL_OWNER_TEST; release OPEN.**
Client source `ded58b1906bbfb1096ff919085ef37f5be942eb7`, Core
`94dd31012ac91fb9ecf2c98ad7383afb54102dd4`, platform starting HEAD `5d613dc`.
This advances local N02/D05 verification and W01–W03 preparation. It does not
close their actual managed-network, crash/sleep or installer criteria. Register
statuses remain unchanged; no new candidate or historical receipt reuse.

## Environment and bytes

The source `POKROV-Win11-Test` remains powered off. A linked clone was created
from its `ready-for-pokrov-tests` snapshot
`c0abfe48-b33c-4d9d-8556-6a7196aa1916`. Clone
`POKROV-r12-win11-20260906T035616Z`, UUID
`d5ae2f7a-96c3-48b5-a2ba-5e009948ee27`, had NIC1 set to `none` before its first
boot. Guest SMBIOS UUID matches; Windows version is `10.0.26200`.

Guest baseline: no POKROV service, process, Program Files/ProgramData directory
or POKROV/TUN adapter; zero up adapters. Guest control runs with a filtered,
unelevated token. The account is a member of Administrators; UAC is enabled.
The initial Guest Additions version lookup used a nonexistent path and is not
version evidence. Source VM disk/config byte equality was not measured; no
original guest boot/install or explicit NIC change was performed.

Current Release service and seven native test executables were built from the
client worktree. Three x64 VC143 CRT DLLs and the two D05 Core runtime DLLs were
copied into a 13-file component payload. Host and guest SHA-256 match; Core DLL
hashes also match existing D05 two-build evidence. The 24,498,823-byte local ZIP
has SHA-256 `a6701396031b29efbb463811bf7a2fbe099cea170b0e937106367c7cb8ee2baf`.
It contains neither a UI nor an installer and is not a release candidate.

## Executed checks

- `cmake.exe --build apps/windows_shell/build/windows/x64 --config Release --target pokrov_service pokrov_service_runtime_test pokrov_service_security_test pokrov_service_protocol_test pokrov_windows_crash_profile_test pokrov_service_events_test pokrov_service_client_test pokrov_service_pipe_client_test` — exit 0.
- Guest `C:/Users/Public/R12Lab/native-tests-v2.ps1` through the clone-targeted
  `E:/r12-win11-invoke-guest.ps1` — seven exit codes 0, no timeouts. Protocol,
  security, crash profile, runtime, events, client parser and pipe client pass.
- The real guest runs filesystem/ACL, journal/restart and named-pipe mechanisms.
  Runtime tests use fake Core, egress and network backends. Release test checks
  use explicit failure returns; `NDEBUG` does not remove them. Debug-only
  service integration mode was not run.
- The first collector produced seven `null` exit codes due to its PowerShell
  process handling. It is rejected evidence, not PASS. It was replaced with
  `System.Diagnostics.Process`; both runs and all logs are retained.
- Seven final exits, 14 final log hashes, 13 payload hashes, D05 binding and
  three prepared SCM file hashes were verified. Post-run: service absent,
  zero up and POKROV adapters; source VM powered off, clone NIC1 `none`.

The exact CMake executable, source hashes, commands, raw logs and fixture
scripts are indexed in client
`E:/r12client/docs/operations/evidence/2026-09-06-r12-win11-component-lab/evidence.json`.
The work-order receipt is [windows-lab.json](evidence/windows-lab.json).

## Concrete pending SCM step

Inside the named clone, the owner can run
`C:/Users/Public/R12Lab/Run-SCM-Smoke.cmd` and confirm UAC. This launches the
prepared `scm-smoke.ps1`, which rejects a different VM, active network,
preexisting POKROV state or mismatched payload/probe hashes. It copies the
components into Program Files, creates a **manual-start** LocalSystem service,
queries authenticated status using current production client code, stops the
service and checks durable lifecycle events. It never requests profile staging
or connect. It retains the stopped service, registry, files and journal in the
clone for inspection; no removal is part of the script.

The probe compiled successfully and transferred files match their host hashes.
Before installation it returns exit 1 with unavailable/untrusted/incompatible
flags false, the expected negative result; this is not an installed-service pass.
The elevated script was syntax-checked only; its result is **MANUAL_OWNER_TEST**.
The owner action request is pending. The clone remains running without a NIC
for that action. The original VM stays powered off. After the owner run, collect
`C:/Users/Public/R12Lab/scm-smoke.json` and its logs before claiming any SCM PASS.

W01–W03 still require exact packaged bytes, standard-user UI/SCM, live managed
transport, TUN/DNS/IPv6/routes, Windows 10 scope, actual crash/kill/sleep/network
handoff/reboot, and connected upgrade/uninstall/reinstall evidence. No source
change, host VPN installation, production mutation, signing, push, merge,
deploy, publication or new release candidate was performed.

Documentation checks: client `validate-seed.ps1 -PlatformRoot
C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start -CoreRoot
E:/r12core-implementation` PASS; platform docs/context tests 33 PASS; context
packet audit PASS; package validator PASS (13 imports, 83 R12 IDs, 378 retained
legacy IDs, 182 links); scoped `git diff --check` PASS. Initial client seed
validation failed because the added introduction displaced the retained
candidate from the checked header; an explicit candidate.33 reference fixed
the report. Both validation logs are retained. Client evidence commit:
`777e48e97913618df4e16be5eebb1e46a559b32d`.
