# Brain Static Public Smoke

Date: 2026-05-15

Status: `PASS`

Static deploy:

- command: `python scripts/remote_deploy_brain_static_sites.py --brain-ip 82.21.114.104 --web-domain pokrov.space --api-domain api.pokrov.space --ssh-user root --ssh-port 29374`
- release id: `20260515013230`
- auth method: key
- webapp bundle: 361 files, 5.5 MiB source, 1.2 MiB archive
- marketing bundle: 63 files, 2.3 MiB source, 776.3 KiB archive

Brain-origin smoke:

- `https://api.pokrov.space/api/health` via local resolve: HTTP OK, status `ok`
- `https://pokrov.space/` via local resolve: returned marketing HTML
- `https://app.pokrov.space/` via local resolve: returned webapp HTML
- `https://pokrov.space/fk-verify.html` via local resolve: returned verification hash
- `https://pay.pokrov.space/checkout/` via local resolve: returned checkout HTML

External HTTPS smoke:

- `https://api.pokrov.space/api/health`: HTTP 200, status `ok`
- `https://pokrov.space/`: HTTP 200
- `https://pokrov.space/install/`: HTTP 200
- `https://app.pokrov.space/`: HTTP 200
- `https://app.pokrov.space/release-status.json`: HTTP 200, `verdict=GO`, `safe_to_publish_public_beta=true`, includes `static_public_smoke`

Full brain verification after deploy:

- `python scripts/verify_brain_ready.py --brain-ip 82.21.114.104`: PASS
- services active: `caddy`, `portal-api`, `portal-bot`, `portal-helpbot`, `portal-feedbackbot`
- subscription fetch smoke: five selected-token fetches returned valid payload summaries

No secrets, private emails, payment ids, callback payloads, Telegram initData, subscription URLs, or access keys are stored in this artifact.
