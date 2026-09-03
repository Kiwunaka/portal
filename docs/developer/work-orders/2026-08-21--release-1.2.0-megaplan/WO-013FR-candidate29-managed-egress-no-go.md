# WO-013FR — candidate.29 managed egress and RU-Pi AWG NO_GO

Status: `EXACT_CANDIDATE29_WINDOWS_MANAGED_EGRESS_FAIL_RU_PI_AWG_NO_OUTER_RESPONSE`

Observed: `2026-09-03T11:35:00Z`–`2026-09-03T12:10:10Z`

Production/public mutation: `NONE`

## Outcome

Exercise exact installed candidate.29 through its real managed Windows path,
then separate client-specific behavior from the owned AWG server path with the
same exact Core revision on the direct-RU Raspberry Pi 4. Everything runs
headlessly. The owner workstation's mouse, keyboard, windows, tunnel, routes
and DNS remain untouched.

Fresh first launch succeeds in the isolated Windows 11 guest: the candidate
creates its ordinary five-day trial and renders Home. The installed automatic
`POKROVService`, authenticated IPC, service trust, compatibility and Core
readiness all pass. AWG3.1, AWG2 and the ordinary Reality fallback each resolve
and stage successfully, but each fails the authenticated egress probe and
rolls back cleanly. The final service state is ready, no tunnel is running and
no `tun0` remains.

The failure is not specific to the AWG parser or the Windows AWG selector. The
guest reaches both public health endpoints, and the same unauthenticated
network path receives the required HTTP `204` plus the exact public egress
marker. The failure appears only after the managed tunnel is staged, including
the ordinary fallback control.

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
from manual to `FAIL` and `authenticated_client_egress` from not-run to `FAIL`.
A regenerated snapshot would therefore contain three FAIL rows while keeping
the same two PASS and seventeen non-PASS rows. It is not regenerated while the
shared live path is known-bad.

Candidate.29 is not rejected for replacement because no candidate source or
artifact defect is isolated: all three Windows transports share the same
failure, and both Pi AWG variants independently receive no server response.
Repair or restore the live delivery contour first, then repeat the exact same
candidate. A replacement build is required only if that repair identifies a
source or packaged-byte change.

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
  `592bccbd7317e8735c22166793aaf4d36997cd60268f7ebc5887ddc4b579f0c3`.

External evidence is retained under
`E:/POKROV-tools/release-evidence/1.2.0-candidate29-windows-awg-smart-dns-2026-09-03/`:

| File | SHA-256 |
|---|---|
| `candidate29-windows-managed-egress-summary.json` | `3a0194e14fd11fec5bf1d97d84b2acee770b8c8a4f55ee7276e2599ab156772a` |
| `candidate29-pi4-awg31-core-interop.json` | `1e63db2045cf5ed084f6ead9cc83d0e0bb6c67cf2140d9e6d4f5ee0db2fe409d` |
| `candidate29-pi4-awg2-core-interop.json` | `7ade05416fd7a41792b0180ca90eb52cbbe39e27e34e9c362b64cfe76ace27f1` |
| `candidate29-fresh-awg31-bind-apply.json` | `9f4414cdfb0613bd0fc8286f213e61281d57ae6dccec90919ac7fb45969d1c76` |
| `candidate29-fresh-awg2-bind-apply.json` | `9c543c28a827139bf7aba42173e33bdaaa9076c2bb0fa016cd1927ac3831882b` |
| `candidate29-fresh-default-bind-control.json` | `76b0a8634176e73232ec1b50fd3e48b392b36293a9bfa000f908c4bd253657b0` |

The retained records contain no raw profile, credential, private key, token,
connection URI, customer identifier, device identifier or raw address.
