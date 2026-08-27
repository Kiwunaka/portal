# WO-013AE — Candidate.3 signed/private-carrier and bounded runtime reconciliation

Status: `CANDIDATE3_SIGNED_PRIVATE_CARRIER_WINDOWS_CLEAN_HOST_AND_LDPLAYER_PREFLIGHT_PROVED`
Phase: `11`
Candidate: `pokrov-1.2.0-candidate.3`
Recorded: `2026-08-27`
Production mutation: `NOT_PERFORMED_IN_THIS_RECONCILIATION`
Public/stable mutation: `NOT_PERFORMED`

## Outcome

Candidate.3 supersedes candidate.2 as the current exact release identity. It
binds the SPB stale-variant client correction, the current platform source,
the unchanged candidate Core authority and the public release-index signing
source. Its detached Ed25519 signature validates independently, and a private
client prerelease retains the exact Windows installer plus the signed
manifest, signature and receipt. This is a private evidence carrier, not the
public 1.2.0 release.

The exact Windows installer passes a GitHub-hosted clean-Windows install,
installed-file identity, LocalSystem service, authenticated IPC, restart,
uninstall and idle-network restoration run. The exact universal Android APK
passes an LDPlayer upgrade install, package/version readback, launch/relaunch
and persisted AI/Games routing-control smoke. The retained emulator account is
expired, so the catalog, tunnel, DNS behavior and egress are
`BLOCKED_BY_ACCESS`; they are not relabeled as a pass.

The real PB-14 release-health/action-intent control was also replayed from the
candidate.3 signed bytes. One identity-free `UPD-004` blocks observation close
and drives the guarded exact-candidate rollback request/public policy to zero
in an isolated temporary database. It does not switch an external artifact or
prove a deployed cohort.

The owner removed the physical phone and explicitly limited current device
work to LDPlayer. Candidate.3 physical Beeline/OEM/handover evidence therefore
remains `MANUAL_OWNER_TEST`/`NOT_REQUESTED` for this run. Earlier candidate.2
and non-candidate Beeline evidence remains historical and is not transferred
to candidate.3.

Public `v1.2.0`, six public assets, same-byte public promotion and the stable
pointer remain absent. The current public release remains `v1.1.6`.

## Exact candidate identity

| Surface | Exact identity | Evidence state |
|---|---|---|
| Candidate | `pokrov-1.2.0-candidate.3`, product `1.2.0+30` | `PASS` signed manifest |
| Platform | `eafaca3e64c0619dea7f58fc9c430682b4520559` | candidate-bound; PR/post-merge Guardrails and Release v2 pass |
| Client | `ac22825e857a313c9e4eba61030eb548d6346ead` | candidate artifact source; PR/post-merge Release v2 pass |
| Core | `344b317a7a09eca7943a93866b193553538bd8f6` | exact candidate source authority |
| Release index | `6a1afa95fe52da2d559ba7b1da88715cd0344bb2` | candidate source and signer run pass |
| Manifest | SHA-256 `a2752b6a3b95faacf13a68edb708c560966a0f5eb8727e109d7f1603fdc81090` | `READY_SIGNED_MANIFEST` |
| Detached signature | SHA-256 `926f0b4667a58ba9cc5ace5c4e6c3c8129d1ec3d4d449b3f0831a8c527cd7121` | Ed25519 key `pokrov-release-2026-01`; independent verification `PASS` |
| Receipt | SHA-256 `fb4d0d5dd272b8d3e7ea2303e2ffa93e332f54ac3e92f245400decc6c06e4b53` | manifest/signature/template/source binding `PASS` |

The six signed artifact identities are:

