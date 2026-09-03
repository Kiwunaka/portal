# WO-013FY — candidate.31 exact-source CLI rebuild and headless VM recheck

Status: `FRESH_EXACT_SOURCE_BUILD_PASS_NOT_SAME_BYTES_VM_IPC_PASS_GATE_UNCHANGED_NO_GO`

Observed: `2026-09-03T19:41:17Z`

Production/public mutation: `NONE`

## Outcome

A fresh headless CLI build from candidate.31's exact client and Core revisions
passes the complete bounded release build and test contour without taking the
owner's screen, mouse or host network. The build produces a valid Windows setup
and manifest, but it does **not** reproduce candidate.31 byte for byte. Eight of
the eleven required runtime files are exact; `pokrov_windows.exe`,
`pokrov_service.exe` and `data/app.so` have equal sizes and exact executable
`.text` sections but different build metadata or non-code sections.

This result is therefore a functional exact-source build PASS without
same-byte reproducibility credit. The fresh setup is retained as diagnostic
evidence only. It is not installed, signed, promoted or assigned a new
candidate number, and it does not replace candidate.31.

The isolated Windows 11 VM separately rechecks the already installed exact
candidate.31 payload. All `11/11` required files still match the signed
candidate, the automatic LocalSystem service remains running, and a probe
compiled from the exact current client source passes `32/32` concurrent IPC
requests. Guest temporary state is removed and the VM ends powered off.

Gate F remains exact `NO_GO 2/17/1` with zero validation errors. This evidence
does not close managed Windows network, physical Android, current/Brain origin,
provider, rollback, approval or final-attestation rows.

## Exact boundary

| Item | Identity |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.31`, app `1.2.0+4053` |
| Operational id | `4ee73886c1a285526baf3b666d5845b426754d8bee9f48365d1550a6ece1dd79` |
| Platform | `84837ce68a028f0c81580a5f1beefddba584de6d` |
| Client | `7e3e771fe36333a75244cbfd828c60beb84c7ff1` |
| Core | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Signed release index | `6de47f0320c9262a5bd2d454f3edb83d557f33a4` |
| Signed manifest | `dd4e99166ac3ec2c566e7d44ee93324f15ae7b3b92df6b35ff35de7053691f9a` |

The build worktree used the exact client and Core revisions above. Its required
platform projection (`shared/` and `scripts/sync_shared_surface_facts.py`) was
proved identical to candidate.31 before the root was supplied explicitly.
The first preflight stopped before artifact creation because a temporary
E:-drive worktree could not autodiscover the platform root; the corrected run
used the proved projection and passed.

## CLI build and tests

| Surface | Result |
|---|---|
| Flutter / Dart | `3.38.5` / `3.10.4` |
| MSVC / Inno Setup | `14.42.34433` / `6` |
| Windows signing | `SKIPPED_BY_OWNER` |
| Seed, cross-repository, hygiene, presentation and performance contracts | `PASS` |
| Flutter analyze | `PASS` |
| Observability contracts / runtime | `3/3` / `29/29 PASS` |
| Diagnostics / support bundle | `6/6` / `15/15 PASS` |
| App shell | `413/413 PASS` |
| Runtime engine | `72 PASS`; one exact-DLL backtest `SKIPPED_BY_ENVIRONMENT` |
| Android / Linux / Windows Flutter | `8/8`, `5/5`, `23/23 PASS` |
| Android Gradle | `BUILD SUCCESSFUL`; 162 tasks |
| Windows native Release CTest | `7/7 PASS` |
| Windows release build | `PASS` |

## Rebuild comparison

| Artifact | Candidate.31 SHA-256 | Fresh SHA-256 | Result |
|---|---|---|---|
| Setup | `a6512bb6bbac328c62497ebad234b97a2794cb178a1949d35362e919f0d6adf0` | `4e685a7f45d31cd67937fcb286d5cb104752c62a0b18733b6f0a06efc4a18062` | different bytes |
| Bundle manifest | `b73b48f584d8d7e436d2801447a3cf0ab0c13eee652a82c9464377c8ab94e6ee` | `cc4a66b60d9acf02e150bd195ed941c967749edb238dd7987374b48bbeb02733` | different bytes |

Required runtime files reproduce `8/11` exactly. The three differences are:

| File | Candidate.31 SHA-256 | Fresh SHA-256 | Code comparison |
|---|---|---|---|
| `pokrov_windows.exe` | `b81bb66887f1e09d8bf2fe58aa07803ae01a2add44d829f43e5f65f0ddde989a` | `9634a784c40621387dd614f01c2d7dcb344eaa7668fd5977666328909f5de861` | same size and exact `.text`; PE timestamp/build metadata differ |
| `pokrov_service.exe` | `f8daab49b259edc7b09bf8277e753a094489c0429fa1d2e64b4cab46fb645871` | `3a1cab3525f00ce665f3bee84c491aa7dbf483d8e0974a67bd7f747e560f4670` | same size and exact `.text`; PE timestamp/build metadata differ |
| `data/app.so` | `a45e1682adb840ec7ba351f18348967ec3fc6d19630f1e621400e362792d5451` | `dace7e2dc07542a036207393810250a6cd7e7ebe3b325c0a1f1b02190d66372a` | same size and exact `.text`; non-code ELF sections/build id differ |

The matching `.text` hashes prove identical executable code sections for this
bounded comparison. They do not establish full artifact reproducibility, so no
same-byte or signed-supply credit is assigned.

## Headless VM recheck

```text
installed candidate.31 files -> 11/11 PASS
POKROVService -> Running / Automatic / LocalSystem
fresh exact-source status probe -> f485d301d7b8e6ea957f5e28dd3a77bfd10fd4b1c071de3168a924fbf135e43b
concurrent authenticated IPC -> 32/32 PASS
screen or host input used -> false
host or guest network mutated -> false
guest tunnel started -> false
guest temporary state removed -> true
final VM state -> poweroff
```

The fresh diagnostic setup was not installed in the VM. The runtime result is
bound to the already installed exact candidate.31 bytes and intentionally kept
separate from the fresh-build comparison.

## Gate and cleanup

```text
decision=NO_GO
required=19
pass=2
non_pass=17
fail=1
validation_errors=0
```

The temporary 5.94 GB client worktree, comparison copy and compiler
intermediates were removed after their resolved paths were checked. About
28.02 MB of diagnostic evidence is retained under
`E:/POKROV-tools/release-evidence/1.2.0-candidate31-cli-recheck-2026-09-03/`.
No production, database, delivery-node, host-network, public-release or stable
pointer mutation occurred.

## Follow-up

Before claiming full client reproducibility, isolate and remove the
nondeterministic PE and ELF metadata for the UI, service and `app.so`, then
repeat this same-byte check. Any source or release-tooling correction must be
merged and built as a newly numbered candidate before receiving release
credit. Independently, continue candidate.31's exact managed Windows and
physical Android matrices without taking over the owner's active desktop.

## Evidence digest

| File | SHA-256 |
|---|---|
| `013FY-candidate31-cli-recheck.json` | `537ef4b247d38fb4867bebe1c91131487532a6f6ba13e3b64a55eaa99c22d26a` |
| external `candidate31-cli-recheck.json` | `cdfb27a88dbcea2b0a823fa135fa3e9c925db36765b9057158a5230b0b4f8cf8` |

The tracked record retains no secret, private key, token, raw connection
material, address or response body.
