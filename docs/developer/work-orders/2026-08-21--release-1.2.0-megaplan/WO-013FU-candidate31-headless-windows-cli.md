# WO-013FU — candidate.31 headless Windows CLI identity and contention

Status: `EXACT_CANDIDATE31_SAME_BYTE_WINDOWS_IDENTITY_PASS_IPC_32_OF_32_PASS`

Observed: `2026-09-03T17:27:55Z`–`2026-09-03T17:34:00Z`

Production/public mutation: `NONE`

## Outcome

Candidate.31's exact setup file and all eleven manifest-owned Windows runtime
files match the already installed files byte-for-byte inside the isolated
Windows 11 VM. The LocalSystem service is `Running` with automatic start, and
the corrected command-line contention probe completes `32/32` authenticated
status requests while the service remains running.

This is supplemental installed-identity and local IPC evidence. It does not
credit the noninteractive installer rerun, does not prove a managed connection,
and does not change Gate F from `BLOCKED 2/17/0`.

## Exact boundary

| Item | Identity |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.31`, app `1.2.0+4053` |
| Installer SHA-256 | `a6512bb6bbac328c62497ebad234b97a2794cb178a1949d35362e919f0d6adf0` |
| Windows manifest SHA-256 | `b73b48f584d8d7e436d2801447a3cf0ab0c13eee652a82c9464377c8ab94e6ee` |
| Status probe SHA-256 | `e398c7e8626e3594774d36ad146a61fcd1e095a9ace4a558650739d9b5a3ad87` |
| Guest | isolated `POKROV-Win11-Test`, Windows `10.0.26200.0` |
| Host UI/network | mouse, keyboard, screen focus, host routes, tunnel and DNS untouched |

Candidate.31 intentionally reuses the exact application bytes produced by the
fresh candidate.30 CLI build; WO-013FT regenerated only its candidate-bound
SBOM, provenance, handoff and signed release envelope. This work order does not
misrepresent those same bytes as another application compilation.

## Installed identity

The candidate.31 setup hash matches the expected private artifact. All `11/11`
runtime files are present and match both size and SHA-256 from the exact Windows
manifest. The service is present as `LocalSystem`, `Running`, and `Auto`; there
is no active POKROV adapter before the probe.

An attempted setup rerun from the noninteractive guest-control session exits
`1` before creating an installer log. It is retained as `NOT_CREDITED`, not as
an install PASS. Only the separately measured same-byte installed identity is
credited.

## Corrected contention probe

Two preliminary harness versions incorrectly interpreted child processes as
failures because PowerShell `Start-Process` did not retain their exit codes.
The second invalid run still parsed `32/32` available and accepted responses,
which exposed the harness defect. Both false results are retained in
`013FU-candidate31-ipc-harness-history.json`.

The corrected harness uses direct `.NET Process` handles and waits for every
child. Its exact result is:

```text
requested=32
passed=32
failed=0
exit_zero=32
parsed=32
available=32
accepted=32
stderr_empty=32
service_before=Running
service_after=Running
```

## Release interpretation

- `PASS`: exact same-byte installed file identity, service state and corrected
  32-client local IPC contention.
- `NOT_CREDITED`: setup rerun from the noninteractive guest-control context.
- `NOT_RUN`: managed default/AWG3.1/AWG2/Smart-DNS connection, connected
  uninstall, interactive SmartScreen and physical Android.
- Gate F remains `BLOCKED 2 PASS / 17 non-PASS / 0 FAIL` with no Gate G,
  public asset, Store submission, stable-pointer change or deploy.

The VM was shut down normally and ends in `poweroff`. Its configured resources
remain `2` vCPU and `4096` MB RAM.

## Evidence digests

The retained source-capture hashes are embedded in the JSON records:

| Capture | SHA-256 |
|---|---|
| Installed identity | `974e11496e8710739cce913e239c7e19dd8b68b2a16cda1e0f36479fe3db839c` |
| Invalid harness v1 | `1822f88f75f1888e608d56f7adeae56b89f20117e128e43e0becbbb2f0dd25fc` |
| Invalid harness v2 | `a90a29b7d9868478e5de535c03637e19a996337effaaea21e3f7b8c30d96f455` |
| Corrected contention result | `e4f1a53e18f77dc0056239af873d8e9739c11f788457a942ad7791ff9cc62c4d` |
