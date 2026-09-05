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

## Follow-up: actual UI attempt

The welcome screen was not an authentication blocker. Exact candidate source
maps `Начать бесплатно` to local completion plus existing-session telemetry
and account refresh. Completing it rendered the home screen. A fresh guarded
AWG3.1 APPLY succeeded, then the app's Connect button reached the first-connect
route-scope sheet (`Всё устройство` / `Выбранные приложения`). No mode was
selected: Windows computer-use restrictions require owner handling of this
VPN scope setting. No tunnel/DNS/egress PASS follows from reaching this sheet.

`awg31-ui-test-apply.json` and `default-after-ui-route-prompt.json` retain this
additional selection/restoration, separately from the original eight-report
index. Final readback again has `ok=true`, `legacy_reality_fallback`, no target
cohort and no lab allowlist identity. Local onboarding completion is retained;
the UI is left at the scope sheet. App session storage remains protected and
no managed profile file was observed. The next manual step is scope selection,
not login. Re-select the lab with the guarded helper before resuming AWG proof.

A status CLI launched from Downloads returned `server_untrusted`: its exact
source binds the service path relative to its own executable directory, so
this is not evidence of an installed-app service failure. Placing that helper
beside the installed app was denied under the limited guest-control token;
no trust checks or file permissions were weakened. This invocation receives
no runtime credit.

GitHub PR 238 guardrail/contract annotations explicitly report that jobs did
not start because of account billing/spending restrictions. Hosted checks
remain `BLOCKED_BY_ACCESS`, not a code-test PASS. The owner-solo exception
applies to source promotion; it does not waive exact-candidate runtime gates.
