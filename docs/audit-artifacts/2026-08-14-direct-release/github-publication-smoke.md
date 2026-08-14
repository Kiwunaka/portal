# POKROV 1.0.5-beta.1 public asset smoke

Observed at: 2026-08-14T08:56:25+03:00

Release: `https://github.com/Kiwunaka/pokrov/releases/tag/v1.0.5-beta.1`

GitHub state: public, prerelease, not draft, eight assets.

Anonymous downloads were streamed from the public GitHub release URL and
hashed independently after publication:

| Asset | Bytes | SHA-256 | Result |
| --- | ---: | --- | --- |
| `pokrov-android-arm64-v8a.apk` | 99117851 | `F36CA9EAB09BFC0D0AA748EC526445143AB4B78241F360702EE4EA2ABC0BA3A5` | PASS |
| `pokrov-android-armeabi-v7a.apk` | 88460533 | `4CF215469580ABC1BEE0F6598D12ABE3A5DFAAB91DF42A0736DEB5E0554D8305` | PASS |
| `pokrov-android-x86_64.apk` | 107631710 | `0EF7AA3E828E09249AAFE49BAF88BEBEDC1B79746341B1F327A5417A11B7FB59` | PASS |
| `pokrov-android-universal.apk` | 289871382 | `13E776C3552773654C03632F134E2FA7339EEA280F7615448C77157D9E38E684` | PASS |
| `pokrov-windows-setup-x64.exe` | 38768640 | `02EA8AED7D63B8D1BB42EB3A09A22BD67C215EB80C86E3B8975FB10236D2E8F1` | PASS |
| `pokrov-windows-portable-x64.zip` | 38997174 | `877A4CDC61AB85E815139F258CCD4C3BC2C944EDB8E55D74041CF15A0B64619B` | PASS |
| `pokrov-windows-1.0.5-beta.1.manifest.json` | 2666 | `9BB2B251405FCAAEBFD87A5C6740E6A692B1E0453D8432CA01FD1D2756641A1F` | PASS |
| `SHA256SUMS.txt` | 680 | `6C11A758DD1E72BB4287C4DC83C0C8CFDE941DF85567A48BF62D3F898564D7CD` | PASS |

Classification: PASS. Production runtime synchronization was still pending at
the time of this smoke.
