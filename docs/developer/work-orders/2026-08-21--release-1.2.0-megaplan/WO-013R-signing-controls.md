# WO-013R — Fail-closed Windows and release-index signing controls

Status: `SIGNING_CONTROLS_MERGED_CANDIDATE_INPUTS_STILL_BLOCKED`
Phase: `11`
Rows: `REL/REPO-001`, `REL_DOD/DOD-02`, `REL_DOD/DOD-15`, `FE/P12-023`
Candidate: `NOT_CREATED`
Production/publication: `NOT_AUTHORIZED_NOT_RUN`

## Outcome

The explicitly authorized continuation slice merged two controls needed before
an exact 1.2.0 candidate can exist:

- client `main` `3cab149c5d54105900fdcdceb36bf616c729d2fa` adds a
  fail-closed Windows Authenticode release path;
- public release-index `main`
  `7d5e402c47186fbe2ea1eb30ee1dc8cafdf066b2` adds deterministic,
  secret-only Ed25519 candidate-index signing and artifact-only output.

These controls are source and hosted-gate proof, not signatures on an exact
candidate. No Windows signing certificate or support-mode production public
key was provisioned, no signed candidate index was generated, and no GitHub
Release, stable pointer, store publication or production mutation occurred.

## Windows signing control

Client PR 11 head `dbed065714bd967748875407ef1afb357f3e2131` passed the
complete `cross-repository-contract` job in run `32667486277`, job
`97263089736`, and merged under `OWNER_SOLO_EXCEPTION` as client `main`
`3cab149c5d54105900fdcdceb36bf616c729d2fa`.

The Windows release builder now accepts only a certificate selected from the
Windows Certificate Store by thumbprint or exact subject. It rejects partial
configuration, non-HTTPS timestamp URLs, absent private key or Code Signing
EKU, invalid validity/chain, self-signed material, signer mismatch and missing
RFC3161 timestamp. It signs the staged shell and service, delegates signed
setup/uninstaller generation to Inno Setup and verifies the final outputs.
The release manifest reports canonical `PASS` or `MISSING`; unsigned local
builds remain possible but are not promotable.

Focused Windows tests passed `6/6`; partial configuration failed closed;
unsigned manifest and installer smoke tests retained `MISSING`/`NotSigned` and
the prior setup SHA-256
`fd1de72735b735851e69a010914e1d6090f6466efaacd2d90b67d5f8ca830899`.
The full exact local client entrypoint, both Android flavors and Gradle release
build passed. Post-merge client run `32668204355`, job `97264860389`, repeats
the complete cross-repository contract and full standard client/Android flavor
gate successfully in 12m35s.

No trusted Windows code-signing certificate was found or supplied. Therefore
`WINDOWS_TRUSTED_SIGNING` remains `BLOCKED_BY_ACCESS`; none of the existing
unsigned Windows bytes gained release eligibility.

## Deterministic release-index signer

Public-index PR 2 head `ac3bfd511598ee2781d1aee788606949bc14d095`
passed run `32668457611`, job `97265476931`, and merged as
`0d416b56f0a26686638972e1b8c527bbad872a92`. It adds a signer that:

- accepts only an exact tracked candidate template from
  `candidate-inputs/1.2.0/` whose bytes and caller-supplied SHA match `HEAD`;
- canonicalizes JSON and produces a deterministic raw Ed25519 signature;
- reads private material only from `POKROV_RELEASE_SIGNING_KEY_PEM`, never a
  command-line or tracked-file input;
- validates schema, source revision, asset digests and public-key trust before
  atomically publishing output outside the checkout;
- refuses overwrites and leaves no output on template or key mismatch.

The manual workflow has `contents: read`, pinned actions, no persisted checkout
credential and a 14-day Actions artifact. It cannot publish a release or write
back to the repository. Local source validation passed; signer tests passed
`4/4`, including deterministic repeat output and fail-closed tamper/key cases.

The first merged workflow revision produced invalid-workflow run `32668483287`
before any job or signing step because a runner-only context was used at job
environment evaluation time. No secret was accessed. PR 3 head
`c003fe82373c4858865c20c8b9d1959a79ff2dba` moved that path to the runner
shell environment, added a regression assertion and passed run `32668539447`,
job `97265668849`. It merged as final public-index `main`
`7d5e402c47186fbe2ea1eb30ee1dc8cafdf066b2`; post-merge run
`32668571694`, job `97265747549`, passes. No new invalid workflow run exists
for that final SHA.

The owner-controlled Ed25519 secret is the release-index private half. It is
not an Authenticode certificate, and its value was never read or exposed.

## Candidate boundary

The 013Q pre-candidate artifacts remain immutable historical evidence for
client `3904734ce7761cc92c4136f1eaf13e20f2354f72` and public index
`491436889ef911de868d704e68ba86e77102b0f1`. They cannot be promoted after
these source-control changes.

The next possible build tuple is platform runtime source
`2ed944c5eaa667c44a7bc1970d2dd175ff34f8c9`, client
`3cab149c5d54105900fdcdceb36bf616c729d2fa`, Core
`bdbd97fae35103e705f55908caebf75b4a9ff72f` and public-index source
`7d5e402c47186fbe2ea1eb30ee1dc8cafdf066b2`. It is not frozen as a candidate:
adding the support-mode public key changes client inputs, and trusted Windows
signing changes final Windows bytes. The artifact set, checksums, SBOM,
provenance and strict handoff must all be regenerated afterward.

## Ledger decision

No row advances. `REL/REPO-001` and `FE/P12-023` remain `I3` with stronger
public source/signing-control evidence. `REL_DOD/DOD-02` and
`REL_DOD/DOD-15` remain `I2` because no exact signed candidate manifest or
trusted Windows artifact exists. Distribution remains `I3=309`, `I2=17`,
`I1=37`, `I0=14`; 68 rows remain below `I3`, with stage split
`0/33/14/21`.
