# WO-013GG — candidate.32 Gates A–E source replay and isolated rollback

Status: `PASS_EXACT_SOURCE_LOCAL_QUALITY_AND_ISOLATED_ROLLBACK; GATES_A_E_AND_GATE_F_BLOCKED`

Observed: `2026-09-04T00:25:38Z`–`2026-09-04T00:58:00Z`

Production/public mutation: `NONE`

## Outcome

Replay the source-owned portions of Gates A–E against the exact signed
candidate.32 tuple and run the real portal/client pointer mechanisms inside an
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
- fresh npm audits for WebApp, AdminApp and Marketing each report zero findings;
- the signed candidate drives the isolated sequence
  `1.1.6+20260819 -> pokrov-1.2.0 -> 1.1.6+20260819`, with byte-identical portal
  and client restoration and unrelated state preserved.

No host route, DNS, tunnel, VM, emulator, phone, provider, production database,
Operator action, runtime pointer, public asset or stable state changes.

## Gate decisions

| Gate | Decision | Exact remaining boundary |
|---|---|---|
| A | `BLOCKED/I1` | Local STOP-SHIP anchors pass `7/7`; exact Windows live TUN/DNS/egress/recovery, physical Android, hosted platform/client execution and trusted Windows signing remain non-PASS. |
| B | `BLOCKED/I3` | Exact source state/diagnostics contracts pass; connected Windows recovery and physical-device false-green boundaries remain open. |
| C | `BLOCKED/I3` | Signed packages and non-elevated Windows fail-closed proof exist; elevated Windows managed lifecycle, physical Android matrix, Store delivery and conditional Linux package proof remain open. |
| D | `BLOCKED/I3` | Source transaction and policy contracts pass; production provider, PostgreSQL locking/load, outbox delivery/reconciliation/reversal and real Operator rollback remain open. |
| E | `BLOCKED/I3` | Exact local UX/a11y/build/static-performance aggregate passes; authenticated journeys, physical accessibility/OEM/scaling, comparable device/browser performance, support, named origins and post-promotion proof remain open. |

All five gates stay below `I4`. There are zero explicit source failures and no
observed reason to replace candidate.32 from this replay.

## Isolated rollback boundary

The generated strict-v2 handoff SHA-256 is
`4e7054fa3966855942352a9155f69c5148d623752ba819bb5ac50b9799cb43f4` and
binds canonical artifact set
`1392133caa1cb52f59c058a918ba5006d6aefded048fc0927052e4ff51575fb0`.
The retained stable handoff returns byte-identically to
`563dd47835e017363eac63b33d66bdfeb9b41881168d4a14808f1daf48d3569f`.

This strengthens `REL_DOD/DOD-18` and `FE/P12-130` at `I3`. It is not a
runtime pointer/kill rollback, external backup/receipt, current/Brain readback
or post-rollback health proof, so neither row advances to `I4`.

## Gate F refresh

The new Gate F input binds this exact replay plus the prior candidate.32 signed
supply, hosted-check and Windows non-elevated evidence. All `19/19` evidence
pointers validate. The decision remains:

```text
BLOCKED
required=19
pass=2
non_pass=17
fail=0
validation_errors=0
gate_g_authorized=false
```

The count does not rise because source/local success cannot replace live
device, origin, provider, Operator, legal, comparable-performance, runtime
rollback or final attestation rows.

## Verification

```text
candidate.32 source preflight -> READY_LOCAL_FREEZE; blockers=0
STOP-SHIP -> BLOCKED; local regressions 7/7 PASS; Windows live NOT_RUN
Gate B platform -> 70/70 PASS
Gate B client -> 111/111 PASS
Gate D payment/HTTP/DB/outbox -> 196/196 + 12 subtests PASS
Gate D Action Intent/policy -> 25/25 PASS
local quality -> 15/15 PASS
client widgets -> 413/413 PASS
cabinet Playwright -> 69/69 PASS
static performance -> 9/9 PASS
npm audit WebApp/AdminApp/Marketing -> 0/0/0
rollback/PB-14 harness -> 16/16 PASS
candidate.32 isolated rollback -> PASS_LOCAL; byte-identical restore
Gate F -> BLOCKED 2/17/0; validation_errors=0
```

## Evidence digests

| File | SHA-256 |
|---|---|
| `013GG-candidate32-gates-a-e-local-rollback.json` | `84b434a9cda73d303b166271aa347bf28d7306dd942f62cc0c8cb01421f4f986` |
| `013GG-candidate32-gate-f-evidence.json` | `205ffc33a3c21523a4b132eea07d894240b76fcfe5ba4d87225253b0de87f7ae` |
| `013GG-candidate32-gate-f-input.json` | `98150d6c8a64ad064b6f892fd0a2ed007a977e4d9672467d7230d2fe9ddb2b31` |
| `013GG-candidate32-gate-f-decision.json` | `392cb684303ec8d53bc95d92d03ff449d89db43360e2e730e502598be1ce143e` |
| external local-quality report | `aedd182b001cd3849b4cd2fef24a8e7dfce97f39987e2ad37eeca8e56e71b0c9` |
| external rollback report | `8e70ae2ba7ef1c1888d5e2a48ee0c22535fff4f2f6b3ff632778a19f4ff5e8ed` |

External evidence remains under
`E:/POKROV-tools/release-evidence/1.2.0-candidate32-gates-a-e-2026-09-04/`
and the candidate rollback directory. No Gate G, deploy, tag, public release,
Store submission or stable promotion is authorized.

## Follow-up

Use an elevated headless Windows mechanism only if it becomes available
without screen automation. Connect an isolated Android target for the exact
APK matrix. Then refresh current/Brain/RU origins and the remaining provider,
Operator, legal, comparable-performance, runtime rollback and final
attestation rows before recalculating Gate F.
