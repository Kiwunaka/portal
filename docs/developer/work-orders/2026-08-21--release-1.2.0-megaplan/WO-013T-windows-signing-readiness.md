# WO-013T — Trusted Windows signing readiness and exact custody blocker

Status: `READINESS_CONTROL_PROVED_TRUSTED_CERTIFICATE_BLOCKED`
Phase: `11`
Rows: `REL_DOD/DOD-15`
Candidate: `NOT_CREATED`
Production/publication: `NOT_AUTHORIZED_NOT_RUN`

## Outcome

Client `main` now contains a non-mutating readiness-only path for the exact
Windows Authenticode identity. It exercises the same certificate-store,
subject, Code Signing EKU, validity, online entire-chain trust and SignTool
resolution used by the full release builder, then stops before build, signing,
packaging or candidate creation.

Client PR 13 head `0f2fe25d9a913edfcb9b1b176470afce79e99586`
passed the complete hosted cross-repository/client/Android gate in run
`32675312337`, job `97282255100`, in `12m51s`. It merged under
`OWNER_SOLO_EXCEPTION` as client `main`
`1627fc88da0dece56fdb4be6fd281dac95268be9` with the exact same Git tree
`48a095d1d92955f3b803dd413bd522bb94ffa671`. Post-merge run
`32676034400`, job `97284205083`, repeats the complete hosted gate
successfully in `12m28s`.

The readiness path emits `pokrov.windows-signing-readiness-receipt.v1` only
after all local checks pass. The public receipt explicitly reports
`artifacts_signed=false`, `candidate_created=false` and
`production_runtime_mutated=false`. It accepts no PFX path or password and
does not expose a private-key value. A readiness receipt still does not prove
private-key usability, timestamp-service operation, signed bytes, clean-host
trust or candidate eligibility; those require the full exact build and later
candidate gates.

## Local certificate-store audit

Two Code Signing certificates are present in `CurrentUser/My`. Both report an
associated private key, Code Signing EKU and a current validity interval. They
are nevertheless unusable for a public trusted release because each is
self-signed and its online entire-chain result is `UntrustedRoot`:

| SHA-1 thumbprint | Certificate SHA-256 | Valid UTC | Result |
| --- | --- | --- | --- |
| `8C113EFF1B724EECA2FBC0D520B3E6A6CB1457FF` | `5C8EA6BC56C0023C08947926440BD4056AEA606D39B2975CC72027FAF5522753` | 2026-03-18T01:12:04Z – 2027-03-18T01:32:04Z | `SELF_SIGNED`, `UntrustedRoot` |
| `436C50259F8ABD22F74E46A8605B6E2A514D7280` | `C94AC85490C72181027B14C0665709047C4FA0463383D48BFBA7F375F22EEB7A` | 2026-03-18T01:11:32Z – 2027-03-18T01:31:32Z | `SELF_SIGNED`, `UntrustedRoot` |

Both have subject and issuer
`CN=8CB43675-F44B-4AA5-9372-E8727781BDC4`. `LocalMachine/My` contains zero
Code Signing certificates. No certificate or private key was removed, copied,
exported, printed or committed during the audit.

Running the readiness path against the first exact thumbprint returns the
expected fail-closed error:

`Self-signed certificates cannot satisfy trusted Windows signing.`

The Windows SDK x64 SignTool is installed at
`C:/Program Files (x86)/Windows Kits/10/bin/10.0.22621.0/x64/signtool.exe`.
Therefore tooling is ready; the blocking input is the trusted release
identity, not SignTool installation.

## Hosted and repository custody audit

The active client repository exposes only the release-platform deploy secret
name and the public support-signing variables. The platform repository exposes
only the separate Ed25519 support-mode signing secret name plus its public
identity variables. Neither repository has a Windows/Authenticode/PFX/
certificate-thumbprint secret or variable.

The inspected platform, client, Core and public-index trees contain no PFX,
P12, PVK, private `.key`, CER or CRT candidate-signing file. Seven PEM files
under vendored Core test/public-root data are unrelated to POKROV Authenticode
custody and were not treated as release inputs.

All five local signing environment inputs were unset during the audit:

- `POKROV_WINDOWS_SIGNING_CERTIFICATE_THUMBPRINT`;
- `POKROV_WINDOWS_SIGNING_EXPECTED_SUBJECT`;
- `POKROV_WINDOWS_SIGNING_TIMESTAMP_URL`;
- `POKROV_WINDOWS_SIGNING_STORE_LOCATION`;
- `POKROV_SIGNTOOL_PATH`.

This explains the earlier owner recollection precisely: a private key was
created and still exists, but it belongs to a self-signed development identity.
A private key alone is not a publicly trusted Authenticode identity.

## Exact next input and candidate boundary

Before a candidate build, the operator must provision a non-self-signed Code
Signing certificate with an associated private key and a chain trusted by the
target clean Windows environments. The exact subject, 40-hex store thumbprint,
store location and HTTPS RFC3161 timestamp URL must then be supplied to the
readiness-only command. Certificate purchase, organization/individual
validation, hardware-token or managed-signing enrollment is an external owner
action and was not performed or charged by this work order.

After the readiness receipt passes, the full builder must prove key usability
by signing and verifying the staged shell, service, installer and embedded
uninstaller with RFC3161 timestamps. The exact artifact set, checksums,
SBOM/provenance, strict handoff and candidate index must then be regenerated.

No candidate, signed Windows artifact, GitHub Release, stable pointer, store
publication, clean-host/device/origin proof, provider action, production
deploy or support-mode runtime mutation was performed.

## Ledger decision

No row advances. `REL_DOD/DOD-15` remains `I2`: the trusted-signing control
and exact blocker are stronger, but there is no positive trusted-certificate
receipt, signed Windows artifact, regenerated candidate set or manual/promotion
proof.

Distribution remains `I3=309`, `I2=17`, `I1=37`, `I0=14`; 68 rows remain
below `I3`, with stage split `0/33/14/21`.
