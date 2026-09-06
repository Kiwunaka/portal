# Local quality convergence after C03 — 2026-09-06

**PASS: 15/15 local stages, exit 0.** Source tuple: platform `272ef9a`,
client `70907c0`, Core `8dc57a8`. This refresh is required after the Core,
packaging and ownership changes since the earlier aggregate run. It closes
the current aggregate local check, not the release or all 83 R12 requirements.
[Structured receipt](evidence/local-convergence.json).

Command, from the platform feature worktree:

```powershell
$env:PATH = 'E:/POKROV-tools/runtimes/node-v22.14.0-win-x64;E:/POKROV-tools/tmp/node22-npm11;C:/Users/kiwun/tools/flutter/git-3.38.5/bin;' + $env:PATH
python -B scripts/release_1_2_local_quality_gate.py --client-root E:/r12client --core-root E:/r12core-implementation --evidence-dir E:/r12-final-local-quality-20260906-c03-pinned --keep-going
```

Toolchain: Node 22.14.0, npm 10.9.2 as the script runner, Python 3.12.5,
Flutter 3.38.5 (`f6ff1529fd`), Dart 3.10.4. Existing frontend dependencies
were used; no npm install or lockfile changes. npm differs from the declared
package-manager pin; this is a local build/test run, not an installation
reproducibility assertion. The initial run with ambient Node 24 was interrupted
before completing; its separate log is retained and not counted as PASS.

## Executed scope

- Performance contract and its five test files; client analyze, all **458**
  app-shell tests, cross-repository seed validation and client docs contracts.
- Cabinet lint/build and **69** browser tests using the existing fixtures.
- Marketing build, SEO and responsive/reduced-motion/checkout fixtures.
- Fresh admin build, static asset collection and performance validation.
- Static stop budgets **9/9 PASS**. Five targets remain unmet: critical-route
  gzip JS for marketing (239757 bytes), cabinet (305386), admin (451397), and
  total export images for marketing (7848431) and cabinet (5390960).
  These are deterministic static measurements, not WAN, RUM or device timings.

All stage commands/cwds are defined by the unchanged, SHA-bound aggregate
script; per-stage exit codes and durations are retained in the receipt.
The earlier failed aggregate and its focused corrective reruns remain intact.

## Identity, limits and next boundary

Core was clean. Platform had only the pre-existing untracked marketing
instruction files; client had four pre-existing generated registrant changes.
`git diff --ignore-space-at-eol --exit-code` on the client passed: these are
line-ending-only. They were preserved, and the report honestly records both
worktrees as dirty. Product source and native bytes were not changed here.

The aggregate explicitly reports `candidate_proven=false` and promotion
`MANUAL_OWNER_TEST`. Final packaged/device performance, signing, provider,
controlled API and browser/network evidence remain separate. This run does
not refresh the external access observations from
[14:39 UTC](EXECUTION-ACCEPTANCE-READBACK.md).

The next mandatory chain still needs the N02 rollback-authority decision,
O03/V02 diagnostic-source decision, M01 seller/receipt data, executable hosted
CI/enforcement and the required device/lab/candidate inputs listed in
[NEXT_ACCEPTANCE](NEXT_ACCEPTANCE.md). Earlier questions remain unanswered.
Postrelease activation is unchanged. None of these missing prerequisites is
converted to PASS by the local aggregate.

No push, merge, deploy, signing, publication, payment, new release candidate,
VM boot or host VPN change. Browser runners completed their own server cleanup;
logs and original receipts remain on E:. This documentation-only handoff can
be reverted independently without changing the verified product source.

Documentation handoff, all exit 0: `python -B -m pytest -p no:cacheprovider
tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q`
(33 PASS); `python -B scripts/agent_context_packet_audit.py
--platform-context-root .`; `python -B
docs/developer/work-orders/2026-09-05--consolidated-release-and-post12/validate_package.py`
(13 section hashes, 83 R12 IDs, 378 legacy IDs, 259 links); `git diff --check`.
