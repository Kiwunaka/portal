# WO-013AC — Candidate.2 signed/private-carrier and Windows clean-host reconciliation

Status: `CANDIDATE2_SIGNED_PRIVATE_CARRIER_AND_BOUNDED_WINDOWS_CLEAN_HOST_PROVED`
Phase: `11`
Candidate: `pokrov-1.2.0-candidate.2`
Recorded: `2026-08-27`
Production mutation: `NOT_PERFORMED_IN_THIS_RECONCILIATION`
Public/stable mutation: `NOT_PERFORMED`

## Outcome

Candidate.2 replaces candidate.1 as the current exact release basis. Its
detached Ed25519 manifest, signing receipt, six artifact identities, source
tuple and supply-chain bindings validate independently. A private prerelease in
the client repository retains the exact Windows installer plus the manifest,
signature and receipt with matching GitHub asset digests. It is an evidence
carrier, not the public 1.2.0 release.

The exact unsigned Windows installer passes a GitHub-hosted clean-Windows
install/service/authenticated-IPC/restart/uninstall/idle-network run. This is
candidate evidence for the service privilege boundary, but it does not prove a
live TUN, connected DNS/leak behavior, authenticated egress, crash/reboot,
uninstall while connected or interactive SmartScreen behavior.

The real PB-14 release-health/action-intent control was rerun from the
candidate.2 manifest bytes. It blocks an unhealthy observation close and
drives a guarded rollback request to zero distribution in an isolated temporary
database. It does not switch an external artifact or prove a deployed cohort.

Public `v1.2.0`, six public assets, a stable pointer and same-byte public
promotion remain absent. The current public release remains `v1.1.6`.

## Exact candidate identity

| Surface | Exact identity | Evidence state |
|---|---|---|
| Candidate | `pokrov-1.2.0-candidate.2`, product `1.2.0+30` | `PASS` signed manifest |
| Platform | `c5f3fca5c55d6baa48b54af3bf756ef40cc0e6e1` | candidate-bound; PR/post-merge Release v2 and Guardrails pass |
| Client | `e6c29d1201eded0d045a3e75f43beff8ae24bd8f` | candidate-bound; PR/post-merge Release v2 pass |
| Core | `344b317a7a09eca7943a93866b193553538bd8f6` | candidate-bound; prior 013AA exact-source reconciliation retained |
| Release index | `4c6d46c10083e68dc5d2032c13f51c4e80a17049` | candidate template/source and signer run pass |
| Manifest | SHA-256 `1697a1bce4f72314aa1f60cd74a1711f9b8f7d70091c5757e98fbdc09b4ce5e0` | `READY_SIGNED_MANIFEST` |
| Detached signature | SHA-256 `ebf259f1a9d3c9d561e3f39123c12804a178da5f15efcb293aeab47d45308a82` | Ed25519 key `pokrov-release-2026-01`; independent verification `PASS` |
| Receipt | SHA-256 `975eaa3ae2af4bda6e33f73fe48c483a4b6b12d9b8e6219e8211f4e60cc431e0` | manifest/signature/template/source binding `PASS` |

The six signed artifact hashes are:

| Artifact | Bytes | SHA-256 | Signing |
|---|---:|---|---|
| Android arm64-v8a APK | 101213906 | `a1ac79a979b3f80036ad9b817790e3c3dd00f8c2483901215b74577381a5cbc9` | production certificate |
| Android armeabi-v7a APK | 90677536 | `50b2ff36bafd2b38aa4c6dbf5981a8547d85937a2039d65fa5a29dec678d942a` | production certificate |
| Android market AAB | 126150030 | `b7a633e23e6ce86761c92047f048cf069c8d84d6e430befffc01ad239b6e566f` | production certificate |
| Android universal APK | 295018413 | `799d96e150ac2a658f66c3495347aff9bf3a314969906c2e9a6f0e7315232e2b` | production certificate |
| Android x86_64 APK | 109862385 | `b530ff2568d517930a9d8c30bd81cdf3594bb6b64c607f4f6f22b3ce54bc00fc` | production certificate |
| Windows x64 setup | 28893114 | `4226daa49975cb25dae5bec8cbcd26299648ee89f5dbff613f62d807be0ac412` | `SKIPPED_BY_OWNER`, direct beta only |

