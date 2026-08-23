# WO-002 — Release Handoff v2 Contract

Status: `COMPLETE`
Classification: `ACTIVE_EXECUTION`
Phase: `01`
Lane: platform release contract

## Bounded outcome

Evolve the existing canonical `release-handoff.json` contract from permissive schema v1 to a strict, machine-validated v2 without creating a second release manifest. Preserve read-only validation of current v1 handoffs during migration, while making every new v2 candidate bind exact source revisions, component compatibility, contract hashes, artifacts, signing/provenance state and explicit manual gates.

This WO defines and proves the platform-owned contract/validator only. Client production of v2 metadata, core adoption, workflow enforcement, branch settings, candidate generation, signing and promotion are later bounded Phase 01 slices.

## Why this is first

Current release authority already names client-owned `release-handoff.json` and the platform schema `scripts/release_handoff_metadata.schema.json`. Creating another `release-manifest.json` owner would split truth. The current schema is intentionally permissive: fields are optional and `additionalProperties` is broadly allowed. A strict versioned branch inside the same contract is the smallest architectural seam that later CI, client, core, portal and public-release work can share.

## Write scope

- `scripts/release_handoff_metadata.schema.json`
- new `scripts/validate_release_handoff_metadata.py`
- `scripts/manifest.yaml` for the new script entry
- `portal_bot/requirements.txt` only if the selected JSON Schema validator is added as a direct bounded dependency
- new `tests/test_release_handoff_metadata.py`
- new synthetic fixtures under `tests/fixtures/release-handoff/`
- `docs/operations/publishing-and-signing-guide.md`
- `docs/operations/client-delivery-update-content-plan.md`
- this wave index/ledger and this WO

## No-touch scope

- `C:/Users/kiwun/Documents/ai/POKROV-app/**`
- `C:/Users/kiwun/Documents/ai/POKROV-core/**`
- `C:/Users/kiwun/Documents/ai/pokrov-release/**`
- `.github/workflows/**`, branch protection and repository settings
- real release artifacts, current `1.1.6` handoff content and runtime env
- production, signing keys, provider data, payments, deploy and promotion

## Authority anchors

- `docs/operations/publishing-and-signing-guide.md`
- `docs/operations/client-delivery-update-content-plan.md`
- `docs/operations/deployment-and-access.md` for later sync behavior
- `scripts/release_handoff_metadata.schema.json`
- active client metadata home: `POKROV-app/config/release-handoff.seed.json` and versioned release bundles

## Required v2 contract

The v2 schema must use JSON Schema Draft 2020-12 and discriminate on `schema_version`. It must be strict (`additionalProperties: false`) within v2-owned objects and require:

1. release identity: version, channel, candidate label and UTC creation time;
2. exact repositories/revisions for platform, active client, core and public release index;
3. compatibility: core version/ABI plus versioned app/API contract identifiers;
4. hashes for governed product/release/observability contracts that exist for the candidate;
5. every artifact's platform, kind, architecture where applicable, canonical filename, SHA-256, positive size and source revision;
6. signing state with an allowlisted evidence label; signer/certificate identity when a signed claim is made;
7. SBOM and provenance descriptors or an explicit non-pass state that blocks stable promotion;
8. exact manual gate rows using repository-approved labels without coercing skips, attestations, missing access or manual tests into `PASS`;
9. immutable promotion intent separated from observed promotion evidence.

SHA-256 and Git revisions must have canonical lowercase/uppercase-insensitive input validation and deterministic normalized output rules. No field may contain a secret, raw provider payload, customer identifier or connection material.

## Migration rule

- Existing schema v1 payloads remain valid only through an explicit legacy branch and produce a machine-readable `legacy_v1` classification.
- v1 cannot be used to prove a new 1.2.0 candidate or stable promotion.
- v2 unknown fields, malformed hashes, floats used as sizes, missing compatibility, contradictory signing state and invalid gate labels fail closed.
- The validator is offline and must not fetch remote `$ref` documents or URLs.

