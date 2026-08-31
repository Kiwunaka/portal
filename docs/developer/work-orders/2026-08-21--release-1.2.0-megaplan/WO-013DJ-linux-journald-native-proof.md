# WO-013DJ — Linux native journald transport proof

Status: `PASS_I3_CURRENT_SUCCESSOR_SOURCE`

Observed: `2026-08-31T19:05:00Z`

## Scope

Close the source/runtime evidence gap for `OBS/OBS-043` without installing or
publishing the conditional Linux client. Prove that the existing closed
`pokrov-linux-operational-v1` envelope reaches a native journald Unix datagram
socket, that a missing native socket uses only the bounded JSON fallback, and
that one safe event can be read back from a real owned systemd journal.

This work does not implement Linux traffic, install the daemon, alter a
systemd unit, rotate the host journal, mutate network state or change signed
candidate.16.

## Exact boundary

| Item | Value |
|---|---|
| Signed candidate | `pokrov-1.2.0-candidate.16`, unchanged |
| Candidate client source | `75ba7e721cfee486f7189edd51de97aba2746722`, no Linux artifact |
| Successor client PR | `Kiwunaka/POKROV-app#47` |
| Successor head | `f191e70724e93ccb3167a06b5ea8c0a169644cde` |
| Client `main` merge | `6470d760a12c26e2c5f01354e83f20e89185711b` |
| Test binary | Linux/ARM64, SHA-256 `87607b7fa95d19cb431d2afba459c27010006c174429b1615f33f26e6339b394` |
| Owned test host | Raspberry Pi 4 Model B Rev 1.2, Debian 13, `aarch64`, systemd 257 |

The production writer still targets `/run/systemd/journal/socket` and keeps
the existing native-first, closed-fallback behavior. PR 47 only moves the
socket path behind a package-private helper and adds Linux-only tests plus an
explicitly opt-in owned-host probe.

## Native proof

On the owned Raspberry Pi, the exact cross-built test binary passes:

- one complete payload arrives as one Unix datagram;
- an absent native socket exercises the real transport error and produces the
  exact closed JSON fallback, with no additional field;
- the opt-in live probe writes one valid `request/pass` event to the actual
  journald socket;
- a sanitized `journalctl` readback returns only the expected schema, event,
  outcome, correlation ID, generation, identifier and `journal` transport.

The retained safe readback is timestamped
`2026-08-31T18:52:39.4490000Z`. The remote test binary and directory are
removed after execution. No service is installed or restarted.

## Verification

- Go `1.25.13` Windows-host journal package tests: `PASS`;
- full Linux daemon Go suite: `PASS`;
- Linux/ARM64 cross-vet and daemon build: `PASS`;
- owned Linux/ARM64 native socket, fallback and live readback: `PASS`;
- full client `scripts/run-tests.ps1`: `PASS`, including Android direct/store
  Gradle lanes;
- `artifacts/releases/**` delta: none;
- GitHub run `33428507999`, job `99607867109`: zero runner steps,
  `HOSTED_CHECK_BLOCKED_BY_BILLING`; PR 47 merged under the authorized
  `OWNER_SOLO_EXCEPTION`, not as a hosted PASS.

## Completion-index effect

`OBS/OBS-043` advances `I2 -> I3`. The current successor source now has native
socket delivery, real missing-socket fallback and live journald readback on an
owned Linux host. The row receives no candidate or release credit.

`OBS/OBS-045` remains `I2`: real NetworkManager/resolved/nft transactions,
partial-failure rollback and clean-host restoration remain absent.
`REL/LNX-001` and Gate C remain `I3`; Linux is still conditional and absent
from signed candidate.16.

The 378-row distribution becomes `I4=5`, `I3=318`, `I2=21`, `I1=34`,
`I0=0`.

## Evidence and ceiling

- normalized evidence:
  `evidence/013DJ-linux-journald-native-proof/013DJ-linux-journald-native-proof.json`;
- normalized evidence SHA-256:
  `e9b7cd1e2e87588b4a8505cb157d6a05a1c56e8ec5d37d861dd7d7b6ade93beb`;
- external safe evidence SHA-256:
  `465ed2f41b57b23307bdcf0f6427c73a6d737448d1954e0f16284dbf597814a3`.

The evidence ceiling is `I3` for current successor source. `I4` still requires
an exact signed Linux package on the declared clean Ubuntu 24.04 desktop row,
real socket activation and daemon lifecycle, retention/rotation behavior under
bounded pressure and reboot, plus package install/update/remove rollback.

## Next action

Keep Linux outside candidate.16. Continue with the real Linux Core/TUN and
NetworkManager/resolved/nft transaction/rollback lane before packaging; do not
force host-wide journal rotation merely to inflate this source proof.
