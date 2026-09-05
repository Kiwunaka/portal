# N02 — interrupted Windows recovery completion

Local implementation on 2026-09-05; client commit `20b997afb9fbad6d77d9d278c06c9ae0dcc6d3a8`.
Parent N02 remains **PARTIALLY_FIXED**, release **BLOCKED**.

The durable network journal could reach `recovered` before a service restart or
final write failure. Its retry branch wrote `clean` while retaining the network
snapshot. The next loader rejected that journal and blocked another transaction.
Both normal completion and recovery retry now use the same final atomic write:
clear the snapshot for `clean`, preserve `recovered` and its snapshot on failure.

The regression uses a synthetic backend, a real temporary journal, restart at
`recovered` and a file lock that rejects replacement. Before the fix it failed
both reload checks; after the fix it passes and allows the next transaction.
Source changes: `service_recovery.cpp`, `service_runtime_test.cpp`; canonical
owner: client `docs/architecture/platform-privilege-runtime-contract.md`.

## Verification

Exact commands, results and retained log hashes:
[evidence/n02-recovered-journal.json](evidence/n02-recovered-journal.json).
CMake/CTest use the Visual Studio 2022 BuildTools bundled binaries.

- Native focused regression: expected FAIL before fix, PASS after fix.
- Affected native targets rebuilt; Debug CTest: 9/9 PASS.
- Runtime Flutter profile-mismatch regression: 1 PASS; analyze: no issues.
- Client validate-seed with current Core/platform worktrees: PASS.
- git diff --check: PASS; artifacts/releases delta: empty.
- Platform package validator: 13 imported hashes, 83 R12 IDs, 378 retained
  legacy IDs, 128 links PASS; documentation/context tests: 33 PASS;
  `python -B scripts/agent_context_packet_audit.py --platform-context-root .`: PASS.
- Initial Flutter invocation used a nonexistent filename and did not run tests;
  it is retained as NOT_RUN, followed by the corrected successful invocation.

## Remaining decision and proof

This corrects the network journal, not durable profile last-known-good storage.
The current bootstrap owner requires a fresh managed profile after dataplane
failure. `RuntimeProfileSource`/managed manifest supplies revision, but no grant
authorizing restoration of an older revision. Owner was asked to choose fresh
server confirmation (remain disconnected on outage) or a new signed offline
rollback authority. That decision is pending; no fallback permission was invented.

Exact packaged VM/reboot and physical-device proof remain MANUAL_OWNER_TEST.
The existing O03 data-source question and candidate/provider/origin gates in
[HANDOFF.md](HANDOFF.md) remain open. No push, merge, deployment or new candidate.
Rollback: revert this scoped client commit; retained historical artifacts stay
unchanged. Concurrent generated registrant deltas remain outside the commit.