## Acceptance oracle

1. Current client `config/release-handoff.seed.json` validates as legacy v1 without being rewritten.
2. One fully synthetic v2 fixture validates and emits normalized summary containing schema version, release identity, source revisions, artifact count and blocking-gate count.
3. Focused negative fixtures/tests reject: missing source revision, malformed SHA-256, zero/float artifact size, duplicate artifact identity, missing core ABI, unknown field, signed claim without signer identity, false `PASS` provenance, invalid/manual-gate status and secret-shaped field value.
4. Validator exit codes distinguish valid v2, valid legacy v1 and invalid payload without printing the input payload.
5. Schema and validator do not make network calls and never log artifact URLs or sensitive metadata on failure.
6. Script is registered in `scripts/manifest.yaml` and its focused tests pass.
7. Existing release gate/orchestrator tests remain green.
8. Publishing and delivery owners explain the v1 migration boundary and state that only v2 can become a new 1.2.0 candidate.
9. `git diff --check`, docs contract/context tests and link check pass.

## Focused verification

```powershell
python -B -m pytest -p no:cacheprovider tests/test_release_handoff_metadata.py tests/test_release_gate_check.py tests/test_release_orchestrator.py tests/test_check_script_manifest.py -q
python -B scripts/validate_release_handoff_metadata.py --metadata-file C:/Users/kiwun/Documents/ai/POKROV-app/config/release-handoff.seed.json --allow-legacy-v1
python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q
python -B scripts/agent_context_packet_audit.py --platform-context-root .
python -B scripts/check-links.py
git diff --check
```

## Triggered proof blocks

- Candidate generation/signing/promotion: `NOT_REQUESTED`.
- Physical device, clean-host Windows, RU-origin, provider dashboard and production origin: `NOT_REQUESTED`.
- Dependency change, if required: must be explicit in the main dependency set and proved by the focused test environment; no CI-only install.

## Completion boundary

`COMPLETE` means the local contract and compatibility validator are proved. It does not mean any client/core consumer has adopted v2, any workflow requires it, a 1.2.0 candidate exists, artifacts are signed, or promotion is allowed.

## Next slice after completion

Add client-owned v2 generation and exact app/core/version parity checks in the active client repository, then wire the strict cross-repository gate without `--allow-missing-client-root` for release-bound workflows.

## Closure record

Result: `COMPLETE` — strict platform contract locally proved; consumer adoption
and candidate proof remain open.

Implemented on 2026-08-21:

- one Draft 2020-12 schema with permissive legacy-v1 and strict v2 branches;
- offline validator with distinct exits: valid v2 `0`, invalid `2`, legacy v1
  migration classification `3`;
- exact source, compatibility, artifact-set, signing, SBOM, provenance, gate,
  same-byte promotion, privacy, and stable-claim semantic checks;
- Core binding corrected against `POKROV-core/config/release.json`: Android
  package plus exact AAR digest, Windows desktop ABI plus exact DLL digest;
- synthetic v2 fixture and planted-secret/mutation/drift tests;
- canonical publishing/delivery migration text and script registry entries.

Validation:

- `PASS` — 39 focused validator/schema/privacy tests;
- `PASS` — release regression: 73 tests and 21 subtests;
- `PASS` — Draft 2020-12 schema check and v2 fixture validation;
- `PASS` — current client `1.1.6` seed validates as schema v1 and the CLI
  returns the expected migration-only exit `3`;
- `PASS` — script manifest, docs contract/context (30 tests), context audit,
  link check, JSON parse, compile, line-length, whitespace and diff checks;
- `PASS` — scoped production/docs/schema/fixture secret scan; secret-shaped
  strings exist only as intentional test vectors.

Manual/runtime/signing/device/RU-origin/provider/deploy/production checks:
`NOT_REQUESTED` for this contract-only WO.

Commit/push/PR/merge/deploy/promotion state: not performed.
