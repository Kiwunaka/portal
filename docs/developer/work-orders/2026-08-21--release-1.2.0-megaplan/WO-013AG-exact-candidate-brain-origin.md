# WO-013AG — Exact candidate.3 Brain-origin source and control-plane evidence

Status: `EXACT_CANDIDATE_PLATFORM_SOURCE_AND_BRAIN_CONTROL_PLANE_PASS`
Phase: `11`
Candidate: `pokrov-1.2.0-candidate.3`
Rows: `FRKN_PLAN/W9-02`
Deployment: `NOT_REQUIRED_NOT_RUN`
Recorded: `2026-08-27`

## Goal

Answer whether the production Brain backend is stale and retain a repeatable,
secret-free Brain-origin result for the exact signed candidate platform source
without deploying, restarting services, changing routes, granting entitlement
or touching the stable/public release surface.

The owner removed the physical phone and directed Android work to LDPlayer
only. This work therefore uses no physical-device evidence. The exact
candidate APK remains installed on `emulator-5554`, but its retained account
has no active access, so catalog, TUN, DNS and authenticated egress remain
`BLOCKED_BY_ACCESS` rather than being inferred from server checks.

## Exact candidate binding

| Component | Exact source |
|---|---|
| Platform | `eafaca3e64c0619dea7f58fc9c430682b4520559` |
| Client | `ac22825e857a313c9e4eba61030eb548d6346ead` |
| Core | `344b317a7a09eca7943a93866b193553538bd8f6` |
| Release index | `6a1afa95fe52da2d559ba7b1da88715cd0344bb2` |

Manifest/signature/receipt SHA-256 remain `a2752b6a3b95faacf13a68edb708c560966a0f5eb8727e109d7f1603fdc81090`,
`926f0b4667a58ba9cc5ace5c4e6c3c8129d1ec3d4d449b3f0831a8c527cd7121`
and `fb4d0d5dd272b8d3e7ea2303e2ffa93e332f54ac3e92f245400decc6c06e4b53`.
WO-013AE remains the signed-candidate identity authority; this work order adds
Brain-origin runtime evidence and does not replace the manifest.

The deploy payload under current platform `master` is unchanged from signed
candidate source `eafaca3...`: tracked `portal_bot/`, `shared/`,
`copy/catalog.ru.json` and the four explicit probe helpers have no source
delta. Post-candidate evidence tooling is outside the deployed payload.

## Read-only runtime-source control

`scripts/remote_brain_runtime_source_probe.py` uses the exact payload selector
owned by `remote_deploy_brain_portal_code.py`. For every selected path it reads
the candidate Git blob with `git show` and the live Brain file through SFTP.
It never uploads or retains remote contents. Its artifact contains only
counts, safe tracked paths for failures, the exact source revision and a
bounded verdict.

Raw working-tree comparison is not an identity authority on Windows because
checkout and upload boundaries may use CRLF. The probe therefore records raw
identity separately and permits exactly one semantic normalization:
`CRLF_TO_LF_ONLY`. Lone CR, missing data, an unreadable file or any other byte
difference fails closed.

Focused local tests cover exact commit validation, Git-blob loading, exact and
CRLF-only comparison, fail-closed content mismatch, secret-free output and the
existing deploy/network-probe contracts.

## Brain-origin result

| Slice | Result | Exact observation | Retained SHA-256 |
|---|---|---|---|
| Brain readiness | `PASS` | `23/23`, zero failures, required units/listeners/endpoints and `5/5` subscription-stability samples | `980f2e62222f85e54aae6c76deddf3fa0b6081aad444e4724c5c60891b964404` |
| Live enabled delivery TCP | `PASS` | `7/7` configured endpoints open: `de`, `it`, `nl`, `pl`, `ru`, `ru_spb`, `us` | `15732fcbf4b40e43722c98af4fe3d6b1665ae6f0ed3d32cac9efed3d0e18c246` |
| Exact runtime source | `PASS` | `193/193` candidate Git blobs match; `4` raw exact, `189` CRLF-only, `0` semantic mismatches | `27bba27b529e065b4770467c519e4072d13e0c06ace0382eaac4b2ef40ad8b77` |

This proves that the live Brain backend deploy payload is semantically the
exact signed candidate.3 platform source and is healthy at the control-plane
and Brain-to-enabled-node TCP layers. The server is not running an older
backend payload. No backend deployment or restart is required.

It does **not** prove authenticated client egress, LDPlayer catalog/TUN/DNS,
current-origin aggregate behavior, RU-origin reachability, payment-provider
E2E, Operator OIDC/RBAC, physical-device behavior, public release assets or a
stable pointer. `ru_spb:443 open` is a Brain-origin TCP result for the normal
enabled delivery row, not proof of Beeline mobile reachability and not a
reactivation of the disabled stale type-3 bridge identity from WO-013AD.

## Mutation and ledger decision

No deploy, service restart, route/pointer change, entitlement grant, payment
action, public asset publication or stable promotion occurred.

No ledger row advances. `FRKN_PLAN/W9-02` remains `I1` with stronger exact
candidate Brain-origin evidence because exact current-origin aggregate and a
separately authorized RU-origin result are still absent. Distribution remains
`I4=4`, `I3=308`, `I2=15`, `I1=38`, `I0=12`; `312` rows are at or above `I3`,
`65` remain below, and the pending stage split remains `0/30/14/21`.

## Verification

```text
python -B -m pytest -p no:cacheprovider tests/test_remote_brain_runtime_source_probe.py tests/test_remote_deploy_brain_portal_code.py tests/test_remote_brain_network_probe.py -q
17 passed, 9 subtests passed

python scripts/remote_brain_runtime_source_probe.py --brain-ip <brain> --source-revision eafaca3e64c0619dea7f58fc9c430682b4520559 --passwords <owner-secret-location> --json-out <ops-local-artifact>
PASS 193/193 semantic byte matches; normalization=CRLF_TO_LF_ONLY
```

The owner-secret path was supplied locally and is neither printed nor retained
in evidence.

## Retained evidence

- `evidence/013AG-exact-candidate-brain-origin/013AG-brain-readiness.json`
- `evidence/013AG-exact-candidate-brain-origin/013AG-brain-live-enabled-nodes.json`
- `evidence/013AG-exact-candidate-brain-origin/013AG-brain-runtime-source.json`
- `evidence/013AG-exact-candidate-brain-origin/013AG-exact-candidate-brain-origin.json`

## Next action

Continue LDPlayer-only testing. Obtain an explicit, valid owned entitlement
before catalog/TUN/DNS/egress checks; do not wipe the login or silently grant
commercial access. Separately retain the exact current-origin aggregate and
an authorized RU-origin run, then execute the Windows live
TUN/DNS/egress/connected-rollback matrix. Public `v1.2.0` and stable promotion
remain prohibited.
