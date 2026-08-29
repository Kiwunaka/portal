# WO-013BC — Core artifact convergence and Windows pre-candidate assembly

## Outcome

Android and Windows now consume byte-reproducible Core artifacts from the same
clean source revision, `3c2b1147c1b42e39026231525c08558a50bc3d0f`. The
Android AAR and Windows DLL were each built twice with byte-identical results,
their build trees and evidence documents were hashed, and deterministic Core
and sing-box SBOM inputs were retained. Client commit
`75aabd9819b0e2dfd36efa3ddf7a8d7aa63a562c` binds those exact bytes; client
documentation commit `55e7d5c8b653b16d850e0d55b797d65f11893988` records the
result and its remaining gates.

This closes the local single-source Android/Windows artifact-convergence
prerequisite. It does not create a Core tag, client release candidate, signed
Windows binary, public asset or promotion decision.

## Exact Core artifacts

| Platform | Artifact | Size | SHA-256 | Reproducibility result |
|---|---|---:|---|---|
| Android | `pokrov-core.aar` | `107408874` | `b42a548910b7369f64fcd484c5acf74180583d77299629ce4d2f9156fc598007` | two builds byte-identical; four required ABIs present |
| Windows x64 | `pokrov-core.dll` | `55417856` | `58e329eaddb2dd1f40c1663b380a03a0c7c34c5a3e8506eb2c692611234ac082` | two builds byte-identical; 15 required exports present |
| Windows dependency | `libcronet.dll` | `8596992` | `8ef1f8bbde77f954af1ae47bee1819ac8dc2354bb0e1d4baba3dad9e58d7a6f7` | unchanged retained dependency |

The Android tree/evidence SHA-256 values are respectively
`c0860173aa4a18d2e1864ecb8595ed809e38d6f394b781a6572299534e893d30`
and `077e0dd9b1c0349ae065434e38b0110cc17ea547cd251623fcd743ed15ee39e5`.
The Windows tree/evidence values are
`25feb38570f049d4053f8632826fb8b2a254665db3b771a84878b7e013312dde`
and `98b984109a3df227262179d1c3cbf46c8f0abbde0049187fb83db088a444e9c6`.
The Core and sing-box CycloneDX inputs hash to
`d6847ac8ba97675d62b7021a8d2d89ce5dc6a38a58c0c1afb82321fca121d30a`
and `338c18be688ee0892851b93e2a5c659b79660d868af4a1f0070a80d0fc23096b`.

The production-signed physical Android replacement artifact from WO-013BB
embeds an ARM64 Core library whose digest exactly equals the ARM64 entry in this
AAR. Its AWG2 and AWG 3.1 physical Beeline result therefore remains relevant to
this same Core source. It is still pre-candidate proof and is not transferred
into an exact-candidate row.

## Windows pre-candidate assembly

Clean client source `75aabd9819b0e2dfd36efa3ddf7a8d7aa63a562c` produced
`pokrov-windows-x64-1.2.0+4046-setup.exe`, size `28928829`, SHA-256
`f12dc8da726aa621834d630eca7b625388553dd131e7e71f7ff165724a26e6fa`.
Its build manifest hashes to
`442597ca283dcb40cc4e9c3dde5a572f2cc780f6f0a0af62f62d36bcc7a32946`,
binds all eight required bundle files and contains the exact Core DLL above.

The setup is Authenticode `NotSigned`. The retained status is
`SKIPPED_BY_OWNER` under `OWNER_ACCEPTED_UNSIGNED_WINDOWS_BETA_1_2_0`, with a
mandatory SmartScreen/unknown-publisher warning. This permits one unsigned
direct-download beta path only; it does not establish trusted signing, Store
readiness or broad-stable trust.

The exact Core DLL passes 100 proxy-only start/stop cycles. This proves DLL
loading, ABI compatibility, local proxy startup and bounded teardown without
changing host routes. It does not exercise installation, SCM service control,
TUN, DNS capture, authenticated egress, leak protection, sleep/reboot/crash
recovery, uninstall while connected or interactive SmartScreen behavior.

## Clean aggregate result

The local aggregate rerun used clean platform
`882f287a0e4900f3da0b1992c7e153bd2a588cdbb`, clean client
`55e7d5c8b653b16d850e0d55b797d65f11893988` and clean Core
`3c2b1147c1b42e39026231525c08558a50bc3d0f`, with pinned Node `22.14.0` and
lockfile-exact frontend dependencies. All `15/15` steps passed, including the
client static/widget/contracts, webapp lint/build/69 browser tests,
marketing build/SEO/responsive checks, admin build and all `9/9` local static
performance stops.

The report is retained outside candidate artifacts at
`E:/POKROV-tools/builds/release-1.2.0-local-quality-20260829-awg-converged-rerun/010I-local-quality-gate.json`,
SHA-256
`ca84626431041a0d29bef42d7d7132475baf066a16f900ed8a8149fc3e27dd26`.
It explicitly states `candidate_proven=false`, local `PASS` and promotion
`MANUAL_OWNER_TEST`. The first attempt remains retained separately as an
environment-setup failure caused by missing clean-worktree dependencies and an
unpinned ambient Node runtime; it is not overwritten or relabelled as a product
failure.

## Release interpretation

- Candidate.5 remains immutable and `REJECTED_FOR_REPLACEMENT`.
- Phase 10 remains `I3`; no source-plan row advances to `I4`.
- Gate F does not advance and no replacement candidate exists yet.
- Android/Windows now bind one exact Core source locally.
- Windows artifact assembly exists, but live Windows app/service/TUN/DNS/AWG
  parity remains `MANUAL_OWNER_TEST`.
- Exact-candidate Android repeat, DNS/leak/origin, performance, provider,
  Operator, legal/commercial and post-promotion evidence remain open.
- No tag, upload, deploy, public release, Store object or stable switch occurred.

The next bounded slice is exact Windows app/service/TUN execution for AWG2 and
AWG 3.1 in an isolated Windows host, including DNS/egress/leak and cleanup
readback. Only then should a new digest-bound replacement candidate be assembled
and the exact-candidate Android repeat plus Gate F be run.

## Verification and retained evidence

The client full gates, Android Gradle flavor unit builds, exact DLL cycle test
and clean cross-repository local aggregate pass. Platform documentation,
context, candidate-preflight and manifest tests pass `59/59`; performance/local
gate tests pass `23/23`; the platform-context audit, link check, script manifest
and diff check pass. Machine-readable evidence is retained at
`evidence/013BC-core-artifact-convergence/013BC-core-artifact-convergence.json`,
SHA-256
`0857249541c53cee0eeb51d01796bd0a17407fdd1f54866d266f25d8b8a7a2b4`.
It contains no raw address, device identity,
account identity, key, credential or endpoint material.