The production Android certificate remains
`0a0602a7df5d96a0b427909d004f3ddf26def86587634bf16694da8d654b2500`.
Windows remains `NotSigned` under
`OWNER_ACCEPTED_UNSIGNED_WINDOWS_BETA_1_2_0`; the Unknown publisher and
SmartScreen warning remain mandatory and are not relabeled as a pass.

## Hosted source and signing gates

- Platform PR 42 head `eea96ac...` passed Guardrails/Release v2 runs
  `33006615867`/`33006615938` and merged as candidate-bound `c5f3fca...`.
  Post-merge runs `33007643338`/`33007643354` pass.
- Client PR 21 head `59c873c...` passed Release v2 run `33014464548` and
  merged as candidate source `e6c29d1...`; post-merge run `33015545269`
  passes.
- Public release-index PR 5 passed run `33016740287`, merged as `4c6d46c...`,
  and passed post-merge run `33016796838`.
- Main-only signer run `33016840137`, job `98337138521`, produced the exact
  manifest/signature/receipt without reading or exporting the private key.
  Downloaded bytes pass the public-key validator at exact release-index Git
  revision `4c6d46c...`.
- The expiring Actions artifact is supplemented by the private client
  prerelease tag `pokrov-1.2.0-candidate.2-private-ci` at exact client source
  `e6c29d1...`. Its four GitHub asset digests match the installer and signed
  manifest outputs. This carrier is private/prerelease and is not stable.
- Release-index evidence PR 6 merged as `64f5350...`; post-merge contract run
  `33019900704` passes. It does not rewrite immutable signed candidate inputs.

## Exact Windows clean-host boundary

Workflow run `33017409577` used candidate manifest SHA-256 `1697a1bc...`,
installer SHA-256 `4226daa4...` and workflow commit `2b290a9...` on
GitHub-hosted Windows image `win25-vs2026`.

The retained run proves:

- a clean baseline without prior service/install owner/POKROV adapter;
- silent machine-wide install of the exact candidate bytes;
- byte identity for all eight installed manifest-bound files;
- an automatic LocalSystem service running the exact installed binary;
- authenticated UI-to-service IPC with an accepted status request;
- SCM stop/restart;
- clean uninstall of service, installed files and owner registry record; and
- unchanged idle route/DNS fingerprints with no residual POKROV/Wintun adapter.

The run does not prove live TUN/full-tunnel traffic, connected DNS/leak
protection, authenticated egress, sleep/reboot/crash recovery, uninstall while
connected or an interactive SmartScreen screen. Those remain
`MANUAL_OWNER_TEST`, so `REL/WIN-003`, `REL/WIN-004`, `REL/WIN-005`,
`REL/SEC-001` and broad `REL_DOD/DOD-04` do not become candidate passes.

## PB-14 candidate.2 replay

`scripts/release_1_2_pb14_candidate_gate.py` re-hashes all three signed outputs,
loads the public keyring from exact release-index Git object `4c6d46c...` and
verifies the detached signature. Operational candidate ID
`ad4dbea106386c9a9d58f29f15b530d5cb386ac4f00fa82534adbe4bba4233bf`
is bound to client `e6c29d1...`, Android x86_64 SHA-256 `b530ff25...` and build
4030.

In a temporary SQLite control fixture, one identity-free Android `UPD-004`
failure causes `release_health_gate_failed`; the staged state is preserved.
The guarded rollback request then sets the exact candidate to
`rollback_requested`/zero and the retained rollback candidate to
`current`/100. Production, deployment, public assets, stable pointer and
external artifact switch are all false/not performed. `OBS_PB/PB-14` remains
`I3`: current candidate evidence is stronger, but no deployed cohort exists.

## SPB dual-role boundary

The candidate-bound platform revision includes the deployed self-hop guard.
`ru_spb` is both a normal delivery node and the type-3 RU bridge; generated
configs now omit a bridge whose stable id or host identifies the selected
delivery node. This closes `client -> SPB bridge -> SPB delivery` loops.

The earlier physical Beeline observation still cannot be promoted to
candidate.2 proof. It showed SPB direct and type 3 unavailable while the
default and type-2 whitelist routes worked. Because direct SPB has no bridge
hop, the remaining failure is classified as a shared SPB entry-path/carrier
problem, not a remaining self-hop. Exact candidate.2 physical Beeline and OEM
testing is still `NOT_RUN`/`MANUAL_OWNER_TEST`.

## Ledger decision

Four bounded rows advance:

- `REL/REL-002`: `I3 -> I4` because the exact candidate client source has a
  successful release-bound hosted run and the candidate bytes pass the hosted
  clean-host workflow.
- `REL/REL-003`: `I3 -> I4` because the exact candidate platform revision has
  successful PR and post-merge Release v2/Guardrails runs with the strict
  client-root contract.
- `REL/WIN-002`: `I3 -> I4` because the exact candidate installer proves the
  machine-wide LocalSystem service boundary and authenticated UI/service IPC
  on a clean hosted Windows machine.
- `REL_DOD/DOD-04`: `I0 -> I1` only. The exact scope and a clean-host partial
  slice are verified, but live TUN, connected DNS and connected rollback are
  not run.

All other named rows retain their prior index. In particular,
`REL_DOD/DOD-15` stays `I2`, `OBS_DOD/DOD-29` stays `I4`,
`OBS_PB/PB-14` stays `I3`, `FE/P12-022` stays `I2` and `FE/P12-023` stays
`I3`.

The distribution becomes `I4=4`, `I3=307`, `I2=15`, `I1=38`, `I0=13`.
There are still 311 rows at or above `I3` and 66 below `I3`; pending stages
remain `0/31/14/21` for pre-freeze/candidate/external/deferred.

## Verification

- Exact release-index checkout `4c6d46c...`:
  `python -B scripts/validate_release_index.py --root . --require-ready
  --manifest <candidate.2 manifest> --signature <candidate.2 signature>` ->
  `READY_SIGNED_MANIFEST`, six artifacts, one owner-approved unsigned Windows
  exception.
- Candidate.2 PB-14 command ->
  `PASS_LOCAL_EXACT_CANDIDATE_HEALTH_STOP_AND_ROLLBACK_REQUEST`.
- `python -B -m pytest -p no:cacheprovider
  tests/test_release_1_2_pb14_candidate_gate.py
  tests/test_release_1_2_candidate_preflight.py
  tests/test_release_1_2_stop_ship_gate.py -q` -> `32 passed`.
- `python -B -m pytest -p no:cacheprovider
  tests/test_agent_docs_contract.py -q` -> `28 passed`.
- `python -B scripts/check_script_manifest.py` -> `PASS`.
- Machine-readable ledger parse -> 377 unique rows and exact distribution
  `13/38/15/307/4` for `I0/I1/I2/I3/I4`.
- Candidate preflight in expected-blocked mode -> `BLOCKED`, zero pre-freeze
  rows, 31 candidate rows, 14 external rows, 21 deferred rows. The pre-commit
  run also reports the current documentation worktree as dirty; this is not
  converted into candidate evidence.
- Live STOP-SHIP readback in expected-nonpass mode -> `BLOCKED`; all seven
  local regression anchors are present and `WIN-003` remains `NOT_RUN` for the
  live clean-host TUN/DNS/egress/rollback matrix.
- JSON parse and `git diff --check` -> `PASS`.

## Retained evidence

- `evidence/013AC-candidate2-reconciliation/013AC-candidate2-signed-manifest.json`,
  4544 bytes, SHA-256
  `4b158f03c942013fc0c736a9d240e3219059e043ade8e6caf55a8bcf1912a8cf`.
- `evidence/013AC-candidate2-reconciliation/013AC-windows-clean-host.json`,
  3904 bytes, SHA-256
  `5432122104bf2ea78ea6a373c1af6847d652007053f25a4a3a84cb8ecadd99b2`.
- `evidence/013AC-candidate2-reconciliation/013AC-pb14-candidate2-health-stop.json`,
  2636 bytes, SHA-256
  `075769e685e9e4636f0d56806428fd5604ccdb1e1c823b9240120589de2a60cd`.
- `evidence/013AC-candidate2-reconciliation/013AC-candidate2-reconciliation.json`,
  6722 bytes, SHA-256
  `cc4905e6ea784d07bb88de236c6458e43f66ac60697d9574275edecd32051c6b`.

## Next action

Run the exact candidate.2 Android bytes on the physical Beeline device and
retain direct/default/type-2/type-3, DNS/AI/Games content, Wi-Fi/LTE and final
disconnect evidence. Separately execute Windows live TUN/DNS/egress and
connected rollback/reboot/crash checks. Then collect exact-candidate
current/Brain/RU-origin and provider/Operator/legal evidence. Public `v1.2.0`
and stable promotion remain prohibited until required stop-ship gates are at
least `I4` and the user explicitly authorizes publication.
