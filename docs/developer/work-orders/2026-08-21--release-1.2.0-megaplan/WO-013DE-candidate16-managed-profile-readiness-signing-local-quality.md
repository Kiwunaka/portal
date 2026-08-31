# WO-013DE — candidate.16 managed-profile readiness, signed supply and local quality

Status: `SIGNED_SUPPLY_PASS; READINESS_CORRECTION_DEPLOYED; LOCAL_QUALITY_PASS; DEFAULT_LDPLAYER_PASS; LABS_NOT_RUN; PROMOTION_BLOCKED`

Observed: `2026-08-31T15:07:31Z`

## Scope

Replace candidate.14 as current release authority after correcting the
managed-profile readiness boundary, deploy only that authorized platform
correction to the owned Brain `portal-api`, bind the resulting source tuple to
an immutable signed candidate, repeat complete local quality from exact source,
and prove the exact x86_64 application bytes on LDPlayer through the ordinary
default path.

This work order does not transfer candidate.13's successful AWG emulator run or
candidate.14's cached-default lab result. Candidate.16's AWG 3.1 and AWG2 lab
runtime paths are `NOT_RUN` and remain open.

## Exact boundary

| Item | Value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.16`, immutable, internal only |
| Version/build | `1.2.0+4049` |
| Platform source | `719e23dc49407beb9ae30d98d17d4b73d18ae37c` |
| Client source | `75ba7e721cfee486f7189edd51de97aba2746722` |
| Core source | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Signed release-index source | `54cfa03502ffafa5e4fb230a2cbdb0c0572c429f` |
| Receipt-recording release-index source | `f321a8ce9bb7913774ac49eefe1da0f4d2d0cfaa` |
| Strict-v2 handoff SHA-256 | `e604410e7dce9e39a22c8b54f8863216c3df71311b9d6639189ef4bc09aa2ac3` |
| Signed manifest SHA-256 | `ae1906e68df755b1e0ce6a77d6ede8256f923e72fe11da57f1cae89a82c4ffe6` |
| Detached signature SHA-256 | `f5df63578d56db84a48eac1c68f1192e81462e8b407b1b6ff877c2b415507a9a` |
| Signing receipt SHA-256 | `1231ab6988746ca0e9725296826de2a9696a9a78600aa5e7f0b0c1b8c5782de4` |
| Runtime | exact x86_64 APK on LDPlayer Android 9/API 28, current origin |

Candidate.14 and the intermediate candidate.15 assembly remain immutable
history. Candidate.16 is the first signed authority containing the merged
platform correction. Output remains `ACTIONS_ARTIFACT_ONLY` with
`promotion_authorized=false`.

## Managed-profile readiness correction

The observed failure was above protocol execution. A pending live sync could
report ready without a durable eligible node mapping, leaving the client on a
cached default profile. Platform commit `20d7da7...` and PR `#129` correct that
boundary: a confirmed `UserNode` plus active `AccessKey` is intersected with
the current eligible pool, and the false `sync_ok` state is rejected.

The owner-authorized production change was limited to Brain `portal-api`.
Predeploy and postdeploy source probes were retained; the deployed semantic
source readback passes `197/197`, and the public API health check returns HTTP
200. The rollback backup is
`/root/portal_bot.deploy-backups/20260831T134406Z-436028`. Platform hosted jobs
that exposed zero executable steps are recorded as `SKIPPED_BY_OWNER`, not
PASS.

This proves the readiness/sync truth boundary and the ordinary default-profile
path. It does not prove AWG 3.1, AWG2, Hysteria2, Brain-origin egress, RU-origin
behavior, provider payment flow or Operator mutation.

## Signed supply and support-pin result

Release-index input PR `#33`, signer run `33402507136`, and receipt PR `#34`
all execute real hosted steps successfully. The retained signing artifact is
ID `9761790067`, digest
`sha256:aba50268ad4acffc3fcc360d11dcd026590c3fae1635729a0378588d95c52b8d`.
The owner-solo exception remains explicit and
`independent_review_performed=false`.

