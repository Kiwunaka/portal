# G06 — live branch protection and bounded owner exception

**VERIFIED / I3 for R12-G06.** Current-origin GitHub REST and GraphQL readback,
2026-09-09. Source inputs: platform `5e7cb54`, client `5760f41`, Core `c7a11f7`.
This is governance proof; the release remains **BLOCKED**.

The initial readback found all three repositories public, admin access present,
branch protection absent (`404 Branch not protected`), and rulesets empty.
This supersedes the earlier access-denied observations without rewriting them.
GitHub documents protected branches as available for public repositories on
[GitHub Free](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).
No visibility, subscription, billing limit, runner or LFS settings changed.

Under the [owner's existing authorization](OWNER-DECISIONS-2026-09-09.md),
the already specified policy in `shared/release-1.2.0-stop-ship-regressions.json`
was applied to the three promotion branches using GitHub REST. Prepared requests
were reviewed before mutation; protection/rulesets were checked again immediately
before each PUT to avoid replacing concurrent settings. Required signatures
were enabled through the separate endpoint.

| Repository / branch | Strict required checks, bound to GitHub Actions app 15368 |
| --- | --- |
| Kiwunaka/portal / master | repo-guardrails; cross-repository-contract |
| Kiwunaka/POKROV-app / main | cross-repository-contract |
| Kiwunaka/pokrov-core / main | test; release-contract; android-artifact-reproducibility; windows-artifact-reproducibility; apple-source-build |

All three require PRs, signed commits, linear history and resolved conversations.
Admin enforcement is enabled; force pushes and branch deletion are disabled.
REST readback confirmed the policy, and GraphQL independently confirmed required
PRs, zero required second-person approvals and zero PR/force-push bypass actors.
Rulesets remain empty; enforcement is the exact branch-protection rule.
The platform draft PR was observed `mergeStateStatus=BLOCKED`; no merge or
deliberate invalid push against a promotion branch was attempted.

The sole-owner exception remains limited to Android/Windows 1.2.0 direct
distribution, its prerelease candidates and same-byte stable promotion; it
expires when release 1.2.0 closes. It does not cover store/Apple/Linux releases
or later versions. `independent_review_performed=false`. The paid-private-
protection waiver is not used on these current public branches. Missing/failed
checks, signing and device proof do not become PASS through this exception.
The [canonical publishing owner](../../../operations/publishing-and-signing-guide.md)
records these boundaries.

## Commands and results

Retained one-shot helper in [the evidence manifest](evidence/g06-enforcement-20260909/receipt.json):

```powershell
python -B E:/r12-g06-enforcement-20260909/enforcement.py prepare
python -B E:/r12-g06-enforcement-20260909/enforcement.py apply
python -B E:/r12-g06-enforcement-20260909/enforcement.py readback
python -B scripts/release_1_2_stop_ship_gate.py --client-root E:/r12client --core-root E:/r12core-implementation --query-github --output E:/r12-g06-enforcement-20260909/gate-after-recheck.json --expect-nonpass
```

The existing gate reported `NO_GO` before changes. Its first post-change run
could not read platform protection, while the separate REST/GraphQL readback
succeeded; that incomplete result is retained as `gate-after.json`. A second
read-only gate completed with **3/3 hosted branch policies PASS**, seven local
source anchors PASS, reviewer exceptions explicit, and aggregate **BLOCKED**.
The aggregate still lacks the three exact PR bindings and installed Windows
candidate proof. A source anchor check does not execute its referenced tests.

The helper, exact requests, API results, before/after gates and bypass readback
are retained with byte sizes and SHA-256 hashes. Pre-change state was no branch
protection in each repository. Any future rollback of these settings requires
an explicit decision to remove protection; no rollback or bypass was executed.
No source/default-branch promotion, deploy, candidate or release publication.

Documentation verification: `python -B -m pytest -p no:cacheprovider
tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q`
— 33 PASS; `python -B scripts/agent_context_packet_audit.py
--platform-context-root .` — PASS; work-order `validate_package.py` — 83 R12 IDs,
378 retained legacy IDs and 411 local links PASS; `git diff --check` — PASS.
