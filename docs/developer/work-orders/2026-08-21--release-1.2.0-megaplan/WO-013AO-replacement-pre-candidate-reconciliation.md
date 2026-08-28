# WO-013AO — Replacement pre-candidate reconciliation

Date: `2026-08-28`

Status: `LOCALLY_PROVED_PRE_CANDIDATE / HOSTED_CHECKS_BLOCKED`

## Objective

Reconcile the current post-candidate source line after the Gate B correction,
owned AWG/DNS lab work and Android Core rebinding without transferring any of
that evidence into signed `candidate.3` or creating a replacement candidate.

## Exact implementation and evidence tuple

| Lane | Revision | Branch / PR | State |
| --- | --- | --- | --- |
| Platform runtime | `e5ef03ac7ab013d8810cc9c6ea9ccc40cebd11db` | `codex/awg-owned-lab-deploy`, PR `#58` to `master` | locally gated runtime source |
| Platform AWG operations/evidence | `39af0f1d3a01209bd46dcd0661cabef5de679efe` | same branch / PR | focused checks passed; pushed after the aggregate gate |
| Platform AWG managed issuance | `32e444695432531d7a1a517cb0386bb690c73969` | same branch / PR | local source correction; `53/53` focused and `154 + 8 subtests` backend pass; not deployed |
| Client runtime | `c196dff6bf72c325d5bba675fe19342cd3821f61` | `codex/release-1.2.0-candidate-8-source`, PR `#33` to `main` | locally gated runtime source |
| Client AWG evidence docs | `2eeee5fa0c09096426e09aeb0eeb865a6aede981` | same branch / PR | docs/seed contracts passed; pushed after the aggregate gate |
| Core | `f44dbe89d6b89954032a1a798c2209d8c0aff90d` | `codex/fix-egress-event-subsystem`, PR `#6` to `main` | clean and pushed |

This tuple is `PRE_CANDIDATE_LOCAL`. It is not signed, promoted, public or
stable. Signed private `candidate.3` remains the exact-candidate authority and
remains `NO_GO`.

## Android Core provenance reconciliation

Core Android was built twice from `f44dbe89d6b89954032a1a798c2209d8c0aff90d`.
Both AARs were byte-identical with SHA-256
`ca391059b6676de5a2cfbf582395fd7ab0b0b5979c8a0c40faaa7208b79178e5` and
size `107394593` bytes. The bytes also match the client AAR previously built
from `54e76bbb...` because the intervening Core commit changes tests only.

The client seed, validation fixtures and canonical client release documents
now bind Android source provenance to `f44dbe89...`; no runtime binary changed.
Windows remains bound to its separately declared Core revision and artifact.

## Current local quality evidence

The aggregate local gate ran with exact Node `22.14.0` against platform runtime
`e5ef03ac...`, client runtime `c196dff...` and Core `f44dbe89...`. All `15/15`
steps passed:

- performance contract and `30/30` contract tests;
- Flutter analysis and `400/400` app-shell tests;
- client seed, release-v2, documentation and repository-hygiene contracts;
- WebApp lint/build and `69/69` cabinet Playwright tests;
- marketing build, SEO, responsive, accessibility and reduced-motion checks;
- AdminApp production build;
- local static performance collection and required gate `9/9 PASS`.

The private local report `010I-local-quality-gate.json` has SHA-256
`facc6b09b7ad94768c59f946d7164adbc7c229a6de605fa958bdc20bb5599e6e`.
It explicitly records `candidate_proven=false`, `local_status=PASS` and
`promotion_status=MANUAL_OWNER_TEST`. Exact candidate/device performance,
artifact comparison, selected browser lab, authenticated controlled-origin
API work and signing/device/origin proof remain non-PASS manual lanes.

The later AWG operations/evidence commits do not change platform or client
runtime behavior. They pass `47/47` focused AWG/smart-connect tests, `32/32`
platform documentation tests, platform-context audit, client seed validation,
client docs contract and both diff/secret checks. The full aggregate gate was
not relabeled or rerun against those documentation/operations heads.

## Owned AWG and DNS physical slice

