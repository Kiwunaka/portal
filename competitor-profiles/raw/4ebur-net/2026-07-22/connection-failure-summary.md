# 4ebur.net Controlled Connection Failure

**Date:** 2026-07-22<br>
**Device:** LDPlayer Android 14, x86_64<br>
**App:** `com.cheburnet.mobile` 5.1.0<br>
**Protocol/location:** VLESS, free Poland / Warsaw `#2`<br>
**Precondition:** no other competitor process and no `tun0`; Android VPN consent granted.

## Result

- Connect caused a fatal foreground-process crash before `tun0` appeared.
- Android force-finished `com.cheburnet.mobile/.MainActivity` and returned to the launcher.
- Exception: `java.lang.UnsatisfiedLinkError` for native method `hev.htproxy.TProxyService.TProxyStartService(java.lang.String, int)`.
- Call path: `hev.htproxy.TProxyService` → `com.cyberwool.xray.XrayVpnConnection.initWithService` → Xray VPN service start coroutine.
- No endpoint, IP, key, token, configuration or raw log payload is retained here.

## Interpretation Limit

This demonstrates a missing or unloaded JNI implementation in the audited x86_64 LDPlayer artifact/runtime. It is not evidence that the service fails on ARM hardware or that its remote VPN nodes are unavailable.
