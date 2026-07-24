# VPN Наружу — Redacted Connection Health Summary

**Capture date:** 2026-07-22<br>
**Environment:** LDPlayer 14, Android 14 / x86_64<br>
**Package:** `online.vpnnaruzhu.client.android`<br>
**Build:** `1.8.1` (`versionCode 90`, in-app build label `1.8.1.90`)

Raw exit addresses, tunnel configuration, peer addresses, DNS targets, account data and authenticated logs were not retained in the worktree.

## Test Matrix

| State | Android tunnel | DNS / HTTPS observation | Exit observation | Result |
| --- | --- | --- | --- | --- |
| Disconnected baseline | no `tun0` | HTTPS control page loaded | baseline recorded outside the repository | control only |
| Smart / Automatic | `tun0` present, MTU 1280 | DNS and HTTPS control succeeded | exactly the same exit as the disconnected baseline | tunnel UI and interface came up, but the tested destination was routed directly |
| Direct / Automatic | `tun0` present, MTU 1280 | HTTPS control succeeded | exactly the same exit as both baseline and Smart | contradicts the in-app FAQ promise that Direct sends all traffic through a foreign server for this tested destination/state |
| Direct / United Arab Emirates | `tun0` present, MTU 1280 | browser failed with `DNS_PROBE_FINISHED_NXDOMAIN`; DNS and direct reachability checks failed | could not be measured | connected UI without usable Internet on the controlled test |

## Runtime Evidence

- The Android VPN consent path completed normally.
- The active tunnel used the app's AWG/WireGuard-derived backend; runtime logs identified the interface as `Tun/vpnn-tun` and showed keepalive activity.
- During the failed United Arab Emirates test, Android Private DNS produced TLS timeouts and validation failures even though Android's connectivity layer also emitted a misleading VPN-validation success event.
- The app could be disconnected normally after each attempt. The final teardown found no `tun0` interface.

## Interpretation Boundary

This is a controlled emulator smoke test, not a packet-level audit and not proof of behavior for every destination, server, ISP or ARM device. Smart mode is expected to bypass selected Russian traffic, so the unchanged Smart exit is not itself a defect. The unchanged **Direct / Automatic** exit is material because current FAQ copy says Direct routes all traffic through a foreign server. The selected UAE node additionally produced a clear connected-but-offline failure in this environment.
