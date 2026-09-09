# Android — current Core installed on Huawei

**PASS_BOUNDED**, client `76614b1` / Core `02a091c`, Huawei ADA-AL00U,
Android 12/API31, current-origin. The prepared 101,229,131-byte ARM64 APK is now
installed: SHA-256 `0206cd2a0d76ae427a988bc2220af8f2157d5c153c212cbdcaa3338cf89b41ce`.
Canonical evidence is in client `docs/operations/evidence/2026-09-08-r12-android-device/`.
Client evidence commit `7ae931b`; [cross-repository receipt](evidence/android-device-20260908.json).

Same-signer `adb install -r` passed; installed hashes matched before and after
runtime checks. Location, routing and WARP preferences and the first-install
timestamp survived the replacement. Account identity was not independently
compared. VersionCode remains 4053; this does not prove a new-version/channel
update or final downloadable candidate.

Ordinary managed-profile Wi-Fi connect, Wi-Fi → mobile → Wi-Fi with explicit
protection refresh, and a second Wi-Fi reconnect all showed confirmed
tunnel/DNS/VPN egress. The four handoff samples retained one process and the
foreground VPN service. These are app observations, not independent leak or
AWG proof. The broad dumpsys transport list includes request declarations.

After handoff, routes matched but the policy-rule hash differed; exact original
rule restoration is unproven. A separate reconnect without radio changes
restored exact route/rule hashes and removed TUN and the service. Both outcomes
are retained. Final state: new APK, Wi-Fi/mobile enabled, VPN off, no `tun0`.

Read-only AWG binding preview rejected a stale label-matching 1.0.8 record;
it was not accepted as the current installation. No server binding, entitlement
or cohort changed. Installed AWG2/AWG3.1, IPv6/UDP53/MTU, Doze/battery,
independent origins and complete D01/D02/F07/release acceptance remain open.

Client seed with explicit platform/Core roots and PowerShell Core, docs contract,
26 retained hashes, file links and diff checks PASS. Initial tool/setup failures
are retained separately. No product source, release artifact, push, merge,
backend deploy or public pointer changed. Previous APK remains available for
rollback. Detailed commands and receipts: `E:/r12-android-device-20260908`.
