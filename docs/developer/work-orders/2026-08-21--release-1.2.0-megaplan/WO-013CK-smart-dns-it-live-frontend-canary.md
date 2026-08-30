# WO-013CK — Smart DNS `it` live frontend canary

Status: `POST_CANDIDATE_IT_FRONTEND_APPLY_ROLLBACK_REAPPLY_PASS_SMART_DNS_NOT_INSTALLED`
Classification: `ACTIVE_EXECUTION_EVIDENCE`
Phase: `10`; Gate F impact is retained separately
Candidate: `pokrov-1.2.0-candidate.8` remains immutable
Live platform source after candidate: `9dee5491ac70cee3e82f776f7601430639c94d1b`

## Outcome

Advance the preferred no-purchase Smart DNS topology from source-only PLAN to
a bounded live transport-front canary on the foreign `it` node. The exact
legacy Xray/Reality inbound now remains the HAProxy default route on public
TCP/443 while Xray listens on loopback TCP/10443. Current-origin and
Brain-origin TCP/443 checks pass after APPLY, after explicit receipt-bound
ROLLBACK and after guarded re-APPLY.

Smart DNS itself is **not installed**. Loopback TCP/18443 is free and the exact
fronted server bundle passes PLAN, but runtime material is absent and no public
DoH hostname, certificate or DNS record exists. This work therefore proves
transport placement and rollback only, not DoH answers, ChatGPT/Gemini/Xbox
access, privacy/leak behavior, RU-origin access or release readiness.

## Source corrections before live success

The first two attempts exposed operation defects without leaving the frontend
active:

1. The initial APPLY failed while creating the remote staging file. Paramiko
   4.0 maps exclusive create separately from write; opening with `xb` did not
   grant write access. Platform PR 88 changed the mode to `x+b`, added a
   focused fake-SFTP regression and records mutation intent before staging.
   No dataplane mutation occurred; the one empty staging directory was
   verified and removed.
2. The next APPLY completed the compare-and-swap and restart but checked the
   listener before Xray became ready. Its automatic rollback restored direct
   Xray TCP/443, while the receipt conservatively reported rollback failure.
   Platform PR 89 added bounded listener-readiness waits to APPLY and both
   rollback paths, avoids disabling a frontend that was never installed and
   removes only operation-owned HAProxy state.

PR 88 merged as `9284ca80b7e38794d35a744429ba99e9aba04b47` and PR 89 as
`9dee5491ac70cee3e82f776f7601430639c94d1b` under the retained
`OWNER_SOLO_EXCEPTION`. Their private hosted checks executed zero steps and
remain `SKIPPED_BY_OWNER`; local and remote bounded evidence is not relabelled
as hosted CI.

## Live frontend proof

The corrected operation produced this sequence:

```text
guarded APPLY                 -> PASS
current-origin TCP/443        -> PASS
Brain-origin TCP/443          -> PASS
explicit rollback PLAN        -> PASS
explicit rollback APPLY       -> PASS, receipt state rolled_back
post-rollback current-origin  -> PASS
post-rollback Brain-origin    -> PASS
guarded re-APPLY              -> PASS
```

During the proven rollback, direct Xray ownership of TCP/443 was restored,
HAProxy/frontend files were removed and loopback TCP/10443 and TCP/18443 were
free. The final current state is HAProxy on public TCP/443, the exact legacy
Xray backend on loopback TCP/10443 and free loopback TCP/18443. The Smart DNS
service, unit, runtime config and release targets remain absent.

## Exact Smart DNS readiness

The server input is rebuilt twice from exact source
`650dc3fab8053736cfb976d4a34ea1f2f0b40349` with Go `1.25.13`:

| Property | Result |
|---|---|
| Independent Linux/amd64 bundles | byte-identical |
| Bundle size | `2916305` bytes |
| Bundle SHA-256 | `cda97da16a892c1a8563bd20434cd749a2174c192ba722147091a3e1c14a0225` |
| Fronted install PLAN | `PLAN_READY_RUNTIME_MATERIAL_MISSING` |
| Loopback TCP/18443 | free |
| Mutation performed by PLAN | `false` |
| Smart DNS installed | `false` |
| DNS hostname published | `false` |

The PLAN proves root/tools/UFW readiness, unique owned public IPv4 and absent
targets. APPLY remains fail-closed until the owner chooses a public DoH name,
authorizes its DNS publication and a trusted certificate plus root-only
runtime configuration are materialized outside Git.

## Beeline whitelist differential

