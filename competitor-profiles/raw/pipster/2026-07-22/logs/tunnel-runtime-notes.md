# Pipster Controlled Tunnel Runtime

Snapshot: 2026-07-22. Guest account, Auto server, Android 14 LDPlayer.

## Consent And Connection

- First connection triggered the standard Android VPN consent dialog.
- After consent, Pipster opened a Yandex Mobile Ads video before establishing the tunnel. The captured placement initially showed a 34-second reward countdown, then required leaving a separate end card.
- Only after the ad and end card were closed did Pipster establish `tun0` and show **VPN подключен**.
- Auto selected Germany; an external exit check resolved the VPN exit to Frankfurt am Main, Germany, AS58212 / dataforest GmbH.
- The exact public exit IP is intentionally excluded from the repository and held only in the sensitive temporary audit area.

## Network Evidence

- `tun0` IPv4/IPv6: private tunnel ranges only (`[IPv4 address omitted]/30`, `[IPv6 address omitted]/64`).
- Default IPv4 and IPv6 routes used `tun0`.
- MTU: 1400.
- Tunnel DNS list: local tunnel resolver `[IPv4 address omitted]` plus Google Public DNS `[IPv4 address omitted]` and `[IPv4 address omitted]`.
- One controlled ICMP request to `[IPv4 address omitted]` passed while the tunnel was active.
- Android `vpn_management` reported `com.vipin.pipster` as the active VPN package.

These checks prove a working tunnel for this exact session. They do not constitute a DNS/WebRTC/leak/security audit or performance benchmark.

## Repair Funnel

- Connected Home exposed **Не работает? / Попытаться исправить (1/4)**.
- Tapping it immediately removed `tun0` and opened another Yandex Mobile Ads placement, this time with a 98-second countdown, before any repair explanation or result.
- The ad was aborted by force-stopping Pipster to avoid an unnecessary 98-second resource-heavy playback. Repair stages 2–4 therefore remain unexecuted.
- Closeout after that abort: Pipster process absent and no `tun*` interface present.
