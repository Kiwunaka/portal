# WO-013FJ — candidate.25 Windows CLI rebuild and hosted clean-host pass

Status: `PASS_EXACT_PRIVATE_CI_INSTALL_SERVICE_IPC_RESTART_UNINSTALL_IDLE_NETWORK`

Observed: `2026-09-03T05:00:52Z`–`2026-09-03T05:01:45Z`

Production/public mutation: `NONE`

## Outcome

Run a fresh headless Windows build rehearsal, then exercise the immutable exact
candidate.25 setup on an ephemeral hosted Windows machine. The exact candidate
passes machine-wide installation, all `11/11` installed-file identities,
LocalSystem service ownership, ordinary-UI authenticated IPC, SCM stop/restart,
clean uninstall and idle route/DNS/adapter restoration.

This closes the basic elevated clean-host installation and idle lifecycle gap
reported by WO-013FH. It does not prove a connected tunnel, connected DNS,
authenticated egress, connected uninstall, reboot/sleep/crash recovery or the
interactive SmartScreen experience. Gate F therefore remains `BLOCKED 5/14/0`.

## Exact candidate boundary

| Item | Identity |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.25`, app `1.2.0+4053` |
| Platform source | `883cd1038a087fbf9f570cffcbfdfd5f5197ffd4` |
| Client source | `54259b0f84e16c58e2d1f5f04b369af4fd0834b2` |
| Core source | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Release-index source | `18d9cb4c5541481c5e60713376904f962ec19a7c` |
| Signed manifest | `7161bae715d590fac0623561d147e4d9ee069da14a5e3645001cc4c39aa329b6` |
| Detached signature | `f83cf5acbfa8aa55a45a73f03a2f4e829661215a788f68e8b7b36764b1ff3d14` |
| Windows setup | size `29139238`, SHA-256 `ffc9b07c59f75372b48c5c1e94551d6d9af710ac0287cd1352142b0964707fb3` |
| Windows bundle manifest | `344b842cd0222aa642115c00f42810bf922492394435271d43d9837169f187c0`, `11/11 PASS` |

The setup is `NotSigned` under the owner's explicit direct-beta exception.
The SmartScreen warning remains a release limitation and is not relabeled as a
pass.

## Fresh headless CLI rehearsal

The full `scripts/build-windows-release.ps1` path is replayed without UI from a
disposable worktree at the exact client and Core revisions. Current platform
contract validation uses `c6007d1c35778171e730003edce11a386b465285`.
Release contracts, client widgets `413/413`, runtime engine `72/72` with one
declared optional skip, Windows widgets `23/23`, Windows release/Inno, both
Android Gradle flavors and Debug native CTest `8/8` pass. Release native CTest
passes all seven applicable tests when the Debug-only service integration test
is excluded.

The rehearsal setup is size `29142988`, SHA-256
`337fe374fa7015386ae187d11708c4a85e11ff0709dfcee1624457c18be30bcc`;
its `11/11` manifest is
`54fbc7473185677d9fd23821405e40c4ba3cc3dfce2e1428186894e17883120f`.
These are rehearsal bytes, not immutable candidate.25 bytes, and receive no
candidate credit. An unfiltered Release CTest scheduling the Debug-only pipe
integration test is retained as a non-gate test-harness configuration issue;
it is not represented as a product-runtime failure.

The disposable build worktree is removed after evidence extraction. The main
desktop, foreground UI, input devices, installed service and network state are
not touched.

## Private hosted execution

The private POKROV-app repository carries the exact setup only through private
prerelease tag `pokrov-1.2.0-candidate.25-private-ci`, targeted at reviewed
workflow commit `934924d1082ea4964ae21f835695e23dcb8245d8`. GitHub's asset digest and
an authenticated readback both match the signed candidate identity. This
carrier is not a public or stable product release.

Workflow `Windows Exact Candidate Clean Host`, run `33717151777`, succeeds on
ephemeral `win25-vs2026` image version `20260824.214.3`. The sanitized result
records:

- exact setup, signed-manifest and source-tuple identity: `PASS`;
- clean service/install/registry/adapter baseline: `PASS`;
- silent machine-wide install: `PASS`;
- installed runtime identity: `11/11 PASS`;
- exact automatic LocalSystem service and install-owner binding: `PASS`;
- ordinary UI to service authenticated IPC/status request: `PASS`;
- SCM stop/restart: `PASS`;
- clean uninstall of service, files and owner record: `PASS`;
- unchanged idle route/DNS fingerprints and no remaining adapter: `PASS`;
- bounded service data under ProgramData: `OBSERVED`, raw content not exported.

## Proof ceiling and release decision

Connected TUN/full traffic, connected DNS capture and leak checks,
authenticated profile egress, sleep/reboot/crash recovery, uninstall while
connected and interactive SmartScreen observation remain
`MANUAL_OWNER_TEST`. The hosted Windows Server result does not replace a
Windows 10/11 device matrix or packaged AWG3.1/AWG2/Smart-DNS tests.

Phase 03 remains `I3`. `REL_GATE/GATE-F` remains `I3` at exact
`BLOCKED 5 PASS / 14 non-PASS / 0 FAIL`; no Gate F regeneration is warranted
because its `windows_live_network` acceptance criterion requires the connected
matrix. Gate G remains unauthorized.

No production deploy, public release, stable pointer, Store object, current-
host runtime mutation or desktop input control occurs.

## Evidence and verification

- normalized record:
  `evidence/013FJ-candidate25-windows-hosted-clean-host-pass/013FJ-candidate25-windows-hosted-clean-host-pass.json`;
- normalized record SHA-256:
  `02fd478ad1dfb01384052aac3a150750c1ee5cf1ac59ac78d1c152e18cb5956f`;
- source hosted record SHA-256:
  `c6ec9d18366289d02fcf6e9c8fe168227a3a9a1a5a19457703120c6a9582bfcd`;
- source CLI rehearsal record SHA-256:
  `2fb85a04f3eb85a6b1f52c5edd19de33af8a1ac189125ecda3412e2308cc6266`;
- exact private asset authenticated readback: `PASS`;
- production/public mutation: `NONE`.
