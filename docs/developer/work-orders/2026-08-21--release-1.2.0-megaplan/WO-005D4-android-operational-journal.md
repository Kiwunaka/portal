# WO-005D4 — Android private operational journal

Status: `COMPLETE_LOCAL_I3`
Classification: `ACTIVE_EXECUTION`
Phase: `03`
Lane: active Android client
Depends on: `WO-005D1..D3`, `WO-006A`, `WO-006I`
Production/external actions: `NOT_AUTHORIZED`

## Outcome

Close the five Android platform-producer gaps that were still captured at
`I0`: app-private release logging, VPN lifecycle/permissions, default-network
and power/standby state, safe ANR/watchdog breadcrumbs and direct-updater
identity outcomes. The result is a local source contract only. It does not
claim an exact APK, a physical-device event, Android ANR delivery, production
signing, upgrade lineage or candidate proof.

## Implemented boundary

- The client writes `android-operational-v1.jsonl` and one previous file under
  `noBackupFilesDir/observability`. Both files are owner-only and capped at
  256 KiB. A single writer has a 256-record queue; rejection/failure is carried
  as a numeric `dropped_before` value instead of blocking the runtime.
- The JSONL schema has only schema version, UTC timestamp, local sequence,
  closed event/outcome enums, optional positive runtime generation and dropped
  count. There is no field for message, URL, endpoint, interface, package,
  profile, token, exception or stack.
- `VpnService` emits create/start/session/TUN/stop/revoke/destroy/failure and
  VPN/notification permission outcomes. Default-network callbacks emit only
  available/capability-change/lost enums.
- Process diagnostics retain Doze, app-standby bucket and background restriction
  as closed state enums. A background checker observes a main-thread heartbeat;
  a stall emits one rate-limited breadcrumb without taking a stack dump.
- The direct flavor emits `verified` or `rejected` only after the existing APK
  package/version/versionCode/SDK/ABI/signer-lineage policy. Installer/store/
  permission handoff is a separate closed event. Store source still has no APK
  identity/download path.
- Telemetry initialization and writes fail open for application behavior. Raw
  Core messages remain discarded; this journal does not compete with the
  cross-repository support-envelope owner.

## Acceptance evidence

- Direct and store Android JVM suites: `172/172 PASS` each, zero failures,
  errors or skips.
- `:app:assembleDirectDebug` and `:app:assembleStoreDebug`: `BUILD SUCCESSFUL`.
  These ignored debug APKs are compilation evidence only.
- Client documentation contract: `PASS`.
- Client seed/cross-repository validation with explicit active platform/Core
  worktree roots: `PASS`; product target remains `1.2.0+30`, Core target
  `1.1.0 PRE_CANDIDATE_LOCAL`, desktop ABI 2, event ABI 1.
- `git diff --check`: `PASS`; only line-ending warnings.
- `git status --short -- artifacts/releases`: empty; retained release evidence
  was not changed.

The first seed command used its default neighboring `POKROV-core` checkout and
failed on that checkout's missing `abi_contract`. It is retained as a wrong-root
diagnostic, not a product failure. The required rerun named the active Core and
platform worktrees explicitly and passed.

Machine evidence:
`evidence/005D4-android-operational-journal/005D4-android-operational-journal.json`.

## Ledger effect

- `OBS/OBS-037`: `I0 -> I3`.
- `OBS/OBS-038`: `I0 -> I3`.
- `OBS/OBS-039`: `I0 -> I3`.
- `OBS/OBS-041`: `I0 -> I3`.
- `OBS/OBS-042`: `I0 -> I3`.

Distribution becomes `I3=273`, `I2=36`, `I1=47`, `I0=21`, total `377`;
`356` rows are at least `I1` and `104` remain below `I3`.

## Remaining exact-candidate gates

- Physical-device file mode, rotation, process death and long-run overhead.
- Real VPN grant/deny/revoke, Wi-Fi/LTE, Doze/standby and Android lifecycle.
- Controlled hang/ANR delivery and recovery without stack/private data.
- Exact production-signed direct upgrade, hostile APK rejection and installer
  permission cycle.

These stay below `I4` until retained against exact APK hashes and named devices.

## Rollback

Remove the five producer calls and the journal/runtime helper together, then
restore the preceding Android docs. Do not roll back to Logcat, free-form
exception logging, a public/external directory, unbounded files or stack dumps.