The retained
[physical pre-candidate record](../../../audit-artifacts/2026-08-28-owned-awg-dns-physical-pre-candidate.md)
binds production-signed working Android package `1.2.0+4044` without treating
it as a candidate.

- AWG2 and randomized-trailer AWG3.1 live server/client alignment pass.
- On physical Beeline, both guarded UDP controls reached the server and were
  echoed `3/3`, while the phone received `0/3`. Both handshakes therefore stay
  `BLOCKED_BY_NETWORK_CURRENT_ORIGIN`; this is not a cryptographic failure or
  universal transport verdict.
- Explicit no-carrier readback selected AWG2 for the exact physical and
  LDPlayer identities, but build 4044 on Wi-Fi and build 4043 on LDPlayer
  emitted no AWG traffic. LDPlayer also rejected the selected Frankfurt
  location before tunnel start. This is `FAIL_WORKING_CLIENT_ACTIVATION` and
  blocks another AWG3.1 device loop until the common client path is fixed.
- Direct HTTPS DoH returned valid responses for the bounded AI/Games set.
  Product routes still require the VPN, so DNS-only ChatGPT/Gemini/Xbox access
  remains `NOT_IMPLEMENTED` and would be a separate Smart-DNS architecture.
- Normal WARP plus independent IP and DNS egress passed after exact lab unbind.

Post-observation source review located the first common activation blocker in
the platform managed-profile route: device-bound `awg2_lab` and `awg31_lab`
material was selected correctly, but issuance still passed through the
ordinary Smart Connect/node shortlist and could return `503 No eligible nodes`
before the typed endpoint reached the client. The route now bypasses that
unrelated catalog for both owned labs, ignores `selected_node_code` and returns
`smart_connect: null`; all device/material/rollout/server gates remain
fail-closed. Focused network regressions pass `53/53`, the router-mandated
backend suite passes `154` tests plus `8` subtests, and documentation contracts
pass `32/32` with platform-context and diff checks. This is
`PASS_LOCAL_SOURCE`, not deployed-device proof, and does not relabel the
retained 4044/4043 failures.

## Working build 4045 correction slice

Client runtime source `51f41c646796e506d9d329ce54e8cc15fb7dfa7b`
demotes an Android `running` snapshot when the app-owned TUN is absent. It
preserves the staged configuration for retry, clears stale Core egress truth
and records `service_destroyed`. Direct and Store Android unit matrices pass
`179/179` each, Flutter analysis is clean, app-shell tests pass `400/400`, the
client docs contract passes and cross-repository seed validation projects
`1.2.0+4045` consistently into platform head
`34d1551f9c732ed879629a768d8825cc694f435c`.

Production-signed working APKs from that exact client source were verified and
installed without declaring a candidate:

- arm64 `1.2.0+4045`, SHA-256
  `8e3c45df8db2582f1a29a1f49776f45da5a0420391f584b892f66e4a7947eddf`,
  installed on the physical Huawei;
- x86_64 `1.2.0+4045`, SHA-256
  `0d76ee15fb9b1519cb8f92940cce315fbe3a1b485aaa44625a8f75623f1cc786`,
  installed on LDPlayer.

Both hosts cold-started without the app-owned VPN service and reported
`Подключить` / `Не защищено`; the physical Wi-Fi state remained disabled.
This is `PASS_4045_DISCONNECTED_HOST_TRUTH`. It closes the stale-running
false-green regression only. It does not prove AWG2/AWG3.1 handshake, tunnel
egress, DNS/leak behavior, endurance or release readiness, and the paired
platform managed-profile correction is still not deployed.

A subsequent bounded physical connect control started the POKROV service but
produced no Android VPN transport after approximately `25` seconds. The UI
tree was unavailable before a post-connect label could be retained, so DNS and
HTTPS were not run. Exact cleanup stopped POKROV, confirmed no Android VPN
transport, foregrounded Hiddify and preserved disabled Wi-Fi. Record this as
`FAIL_4045_PREDEPLOY_ANDROID_ACTIVATION`; it still precedes deployment of the
managed-profile correction and is not an AWG cryptographic verdict.

