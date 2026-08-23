# WO-003B — Release-Handoff v2 CI Enforcement

Status: `COMPLETE_I3`
Classification: `ACTIVE_EXECUTION`
Phase: `01`
Lane: cross-repository release gates

## Bounded outcome

Make schema-v2 generation and validation mandatory on release-bound platform,
client and Core paths. Remove the release-path ability to pass without the
active client checkout. Keep ordinary quick checks independent from multi-repo
candidate orchestration.

No candidate, artifact, deploy, branch-protection mutation or production
change is authorized by this WO.

## Entry evidence

- `WO-002`: strict platform v2 validator is locally proved.
- `WO-003`: client generation and app/Core parity are locally proved.
- `REL/REL-002` and `REL/REL-003` remain `I1`; workflow enforcement is absent.

## Authority decision

The generic platform `Guardrails` workflow remains a repository-local PR/push
check. It may continue to use `--allow-missing-client-root`; that skip is
`BLOCKED_BY_ACCESS` evidence and must never be represented as release proof.

The following paths are release-bound and must fail closed when the active
client or Core checkout is absent or release-handoff v2 validation fails:

1. the dedicated cross-repository release-v2 contract workflow in platform;
2. the weekly release-gate snapshot;
3. the manual release orchestrator before any non-dry-run remote action;
4. the active client PR/push release-v2 contract workflow;
5. the POKROV Core PR/push release-contract CI job.

External checkout refs use the promotion lines frozen by repository authority:
platform `master`, client `main`, Core `main`. The repository under test uses
the triggering commit; the other two repositories use their promotion lines.
This makes cross-repository merge order explicit: platform contract first,
client adoption second, Core integration job third.

## Exact write scope

Platform (`codex/1.2.0-phase00`):

- `.github/workflows/release-v2-contract.yml`;
- `.github/workflows/weekly-release-gate-snapshot.yml`;
- `.github/workflows/release-orchestrator-manual.yml`;
- `scripts/run_client_release_gate.py`;
- `scripts/release_gate_check.py`;
- `scripts/release_orchestrator.py`;
- focused tests for those scripts;
- the matching release-operation owners and this megaplan packet.

Client (`codex/1.2.0-release-v2`):

- `.github/workflows/release-v2-contract.yml`;
- one static workflow contract test wired into `validate-seed.ps1`;
- client test/release-operation documentation.

Core (`codex/1.2.0-release-v2` in a separate worktree):

- `.github/workflows/ci.yml`;
- `docs/release.md`.

No other Core code, artifact, release configuration or evidence is in scope.

## Event and enforcement matrix

| Surface | Events | Checkout contract | Required action |
| --- | --- | --- | --- |
| Platform `Guardrails` | PR, push | platform only | quick repository guardrail; client skip remains explicit and non-release |
| Platform release-v2 contract | PR, push to `master`, manual | triggering platform + client `main` + Core `main` | client `validate-seed` and deterministic v2 contract with explicit roots |
| Weekly release snapshot | schedule, manual | platform `master` + client `main` + Core `main` | strict quick gate; no `--allow-missing-client-root` |
| Manual orchestrator | manual | triggering platform + client `main` + Core `main` | cross-repo contract always; real v2 metadata required before non-dry-run remote work |
| Client release-v2 contract | PR, push to `main`, manual | triggering client + platform `master` + Core `main` | strict `validate-seed` with explicit roots |
| Core CI release contract | PR, push to `main` | triggering Core + platform `master` + client `main` | strict client/Core parity and v2 contract with explicit roots |

## Fail-closed rules

- Release-bound jobs do not pass `--allow-missing-client-root`.
- Platform, client and Core roots are explicit; sibling-name guessing is not
  the CI contract.
- Client preflight includes the v2 generator and v2 contract entrypoint.
- The platform release gate contains the v2 client contract as a named gate.
- Non-dry-run remote orchestration rejects missing v2 metadata and rejects a
  legacy env-only handoff.
- Supplied metadata is validated locally before any remote handoff or deploy
  step is built or executed.
- Contract workflows create no retained release artifact and perform no deploy,
  signing, publish, promotion or branch-protection mutation.

