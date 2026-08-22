# WO-006L — Windows sanitized-service native proof

Status: `COMPLETE_LOCAL_I3`
Phase: `04`
Row advanced: `OBS_DOD/DOD-08`
Promotion: `NOT_REQUESTED`

## Outcome

Close the shipped-platform part of the observability daemon boundary with a
current native Windows build, without pulling the conditional Linux beta into
the `1.2.0` release. Windows remains the only shipped desktop privileged host;
Linux remains `NOT_SHIPPED_IN_1.2.0` under the client architecture owner.

## Implemented boundary

- The Windows service journal accepts closed service/Core event fields only.
  Each line is at most 512 bytes, the asynchronous queue is capped at 4096
  events, and current/previous files are capped at 256 KiB each.
- The journal regression rejects unknown wire versions, changed field counts,
  profile material, session tokens, operation nonces and endpoint material; it
  also forces rotation and verifies both retained files stay within bounds.
- The root Windows CMake contract now passes `/wd4100` to MSVC. The prior
  `/wd"4100"` spelling was escaped by Ninja and made every native target fail
  with `D8021` before compilation.
- The current source was configured with Visual Studio 2022 Build Tools,
  MSVC `19.42.34435`, Windows SDK `10.0.22621.0`, CMake and Ninja. The service,
  its six tests and the runner activation test compiled as Debug targets.
- No Linux daemon or compatibility logger was added. If Linux becomes a
  supported release surface later, its journald/sanitized-slice contract needs
  a separate bounded implementation and evidence set.

## Index decision

`OBS_DOD/DOD-08` advances `I1 -> I3`. The active Windows privileged host has
current native build/test proof for the bounded sanitized slice, while the
only second platform named by the row is explicitly outside the `1.2.0`
shipped matrix. This is local source proof, not installed-service or candidate
proof.

Distribution becomes `I3=296`, `I2=24`, `I1=40`, `I0=17`; `81` rows remain
below `I3`. Stage split becomes `11/32/17/21`.

## Local proof

- MSVC/CMake/Ninja Debug configure and targeted native build: PASS.
- Service native CTests: `6/6` PASS.
- Complete native CTest set including activation protocol: `7/7` PASS.
- CMake immediate no-op rebuild after success: PASS (`ninja: no work to do`).
- Source hashes and transient local binary identities are retained in machine
  evidence. The binaries are development outputs, not release artifacts.

Machine evidence:
`evidence/006L-windows-sanitized-service-native-proof/006L-windows-sanitized-service-native-proof.json`.

## Evidence ceiling

The build used a dirty development worktree. No service was installed, no SCM,
route, DNS or TUN mutation occurred, and no clean host, exact Core DLL, signed
installer, exact candidate, crash/reboot drill, deployed readback, publication
or promotion was created. Two temporary build directories remain outside all
repositories because automated recursive cleanup was denied by the sandbox.