While the owner explicitly enabled the Beeline whitelist condition, the exact
candidate.8 physical device was checked over mobile data with Wi-Fi, Private
DNS and VPN disabled. A bounded TCP differential returned:

| Target class | Result |
|---|---|
| Beeline carrier control | `PASS` |
| allowed RU control | `PASS` |
| POKROV control/API TCP/443 | `TIMEOUT` |
| `ru_spb` TCP/443 | `TIMEOUT` |

This is `BOUNDED_TCP_DIFFERENTIAL_ONLY`. It proves that the physical carrier
path works while the current POKROV control endpoint and `ru_spb` are filtered
before VPN/TLS. It does not identify an AWG defect and does not prove every
carrier whitelist category. Direct `it` is not a bootstrap solution for this
specific whitelist condition; a separately designed allowed/CDN emergency
ingress would be required.

Termux was used only for bounded TCP probes with shell history disabled. Raw
node addresses, device identifiers and runtime material were not retained.
Temporary screenshots were inspected and deleted. The POKROV app was stopped,
no VPN was left active, Private DNS remained off and the owner's foreground
Hiddify state was restored.

## Evidence and verification

The normalized summary has SHA-256
`2d8eaca8acceb13461381c5643e45c408a75140a9f79cf554e0e7391d9226516`.
Its constituent sanitized reports include:

| Evidence | SHA-256 |
|---|---|
| Corrected initial PLAN | `72d768dd20633b8caab80173d8b985359b012c90b0f9aa72b98e9b319b63fb83` |
| Initial staging failure | `42250d3bdde7a5af70ceb996766b29ef16199769d6d281620e0f7544f1121cee` |
| Readiness-race failure | `fd7d60eafbc0ff8570610b0b7f70c1c7bf09044ca55b45fff5a4757af2d0d6fb` |
| Corrected guarded APPLY | `3d881420f275da0f77dbd0175dbee5e87ef6c7192216a15792fa09596ef53e42` |
| Explicit rollback PLAN | `263bb3b2a5101f8457b753ebe84d4a8e4a6e6abb83e966daf3fd95a405b8af6f` |
| Explicit rollback APPLY | `a9ecd45ccbdcd453422c358464b541a90cbb808a506eb8ecb2576cb1cacf2e2a` |
| Guarded re-APPLY | `1764f789a35c7deb8f3bcc2bc692e55c3d3b0914f872b68495282f511b517ad5` |
| Smart DNS server PLAN | `4f91c4b046d02bebbac96868364cd9ee7f5083d6ef37f98992c02646d6923831` |
| Beeline whitelist differential | `e697c96eba32f738bd24b1a13e84649152efa9fffd37cedc8d43f83fa6761c38` |

```text
transport/fronted focused tests -> 27 PASS
release-operation suite         -> 44 PASS + 21 subtests PASS
remote APPLY shell syntax       -> PASS
remote ROLLBACK shell syntax    -> PASS
documentation/context tests     -> 31 PASS, 1 known unrelated mojibake
                                   assertion in ru-origin-probe-handoff.md
platform context packet audit   -> PASS
git diff --check                -> PASS
```

The unrelated documentation failure is retained honestly: the failing
assertion targets pre-existing mojibake in `ru-origin-probe-handoff.md`, which
this work order does not modify.

## Release interpretation

`FRKN_SMART_DNS/SMARTDNS-01` remains `I3`. Its frontend APPLY and live
transport rollback gaps are closed on one foreign canary, but runtime deploy,
real DoH/service sessions, attribution, leak/lifecycle and required origins
remain open.

Signed `pokrov-1.2.0-candidate.8` is unchanged. Gate F remains `BLOCKED` at
`6 PASS / 13 non-PASS / 0 FAIL`; this post-candidate runtime evidence cannot be
silently inserted into its signed source tuple. No tag, public release, store
object, stable pointer or Gate G authorization was created.

## Required next evidence

1. obtain the owner's explicit public DoH hostname/DNS authorization;
2. materialize a trusted certificate, key and exact root-only runtime config;
3. run guarded Smart DNS server PLAN/APPLY and then the separate frontend route
   PLAN/APPLY with current transport checks at each boundary;
4. prove exact DoH behavior and real ChatGPT/Gemini/Xbox access, attribution,
   privacy/leak, lifecycle and receipt-bound rollback from required origins;
5. keep the Beeline whitelist emergency-ingress design separate from direct
   `it` Smart DNS deployment;
6. bind any shipped source/runtime change to a successor candidate instead of
   relabelling immutable candidate.8.
