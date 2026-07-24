# ByeByeDPI App — Competitor Profile

**Package:** io.github.romanvht.byedpi
**Generated:** 2026-07-12
**Depth:** local APK static profile
**Evidence:** PASS_DIRECT for found APK candidate

## At a Glance

| Metric | Value |
|---|---|
| Version | 1.7.6, versionCode 1760 |
| Target SDK | 34 |
| Modes | Local VPN and proxy |
| ABI | arm64, armv7, x86, x86_64 |
| Strategies | 60 |
| Target groups | 8, 139 unique domains |

## Security and Privacy

- No static ad, billing or telemetry SDK markers found.
- Self-signed Roman Kostin certificate; official provenance not confirmed.
- Main risk: exported unprotected ToggleActivity can accept strategy and service-control extras from another installed app.
- Broad storage and QUERY_ALL_PACKAGES.
- Unencrypted JSON export and unredacted diagnostics.

## Strengths

- Quick Tile.
- CLI and GUI editors.
- Strategy tester.
- History with pin/rename.
- Custom target lists.
- Separate autostart and auto-connect.

## Weaknesses

- It is local DPI bypass, not remote privacy VPN.
- No clear first-run education.
- Potential LAN proxy exposure.
- Empty whitelist ambiguity.
- Quick Tile silently fails before VPN consent.

## POKROV Implication

Use its power-user tooling with a permission-safe, signed, redacted implementation.

## Raw Data Sources

- Local APK source: <redacted-local-source>/ByeByeDPI-1.7.6.apk
- SHA-256: C86359CD02D173A3EAFF90FFE038B7A4018D844C139B92515678BD7D7B10BFDD
- [Full report](../docs/competitive/telegram-vpn-2026-07-12/final-market-report.md)
