# WO-013V — Exact local pre-candidate and LDPlayer evidence

Status: `EXACT_LOCAL_PRE_CANDIDATE_ASSEMBLED_LDPLAYER_RECORDED`
Phase: `11`
Rows: `REL_DOD/DOD-15`
Candidate: `NOT_CREATED`
Publication: `NOT_AUTHORIZED_NOT_RUN`
Recorded: `2026-08-26`

## Goal

Rebuild the complete Android/Windows direct-beta artifact set from the final
source tuple, retain its supply-chain and checksum evidence, and exercise the
byte-identical x86_64 Android artifact on LDPlayer without converting emulator
results or an older physical-device run into exact-candidate proof.

## Non-goals

- Do not create a GitHub Release, signed public index, stable pointer or Store
  submission.
- Do not claim trusted Windows signing; the 1.2.0 direct-beta owner exception
  remains `SKIPPED_BY_OWNER` with a mandatory SmartScreen warning.
- Do not reuse the earlier `1.2.0 (4031)` Beeline run as physical-device proof
  for the rebuilt `1.2.0 (4030)` bytes.
- Do not describe AI/Games routing as DNS-only access without VPN.
- Do not expose AWG 3.1 publicly or claim a live endpoint.

## Write and no-touch scope

This WO writes only its own platform evidence record and wave index entry.
The immutable binaries remain outside Git in
`C:/Users/kiwun/Documents/ai/POKROV-builds/1.2.0-direct-beta-pre-candidate.3+30`.
Platform runtime code, client/Core sources, the public release index,
production configuration and unrelated dirty platform files are no-touch.

## Authority and exact identities

| Surface | Identity | Interpretation |
|---|---|---|
| Platform source used by the assembly | `8bed966e64e23527da982f3fcfb1b9e48ce6f408` | clean source; delta after deployed runtime is release documentation only |
| Deployed platform runtime code | `243dcbe4727041d62cc0a36e7d2fd5a8530c7c25` | current owned Brain deployment; no redeploy required for the docs-only delta |
| Client source | `a74d2aea5aed62f5c31d3a0bbc258e408cebe3bd` | exact Android/Windows build source |
| Core source embedded in artifacts | `344b317a7a09eca7943a93866b193553538bd8f6` | exact reproducible runtime source |
| Core `main` control head | `9b94e0bda7e454536e8fa9b4519f2281211798e0` | differs from embedded source only by hosted CI workflow control |
| Public release-index source | `7d5e402c47186fbe2ea1eb30ee1dc8cafdf066b2` | schema/trust-root source only; no candidate index created |

## Exact local artifact set

| Artifact | Size | SHA-256 | Signing state |
|---|---:|---|---|
| `pokrov-android-arm64-v8a.apk` | 101213906 | `4c3d6907741bfce04d1d4196fbf5d2821f93394c45f44bdc6116fcb4ddfbe933` | production signer `PASS` |
| `pokrov-android-armeabi-v7a.apk` | 90677536 | `52fa507c3b985a90787ef3f302796edf4192e80b1aa981ce076a3e808f0fabbf` | production signer `PASS` |
| `pokrov-android-market.aab` | 126149946 | `4a3b8c8e7b927a685f9e7c27ef8575ca5b2928e6eea294c9291106cd7a8bec4f` | production signer `PASS`; Store `NOT_RUN` |
| `pokrov-android-universal.apk` | 295018413 | `c03a5dea38cc031086e15cfabee95b403f1f5fa662583edd7d804be8401f26f2` | production signer `PASS` |
| `pokrov-android-x86_64.apk` | 109862385 | `7d7a22b23a33811326c452fdd23d19bbb02aae0b3f6bd74a6753e38f222675ed` | production signer `PASS` |
| `pokrov-windows-setup-x64.exe` | 28890834 | `730428bf6ff157502069d79fed3d89e17814bfff4cd023b9cfd404c838a038de` | `NotSigned`; `SKIPPED_BY_OWNER` direct beta only |

The artifact-set SHA-256 is
`d9cc602fea31a3ad5ebac1e92dabf84bde7f5e46d7c8c7abea384f1e69cbe89d`.
All five Android outputs match the existing production signer; no debug signer
or Store availability is credited. The Windows manifest proves all eight
required runtime files and keeps the exact SmartScreen/unknown-publisher
warning.

## Supply-chain and bundle proof

- CycloneDX 1.5 SBOM:
  `07ba9b1c8fbc9323b5411d7911dab7cca5458d6fda07b6b76a2e1d708694e7eb`.