An independent LDPlayer connect control reached canonical
`core_egress_probe_failed`: the selected outbound did not pass internet proof,
so POKROV stopped the system VPN fail-closed and exposed the safe retry state.
There was no VPN-permission prompt, residual POKROV service or VPN transport
after cleanup. No AWG policy was bound and no server policy was mutated, so
this is `FAIL_4045_LDPLAYER_SELECTED_OUTBOUND_EGRESS`, not AWG tunnel evidence.

The full bounded local quality gate was then repeated on exact clean platform
`9383117794f9ee17b5976204c3b8601732464c17`, client
`f3d3310f520156cbb07a8993fbe485cf599a174f` and unchanged Core
`f44dbe89d6b89954032a1a798c2209d8c0aff90d` under declared Node `22.14.0`.
All `15/15` steps pass, including Flutter `400/400`, cabinet E2E `69/69` and
local static performance `9/9`. Private report SHA-256 is
`57ca935298957ec88f86f118441acc8611fe1a044af879c0038b3074964f02ed`.
It explicitly records `candidate_proven=false`, `local_status=PASS` and
`promotion_status=MANUAL_OWNER_TEST`; it does not convert the predeploy device
failure or any external/manual lane to PASS.

Read-only Brain source probes now bind the exact change window. Current live
runtime `e5ef03ac...` matches `193/193` deploy-payload files; report SHA-256 is
`2be21f11...26c6c`. Corrected runtime source `716186a...` matches `192/193` and
differs only at `portal_bot/api_client_routes.py`; report SHA-256 is
`410d7cff...556a` with `runtime_mutated=false`. Deploy/source-probe/release-op
tests pass `57` tests plus `25` subtests. The authorized plan restarts only
`portal-api`, requires staging/backup/preflight, delayed active+zero-restart
health, automatic rollback on deploy failure and a postdeploy `193/193` source
readback before any AWG device binding. No deploy or runtime mutation occurred.

## Hosted PR evidence

Exact jobs observed for platform PR `#58` at `34d1551f...` and client PR `#33`
at `2f47148e...` received zero execution steps although both PRs were
mergeable. GitHub
reports failed account payments or a spending-limit block. They are
`BLOCKED_BY_ACCESS_GITHUB_BILLING`, not product test failures and not passes.
`OWNER_SOLO_EXCEPTION` does not waive them.

Core PR `#6` passes `test`, Android artifact reproducibility, Windows artifact
reproducibility and Apple source build. Its `release-contract` job fails
closed because client `main` still binds the prior Core source; the current
client PR contains the exact `f44dbe89...` binding but is not merged.

No PR is merged while these required checks are unresolved. No deploy,
candidate creation, public asset, stable pointer or production mutation occurs
in this work order.

## Ledger decision

`FRKN_PLAN/W3-01` advances `I1 -> I3`: the isolated POKROV-owned lab now has a
retained server record, exact alignment readback, default-off policy and
guarded kill/unbind path. This does not claim a successful tunnel or cohort.

The tuple also strengthens existing `I3` local evidence for `REL/PERF-001`,
`REL_GATE/GATE-E`, `FRKN_PLAN/W3-02`, `W3-03` and `W6-02`, and narrows the
`UNCERT-02` boundary without advancing it. Exact signed candidate,
device/origin matrix and promotion evidence required for `I4/I5` are absent.

Distribution becomes `I4=4`, `I3=313`, `I2=19`, `I1=40`, `I0=1`.

## Next action

1. Deploy the locally verified managed-profile correction to an authorized
   controlled environment, then prove build `4045` creates an app-owned TUN and
   reaches Core over AWG2 before running AWG3.1 and the bounded DNS/egress/leak
   matrix.
2. Restore private-repository Actions through Billing & plans, or obtain an
   explicit owner instruction before changing repository visibility.
3. Require successful platform/client app-bound checks on the exact PR heads.
4. Merge the client binding under the solo PR control, rerun Core
   `release-contract`, then promote Core and platform only with their required
   checks green.
5. Freeze and sign a replacement exact candidate from the promoted tuple.
6. Run the candidate-bound Android/Windows, current/Brain/RU-origin, provider,
   Operator, legal and performance matrices before any Gate F `GO` or Gate G.
