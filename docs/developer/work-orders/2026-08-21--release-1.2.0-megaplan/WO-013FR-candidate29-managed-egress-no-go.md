# WO-013FR — candidate.29 managed egress and RU-Pi AWG NO_GO

Status: `CORRECTED_EXACT_CANDIDATE29_AWG_EGRESS_FAIL_ORDINARY_PROVISIONING_FAIL_RU_PI_AWG_NO_OUTER_RESPONSE`

Observed: `2026-09-03T11:35:00Z`–`2026-09-03T12:10:10Z`

Production/public mutation: `NONE`

Correction recorded: `2026-09-03T13:05:11Z`

## Outcome

Exercise exact installed candidate.29 through its real managed Windows path,
then separate client-specific behavior from the owned AWG server path with the
same exact Core revision on the direct-RU Raspberry Pi 4. Everything runs
headlessly. The owner workstation's mouse, keyboard, windows, tunnel, routes
and DNS remain untouched.

Fresh first launch succeeds in the isolated Windows 11 guest: the candidate
creates its ordinary five-day trial and renders Home. The installed automatic
`POKROVService`, authenticated IPC, service trust, compatibility and Core
readiness all pass. AWG3.1 and AWG2 each resolve and stage successfully, then
fail the authenticated egress probe and roll back cleanly. The later fresh
ordinary Reality control does **not** stage a Core configuration: it remains at
`pending_sync`, so the earlier statement that ordinary Reality reached the
same Core egress failure is withdrawn. The final service state is ready, no
tunnel is running and no `tun0` remains.

Read-only Brain evidence resolves the fresh trial to one active entitled
account. Its client exists on six panels and those panels authenticate
successfully; only `ru_spb` returns `ServerDisconnectedError`. The database
nevertheless has zero `UserNode` confirmations, zero active access-key rows and
zero provisioning jobs. Source inspection isolates the platform defect:
`ControlPanel.ensure_user_on_all_nodes` waits for the complete all-node result
before committing any successful mapping, while the managed-profile request
has a bounded aggregate timeout. The slow peer therefore cancels the aggregate
after six panel writes but before their local confirmations are retained.

This is a candidate platform-source defect and requires a successor candidate.
It does not prove an AWG-specific failure because the intended ordinary
transport differential never reached Core.

## Independent RU-Pi result

The guarded interop runner validates exact Core
`cd8f0f4169d570d693992a959d81d17c2c44884d`, exports only that tracked module,
cross-builds digest-bound Linux ARM64 binaries and runs them on the explicitly
confirmed owned Pi 4 with a direct default route. Both current owner labs fail:

| Profile | Result | Binary SHA-256 |
|---|---|---|
| `awg31_lab` | `failed_no_outer_response` | `b1ba0feca601935ea380f5def3ab32af41bc7a8a0dac77bc8cbf8b21535c61ab` |
| `awg2_lab` | `failed_no_outer_response` | `2e03aad39ebebee9dd190ca9df257b5e93f5ddc7720f4a16d4b31280bf4da38c` |

Both runs remove their temporary Pi state and report no runtime or server
mutation. The result is exact current evidence and supersedes the older
candidate.25 Pi PASS for present availability; it does not erase that history.

## Server diagnostic boundary

A bounded read-only alignment check cannot establish the DE SSH session before
timeout. The duplicate long wait is stopped instead of repeated. No permissive
host-key mode, trust-file change, service action or server mutation is used.
This is `BLOCKED_BY_ACCESS`, not a substitute explanation for the measured
no-response failures.

## Release effect

The immutable WO-013FQ Gate F snapshot remains `NO_GO 2 PASS / 17 non-PASS /
1 FAIL`. This later exact-candidate evidence changes `windows_live_network`
from manual to `FAIL` and `authenticated_client_egress` from not-run to `FAIL`
based on the two packaged AWG attempts. A regenerated snapshot would therefore
contain three FAIL rows while keeping the same two PASS and seventeen non-PASS
rows. The fresh ordinary first-run provisioning failure is an additional P0
release defect; it is not misreported as a third transport attempt.

Candidate.29 is rejected for replacement because the partial-success
confirmation defect is isolated in its platform source. The AWG no-response
and egress failures remain current evidence, but their server-path diagnosis is
separate from this first-run correction.

`FRKN_AWG/AWG-10` stays `I2`, `REL/WIN-003` stays `I4` for its already-proved
direct substrate, and Gates B/C stay `I3`; the new managed failure is retained
without downgrading historical proof. No completion level changes. Gate G,
public assets, Store submission and stable promotion remain unauthorized.

## Cleanup and evidence

The exact fresh Windows install is restored to `default`; cohort membership,
both lab allowlists and provisioned AWG material are absent. The automatic
service remains running, the app is disconnected, pairing temp count is zero
and the pre-fresh application data is retained for rollback. The temporary
combined SSH trust file is deleted.

Tracked evidence:

- `evidence/013FR-candidate29-managed-egress/013FR-candidate29-managed-egress.json`;
- SHA-256
  `d1a974f4fda2e20b6097b1842d8dbb29c11007d5719489b77829ecd6eaad9c21`.

External evidence is retained under
`E:/POKROV-tools/release-evidence/1.2.0-candidate29-windows-awg-smart-dns-2026-09-03/`:

| File | SHA-256 |
|---|---|
| `candidate29-windows-managed-egress-summary.json` | `e7b6b49c0d12b3d98aad0da20661a76d674779d0a2674b8f54ee80358ae6219a` |
| `candidate29-pi4-awg31-core-interop.json` | `1e63db2045cf5ed084f6ead9cc83d0e0bb6c67cf2140d9e6d4f5ee0db2fe409d` |
| `candidate29-pi4-awg2-core-interop.json` | `7ade05416fd7a41792b0180ca90eb52cbbe39e27e34e9c362b64cfe76ace27f1` |
| `candidate29-fresh-awg31-bind-apply.json` | `9f4414cdfb0613bd0fc8286f213e61281d57ae6dccec90919ac7fb45969d1c76` |
| `candidate29-fresh-awg2-bind-apply.json` | `9c543c28a827139bf7aba42173e33bdaaa9076c2bb0fa016cd1927ac3831882b` |
| `candidate29-fresh-default-bind-control.json` | `76b0a8634176e73232ec1b50fd3e48b392b36293a9bfa000f908c4bd253657b0` |
| `candidate29-fresh-trial-provisioning.json` | `ef02b1db7506def4407cc495856798095fd742b2f0773ba69b91fb29f5243a73` |
| `candidate29-fresh-trial-provisioning-latest.json` | `71c44d9135ba32d7606de1f5e442530756688b1a60c6247bbf27599915fdc8ea` |
| `candidate29-panel-sync-diagnostic.json` | `a228e2e700faa0cc955bab7ac4489d7877e2e9626a8fed353f578b17c349e8fd` |

The retained records contain no raw profile, credential, private key, token,
connection URI, customer identifier, device identifier or raw address.