| Artifact | Bytes | SHA-256 | Signing |
|---|---:|---|---|
| Android arm64-v8a APK | 101213906 | `e105dc28bcadba9c063f64fb05652f6d905df373700c3c9d531a10ed0bd5d4d3` | production certificate |
| Android armeabi-v7a APK | 90710304 | `ef8b96bdaef056a138d7bf444909011d8f5ca388180e695bd733e35af7b769b4` | production certificate |
| Android market AAB | 126171642 | `50c1db2ef0f7f00c8fb2a60951e2c63226126d5da4a97cdf682c5531562a90da` | production certificate |
| Android universal APK | 295051181 | `f41c76ebf7bf69f6681d7df87e7722dcdccdec383ef950156b69829caee71c51` | production certificate |
| Android x86_64 APK | 109862385 | `7e697a2b7ea0fc0b390f7ee1df0a9c5cdce2730612579c3b6958138c35f6eba1` | production certificate |
| Windows x64 setup | 28898240 | `9962e3e80947dae374619ed388fc08b7322bffda38202a42e5812597c7818021` | `SKIPPED_BY_OWNER`, direct beta only |

The Android certificate remains
`0a0602a7df5d96a0b427909d004f3ddf26def86587634bf16694da8d654b2500`.
Windows remains `NotSigned` under
`OWNER_ACCEPTED_UNSIGNED_WINDOWS_BETA_1_2_0`; the Unknown publisher and
SmartScreen warning remain mandatory.

Supply-chain bindings are artifact set `103db0ec...`, SBOM `a98d9a12...`,
provenance `17895205...`, candidate input `99434da8...`, release handoff
`eba6d4c2...` and Windows manifest `6c1b4a11...`.

## Hosted source and signing gates

- Platform candidate source `eafaca3...` passed post-merge Guardrails and
  Release v2 runs `33029917507`/`33029917498`.
- Client PR 25 passed Release v2 run `33031007292`, merged as exact artifact
  source `ac22825...`, and its post-merge run `33032033161` passes.
- Client PR 26 added the exact-candidate clean-host workflow control. PR and
  post-merge Release v2 runs `33032654414`/`33033052385` pass; its workflow
  merge revision is `745c81fc...` and does not change candidate artifact bytes.
- Release-index PR 7 passed source-contract run `33032345273`, merged as
  `6a1afa95...`, and main-only signer run `33032397754` produced the exact
  manifest/signature/receipt without exposing the private key.
- Release-index evidence PR 8 passed source-contract run `33033414861` and
  merged as `32f560dd...`; immutable signed candidate inputs were not changed.
- Private prerelease `pokrov-1.2.0-candidate.3-private-ci` retains the Windows
  installer and three signed outputs at the exact client source. All four
  GitHub asset digests match. It is private, prerelease and non-stable.

## Exact Windows clean-host boundary

Workflow run `33033294889` used exact manifest `a2752b6a...`, signature
`926f0b46...`, installer `9962e3e8...` and workflow revision `745c81fc...` on
GitHub-hosted Windows image `win25-vs2026`.

The run proves a clean baseline, exact silent machine-wide install, all eight
installed-file identities, automatic LocalSystem service identity,
authenticated UI/service IPC, SCM stop/restart, clean uninstall and unchanged
idle route/DNS fingerprints with no residual POKROV/Wintun adapter.

It does not prove live TUN/full-tunnel traffic, connected DNS/leak protection,
authenticated egress, sleep/reboot/crash recovery, uninstall while connected
or an interactive SmartScreen observation. Those remain
`MANUAL_OWNER_TEST`.

## Exact Android LDPlayer boundary

The exact universal APK `f41c76eb...` was installed with retained data on
LDPlayer 9 instance `tiktok-test`, ADB `emulator-5554`, reported Android 9/API
28 model `SM-S9280`. Package readback reports
`space.pokrov.pokrov_android_shell`, version `1.2.0`, code `30` and the
production signer.

Upgrade install, foreground launch, force-stop/relaunch and bounded crash
inspection pass. AI services (ChatGPT/Gemini) and Games (Xbox) remained enabled
after relaunch. The account screen reports expired access, so the app withholds
the location catalog and cannot start VPN. Catalog, TUN, DNS, owned egress and
content reachability are therefore `BLOCKED_BY_ACCESS`, not `PASS`.

