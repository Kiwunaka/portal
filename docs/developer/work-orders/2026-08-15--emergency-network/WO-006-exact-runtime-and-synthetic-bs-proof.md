# WO-006 — Exact Runtime And Synthetic BS Proof

## Metadata

| Field | Value |
| --- | --- |
| WO id | `WO-006-exact-runtime-and-synthetic-bs-proof` |
| Title | Exact Core 1.0.3 and an isolated firewall lab prove all emergency paths |
| Ceremony | `release_wo` |
| WO status | `closed_with_manual_gate` |
| Orchestrator | `/root` |
| Repository lane | `mixed` with core read-only |
| Working branch or worktree | platform/client feature branches; core `main` read-only |
| Intended promotion state | evidence gate for WO-007 |
| Created / updated | `2026-08-15` |

## Goal

Prove the exact materialized direct, two-hop and three-hop profiles using the
shipped POKROV Core 1.0.3, then reproduce a controlled БС-like condition in an
isolated Android/LDPlayer and Windows lab where RU control origins remain
available and selected foreign/normal POKROV first hops are blocked.

## Non-Goals

- Scanning or attacking unrelated networks/services.
- Global firewall changes on the operator workstation.
- Disabling Hiddify or claiming synthetic lab equals real carrier БС.
- Core source changes or version upgrade.

## Write Scope

- platform/client test harnesses and fixtures
- isolated lab scripts/config under an exact bounded test owner
- evidence under `docs/audit-artifacts/` and external heavy evidence on E:
- this WO status

## No-Touch Scope

- `C:/Users/kiwun/Documents/ai/POKROV-core/**` writes
- host-wide default route, DNS, Hiddify process or persistent Windows firewall
- third-party credentials or raw user traffic in retained evidence

## Authority Anchors

Core 1.0.3 release decision and binary; managed profile from WO-004; client from
WO-005; official sing-box detour/schema behavior; origin/evidence rules.

## Acceptance Oracle

- Authoritative boundary: exact candidate TUN plus deterministic controlled payload.
- Success observation: each mode reaches the expected exit and retrieves the
  expected payload hash; DNS follows the intended hop; disconnect restores the
  isolated environment; API outage uses valid LKG; reconnect does not reuse a
  stale reserve.
- Negative cases: cycle, missing hop, wrong foreign exit, local-DNS dependency,
  invalid signature, blocked reserve, WARP presence and stale snapshot fail closed.
- Proof mechanism: exact-core config check/start, local controlled endpoints,
  packet/route/DNS assertions, LDPlayer and isolated Windows runtime smoke.
- Limitations: synthetic firewall cannot produce `Проверено при реальном БС`.
- Triggered proof blocks: MREP, risk proof, mechanism adequacy, manual gates,
  validation attribution and promotion evidence.

## Docs Impact

Client bootstrap/runtime docs, platform monitoring/origin owner, this wave and
candidate-specific evidence only.

## Validation And Evidence

Evidence records must bind platform/client/core commits, candidate hashes,
catalog revision, reserve stable ID, route mode, firewall policy hash, payload
hash, DNS/route/exit verdict and teardown result without secrets.

Manual result remains `MANUAL_OWNER_TEST_REAL_RU_BS` until owner runs exact LTE.

## Status And Handoff

- Current WO status: `closed_with_manual_gate`
- Dependencies: WO-004, WO-005
- Exact Windows adapter pins the shipped Core 1.0.3 DLL; the Linux probe adapter
  pins the embedded sing-box 1.13.0 engine. Both reject non-allowlisted
  VLESS/REALITY shapes, missing country proof and payload mismatch.
- Exact Windows adapter still pins Core 1.0.3 SHA-256
  `7cc83854fc4022b759e9de3d0942b90a24c859cfd51e3231d04e7c7a6b7d5054`.
  The final synthetic controller result is `BLOCKED_BY_ACCESS`: the controlled
  fixture manifest and isolated executor are unavailable. It did not change the
  Windows firewall or Hiddify.
- Production-signed Android 1.0.10 in LDPlayer loaded the live signed catalog,
  rendered five active reserves and materialized all three route shapes. The
  direct emergency route reached a healthy selected-outbound proof. The
  two-hop and three-hop routes established TUN and passed every hop TCP
  preflight, then failed closed on the same Reality handshake limitation as the
  normal POKROV control profile in this emulator/network path.
- Sanitized three-hop runtime evidence proves
  `reserve -> owned RU -> owned foreign`; detoured hops do not receive a local
  `domain_resolver`, and emergency DNS uses DoH through the final chain.
- Exact browser payload/exit proof in LDPlayer is therefore
  `BLOCKED_BY_ACCESS`, not PASS. Real LTE remains
  `MANUAL_OWNER_TEST_REAL_RU_BS` before any real-BS badge or carrier claim.
