# WO-013GV — candidate.33 bounded Windows and physical Android runtime

Status: `PASS_BOUNDED_EXACT_CANDIDATE_RUNTIME; GATE_F_BLOCKED`

Observed: `2026-09-04T10:19:07Z`–`2026-09-04T10:57:02Z`

Production/public mutation: `NONE`

## Outcome

Bind two new runtime slices to the unchanged private signed candidate.33:

- the exact installed Windows service and Core complete direct and Smart DNS
  synthetic TUN/DNS lifecycles inside the dedicated headless Windows 11 VM;
- the exact universal Android APK installs in place on a physical Huawei
  Android 12 device, preserves app data, passes ordinary Wi-Fi connection and
  DNS health, and supplies a bounded Beeline mobile slice.

These results remove the earlier `NOT_RUN` labels for the bounded Windows live
network and physical Android Gate F rows. Both become
`MANUAL_OWNER_TEST`, not `PASS`, because the exact release requirements are
wider than these slices. Gate F therefore remains `BLOCKED 2/17/0`.

No candidate byte, managed server profile, host route/DNS/tunnel, production
runtime, public asset, Store object or stable pointer changes.

## Windows VM result

The exact candidate.33 Auto/LocalSystem service stages, connects and
disconnects two secret-free synthetic profiles through the installed service
and Core:

| Slice | Exact result | Honest ceiling |
|---|---|---|
| Direct | TUN appears, route and DNS change, four DNS targets resolve, API health returns `200`, then TUN disappears and baseline route/DNS hashes return | Proves service/Core/TUN/DNS lifecycle; not managed-node or protocol egress |
| Smart DNS | Same lifecycle plus the configured POKROV DoH endpoint returns `200` with a DNS message | Proves synthetic Smart DNS contour; not authenticated application-session or leak/load proof |

The main Windows host is not used for input or network control. Managed
default-node egress, AWG3.1, AWG2, sleep/resume, connected forced recovery,
connected uninstall, Windows 10, SmartScreen UI and IPv6/leak coverage remain
open.

## Physical Android result

`pokrov-android-universal.apk` installs with `adb install -r`; version code
`4053`, installed base-APK SHA-256 and the production signing certificate all
match candidate.33. Uninstall and data clearing are not used.

On Wi-Fi, Android reports the POKROV VPN as connected and validated. DNS checks
for `example.com`, `chatgpt.com`, `gemini.google.com` and `xbox.com` pass, and
the bounded log-health inspection finds no fatal, ANR, uncaught, egress or
permission errors.

On Beeline:

- the selected Milan whitelist profile reaches a transient validated state
  and later fails closed;
- emergency white mode checks four reported channels and fails closed without
  claiming a confirmed route;
- automatic mode remains connected and validated for 32 seconds;
- a later externally initiated transport change to Wi-Fi ends mobile credit,
  and no result after that change is attributed to Beeline.

When owner foreground use is detected, device UI actions stop. Final retained
state is Wi-Fi enabled, POKROV disconnected and the owner's foreground app
preserved.

This is exact-candidate physical-device evidence, but not the complete Android
matrix. LDPlayer parity, AWG3.1/AWG2/HY2, direct DoH/Smart DNS UI, Doze,
Private DNS, IPv6/leaks, UDP53/MTU, multi-OEM, battery/thermal and endurance
remain open.

## Client truth merge

Client PR 76 merges the exact evidence and cutover truth at
`e23101f9cfa4bff055511e286118c941bf595712`. Local seed, docs-contract and
diff checks pass. The hosted `cross-repository-contract` job terminates with
zero steps and remains `BLOCKED_BY_ACCESS_GITHUB_BILLING`; it is not reported
as a contract failure or hosted PASS.

## Completion index and Gate F

No completion level changes. Distribution remains:

```text
I4=8 I3=319 I2=19 I1=32 I0=0 total=378
```

The refreshed Gate F result remains:

```text
BLOCKED
required=19
pass=2
non_pass=17
fail=0
validation_errors=0
gate_g_authorized=false
```

`windows_live_network` and `android_physical_device` move from `NOT_RUN` to
`MANUAL_OWNER_TEST`; the total remains non-PASS. No Gate G, deploy, tag,
public release, Store submission or stable promotion is authorized.

## Evidence digests

| File | SHA-256 |
|---|---|
| `013GV-candidate33-bounded-windows-android-runtime.json` | `2380ea7aaf8b0ef66ad12b028d1ff84d6077b015f6569220859e9cac28b3407b` |
| `013GV-candidate33-gate-f-evidence.json` | `205333e44be49bd9a2ccb8898b3abaaf08a9cae2b340951978221a58094f0d97` |
| `013GV-candidate33-gate-f-input.json` | `094618d1007e85e53d1967c492ddf41d4568249df175274cbd1f25ce73bfa267` |
| `013GV-candidate33-gate-f-decision.json` | `45260e8f21cf3ccfcd9f9fad93858384c78c9d6d526a1026d1d49b651f293e91` |
| external Windows direct result | `f0eaa96e81f950cd39aa485a01c1240ed1dce06cc40ba925d3f465b1c98105f6` |
| external Windows Smart DNS result | `ae7d0c3fc6038e2514bf97d143f71bad374bbbce81c2bdc8958369d6fa061d1a` |
| external Android summary | `e89799a184762ef73efbff782bff8c033876f854eb2ddad1833bdb369345824e` |
| external Android manifest | `364f29a286f78cbed2be3710d4f84b8abc19834e5741b7daf2fd2de72476928e` |

External evidence remains under:

- `E:/POKROV-tools/release-evidence/1.2.0-candidate33-windows-connected-2026-09-04/`;
- `E:/POKROV-tools/release-evidence/1.2.0-candidate33-android-physical-2026-09-04/`.

## Follow-up

Use the exact candidate.33 artifacts for managed default, AWG3.1 and AWG2 on
the isolated Windows VM and physical Android, then run the remaining
network-change/leak/lifecycle, named-origin, provider, Operator, legal,
comparable-performance, runtime-rollback and final-attestation rows before
recalculating Gate F again.
