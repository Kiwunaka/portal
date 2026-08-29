# WO-013BS — candidate.6 RU-origin environment preflight

## Outcome

Run a bounded read-only preflight against the canonical RU-origin sandbox and
separate access readiness from an actual candidate.6 RU-origin result.

The host is reachable with the owner's retained key and its clock reports NTP
synchronization. The POKROV RU-origin contour is not installed:

| Check | Result |
|---|---:|
| Exact source-bound runner/uploader/support paths | `0/9 installed` |
| Required systemd service/timer units | `0/4 installed` |
| Required environment/key/profile records | `0/4 present` |
| Probe spool | `ABSENT` |
| Runtime mutation | `false` |

The release classification is
`MANUAL_OWNER_TEST_ENVIRONMENT_NOT_INSTALLED`. This is not an access failure,
not a product/runtime failure and not RU-origin PASS.

## Exact identity

| Component | Revision or digest |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.6` / `1.2.0+4046` |
| Operational ID | `62526fdbf0f86c2a7083eb9d2cff4f8645949a31c59032fa593dad9bc68cae05` |
| Platform source | `5713324c1c0c2566befadf527bc09ec0ecf84a4e` |
| Client source | `b2497af7704d0aa6901541e175ce154b0eab05d7` |
| Core source | `a45d69e40ed7d892619a2b5c4592a527f630665e` |
| Release-index source | `8d09ae5e8ec0c8347bcd4e2659944bdf7c9c9db3` |
| Signed manifest | `8aac2458f8c43c0ef2955719dcede44f495d60acf681bc804bd6bf9828ee9054` |
| Signature | `2307906a920fb9b4dcd4c0025bf7628972668905d13897c553ddf27a81592dfa` |
| Receipt | `85dd34504d876086aa8bfe3533ad4db964e4f0a9106f9085657dc08c2c7afcaa` |

The preflight harness is post-candidate read-only tooling at
`b0665b8aa46b15557d57d0f92c8da859fd618375`. It checks the exact candidate
platform revision and does not rebuild or mutate signed candidate bytes.

## Read-only contract

The local canonical RU source/auth/contract/runner/uploader suite passes
`455/455`. The remote command accepts only fixed paths and expected source
hashes. It returns hashes, file modes, systemd state, spool counts and bounded
archive aggregates; it does not return raw configs, profiles, keys, addresses
or host identity. Symlinks fail closed.

The exact remote preflight completed with exit `2`, which is the harness's
expected non-ready outcome. All nine source paths classify `NOT_INSTALLED`.
All four systemd units report `not-found`; the probe and uploader environment,
HMAC key record and profiles are absent. The spool is absent. No runner or
uploader was executed, and no heartbeat/admin readback was attempted.

## Gate F boundary

Gate F is not regenerated because no row moved to PASS. It remains `BLOCKED`
at `4/19 PASS`, `15/19 non-PASS`, `0 FAIL`, with the existing zero validation
errors. `REL_GATE/GATE-F` remains `I3`.

`FRKN_PLAN/W9-02` remains `I1`: current-origin and Brain-origin are separate
PASS results, while RU-origin is now more precisely classified as
`MANUAL_OWNER_TEST_ENVIRONMENT_NOT_INSTALLED`. `FRKN_PLAN/W9-05` also remains
`I1`. No evidence is transferred between origins.

## Required owner-authorized continuation

The next RU step changes the owned server and secret/configuration state, so it
requires explicit owner authorization. It must install the exact runner,
uploader, support modules and four systemd units; provision the environment,
HMAC key record and profiles; then execute a fresh candidate.6 probe/upload and
retain server heartbeat plus admin readback for that same run.

Until that sequence is complete, RU-origin remains non-PASS. The normal
six-hour schedule and stale-result/heartbeat checks cannot be evidenced from an
environment that is not installed.

## Evidence and mutation boundary

Normalized evidence is under
`evidence/013BS-candidate6-ru-origin-environment-preflight/` with SHA-256
`e34d6fc84e29bef7f4722adec4fc4c9cc0df0a2025987977cfbd4cc92961ddf7`.
The external privacy-safe report has SHA-256
`2277a1ac93cae3853c5e7b6f551325ea832d12ef08dd229a2368a50b983121b3`.

No deploy, install, restart, systemd mutation, probe execution, upload,
production mutation, payment action, repository visibility change, tag,
public release, store object or stable pointer occurred. No address, hostname,
SSH alias, credential, key, raw configuration, profile, provider payload or
device serial is retained.

## Verification

```text
python -B -m pytest -q -p no:cacheprovider tests/test_internal_request_auth.py tests/test_ru_probe_contract.py tests/test_ru_probe_service.py tests/test_ru_probe_ingest_api.py tests/test_ru_probe_runner.py tests/test_ru_probe_uploader.py
# 455 passed
python -B -m pytest -q -p no:cacheprovider tests/test_remote_ru_origin_environment_probe.py tests/test_check_script_manifest.py
# 11 passed
python -B -m ruff check scripts/remote_ru_origin_environment_probe.py tests/test_remote_ru_origin_environment_probe.py
python -B -m py_compile scripts/remote_ru_origin_environment_probe.py tests/test_remote_ru_origin_environment_probe.py
python -B scripts/remote_ru_origin_environment_probe.py --source-revision 5713324... --passwords <owner-secret-bundle> --json-out <external-evidence>
# exit 2; MANUAL_OWNER_TEST_ENVIRONMENT_NOT_INSTALLED
```
