# WO-013EU — candidate.21 hosted checks and Gate F refresh

Status: `EXACT_CANDIDATE21_HOSTED_CHECKS_PASS_GATE_F_BLOCKED_5_PASS_14_NON_PASS_0_FAIL`
Classification: `ACTIVE_EXECUTION_EVIDENCE`
Phase: `11`
Candidate: `pokrov-1.2.0-candidate.21`
Production/external mutation: `NONE`

## Outcome

Read the GitHub check runs attached to each of the four exact source SHAs in
the signed candidate.21 manifest. All `10/10` attached GitHub Actions jobs are
completed `success`: platform `2/2`, client `1/1`, Core `5/5` and release-index
`2/2`. A second live API readback matches every retained job ID, check name,
head SHA, status, conclusion and GitHub Actions app.

Refresh the immutable WO-013ET Gate F input with only
`hosted_required_checks: PASS`. Signed-candidate validation, all `19/19`
evidence pointers and all `13` upstream hashes pass. Gate F remains `BLOCKED`,
advancing from `4/15/0` to `5 PASS / 14 non-PASS / 0 FAIL` with zero validation
errors. Gate G and publication remain unauthorized.

## Exact hosted checks

| Repository / exact SHA | Check runs | Result |
|---|---|---|
| `Kiwunaka/portal` / `e2608130...` | `cross-repository-contract` run `33575453809`; `repo-guardrails` run `33575453765` | `2/2 success` |
| `Kiwunaka/POKROV-app` / `1e164586...` | `cross-repository-contract` run `33576468801` | `1/1 success` |
| `Kiwunaka/pokrov-core` / `cd8f0f4...` | `test`, Apple source build, Windows/Android reproducibility and release contract in run `33303561763` | `5/5 success` |
| `Kiwunaka/pokrov` / `cae911e...` | `source-contract` run `33586728089`; `prepare-signed-candidate` run `33586752995` | `2/2 success` |

The query is read-only. It dispatches and reruns nothing. Hosted execution does
not imply branch enforcement: the owner-declined paid branch-protection path
remains `SKIPPED_BY_OWNER`, and `independent_review_performed=false` remains
explicit under `OWNER_SOLO_EXCEPTION`.

## Gate F result

```text
BLOCKED
required=19
pass=5
non_pass=14
fail=0
validation_errors=0
candidate_validation=PASS
hosted_required_checks=PASS
gate_g_authorized=false
```

The five PASS rows are signed supply/SBOM/provenance, release docs to manifest,
current-origin public API budgets, Brain exact-source readiness/delivery and
exact-SHA hosted checks. The remaining fourteen rows keep their WO-013ET
statuses and evidence boundaries.

## Evidence digests

| File | SHA-256 |
|---|---|
| `013EU-candidate21-hosted-checks.json` | `4234e46f3dfbe3da4df58789a3e6c591a405b328c3d761de9edabf953b5df427` |
| `013EU-candidate21-gate-f-evidence.json` | `4f83e1f24d0f6148f80773a188dc10f9b7990a125652161a3c9aa4e382d8f2e9` |
| `013EU-candidate21-gate-f-input.json` | `50e6a312cf6a2547305621168f6de75b87ebbd33954786a2218d49da84efa1ee` |
| `013EU-candidate21-gate-f-decision.json` | `988f86369490b137160742ad3ff877bae98fcc3a4f48ca76f377455ad0a6afb0` |

The aggregate evidence pins the new hosted-check record plus the same exact
candidate.21 signed binding and eleven source/runtime records used by WO-013ET.
All JSON files are LF-pinned for portable digests.

## Verification

```text
live GitHub API evidence readback -> PASS 10/10 exact job IDs/names/head SHAs/status/conclusion/app
Gate F -> expected BLOCKED exit 0 with --expect-blocked; 5/14/0; validation_errors=0
all four retained JSON records -> PASS parse
```

## Completion index and next boundary

`REL_GATE/GATE-F` stays `I3` and advances from exact candidate.21
`BLOCKED 4/15/0` to `BLOCKED 5/14/0`. The `378`-row distribution remains
`I4=7`, `I3=320`, `I2=19`, `I1=32`, `I0=0`; no row changes level.

The next technically available Windows recovery step still requires one
owner UAC confirmation inside the VM: the background account is verified as a
medium-integrity non-admin token, and the test controller correctly refuses to
trust its Downloads path. Android, general RU execution, provider, Operator,
legal/commercial, runtime rollback, comparable performance and final live
attestations remain separate work.

No workflow, runtime, candidate byte, VM network, phone, emulator, server,
DNS, provider, database, credential, branch policy, tag, GitHub Release, Store
object or stable pointer is changed by this work order.
