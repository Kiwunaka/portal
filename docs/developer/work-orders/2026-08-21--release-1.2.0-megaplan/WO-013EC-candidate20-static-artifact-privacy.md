# WO-013EC — candidate.20 bounded static artifact privacy scan

Status: `PASS_BOUNDED_STATIC_ARTIFACT_PRIVACY_SCAN; ANDROID_RUNTIME_AND_FINAL_AGGREGATE_OPEN`

Observed: `2026-09-01`

Production/public mutation: `NONE`

## Outcome

Inspect the exact immutable candidate 20 distribution bytes without launching
an app, installer, VM, LDPlayer or phone and without changing host VPN, route
or DNS state. All six distribution files match the exact sizes and SHA-256
values in signed release index
`046d331274da76ba524f824debb17c4abc080657456c41099246589cc3c1770a`.

The five Android archives are streamed in place; no archive is extracted to
disk. Their `1895` entries and `976326012` uncompressed bytes return zero
complete private-key blocks, populated authorization values, credential
assignments, high-confidence connection URIs or provider-specific live-token
shapes.

The exact Windows installer returns the same zero-result raw-byte scan. Its
build manifest matches the signed installer and the preserved clean exact
client source `8ab9815...`: all `11/11` required files pass size and SHA-256
binding, and all `302` files / `99269281` bytes in the staged tree return zero
definite findings.

This replaces candidate 16 static privacy evidence for the current candidate.
It is bounded static evidence, not installed Android, connected Windows,
deployed encrypted ingest or the final live owner attestation.

## Broad-match triage

The first intentionally loose token-shape pass stops at `12` matches. All
twelve are one 39-byte fingerprint duplicated across Android ABIs: nine occur
inside Flutter runtime libraries and three inside the matching AAB Flutter
symbol entries. The sequence does not satisfy a strict provider-token format.
The same loose pattern matches zero text-source files across the exact
platform, client and Core trees.

The retained triage record stores only the value SHA-256, length, class and
counts. It stores neither the matched value nor raw archive paths. The strict
provider-shape replay returns zero matches, so the final classification is
`ABI_DUPLICATED_FLUTTER_RUNTIME_AND_SYMBOL_STRING_NOT_A_PROVIDER_TOKEN_FORMAT`.
The initial non-PASS discovery report remains retained and is not relabeled.

## Windows boundary

The installer is not independently unpacked. Windows evidence is limited to:

- exact installer size/SHA equality with the signed release index;
- exact installer SHA equality with build manifest
  `57687e95bd3368e43d71025c5d607a60456abfcaf869cf37c6bf84ff297afbd7`;
- direct raw-byte scanning of that installer;
- `11/11` size-and-SHA verification of manifest-required payloads;
- complete scanning of the preserved `302`-file staging tree under the clean
  exact client worktree.

Only the eleven required files are individually bound by the build manifest.
The remaining staging files are bound to the preserved exact-client build
directory, not individually to the signed release index. WO-013EA remains the
separate authority for installed Windows 11 default-path runtime.

## Ledger effect

`OBS-005`, `OBS-006`, `OBS-010`, `REL_DOD/DOD-12`,
`FRKN_AWG/AWG-01` and Gate F gain candidate 20 replacement evidence without
level promotion. Distribution remains `I4=7`, `I3=320`, `I2=19`, `I1=32`,
`I0=0` across `378` unique rows.

Gate F remains `I3/NOT_RUN`. Candidate 20 Android install/runtime, remaining
Windows coverage, authenticated origins, provider/Operator/legal, guarded
candidate rollback, comparable performance and the final live no-open-P0/
false-green/privacy attestation remain non-PASS. Gate G, public assets, Store
submission and stable promotion remain unauthorized.

## Commands and results

- strict six-artifact stream scan: `6/6` size/SHA bindings, `1895` Android
  archive entries, zero definite findings, `PASS_BOUNDED_STATIC_SCAN`;
- fingerprint-only loose-match triage: `12` occurrences, one fingerprint,
  zero strict provider-shape matches, `NO_HIGH_CONFIDENCE_TOKEN_MATCH`;
- exact-source text correspondence: platform/client/Core `0/0/0` matching
  source files;
- Windows staging scan: installer signed/build binding PASS, `11/11` required
  files, `302` staged files, zero definite findings,
  `PASS_BOUND_STAGING_STATIC_SCAN`.

## Evidence

- normalized record:
  `evidence/013EC-candidate20-static-artifact-privacy/013EC-candidate20-static-artifact-privacy.json`;
- normalized record SHA-256:
  `90e82917194a102afda35d041b32ffbd031a55dbd0aa5286e7a47ebcf1b794f7`;
- private initial broad discovery SHA-256:
  `64fcc12c6e342c1f1016e3bd91502553e80cb37b4c078cc7cb5b770c4fc00b3d`;
- private strict scan SHA-256:
  `e9d09c37e054be503130c7b006a145a4e093e3561373a575110c4a25fd1e5407`;
- private triage SHA-256:
  `adb6e5363e2540fb919ab79c9567a8c95bf093f6fe3d47462a736febcc763ca4`;
- private Windows staging report SHA-256:
  `2d710bb828a7d88e04b332e57c466dafcab1bb54b4dbce04ea3f2147d1b77ebe`;
- private report directory:
  `E:/POKROV-tools/temp/candidate20-offline-gates/`.

The normalized record contains no matched value, raw local path, credential,
customer/provider payload or connection material.
