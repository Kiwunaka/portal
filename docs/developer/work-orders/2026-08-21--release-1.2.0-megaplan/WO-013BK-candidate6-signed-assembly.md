# WO-013BK — signed candidate.6 assembly

## Outcome

Create the replacement signed candidate from the resolver-corrected active
source without rewriting rejected candidate.5 or claiming that the remaining
runtime gates passed.

`pokrov-1.2.0-candidate.6` now binds platform
`5713324c1c0c2566befadf527bc09ec0ecf84a4e`, client
`b2497af7704d0aa6901541e175ce154b0eab05d7` and Core
`a45d69e40ed7d892619a2b5c4592a527f630665e`. Release-index PR `13` passed its
source-contract job and was merged under the already approved
`OWNER_SOLO_EXCEPTION` as `8d09ae5e8ec0c8347bcd4e2659944bdf7c9c9db3`.

The main-only signer run `33239993242` produced and independently revalidated
the exact manifest, detached Ed25519 signature and public receipt. The result
is a private Actions artifact only. It did not create a tag, GitHub Release,
public asset, store submission, stable pointer, deployment or promotion.

## Exact artifact set

| Artifact | Bytes | SHA-256 | Signing state |
|---|---:|---|---|
| `pokrov-android-arm64-v8a.apk` | `101366934` | `b583205db9e197c6de873264821319ef1108a2786f1ee5466501712568147296` | production Android certificate |
| `pokrov-android-armeabi-v7a.apk` | `90779172` | `6a1140109c55f79a30c94bb29caa5fa541953cf1c2f2c4ac14795dc2dd9ee408` | production Android certificate |
| `pokrov-android-market.aab` | `126269864` | `676ee2b1f5480d0bd66e58662399b758466ad1472862db5c87a145d2d44e05c1` | production Android certificate |
| `pokrov-android-universal.apk` | `295370385` | `3e3e27eb48f4351b9f8bf3f6bd386faf05ae058322de29ee8b3c94d53ef996d6` | production Android certificate |
| `pokrov-android-x86_64.apk` | `109952213` | `3d95d82d8290150fadd13600b79eca26326792407532f571909d8df224df6fa4` | production Android certificate |
| `pokrov-windows-setup-x64.exe` | `28931862` | `18a0b4293930959b31dfb41df55b94caad87ce2d574b4dfa2d12832e80307643` | `SKIPPED_BY_OWNER`; direct-beta SmartScreen warning |

All six staged files match the candidate template by name, size and SHA-256.
The strict-v2 handoff SHA-256 is
`9c3f810bd9eac9e69d61b25ff4f7c4a18fb8bc0a2b4dbefeec664877f76e23f7`;
its descriptor-set digest is
`85dc98079544392d82eacec45d1be99608664584422982eab8105d39b514992b`.
The CycloneDX SBOM and SLSA provenance hashes are respectively
`2fd9be4c7e9e11c2ee70b3e6efe8a2e6ac3277dfb73d2a12e701b3c9986383d1`
and `979f3223d8cb7f76b4e7c973abfcc0fa76d644cd99c74fa7230859a9f58e6693`.

The Windows runtime manifest is
`8facd602fb8eacb7077aa7ca122a261028526cf2871a7bf5ccda1af6e3b331f2`.
All `8/8` required staged files and the installer binding match. This is
package evidence only: the installer was not run on the non-isolated working
host.

## Signed manifest and source gate

- local exact-source quality gate: `15/15 PASS`;
- read-only candidate preflight: `READY_LOCAL_FREEZE`, zero blockers;
- release-index template SHA-256:
  `267525631724fb2aa64e98232ac415accb6e959c5ccd1321457b6c004c8f2e83`;
- signed manifest SHA-256:
  `8aac2458f8c43c0ef2955719dcede44f495d60acf681bc804bd6bf9828ee9054`;
- detached signature SHA-256:
  `2307906a920fb9b4dcd4c0025bf7628972668905d13897c553ddf27a81592dfa`;
- signing receipt SHA-256:
  `85dd34504d876086aa8bfe3533ad4db964e4f0a9106f9085657dc08c2c7afcaa`;
- independent result: `READY_SIGNED_MANIFEST`, trusted key
  `pokrov-release-2026-01`, six artifacts, one bounded owner-approved unsigned
  Windows artifact and `promotion_authorized=false`.

The physical phone contains exact candidate.6 ARM64 bytes and reports
`1.2.0+4046`. The owner keyguard was locked at capture time, so this proves
only install identity. It does not prove AWG, WARP, Smart DNS, per-app, OEM,
leak or lifecycle behavior for candidate.6.

## Release interpretation

- `REL/REL-001` remains `I3`: hosted signing and solo provenance are proved;
  independent review and branch protection remain explicitly absent.
- `REL_GATE/GATE-F` remains `I3`, not `GO`: candidate.5's frozen decision is
  immutable and candidate.6 needs a fresh digest-bound Gate F run.
- `FRKN_SMART_DNS/SMARTDNS-01` remains `I3`: candidate.6 binds the source
  contract, but no live resolver or access proof exists.
- `FRKN_PLAN/W9-05` remains `I1`: the exact-candidate metric decision is not
  made.
- No evidence is transferred from pre-candidate AWG/WARP/lifecycle runs into
  an exact-candidate runtime PASS.

Next: with the owner-unlocked phone, run candidate.6 AWG2/AWG3.1, WARP,
per-app, Private DNS/IPv6, OEM/Doze, leak and cleanup checks. Separately run the
unsigned Windows setup on a clean isolated Windows 10/11 host. Then regenerate
candidate.6 Gate F from exact evidence. Smart DNS stays undeployed until an
owned endpoint is deliberately freed through an independently reviewed
migration and rollback.

Machine evidence:
`evidence/013BK-candidate6-signed-assembly/013BK-candidate6-signed-assembly.json`.
Its SHA-256 is
`4fd43f8a83519f17b407ee32ff55840439c7b84a69ad75c8aea577e9e98eeacb`.
It contains no device serial, address, hostname, credential, private key,
runtime material, customer data or raw provider response.
