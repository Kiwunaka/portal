# WO-013GQ — candidate.32 Windows singleton/focus NO_GO and successor correction

Status: `NO_GO_EXACT_CANDIDATE32_WIN_001; PASS_PRE_CANDIDATE_SUCCESSOR_FOCUS`

Observed: `2026-09-04T03:50:48Z` through `2026-09-04T04:15:55Z`

Production/public mutation: `NONE`

## Outcome

The exact signed candidate.32 Windows UI passes the singleton and typed
forwarding portions of `REL/WIN-001`, but fails its required focus behavior.
From an independent foreground control window, both plain and typed second
launches exit `0` and retain exactly one original UI process, yet the existing
window does not regain foreground focus.

Candidate.32 is therefore immutable `NO_GO`. Its application files, signed
manifest, detached signature and receipt are not rewritten or re-signed.

## Exact candidate boundary

| Item | Identity |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.32`, app `1.2.0+4053` |
| Platform | `d0dd37c1003198ba08cffc49a040a77e21621a86` |
| Client | `2d6adfcebc37f2109ef339276be6a1569cb7aa1e` |
| Core | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Signed release index | `5d11fd6821a5ebfa42163f461332125143c553c3` |
| Installed UI | `611208b20b68b333d81655b0d6dbd7ada3a213fbfd9a82b6af71b01b3bdf15a2` |
| Exact runtime result | `FAIL_EXACT_CANDIDATE32_SECOND_LAUNCH_FOCUS_NOT_RESTORED` |

The final exact-candidate raw record is
`candidate32-singleton-focus-final.json`, SHA-256
`46cab10a7a64fbc1c934f7762bad0d62826e404ded7c591fcf96100bf1fb2a28`.
The canonical harness SHA-256 is
`7bacd820696da7a35db922b214b6511e9eeee7b7a6537e7e3ae22584cc072178`.

## Cause and source correction

Candidate.32's foreground-launched second process sends `WM_COPYDATA`, while
the existing process restores its window and calls `SetForegroundWindow`.
Windows can still deny that request because the existing process does not own
the foreground activation permission.

Client commit `76abed9056282df6436fbd8734f8093baabdb711` keeps the existing
mutex, typed frame and `WM_COPYDATA` path. Before forwarding, the new process
resolves the existing window's process id and calls `AllowSetForegroundWindow`
for that process. The existing process then uses its unchanged restore/focus
handler.

Verification against that source:

- focused Flutter Windows release contract: `8/8 PASS`;
- native Release CTest: `7/7 PASS`;
- Windows Release build: `PASS`, UI
  `1ac2bb3135b66930bfbbb7d6cd0b5fc319bad5c56fe62c8f7b7af848caabcdb9`,
  `192512` bytes;
- ordinary medium-integrity Windows 11 VM: plain and typed second launches
  each exit `0`, retain one original PID and return foreground focus;
- adapter, route and DNS counts remain unchanged.

The corrected runtime record is `successor-singleton-focus-final.json`,
SHA-256
`a7b08b9ad0aac97199adb0acbee666dea2cff22d39a387043f33e4c66e755268`.
The first successor attempt is retained as a harness process-enumeration race,
not a product failure; no product source changed for its replay.

## Cleanup and evidence ceiling

The successor UI was staged under a separate filename and never replaced
candidate.32. The bounded elevated removal passes, candidate.32's installed UI
hash remains exact, its service was `Running`, the guest staging directory was
removed and the VM was powered off. No host screen, input, route, tunnel or DNS
setting was used or changed.

This is `PASS_PRE_CANDIDATE_LOCAL` only. A newly numbered exact candidate must
rebuild and package the correction before receiving any candidate runtime or
promotion credit.

## Gate F

The exact candidate failure changes two of the 19 aggregate checks:

- `gates_a_e_exact_candidate`: `FAIL`, because Gate A contains the failed
  exact-candidate STOP-SHIP boundary;
- `mandatory_stop_ship_and_dod`: `FAIL`, because `WIN-001` fails on exact
  candidate bytes.

`no_open_p0_false_green_or_secret_leak` remains `MISSING`; this work order does
not assign a separate P0 classification. `windows_live_network` remains
`MANUAL_OWNER_TEST` because the focus result does not prove or disprove managed
TUN/DNS/egress.

The regenerated exact decision is:

```text
NO_GO
required=19
pass=2
non_pass=17
fail=2
validation_errors=0
gate_g_authorized=false
```

All completion-index levels remain unchanged. Seven current status rows now
carry the exact `NO_GO`; all `57` future-action fields that previously targeted
candidate.32 are reconciled to immutable-history or successor-candidate work.
The eight remaining candidate.32 mentions in `next_action` explicitly say to
keep or not rewrite the rejected bytes. `REL/WIN-001` stays `I3` for verified
local implementation, but candidate.32 receives no `I4` credit.

## Evidence

| File | SHA-256 |
|---|---|
| `013GQ-candidate32-windows-singleton-focus-no-go.json` | `f337599e36b7279aa4b5b6a9d4a99d79e7f6144df06c4855460bb942b66fe6c1` |
| `013GQ-candidate32-gate-f-evidence.json` | `1c8bb9cd4e929b8cbefe6c1939b773ea92273cf01c132bef96ad306e4595b4d6` |
| `013GQ-candidate32-gate-f-input.json` | `98002efb28a67915f86214ee440ed1c815903977231327a1a39d9acd161620bb` |
| `013GQ-candidate32-gate-f-decision.json` | `8758fa201760970cb4823e8dac3435d862a52effacdb72d511ab79a780f47b29` |

Raw evidence is retained under
`E:/POKROV-tools/release-evidence/1.2.0-candidate32-windows-singleton-focus-2026-09-04/`.

## Follow-up

Keep candidate.32 immutable. After separate candidate-creation authorization,
assemble a newly numbered exact candidate from the corrected client source and
repeat `WIN-001` plus the remaining applicable Windows, Android, origin,
rollback, approval and final Gate F rows. No deploy, public release, Store
submission, stable-pointer change or promotion is authorized by this result.
