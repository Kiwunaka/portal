# WO-013HB — candidate.33 Windows product startup preference

Status: `PASS_EXACT_CANDIDATE33_PRODUCT_PREFERENCE_TOGGLE_ON_OFF_NO_PREMATURE_AUTOCONNECT; GATE_F_BLOCKED`

Observed: `2026-09-04`

Production/public mutation: `NONE`

## Outcome

The exact installed candidate.33 now passes the owning product-preference
boundary for Windows login startup. With the dedicated Windows 11 guest link
temporarily off, guest-only keyboard traversal opened Profile → Windows.
Enabling `Запускать вместе с Windows` created the exact quoted installed UI
plus `--startup` Run value; disabling the same switch removed it.

The same ordinary UI PID and Automatic LocalSystem service remained throughout.
No UAC, TUN, route or DNS mutation occurred. A temporary first-launch-completed
marker exposed the ordinary shell without reading or moving retained session
secret files. The marker, UI and temporary guest fixtures were removed, and the
bridged guest link plus exact network baseline were restored.

WO-013HA separately proves that this exact product-generated Run value starts
one hidden responsive process at a real guest login and that ordinary activation
exposes the same PID. This slice did not repeat the product-toggle → reboot
sequence. Saved account/profile migration, managed auto-connect and
delayed-network readiness therefore remain open.

## Exact boundary

| Fact | Exact value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.33`, app `1.2.0+4053` |
| Platform / client / Core / index | `f530005...5bc1` / `6ab1bca...735e` / `cd8f0f4...884d` / `63993fb...c43c` |
| Windows setup | `250622f7...3580`; installed `11/11` |
| Installed UI | `1b175a66...1d97`; PID `6212` |
| Startup value | `"C:\Program Files\POKROV\pokrov_windows.exe" --startup` |
| Toggle on | `2026-09-04T13:41:49.9598992Z`; exact Run value present |
| Toggle off | `2026-09-04T13:42:25.9388922Z`; Run value absent; same UI PID |
| Network | TUN `0`; DNS `43a34dfb...5f2d`; routes `081b333e...9865` before, during and after |
| Cleanup | marker/Run/UI/task/script absent; guest bridged link on; service Running/Auto/LocalSystem |

## Evidence

The external evidence index is:

```text
E:/POKROV-tools/release-evidence/1.2.0-candidate33-windows-startup-2026-09-04/candidate33-windows-product-preference-evidence-index.json
SHA-256 085419e4c733eb9659cd4745a8e7119ceb0eaea7d4da1991c4c63f6d1e6e21a2
```

The product-toggle-on screenshot SHA-256 is
`2cd0d2d16e9eb0ea8b017d5a3cddb15686e536bab8d1c9014ef73b6e67031ce7`.
Windows UI Automation exposed no named Flutter controls, so those no-mutation
probes receive harness credit only. The successful path used guest-only keyboard
focus traversal. One offline rehearsal entered the whitelist information screen
and performed no server or network action.

Client PR `81` merges the current readiness reconciliation at
`de3411eff774facfdc6b268e32871b58dcff9709`. Its local client docs contract and
full seed validation pass. Hosted run `33880074351` terminates with `steps=[]`
and remains `BLOCKED_BY_ACCESS_GITHUB_BILLING`, not a product-test failure or
PASS.

The platform-retained summary is
`evidence/013HB-candidate33-windows-product-preference/013HB-candidate33-windows-product-preference.json`,
SHA-256 `00c2701e9cc6d72214e6c1b84554cc334a7986bfa635a8fcfee059717b2bb203`.

## Release impact

`REL/WIN-005` now has exact-candidate product-preference and real-login startup
evidence but remains `I3`: sanitized saved account/profile state, managed
auto-connect and delayed-network/service-readiness timing are unproved. Gates C
and F remain blocked; Gate F stays `2/17/0`. No candidate bytes, deploy, public
asset, Store object, stable pointer, production account, server or host network
changed.
