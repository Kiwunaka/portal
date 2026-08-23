# WO-003D — Release-handoff v2 runtime consumer

Status: `IMPLEMENTED_PARTIAL_I2`
Phase: `01`
Ledger rows: `REL_DOD/DOD-02`, `FE/P12-022`
Promotion: `NOT_REQUESTED`

## Intent

Close the source-level gap between strict cross-repository release-handoff v2
validation and the platform runtime download consumer. A valid v2 file must not
fall through the legacy `downloads/runtime_env` parser and fail only after
orchestration has started.

## Implemented contract

- `remote_brain_apply_release_handoff.py` detects schema v2, runs the canonical
  offline validator again and rejects invalid metadata before SSH is loaded.
- The v2 projection accepts only the canonical Android APK identities and the
  canonical Windows x64 setup EXE. The ARM64 APK is primary when present, with
  deterministic universal, ARMv7 and x86_64 fallback order.
- Runtime env receives the release channel/version, exact handoff SHA-256,
  artifact-set SHA-256, candidate label and Core version/desktop ABI/Android
  package in addition to artifact URLs, hashes and sizes.
- `/api/client/apps` and `/api/public/client-apps` expose a bounded
  `release_manifest` identity. Partial, malformed or legacy configuration
  returns `null`; it cannot appear manifest-bound.
- Schema-v1 `runtime_env` and `downloads` remain migration-only compatibility.
  No second release-manifest owner was created.

## Retained local proof

- Strict-v2 projection and validator regression: `53/53` tests.
- Client-app API fail-closed projection: `6/6` focused tests; complete adjacent
  API regression: `29` tests plus `4` subtests.
- Release orchestrator/gate regression: `48` tests plus `21` subtests.
- Exact synthetic v2 dry-run: `PASS`; no SSH module was loaded and no remote
  operation occurred.
- Python compilation, focused Ruff, webapp ESLint, docs contracts (`26/26`),
  link check and scoped diff check: `PASS`.

Evidence:
`evidence/003D-release-v2-runtime-consumer/003D-v2-runtime-consumer.json`.

## Evidence ceiling

This is source, fixture, API and dry-run proof. The platform, client and Core
worktrees remain dirty; no real 1.2.0 candidate, public release-index revision,
detached manifest signature, signed artifacts, hosted CI, runtime sync, public
readback, deploy or promotion was produced. The two rows therefore advance only
to `I2`. Exact signed-candidate and runtime/static-surface readback are required
before `I3`/`I4`.
