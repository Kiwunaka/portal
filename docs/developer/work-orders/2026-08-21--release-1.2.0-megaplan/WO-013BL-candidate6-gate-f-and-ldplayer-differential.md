# WO-013BL — candidate.6 Gate F and LDPlayer differential

## Outcome

Run a new digest-bound Gate F for signed `pokrov-1.2.0-candidate.6` and retain
the exact post-signing LDPlayer AWG2/AWG3.1/control comparison without
transferring pre-candidate or candidate.5 runtime claims.

Gate F accepts the signed candidate identity and evidence grammar with zero
validation errors, then returns `BLOCKED`: `2/19 PASS`, `17/19 non-PASS` and
`0 FAIL`. The passing rows are supply-chain signature/SBOM/provenance and
release-doc/manifest binding. `promotion_authorized=false`; this is not Gate F
`GO` and does not authorize Gate G, public assets, stores or stable rollout.

## Exact candidate boundary

- candidate: `pokrov-1.2.0-candidate.6`;
- operational id:
  `62526fdbf0f86c2a7083eb9d2cff4f8645949a31c59032fa593dad9bc68cae05`;
- platform/client/Core source:
  `5713324c1c0c2566befadf527bc09ec0ecf84a4e` /
  `b2497af7704d0aa6901541e175ce154b0eab05d7` /
  `a45d69e40ed7d892619a2b5c4592a527f630665e`;
- release-index signing source:
  `8d09ae5e8ec0c8347bcd4e2659944bdf7c9c9db3`;
- manifest/signature/receipt SHA-256:
  `8aac2458f8c43c0ef2955719dcede44f495d60acf681bc804bd6bf9828ee9054` /
  `2307906a920fb9b4dcd4c0025bf7628972668905d13897c553ddf27a81592dfa` /
  `85dd34504d876086aa8bfe3533ad4db964e4f0a9106f9085657dc08c2c7afcaa`.

## LDPlayer differential

The exact candidate.6 x86_64 APK matches the signed artifact. Temporary,
exact-owned-device lab binding was applied separately for AWG2 and AWG3.1.
Each profile materialized the expected `awg` endpoint, started the app-owned
VPN and produced interface, route and managed-DNS proof. Both stopped at the
same egress boundary.

An ordinary default control, with no AWG configuration, reproduced that same
interface/routes/DNS-positive and egress-negative result. The bounded
classification is therefore `BLOCKED_BY_LDPLAYER_NETWORK_CURRENT_ORIGIN`, not
an AWG-specific protocol failure and not an authenticated tunnel PASS. Final
readback restored `default` / `legacy_reality_fallback`, removed AWG material
from the managed configuration and confirmed that both the app service and
TUN were stopped.

The physical ARM64 device still contains exact candidate.6 and reports
`1.2.0+4046`, but owner keyguard remained locked during this checkpoint.
Physical AWG2/AWG3.1, WARP, per-app, Private DNS/IPv6, OEM/Doze, leak,
lifecycle and cleanup proof therefore remain `MANUAL_OWNER_TEST`, not PASS.

## Gate F interpretation

- `REL_GATE/GATE-F` remains `I3` with
  `SIGNED_CANDIDATE6_GATE_F_BLOCKED_2_PASS_17_NONPASS`.
- `FRKN_PLAN/W9-05` remains `I1`: comparable exact-candidate Android/Windows,
  Smart-DNS access/attribution and required-origin metrics remain incomplete.
- The LDPlayer row is `BLOCKED_BY_ACCESS`; physical Android is
  `MANUAL_OWNER_TEST`; current, Brain, RU and authenticated-client origins,
  Windows live network, provider, Operator, legal/commercial, comparable
  performance and post-promotion health are non-PASS.
- Hosted required checks stay `SKIPPED_BY_OWNER` under the no-purchase
  `OWNER_SOLO_EXCEPTION`; the skip is not converted to PASS.
- No ledger row advances. The 378-row distribution remains `I4=4`, `I3=316`,
  `I2=21`, `I1=37`, `I0=0`.

Next: unlock and leave POKROV open on the physical phone, then execute the
candidate.6 Android matrix and restore the device. Run Windows parity only on
an isolated clean Windows 10/11 host. Close the remaining origin, provider,
Operator, legal and performance rows, then regenerate Gate F from new
digest-bound evidence. Smart DNS remains source-only until a safe owned
endpoint is deliberately freed with reviewed migration and rollback.

Machine evidence:
`evidence/013BL-candidate6-gate-f/013BL-candidate6-gate-f-evidence.json`,
`evidence/013BL-candidate6-gate-f/013BL-candidate6-gate-f-input.json`,
`evidence/013BL-candidate6-gate-f/013BL-candidate6-gate-f-decision.json` and
`evidence/013BL-candidate6-gate-f/013BL-candidate6-ldplayer-differential.json`.
Their SHA-256 values are respectively
`b62922ad447c4a617b1fced4e19498beb8134d6c941df70f8b413b2866883372`,
`f806571335712898801c84fbc7283b6a3d6331e108bdaf1c2dd8e369b7261e83`,
`d1de4f6a1e2a2624fbcd5f3858827f55781bb5e684775b2b5b67341987565698`
and `a7e6b2633a86f8ee4b77ebfcc2d1ad8e6bba45b5e42e76cc26a9c4c66f70ab47`.
The retained documents contain no device serial, address, hostname,
credential, private key, runtime material, customer data or raw provider
response.
