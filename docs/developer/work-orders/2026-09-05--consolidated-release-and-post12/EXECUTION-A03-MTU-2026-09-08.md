# A03 — owned Pi client-MTU matrix, 2026-09-08

PASS_BOUNDED for six live cases against the two separate owned AWG labs.
Core test commit `a57462e` differs from runtime `8dc57a8` only in the interop
test and release documentation; shipped DLL/AAR bytes were not rebuilt.
[Evidence](evidence/awg-mtu-pi-2026-09-08.json) binds source, tools, material and
test binaries. Registered Pi 4/aarch64 and direct-default-route preflight passed;
no independent geographic or whole-client RU-origin claim follows from that.

| Profile | Client MTU | TX/RX packets | Largest TX/RX UDP payload, bytes | Elapsed, ms |
| --- | ---: | --- | --- | ---: |
| AWG3.1 | 1280 | 22 / 12 | 1300 / 1328 | 1226 |
| AWG3.1 | 1400 | 22 / 15 | 1420 / 1328 | 1198 |
| AWG3.1 | 1408 | 22 / 15 | 1300 / 1328 | 1200 |
| AWG2 | 1280 | 19 / 13 | 1296 / 1312 | 248 |
| AWG2 | 1400 | 19 / 14 | 1296 / 1312 | 186 |
| AWG2 | 1408 | 20 / 15 | 1296 / 1312 | 187 |

Each case changes only its in-memory client MTU, creates a separate userspace
device, completes TLS and checks the authenticated HTTP egress marker. The
request has 4096 bytes of inert header padding to span multiple inner packets.
The table measures this short request; it does not establish throughput,
energy, optimal presets, server MTU or a full outer-path MTU limit. Maximum
UDP payload is not the inner MTU and excludes outer IP/UDP headers.

The platform runner now emits v4 receipts with these safe measurements and
requires all three named subtest PASS markers plus nonzero TX/RX. A new negative
regression first showed missing/skipped MTU, zero packets and duplicate results
accepted under the earlier single-smoke oracle. The corrected collector rejects
these. Older v3 receipts retain their original single-configuration scope.

Commands: `go1.26.8 test -count=1 ./protocol/awg ./transport/awg` from the Core
embedded module PASS; operator-only test skips when material is absent.
Platform `python -B -m pytest -p no:cacheprovider tests/test_owned_awg_ops_gap.py
tests/test_release_gate_check.py tests/test_release_orchestrator.py
tests/test_check_script_manifest.py -q` — 76 tests / 33 subtests PASS.
For each profile, `remote_run_owned_awg_core_interop.py` used Core `a57462e`,
explicit Git/Go1.26.8/SSH/SCP paths, the already trusted combined host file,
confirmed `shrek` alias, exact-commit snapshot, and local temp root
`E:/r12-awg-mtu-20260908`. Endpoint material stayed in memory/SSH stdin.
The first invocation stopped before building or retrieving material because
the feature worktree lacked the default credential file; the corrected command
used the existing owner credential path explicitly.

Both receipts confirm temporary remote cleanup. No server configuration,
interface, route, entitlement, endpoint key or release artifact changed.
No server trust bypass, push, merge, deployment, publication or new candidate.

A02 server image/parameter/HP/peer readback and A03 cross-field H/S/timing/wire
bounds remain open. This result closes the six client-MTU smoke cases only.
