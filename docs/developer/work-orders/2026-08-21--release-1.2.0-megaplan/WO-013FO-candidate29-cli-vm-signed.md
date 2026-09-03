# WO-013FO — candidate.29 signed CLI build and bounded Windows VM

Status: `PASS_PRIVATE_SIGNED_CANDIDATE29_CLI_AND_BOUNDED_WINDOWS_VM`

Observed: `2026-09-03T09:47:05Z`–`2026-09-03T10:03:26Z`

Production/public mutation: `NONE`

## Outcome

Create the exact all-platform successor required by WO-013FN without taking
control of the owner's desktop. Candidate 29 is a six-artifact private signed
candidate built through the headless CLI path from current platform/client
source and the pinned Core artifact source.

The exact Windows setup upgrades the installed candidate.28 precursor on its
first attempt. All `11/11` installed runtime identities match, the protected
installation owner is reused, the LocalSystem service is healthy, the
ordinary-user UI opens, a secret-free direct fixture passes TUN/DNS connect and
clean disconnect, and a real connected guest reboot restores the clean network
baseline. The VM is powered off afterward and returned to `2 CPU / 4096 MiB`.

Candidate 29 is not a release decision. Gate F has not yet been regenerated
for this candidate, and no public or production promotion occurred.

## Exact identity

| Item | Identity |
|---|---|
| Candidate | private `pokrov-1.2.0-candidate.29`, app `1.2.0+4053`, six artifacts |
| Sources | platform `efb05e0899ad51afd4453ae2fb75f8cafe96db7e`; client `7e3e771fe36333a75244cbfd828c60beb84c7ff1`; Core `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Windows setup | `60487a7bb17da33dbca842a146f6eb24dddd089e532c241670c9c0fd79610451`, `29154403` bytes |
| Windows manifest | `8d535ff682b7beac7a23c52d63cd37698a1d6d8edbf19c48a2121ac9f398f9a3`, `11/11` files |
| Android | four production APKs plus store AAB; certificate `0a0602a7...4b2500` |
| Handoff / SBOM / provenance | `f0579169...9ab8` / `07a4e19e...2e44` (`352` components) / `2993b8a1...7c77` |
| Signed manifest | release-index `71e2c71...`; manifest `231e3d52...e9df`; signature `215f8234...27bfc`; receipt `097b0c3f...24fcf` |
| Signer | hosted run `33741376651`, retained artifact digest `sha256:e5683b5c...1250c` |
| Windows signing | `SKIPPED_BY_OWNER`, direct beta only; SmartScreen/unknown-publisher warning remains mandatory |

## CLI and supply checks

The full build passes release/repository/shared-facts/observability/logging,
handoff and rollback contracts; app-shell `413/413`; runtime engine with the
declared optional real-Core skip; Android `8/8`; Linux `5/5`; Windows widget
`23/23`; Android direct/store Gradle tests; Windows analyze, Release and Inno
assembly. Fresh native CTest passes Release `7/7` and Debug `8/8`.

Four APKs are production-signed with the expected certificate. The AAB JAR
signature integrity and fingerprint pass; its self-managed upload key has no
public chain or timestamp and is not described as public-chain trust. Offline
supply validation binds `6/6` artifacts, `11/11` Windows files, strict-v2
handoff, SBOM and provenance. The final high-confidence archive scan reports
zero findings. The earlier deliberately overbroad scan is retained under an
explicit diagnostic label and receives no release status.

Release-index PR 53 and its source-contract job pass. The main-only signer
creates the exact Ed25519 manifest and independently validates it. PR 54
records the receipt after its own source-contract PASS. The candidate directory
retains only final handoff inputs; two zero-placeholder preliminary handoff
files were removed after all final replacements and signature files existed.

## Isolated Windows result

The candidate setup and package manifest are copied into the guest through
Guest Control and re-hashed before execution. UAC is accepted only on the
headless virtual console. The first upgrade attempt records
`POKROV_INSTALL_OWNER_REUSED_FOR_UPGRADE` and successful installation. All
`11/11` files match exact size and SHA-256; `POKROVService` is `Running`,
`Automatic`, `LocalSystem`.

The production authenticated pipe then stages the connection-material-free
direct fixture. TUN changes `0 -> 1`; route and DNS fingerprints change;
Core reports `running=1`, `core_egress_validated=1`, `dns_ready=1`; DNS and API
health pass. Disconnect removes the tunnel and restores exact same-boot route
and DNS fingerprints. A connected Windows reboot leaves the service clean and
lazy at `artifact_ready`, with no tunnel, restored route/DNS, working API DNS
and health `200`.

The ordinary-user app process opens responsively in the interactive guest and
renders the protection shell, connect control, location selector and WARP
toggle without an error dialog. It is then closed; the service remains running
and the tunnel count remains zero. No host input, route, DNS, adapter or tunnel
is used or changed.

## Remaining gates

The direct fixture deliberately preserves public egress and therefore does
not prove a managed POKROV node, DE, AWG3.1/AWG2 or Smart DNS. Connected
uninstall, 32-client contention on the exact installed build, Windows 10,
SmartScreen interaction, sleep/resume, forced process/service termination,
external IPv6/leak and endurance remain separate.

Exact APK install/runtime on physical ARM64 Wi-Fi and Beeline remains manual,
including default/fallback, AWG3.1 then AWG2, WARP, Smart DNS, Private DNS,
Doze/OEM, handover and leak matrices. Current/Brain/general-RU origins,
provider/PostgreSQL/outbox, Operator OIDC/RBAC, legal/commercial approval,
runtime rollback, comparable performance/accessibility and the final live
aggregate are not transferred from predecessors.

Gate F is `NOT_RUN_FOR_CANDIDATE29`. No tag, GitHub Release, public assets,
store submission, stable pointer or production deploy exists.

## Evidence

- tracked summary:
  `evidence/013FO-candidate29-cli-vm-signed/013FO-candidate29-cli-vm-signed.json`,
  SHA-256 `4a070634264f38f86b15a8b5ceb418128d2467682e6f29f1fb2361df04505b0b`;
- exact private candidate:
  `E:/POKROV-tools/release-candidates/pokrov-1.2.0-candidate.29/`;
- external build, JUnit and sanitized VM evidence:
  `E:/POKROV-tools/release-evidence/1.2.0-candidate29-all-platform-2026-09-03/`;
- release-index PRs `53` and `54`; signer run `33741376651`.
