# WO-013EP — candidate.21 bounded static artifact privacy scan

Status: `PASS_BOUNDED_STATIC_ARTIFACT_PRIVACY_SCAN; ANDROID_RUNTIME_AND_FINAL_AGGREGATE_OPEN`

Observed: `2026-09-02`

Production/public mutation: `NONE`

## Outcome

Inspect the exact immutable candidate.21 distribution bytes without launching
an app, installer, VM, LDPlayer or phone and without changing host VPN, route
or DNS state. All six distribution files match the exact size and SHA-256
values in signed release-index manifest `ce0b8586...`.

The five Android archives are streamed in place; no archive is extracted to
disk. Their `1895` entries and `976326012` uncompressed bytes return zero
complete private-key blocks, populated authorization values, credential
assignments, high-confidence connection URIs or provider-specific live-token
shapes.

The exact Windows installer returns the same zero-result raw-byte scan. Its
build manifest `665f77f0...` matches the signed installer and the preserved
clean exact client source `1e16458...`: all `11/11` required files pass size
and SHA-256 binding, and all `302` files / `99269281` bytes in the staged tree
return zero definite findings.

This replaces candidate.20 static privacy evidence for the current candidate.
It is bounded static evidence, not installed Android, connected Windows,
deployed encrypted ingest or the final live owner attestation.

## Broad-match triage

The intentionally loose token-shape pass finds the same `12` occurrences and
single 39-byte fingerprint seen in predecessor evidence. Nine occur in native
libraries and three in another archive-entry class. The value itself is not
retained; only SHA-256 `12a50a79...`, length, class and counts are stored. The
strict provider-shape replay returns zero matches, so the classification stays
`ABI_DUPLICATED_FLUTTER_RUNTIME_AND_SYMBOL_STRING_NOT_A_PROVIDER_TOKEN_FORMAT`.

The prior candidate.20 scan programs are reused with only the expected
candidate ID and exact client SHA assertions substituted in memory. Their
scan logic and retained-value policy are unchanged; source-program hashes are
recorded in normalized evidence.

## Windows boundary

The installer is not independently unpacked. Windows evidence is limited to:

- exact installer size/SHA equality with the signed release index;
- exact installer SHA equality with build manifest `665f77f0...`;
- direct raw-byte scanning of that installer;
- `11/11` size-and-SHA verification of manifest-required payloads;
- complete scanning of the preserved `302`-file staging tree under the clean
  exact client worktree.

Only the eleven required files are individually bound by the build manifest.
The remaining staging files are tied to the preserved exact-client build
directory, not individually to the signed release index. WO-013EH remains the
separate authority for installed Windows 11 default-path runtime.

## Ledger effect

`OBS-005`, `OBS-006`, `OBS-010`, `REL_DOD/DOD-12`, `FRKN_AWG/AWG-01` and Gate
F gain candidate.21 replacement evidence without level promotion.
Distribution remains `I4=7`, `I3=320`, `I2=19`, `I1=32`, `I0=0` across `378`
unique rows.

Gate F remains `I3/NOT_RUN`. Candidate.21 Android install/runtime, remaining
Windows coverage, authenticated origins, provider/Operator/legal, guarded
runtime rollback, comparable performance and the final live no-open-P0/
false-green/privacy attestation remain non-PASS. Gate G, public assets, Store
submission and stable promotion remain unauthorized.

## Commands and results

- strict six-artifact stream scan: `6/6` size/SHA bindings, `1895` Android
  archive entries, zero definite findings, `PASS_BOUNDED_STATIC_SCAN`;
- fingerprint-only loose-match triage: `12` occurrences, one fingerprint,
  zero strict provider-shape matches, `NO_HIGH_CONFIDENCE_TOKEN_MATCH`;
- Windows staging scan: installer signed/build binding PASS, `11/11` required
  files, `302` staged files, zero definite findings,
  `PASS_BOUND_STAGING_STATIC_SCAN`.

## Evidence

- normalized record:
  `evidence/013EP-candidate21-static-artifact-privacy/013EP-candidate21-static-artifact-privacy.json`;
- normalized record SHA-256:
  `785d64a03d688a68dfa930f402a61072ba5aebc91d2c182a9b0ec82a6cb46255`;
- private strict scan SHA-256:
  `bb8939475b8dfa86c2e922b0a55e0beab44e23d9a206925f7132f2eea6911dc7`;
- private triage SHA-256:
  `a31d681e6bf3870e541cf4c7b3c47bf3ceb63d4f5a7ba5e75fba18a9ee844e43`;
- private Windows staging report SHA-256:
  `5a86773a6cea4b6f924887a45bae23ef2d9be5e1ea373b7384daf03e3580aec5`;
- private report directory:
  `E:/POKROV-tools/temp/candidate21-static-privacy/`.

The normalized record contains no matched value, raw local path, credential,
customer/provider payload or connection material.
