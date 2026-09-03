# WO-013FV — candidate.31 current/Brain origin and Gate F NO_GO

Status: `EXACT_CANDIDATE31_GATE_F_NO_GO_2_PASS_17_NON_PASS_1_FAIL`

Observed: `2026-09-03T17:46:09Z`–`2026-09-03T17:57:14Z`

Production/public mutation: `NONE`

## Outcome

The first exact candidate.31 origin refresh finds one explicit release failure:
the live Brain payload matches `196/197` files from candidate.31 platform source,
with a content mismatch at `portal_bot/control_panel.py`. The live file does not
match any of the 21 versions of that path reachable from the known local Git
history. No remote content is retained.

Brain's final complete readiness sample passes `23/23`, subscription stability
passes `5/5`, and the final three consecutive enabled-delivery samples pass
`7/7`. Earlier administrative SSH timeouts are retained rather than discarded.
The owner workstation still has an active `sing-tun` default route, so an honest
current-origin result cannot be attributed without changing the owner's network;
that contour is `BLOCKED_BY_ACCESS` and remains untouched.

The regenerated exact-candidate decision is:

```text
NO_GO
required=19
pass=2
non_pass=17
fail=1
validation_errors=0
candidate_validation=PASS
gate_g_authorized=false
```

## Exact boundary

| Item | Identity |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.31`, app `1.2.0+4053` |
| Operational id | `4ee73886c1a285526baf3b666d5845b426754d8bee9f48365d1550a6ece1dd79` |
| Platform | `84837ce68a028f0c81580a5f1beefddba584de6d` |
| Client | `7e3e771fe36333a75244cbfd828c60beb84c7ff1` |
| Core | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Signed release index | `6de47f0320c9262a5bd2d454f3edb83d557f33a4` |
| Manifest | `dd4e99166ac3ec2c566e7d44ee93324f15ae7b3b92df6b35ff35de7053691f9a` |

Candidate validation, signature, supply metadata and the Windows evidence from
WO-013FT/WO-013FU remain valid. This origin failure does not change candidate
bytes; it proves that the currently deployed Brain payload is not the exact
platform source bound by those bytes.

## Brain-origin results

| Check | Result |
|---|---:|
| Exact platform source | `196/197`, one content mismatch, FAIL |
| Final complete readiness | `23/23 PASS` |
| Subscription stability | `5/5 PASS` |
| Enabled delivery sample 4 | `7/7 PASS` |
| Enabled delivery sample 5 | `7/7 PASS` |
| Enabled delivery sample 6 | `7/7 PASS` |

The source mismatch is not normalized line-ending drift. Its path is retained,
but no remote file content, raw host, address, key or response body is stored.

The first readiness attempt loses only `checkout443` to an administrative SSH
timeout. The second loses the `caddy` and `portal-api` unit reads to the same
transport condition. The third complete attempt passes all `23/23`. Delivery
sample 1 returns no inventory after a transient remote operation error; samples
2–6 all pass `7/7`, and samples 4–6 form the retained consecutive final set.
Those transient attempts remain evidence and are not silently removed.

## Current-origin boundary

A read-only adapter and default-route inventory finds an active `sing-tun`
default route. No route, DNS, tunnel, adapter, process, screen, mouse or keyboard
state is changed. Source-address binding would still not prove that traffic
bypassed that route, so no latency or authenticated-egress sample receives
current-origin credit.

## Gate F effect

`current_origin` advances from `NOT_RUN` to `BLOCKED_BY_ACCESS` without PASS
credit. `brain_origin` advances from `NOT_RUN` to `FAIL`. The remaining seventeen
check statuses retain the WO-013FT evidence pointers. The aggregate therefore
moves from `BLOCKED 2/17/0` to exact `NO_GO 2/17/1` with zero validation errors.

This snapshot can be superseded only by new exact evidence. Reconciliation of
the production Brain file requires separate production authorization: either
deploy the exact candidate.31 platform source, or first reconcile a legitimate
runtime change into committed source and create a newly bound candidate. No such
mutation occurs here.

## Verification

```text
remote Brain exact-source probe -> 196/197; one CONTENT_MISMATCH; FAIL
known Git versions of the mismatched path -> 21 scanned; no live match
Brain readiness final complete attempt -> 23/23 PASS; subscription 5/5 PASS
enabled delivery final consecutive samples -> 7/7, 7/7, 7/7 PASS
current-origin route inventory -> active sing-tun default route; BLOCKED_BY_ACCESS
release_1_2_gate_f.py -> expected NO_GO exit 2
candidate_validation=PASS; required=19; pass=2; non_pass=17; fail=1
validation_errors=0
```

## Evidence digests

| File | SHA-256 |
|---|---|
| `013FV-candidate31-current-brain-origin.json` | `6dca7954e458cb0ac4c747d6f539a3bfaf0efe4edabeeb8b8babb53ae71186f1` |
| `013FV-candidate31-gate-f-input.json` | `cfb38c98685526b9e737157b626e2069e681fbed626d094c0f8be7bebc2d7f78` |
| `013FV-candidate31-gate-f-decision.json` | `a19e299888d0db7fcb8f644ec8e11b383f0b43d9585314b336d0120848dd41e8` |

Private raw reports remain under
`E:/POKROV-tools/release-evidence/1.2.0-candidate31-origin-refresh-2026-09-03/`.
No deploy, restart, database write, node mutation, public release, Store
submission, stable-pointer change or Gate G authorization occurs.
