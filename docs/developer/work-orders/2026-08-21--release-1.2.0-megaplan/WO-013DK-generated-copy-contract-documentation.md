# WO-013DK — Generated copy-contract documentation

Status: `PASS_I3_CURRENT_SUCCESSOR_SOURCE`

Observed: `2026-08-31T19:59:29Z`

## Scope

Close the local `FE/P12-210` gap without creating another product, commercial
or copy authority. Extend the existing platform-owned product-facts
synchronizer so the active client pins the copy catalog and marketing
governance beside product, public-URL, tariff and commercial digests. Generate
one read-only client reference that explains every copy namespace and the
active-client `app.*` baseline.

This work does not bulk-import platform copy into the app, change runtime UI
text, calculate prices or eligibility on the client, approve legal/advertising
state, rebuild candidate.16, deploy or publish.

## Exact boundary

| Item | Value |
|---|---|
| Signed candidate | `pokrov-1.2.0-candidate.16`, unchanged |
| Candidate platform/client/Core | `719e23d...` / `75ba7e7...` / `cd8f0f4...` |
| Successor platform implementation | `f8a3b3369a16b37494f910a31ac39fcf5ba70ab4` |
| Successor client PR | `Kiwunaka/POKROV-app#48` |
| Successor client head | `0429213e846ab06261fd5a489a5ffc8f78f3128c` |
| Client `main` merge | `9b52d6a7d461fcebe4c2225dfe5655f6cc8aa02d` |

The canonical owners remain in the platform repository. The generated client
document is evidence of their mapping and current digests; editing it cannot
change product, price, claim, campaign or launch state.

## Implemented contract

- `config/product-contract.seed.json` now pins copy-catalog path, version and
  SHA-256 plus marketing-governance path, revision and contract SHA-256.
- `docs/generated/platform-copy-contract.md` is emitted by the existing
  platform synchronizer and checked byte-for-byte in read-only mode.
- The reference covers all seven current namespaces: `admin`, `app`, `bot`,
  `cabinet`, `marketing`, `retention` and `webapp`.
- The ten `app.*` entries are shown as reconciliation baselines. They are not a
  bulk runtime import and do not replace state-specific client wording.
- Product facts and public URLs remain safe generated runtime inputs. Prices,
  promo results, account state and payment outcomes remain server authority.
- Marketing governance remains public-acquisition policy. Its generated
  presence does not approve client wording or unblock a campaign.
- The synchronizer fails before generation when the marketing-governance
  copy-catalog digest does not match the current catalog.

The generated document SHA-256 is
`f9b53041831a94ffff548e2e875eab3d4c38e9b8c70aff75d4b235c94cfe17eb`.
The updated client seed SHA-256 is
`b24aecf994a7207d7af32a244ac18cc9e68213720f5e32595e12e32e3124461e`.

## Verification

- platform shared-facts, commercial, frontend-text, public-copy and marketing
  governance matrix: `41/41 PASS`;
- platform documentation/context contracts: `32/32 PASS`;
- candidate-preflight contract: `24/24 PASS`;
- platform context audit and link check: `PASS`;
- exact cross-repository generator `--check` against active client `main`:
  `PASS_READ_ONLY`;
- full client `validate-seed.ps1` against clean exact Core `cd8f0f4...`:
  `PASS`;
- client documentation contract: `PASS`;
- scoped Ruff and Git diff checks: `PASS`.

Client GitHub run `33433077192`, job `99622895055`, failed before runner
execution with `steps=[]`. It is recorded as
`HOSTED_CHECK_BLOCKED_BY_BILLING`; PR 48 merged under the authorized
`OWNER_SOLO_EXCEPTION`, not as a hosted PASS.

## Completion-index effect

`FE/P12-210` advances `I2 -> I3`. The current successor source now has a
deterministic generated authority map, source digests, complete namespace
coverage, active-client baseline and read-only drift rejection.

The 378-row distribution becomes `I4=5`, `I3=319`, `I2=20`, `I1=34`,
`I0=0`.

No commercial, marketing, client runtime, release-candidate or Gate F/G row
advances from documentation consistency.

## Evidence and ceiling

- normalized evidence:
  `evidence/013DK-generated-copy-contract/013DK-generated-copy-contract.json`;
- normalized evidence SHA-256:
  `d1c286714bafb33de769f1b47741f4a82c7f53cde804a72a8e10a8d5695cb732`.

The evidence ceiling is `I3` for current successor source. It proves local
generation, ownership and drift rejection. It does not prove deployed copy,
public URL availability, legal or campaign approval, provider prices, signing,
store publication, candidate.16 contents or release promotion.

## Next action

Keep the generator in the next exact-candidate preflight. Regenerate only from
platform owner changes. Do not hand-edit the client projection or treat it as
commercial, legal or release evidence.