- SLSA v1 provenance:
  `5534209a93f839f057e0701e8bd3d358db6dfff6a5d1924d3dec608c42e21685`.
- Strict release handoff:
  `af83aa0afb26489dc5572aab6f515d5543f3ba50c14b56ed202e2cbd084e9e8d`,
  `valid_v2`, six artifacts and ten unresolved required promotion gates.
- Pre-candidate bundle:
  `a6f957a9243c4f9be74e7d05744db3927646bebf647897d9ed2098a59e174bc7`.
- Finalizer checksum list:
  `46ed2086f696c08dc7b92387bae00e3a9e48d7b2e7817511822341db4a962dd0`.
- Complete 36-entry staging manifest, including notes and publication plan:
  `902be7cfc0c2a3d646f606b32951fca72d1a2b8183e1ea74991bace0a8b46480`;
  every referenced file revalidated.
- Read-only preflight:
  `81c62fd7fc11c7f0a2fabe5f9e24f5846988d21912fd893a9fa2068b089d5398`,
  `READY_LOCAL_FREEZE`, zero local blockers and zero pre-freeze rows below
  `I3`. A separate CRLF-mutated checkout probe remains superseded diagnostic
  evidence, not a source failure.

The publication handoff is `PLAN_ONLY` and
`NOT_AUTHORIZED_NOT_RUN`. A URL in the handoff is an intended destination, not
proof that a release or asset exists.

## Exact LDPlayer proof

The production-signed x86_64 APK was clean-installed on LDPlayer Android 14
after Android correctly rejected an in-place downgrade from local version code
4031 to exact version code 4030. Package data was reset for that emulator only.
The installed base APK was pulled and matched the staged SHA-256 byte for byte;
the app launched with zero crash-buffer lines.

Observed on these exact bytes:

- all seven locations and all four Saint Petersburg variants were visible;
- Saint Petersburg direct created `tun0`, used MTU 1280 and returned HTTPS
  egress 204 while the UI showed the proof-driven connected state;
- type 2 and type 3 failed closed: no `tun0`, no false connected state and no
  crash. These are `DIAGNOSTIC_ONLY` emulator results and do not override the
  independent owned-server full-chain passes or earlier physical Beeline data;
- Automatic, Cloudflare, Google, AdGuard and custom DoH presets were visible;
- AdGuard plus bounded AI and Games/Xbox routes persisted after restart;
- no ChatGPT, Gemini or Xbox content transaction was run, and the product
  remains an active-VPN routing feature rather than DNS-only unblocking;
- AWG2 and AWG 3.1 exact embedded runtime contracts pass default-off. AWG 3.1
  live proof is `BLOCKED_BY_ACCESS` because no isolated owned endpoint exists;
  Hysteria2 was still deferred for this exact 4030 evidence tuple. The later
  owner-authorized default-off source lab is tracked separately by `WO-013AR`
  and does not alter or upgrade this retained result.

The emulator was left with the exact app installed, VPN disconnected and
automatic location selected. A current-origin free-trial entitlement was
created during the test without payment; no account or session identifier was
retained. This is a production API mutation and is not candidate deployment.

## Runtime and deployment decision

The owned Brain services and Caddy remain active with zero observed restarts
for the release runtime units, and `/api/health` returns `status=ok`. The
installed backend code remains `243dcbe...`; platform `8bed966...` adds only
release evidence/docs, so another backend deploy would change no runtime byte
and is not required. Pre-existing failed Certbot/guarded announcement units are
kept separate from the healthy release runtime and are not converted to
`PASS`.

## Acceptance and ledger decision

The oracle for this WO is exact file identity plus production signer readback,
strict handoff/supply/checksum validation and byte-identical LDPlayer install
with fail-closed connection behavior. That oracle passes at the local
pre-candidate boundary.

No execution-ledger row advances. `REL_DOD/DOD-15` remains `I2`: candidate
creation, detached signed public index, same-byte public digest readback,
physical Android/OEM proof, signer recovery, `WIN-003`, current/Brain origin,
payment provider, Operator OIDC/RBAC, legal/commercial approval and rollback
drill remain absent. Distribution remains `I3=309`, `I2=17`, `I1=37`,
`I0=14`; 68 rows remain below `I3`, split `0/33/14/21` across pre-freeze,
candidate, external and deferred stages.

## Handoff

The next trustworthy step is exact physical-device Beeline testing of these
4030 bytes, followed by the remaining manual/origin gates. Candidate creation
and publication require an explicit owner command after those results are
classified. If publication is authorized, promote these same six byte hashes,
generate and verify the detached signed public index, then retain public asset
digest readback and rollback evidence.
