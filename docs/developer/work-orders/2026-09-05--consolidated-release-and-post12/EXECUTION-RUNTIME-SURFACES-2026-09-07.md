# Owned Pi and Huawei execution — 2026-09-07

The owner explicitly directed tests on the existing Windows VM, Raspberry Pi 4
and connected Android. All three surfaces were accessed. [Retained evidence](evidence/runtime-surfaces-2026-09-07.json).
Windows source/runtime results are in [W04](EXECUTION-W04-SHELL.md).

## Raspberry Pi 4

Current Core `8dc57a8` was exported from the confirmed Git commit and built with
Go1.26.8 as Linux ARM64. The canonical
`scripts/remote_run_owned_awg_core_interop.py` executed both `awg31_lab` and
`awg2_lab` on trusted alias `shrek`, with explicit source confirmation, tool
paths, SSH config/trust and isolated temporary root. Both tests PASS, including
actual registered authenticated handshake/egress tests and temporary-state
removal. Receipts retain binary/tool/material digests without raw material.
No server, host interface or route configuration changed.

The first command used old Go1.25.13 and failed before material retrieval; the
correct toolchain verifies all modules. A subsequent strict-host preflight
failed because that trust input lacked the Pi entry. Combining the already
trusted Pi key with owned-node keys resolved it without host-key bypass.
The tool's `execution_origin=ru` identifies the registered Pi and direct default
route. No independent geographic check or whole-client RU acceptance is claimed.

## Huawei

Same installed Android12/API31 ARM64 APK, client `9334d46`, Core `8dc57a8`.
A controlled Wi-Fi→mobile→Wi-Fi sequence retained the same process, foreground
VPN service and TUN in every timed sample. Explicit mobile protection refresh
also retained service and confirmed tunnel/DNS/VPN egress; restored Wi-Fi refresh
confirmed protection. Final installed hash matches `d849d273…e14d2`; Wi-Fi on,
VPN connected as observed at this slice's start. App observer evidence is not
independent leak/packet/route-matrix acceptance.

An earlier resumed-UI attempt ended with absent service after Wi-Fi disable and
refresh. It lacked a native before-state and remains an unresolved observation.
Two controlled sequences did not reproduce it. The full D02/OEM/API/IPv6/MTU/
UDP53/endurance matrix therefore remains open. Canonical device evidence lives
in client `docs/operations/evidence/2026-09-07-r12-network-handoff/`.

No production deployment, repository push/merge, payment, release candidate,
store upload or public promotion. These results advance available hardware
verification and do not declare the consolidated plan complete.
