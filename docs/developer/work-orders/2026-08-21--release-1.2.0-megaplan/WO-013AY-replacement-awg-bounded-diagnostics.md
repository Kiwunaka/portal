# WO-013AY — Replacement AWG bounded diagnostics and LDPlayer isolation

## Outcome

Candidate.5 remains immutable and `REJECTED_FOR_REPLACEMENT`. Replacement
source now carries a bounded production-safe AWG diagnostic bridge from the
official upstream Core into the existing Android runtime snapshot and the
dedicated POKROV diagnostics screen. A production-signed diagnostic
pre-candidate was installed on the owned LDPlayer and exercised against both
default-off owned lab profiles.

AWG2 and AWG 3.1 each created an Android VPN transport, remained in the client
`Проверяем…` state and produced the exact bounded diagnostic
`AWG · handshake_retry · #4`. Literal-IP ICMP remained reachable, but the
separate DNS-name and HTTPS egress checks failed for both profiles. The result
narrows the replacement defect to an unaccepted handshake before the bounded
retry limit. It does not yet identify which client/server parameter is wrong,
and it is not physical-device, Beeline, RU-origin or new-candidate proof.

## Exact source and artifacts

| Component | Exact identity |
|---|---|
| Platform operator path | `b0affe4` (`fix(ops): bind exact owned AWG test installs`) |
| Client diagnostic source | `7a633a83ca6605df9d06b8bf17a7c36240824bbb` |
| Core diagnostic source | `b057ff3f68b8fd8ddb057f3ef6e4bcd4fde54390` |
| Core Android AAR | SHA-256 `80fd68ee55defdf60d5e40b807c9dc962319d6ce11079a88b7aef47b223cb514` |
| ARM64 diagnostic APK | SHA-256 `8939570a182d4916dfc2ecade27cdd8503c62dc6ef8fcac3d5c533a1d094eab2` |
| x86_64 diagnostic APK | SHA-256 `7279c6bc00b17fe5fc2f1edbacc87ce635649bab615fc84e3aef5b4df7749b6a` |
| Android certificate | SHA-256 `0A0602A7DF5D96A0B427909D004F3DDF26DEF86587634BF16694DA8D654B2500` |
| App version | `1.2.0+4046`; diagnostic pre-candidate, not candidate.5 and not release |

The replacement Android AAR was built from exact Core source. The diagnostic
APKs use the existing production certificate continuity, but production
signing alone does not turn these bytes into a release candidate. The tracked
client AAR and release seed were restored after the isolated build; client and
Core worktrees were clean at handoff.

## Diagnostic safety contract

Core still uses official pinned AmneziaWG cryptography. No POKROV fork of
handshake or cipher code was added. Production forwarding reconstructs only a
closed `awg_safe_diag code=<allowlisted> occurrence=1..4` record; it never
forwards upstream format strings, arguments, endpoints, keys or packet bytes.
The accepted categories are:

- receive unknown type, invalid MAC1, invalid/decode/accepted response;
- send initiation, retry and give-up;
- bounded receive/send/upstream error categories.

Android rejects every callback string outside that canonical grammar, holds
only code plus occurrence in the in-memory runtime snapshot, clears it on the
next attempt, writes nothing to Logcat and exposes it only on the dedicated
diagnostics surface. The diagnostic does not change the protection state or
turn missing DNS/egress proof green.

## Exact LDPlayer run

The x86_64 APK upgraded the existing owned install and preserved its app-first
identity. The protected binder confirmed the exact local install digest and
matching device/account owner. Because that owned test user was inactive, the
new operator guard allowed exactly one explicit test day. It did not transfer
the runtime administrator's entitlement. The guarded readback proved the
extension and selected profile before either client run.

| Slice | Android/runtime observation | Network observation | Verdict |
|---|---|---|---|
| `awg2_lab` | VPN transport connected; POKROV stayed `Проверяем…`; diagnostics showed `handshake_retry #4` | literal-IP ICMP PASS; DNS-name reachability FAIL; HTTPS egress FAIL | `FAIL_AWG_HANDSHAKE_RETRY_DNS_AND_HTTPS_EGRESS` |
| `awg31_lab` | VPN transport connected; POKROV stayed `Проверяем…`; diagnostics showed `handshake_retry #4` | literal-IP ICMP PASS; DNS-name reachability FAIL; HTTPS egress FAIL | `FAIL_AWG_HANDSHAKE_RETRY_DNS_AND_HTTPS_EGRESS` |

The diagnostics screen also labeled the Android tunnel and route boundary as
confirmed, DNS as locally confirmed and authenticated egress as requiring
attention. That UI DNS label is not promoted over the independent failed
DNS-name smoke. The safe result is therefore failure, not partial tunnel PASS.

After both runs the app was force-stopped, Android exposed no connected VPN,
the binder restored `default`, readback resolved `legacy_reality_fallback` and
the LDPlayer lab allowlist membership was absent. The one-day owned test
entitlement remains time-bounded. The physical phone was absent from ADB, so no
new physical/mobile-origin test was manufactured from emulator evidence.

## Verification

- Core `scripts/test.ps1`: `PASS`, including brand, ABI, observability,
  AWG2/AWG3.1/HY2 contracts and Go suites.
- Client `scripts/run-tests.ps1`: `PASS`, including Flutter packages, Android
  direct/store unit flavors, Windows shell and the release-source logging gate.
- Platform operator/docs slice: `48 passed, 6 subtests`; link check,
  `py_compile` and `git diff --check` pass.
- Normalized secret-free evidence:
  `evidence/013AY-replacement-awg-diagnostics/013AY-replacement-awg-diagnostics.json`,
  SHA-256 `ef2dce80c330f699effee11cc0dc99b3dcd98620a6e9000a6611ffca6b4e56c2`.

## Release interpretation and next action

- Candidate.5 bytes and WO-013AV's digest-bound Gate F result are unchanged.
- No release row advances; the emulator run strengthens failure diagnosis but
  cannot satisfy physical Android, Beeline or RU-origin gates.
- Compare exact client/server AWG2 and AWG 3.1 parameter material and upstream
  version/feature parity without logging secrets or replacing official
  cryptography.
- Retest the corrected replacement bytes first on LDPlayer, then on the owned
  physical Android mobile-origin slice. Only then build a new signed candidate.
- Continue HY2 and compatible Smart-DNS as separate default-off lanes; neither
  is promoted by this evidence.
