# WO-013BF — Active resolver-corrected Windows setup

## Outcome

Package the exact current Windows runtime after WO-013BE without installing it
on the non-isolated build host or converting packaging into live-network proof.

Clean client `f500728...` synchronized exact Core `a45d69e...` and built
unsigned outside-store setup `1.2.0+4046`. Its eight required files match the
generated manifest, and bundled `pokrov-core.dll` matches the two-build
reproducible Core artifact exactly. This closes the active-source setup gap.

It does not close Windows SCM/service/TUN/DNS/AWG/egress, recovery, uninstall,
SmartScreen, candidate or promotion gates.

## Exact artifact contract

| Item | Exact identity | Result |
|---|---|---|
| Platform | `1bb7b75e76ca6c88485cdef63222c5d53ef34f0e` | clean current release ledger owner |
| Client | `f500728ce1fef54a32573263999652383cd86ad2` | clean setup source |
| Core | `a45d69e40ed7d892619a2b5c4592a527f630665e` | exact synchronized DLL source |
| Setup | `28932687` bytes; `81268d7e…723c` | build and retained-copy readback PASS |
| Manifest | `d2a7a900…4805` | eight required files, zero mismatch |
| Bundle tree | `26e2e63b…fbf7` | retained pre-candidate bundle |
| Core DLL | `55426048` bytes; `53b5e82a…4652` | exact reproducible Core artifact |

Seed, product-facts, version, observability, source-logging, release-handoff,
rollback-catalog, repository-hygiene, presentation, performance and docs
contracts pass before compilation. Analyze/tests are the existing exact clean
`15/15` aggregate for this source tuple; they were not rerun and relabelled.

## Signing and runtime boundary

The owner-approved `1.2.0` direct-beta exception remains exact:

- setup, UI and service are Authenticode `NotSigned`;
- manifest status is `SKIPPED_BY_OWNER` with blocker
  `OWNER_ACCEPTED_UNSIGNED_WINDOWS_BETA_1_2_0`;
- the SmartScreen/unknown-publisher warning is mandatory;
- no trusted, signed, Store or broad-stable claim is allowed.

Public verification keys were recovered only as exact pinned build inputs and
redacted from command output. No private signing key was used or retained.

The host exposes no available Windows Sandbox, Hyper-V module, VirtualBox or
QEMU runtime in this session. The setup was therefore not installed, the main
host network was not mutated and live Windows parity remains
`MANUAL_OWNER_TEST`.

## Release interpretation

- Phase 10 remains `I3`; packaging is not platform-runtime proof.
- Candidate.5 remains immutable and rejected.
- No replacement candidate, Gate F rerun, tag, upload, publication or stable
  promotion occurred.
- The next Windows action is exact setup install plus SCM/UI/TUN/DNS/AWG2/
  AWG3.1/egress/leak/recovery/uninstall in an isolated Windows host.

Machine evidence:
`evidence/013BF-windows-resolver-setup/013BF-windows-resolver-setup.json`.
