# Release Gate Report

- Generated at: `2026-05-15 04:17:00`
- Status: `PASS`
- Gate set: `quick`
- Brain IP supplied: `yes`
- Client platform gates: `none`
- Android audit required by selected gates: `operator-attested separately`

## Summary

| Gate | Command | Result |
|---|---|---|
| Brain-origin runtime/static verify | `python scripts\verify_brain_ready.py --brain-ip 82.21.114.104 --web-domain pokrov.space --api-domain api.pokrov.space --connect-domain connect.pokrov.space --ssh-user root --ssh-port 29374` | exit `0` |
| Node predeploy readiness | `python scripts\predeploy_node_readiness.py --brain-ip 82.21.114.104 --web-domain pokrov.space --ssh-user root --ssh-port 29374 --json-out docs\audit-artifacts\node-predeploy-readiness-2026-05-15.json` | exit `0`, `ok=true`, `failures=[]` |
| Brain runtime app-download smoke | `python scripts\brain_runtime_app_download_smoke.py ... --output docs\audit-artifacts\brain-runtime-app-download-smoke-2026-05-15.json` | `PASS` |
| Brain payment/email live probe | `python scripts\brain_payment_email_readiness.py ... --post-deploy-live --output docs\audit-artifacts\brain-post-deploy-live-probe-2026-05-15.json` | `PASS` |

## Evidence Classification

| Evidence | Scope | Status | Notes |
|---|---|---|---|
| current-origin check | local quick/full gate set | PASS | See `release-gate-local-quick-2026-05-15.md` and `release-gate-full-local-2026-05-15.md`. |
| brain-origin check | `scripts/verify_brain_ready.py` plus node predeploy readiness | PASS | Services active, public API health OK, static pages returned HTML, subscription fetches succeeded, node readiness JSON has no failures. |
| RU-origin check | external RU probe (`mini` or replacement) | OPERATOR_ATTESTED_LIMITED | Owner reduced scope: Telegram-from-Russia is not a blocker; brain/API reachability from RU remains best-effort if RU host access exists. |
| Android physical audit | release-build localhost/control-surface audit | OPERATOR_ATTESTED | Owner reported physical Android audit completed and OK. |
| Runtime app-download smoke | `/api/client/apps` and provider checks | PASS | Brain-signed initData runtime smoke returned the Android APK, Windows EXE, and install docs URLs. |
| Client platform builds | GitHub Release artifacts | PASS | Existing GitHub Release APK/EXE URLs were reachable on 2026-05-15. |

## Command Tails

```text
[caddy] active
[portal-api] active
[portal-bot] active
[portal-helpbot] active
[portal-feedbackbot] active
[health443] {"status":"ok","ts":"2026-05-15T01:15:13.806867"}
sub_fetch_1 user=selected mode=token fmt=base64 lines=4 hosts=4 connect_json=1 outbounds=8
sub_fetch_2 user=selected mode=token fmt=base64 lines=4 hosts=4 connect_json=1 outbounds=8
sub_fetch_3 user=selected mode=token fmt=base64 lines=4 hosts=4 connect_json=1 outbounds=8
sub_fetch_4 user=selected mode=token fmt=base64 lines=4 hosts=4 connect_json=1 outbounds=8
sub_fetch_5 user=selected mode=token fmt=base64 lines=4 hosts=4 connect_json=1 outbounds=8
```

`predeploy_node_readiness.py` printed transient Paramiko banner warnings while checking node-side SSH details, but the generated JSON ended with `ok=true` and `failures=[]`; node TCP/TLS probes and drift checks were green.
