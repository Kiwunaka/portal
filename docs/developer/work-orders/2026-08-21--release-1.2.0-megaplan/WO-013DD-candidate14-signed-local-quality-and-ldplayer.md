# WO-013DD — candidate.14 signed supply, local quality and LDPlayer truth

Status: `SIGNED_SUPPLY_PASS; LOCAL_QUALITY_PASS; LAB_PROFILE_ACTIVATION_FAIL; PROMOTION_BLOCKED`

Observed: `2026-08-31T09:20:59Z`

## Scope

Bind the dependency-refresh successor to one immutable signed candidate, rerun
the complete local quality gate from exact source, install the exact x86_64
artifact on LDPlayer, test the default and guarded AWG lab paths, and retain
the result without touching public assets, Store state, stable pointers or
production runtime.

This work order supersedes candidate.13 only as the current candidate
authority. Candidate.13 remains immutable historical evidence. Its successful
AWG runtime result is not transferred to candidate.14.

## Exact boundary

| Item | Value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.14`, immutable, internal only |
| Version/build | `1.2.0+4049` |
| Platform source | `6f694d003934731045b5d02dccff1d61fecc1380` |
| Client source | `75ba7e721cfee486f7189edd51de97aba2746722` |
| Core source | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Signed release-index source | `ef084ae2f8550b7aa488fc1a7de492e706812821` |
| Receipt-recording release-index source | `93975850f39955fd7a55ce53d6cee603aa44dc7a` |
| Strict-v2 handoff SHA-256 | `8682fc6c04fc74241fc045eea19ded11909ea4faa399b4afddd3fad69d8dbaae` |
| Signed manifest SHA-256 | `e847bb33c9d7004cb74f0baf311b1b7bf7cd9ab20d72bfe88d3a6c9c8656bc07` |
| Detached signature SHA-256 | `86a76642ecfde2855914be03240c17f2757921a6467bae2ef7a65971eb0ed10f` |
| Signing receipt SHA-256 | `7b616beadbb0aa225d6b2efc2388ec3799df02692835ae1fe6165cea2828c2a1` |
| Runtime | exact x86_64 APK on LDPlayer Android 9/API 28, current origin |

The source seed remains `PRE_CANDIDATE_LOCAL` and is not release authority.
The generated strict-v2 handoff and signed release-index receipt are the
candidate authority. Signer run `33359918180` produced
`ACTIONS_ARTIFACT_ONLY` with `promotion_authorized=false`.

## Signed supply and dependency result

Candidate.14 carries the refreshed Python locks from WO-013DC. An isolated
Python 3.12 environment installs the exact locks, `pip check` passes, fresh
production and test audits return zero known findings, the dependency contract
passes, and the focused release/dependency slice passes `55` tests.
`REL/DEP-001` therefore advances from `I3` to `I4` for the exact signed
successor. This does not prove unrelated hosted, device or production gates.

All six build-4049 application artifacts are byte-identical to candidate.13
because the successor change is in platform dependency/source truth, not the
client/Core payload. The unchanged bytes are nevertheless rebound to the new
platform source and newly signed manifest; candidate.13's promotion status is
not reused. Offline validation passes `6/6` artifacts and `8/8` Windows runtime
files. CycloneDX 1.5 contains `349` components and provenance binds six
subjects.

Five Android artifacts retain the production certificate and are
non-debuggable. Windows setup SHA-256
`0afaf6e1d73a7e72762d945557f48793646a9bdbf12bb8ca2e843d4b94df276c`
remains unsigned under `OWNER_ACCEPTED_UNSIGNED_WINDOWS_BETA_1_2_0`. It is
eligible only for the explicitly labeled direct beta with the expected
SmartScreen warning; it is not trusted, Store or broad-stable proof.

## Complete local quality result

The exact platform/client/Core worktrees pass the aggregate local gate in an
isolated tool environment with Node `22.14`, npm `11.7`, Playwright `1.61.1`
and Chromium `149.0.7827.55`. All `15/15` steps pass, including:

- the performance contract and `30` focused tests;
- client analysis and `413` widget tests;
- release seed/docs validation;
- web lint/build and cabinet Playwright `69/69`;
- marketing build, SEO, responsive and reduced-motion checks;
- admin build;
- static performance collection and gate `9/9`.

The aggregate report correctly says `local_status=PASS`,
`candidate_proven=false` and `promotion_status=MANUAL_OWNER_TEST`. The local
gate advances no device or promotion row beyond `I3`.

## Exact LDPlayer result

The installed `base.apk` SHA-256 equals the candidate.14 x86_64 artifact
`73c43e21dfc984c474941e14800c551f9545fe423b8f11458f6d41b8cb9af5ff`.
Install, package/build readback, cold launch, UI hierarchy and crash-buffer
checks pass. The ordinary `default` profile establishes Android VPN service,
`tun0`, managed DNS and authenticated VPN egress with `33` VLESS outbounds.

A one-day exact-install test entitlement extension was applied to run the
owner-authorized closed lab. Both AWG 3.1 and AWG2 control-plane operations
selected the requested profile and provisioned guarded test material. The app
did not activate either requested runtime profile: every sanitized runtime
readback remained `default`, including after normal reconnect and the
user-facing repair flow. The exact result for both lanes is therefore
`FAIL_MANAGED_PROFILE_ACTIVATION_CACHED_DEFAULT`.

The observed boundary is above protocol execution: the app's managed-profile
refresh did not stage the requested profile and used cached default state.
Consequently this run proves neither AWG 3.1 nor AWG2 protocol-engine success
or failure. A separate owned-node alignment check could not complete in the
current access window and is labeled `BLOCKED_BY_ACCESS_CURRENT_RUN`, not
PASS.

Cleanup passed. The selected profile is `default`; lab cohort/allowlist and
AWG material are absent; the app is disconnected; Android reports no active
VPN service or tunnel interface; and a final cold relaunch is normal with an
empty crash buffer. The one-day entitlement extension is retained as an
explicit test mutation. The exact app remains installed.

## Release decision

Candidate.14 is current and reaches `I4` for signed supply and the exact
dependency-lock slice only. `FRKN_PLAN/W3-02` and `W3-03` return to `I3` for
the current candidate because candidate.14 did not activate an AWG runtime
profile; candidate.13's successful emulator result remains history.

Gate F is not generated because its required exact physical ARM64 install
binding is absent. Physical Android, isolated clean Windows connected
TUN/DNS/recovery, RU origin, provider payment E2E, Operator OIDC/RBAC, legal
and commercial approval, real runtime rollback, comparable device performance
and authenticated journeys remain non-PASS. Gate G is `NOT_AUTHORIZED`.

No tag, GitHub Release, public asset, Store submission, stable pointer, runtime
sync or production deployment occurred.

## Evidence

- normalized evidence:
  `evidence/013DD-candidate14-signed-local-quality-and-ldplayer/013DD-candidate14-signed-local-quality-and-ldplayer.json`;
- normalized evidence SHA-256:
  `bfb1342f181a88792e30455c92c39c4b40280c457787cefc64d124256c3754af`;
- local quality report SHA-256:
  `1bf20e3efedf4bb53c71ea7886c1db201bc27d64171d2f864dae4dfa6ea0d09c`;
- local web-performance evidence SHA-256:
  `4a884a7307d166b8d8aeffb36c8a53727dc786d64cc9d62538a2189cfd389af0`;
- candidate artifact-set SHA-256:
  `e0dd97e50c255b1e5efe8aa808e0bfb67b5a05be9a079c9c5d8c8a5e7f83a361`.

Raw emulator captures remain outside Git under the retained release-evidence
root. The normalized record includes only bounded identifiers, statuses and
SHA-256 values; it contains no endpoint, address, credential, key or runtime
material.

## Rollback

The runtime lab cleanup already restored default/no-lab/disconnected state.
For candidate metadata, retain candidate.14 immutably and select a separately
signed successor; never rewrite its manifest or receipt. The documentation
change can be reverted as one evidence commit without changing artifacts,
runtime, DNS, public release or stable state.
