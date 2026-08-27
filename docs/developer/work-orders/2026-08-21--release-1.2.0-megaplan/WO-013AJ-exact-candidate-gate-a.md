# WO-013AJ — Exact candidate.3 Gate A baseline

Status: `BASELINED_EXACT_CANDIDATE_BLOCKED_I1`
Classification: `ACTIVE_EXECUTION_EVIDENCE`
Phase: `01`, decision replay in Phase `11`
Row: `REL_GATE/GATE-A`
Candidate: `pokrov-1.2.0-candidate.3`
Production/external mutation: `NOT_AUTHORIZED`

## Outcome

Turn Gate A from an unexamined aggregate into one exact-candidate decision
without manufacturing a pass. The source plan defines six requirements:
branches/CI, payment fallback, one manifest, version/contracts validation,
Windows clean-host proof, and release signing/provenance.

Four requirements are proved or covered by the explicit owner-solo promotion
control. Two remain non-PASS: the live Windows network/recovery matrix and
public/stable Windows signing. Gate A therefore returns `BLOCKED` and advances
only from `I0` to baseline `I1`.

## Exact source and source-plan proof

The audit uses clean detached worktrees for the signed source tuple:

- platform `eafaca3e64c0619dea7f58fc9c430682b4520559`;
- client `ac22825e857a313c9e4eba61030eb548d6346ead`;
- Core `344b317a7a09eca7943a93866b193553538bd8f6`;
- release index `6a1afa95fe52da2d559ba7b1da88715cd0344bb2`.

The retained manifest/signature/receipt hashes remain `a2752b6a...`,
`926f0b46...` and `fb4d0d5d...`; Ed25519 verification uses active key
`pokrov-release-2026-01`.

## Gate A requirement result

| Requirement | Result | Exact boundary |
|---|---|---|
| Branches and CI | `PASS_WITH_OWNER_SOLO_EXCEPTION_AND_FAIL_FIRST_RECONCILIATION` | All seven STOP-SHIP source anchors pass; exact historical owner-solo PR controls pass `3/3`; Core branch protection is live; private platform/client protection APIs remain plan-blocked. Candidate Core exact aggregate retains the LFS-control failure while four product jobs and the product-identical corrected five-job control pass. Current replacement PRs are billing-blocked and are not credited. |
| Payment fallback | `PASS` | Exact platform tests prove one parser and no synthesized zero-amount fallback; FreeKassa remains disabled. |
| Single manifest | `PASS` | One signed release-index manifest binds the exact source tuple and six artifacts. |
| Version/contracts | `PASS` | Exact-source focused suite passes `103` tests plus `21` subtests; cross-repository client/Core contract passes. |
| Windows clean-host | `MANUAL_OWNER_TEST` | Install, LocalSystem service, authenticated IPC, restart, clean uninstall and idle route/DNS restoration pass. Live TUN, connected DNS, authenticated egress and connected rollback/recovery remain unrun. |
| Signing/provenance | `SKIPPED_BY_OWNER` | Manifest, Android certificate, SBOM and provenance pass. Windows remains unsigned only under the owner's direct-beta/SmartScreen exception and cannot prove public/stable signing. |

## STOP-SHIP replay

The existing read-only verifier runs against the exact source worktrees and the
retained owner-solo PR controls:

- local permanent regressions: `PASS 7/7`;
- owner-solo PR controls: `PASS 3/3`, all required checks bound to GitHub
  Actions App `15368`;
- reviewer controls: explicit `OWNER_SOLO_EXCEPTION 3/3`, independent review
  not invented;
- Core live branch protection: `PASS`;
- platform/client private branch protection API: GitHub plan `403`, compensated
  only by the exact PR controls allowed by the owner-solo contract;
- Windows live manual gate: `NOT_RUN`;
- aggregate: expected `BLOCKED`.

The exact candidate Core push aggregate remains a truthful historical failure:
its old workflow omitted Git LFS for the private client checkout. The four
product/security/reproducibility jobs passed. A workflow-only, product-identical
correction later passed all five jobs. This is retained as fail-first evidence,
not rewritten into an exact-source green aggregate.

## Evidence digests

| File | SHA-256 |
|---|---|
| `013AJ-owner-solo-pr-input.json` | `2bab756b5d17f17a61f2de30e8b95b1ad5a43c4555b06acd2e9d7681ff2e1604` |
| `013AJ-stop-ship-exact-source.json` | `d06df26ac9d2ddb20d9e2442cf7748ff0afda3014f94aeea9778f894c22622b1` |
| `013AJ-gate-a-decision.json` | `f4441a19521d1d77703f599c1257f620fb048167c3db9ff3a24f2935694f2d01` |
| Current execution ledger | `de901f7a26348e09132f83ff35175715bc460ef70c7922f62f0e99b1d5477fbc` |
| Rehashed Gate F decision | `3eb6b06dfd345c7df1ef4d5f09cfd354e22e2efeec13abc674930800037c631b` |

## Verification

- exact platform payment/release/manifest suite: `103 passed`, `21 subtests`;
- exact client/Core release contract: `PASS`;
- STOP-SHIP command with `--expect-nonpass`: exit `0`, result `BLOCKED`;
- Gate F replay: exit `0` only with `--expect-blocked`, result remains
  `5 PASS / 14 non-PASS / 0 FAIL / 0 validation errors`;
- release/preflight/STOP-SHIP/docs contract suite: `71 passed`;
- platform context audit and upstream-evidence hash audit: `PASS`;
- exact source worktrees: clean;
- no payment, branch setting, signing key, live Windows network, deploy,
  public asset, stable pointer or Gate G mutation.

## Ledger decision

`REL_GATE/GATE-A` advances `I0 -> I1` as
`BASELINED_EXACT_CANDIDATE_BLOCKED`. It does not reach `I3` or candidate proof:
an aggregate gate is not locally verified while required manual/signing results
remain non-PASS.

Distribution becomes `I4=4`, `I3=312`, `I2=19`, `I1=41`, `I0=1`; `316` rows
remain at or above `I3`, `61` remain below and pending stage split stays
`pre_freeze=0`, `candidate=28`, `external=14`, `deferred=19`.

## Next action

Run the exact-candidate Windows live TUN/DNS/egress/connected rollback matrix
only after the owner explicitly authorizes the interactive/UAC work. Keep the
unsigned Windows direct-beta exception non-PASS for public/stable signing.
Restore GitHub Actions billing before merging current PRs or constructing a
replacement candidate. Rerun Gate A after any exact candidate change.
