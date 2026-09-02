# WO-013EI — candidate.21 strict-v2 supply and signed private release index

Status: `PRIVATE_CANDIDATE21_SIGNED_SUPPLY_READY_RUNTIME_AND_PROMOTION_GATES_OPEN`

Observed: `2026-09-02`

Production/public mutation: `NONE`

## Outcome

WO-013EH remains the immutable private-assembly and bounded Windows 11 runtime
record. This work order closes only its missing supply-chain slice for the same
six candidate bytes. It does not rewrite the Windows evidence or convert any
unrun runtime/manual gate into a pass.

Exact platform `e2608130e85d9a0f8fa4b920f46cf3d7679332c3`, client
`1e164586d741484b5ae8fb2ee267ef5dd813cadb` and Core
`cd8f0f4169d570d693992a959d81d17c2c44884d` now bind to a generated strict-v2
handoff, refreshed candidate.21 CycloneDX SBOM, provenance, offline supply
validation and a trusted Ed25519 release-index manifest. The release-index
signing source is exact commit `cae911e506d95eb72c1364b847992e30cbf9baf9`;
the later receipt documentation merge is
`3b75446b88c04e0b2cc6712c6193b64195cadf3a` and is not substituted into the
signed manifest.

The signer output is retained as a 14-day GitHub Actions artifact only. No
`v1.2.0` tag, public GitHub Release, public binary, Store upload, stable pointer
or promotion was created. Windows remains the owner-approved unsigned
direct-download beta with mandatory SmartScreen/unknown-publisher warning.

## Exact signed supply

| Item | SHA-256 / value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.21`, `1.2.0+4050` |
| Artifact set | `36c42f32596ecb9f52ab401f3b210c894d8b70be7e62121e107a05e310845a02` |
| Creation manifest | `c79eb481c3ce0402edaf72c2a5083027481b5a8bc34511c1a694cb972f5331d6` |
| CycloneDX 1.5 SBOM | `c01234bf303b516764da9046fa08208b31126255355e68ca25b1f54180082738` |
| Provenance | `b6e63ae0708f23932de4e07039b3c99c8be892a779df6135450ea6717f1ad4ad` |
| Handoff input | `7ef3b7295a665b9fad4b672ce451fd2090ea984a88b632c2afebfd786f778efa` |
| Strict-v2 handoff | `07e0009c8d773402e25f2ab8cb823bafab738026439b8c60f5d509629b7955e9` |
| Offline supply validation | `9b9a68ef53e594ecb4cdb0549962a7c8a6f480a92e7129bae800e388a34f2118` |
| Signed manifest | `ce0b8586d4d9b5b625bbcd2c93b03fd783f89b4958a7fd79e58ef65b52c3dc6b` |
| Detached signature | `ef474e6e1e147093b8b15c3cdc29bd35b5779249854a63ef7d6535d2588c7a58` |
| Signing receipt | `aaa027cc5d71fd567c6f3c0b8a9e3b0e965a67760fd02d1769eb3d54062926f8` |
| Signing key | `pokrov-release-2026-01` |
| Manifest validation | `READY_SIGNED_MANIFEST`, `6` artifacts, `1` owner unsigned-Windows exception |
| Promotion | `promotion_authorized=false` |

Strict-v2 validation binds all six artifacts and reports nine blocking manual
gates. Offline platform validation binds the exact four-repository tuple, six
artifacts and all `11/11` Windows runtime files. The SBOM/provenance contain
build `4050` and candidate.21 identities; no candidate.20/build-4049 identity
is retained as current supply truth.

## Hosted chain

- release-index input PR 43: head `ac902f9ca59d6bf4a8986744e27aeda067c1ca67`,
  source-contract run `33586691099` `SUCCESS`, merged as `cae911e...`;
- signer run `33586752995`: manual main-only dispatch on `cae911e...`,
  `SUCCESS`, output `ACTIONS_ARTIFACT_ONLY`;
- Actions artifact `9830338475`: digest
  `sha256:9bd2ac5e7e69722c143ec1a50fc7e24564396f6fec647f21a6a2a84188823568`,
  expiry `2026-09-16T03:22:09Z`;
- receipt PR 44: head `3ff81e983ac6a33218202b4595db0553ab21f413`,
  source-contract run `33586988337` `SUCCESS`, merged as `3b75446...`.

The signed manifest was revalidated from a clean detached release-index
worktree at exact signing commit `cae911e...`. Validation against later main is
deliberately rejected because a signed manifest must bind the exact
release-index revision rather than a newer receipt-only commit.

## Ledger effect

No completion-index level changes. Distribution remains `I4=7`, `I3=320`,
`I2=19`, `I1=32`, `I0=0` across `378` unique rows. Rows that previously named
candidate.21 handoff, SBOM/provenance or signed-index creation as open are
rebound to this exact supply evidence; public assets, device/runtime evidence
and promotion remain open.

## Open gates

- exact candidate.21 Android install/launch and physical Wi-Fi/Beeline runtime;
- fresh in-place Windows service-restart recovery, remaining Windows lifecycle
  and non-default protocol paths;
- exact-candidate AWG2/AWG3.1 live transport and in-app Smart DNS session,
  leak/privacy/load/lifecycle matrices;
- authenticated current-, Brain- and RU-origin evidence kept separate;
- guarded candidate rollback plus pointer/origin readback;
- provider, PostgreSQL/outbox, Operator, legal/commercial, accessibility,
  comparable performance and endurance gates;
- final no-open-P0, false-green and privacy attestation;
- Gate F `GO`, followed by separately authorized Gate G.

## Evidence

- normalized record:
  `evidence/013EI-candidate21-signed-supply/013EI-candidate21-signed-supply.json`;
  SHA-256
  `dfedd1d77ebec22b92222dd8740d2d3a35345d298fdeedead4e5137047dbb7a2`;
- immutable local candidate root:
  `E:/POKROV-tools/release-candidates/pokrov-1.2.0-candidate.21`;
- exact release-index validation worktree: `E:/ri21v` at `cae911e...`.

The normalized record retains only public repository identities, hashes,
counts and release states. It contains no credential, private key, raw profile,
connection material, customer data or provider payload.
