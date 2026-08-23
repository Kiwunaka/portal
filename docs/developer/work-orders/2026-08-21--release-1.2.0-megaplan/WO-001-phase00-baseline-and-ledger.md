# WO-001 — Phase 00 Baseline and Execution Ledger

Status: `COMPLETE`
Classification: `ACTIVE_EXECUTION`
Lane: platform documentation
Executor branch/worktree: `codex/1.2.0-phase00` / `C:/Users/kiwun/Documents/ai/VPN-1.2.0-phase00`

## Bounded outcome

Create a resumable, machine-checkable Phase 00 packet that fixes the exact starting revisions, assigns every explicit source-plan item a unique tracked row, defines an execution index, records authority conflicts, and routes the 1.2.0 work from architecture to exact-candidate release proof.

## Write scope

- `docs/developer/work-orders/2026-08-21--release-1.2.0-megaplan/**`
- one registry row in `docs/README.md`

## No-touch scope

- user/concurrent files under `competitor-profiles/**`
- all platform source/runtime code
- the active client, core and public release repositories
- production, payments, campaigns, providers, signing and GitHub settings

## Authority anchors

- `AGENTS.md`
- `docs/developer/agent-context-map.md`
- `docs/README.md`
- `docs/developer/developer-guide.md`
- `docs/developer/orchestration/orchestration-standard.md`
- `docs/developer/orchestration/wo-authoring-guide.md`
- canonical owners linked by the task router for later behavior-changing WOs

## Inputs

| Plan key | Source snapshot |
|---|---|
| `REL` / `OBS` | `POKROV_release_1.2.0_full_audit_with_client_logging_RU.md` |
| `OC` | `POKROV_OPERATOR_CENTER_V2_AUDIT_AND_IMPLEMENTATION_PLAN_2026-08-20.md` |
| `FE` | `POKROV_1.2.0_FRONTEND_AUDIT_AND_RELEASE_PLAN.md` |
| `MKT` | `POKROV_MARKETING_AUDIT_RELEASE_1.2.0_2026-08-20.md` |
| `FRKN` | `frkn-org.md` |

These files are advisory inputs, not repository authority. Their instructions are reconciled against current code, canonical owners and exact evidence.

## Acceptance oracle

1. `BASELINE.json` parses and contains exact branch/commit observations for platform, client, core and public release index.
2. `EXECUTION-LEDGER.csv` parses, has unique `(plan,id)` keys and contains all explicit IDs from the five input plans plus release Gates A–F and both release/observability DoD sets.
3. `EXECUTION-INDEX.md` defines auditable states `I0`–`I5`; no percentage is inferred from prose.
4. `SOURCE-CROSSWALK.md` records lane ownership, plan coverage and all material conflicts.
5. The wave index exposes current state, dependencies, manual proof boundaries and the next WO.
6. Docs contract tests, context audit, link check and `git diff --check` pass.
7. Final scoped diff contains no secrets, release claim inflation, source-code change or unrelated cleanup.

## Validation commands

```powershell
python -m json.tool docs/developer/work-orders/2026-08-21--release-1.2.0-megaplan/BASELINE.json > NUL
$rows = Import-Csv docs/developer/work-orders/2026-08-21--release-1.2.0-megaplan/EXECUTION-LEDGER.csv
$rows | Group-Object plan,id | Where-Object Count -gt 1
python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q
python -B scripts/agent_context_packet_audit.py --platform-context-root .
python -B scripts/check-links.py
git diff --check
```

## Risk and evidence boundary

This WO proves only local documentation integrity against the inspected revisions. It does not prove branch protection, trusted signing, physical-device behavior, clean-host TUN/DNS, RU-origin operation, provider readiness, legal qualification, deployment or production availability.

## Documentation impact

Adds execution-state documents and a registry route. No canonical product, architecture, release or support truth changes in this WO.

## Promotion state

No commit, push, PR, merge, deploy or release promotion requested or performed.

## Closure record

Result: `COMPLETE` — locally proved execution packet; no runtime or release claim.

Validation on 2026-08-21:

- `PASS` — `BASELINE.json` parsed with `python -m json.tool`.
- `PASS` — 377 CSV rows, 19 plan namespaces, zero duplicate `(plan,id)` keys, zero invalid indices/phases and zero empty required fields.
- `PASS` — source comparison found zero missing/extra IDs for REL 37, OBS 90, OBS playbooks 14, OC 30, FE 64, FE bugs 3, FE PRs 11 and MKT 10; synthetic Gate/DoD/FRKN/stage groups matched declared counts.
- `PASS` — docs contract/context tests: 30 passed.
- `PASS` — platform context audit.
- `PASS` — repository link check.
- `PASS` — tracked diff check plus per-file untracked whitespace check.
- `PASS` — bounded credential/private-key pattern scan returned no matches.

Manual/runtime/signing/device/RU-origin/provider/deploy/production checks: `NOT_REQUESTED` for this documentation-only WO.

Commit/push/PR/merge/deploy/promotion state: not performed.
