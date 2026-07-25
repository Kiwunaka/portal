# Repository Consolidation Evidence — 2026-07-25

## Scope

This record covers the 2026-07-25 consolidation of the platform, active private
client, POKROV Core, and public source-client lanes. The exact platform
candidate is the commit that contains this document. No production status is
inferred from a local build or a Git push; live origins are recorded separately
after deployment.

The consolidation rule was:

1. preserve unique evidence before cleanup;
2. choose one implementation for every conflicting runtime responsibility;
3. retain patch-equivalent or semantically equivalent work once, not once per
   worktree;
4. test the resulting candidate rather than the source worktrees;
5. keep signing, physical-device, and binary-provenance gates explicit.

## Platform Worktree Resolution

| Source branch | Disposition | Retained result |
| --- | --- | --- |
| `master` / `codex/ai-seo-aggressive` | base retained | AI/SEO positioning from `95febec` |
| `codex/aggressive-sales-copy` | integrated with policy reconciliation | conversion copy from `09dac0e`; absolute public promises were removed when the repository copy guard caught them |
| `codex/research-censorship-stack-2026-07-22` | patch-equivalent integration | censorship and client-core research under the dated competitive-research owners |
| `codex/selected-vpn-features-ios-ui` | integrated | selected cross-surface VPN features in `4629a51` |
| `codex/telegram-rich-bot` | integrated and hardened | rich Telegram presentation in `e76e50d`, followed by compatibility fixes |
| `codex/ops-admin-rebuild` | integrated and hardened | command center in `7d23a00`, with explicit audit/confirmation classification for guarded mutations |
| `codex/vpn-competitor-app-audit` | tracked evidence integrated | deep audit in `fbca5a7`; unique untracked raw corpus preserved outside Git before cleanup |
| `codex/vpn-competitor-infographics` | integrated and regenerated | platform refinement in `6af6b11`; HTML, PNG, and manifest regenerated from the final source |

Semantic comparison was used where `git cherry` remained positive because the
final candidate contained a reconciled or evolved implementation. No source
branch was promoted merely because it was newer.

## Private Client Conflict Resolution

