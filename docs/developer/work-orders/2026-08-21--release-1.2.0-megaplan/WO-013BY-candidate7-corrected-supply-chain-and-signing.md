# WO-013BY — candidate.7 corrected supply chain and signing

## Outcome

Create a replacement signed candidate whose supply-chain evidence matches the
final platform verifier merge without rebuilding unchanged client/Core
binaries or rewriting candidate.6 history.

`pokrov-1.2.0-candidate.7` binds platform
`af259f377ec7a3cd757f0f43762154dd25e09f94`, client
`b2497af7704d0aa6901541e175ce154b0eab05d7` and Core
`a45d69e40ed7d892619a2b5c4592a527f630665e`. Client and Core are unchanged
from candidate.6, so the six build `1.2.0+4046` files were reused only after
name, size and SHA-256 equality checks. No binary rebuild or production deploy
occurred.

## Corrected exact supply chain

The final platform source adds an offline fail-closed verifier for the fixed
six-file artifact set, strict-v2 handoff, CycloneDX 1.5 SBOM, in-toto/SLSA v1
provenance, exact Core AAR/DLL and Windows runtime manifest. Its focused suite
passes `78/78`; Ruff, compile, script-manifest and diff checks pass. The final
security diff scan covers `2/2` changed source files and reports zero findings.

Candidate.6 is retained unchanged and now serves as negative regression
evidence: the verifier rejects its stale SBOM at
`sbom_source_revision_mismatch`. Candidate.7 replaces those metadata bytes:

- strict-v2 handoff SHA-256:
  `06e94a9f6a8821e41f7acb36eed33dbb09da8ba39b9e4fcdef6feac42861e831`;
- CycloneDX 1.5 SBOM: `349` components, SHA-256
  `5951587d47aecb0719839ad9f3c169da038f79d649b9ab4083c5b6a5e6e4633e`;
- SLSA provenance: six exact subjects, SHA-256
  `8cddf4ea90d1a30f71068d027bb78462a5f5008e0a42ebb56647587b1a12f876`;
- support-pin evidence SHA-256:
  `c738296f2c49445d4380a6a17536942863f5fa729a8783a8a65f71097d6a495e`;
- Windows runtime manifest SHA-256:
  `8facd602fb8eacb7077aa7ca122a261028526cf2871a7bf5ccda1af6e3b331f2`.

The corrected SBOM removes the obsolete `flutter_displaymode@0.6.0`, uses the
current client production closure and current Core source-SBOM union, and binds
Core AAR
`ce82f54b073645fbd7ea0cc7ba576597456627cb5d0c7d80926afaa1dba154dd`
plus DLL
`53b5e82a9c7bc20055c0889a1c8fabb5137f52ad09d38b23cf86477184474652`.
The Windows manifest and SBOM agree on all `8/8` runtime files. The complete
offline candidate validator returns `PASS` for `6/6` artifacts; its report
SHA-256 is
`56396f64812614bfab961e9c7bec795b6abde2be97bd503a5aff20325e7ea6c2`.

The exact final local source gate passes `15/15`, and read-only preflight
returns `READY_LOCAL_FREEZE` with zero blockers. These prove source and package
binding only; they do not prove device, origin or promotion readiness.

## Signed private candidate

Release-index PR `15` passed source-contract run `33256936721` and was merged
under `OWNER_SOLO_EXCEPTION` as
`f6917c8264015aee72fe51126943b08191e85b07`. Main-only signer run
`33256988566` then produced and independently revalidated:

- manifest SHA-256:
  `fb1d7049deaf3047456377e675c45a2177c76c51f8792703886ca2bcca5490ce`;
- detached Ed25519 signature SHA-256:
  `2b20ed7881c36f72b0777aa8c2a571e192895df15eb598165d5e93ae68418abf`;
- public receipt SHA-256:
  `ff93d33bf0ef4b0e1b036ee1be5b83f769791295d0e1cfcde0a1f854b2799b04`.

Independent readback returns `READY_SIGNED_MANIFEST`, trusted key
`pokrov-release-2026-01`, six artifacts and one narrowly owner-approved
unsigned Windows artifact. Receipt PR `16` also passed its source-contract
check and recorded the result on release-index `main` at
`9e5b7bd3be3b8468e733bb30da829c7f91f6235a`.

This is an Actions-artifact-only candidate. No tag, GitHub Release, public
asset, Google Play submission, stable pointer, production deploy or promotion
was created. `promotion_authorized=false`. Independent review and branch
protection remain explicitly absent under the owner's solo exception.

## Release interpretation

- `REL/REL-001` remains `I3`: exact candidate.7 signing and corrected
  provenance are proved, but branch protection, independent review, public
  same-byte assets and stable promotion are absent.
- `REL_GATE/GATE-F` remains `I3`: candidate.6's `4 PASS / 15 non-PASS`
  decision is immutable, while candidate.7 has not yet received a fresh
  digest-bound Gate F run.
- `FRKN_PLAN/W1-03` remains `I3`: candidate.7 now binds the corrected
  full-product SBOM and signer, but public release/notices mapping and final
  promotion proof remain open.
- `FRKN_PLAN/W9-05` remains `I1`: no candidate.7 metric-based go/no-go exists.
- No pre-candidate or candidate.6 Android result is silently relabelled as an
  exact candidate.7 runtime `PASS`, even though the artifact bytes are equal.

The next device work is exact candidate.7 on LDPlayer and the returned
physical Android phone: ordinary control, AWG2, AWG3.1, WARP, per-app,
Private DNS, IPv6/leak, lifecycle and final cleanup. Windows still requires an
isolated Windows 10/11 install/service/TUN/DNS/egress/recovery/uninstall run.
The local Raspberry Pi 4 is accepted as a terminal-only direct-RU probe, but
its trusted SSH alias or `user@local-IP` is still required before any retained
RU-origin test. Passwords and private keys must not enter chat or evidence.

Machine evidence:
`evidence/013BY-candidate7-corrected-supply-chain-and-signing/013BY-candidate7-corrected-supply-chain-and-signing.json`.
Its SHA-256 is
`08a1477aaa4306d2811b98aec242b3bdd0cf918f5ca2d9beddffb7c2cf510d39`.
It contains no device serial, address, hostname, credential, private key,
runtime material, customer data or raw provider response.
