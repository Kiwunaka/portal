# WO-013P — Final source promotion under owner-solo controls

Status: `SOURCE_PROMOTION_COMPLETE_CANDIDATE_NOT_CREATED`
Phase: `01`, `02`, `11`
Rows: `REL/REL-001`, `REL/CORE-001`, `REL/TEST-001`, `REL_DOD/DOD-09`
Candidate: `NOT_CREATED`
Production mutation: `NOT_AUTHORIZED_NOT_RUN`

This WO is post-freeze documentation evidence. Its own documentation commit is
not added recursively to the frozen source tuple. Any candidate must check out
the exact platform commit named below, not a later documentation-only `master`
tip.

## Outcome

The final 1.2.0 source tuple was promoted through owner-authored pull requests
under the explicitly authorized `OWNER_SOLO_EXCEPTION`. No second reviewer or
independent approval is claimed. Before merge, the read-only live gate bound
all three exact PR heads and observed every required GitHub Actions check from
GitHub Actions app id `15368` as successful.

The signed promotion commits are:

- platform `Kiwunaka/portal:master`:
  `2ed944c5eaa667c44a7bc1970d2dd175ff34f8c9` from PR 20 head
  `672a245aac1481220d118463a3b65b7d63275790`;
- client `Kiwunaka/POKROV-app:main`:
  `3904734ce7761cc92c4136f1eaf13e20f2354f72` from PR 10 head
  `4864e439126263296a68ea8c1ba213f25c57a5fb`;
- Core `Kiwunaka/pokrov-core:main`:
  `bdbd97fae35103e705f55908caebf75b4a9ff72f` from PR 2 head
  `0e6b0204d764ae6b1d726343f487a7004d13393b`.

Client and Core squash merges preserve the exact checked PR trees. The
platform merge also includes the already merged, retained PR-00 base additions;
therefore its merge tree is intentionally not mislabeled as identical to PR 20.
Both platform post-merge workflows passed on the final `master` revision.

## Hosted and artifact evidence

Exact PR-head evidence:

- platform PR 20: `repo-guardrails` run `32654545629`, job `97231156363`,
  and `cross-repository-contract` run `32654545639`, job `97231156549`;
- client PR 10: `cross-repository-contract` run `32655837199`, job
  `97234316532`, including the full standard client gate and both Android
  flavors;
- Core PR 2: run `32619396382`, with all five required jobs successful.

Exact post-merge evidence:

- platform `repo-guardrails` run `32655166506`, job `97232627244`, and
  cross-repository run `32655166477`, attempt 2, job `97236501345`;
- client run `32656692926`, job `97236406043`, including the full standard
  client gate and Android flavor builds;
- Core run `32651975372`, with `test`, `release-contract`, Android and Windows
  reproducibility, and Apple source-build jobs successful.

The final Core source was built locally twice per shipped lane. Android local
builds are byte-identical with AAR SHA-256
`83a5bd740774a2a16117f0c242c3ada4bcbb22a65255c3ee008a751e681c06f0`
and tree SHA-256
`565266016cf823b30a36645c37156a8ba69d3f0fd55f8b22df665c321bcfcc90`.
Windows local builds are byte-identical with DLL SHA-256
`ef9672b3ba9983012bfa78abd2e4cd8ef5ef65d8e4b6a49ff89f8c4d0d575040`
and tree SHA-256
`32089d0e133703433f43e4e8041f45fdf931e937bfb9ca10f2a72725a5c24d9f`.
The final client `main` embeds those exact AAR, DLL and Cronet bytes. The Core
hosted Linux Android artifact is reproducible within its runner but is not
claimed byte-identical to the Windows-produced embedded AAR.

## Live gate and index decision

The final clean read-only report binds all three merge commits. Seven of seven
permanent regression anchors and all three owner-solo PR controls pass. The
report remains `BLOCKED`, not `PASS`, solely because exact-candidate Windows
10/11 clean-host TUN, DNS, egress and rollback evidence is `NOT_RUN`.
`candidate_proven=false` is retained.

The 8,248-byte report has SHA-256
`71512121d6c9b0ccd9c73423056a14707e11a1db7a2027ca851ad04130927109`;
the registry SHA-256 is
`dbe322645bc9d7da9e343f90267675e51dbf12f793eaf470f4a54562e6129e4a`.
Transient GitHub API failures remained fail-closed in three earlier report
attempts; a later complete readback produced one retained 3/3 result rather
than merging partial observations by hand.

`REL/REL-001` and `REL_DOD/DOD-09` advance `I1 -> I3`. The owner-solo review
decision, exact PR heads, required app-bound checks, PR-only merges, signed
promotion commits and final promotion-branch runs are now retained. This is
source-promotion proof, not an exact-candidate or production proof.

Distribution becomes `I3=309`, `I2=16`, `I1=37`, `I0=15`; 68 of 377 rows
remain below `I3`. Pending stages become `0/33/14/21` for
pre-freeze/candidate/external/deferred. Candidate construction, signing,
physical-device/clean-host, origin, provider, rollback and stable-promotion
evidence remain unperformed and are not authorized by this WO.
