# Windows upgrade and installed AWG31 cancellation — 2026-09-08

Client commit `6fc1e84` handles confirmed session end so Restart Manager can release
files during upgrade. The old v2 package needed manual UI termination; repeated
v3 upgrade shut it down automatically. The installer also removes one exact
obsolete native test EXE. Win11 readback: 305 installed package hashes match,
ordinary-account IPC and LocalSystem SCM PASS, saved state unchanged.

Windows Flutter 24, analyze, Release build, local packaging and client seed/docs
PASS. The initial seed command used a missing default sibling Core path; the
explicit-root rerun passed. Source is parent `0218e89` plus recorded file hashes;
the manifest parent alone does not identify the modified UI. Exact binding and
retained red/green results: [evidence](evidence/windows-upgrade-managed-2026-09-08.json).

The initial automated installer launch triggered Defender
`Behavior:Win32/SuspClickFix.G2`; history is retained. Later interactive installs
completed, with final realtime/behavior protection enabled and zero current
detections on newer signatures. Cause remains unresolved; broad antivirus
compatibility is not marked PASS.

The installed matching UI/service connected with the existing exact-install
AWG31 lab material. Two observations reported running/Core/DNS/egress readiness
and matching staged/effective profile, one TUN, successful health and DNS. The
external egress hash was identical before/during/after connection, so this is
not independent route or origin proof. Full N03 and W01 remain OPEN.

Disconnect took 625 ms. A new connect cancelled after 150 ms returned
`operation_cancelled` in 2110 ms; running/effective protection remained false,
TUN count was zero, and routes/DNS matched the pre-connect baseline. The result
advances W02/W06 within this one installed scenario, without proving arbitrary
blocking Core interruption, sleep/crash, connected update, WFP or Win10.

The temporary exact-install server cohort and expiry were restored with full
original rollout-config hash equality; entitlement and key material were not
changed. Host routes/DNS also match the initial hashes. The disposable clone
retains the lab package/probe, is powered off, and has NIC disabled. Its source
VM remains preserved. No new release candidate, push, merge, deployment or
publication occurred; retained release artifacts remain unchanged. Rollback
of the server test is complete; source rollback is a scoped revert with matched
UI/service packaging. R12 and final release gates remain partial.

Platform handoff: 33 docs-contract tests PASS; context audit PASS; package
validation PASS (83 R12 IDs, 378 legacy IDs, 292 links). `git diff --check` PASS.
Thirty client source/evidence Git blob hashes match their receipt. The only
remaining client dirty files are four pre-existing generated registrants;
platform generated marketing instruction files remain outside this commit.