Offline validation passes all six artifacts and all eight Windows runtime
files. CycloneDX 1.5 contains `349` components, provenance binds six subjects,
and the exact refreshed dependency locks retain bounded `REL/DEP-001 I4`.
Five Android artifacts remain production-signed and non-debuggable. Windows
setup SHA-256 `0afaf6e1...f276c` remains unsigned under
`OWNER_ACCEPTED_UNSIGNED_WINDOWS_BETA_1_2_0`; only the clearly labeled direct
beta with the expected SmartScreen warning is permitted.

The copied auxiliary support-pin report initially retained candidate.15's ID.
It was corrected before this reconciliation and independently revalidated over
six exact candidate.16 artifacts and ten binary archive entries. The report
keeps `ce2581dd...` as the actual artifact build source and separately records
candidate client source `75ba7e7...`; their delta is documentation-only and
does not change a build input. Its SHA-256 is
`1af65938e425dd1caf7ac3088a03be65742ff85495e24b1f807b407e9c05a9a0`.

## Complete local quality result

The exact platform/client/Core tuple passes the aggregate local gate under the
required Node `22.14.0`, npm `11.7.0` and Playwright `1.61.1` environment. All
`15/15` steps pass, including client analysis, `413` widget tests, cabinet
Playwright `69/69`, marketing/admin builds and static performance `9/9`.

The authoritative report SHA-256 is
`37004c7e1afb2728b63bc11d39ecce5f99de09db3cce25c4453d3637535c3000`.
It correctly retains `candidate_proven=false` and
`promotion_status=MANUAL_OWNER_TEST`; earlier environment-preparation failures
remain honest history and are not the final result.

## Exact LDPlayer result

The installed x86_64 APK SHA-256 is
`73c43e21dfc984c474941e14800c551f9545fe423b8f11458f6d41b8cb9af5ff`,
byte-identical to the candidate.16 artifact. After the readiness correction,
a fresh ordinary connection proves Android VPN service, tunnel interface,
managed DNS and authenticated VPN egress. Sanitized runtime structure contains
`28` VLESS, `2` selector, and one each direct, block and urltest outbound.
Disconnect cleanup passes.

No physical phone was touched. Candidate.16 AWG 3.1 and AWG2 lab paths were not
run, so `FRKN_PLAN/W3-02` and `W3-03` remain `I3` without a current-candidate
protocol result.

## Release decision

Candidate.16 is current and reaches `I4` only for signed supply and the exact
dependency-lock slice. Gates B, C and E remain `I3` with stronger default-path
evidence. Gate F is not generated because its exact physical ARM64 install
binding is absent. Physical Android, isolated clean Windows, RU-origin,
provider E2E, Operator OIDC/RBAC, legal/commercial approval, runtime rollback,
device performance and authenticated journeys remain non-PASS. Gate G is
`NOT_AUTHORIZED`.

No tag, GitHub Release, public asset, Store submission or stable pointer was
created or changed.

## Evidence

- normalized evidence:
  `evidence/013DE-candidate16-managed-profile-readiness-signing-local-quality/013DE-candidate16-managed-profile-readiness-signing-local-quality.json`;
- normalized evidence SHA-256:
  `6505301fa741a9a024c24b8ac090cfe365644858d870647898c945f90a386deb`;
- local quality report SHA-256:
  `37004c7e1afb2728b63bc11d39ecce5f99de09db3cce25c4453d3637535c3000`;
- candidate artifact-set SHA-256:
  `d9bba178d184958f9577ac39e3e736ef081677297cc67dc5bcffcb327edb4f69`.

Raw runtime captures remain outside Git under the retained release-evidence
root. The normalized record contains bounded identifiers, statuses and hashes,
not credentials, keys, addresses, endpoint material or raw provider payloads.

## Rollback

The LDPlayer path is already disconnected. The Brain correction can be rolled
back from the retained predeploy backup with source/readiness readback.
Candidate.16 metadata is immutable: if later checks require different bytes or
source, create and sign a successor instead of rewriting its manifest or
receipt. This documentation change can be reverted as one evidence commit
without changing artifacts, production, DNS, public release or stable state.
