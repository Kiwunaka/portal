# Brain-Origin Static Deploy Verify 2026-05-09

Status: `PASS_STATIC_NO_GO`

Scope:

- Static deploy only: `webapp/out` and `marketing/out`.
- Deployed release directory: `/var/www/portal/releases/20260509114547`.
- Root repo commit verified/deployed from local `master`: `89df59aefe3c4324c69f86d5e59324b52265ab6f`.
- No runtime `APP_*` sync was performed.
- Paid checkout remained closed.
- Telegram announcement was not posted.

Commands:

```powershell
cd webapp
npm.cmd run build
cd ..\marketing
npm.cmd run build
cd ..
python scripts\remote_deploy_brain_static_sites.py --brain-ip 82.21.114.104 --ssh-user root --ssh-port 29374 --plan-only
python scripts\remote_deploy_brain_static_sites.py --brain-ip 82.21.114.104 --ssh-user root --ssh-port 29374
python scripts\verify_brain_ready.py --brain-ip 82.21.114.104 --ssh-user root --ssh-port 29374
```

Brain-origin results:

- `caddy`: active
- `portal-api`: active
- `portal-bot`: active
- `portal-helpbot`: active
- `portal-feedbackbot`: active
- `https://api.pokrov.space/api/health` through brain-origin: `{"status":"ok"}`
- `https://app.pokrov.space/` through brain-origin: HTML served
- `https://pokrov.space/` through brain-origin: HTML served
- `https://pay.pokrov.space/checkout/` through brain-origin: HTML served
- `/fk-verify.html`: absent or safe fallback, no legacy marker
- `/fk-payment-theme.css`: absent or safe fallback, no legacy marker
- Subscription fetch repeated 5 times: `lines=4`, `hosts=4`, `connect_json=1`, `outbounds=8`

External read-only checks after deploy:

- `https://app.pokrov.space/`: `200`
- `https://app.pokrov.space/admin/release/`: `200`
- `https://app.pokrov.space/release-status.json`: `NO_GO`, `safe_to_publish_public_beta=false`
- `https://api.pokrov.space/api/payments/providers`: `blocked=true`, provider count `0`, public blocked text present
- Rendered `https://pokrov.space/checkout/`: payment closed copy present, FreeKassa absent, no paid-ready claim, no console errors

Current blocker:

Runtime app download links still require an explicit operator authorization file or message containing exactly:

```text
RUNTIME LINK SYNC GO FOR APP-DOWNLOAD SMOKE
OPERATOR_APPROVED_RUNTIME_LINK_SYNC=true
STAGED GITHUB ASSET REACHABILITY GREEN
NO PUBLIC ANNOUNCEMENT
PAID CHECKOUT REMAINS CLOSED
```

Until that happens, public beta remains `NO_GO`.
