# WO-013DZ — Reject candidate 18 and bind signed private candidate 19

Status: `CANDIDATE19_SIGNED_PRIVATE_FOUNDATION_PASS_NETWORK_GATES_OPEN`

Observed: `2026-09-01`

Production/public mutation: `NONE`

## Outcome

Candidate 18 is immutable `NO_GO`. An ordinary non-admin Windows UI attempted
to authenticate its LocalSystem service through process-token access. Windows
denied that access, the UI classified the correct service as untrusted, closed
the pipe and the service exited with code `5`. The exact reproduction is
retained outside Git with SHA-256
`4042ad57ab0280e59b8b65a990831ed8f0d8d38d08d18455dff9e6cec90cfba8`.

Client PR 54 replaces that check with a protected SCM-service record: the
service must be running under the exact PID, own-process service type, exact
sibling binary path and LocalSystem account. Existing pipe ACLs and
server-side caller authentication remain unchanged. The PR, its retry and the
post-merge exact-main run pass; client `main` is
`10f5516648fd40d6c94eb7a7ca0d05be161d393c`.

That merged correction is rebuilt into signed private candidate 19. Nothing
is tagged, published, uploaded to a Store or promoted to stable.
`promotion_authorized=false` remains authoritative.

## Exact signed candidate

| Item | Value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.19`, `1.2.0+4049` |
| Platform | `d6898e63c5c9ab7dd267b9d5150b54196f99d967` |
| Client | `10f5516648fd40d6c94eb7a7ca0d05be161d393c` |
| Core | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Signed release-index source | `43fc20fd25342f314554a89ef75e1122f00aee01` |
| Receipt merge | `fd00eb38ad9c3906bfd3ba5ec1210136c224d76f` |
| Manifest SHA-256 | `bb78970700d8dc51b6b31caabb76a9b4ca6c94da2f8eef82f1c99ab61b5e6a87` |
| Signature SHA-256 | `1d39b7bb7b20481bd165348abc1321ccd9ef4131021505c4054a8c22f6c24e38` |
| Signing receipt SHA-256 | `12b2de4a89eb2fa48e359bc740b39c924941a725d97009387b6343a047094f84` |
| Release handoff SHA-256 | `ac372450fb98245cd3aa8b34700f94fbf6a6fc48a2de9687df4c49167e4ec317` |
| Artifact-set SHA-256 | `0640a329c479a12dc3b600e0313ea164c2b6cb511fca98e5575fa2da41d9c709` |

All five Android artifacts are production-signed. Windows setup SHA-256 is
`0782152d3a992b1b6320043b9b8ccedb2944b76dcbf939bf7a6ebdad9759f8ff`;
it remains `SKIPPED_BY_OWNER` for trusted signing under the approved direct
beta exception and therefore requires the explicit SmartScreen warning. The
11-file Windows manifest, 352-component SBOM, six-subject provenance and all
six supply bindings pass.

Signer run `33489470612` passes and produces retained artifact `9793146917`.
Release-index PRs 39 and 40 pass their hosted source contract and merge. Exact
cross-repository replay run `33489959772` passes the release-handoff contract,
client/Android-flavour tests and conditional Linux foundation against the
four pinned revisions above.

## Windows and rollback

The isolated Windows 11 VM proves exact candidate 19 under an ordinary user:

- non-elevated UI opens the authenticated service IPC and both processes stay
  alive;
- the protected journal records the accepted IPC session and status request;
- clean uninstall passes;
- public `1.1.6` per-user installation migrates to candidate 19 machine-wide
  and the final uninstall restores clean app state.

Aggregate Windows-foundation evidence SHA-256 is
`949754060cf4386ab961bbf323c60120f6350e4ecf7f15dadcfa9ac36fcbdc5e`.
Connected TUN, DNS, authenticated egress and recovery remain `NOT_RUN`; this
foundation result cannot replace them.

The exact signed tuple also passes an isolated portal/client sequence
`1.1.6 -> candidate.19 -> 1.1.6`. Portal state and the retained stable handoff
restore byte-identically, unrelated fixture state survives, and production,
public and tracked stable pointers remain unchanged. Rollback evidence
SHA-256 is
`9ac2f0a4eb4bbdd46ae7a5f812d930e3e14d99ae8b8ac1cb6fb9ec55ad3038df`.
A real guarded runtime rollback plus current/Brain readback remains open.

## Android boundary

LDPlayer receives only install/launch credit. The exact x86_64 artifact and
installed `base.apk` both hash to
`a0afffdc62800c525ebea96904550a2fd24a91cb4de565652618bddca378fee4`;
version `1.2.0 (4049)`, ABI, Activity launch, five-second process survival and
zero package crash-buffer matches pass. The app is force-stopped after the
check.

LDPlayer network, DNS and egress are excluded because host Windows already has
an active Hiddify/TUN. No emulator is nested inside the Windows VM. Exact
physical ARM64 Wi-Fi and Beeline runtime remain `MANUAL_OWNER_TEST`.

## Named-origin refresh

Brain source comparison passes `197/197`; readiness passes `23/23` with five
stable subscription samples. Delivery samples are retained in order:
`6/7` with `de remote_exec_error`, `7/7`, `6/7` with
`it remote_exec_error`, then three consecutive `7/7`. The two non-PASS
management-command samples are not erased or relabeled. The final Brain slice
is `PASS_WITH_RETAINED_TRANSIENT_MANAGEMENT_SAMPLES`; every final sample,
including `ru_spb`, is open.

Current-origin sockets are bound to the assigned physical `Ethernet 2`
address with proxy discovery disabled, excluding the ambient host tunnel.
Fifty-sample p95 is `38.1649 ms` for health against `100 ms` and
`42.2156 ms` for public catalog against `200 ms`; both pass. Permanent
STOP-SHIP anchors pass `7/7`, while the aggregate remains `BLOCKED` on hosted
policy/manual state. Authenticated client egress is still `NOT_RUN`.

## Decision and open gates

Candidate 19 is the only current private candidate. Gate F is not regenerated
and Gate G remains unauthorized. Before another Gate F decision, complete:

- physical ARM64 Wi-Fi and Beeline runtime;
- connected Windows TUN/DNS/egress/recovery;
- authenticated current-origin client and RU-origin;
- provider/payment, PostgreSQL/outbox, Operator OIDC/RBAC and legal/commercial;
- comparable device performance, accessibility/OEM/endurance;
- guarded runtime rollback with origin readback;
- final no-open-P0, false-green and privacy attestation.

No tag, GitHub Release, public asset, Store object or stable pointer exists for
candidate 19.

## Evidence

- normalized record:
  `evidence/013DZ-candidate19-reconciliation/013DZ-candidate19-reconciliation.json`;
- normalized record SHA-256:
  `fa16249bd272e4366852a2827c4e595ae91c1e56908417677a12557d85e76de2`;
- private candidate root:
  `E:/POKROV-tools/release-candidates/pokrov-1.2.0-candidate.19`;
- external Windows, rollback, LDPlayer and named-origin evidence remains under
  `E:/POKROV-tools/` and contains no retained credential, customer payload or
  device identifier in the tracked record.
