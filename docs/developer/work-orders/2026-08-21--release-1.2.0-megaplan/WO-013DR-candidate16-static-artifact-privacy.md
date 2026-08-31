# WO-013DR — candidate.16 bounded static artifact privacy scan

Status: `PASS_BOUNDED_STATIC_ARTIFACT_PRIVACY_SCAN; AGGREGATE_RUNTIME_GATE_OPEN`
Classification: `ACTIVE_EXECUTION_EVIDENCE`
Phase: `11`
Candidate: `pokrov-1.2.0-candidate.16`
Production/external mutation: `NONE`

## Outcome

Inspect the immutable candidate.16 Android and Windows distribution bytes in
the background without taking screen or input control. All six distribution
files match the exact sizes and SHA-256 values in the signed release index.

The five Android archives expose `1891` entries after extraction. A binary
scan finds zero complete private-key blocks, populated authorization values,
credential assignments, high-confidence connection URIs or known live-token
shapes. The exact Windows installer returns the same zero-result direct scan.
Its manifest-declared staging tree contains `300` files; all `8/8` required
payload files match their declared sizes and hashes, and the complete staging
tree returns the same zero-result definite scan.

This is a bounded static result. It does not replace physical-device runtime
journals, Windows connected operation, encrypted support-bundle flow,
deployed ingest validation or the final aggregate owner attestation.

## False-positive triage

The broad discovery pass sees three protocol scheme prefixes and one private-
key parser marker in the exact Core binary. Exact source correspondence at
`cd8f0f4169d570d693992a959d81d17c2c44884d` accounts for these as dispatcher
keys (`vless://`, `wg://`, `wireguard://`) and a parser prefix. Go's packed
string table places adjacent literals next to the scheme bytes, so a broad
binary regex can read them as one long token.

The strict pass therefore requires a complete protocol credential/endpoint
shape. For WireGuard-like candidates it additionally requires valid base64 or
base64url plus decoded private-key or endpoint semantics. Android has twelve
ABI-duplicated broad candidates representing two unique fingerprints;
Windows has one. None decodes as a valid payload and none contains decoded
private-key or endpoint semantics. Complete private-key blocks remain zero.
No matched value or raw local path is retained.

## Windows extraction boundary

The available extractor rejects this installer's loader revision, so no
claim is made that it independently unpacked the candidate EXE. The retained
Windows result is limited to:

- exact installer SHA-256 equality against both signed and build manifests;
- direct raw-binary scanning of that exact installer;
- `8/8` size-and-hash verification of the build-manifest required payloads;
- scanning all `300` files in the manifest-declared staging tree.

That is useful static evidence, but it is not a byte-for-byte independent
reconstruction of the compressed installer payload.

## Evidence

- normalized record:
  `evidence/013DR-candidate16-static-artifact-privacy/013DR-candidate16-static-artifact-privacy.json`;
- normalized record SHA-256:
  `eb8f6fbff9b4e97e8ba6b2be7ba4fa99a74fc7635bc891ae365d32ab97fe7926`;
- signed manifest SHA-256:
  `ae1906e68df755b1e0ce6a77d6ede8256f923e72fe11da57f1cae89a82c4ffe6`;
- Windows build manifest SHA-256:
  `74e8d512b0c0f403d1bbf90251b7799a0ca086d8d0df51f13860c2e7d3d16051`.

Temporary extraction stays outside Git and is removed after the tracked
record validates. Candidate bytes are never modified.

## Decision

`OBS-005`, `OBS-006`, `OBS-010`, `FRKN_AWG/AWG-01` and Gate F gain stronger
exact-candidate static evidence without index promotion. Gate F remains
`NO_GO 2/17/2`: live runtime, connected Windows, origins, provider, Operator,
legal, rollback, device performance and the aggregate no-open-P0/false-green/
secret-leak attestation remain non-PASS. Gate G, public assets, Store
submission and stable promotion remain unauthorized.
