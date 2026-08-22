# WO-003 — Client Release-Handoff v2 Generation and Parity

Status: `COMPLETE`
Classification: `ACTIVE_EXECUTION`
Phase: `01`
Lane: active client
Executor branch/worktree: `codex/1.2.0-release-v2` / `C:/Users/kiwun/Documents/ai/POKROV-app-1.2.0-release-v2`

## Bounded outcome

Generate strict release-handoff schema v2 from client-owned canonical seeds and
an explicit candidate input. Prove Android/Windows version parity, exact
embedded Core artifact identity, the real desktop ABI, the Android Core package,
and compatibility with the platform validator.

This slice creates no real candidate and does not modify retained release
artifacts. It does not change workflows, runtime metadata, signing, public URLs,
promotion, platform behavior, or Core source.

## Write scope

Client worktree:

- new `scripts/new-release-handoff-v2.ps1`
- `scripts/check-client-version-parity.ps1`
- `scripts/validate-seed.ps1`
- `scripts/README.md`
- `config/runtime-artifacts.seed.json`
- new `test/release-handoff-v2-contract.ps1`
- new synthetic input under `test/fixtures/release-handoff-v2/`
- `test/seed-layout.ps1`
- `apps/windows_shell/test/widget_test.dart`
- `apps/android_shell/android/app/src/test/kotlin/space/pokrov/pokrov_android_shell/AndroidHostSecurityContractTest.kt`
- `docs/decisions/2026-08-13-pokrov-core-1.0.3-release.md`
- `docs/operations/cutover-readiness.md`

Platform worktree:

- this WO, wave index and execution ledger/evidence only

## No-touch scope

- `artifacts/releases/**` and all real build outputs
- Android/Windows application or host source
- `.github/workflows/**`
- `C:/Users/kiwun/Documents/ai/POKROV-core/**`
- public release repository, platform runtime code and production
- signing material, devices, providers, payments, deploy and promotion

## Authority anchors

- client `AGENTS.md` and `docs/README.md` release-metadata route
- client `config/release-handoff.seed.json`
- client `config/runtime-artifacts.seed.json`
- client `config/windows-release.seed.json`
- client Android/Windows `pubspec.yaml`
- Core `config/release.json`
- platform `scripts/release_handoff_metadata.schema.json`
- platform `scripts/validate_release_handoff_metadata.py`
- platform publishing and client-delivery owners

## Generator contract

The generator receives a synthetic/operator candidate-input JSON and an
explicit output path. It fills only client-owned values:

- exact client revision from Git;
- Android and Windows public version from their package manifests;
- Core version, source revision, desktop ABI, Android package, and per-platform
  embedded Core artifact SHA-256 from the runtime artifact seed;
- candidate artifact source revision, Core identity and the deterministic
  artifact-set digest.

The input remains responsible for platform/core/release-index revisions,
contract hashes, public artifact hashes and URLs, signing/SBOM/provenance
evidence, manual gates and promotion intent. The generator must not turn any
missing or manual state into `PASS`.

Default execution fails on a dirty client worktree. A clearly named test-only
switch may bypass that check only for non-stable synthetic output. The script
must never write to `artifacts/releases/**` unless a later artifact WO
explicitly authorizes that destination.

The generated file must pass the platform offline validator. The client does
not copy or redefine the platform schema.

## Parity contract

The standard client parity check must fail when:

1. Android and Windows package versions differ;
2. the current repo-backed release seed version differs from the shell public
   version;
3. runtime Core version/tag/source revision disagree;
4. Windows release config and runtime seed disagree on desktop ABI;
5. the Android Core package is not `space.pokrov.core`;
6. checked-in Android AAR or Windows DLL size/SHA-256 differs from the runtime
   artifact seed;
7. a generated candidate version differs from the two shell versions.

Android has no invented integer ABI. It is bound by package identity and exact
AAR digest. Windows is bound by desktop ABI and exact DLL digest.

## Acceptance oracle

