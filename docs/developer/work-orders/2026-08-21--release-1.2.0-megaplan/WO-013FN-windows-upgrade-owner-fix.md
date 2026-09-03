# WO-013FN — candidate.27 upgrade-owner NO_GO and candidate.28 correction

Status: `PASS_PRE_CANDIDATE_WINDOWS_UPGRADE_OWNER_FIX_AND_DIRECT_RUNTIME`

Observed: `2026-09-03T07:44:49Z`–`2026-09-03T08:40:23Z`

Production/public mutation: `NONE`

## Outcome

Run a new Windows release build entirely through CLI, exercise its exact setup
inside the isolated Windows 11 VM and close any reproduced packaging defect
without taking control of the owner's desktop.

The candidate.27 precursor passes source, unit, native and package assembly but
is `NO_GO`: a direct first in-place upgrade from the retained candidate.23 VM
aborts before file replacement because `PrepareToInstall` cannot resolve the
interactive installation owner. The earlier second-attempt install remains
diagnostic evidence and receives no release credit.

The successor correction preserves the clean-install fail-closed boundary. For
an existing machine installation only, it reuses the protected
`InstallOwnerSid` when the original-user query fails and only after the stored
SID passes exact validation. Client PR 72 merges this correction to `main`.
The resulting candidate.28 precursor passes the same first upgrade on the
first attempt, all `11/11` installed-file identities, the direct-only TUN/DNS
lifecycle and connected guest-reboot recovery. It is not a created, signed or
promotable multi-platform candidate.

## Exact boundary

| Item | Identity |
|---|---|
| Candidate.27 source | client `ed74928a88ead8053a845f9d8e294d1298b83a6a`; Core `cd8f0f4169d570d693992a959d81d17c2c44884d`; platform validation `4d6cd0024ef3a4b58a08adf94e59e8850c3f151a` |
| Candidate.27 setup | `0d8c89aee4eb4280221165224dd792ad6dc0e922b9881b411f52d26635821213`, `29148103` bytes; manifest `812e987ac39e92d60d370746f27b4858594107965defca3548254b0d77f2efcb`, `11/11` |
| Corrected source | base client `ed74928…83a6` plus diff `1341da36…2888`; merged `POKROV-app/main` `7e3e771fe36333a75244cbfd828c60beb84c7ff1` |
| Candidate.28 setup | `7986a2b31e14b11d3765e4d988a6b4f897c05752acfc381f07ab1dd360e88182`, `29141384` bytes |
| Candidate.28 manifest | `1ff59b17f72fa63ece302872eb730bdb173d93604a34480a5ae13121f625cfef`, `11/11` |
| Windows signing | `SKIPPED_BY_OWNER`; direct-beta SmartScreen/unknown-publisher warning remains mandatory |
| VM ancestor | `candidate23-retained-before-candidate25-20260903` |
| GitHub | client PR 72 merged; run `33734564011` executes zero steps and is `BLOCKED_BY_ACCESS`, not PASS |

The candidate.28 bytes were built from the uncommitted two-file source diff
later merged without content changes. The merge commit therefore identifies
the canonical source state; the retained diff binds the exact pre-commit build
input.

## Candidate.27 rejection

Candidate.27's complete CLI build, Debug `8/8`, Release `7/7`, `11/11` staged
manifest and bounded static scan pass. Its exact setup is then launched
directly through the VM's UAC path from the restored candidate.23 state.

The installer closes normally but records
`PrepareToInstall failed: Не удалось определить владельца установки POKROV.`
before replacement. Installed presence is `11/11`, but only `10/11` sizes and
`8/11` hashes match; the three stale paths are `pokrov_windows.exe`,
`pokrov_service.exe` and `data/app.so`. This reproduces independently of the
earlier PowerShell launcher. Candidate.27 is therefore `NO_GO_PRECURSOR`.

## Correction and full CLI verification

The correction attempts the original-user query first. It falls back only when
that query cannot return a valid SID, only when the protected existing machine
registry value exists, and only when parsing returns that complete stored
value unchanged. A fresh install with no valid existing owner still aborts.

The corrected worktree passes:

- full release/repository/shared-facts/observability/logging/handoff contracts;
- app-shell `413/413`;
- runtime engine `72/72` with one declared optional real-Core skip;
- Android shell Flutter `8/8`, Linux shell `5/5` and Windows widget `23/23`;
- Android Gradle direct/store unit configurations;
- Windows analyze;
- native Release CTest `7/7` and Debug CTest `8/8`;
- Windows packaging with `11/11` manifest binding;
- bounded static scan of `303` staged files / `99269838` bytes and the raw
  setup with zero definite findings.

## Isolated Windows 11 result

The candidate.23 snapshot is restored again before the corrected run. The
candidate.28 setup is launched directly inside the guest, UAC is approved only
inside that VM, and the first attempt records
`POKROV_INSTALL_OWNER_REUSED_FOR_UPGRADE` followed by successful installation.
All `11/11` installed files match; `POKROVService` is `Running`, `Automatic`
and `LocalSystem`.

The exact installed precursor then passes the secret-free direct-only profile:
authenticated pipe/Core initialization, TUN `0 -> 1`, route/DNS change, API
health `200`, disconnect, tunnel removal and exact same-boot route/DNS restore.
A connected guest reboot leaves the service running and clean/lazy, removes
the tunnel and keeps DNS/API healthy.

Windows re-enumerates ordinary routes and DNS during this reboot, so their
whole-system hashes differ from the pre-boot hashes. The raw strict failure is
retained. A fresh post-boot connect/disconnect returns both fingerprints
exactly to the new boot baseline, proving that the difference is Windows boot
state rather than POKROV residue.

## Release effect and cleanup

The correction is merged and local `POKROV-app/main` is fast-forwarded to the
same commit. Candidate.25 remains the latest exact private signed candidate,
but it is not promotable: a new exact successor candidate must package the
merged correction and repeat its own required gates. Candidate.28 is only a
Windows precursor. Gate F remains the candidate.25 authority at exact
`BLOCKED 5 PASS / 14 non-PASS / 0 FAIL` and receives no new PASS row.

No public tag, public asset, Store object, stable pointer, production service
or host network state changes. The VM is powered off after the test. Host
mouse, keyboard, foreground UI, service and network are never used.

## Evidence

- `evidence/013FN-windows-upgrade-owner-fix/013FN-candidate27-no-go.json`,
  SHA-256 `24932b8fe41467d2f034f1fb47c9f54b6862ce6eeef8a5085b9522637f59ea88`;
- `evidence/013FN-windows-upgrade-owner-fix/013FN-candidate28-pre-candidate.json`,
  SHA-256 `c2dfb30dc3915df5dbafd91c3962757294a6380e96f607e2a5ab83ccfdca68fb`;
- external setup, manifest, full CLI logs, JUnit, installer logs and sanitized
  VM evidence:
  `E:/POKROV-tools/release-evidence/1.2.0-candidate27-cli-rebuild-2026-09-03/`
  and
  `E:/POKROV-tools/release-evidence/1.2.0-candidate28-owner-upgrade-2026-09-03/`.
