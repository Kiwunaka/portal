# WO-013GH — candidate.32 Android static signing and bundle validation

Status: `PASS_EXACT_ANDROID_STATIC_SIGNING_BUNDLE_AND_DISTRIBUTION_SEPARATION; DEVICE_STORE_AND_PUBLIC_READBACK_OPEN`

Observed: `2026-09-04T01:19:37Z`

Production/public mutation: `NONE`

## Outcome

Independently validate the five exact Android files already bound by the
private signed candidate.32 release index. This slice reads the immutable
candidate files in place and uses no application install, phone, emulator,
VM, host UI, route, DNS or tunnel mutation.

All four APKs pass `apksigner`, `zipalign` and `aapt2`:

- APK Signature Scheme v2 validates with one signer;
- signer SHA-256 is the expected production certificate
  `0a0602a7...4b2500` on `4/4` files;
- package `space.pokrov.pokrov_android_shell`, version `1.2.0 (4053)` and
  non-debuggable state match on `4/4` files;
- universal, ARM64, ARMv7 and x86_64 native-code sets match their artifact
  contracts;
- all four archives pass page-aware zip alignment.

The AAB passes official `bundletool 1.18.1 validate` and manifest inspection.
It contains the same package/version, is not debuggable, disables backup and
contains Core payloads for ARMv7, ARM64 and x86_64. `keytool` reads the same
certificate fingerprint, and non-strict JAR integrity verification exits `0`.

The already-signed distribution artifacts also preserve the intended update
boundary. The direct universal APK contains
`android.permission.REQUEST_INSTALL_PACKAGES` and one non-exported
`androidx.core.content.FileProvider` at
`space.pokrov.pokrov_android_shell.updates` with URI grants enabled. The Store
AAB contains none of that direct-update permission, provider or authority.
Focused direct/store source-contract tasks pass `10/10` tests across
`AndroidManifestPermissionsTest` and `AndroidUpdateFlavorContractTest`.

## Strict JAR warning boundary

`jarsigner -strict` exits `4`, so the result is retained rather than hidden.
It reports the expected self-managed self-signed upload certificate without a
public PKIX chain or timestamp, plus POSIX-attribute and
`JarFile`/`JarInputStream` visibility warnings. The authoritative Android
bundle structural validator exits `0`; this is therefore a local bundle and
signature-integrity pass, not Store acceptance, Play App Signing or a public
trust-chain claim.

No AAB is submitted. Store status remains `NOT_REQUESTED`.

## Signed-index binding

All five Android files independently match the size, SHA-256, signer
fingerprint, SBOM and provenance references in signed release index
`b15938e1...da449`. Candidate source identity remains:

- platform `d0dd37c1003198ba08cffc49a040a77e21621a86`;
- client `2d6adfcebc37f2109ef339276be6a1569cb7aa1e`;
- Core `cd8f0f4169d570d693992a959d81d17c2c44884d`;
- release index `5d11fd6821a5ebfa42163f461332125143c553c3`.

This supersedes candidate.21 references in four signed-supply ledger rows but
does not change their completion level:

- `REL_DOD/DOD-02` stays `I2`;
- `REL_DOD/DOD-15` stays `I2`;
- `FE/P12-022` stays `I2`;
- `FRKN_ADOPT/ADOPT-05` stays `I2`.

It also replaces the active candidate reference in `REL_DOD/DOD-05`, which
stays `I3`: static direct/store separation now belongs to candidate.32, while
physical direct-installer permission/upgrade and Play-managed update remain
open.

Installed Android identity/runtime, public same-byte assets, Windows trusted
publisher identity and stable promotion remain open. Gate F is not regenerated
and remains `BLOCKED 2/17/0` under WO-013GG.

## Commands and results

```text
apksigner verify --verbose --print-certs <four exact APKs>
  -> 4/4 PASS; v2=true; signer_count=1; certificate exact
zipalign -c -P 16 -v 4 <four exact APKs>
  -> 4/4 PASS
aapt2 dump badging <four exact APKs>
  -> 4/4 package/version/ABI/non-debug exact
bundletool 1.18.1 validate --bundle=<exact AAB>
  -> PASS_EXIT_0
bundletool 1.18.1 dump manifest --bundle=<exact AAB> --module=base
  -> PASS_EXIT_0; package/version/debuggable/backup exact
aapt2 dump permissions/xmltree <exact direct APK>
  -> REQUEST_INSTALL_PACKAGES and private .updates FileProvider present
bundletool 1.18.1 dump manifest <exact Store AAB>
  -> direct install permission/provider/authority absent
Gradle 8.11.1 testDirectDebugUnitTest + testStoreDebugUnitTest
  -> 10/10 PASS across manifest and update-flavor contract suites
keytool -printcert -jarfile <exact AAB>
  -> expected certificate SHA-256 and RSA-4096 key
jarsigner -verify <exact AAB>
  -> VERIFIED_EXIT_0_WITH_WARNINGS
jarsigner -verify -strict <exact AAB>
  -> WARN_EXIT_4; warning classes retained above
```

## Evidence

- normalized record:
  `evidence/013GH-candidate32-android-static-signing/013GH-candidate32-android-static-signing.json`;
- normalized record SHA-256:
  `de8ea5fee90a0f1501d6dd0ad8e44848faec64bc0ab86c262023141fad4d5aa0`;
- official bundletool binary SHA-256:
  `675786493983787ffa11550bdb7c0715679a44e1643f3ff980a529e9c822595c`.

The normalized record contains no signing material, private key, credential,
provider payload, customer data or connection configuration.

## Follow-up

When an isolated Android target is available, install the exact ABI-matched
candidate.32 APK and retain installed-byte/package/signer readback before
running default, AWG3.1, AWG2, Smart DNS, network-switch, leak, lifecycle and
clean-restore matrices. Separately exercise direct-installer permission and
retained-settings upgrade plus a Play-managed update when Store work is
authorized. Do not transfer static validation into device or Store credit.
