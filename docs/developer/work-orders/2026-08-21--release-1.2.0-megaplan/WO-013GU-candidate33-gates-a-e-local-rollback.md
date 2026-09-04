# WO-013GU — candidate.33 Gates A–E source replay and isolated rollback

Status: `PASS_EXACT_SOURCE_LOCAL_QUALITY_AND_ISOLATED_ROLLBACK; GATES_A_E_AND_GATE_F_BLOCKED`

Observed: `2026-09-04T09:24:49Z`–`2026-09-04T09:36:00Z`

Production/public mutation: `NONE`

## Outcome

Replay the source-owned portions of Gates A–E against the exact signed
candidate.33 tuple and run the real portal/client pointer mechanisms inside an
isolated disposable fixture. The exact source preflight returns
`READY_LOCAL_FREEZE` with zero blockers and zero pre-freeze rows below `I3`.

The replay finds no source or local-fixture defect:

- Gate B passes platform `70/70`, focused client `111/111` and the full client
  widget suite `413/413`;
- Gate D passes payment/provider/callback/HTTP/DB/outbox/module tests
  `196/196 + 12 subtests` and Action Intent/policy `25/25`;
- declared Node `22.14.0` / npm `10.9.2` / Flutter `3.38.5` local quality
  passes `15/15`, including cabinet Playwright `69/69`, generated Admin v2 SDK
  `75/75` and static performance `9/9`;
- the signed candidate drives the isolated sequence
  `1.1.6+20260819 -> pokrov-1.2.0 -> 1.1.6+20260819`, with byte-identical portal
  and client restoration and unrelated state preserved.

The three package-lock files are byte-identical to candidate.32's locks, whose
retained audit result is zero findings. A fresh candidate.33 WebApp audit
attempt reached the canonical npm audit endpoint but timed out. No fresh
WebApp, AdminApp or Marketing audit result is claimed from that network
failure; the remaining fresh dependency-audit boundary stays explicit.

No host route, DNS, tunnel, VM, emulator, phone, provider, production database,
Operator action, runtime pointer, public asset or stable state changes.

## Gate decisions

| Gate | Decision | Exact remaining boundary |
|---|---|---|
| A | `BLOCKED/I1` | Local STOP-SHIP anchors pass `7/7`; hosted platform/client execution, Core branch enforcement, connected Windows TUN/DNS/egress/recovery, physical Android and trusted Windows signing remain non-PASS. |
| B | `BLOCKED/I3` | Exact source state/diagnostics contracts pass; connected Windows recovery and physical-device false-green boundaries remain open. |
| C | `BLOCKED/I3` | Signed packages and exact `WIN-001` proof exist; connected managed Windows lifecycle, physical Android matrix, Store delivery and conditional Linux package proof remain open. |
| D | `BLOCKED/I3` | Source transaction and policy contracts pass; production provider, PostgreSQL locking/load, outbox delivery/reconciliation/reversal and real Operator rollback remain open. |
| E | `BLOCKED/I3` | Exact local UX/a11y/build/static-performance aggregate passes; authenticated journeys, physical accessibility/OEM/scaling, comparable device/browser performance, support, named origins and post-promotion proof remain open. |

All five gates stay below `I4`. There are zero explicit source failures and no
observed reason to replace candidate.33 from this replay.

## Isolated rollback boundary

The generated strict-v2 handoff SHA-256 is
`6555bd6f086f30a85e2f4c543b3f8b9ce1bf5eecdec2de95a0fa43003c33ce06`
and binds canonical artifact set
`1858db3491effa6224d3816763f7bd90a16429ae6b21c6fc97275d84f5d31978`.
The retained stable handoff returns byte-identically to
`563dd47835e017363eac63b33d66bdfeb9b41881168d4a14808f1daf48d3569f`.

This refreshes `REL_DOD/DOD-18` and `FE/P12-130` at `I3`. It is not a
runtime pointer/kill rollback, external backup/receipt, current/Brain readback
or post-rollback health proof, so neither row advances to `I4`.

## Gate F refresh

The new Gate F input binds this exact replay plus WO-013GT candidate.33 signed
supply, hosted-check and Windows focus evidence. All `19/19` evidence pointers
validate. The decision remains:

```text
BLOCKED
required=19
pass=2
non_pass=17
fail=0
validation_errors=0
gate_g_authorized=false
```

The aggregate Gates A–E row changes from `NOT_RUN` to
`MANUAL_OWNER_TEST`, isolated rollback changes its row from `NOT_RUN` to
`MANUAL_OWNER_TEST`, and comparable local performance replaces its `NOT_RUN`
state with `MANUAL_OWNER_TEST`. These are still non-PASS labels, so the count
does not rise.

## Verification

```text
candidate.33 source preflight -> READY_LOCAL_FREEZE; blockers=0
STOP-SHIP -> BLOCKED; local regressions 7/7 PASS; Windows live NOT_RUN
Gate B platform -> 70/70 PASS
Gate B client -> 111/111 PASS
Gate D payment/HTTP/DB/outbox -> 196/196 + 12 subtests PASS
Gate D Action Intent/policy -> 25/25 PASS
local quality -> 15/15 PASS
client widgets -> 413/413 PASS
cabinet Playwright -> 69/69 PASS
static performance -> 9/9 PASS
fresh npm audit -> BLOCKED_BY_ACCESS_NPM_REGISTRY_TIMEOUT; no PASS claimed
rollback/PB-14 harness -> 16/16 PASS
candidate.33 isolated rollback -> PASS_LOCAL; byte-identical restore
Gate F -> BLOCKED 2/17/0; validation_errors=0
```

## Evidence digests

| File | SHA-256 |
|---|---|
| `013GU-candidate33-gates-a-e-local-rollback.json` | `f183d82a89184443dfeef9d473ade8349ae50196aa2f579afe899be05b8386a4` |
| `013GU-candidate33-gate-f-evidence.json` | `03c8a7241bbb0aa2fa1a7cfdf28f293b7318eed7f29580b4750ee959e89d9638` |
| `013GU-candidate33-gate-f-input.json` | `4d1279962f783e404115b7fc4c9162f8c37922986d89a65e22063e72cd80054c` |
| `013GU-candidate33-gate-f-decision.json` | `6f51e4968c749403e6d446b79f7dac1a431872f36361ec49ea1286a530fadc18` |
| external source preflight | `cffdc9976363dffa9298fe28c85f20898b01a52219c86256cc74af597955d9b2` |
| external STOP-SHIP report | `f7e874f56d7a5145b6b3b7c9fdbf45292812d53b762b86b32d7ad5855d695feb` |
| external local-quality report | `bf14b540a0f1242caa8be4e860480ca3b74043376a6549e42e1bca37fc7b7934` |
| external rollback report | `2f1207c96788c28300220676c78c80a03193de8eb1f39cf2a425331b6fc28dcf` |

External evidence remains under
`E:/POKROV-tools/release-evidence/1.2.0-candidate33-gates-a-e-2026-09-04/`.
No Gate G, deploy, tag, public release, Store submission or stable promotion is
authorized.

## Follow-up

Use the isolated Windows VM for candidate.33 connected default, AWG3.1, AWG2
and Smart-DNS lifecycle without taking host input or host network control.
Then run the exact Android emulator/physical-device matrices and refresh the
named origins, provider, Operator, legal, comparable-performance, runtime
rollback and final attestation rows before recalculating Gate F.
