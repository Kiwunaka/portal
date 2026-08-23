# WO-013I — Reproducible Core 1.1.0 artifact binding

Status: `COMPLETE_LOCAL_PRE_CANDIDATE_EVIDENCE_NO_LEDGER_ADVANCEMENT`
Phase: `11`
Rows reviewed: `REL/CORE-001`, `REL/TEST-001`, `REL/REPO-001`,
`REL_DOD/DOD-10`, `REL_DOD/DOD-15`, `FE_PR/PR-00`,
`FRKN_ADOPT/ADOPT-05`, `FRKN_PLAN/W1-03`, `FRKN_PLAN/W3-02`
Promotion: `NOT_AUTHORIZED`

## Outcome

Build Android and Windows Core `1.1.0` twice from the exact clean Core source,
compare the produced trees byte for byte, bind the resulting AAR/DLL to the
active client, and make exact-byte verification part of the read-only
candidate preflight. Keep the result at `PRE_CANDIDATE_LOCAL`: it is unsigned,
has no release tag, candidate manifest, public release-index revision or
device/origin proof.

## Exact source and binding identities

- Core source: `fcb3c8bbc6efdeed284417369aacb522722ebfa2` on
  `codex/1.2.0-release-v2`, version `1.1.0`, state
  `PRE_CANDIDATE_LOCAL`.
- Client binding: `8e12bddd822174db363483e685a0f6bbadc6661e`, followed by
  self-contained dirty-generation regression commit
  `336d5454d47fa33d08b7a6bae79b7980cc6b11b4` on
  `codex/1.2.0-release-v2`.
- Platform preflight validator: `7a15ba2bd5d17617aca28205cd448b6c917929ab`
  on `codex/1.2.0-phase00`.

All three worktrees were clean for the retained preflight. These local commits
are source identities, not a release candidate.

## Reproducible artifacts

- Android AAR: 107,317,530 bytes, SHA-256
  `26a7b9ebcf05065b33cc40848147a66db5172a9655cb9c77a839fa685145bf93`;
  four packaged ABIs: `armeabi-v7a`, `arm64-v8a`, `x86`, `x86_64`.
- Windows Core DLL: 55,352,320 bytes, SHA-256
  `10ee475d04417c4317221a85ca4b043a7489294d654fc4ce7a64ec56dcdcdbff`;
  required exports pass `15/15`.
- Windows `libcronet.dll`: 8,596,992 bytes, SHA-256
  `8ef1f8bbde77f954af1ae47bee1819ac8dc2354bb0e1d4baba3dad9e58d7a6f7`.
- Android tree SHA-256:
  `78cbf8dddd6ce2c3311a2ec2167c803ec122a6973efe50d955f26ec1d07c3b13`.
- Windows tree SHA-256:
  `a293a83e1efbd653b7a623b3c832df93f4985a57a50bb693cf4aef75dcfe3b4b`.

The Android pair and the successful Windows pair are byte-identical. The first
Windows attempt lacked the portable MinGW directory in its process `PATH` and
is `NOT_CREDITED_ENVIRONMENT_FAILURE`; the two subsequent clean-source builds
are the credited pair. The portable MinGW 13.2.0 archive SHA-256 is
`a05578fab9068c678ce761e7b2e284d23fa7416a2f4f36349e05e506c944e2c7`;
Go is pinned to `1.25.13`.

The two generated CycloneDX documents are retained by identity rather than
copied into the platform source tree:

- `pokrov-core.cdx.json`: SHA-256
  `18707e43f557d80aceecb112d4907c1295e8a27583af1bf2243d45cf63ba38a0`;
- `sing-box.cdx.json`: SHA-256
  `28925d34046ac0f0a7edec40a032938fcbc59c18bd47b9d5d69b6688ebf6637d`.

Local-fork and missing detected-license metadata warnings remain declared
limitations. The SBOM generation pass is not legal clearance.

## Client and Core verification

- Exact Windows Core proxy-only start/stop backtest: `100/100 PASS_LOCAL`.
  This does not prove TUN, DNS, routes or leak protection.
- Client standard gate on `336d5454...`: app-shell `385/385`, runtime-engine
  `59` pass plus one expected external-DLL skip in the standard gate, Android
  shell `8/8`, Windows shell `21/21`, and direct/store Gradle
  `BUILD SUCCESSFUL` with 162 tasks reported.
- Cross-repository client seed validation against the exact platform/Core
  roots passes. The client seed binds source SHA, artifact sizes/hashes,
  two-build evidence, SBOM identities, ABI/event state and
  `candidate_created=false` / `promotion_authorized=false`.
- Platform preflight regression passes `12/12`; Ruff, format check, Python
  compile and `git diff --check` pass.

Machine evidence:
`evidence/013I-core-artifact-binding/013I-core-artifact-binding.json`, plus
content-identical Android and Windows Core evidence mirrors in the same
directory. Repository line endings are normalized; the original evidence
SHA-256 values remain the authoritative byte identities.

## Clean preflight result

The exact-byte-aware read-only preflight returns expected `BLOCKED` with
`candidate_created=false`. Android, Windows and libcronet actual bytes match
their declared sizes and SHA-256 values, Core/client revisions match, and the
two old artifact blockers are closed. Three blockers remain:

1. `release_index_missing` — `BLOCKED_BY_ACCESS`;
2. `ledger_pre_freeze_incomplete` — three rows;
3. `ledger_external_pre_candidate_incomplete` — three rows.

The retained report is 44,597 bytes with SHA-256
`227b5f341b166ff0e162fb505dac3a4a44dc68562f49756ef64226499e458947`.

## Index decision

No ledger row advances. Distribution remains `I3=303`, `I2=19`, `I1=40`,
`I0=15`; 74 of 377 rows remain below `I3`. Pending stage counts remain
`3/33/17/21` for pre-freeze/candidate/external/deferred.

- `REL/TEST-001` stays `I2`: the updated clean client passes locally, but the
  hosted Ubuntu run is still `NOT_RUN`.
- `REL/REPO-001` stays `I2`: exact local bytes do not provide the unavailable
  signed public release-index repository/revision.
- `FE_PR/PR-00` stays `I2`: the current aggregate has visible UI changes and
  is not an isolated no-visible-UI PR with hosted checks.
- `REL_DOD/DOD-10` stays `I2`: exact Android/Windows local artifacts now exist,
  but hosted and Apple build/device proof is absent.
- `FRKN_ADOPT/ADOPT-05` stays `I2`: source/SBOM/artifact identities exist, but
  trusted signer and public immutable mapping do not.
- Candidate-only signing, artifact, device and publication rows do not move to
  `I4` from local unsigned proof.

## Evidence ceiling and next action

This is `LOCAL_PRE_CANDIDATE_ARTIFACT` evidence. No push, release tag, hosted
CI, trusted signing, device/VM run, current/brain/RU-origin run, public index,
provider call, payment, OIDC exchange, server mutation, deployment,
publication, campaign or promotion occurred.

Next close the three pre-freeze rows with a hosted Ubuntu client gate, a real
separate public release-index checkout/revision, and an honest isolated PR-00
proof or owner-approved reclassification. The external pre-candidate rows
`REL/REL-001`, `REL_DOD/DOD-09` and `FE/P12-023` require owner/access work and
remain blockers. Do not construct or sign a candidate until those gates close.
