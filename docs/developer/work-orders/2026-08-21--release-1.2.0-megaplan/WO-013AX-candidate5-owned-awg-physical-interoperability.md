# WO-013AX — Candidate.5 owned-AWG physical interoperability

## Outcome

Exact signed `pokrov-1.2.0-candidate.5` was exercised on the owned physical
Android device over Beeline with the production-managed, default-off `awg2_lab`
and `awg31_lab` profiles. Both profiles start an app-owned Android VPN and reach
their owned server endpoint, but neither completes an authenticated AWG
session. The server sees initiation/response-class outer traffic, no latest
handshake and no client inner traffic. The client consequently cannot prove
DNS or authenticated egress and stays fail-closed.

These are exact-candidate protocol `FAIL` results for the tested physical
slice, not an origin-access blocker and not a general verdict on upstream
AmneziaWG. Candidate.5 remains immutable, but it is not promotable because the
mandatory owned-AWG lane fails and a post-candidate client correction is also
required. Gate F stays `BLOCKED`; its frozen WO-013AV aggregate is not rewritten
as though these later tests had been part of that digest-bound decision.

## Exact basis

| Component | Exact identity |
|---|---|
| Candidate directory | `pokrov-1.2.0-candidate.5` |
| Platform source | `6ea08e9222dff67c93ffa0bb9585a57c5ffe220c` |
| Client source | `6b596cefbc043c2da30b31007789cea7e30fc336` |
| Core source | `e8eb7721fc6eaac6813d3a888ac90d0da1f541a1` |
| Universal APK | SHA-256 `2825a832a43404d7f16b42fbaf6f5e1f443505cca6a9ac8bf4e93e5ae46cbebb` |
| Core implementation | official pinned `amneziawg-go/v3 v3.1.20260814` on client and server; no POKROV cryptography fork |
| Origin/device slice | owned physical Android, Beeline mobile data; raw device/account identifiers are omitted |

The protected binder succeeded for both lab profiles and confirmed the exact
candidate install plus entitled-device ownership without returning raw
identifiers. After the runs it restored `default`, removed both lab
provisioning states and lab membership, resolved
`legacy_reality_fallback`, stopped the app VPN, and restored Wi-Fi. Cleanup is
retained separately and is `PASS` for this device slice.

## What the test proved

| Slice | Outer observation | Inner/handshake observation | Verdict |
|---|---|---|---|
| AWG2 | 40 s: 29 packets, 23 inbound, 5 outbound, 5 initiation-sized and 5 response-sized; 740 bytes received and 460 sent | latest handshake `-1`; zero client-to-server and server-to-client inner packets; DNS and egress unproved | `FAIL` |
| AWG2 later stats | 5 s: 6 packets, 4 inbound, 1 outbound, one initiation-sized and one response-sized; counters increased to 1628/1012 bytes | latest handshake still `-1`; no authenticated session | confirms persistent `FAIL` |
| AWG 3.1 | 40 s: 32 packets, 27 inbound, 4 outbound; randomized-trailer size classification intentionally not applied; 592 bytes received and 1083 sent | latest handshake `-1`; zero client-to-server and server-to-client inner packets; DNS and egress unproved | `FAIL` |

Android accepted and exposed the app-owned VPN transport in both cases. That
proves the request reached the platform VPN boundary, but it is not tunnel
success. The server counters prove bidirectional outer protocol activity; the
absence of a latest handshake and inner packets is the decisive failure.

## Separate client defect and retained correction

The first AWG2 attempt stopped before Core with `Выбранная локация недоступна`.
The server correctly returned the hidden owned-lab profile with
`smart_connect=null`, while candidate.5 still tried to validate a previously
saved manual Frankfurt node. Selecting `Автоматически` allowed the exact
candidate test to proceed without rebuilding it.

Client commit `bbf1de8` (`fix(client): ignore saved location for owned labs`)
retains the narrow correction: only owned `awg2_lab`, `awg31_lab` and `hy2_lab`
materialization ignores a stale saved manual node; the normal user preference
is not cleared. Its exact verification is:

- full `app_first_runtime_bootstrap_test.dart`: `86/86 PASS`;
- focused owned-lab stale-location regression: `PASS`;
- Flutter analyzer for both changed Dart files: `No issues found`;
- `git diff --check`: `PASS`.

Platform commit `f4927c6` (`fix(ops): resolve entitled AWG lab device owner`)
is the guarded binder correction used for the successful binds. It rejects
revoked devices, resolves exactly one entitled account owner, verifies that
owner owns the install and does not fall back to an unrelated runtime admin.
Its focused test result is `18 passed, 6 subtests`, with `py_compile` passing.

Neither correction changes candidate.5 bytes. Both belong to replacement
source and therefore require a new signed candidate before promotion.

## Evidence

The normalized, secret-free record is
`evidence/013AX-candidate5-owned-awg/013AX-candidate5-owned-awg.json`.
Its SHA-256 is
`bd251c8677d732c49acfa518bddf80983450a0876efec59bcc1ebf2a6ff150e9`.
Raw runtime files remain outside the public repository in the immutable
candidate evidence directory. The normalized record binds their SHA-256
digests and contains neither raw endpoint addresses, keys, device serials,
account identifiers nor connection material.

Notable retained UI facts are:

- initial stale-location failure XML SHA-256 `9f9e6464...`;
- AWG2 status-details XML SHA-256 `6e8b781a...`, showing DNS ready but egress
  unconfirmed and the tunnel requiring attention;
- AWG 3.1 result XML SHA-256 `0ef13c00...`;
- final default-state cleanup JSON SHA-256 `c3e20e87...`.

## Release decision and next action

- Keep candidate.5 and WO-013AV evidence immutable; label this later mandatory
  protocol slice `FAIL` and candidate.5 `REJECTED_FOR_REPLACEMENT`.
- Do not run Gate G, create public `v1.2.0`, switch stable, or publish the six
  candidate.5 assets.
- Add bounded, privacy-safe Core rejection diagnostics that distinguish
  unsupported/unknown message type, invalid MAC and invalid response without
  logging raw endpoints, keys or packets.
- Use those diagnostics to identify and fix the client/server interoperability
  defect while retaining the official upstream crypto implementation.
- Merge the narrow binder and stale-location corrections, build and sign a new
  candidate, then rerun AWG2 and AWG 3.1 on Android before Windows parity and a
  new digest-bound Gate F decision.
- Continue compatible Smart-DNS HTTP/access, attribution, leak and rollback
  proof independently; do not spend the release lane on SPB speculation.