1. Client worktree begins from clean `POKROV-app/main` at
   `ba7930ea83487874f47a49199ade89868c5675b3`.
2. Synthetic input generates one deterministic v2 handoff outside
   `artifacts/releases/**`.
3. Repeated generation from the same inputs produces byte-identical output.
4. The generated handoff passes the platform validator with exit `0`.
5. Mutation tests fail on dirty stable generation, shell-version mismatch,
   Core source mismatch, AAR/DLL digest mismatch, invented Android integer ABI,
   invalid evidence and a destination under `artifacts/releases/**`.
6. `scripts/validate-seed.ps1` runs the expanded parity and contract test.
7. Client canonical Core/release docs describe package/digest versus desktop ABI
   correctly.
8. Client tests, docs contract, seed validation and `git diff --check` pass.
9. `git status --short` shows no `artifacts/releases/**` delta.
10. Platform focused validator/docs checks remain green.

## Verification

```powershell
powershell -ExecutionPolicy Bypass -File .\test\release-handoff-v2-contract.ps1 `
  -PlatformRoot C:/Users/kiwun/Documents/ai/VPN-1.2.0-phase00 `
  -CoreRoot C:/Users/kiwun/Documents/ai/POKROV-core
powershell -ExecutionPolicy Bypass -File .\scripts\validate-seed.ps1 `
  -PlatformRoot C:/Users/kiwun/Documents/ai/VPN-1.2.0-phase00 `
  -CoreRoot C:/Users/kiwun/Documents/ai/POKROV-core
powershell -ExecutionPolicy Bypass -File .\test\docs-contract.ps1
git diff --check
git status --short
```

From the platform worktree:

```powershell
python -B -m pytest -p no:cacheprovider tests/test_release_handoff_metadata.py -q
python -B scripts/validate_release_handoff_metadata.py `
  --metadata-file C:/path/to/generated-synthetic-release-handoff.json
```

## Proof boundary

A generated synthetic v2 file is local contract evidence only. It is not a
release candidate, artifact, signing result, device proof, RU-origin proof,
runtime sync, public release or promotion authorization.

## Closure record

Result: `COMPLETE (I3)` — deterministic client generation and cross-repository
version/Core parity are locally proved. CI enforcement and candidate proof
remain open.

Implemented on 2026-08-21 from clean client base
`ba7930ea83487874f47a49199ade89868c5675b3`:

- strict PowerShell generator that refuses retained release destinations,
  overwrite, dirty operator output and stable use of the synthetic bypass;
- exact client revision, Android/Windows version, Core version/source,
  Android package+AAR digest, Windows desktop ABI+DLL digest and canonical
  artifact-set hash binding;
- direct comparison with clean `POKROV-core` checkout at
  `69a74545101708e56183c92e31f2b4c7b2509884` and its `release.json`;
- 12-case deterministic/platform-validator/mutation contract test;
- current 1.1.6 readiness text reconciled without reusing old device evidence;
- Windows/LF-CRLF normalization in two source-contract tests after the full
  suite exposed five false negatives on this Windows checkout.

Validation:

- `PASS` — seed layout, client/Core parity, v2 contract, seed validation and
  docs contract;
- `PASS` — full client test entrypoint: app-shell `311`, runtime-engine `47`
  plus one explicit real-DLL skip, Android Flutter `8`, Windows Flutter `17`,
  Android JVM `143`;
- `PASS` — platform regression: `73` tests plus `21` subtests; docs/context
  regression: `30` tests;
- `PASS` — repeated synthetic output is byte-identical and accepted by the
  platform validator with exit `0`;
- `PASS` — zero `artifacts/releases/**` delta; no candidate or retained output;
- `PASS` — scoped diff/JSON/secret/whitespace checks.

Manual/runtime/signing/device/RU-origin/provider/deploy/production checks:
`NOT_REQUESTED` for this contract-generation WO.

## Next slice

Execute `WO-003B`: wire v2 validation into release-bound cross-repository CI
without `--allow-missing-client-root`, while keeping quick non-release checks
and manual candidate operations explicitly distinct.
