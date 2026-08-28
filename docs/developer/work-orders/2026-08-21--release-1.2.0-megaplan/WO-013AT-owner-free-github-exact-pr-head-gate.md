# WO-013AT — Owner-free GitHub policy and exact PR-head local gate

Date: 2026-08-28

## Objective

Retain the sole owner's decision to continue the 1.2.0 release without a paid
GitHub plan or private-repository branch protection, bind the strongest current
local aggregate to the exact open-PR product sources, and keep hosted, candidate
and publication claims honest.

## Owner decision

The sole owner declined paid GitHub features. Private platform/client branch
protection is therefore waived under the existing `OWNER_SOLO_EXCEPTION`.
Independent review is unavailable and is not claimed.

This decision does not waive named release checks. The platform and client
remain private in this slice, and their hosted jobs remain
`BLOCKED_BY_ACCESS_GITHUB_BILLING`. The owner's stated future intent to make the
repositories public is retained as a separate open-source publication lane. No
visibility mutation occurs until a repository-history, secret, generated
artifact and public-contract audit proves that publication is safe.

The canonical open-source rollout plan is amended to cover eventual
client/Core/platform publication without paid GitHub features. It retains a
client-first order and requires a clean public successor when a current
repository's private history cannot be proven safe without destructive
rewriting.

## Initial publication preflight

A bounded no-mutation current-tree and reachable-history scan was run across
platform, client and Core. High-confidence token/private-key patterns resolve
only to redaction detectors, synthetic tests or key parsers: eight platform
files, one client test and one Core parser. The sole tracked platform env file
is `.env.example`; credential-bearing keys are empty or placeholder-valued.
The Core risky-name set is limited to public/test certificate fixtures and
credential implementation paths already present in the public Core repository.

This is an initial preflight, not publication approval. Neither `gitleaks` nor
`trufflehog` is installed on the host, and dependency licenses, generated-asset
rights, historical low-entropy credentials, private operational facts and a
clean public clone are still unaudited. Platform and client visibility
therefore remain unchanged.

## Exact source and carrier identities

The current local aggregate uses these clean worktrees:

- platform PR 58 input/carrier:
  `663890b564e7d25aaa334cf5b66952f9335ba358`;
- platform frozen product source:
  `e6ae46e33b74029ec30626a216cd947c8c131ba3`;
- client PR 33 source:
  `3564023c8d0e66977043332f2772cfd512489676`;
- Core product source embedded by the client:
  `e8eb7721fc6eaac6813d3a888ac90d0da1f541a1`;
- Core PR 6 CI/evidence carrier:
  `4fa9accf01a7bed717f739d3f57eb27a65593e3c`.

The Core product source and PR carrier differ only under `.github/**`. The
local aggregate intentionally evaluates the client-bound product source, while
the public Core PR carrier supplies hosted CI evidence. These identities are
not interchangeable and are retained separately.

## Exact local aggregate

The final corrected command used platform `663890b...`, client `3564023...`
and Core product `e8eb772...`. It passed all `15/15` steps, including client
analysis and widget tests, cross-repository seed validation, web lint/build/E2E,
marketing build/SEO/responsive coverage and static performance collection and
gate.

Retained local report identities:

- `010I-local-quality-gate.json`: SHA-256
  `91c474deda3b05233e9a110cf364e7bf5974375a84dad63aab12c78f2f0266d8`;
- `010I-local-web-performance-evidence.json`: SHA-256
  `fcd2442d529bd9aa351f5f407fbe11d733e1f6b04296a4762fc3da3a2ec4a381`;
- `010I-local-web-performance-gate.json`: SHA-256
  `f4295697c181e55ac65e8fc6a3fcf6de228eb1a04ab6d7db4bbabde82a9a57fb`.

The aggregate itself reports `candidate_proven=false` and
`promotion_status=MANUAL_OWNER_TEST`. The earlier fail-first run against the
Core CI carrier is retained as a scope-selection correction; it is not product
failure evidence. One earlier marketing `networkidle` timeout also passed on
the corrected complete replay and is not hidden.

## Hosted readback

Read-only GitHub state at the retained checkpoint:

- platform PR 58 is open and mergeable at `663890b...`; `repo-guardrails` and
  `cross-repository-contract` are zero-step failures and
  `release-base-isolation` is skipped;
- client PR 33 is open and mergeable at `3564023...`; its
  `cross-repository-contract` is a zero-step failure;
- Core PR 6 is open and mergeable at `4fa9acc...`; `test`, Android and Windows
  artifact reproducibility and Apple source build pass, while
  `release-contract` fails closed because client `main` still pins the prior
  Core source.

The platform and client failures are access/billing startup failures, not
executed test failures and not passes. Core's release-contract failure is a
real promotion-order dependency. The client binding must land before the Core
contract can become green.

## Decision and evidence ceiling

- paid GitHub plan: `DECLINED_BY_OWNER`;
- private platform/client branch protection:
  `WAIVED_BY_OWNER_SOLO_EXCEPTION`;
- independent reviewer: `UNAVAILABLE_NOT_CLAIMED`;
- platform/client hosted checks: `BLOCKED_BY_ACCESS_GITHUB_BILLING`;
- repository visibility change: `NOT_RUN_SEPARATE_PUBLICATION_SAFETY_GATE`;
- exact local source aggregate: `PASS_15_OF_15`;
- exact candidate: `NOT_CREATED`;
- merge, deploy, public asset, stable pointer and promotion: `NOT_RUN`.

No execution-ledger row advances. This work order changes the repository and
promotion policy record and strengthens exact pre-candidate local evidence; it
does not create candidate or production proof.

## Next action

1. Audit platform and client source/history for secrets, private runtime
   material, generated artifacts, dependency licenses and public-contract
   hazards with a dedicated redacting scanner before any visibility change.
2. Keep private hosted checks marked `BLOCKED_BY_ACCESS`; do not describe the
   solo branch-protection exception as a check waiver.
3. Preserve the promotion order: client binding, Core release-contract replay,
   then Core/platform promotion only when the applicable exact checks are
   genuinely green or a separately documented release-check policy changes.
4. Freeze and sign a replacement candidate only after the promoted source
   tuple is exact, then run the candidate-bound device, Windows network,
   current/Brain/RU-origin, provider, Operator, legal and performance matrices.
