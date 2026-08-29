# WO-013BO — candidate.6 PB-14 exact build binding

## Outcome

Correct a false-exact release-health harness boundary without rebuilding or
resigning `pokrov-1.2.0-candidate.6`.

The first candidate.6 PB-14 execution exposed that the incident fixture still
used fixed historical Android build `4030`. Candidate.6's signed physical
install evidence instead binds product `1.2.0`, build `4046` and exact ARM64
artifact SHA-256
`3d95d82d8290150fadd13600b79eca26326792407532f571909d8df224df6fa4`.
The old output is therefore retained only as
`INVALID_HARDCODED_4030_NOT_RELEASE_EVIDENCE`; its SHA-256 is
`c62f82c61425ae3bec1b7dda72040cf4c45bcaa15867e49e70786a43fd2613f1`.

Platform commit `a12a0a84212167ae579c6274d9e0308effe710cd`, merged by PR
`65` as `c4788f78b8eb8baa11a21ebaeb1caf1ae4195a17`, now derives the
Android build from required signed physical-install evidence only after its
package hash matches the candidate ARM64 artifact. It also verifies the
product version and fails closed on absent, malformed or drifting identity.
No candidate artifact, manifest, signature or receipt changed.

The corrected isolated run binds build `4046` in both the candidate and the
injected identity-free `UPD-004` event. Signature verification, promotion
stop, staged-state preservation and guarded rollback request all pass. The
candidate rollout request reaches zero and the rollback target reaches 100%,
but no external artifact switch, public promotion, stable-pointer change,
deployment or physical-device mutation occurred. Corrected external report
SHA-256 is
`2b23408d7d04a40ba6dc7b8f90961dc675c6602a7954b997d9263cd53685a028`.

## Evidence ceiling

- `OBS_PB/PB-14` remains `I3` with stronger exact candidate.6 build-4046
  local evidence.
- `OBS_DOD/DOD-23` remains `I3` with the same stronger evidence.
- `REL_GATE/GATE-F` remains WO-013BM's
  `3 PASS / 16 non-PASS / 0 FAIL`: a local stop/request does not prove a live
  cohort, deployed ingest/readback, external artifact rollback or
  post-promotion health.
- Platform and client hosted PR checks ended with zero steps under
  `OWNER_SOLO_EXCEPTION`; they are `SKIPPED_BY_OWNER`, not PASS.
- Candidate.6 keeps the original signed manifest/signature/receipt and exact
  source/artifact tuple.

Focused harness tests pass `5/5`; Ruff and compileall pass. Normalized evidence
is
`evidence/013BO-candidate6-pb14-build-binding/013BO-candidate6-pb14-build-binding.json`;
its SHA-256 is
`439cbdc53fc9eec36825535d414af5113bcad5db24b9fa68db9addbacd602266`.
It contains no address, hostname, credential, key, customer data, raw
connection material or provider payload.
