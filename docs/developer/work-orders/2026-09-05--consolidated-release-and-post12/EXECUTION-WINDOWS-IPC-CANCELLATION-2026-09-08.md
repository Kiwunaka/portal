# Windows IPC cancellation and UI worker — 2026-09-08

Client `0218e89` implements cancellation of the active connection through an
authenticated IPC session. The target session token and operation nonce fence
stale cancellation; its own nonce, deadline and authorization remain checked.
Status and cancellation can run during Connect, while competing mutations
return `runtime_busy`. Runtime access and rollback keep one execution owner.
A cancellation accepted during final commit still prevents a success response.

The Windows UI moves service calls to a bounded worker and completes Flutter
results on the window thread. New connection/profile/disconnect requests signal
the preceding connect. WinHTTP cancels pending request I/O and retry waits.
UI and service both require Cancellation capability and must be packaged as a
matching pair. Core bytes remain unchanged.

Validation: Debug CTest 12/12 PASS; Windows Flutter 24 PASS; runtime Flutter
80 PASS with one existing exact-DLL test SKIPPED; Windows analyze, Release
UI/service build and client seed/docs PASS. In the isolated NIC-free Win11 VM,
11 component fixtures passed initially; integration passed after supplying its
omitted sibling Debug service EXE. Both receipts are retained. A stale source
counter-name assertion in the first Flutter run was removed; behavioral native
integration and concurrency coverage remain.

Correlated cancellation and synthetic rollback took 31 ms; pending loopback
HTTP headers cancelled in 94 ms, with peer-observed socket closure. All 305
installed hashes stayed unchanged, no fixture processes remained, and the VM
was returned to poweroff. [Source, commands and evidence binding](evidence/windows-ipc-cancellation-2026-09-08.json).

W02/W04/W06 remain partial: installed matching UI/service with live TUN,
blocking Core Start/Stop or recovery interruption, WFP coexistence, Win10 and
final candidate acceptance are OPEN. These fixtures use synthetic Core/recovery
and loopback HTTP. No installed replacement, host VPN change, candidate, push,
merge, deployment or publication occurred. Rollback is a scoped client revert
with matching UI/service packaging; the installed baseline remains retained.

Platform handoff checks: 33 documentation tests PASS, context audit PASS,
package validation PASS (83 R12 IDs, 378 legacy IDs, 290 local links).
Client staged log hashes match the receipt; both scoped diffs pass whitespace
checks. Retained release artifact delta is empty.
