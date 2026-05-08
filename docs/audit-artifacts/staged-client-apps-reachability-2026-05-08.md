# Staged Client Apps Reachability Check

Generated: 2026-05-08

## Verdict

PASS for staged URL reachability after artifact staging. The staged `/api/client/apps` payload has valid outside-store URL shape, and the GitHub Releases APK/EXE plus install docs URLs respond successfully.

## Command

```powershell
python scripts\smoke_client_apps.py --apps-json docs\audit-artifacts\staged-client-apps-2026-05-07.json --require-release-handoff --timeout 20
```

## Result

```text
[OK] staged /api/client/apps payload loaded from docs\audit-artifacts\staged-client-apps-2026-05-07.json
[OK] release handoff URLs are present
[OK] android.apk_url: HEAD 200 -> https://github.com/Kiwunaka/POKROV-app/releases/download/v0.2.0-beta.1/pokrov-android-universal.apk
[OK] windows.exe_url: HEAD 200 -> https://github.com/Kiwunaka/POKROV-app/releases/download/v0.2.0-beta.1/pokrov-windows-setup-x64.exe
[OK] docs_url: HEAD 200 -> https://pokrov.space/install/
[OK] smoke completed
```

## Classification

- Android APK GitHub Releases URL: PASS
- Windows EXE GitHub Releases URL: PASS
- Install docs URL: PASS

Do not sync runtime `APP_*` links or publish public download copy from these staged URLs until the live runtime app-download smoke passes with env-only Telegram init data.
