# WO-013BU — candidate.6 RU-origin bundle and guarded install PLAN

## Outcome

Turn WO-013BS's read-only environment finding into a deterministic,
candidate-bound installation package and a guarded remote PLAN without changing
the RU host.

The earlier preflight truthfully reported every path it checked as absent, but
its dependency map was incomplete: `scripts/internal_hmac_client.py` also imports
`portal_bot/internal_request_auth.py`. This successor corrects the required set
from nine to ten source/unit members. It does not rewrite the historical report.

## Exact artifact

The builder reads the following payload from exact platform Git objects at
`5713324c1c0c2566befadf527bc09ec0ecf84a4e`, not from the current worktree:

- runner, uploader and three support modules;
- both required `portal_bot` modules, including `internal_request_auth.py`;
- two systemd services and two timers.

| Field | Result |
|---|---:|
| Source/unit members | `10` |
| Bundle size | `47702` bytes |
| Bundle SHA-256 | `e7eb8ec20693f9626d6e7697c7845fa165e77fc1daa7df580ef0618248be345b` |
| Independent repeat | `PASS_BYTE_IDENTICAL` |
| Verification | `PASS` twice |
| Runtime material included | `false` |
| Deployment performed | `false` |

The bundle excludes `probe.env`, `uploader.env`, `hmac.key` and
`profiles.json`. Its manifest binds exact install paths, modes, sizes and member
digests and rejects an incomplete dependency set, a wrong candidate revision,
archive traversal, duplicate members and any tampering.

## Canonical RU-host PLAN

The guarded installer was executed without `--apply` against the canonical RU
sandbox using the owner's retained trusted key:

| Precondition | Result |
|---|---:|
| Authentication | `PASS_KEY` |
| Direct root login | `false` |
| Passwordless bounded privilege | `PASS_SUDO_N` |
| Required tools | `PASS` |
| Existing source/unit/config targets | `0/14` |
| Four systemd units | `inactive / not-found` |
| Runtime user/group | `absent / absent` |
| Probe spool | `absent` |
| Runtime material supplied | `false` |
| Remote mutation | `false` |

The first local invocation against the clean worktree defaults failed closed
because secret inventory material is intentionally not copied into release
worktrees. Repeating with the owner's retained external known-hosts and access
bundle succeeded. No credential, alias, address or host identity was retained.

## Guard and rollback contract

`remote_install_ru_origin_probe.py` separates `PLAN`, `APPLY` and `ROLLBACK`.
APPLY cannot run unless all of the following are true:

1. the bundle SHA, candidate source and node code are confirmed exactly;
2. the four-file local runtime-material set validates without returning values
   or hashes in the report;
3. external mutation, runtime readiness, spool preservation and timer activation
   each receive a distinct literal confirmation;
4. the remote session is root or passes non-interactive `sudo -n`;
5. all 14 fresh-install targets are empty, existing spool is private and all
   units are inactive/not enabled;
6. staged bytes, final source hashes, unit syntax, Python imports, config modes,
   adapter executables and timer state verify before success is reported.

The installer creates a root-only receipt and automatically rolls back on a
post-backup failure. Explicit rollback is bound to the same receipt, bundle,
source and node. It stops/disables the new timers and restores previous files and
timer state but never deletes the spool, `pending`, `blocked`, `quarantine`,
`archive` or manifest-cache evidence. The runtime user/group are retained so a
preserved spool is not orphaned.

## Candidate.6 environment boundary

The candidate.6 unit templates require both env files to exist, but the exact
runner/uploader code uses compiled canonical API/key/host defaults. The guarded
installer therefore permits only matching canonical metadata values; it does
not claim runtime override support. A configurable endpoint/key/host contract
requires a successor candidate with explicit CLI argument wiring.

## Evidence ceiling

`FRKN_PLAN/W9-02` remains `I1` with the stronger status
`CANDIDATE6_CURRENT_BRAIN_PASS_RU_EXACT_INSTALL_PLAN_READY_RUNTIME_MATERIAL_MISSING`.
Current-origin and Brain-origin are still separate PASS evidence. RU-origin is
still `MANUAL_OWNER_TEST_ENVIRONMENT_NOT_INSTALLED`: no files or secrets were
installed, no timer/service ran, and no probe, upload, heartbeat or admin
readback occurred.

Gate F is not regenerated because no required check moved to PASS. It remains
`BLOCKED` at `4/19 PASS`, `15/19 non-PASS`, `0 FAIL`. Candidate bytes, signed
manifest, public assets, stable pointer and store state are unchanged.

## Required owner-authorized continuation

The next RU step is an external mutation and still requires explicit owner
authorization:

1. create the exact four-file runtime-material directory outside Git;
2. verify that every declared adapter executable already exists on the RU host;
3. run guarded APPLY with every exact confirmation and retain the private receipt;
4. execute one manual runner, then one uploader;
5. bind the same run through heartbeat and authenticated admin readback;
6. observe the next scheduled run and execute receipt-bound rollback on any
   failed post-start check.

Only that complete sequence can advance RU-origin. PLAN readiness cannot.

## Evidence and mutation boundary

Normalized evidence is under
`evidence/013BU-candidate6-ru-origin-bundle-and-install-plan/` with SHA-256
`63a4d7f52311bd3a4b740be87a8273fa6a0b593ea7ebda29b4bf4eeb5a98c0e5`.
The external sanitized PLAN report has SHA-256
`c10c19bb00c6b81028b42bae253cdee0638d794e984a162ac635c9996c96bb69`.

No server file, user, group, unit, timer, spool, database or runtime state was
changed. No raw host, address, SSH alias, credential, key, config/profile value,
provider payload or device identity is retained. No tag, public release, store
object or stable pointer changed.

## Verification

```text
python -B -m pytest -p no:cacheprovider tests/test_internal_request_auth.py tests/test_ru_probe_contract.py tests/test_ru_probe_service.py tests/test_ru_probe_ingest_api.py tests/test_ru_probe_runner.py tests/test_ru_probe_uploader.py -q
# 455 passed
python -B -m pytest -p no:cacheprovider tests/test_remote_install_ru_origin_probe.py tests/test_build_ru_origin_probe_bundle.py tests/test_remote_ru_origin_environment_probe.py tests/test_check_script_manifest.py tests/test_release_1_2_candidate_preflight.py -q
# 49 passed
python -m ruff check scripts/remote_install_ru_origin_probe.py tests/test_remote_install_ru_origin_probe.py scripts/build_ru_origin_probe_bundle.py scripts/remote_ru_origin_environment_probe.py
python -m py_compile scripts/remote_install_ru_origin_probe.py tests/test_remote_install_ru_origin_probe.py scripts/build_ru_origin_probe_bundle.py scripts/remote_ru_origin_environment_probe.py
python -B scripts/build_ru_origin_probe_bundle.py build --source-revision 5713324... --output <external-bundle-a>
python -B scripts/build_ru_origin_probe_bundle.py build --source-revision 5713324... --output <external-bundle-b>
python -B scripts/build_ru_origin_probe_bundle.py verify --bundle <external-bundle-a>
python -B scripts/remote_install_ru_origin_probe.py --bundle <external-bundle-a> --operation install --known-hosts <owner-known-hosts> --passwords <owner-secret-bundle> --json-out <external-report>
# PLAN only; privileged=true; installed_target_count=0; mutation_performed=false
```
