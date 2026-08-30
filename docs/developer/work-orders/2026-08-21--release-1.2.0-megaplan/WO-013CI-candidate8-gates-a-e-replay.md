# WO-013CI — candidate.8 Gates A–E replay and Gate F rehash

Status: `EXACT_CANDIDATE8_GATES_A_E_BLOCKED_ZERO_EXPLICIT_FAILURES`
Classification: `ACTIVE_EXECUTION_EVIDENCE`
Phase: `11`, replaying source-plan Gates `A`–`E`
Candidate: `pokrov-1.2.0-candidate.8`
Production/external mutation: `NONE`; one existing exact-Core failed CI job was
rerun and passed

## Outcome

Replace the stale candidate.3 Gate A–E decision layer with one replay bound to
the signed candidate.8 tuple. The replay keeps every manual, provider, signing,
device, origin and post-promotion boundary non-PASS. It finds zero explicit
candidate.8 defects, removes candidate.3's deterministic Gate B CRLF failure,
and advances Gate C from implementation-only `I2` to locally verified `I3`.

All five gates remain `BLOCKED`; none reaches candidate proof `I4`. Gate F is
rehash-stable and remains `BLOCKED` at `6 PASS / 13 non-PASS / 0 FAIL / 0
validation errors`. No Gate G, tag, public asset, Store object, stable pointer,
provider action or production mutation is authorized.

## Exact candidate identity

