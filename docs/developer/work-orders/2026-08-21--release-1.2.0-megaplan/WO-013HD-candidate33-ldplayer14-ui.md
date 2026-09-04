# WO-013HD — candidate.33 LDPlayer 14 install and cold UI start

Status: `PASS_EXACT_CANDIDATE33_LDPLAYER14_INSTALL_IDENTITY_COLD_UI_START_ONLY; NETWORK_BLOCKED_BY_HOST_TUN; GATE_F_BLOCKED`

Observed: `2026-09-04`

Production/public mutation: `NONE`

## Outcome

The exact production-signed candidate.33 universal APK now passes a bounded
LDPlayer 14 in-place update and cold UI-start slice. The dedicated Android 14
QA instance updates from build `4030` to `1.2.0+4053` without uninstall or
clear-data. Installed `base.apk` is byte-identical to the immutable candidate
artifact.

The exact `MainActivity` cold-starts successfully and remains the top resumed
activity on one stable PID for `321` seconds while the LDPlayer host window is
minimized and responsive. The crash buffer stays empty. No POKROV VPN service
or emulator `tun0` appears.

The main Windows host simultaneously has Hiddify and sing-tun `tun0` active.
No DNS, egress, VPN, AWG, Smart-DNS, WARP, routing or protocol observation from
this emulator receives release credit. The slice proves only exact install
identity, launch and bounded process/crash behavior.

## Exact boundary

| Fact | Exact value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.33`, app `1.2.0+4053` |
| Platform / client / Core / index | `f530005...5bc1` / `6ab1bca...735e` / `cd8f0f4...884d` / `63993fb...c43c` |
| Universal APK | `51b86f66...583f2`; `295370161` bytes; production certificate `0a0602a7...2500` |
| Emulator | LDPlayer 14, Android 14, `pokrov-qa-120`, primary ABI `x86_64`, `1080x1920@480dpi` |
| Update | build `4030` → `4053`; data preserved; installed bytes match candidate |
| Cold start | `Status: ok`; `MainActivity`; total/wait `665/670 ms` |
| Stability | same PID for `321` seconds; top resumed activity exact; crash lines `0` |
| Idle runtime | POKROV service records `0`; emulator `tun0` absent |
| UI privacy | sanitized `23/23` POKROV-package nodes; raw tree/screenshot not retained |
| Host boundary | no host input or network change; Hiddify/sing-tun active |
| Cleanup | QA instance stopped gracefully; installed candidate and app data retained |

## Evidence

The external evidence index is:

```text
E:/POKROV-tools/release-evidence/1.2.0-candidate33-ldplayer14-ui-2026-09-04/candidate33-ldplayer14-ui-evidence-index.json
SHA-256 74703a9d17707cccec94f9ad5f134fed02f29ac9e14c23d9953164d6d3dfd850
```

The client-normalized evidence is
`docs/operations/evidence/candidate33-ldplayer14-ui.json`, SHA-256
`6114f575cb9dfe49f7e57bc642f39448dd735d01b950b264d67b531e3765e4c7`.
Client PR `83` merges that reconciliation at
`0113b4dd8b4325ce6b45fb0f4f18e5405b8cc8e8`. Hosted run `33891913025`
terminates with `steps=[]` and remains
`BLOCKED_BY_ACCESS_GITHUB_BILLING`, not a product-test failure or PASS.

An earlier hidden-window harness run was externally terminated by LDPlayer.
The engine records a requested guest power-off and `VERR_INTERRUPTED`; no
product crash or Windows error event is observed. The primary minimized run
passes and owns the release credit above.

The platform-retained summary is
`evidence/013HD-candidate33-ldplayer14-ui/013HD-candidate33-ldplayer14-ui.json`,
SHA-256 `89b5daaad00e4472b15ad2ceab128281e082067a8c30aa846e4c06948d4fee02`.

## Release impact

Gate B/C, Android artifact identity and performance-baseline rows gain stronger
exact-candidate evidence without level change. The one-frame gfx and memory
samples are descriptive only and do not create a performance-budget PASS.
LDPlayer network/full-UI, managed AWG/Smart-DNS/WARP, physical-device lifecycle
and isolated-origin matrices remain open. Gate F stays `BLOCKED 2/17/0`.

No candidate bytes, deploy, public asset, Store object, stable pointer,
production account, control-plane state, host input or host network changed.
