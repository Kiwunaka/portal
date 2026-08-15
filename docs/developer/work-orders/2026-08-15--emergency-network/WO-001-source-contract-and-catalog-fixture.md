# WO-001 — Source Contract And Catalog Fixture

## Metadata

| Field | Value |
| --- | --- |
| WO id | `WO-001-source-contract-and-catalog-fixture` |
| Title | Approved emergency source becomes a bounded, testable data contract |
| Ceremony | `bounded_wo` |
| WO status | `done` |
| Orchestrator | `/root` |
| Repository lane | `platform` |
| Working branch or worktree | `codex/emergency-network` from `master@b093ccd` |
| Intended promotion state | reviewed platform commit, not deployable alone |
| Created / updated | `2026-08-15` |

## Goal

Audit the approved source and mirrors without executing third-party code, define
the exact VLESS+REALITY allowlist schema, and retain a redacted fixture that
proves valid, duplicate, unsafe, malformed and stale input behavior.

## Non-Goals

- Persisting production endpoint credentials.
- Connecting users or promoting a live catalog.
- Importing arbitrary sing-box/Clash JSON.
- Auditing or upgrading POKROV Core.

## Write Scope

- `portal_bot/emergency_catalog_*.py` for pure parsing/normalization only
- `tests/fixtures/emergency_catalog/`
- focused platform tests
- this wave documentation

Collision gate result: platform/client/core clean at wave creation; recheck before writes.

## No-Touch Scope

- production database, runtime environment and third-party repositories
- raw credentials in git, logs, evidence or test names
- `C:/Users/kiwun/Documents/ai/POKROV-core/**`

## Authority Anchors

| Anchor | Why authoritative for this outcome |
| --- | --- |
| `docs/developer/agent-context-map.md` Backend/API row | route, checks and docs ownership |
| `docs/product/portal-vpn-product.md` | active trial/paid and privacy rules |
| approved upstream README/LICENSE | source format, cadence and attribution |
| current `portal_bot` profile builders/tests | exact supported material shape |

## Acceptance Oracle

- Authoritative boundary: normalized catalog item before persistence.
- Success observation: valid VLESS+REALITY becomes one typed record; unsafe or
  unsupported fields are absent or rejected with stable reason codes.
- Negative cases: `allowInsecure`, missing Reality material, RU exit, duplicate,
  arbitrary DNS/route/inbound, unsupported transport and oversized feed fail closed.
- Proof mechanism: redacted fixtures plus focused parser/property tests.
- Limitations: parsing does not prove endpoint reachability or БС behavior.
- Triggered proof blocks: risk proof, mechanism adequacy and attribution.

## Docs Impact

Update the wave and later reconcile the accepted source boundary into the
canonical API/system owner when implementation lands.

## Validation And Evidence

| Check | Command or manual gate | Oracle reached | Target |
| --- | --- | --- | --- |
| fixture/parser | focused `pytest` module selected after file creation | yes | local |
| no raw credentials | added-line secret scan | yes | local |
| source/license | read-only GitHub source and operator agreement note | limited | provider |

## Status And Handoff

- Current WO status: `done`
- Result delivered: strict pure parser, synthetic redacted fixture, stable safe
  projections and trusted fresh non-RU selection gate; see
  [SOURCE-AUDIT.md](SOURCE-AUDIT.md).
- Exact focused check: `12 passed`; combined docs/parser check: `42 passed`;
  scoped `git diff --check` and added-file secret scan: `PASS`.
- Source discovery: six current candidates survive both syntax and advisory
  non-RU classification; no endpoint is yet handshake/payload verified.
- Blockers: none for WO-001; live promotion remains intentionally unavailable.
- Deploy state: not requested.
- Next action: implement snapshot ingestion and controlled verifier boundaries
  in WO-002.