| Component | Revision or digest |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.8` |
| Operational ID | `eeedbaf8540a83649a7143d6c7097336429e466118ed4f9ca2b732b7e6e2195a` |
| Platform source | `241a83b4dca00799b39696a4ae0c3c97e087ec39` |
| Client source | `3459438f02bd774e722b1b858e7f7f16d57a9f5c` |
| Core source | `a45d69e40ed7d892619a2b5c4592a527f630665e` |
| Signed release-index source | `b242e0a3060b04f9b71641a0524bf251a75ce2a8` |
| Manifest SHA-256 | `f0006cec90c84e401e9920d9098102c7f50ab5ace5242e0d7683c3df709a6fbc` |
| Signature SHA-256 | `5fcae0675ea45e79baf495859fd170661f5d6dd3a8535275acd4d62680d324f6` |
| Receipt SHA-256 | `4109bb3417b32a780604300055f5308acf7dc810e7ea9c547075e1da41cc21fc` |

The platform and client source worktrees are detached at their manifest-bound
commits; Core `main` equals the manifest-bound commit. All three are clean.
The evidence worktree starts from platform `master` merge `dfaaf04...` and is
separate from the dirty owner root checkout.

## Gate A — release-line security

Decision: `BLOCKED`, remains `I1`.

- exact payment fallback, one-manifest and version/contracts slices pass;
- signed manifest, six-artifact supply chain, SBOM/provenance and Android
  production certificate remain valid;
- exact Core CI run `33232348126`, attempt `2`, passes all five jobs: test,
  release-contract, Android/Windows reproducibility and Apple source build;
- exact platform/client hosted jobs still contain zero executed steps and are
  `SKIPPED_BY_OWNER` under the no-purchase solo exception;
- Windows current-host install, `8/8` files, LocalSystem service,
  authenticated IPC, restart, uninstall and idle network restoration pass;
- connected clean-VM TUN/DNS/egress/recovery and trusted Windows signing remain
  non-PASS. The existing unsigned direct-beta/SmartScreen exception is not
  trusted, Store or broad-stable proof.

The permanent STOP-SHIP registry passes `7/7` local anchors. The read-only
aggregate remains `BLOCKED` because the exact Windows live gate is `NOT_RUN`;
historical solo PR controls pass `3/3` but do not invent independent review or
candidate.8 platform/client hosted execution.

## Gate B — state, Core and false-green truth

Decision: `BLOCKED`, remains `I3`.

The candidate.3 failure is absent in candidate.8. A normal Windows checkout of
exact platform source passes observability, generated-support-reference and
release-handoff tests `70/70`; canonical LF identity is stable. Exact client
state, diagnostics, migrations and bootstrap tests pass `111/111`.

Typed Core source/ABI, reproducible Android/Windows artifacts and the full
hosted Core matrix pass. Physical ordinary, AWG2 and AWG3.1 paths reach green
only after tunnel, managed DNS and selected egress; the observed ordinary
LDPlayer failure stops VPN and remains visibly unprotected. No false green is
observed. Exact Windows connected stop/recovery remains manual, so source and
Android proof cannot close Gate B at `I4`.

## Gate C — shipped platforms

Decision: `BLOCKED`; advances `I2 -> I3`.

Candidate.8 now has enough bounded exact-runtime and source proof for the local
verification level:

- Windows exact setup passes install, `8/8` file identity, service identity,
  authenticated IPC, restart, uninstall and idle route/DNS restore on the
  owner host;
- physical Android passes ordinary/AWG2/AWG3.1 authenticated egress, WARP
  fallback/revoke, selected-app traffic plus excluded control, uplink changes,
  screen-off, Quick Settings/notification, Doze/standby and Private DNS;
- LDPlayer independently proves exact x86_64 install/catalog, ordinary
  fail-closed and AWG2/AWG3.1 selected egress with clean default restore;
- direct APKs and market AAB are manifest-bound under the Android production
  certificate; Linux is deliberately not shipped in candidate.8;
- exact Core CI and artifact reproducibility pass.

Gate C remains below `I4`: Windows live TUN/DNS/AWG/egress/recovery and clean
VM, Android external IPv6/leak, blocked UDP53, external MTU, excluded-app mode,
broader OEM, endurance/accessibility and actual Store delivery remain open.

## Gate D — payments, DB/outbox and bounded services

Decision: `BLOCKED`, remains `I3`.

On exact platform source, the payment/provider/callback/HTTP/DB/outbox/module
matrix passes `196/196` plus `12` subtests in `648.65 s`; the only output is
`20` already-known deprecation warnings. Action Intent and policy/router
ownership pass `25/25` in `92.48 s`. Exact Brain source/readiness/delivery
remain `197/197`, `23/23`, `7/7`.

This proves source behavior and deployed source identity only. No provider
order/callback, PostgreSQL lock/load/pool observation, outbox delivery/retry/
dead-letter, reconciliation/reversal or real operator prepare/execute/status/
rollback path was run. No money, entitlement, customer row or production
service was changed.

## Gate E — UX, accessibility and performance

Decision: `BLOCKED`, remains `I3`.

The exact candidate.8 local quality report passes `15/15`: client analysis and
widget suite, seed/docs contracts, WebApp lint/build/cabinet E2E, marketing
build/SEO/responsive/reduced-motion, admin build and static collection/gate.
Static performance passes `9/9`. Current-origin health and public catalog p95
pass at `66.9959 ms <= 100 ms` and `68.7012 ms <= 200 ms`.

Authenticated cabinet/client journeys, exact physical TalkBack/Narrator/OEM/
scaling, comparable device and artifact regressions, 20-sample browser-lab
performance, support recovery, canonical RU and post-promotion evidence remain
manual. Automated accessibility does not replace a physical screen reader.

## Gate F effect

The new Gate F input binds the prior candidate.8 decision snapshot and this
Gate A–E replay. All `19/19` pointers validate. The decision remains:

```text
BLOCKED
required=19
pass=6
non_pass=13
fail=0
validation_errors=0
gate_g_authorized=false
```

`gates_a_e_exact_candidate` stays `MANUAL_OWNER_TEST` because all five gates
still contain required live/manual evidence. The broad no-open-P0/
false-green/secret-leak row remains `MISSING`: `7/7` known source anchors and
observed fail-closed behavior do not prove unexecuted live gates safe.

## Evidence digests

| File | SHA-256 |
|---|---|
| `013CI-candidate8-gates-a-e.json` | `6fbaacdceb80b97b82dfa1e1f96699acc35c3f3f939d673d3dfc2fbbfb7bcbae` |
| `013CI-candidate8-gate-f-evidence.json` | `1a098f0090b361632e809d7a527fdeb80ff389f51f8cca2a82bffc748a077f8e` |
| `013CI-candidate8-gate-f-input.json` | `a11837124bbcb9e2661001707cde775a20497bd37634c6d8034c0de33667b2f3` |
| `013CI-candidate8-gate-f-decision.json` | `682f133b2d5c7840f6f73fbc2c185f6992df2b61679bb940e6db2b9f22c13b8b` |

The decision digest is the canonical LF digest. `.gitattributes` pins 013CD
and 013CI JSON to LF so upstream Android and current replay hashes reproduce on
Windows checkouts.

## Verification

```text
candidate.8 preflight with current harness -> READY_LOCAL_FREEZE, blockers=0
STOP-SHIP read-only replay -> BLOCKED, local regressions 7/7 PASS,
  exact Windows live gate NOT_RUN
Core Actions run 33232348126 attempt 2 -> 5/5 jobs PASS
Gate B exact platform -> 70/70 PASS
Gate B exact client -> 111/111 PASS
Gate D payment/HTTP/DB/outbox -> 196/196 + 12 subtests PASS
Gate D Action Intent/policy -> 25/25 PASS
candidate.8 retained local quality -> 15/15 PASS, candidate_proven=false
candidate.8 retained static performance -> 9/9 PASS
Gate F -> BLOCKED 6/13/0, validation_errors=0
focused release/docs/context tests -> 78 PASS, 1 deselected known unrelated
  mojibake assertion in ru-origin-probe-handoff.md
platform context packet audit -> PASS
```

The retained Gate F file includes its generation timestamp, so its digest is
verified byte-for-byte from a fresh default Windows checkout while the command
replay writes to a temporary file and is compared semantically. This avoids
pretending that two timestamped decision files should have the same digest.

## Next action

Execute the connected Windows clean-VM matrix without disturbing the owner's
active Hiddify TUN, then finish the remaining physical Android external leak/
MTU/UDP53/excluded-app/OEM/endurance/accessibility slices. Provider, Operator,
legal/commercial, canonical RU, comparable performance and public promotion
stay separate authorization/manual gates. Rerun Gate F after each evidence
advance; never authorize Gate G from this replay.