The retained screenshot/XML hashes are `cf18419e...`, `8c624bf0...` and
`a219c0e6...`. No physical device was used after the owner's instruction.

## PB-14 candidate.3 replay

`scripts/release_1_2_pb14_candidate_gate.py` re-hashes the exact manifest,
signature and receipt, verifies the detached signature against the public
keyring at release-index revision `6a1afa95...`, and binds operational
candidate id `51f54f88...` to client `ac22825...`, Android x86_64
`7e697a2b...` and build `4030`.

In an isolated temporary SQLite control fixture, one identity-free Android
`UPD-004` failure causes `release_health_gate_failed`; the staged state is
preserved. The guarded rollback request then sets candidate.3 to
`rollback_requested`/zero and the retained rollback candidate to
`current`/100. Production, deployment, public assets, stable pointer and
external artifact switch are all false/not performed. `OBS_PB/PB-14` remains
`I3`: the exact current-candidate local control passes, but no deployed cohort
exists.

## Ledger decision

No execution-ledger row advances. Candidate.3 replaces stale candidate.2
identity in the bounded source/signing/Windows rows and strengthens current
Android preflight evidence, but it does not close the broad device, live
network, origin, provider, Operator, legal, public-asset or promotion gates.

The distribution remains `I4=4`, `I3=307`, `I2=15`, `I1=38`, `I0=13`.
There are 311 rows at or above `I3` and 66 below `I3`; pending stages remain
`0/31/14/21` for pre-freeze/candidate/external/deferred.

## Verification

- Exact release-index public-key validation -> `READY_SIGNED_MANIFEST`, six
  artifacts and one owner-approved unsigned Windows exception.
- Platform exact-source hosted Guardrails/Release v2 -> `PASS`.
- Client exact-source and workflow-control PR/post-merge Release v2 -> `PASS`.
- Windows exact clean-host run `33033294889` -> `PASS` within the boundary
  above.
- LDPlayer exact-candidate upgrade/launch/settings persistence -> `PASS`;
  catalog/TUN/DNS/egress -> `BLOCKED_BY_ACCESS`.
- Candidate.3 PB-14 gate and focused tests ->
  `PASS_LOCAL_EXACT_CANDIDATE_HEALTH_STOP_AND_ROLLBACK_REQUEST`, `3 passed`;
  no production or external mutation.
- Public release creation, public asset upload and stable pointer mutation ->
  `NOT_PERFORMED`.

## Retained evidence

- `evidence/013AE-candidate3-reconciliation/013AE-candidate3-signed-manifest.json`
  retains signer run/output hashes, independent public-key validation and the
  exact private-carrier readback.
- `evidence/013AE-candidate3-reconciliation/013AE-pb14-candidate3-health-stop.json`
  retains the exact current-candidate local health-stop and guarded rollback
  request with explicit no-deployed-cohort/no-external-switch ceiling; 2636
  bytes, SHA-256 `45147c443f236fe7cd6b1c40fed4185017876bf9922ee538b7cb0e1a1979311d`.
- `evidence/013AE-candidate3-reconciliation/013AE-candidate3-reconciliation.json`
  is the sanitized central binding for candidate identity, artifacts, signing,
  hosted gates, Windows, LDPlayer and PB-14 boundaries, publication state and
  the unchanged execution index.
- The exact raw Windows and LDPlayer evidence remains in the local candidate
  staging directory; candidate Windows clean-host evidence is also retained on
  public release-index `main` at `32f560dd...`.

## Next action

Keep LDPlayer as the only active Android target until the owner returns a
physical phone. A valid owned entitlement is required before LDPlayer can
exercise catalog, TUN, DNS/AI/Games routing and authenticated egress. Do not
wipe the retained login or grant production access silently.

Separately execute the Windows live TUN/DNS/egress and connected
rollback/reboot/crash matrix. Then retain exact candidate.3 current/Brain/RU
origin, provider, Operator and legal evidence. Public `v1.2.0`, six same-byte
public assets and stable promotion remain prohibited until the required
stop-ship gates reach `I4` and the owner explicitly authorizes publication.
