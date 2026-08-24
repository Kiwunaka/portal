# WO-013U — Owner-approved unsigned Windows direct-beta assembly

Status: `DIRECT_BETA_PRE_CANDIDATE_ASSEMBLED_OWNER_EXCEPTION_ACTIVE`
Phase: `11`
Rows: `REL_DOD/DOD-15`
Candidate: `NOT_CREATED`
Production/publication: `NOT_AUTHORIZED_NOT_RUN`

## Outcome

The sole owner explicitly authorized Windows 1.2.0 to continue as an unsigned
direct-download beta while Microsoft Defender SmartScreen and
unknown-publisher warnings remain expected. Client PR 14 implements that exact
exception without weakening the trusted-signing path: it is limited to version
`1.2.0`, channel `outside_store_beta` and distribution
`direct_download_only`; it cannot support a trusted, signed, Store or broad
stable claim and expires when trusted signing becomes available.

PR head `f2210ba1f2ab05e8d60b9db7cc6e5f07f9bf9e2c` passed the complete hosted
cross-repository/client/Android gate in run `32678982419`, job `97292161973`,
in `12m54s`. It merged under `OWNER_SOLO_EXCEPTION` as client `main`
`f80387aa75fb632bb48d8023f0cba33f1972a144`; head and merge share Git tree
`d55afa2fe045c1a3569b28af10fb3d59d87b6575`. Post-merge run `32679674864`,
job `97294012063`, repeated the complete gate successfully in `11m58s`.

The merge commit then passed the exact cross-repository seed, observability,
release-handoff, rollback, logging, CI, hygiene, presentation, performance and
documentation validation against platform
`93964280836ff511e35b0856ed24ffdf6c5e34c1` and Core
`bdbd97fae35103e705f55908caebf75b4a9ff72f`.

## Exact local artifact set

| Artifact | Size | SHA-256 | Signing state |
|---|---:|---|---|
| `pokrov-android-arm64-v8a.apk` | 101157042 | `39fd6b2b4b1c9e3a2888a0e2a1e9bc228d8ed81957253a51d3fe8d4229596c25` | production signer PASS |
| `pokrov-android-armeabi-v7a.apk` | 90620944 | `83e8a172f38b1283e852029a6c09daf1137a01fe507472e92ba75916451584c7` | production signer PASS |
| `pokrov-android-market.aab` | 126074040 | `981c2b1bec24e87f860faa3852633afd261f13cb5ac6ed1b8dd1b97f0128c025` | production signer PASS; Store not published |
| `pokrov-android-universal.apk` | 294859469 | `b747f579c9ddba6d093ceef70e4b0f43f0885a580cf058eecaad9dcd53ace256` | production signer PASS |
| `pokrov-android-x86_64.apk` | 109801745 | `b065fdb9bbdb322d80c2638bca38eb88516c2041837e651a2454bd7e130db7bd` | production signer PASS |
| `pokrov-windows-setup-x64.exe` | 28885125 | `1ff2b34e26c2ad971b748a029f9ad787a674e8db8e1ad5cca5c11f9cecfcbe5c` | `NotSigned`; `SKIPPED_BY_OWNER` direct beta only |

All Android files match production certificate SHA-256
`0a0602a7df5d96a0b427909d004f3ddf26def86587634bf16694da8d654b2500`.
No debug signer or Store upload is credited. The Windows manifest proves all
eight required shell/service/Core/Cronet/Flutter files and the exact installer
hash. Independent Authenticode readback returns `NotSigned`; the manifest
records `OWNER_ACCEPTED_UNSIGNED_WINDOWS_BETA_1_2_0`, the required SmartScreen
warning and false trusted/Store claims.

The active support public pin is present in every Android app binary and the
Windows app binary bound by the build manifest. Its retained custody evidence
remains public-key-only; no private key was read, copied, printed or embedded.
The emergency verification input was also supplied as public material only and
matched key id `emg-20260815-v1` with decoded public-key SHA-256
`6eaf0cafd42bf0f1840be7896eb73fc339e735251a1692b114c1d1fd4d768a36`.

## Supply-chain and preflight evidence

The six-file artifact-set digest is
`59408337242f084f9419e2fe2ade229b347ffc117ddc141bee89ca8bb54d29bc`.
The CycloneDX 1.5 SBOM SHA-256 is
`14c09ee30944d2126ea7d9c147cd9201654ccb6a46f96b0aeba485c77b02172e`;
the SLSA v1 JSON provenance SHA-256 is
`c627a48ed15b735156632f29a2526f2bc682724e8aae5fb8e20c758f2d095a01`.

Strict-v2 handoff SHA-256
`847f13fa7418df54ed27ab7a5558dda092e0abcf4c579d89c569cac20aa25277`
classifies `valid_v2`, channel `beta`, with six artifacts and ten unresolved
required promotion gates. The final bundle SHA-256 is
`43847668cc75400e070a1060b33b218f73d8f09982c72783456be218ae0ab5cc`;
the 23-entry final checksum list SHA-256 is
`8f01bbaaa925150c8e71ab55c9703fbd86842479441a9358e64f75d9dcda9fed`,
and all 23 entries revalidate.

Read-only preflight binds platform/client/Core/public-index revisions
`9396428` / `f80387a` / `bdbd97f` / `7d5e402`, reports
`READY_LOCAL_FREEZE`, zero blockers and no pre-freeze row below `I3`. A first
Windows checkout probe was retained as superseded diagnostic because automatic
CRLF conversion changed the public-index schema working bytes; a clean LF
checkout at the same Git revision validates the declared exact schema hash.
No repository source change or false release-index failure is inferred from
that working-copy-only condition.

## Remaining boundary

`candidate_created=false`, `public_release_created=false` and
`production_mutation_performed=false`. The ten unresolved required gates are
`WIN_003`, Android physical/OEM/signer-recovery, current-origin, brain-origin,
payment-provider E2E, Operator OIDC/RBAC, legal/commercial approval and the
rollback drill. RU-origin remains separate and is required only for an RU
claim.

Trusted Windows signing is no longer a beta-candidate blocker under the exact
owner exception, but it remains mandatory before any trusted, signed, Store or
broad-stable Windows claim. Production deployment, GitHub Release creation,
stable-pointer mutation and Store upload still require separate authorization
and exact retained evidence.

## Ledger decision

No row advances. `REL_DOD/DOD-15` remains `I2`: the current source tuple now
has a production-signed Android set, owner-approved unsigned Windows beta,
embedded support pin, SBOM, provenance, strict handoff and final checksums, but
trusted/stable signing, signed public index, required device/origin/provider
proof and same-byte promotion remain absent.

Distribution remains `I3=309`, `I2=17`, `I1=37`, `I0=14`; 68 rows remain
below `I3`, with stage split `0/33/14/21`.