The active client was promoted through
[POKROV-app PR #8](https://github.com/Kiwunaka/POKROV-app/pull/8) and merged as
`b612c3a2aebe81875a74019437d7b341798ab36d`.

| Candidate | Decision | Reason |
| --- | --- | --- |
| Hiddify v4 migration | rejected | conflicted with the owned POKROV Core lane and would have restored a second runtime authority |
| POKROV Core 1.0.0 activation | selected | canonical owned runtime direction; patch-equivalent implementation retained in the integration branch |
| selected protection/routing UI | selected with conflict reconciliation | product controls retained; Android `RuntimeHostBridge` kept the private materialized-config path and also retained Quick Settings |
| client consolidation branch | merged | carried the selected runtime, UI, documentation, tests, and artifact-provenance guard |

The merged client candidate passed seed validation, workspace bootstrap, Dart
analysis, Flutter tests, Android JVM tests, APK/AAB builds, and the Windows
build/package lane. Those local Android artifacts were debug-signed and the
Windows artifact was unsigned, so neither is treated as a publishable stable
binary.

## Core Artifact Provenance Boundary

`POKROV-core` remained clean at tag `v1.0.0`, commit
`3720cb052e56ccd68f0120cc9efaf5804ec84e0b`. Its Go tests passed with Go
1.25.12.

A clean rebuild was deterministic but not byte-identical to the client-pinned
Android AAR and Windows DLL. Embedded Go build information proves that the
pinned artifacts were built from revision `47bbc21...` with
`vcs.modified=true`, while the clean tag build identifies `3720cb0`.
`libcronet.dll` did match.

Consequences:

- the tested client-pinned artifacts were not silently replaced;
- tag `v1.0.0` was not republished;
- client metadata now records the provenance exception;
- the runtime sync script refuses to describe a non-identical clean rebuild as
  the pinned release;
- a future patch release must produce and publish traceable artifacts.

## Backend Composition Split

The 24,034-line `portal_bot/api.py` and 12,134-line `portal_bot/bot.py`
composition roots were split without changing the deployment unit or the
legacy import surface.

Final layout and size budgets are documented in
[`docs/developer/backend-module-map.md`](../developer/backend-module-map.md).
The compatibility runtime:

- loads an explicit ordered module list;
- performs no filesystem discovery and no source-string execution;
- re-exports legacy names from `api` and `bot`;
- preserves reload and monkeypatch behavior used by tests and operator tools.

The split carried 15,731 API source lines and 7,829 bot source lines into the
new slices; only trailing whitespace and end-of-file whitespace were normalized
before commit. Runtime import/reload checks retained 248 FastAPI routes and 155
aiogram handlers. New size-contract tests prevent either composition root from
returning to a 20,000-line monolith.

The exact full-suite run also exposed test isolation that had previously been
masked by leaked SQLite files. Twelve database fixtures now use owned temporary
directories, the direct `sqlite3` schema probe closes its connection
explicitly, and reload-sensitive API/support tests rebuild a coherent module
stack. The final full run left zero `portal_api_test_*.db*` files in the
repository root.

The public-copy guard was also extended to scan the new bot handler slices, the
bot text/profile owners, and the governed copy catalog. This prevents a future
split from moving unsafe public promises outside the scanned surface.

## Preserved Local Evidence

The following non-Git inputs were hashed before their source worktrees or
caches were cleaned:

| Evidence | Contents | Manifest or bundle SHA-256 |
| --- | --- | --- |
| `competitor-audit-raw-20260725` | 1,966 raw research files, 180,623,362 bytes | `aead8f676a1cc9fff16fea7dadaa99940a99dd88cbd9eb833529f45b1a65399b` |
| `legacy-hiddify-cache-20260725-sha256.csv` | 77 rejected Hiddify 3.1.8 cache files, 663,526,285 bytes | `8c2198dd17171881f456b60e3ac6ceb04b662aeb916375e999bed616878dd212` |
| `pokrov-app-worktrees-20260725.bundle` | all four removed private-client worktree refs and complete reachable history | `9fd429bc25d2c4d6767556797321096bf165cb846e3763474230c7e07afc16f9` |
| `pokrov-app-local-evidence-20260725` | 70 ignored client files inventoried; 58 unique reviews, captures, manifests, and workbook files copied before generated/duplicate cleanup | `3c817851aa4b3d27573bb2ba6079d901cee55aeee6790aa7613e4f138ea25cb9` |
| `pokrov-core-clean-build-20260725-sha256.csv` | seven deterministic clean-build/tool files, 191,200,152 bytes, recorded before cache cleanup | `bf35441c002dba07c8b8ca78bfcc21e9253d8d3b2275a52773f4aa81328a9c65` |
| `pokrov-client-superpowers-20260725` | nine untracked public-client brainstorm files, 23,104 bytes | `e70e6fb73e358c235d0872d7bafd3d930b70cb8238196459e28380903d79c568` |
| `pokrov-client-build-evidence-20260725` | 11,294 historical source-release evidence and generated fixture files moved out of the public checkout | `20ef51ff10984895041ba4d1e375799fd1f525ae962e7a3996faf54049c8a5d8` |

The rejected Hiddify cache is reconstructable public cache material, not
release evidence. The branch bundle is the recovery source for deleted local
branch refs.

## Verification Matrix

| Lane | Result |
| --- | --- |
| Backend slice contract and runtime reload | PASS: 248 FastAPI routes, 155 aiogram handlers, reload/monkeypatch propagation retained |
| Focused API, auth, ticket, bot paywall, admin policy, parity, and infographic tests | PASS |
| Platform full Python suite | PASS: 2,391 tests, 245 subtests, 3 expected skips, 0 failures in 42:34; JUnit and logs preserved outside Git |
| Marketing lint, build, SEO, and responsive checks | PASS: ESLint, 32-route production build, SEO contract, responsive contract |
| WebApp lint/build/public-error checks | PASS: ESLint, 40-route production build, 2/2 public-error contracts |
| WebApp full E2E | PASS: 73/73 Playwright tests |
| AdminApp lint/build/E2E | PASS: ESLint, 17-route production build, 60/60 Playwright tests |
| Private client PR #8 CI and local platform builds | PASS within the signing/provenance limits above |
| POKROV Core Go tests | PASS |
| Public source-client design PR #207 CI | PASS: source/import, Flutter analyze/tests, and Android JVM jobs |
| Script manifest | PASS after registering `research_censorship_corpus.py` |
| Generated-artifact/public-copy guard | PASS after generated frontend/test output cleanup |

## Deployment and Manual Gates

Platform backend and static deployment may proceed only after the exact
candidate is merged and rebuilt from the canonical checkout containing the
preserved local secret locations. The staged backend/static deploy scripts own
rollback and retain bounded backups.

Production verification must keep `current`, `brain`, and RU-origin results
separate. Android physical-device audit, trusted Android signing, trusted
Windows signing, and a provenance-correct Core patch release remain manual
release gates; a successful platform deployment does not clear them.
