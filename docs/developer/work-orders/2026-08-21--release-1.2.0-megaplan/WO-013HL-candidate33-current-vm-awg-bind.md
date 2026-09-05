# WO-013HL — current VM AWG binding and default restore

Date: 2026-09-05. Status: `CONTROL_PLANE_APPLY_RESTORE_PASS; CLIENT_CONNECTION_NOT_RUN`.

The owner explicitly authorized temporary AWG3.1/AWG2 testing for the VM and
default-profile restoration. No other device scope, release publication or
backend code deployment was performed.

## Identity and correction

Installed candidate.33 UI/service hashes still match the signed candidate.
The current VM application install digest is `6c6320a2...cf46a250`, not the
older WO-013GZ target `fe746f13...581475d0`. Fresh read-only PLAN resolves one
current Windows device, version `1.2.0+4053`, active entitlement and available
material. No entitlement extension is needed or applied.

The first install-only APPLY selected AWG3.1 but returned `ok=false` because
the readback still required the account-wide allowlist removed by the prior
safety fix. Default restoration immediately succeeded. Executable tests of
the actual readback expression reproduced both errors (rejecting install-only
and accepting account-wide scope). The corrected expression requires exactly
one install and no account/platform selectors. Binder/selector tests: 23 PASS.

## Authorized live results

Using the corrected helper:

| Operation | Readback | Client tunnel proof |
| --- | --- | --- |
| AWG3.1 APPLY | `ok=true`, exact target, resolved `awg31_lab` | NOT_RUN |
| Default restore | `ok=true`, no target cohort/allowlist, `legacy_reality_fallback` | NOT_RUN |
| AWG2 APPLY | `ok=true`, exact target, resolved `awg2_lab` | NOT_RUN |
| Default restore | `ok=true`, no target cohort/allowlist, `legacy_reality_fallback` | NOT_RUN |

Sanitized full reports are retained under:

`E:/POKROV-tools/release-evidence/1.2.0-candidate33-windows-awg-authorized-2026-09-05/`

`evidence-index.json` binds 8 reports by SHA-256 and byte length;
index SHA-256: `36bb5df1451be20655029565bf409bcb36e5b14c64598fb867fa38ce1ac5b627`.

The first failed readback and its successful restoration are preserved beside
the corrected runs. Default cleanup removes rollout scope; it does not claim
deletion of encrypted lab endpoint material.

## Remaining client gate

An interactive limited-user launch renders the welcome screen. Local session
metadata has an account but no managed profile/revision. No AWG connection,
DNS/egress, leak, recovery or physical/RU-origin PASS is assigned. The initial
direct guest-control launch showed a blank window; interactive task launch
rendered the welcome screen and is the appropriate UI test context.

Complete the existing app access/onboarding flow, refresh the exact managed
profile after a new guarded selection, then run connection and cleanup tests.
Earlier GZ PLAN is historical, not current VM identity authority. Candidate
bytes, ledger levels and aggregate Gate F remain unchanged.
