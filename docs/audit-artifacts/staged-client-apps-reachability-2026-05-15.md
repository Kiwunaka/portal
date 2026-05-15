# Staged Client Apps Reachability Check

Generated: 2026-05-15

## Verdict

Status: `PASS`

The GitHub Releases Android APK and Windows EXE URLs from the client release handoff are reachable, and the public install docs page returns HTTP 200. This evidence stores only public URLs and response metadata.

## Commands

```powershell
curl.exe -L -I --connect-timeout 30 --max-time 120 https://github.com/Kiwunaka/POKROV-app/releases/download/v0.2.0-beta.1/pokrov-android-universal.apk
curl.exe -L -I --connect-timeout 30 --max-time 120 https://github.com/Kiwunaka/POKROV-app/releases/download/v0.2.0-beta.1/pokrov-windows-setup-x64.exe
curl.exe -L -I --connect-timeout 30 --max-time 120 https://pokrov.space/install/
```

## Result

```text
[OK] android.apk_url: HEAD 302 from github.com, final HEAD 200 from release-assets.githubusercontent.com, Content-Length 143259872, Content-Type application/vnd.android.package-archive.
[OK] windows.exe_url: HEAD 302 from github.com, final HEAD 200 from release-assets.githubusercontent.com, Content-Length 27455488, Content-Type application/octet-stream.
[OK] docs_url: HEAD 200 from pokrov.space/install/, Content-Length 49914, Content-Type text/html; charset=utf-8.
[OK] smoke completed
```

## Classification

- Android APK GitHub Releases URL: PASS
- Windows EXE GitHub Releases URL: PASS
- Install docs URL: PASS

The live runtime app-download smoke is tracked separately in `docs/audit-artifacts/brain-runtime-app-download-smoke-2026-05-15.json`.
