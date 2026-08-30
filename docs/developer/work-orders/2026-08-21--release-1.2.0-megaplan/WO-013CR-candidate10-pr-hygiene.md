# WO-013CR — candidate.10 pull-request hygiene and DNS recheck

## Outcome

Remove obsolete open pull-request state without deleting branches or changing
the signed candidate.10 source tuple. Keep only work that is genuinely
unmerged and classify its release boundary explicitly.

## Exact boundary

| Item | Value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.10` |
| Candidate platform source | `209b8f40c36d95f2bbc67caa52a41ecb09f46720` |
| Candidate client source | `3459438f02bd774e722b1b858e7f7f16d57a9f5c` |
| Candidate Core source | `a45d69e40ed7d892619a2b5c4592a527f630665e` |
| Platform audit base | `030b671079d61c3b0a44df20abe591b1d1ed7ed4` |
| Client audit base | `f14d48b50f3369720dc89a4c17dab23391174ae7` |
| Core audit base | `a45d69e40ed7d892619a2b5c4592a527f630665e` |
| Audit time | `2026-08-30T07:15:20Z` |

No source, candidate artifact, signed manifest, runtime, tag, release or stable
pointer is changed by this work order.

## Closed obsolete pull requests

Every closure preserves the head branch and commits. No pull request is merged
or force-updated.

- Platform PRs `49` through `56`: each exact head commit is already an
  ancestor of current `origin/master`. These stacked candidate.3 through
  candidate.5 PRs were open duplicates of history already promoted to
  `master`.
- Client PRs `30` through `32`: each exact head commit is already an ancestor
  of current `origin/main`. Their build 31/build 32 and direct-DoH changes are
  already present on the promotion branch.
- Platform PR `17`: its hosted gate is bound to the older exact source tuple
  recorded in the PR body. The current release uses candidate.10 and the
  owner-approved solo/no-paid-branch-protection process, so the old control PR
  is retained as historical evidence rather than merged.
- Client PR `18`: PR `28` explicitly supersedes it with the newer current-main
  Linux beta foundation and replacement journal/network transaction shape.

Each PR received a classification comment before closure. Thirteen obsolete
open PRs were closed in total; no branch was deleted.

## Deliberately retained pull requests

- Platform PR `57`: allowlisted HAPP iOS bridge canary, explicitly deferred to
  post-1.2.0 work and not part of candidate.10.
- Client PR `28`: the active source-only Linux beta foundation. It remains
  unmerged, conflicting with current main and without a passing current hosted
  cross-repository contract; no Linux release claim is made.
- Core PR `5`: a useful source-only AWG2/AWG3.1 userspace lifecycle test. Its
  focused runtime test passed, while the release-contract job failed because
  the PR changes Core source identity beyond the frozen candidate.10 SHA. It
  remains open for a successor source tuple or post-1.2.0 adoption and is not a
  candidate.10 blocker. Exact candidate.10 Android AWG tunnel evidence remains
  separate runtime proof.

## Authoritative DNS recheck

Direct A queries to `ns1.timeweb.ru`, `ns2.timeweb.ru`,
`ns3.timeweb.org` and `ns4.timeweb.org` all return `NXDOMAIN` for
`dns.pokrov.space`: authoritative readiness remains `0/4`.

This is not a TTL wait or local recursive-resolver ambiguity. Certificate
issuance, root-only resolver material, Smart-DNS server APPLY and frontend
route APPLY remain `NOT_RUN`. No raw address is retained in evidence.

## Release decision

This slice changes no completion-index row. `SMARTDNS-01` remains `I3`; the
latest exact candidate.10 Gate F remains `NO_GO 6 PASS / 13 non-PASS / 1 FAIL`.
Gate G, tag, public release and stable pointer remain unauthorized. The
physical phone is unavailable and untouched.

The normalized record is
`evidence/013CR-candidate10-pr-hygiene/013CR-candidate10-pr-hygiene.json`.
