# WO-013HH — candidate.33 artifact-size baseline

Status: `BASELINE_RECORDED_EXACT_CANDIDATE33_ANDROID_WINDOWS_ARTIFACTS; REGRESSION_PASS_OPEN; GATE_F_BLOCKED`

Observed: `2026-09-04`

Production/public mutation: `NONE`

## Outcome

The exact candidate.33 signed universal APK and owner-accepted unsigned Windows
installer now have contract-valid artifact-size baselines. Their local bytes
match the SHA-256 and length in the signed private release index. The Android
artifact is `295370161` bytes; the Windows installer is `29153792` bytes. The
offline validator returns `BASELINE_RECORDED` for both observation-first
budgets. Neither result is a regression PASS until a later comparable
same-kind candidate is measured against it.

The first collection attempt exposed a real client collector defect:
`ArtifactSize` returned one numeric value, and PowerShell serialized it as a
JSON scalar despite the owned contract promising numeric arrays only. The
strict platform normalizer rejected that output. Client revision
`7855edf315a8d0768cb8f78b3f3bbdeab9dd40bf` forces array serialization and its
contract test now asserts the raw one-sample JSON shape. The accepted evidence
was recollected from that clean revision; candidate bytes were not rebuilt or
changed.

## Exact boundary

| Fact | Exact value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.33`, app `1.2.0+4053` |
| Platform / client / Core / index | `f530005...5bc1` / `6ab1bca...735e` / `cd8f0f4...884d` / `63993fb...c43c` |
| Universal APK | `295370161` bytes; SHA-256 `51b86f66...83f2`; `BASELINE_RECORDED` |
| Windows installer | `29153792` bytes; SHA-256 `250622f7...3580`; `BASELINE_RECORDED` |
| Signed index | SHA-256 `5620c2f0...f680`; both artifact hashes and lengths match |
| Contract | `pokrov.performance-budgets` `1.0.0`; SHA-256 `9edc0b96...fca2` |
| Collector fix | `7855edf...40bf`; raw one-sample JSON array contract PASS |

## Evidence

The external raw/normalized evidence index is:

```text
E:/POKROV-tools/release-evidence/1.2.0-candidate33-artifact-size-2026-09-04/candidate33-artifact-size-evidence-index.json
SHA-256 1784eaa9840c18ec4375f39f081815dd2a8829897cfc06ac2cebb812f6eed105
```

Client evidence is
`docs/operations/evidence/candidate33-artifact-size-baseline.json`, SHA-256
`7f53e1979fa597f5a77a63a06e8b2bd950649c965f566e3666d392bc2c0ed7f1`.
Client PR `87` merges the collector fix and evidence at
`f38f6dbba545fd7cd9bddc0109e8912c6c8f8842`. Hosted run `33901995731`
terminates with `steps=[]` and remains `BLOCKED_BY_ACCESS_GITHUB_BILLING`, not
a product-test failure or PASS.

The platform-retained summary is
`evidence/013HH-candidate33-artifact-size-baseline/013HH-candidate33-artifact-size-baseline.json`,
SHA-256 `6bc0f4f2fc8e0a705403c8b4ca740fb493422882c07ff3861870ec741e5636ff`.

## Release impact

`REL_DOD/DOD-13` gains exact candidate.33 coverage for both required
`candidate_artifact` budgets. This establishes the baseline point only. It
does not prove a later <=10% comparison, candidate-device cold start,
connect/reconnect/rollback, frames, Android idle/battery/thermal, comparable
Windows memory, authenticated cabinet performance or post-promotion health.
The row remains `I1` and Gate F remains `BLOCKED 2/17/0`.

No candidate bytes, deploy, public asset, Store object, stable pointer,
production account, control-plane state, host input or host network changed.