## Acceptance commands

Platform:

```powershell
python -B -m pytest -p no:cacheprovider tests/test_run_client_release_gate.py tests/test_release_gate_check.py tests/test_release_orchestrator.py tests/test_release_handoff_metadata.py tests/test_check_script_manifest.py -q
python scripts/run_client_release_gate.py contract --client-root C:\path\to\POKROV-app --core-root C:\path\to\POKROV-core
python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q
python -B scripts/agent_context_packet_audit.py --platform-context-root .
```

Client:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-seed.ps1 -PlatformRoot C:\path\to\platform -CoreRoot C:\path\to\POKROV-core
powershell -ExecutionPolicy Bypass -File .\test\release-v2-ci-contract.ps1
```

Core integration is proved by running the same client validation with the Core
worktree as `-CoreRoot`, plus Core's existing `./scripts/test.ps1`. GitHub-hosted
workflow execution remains unclaimed until the changes are committed, pushed
and observed on the exact commits.

## Closure evidence

Completed on 2026-08-21 in three isolated worktrees:

- platform `codex/1.2.0-phase00`;
- client `codex/1.2.0-release-v2`;
- Core `codex/1.2.0-release-v2`.

Implemented:

- dedicated non-mutating platform and client release-v2 contract workflows;
- strict three-checkout weekly release snapshot;
- Core PR/push release-contract job;
- named release-handoff v2 gate in platform quick/full release gates;
- explicit client/Core roots in the platform contract runner;
- mandatory locally validated v2 metadata for non-dry-run remote orchestration;
- legacy env-only remote execution rejection;
- canonical platform, client and Core release-operation documentation.

Verification:

- platform focused regression: `90 passed, 21 subtests passed`;
- platform contract runner: `PASS`, including client/Core parity, all 12
  generator fail-closed cases, CI static contract and docs contract;
- client `validate-seed.ps1` with explicit platform/Core worktrees: `PASS`;
- platform documentation contract: `30 passed`; context audit: `PASS`;
- platform, client and Core workflow YAML parse: `PASS` (`4`, `1`, `1` files);
- Core `scripts/test.ps1`: `PASS` with official portable Go `1.25.12`; the
  archive SHA-256 matched
  `d5dc82da351b00e5eedd04f41356817d674cc4308131f0f638a5b14c5c3af4cb`;
- `git diff --check`: `PASS` in all three worktrees.

Evidence boundary:

- GitHub-hosted workflow results are `NOT_REQUESTED` and unclaimed because no
  commit, push or PR is authorized or performed;
- no candidate, retained release artifact, signing action, deploy, runtime
  mutation, promotion, branch-protection change or external message occurred;
- `REL/REL-002` and `REL/REL-003` advance to `I3`; broader Gate A, DoD and
  frontend release rows retain partial evidence without an index advance.

## 2026-08-23 exact hosted client gate control

`REL/TEST-001` is deliberately narrower than this WO's already-complete
release-v2 source enforcement. Release-base-isolated control commit
`085ac1ae49eea71f60209d70438fbb8f404b53af` now makes its missing hosted
Ubuntu run exact and reviewable without merging the broad implementation into
the control PR.

The five-path control binds platform
`30859e115859386f5dd51210b5697af5440c36df`, client
`8c6b955dced3b018825c53fe5d14cb632271adeb` and Core
`fcb3c8bbc6efdeed284417369aacb522722ebfa2`. It verifies the three checked-out
HEADs, then runs client `validate-seed.ps1` and `run-tests.ps1` on Ubuntu 24.04
with pinned Python 3.12, Java 17, Flutter 3.38.5 and pinned action revisions.

Local control validation, `4/4` focused tests, Ruff check/format and diff check
pass. The control changes zero visible UI paths. Hosted execution is still
`NOT_RUN`: the exact source commits are not published, the control branch is
not pushed, and cross-private-repository checkout requires an owner-created
`POKROV_RELEASE_REPO_READ_TOKEN` secret limited to `contents:read` on
`Kiwunaka/POKROV-app`. No credential was generated or stored. Therefore
`REL/TEST-001` stays `I2`; see `WO-013L`.
