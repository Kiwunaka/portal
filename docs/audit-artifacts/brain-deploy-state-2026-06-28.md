# Brain Deploy State

Date: 2026-06-28

Command:

```powershell
python scripts/verify_brain_ready.py --brain-ip 82.21.114.104 --ssh-user root --ssh-port 29374 --repeat 2
```

Classification: `PASS`

Scope: brain-origin service and deployed-surface readiness check. This proves
the checked services were active, listener ports were present, brain-local
HTTPS routes responded, and subscription/connect payload fetches worked without
printing bearer subscription tokens. It does not prove real Telegram WebApp
user-session behavior, current-origin authenticated app-session behavior, owner
deploy approval, RU-origin reachability, device install/connect behavior,
payment maturity, signing, or store readiness.

Output:

```text
[caddy] active
[portal-api] active
[portal-bot] active
[portal-helpbot] active
[portal-feedbackbot] active
[listen] LISTEN 0      4096         0.0.0.0:443        0.0.0.0:*    users:(("haproxy",pid=358288,fd=7))
LISTEN 0      4096               *:8444             *:*    users:(("caddy",pid=830,fd=9))
[health443] {"status":"ok","ts":"2026-06-28T09:49:53.145551"}
[webapp443] <!DOCTYPE html><!--NhDdrttF3kJgCm1a_mP_7--><html lang="ru" class="scroll-smooth manrope_f633c6a-module__itHekW__variable jetbrains_mono_e6001fbd-module__b3APNG__variable"><head><meta charSet="utf-8"/>
[mkt443] <!DOCTYPE html><html lang="ru" class="__variable_fe7774"><head><meta charSet="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/><link rel="preload" as="image" href="/pokrov-
[mktCabinet443] <!DOCTYPE html><html lang="ru" class="__variable_fe7774"><head><meta charSet="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/><link rel="preload" as="image" href="/pokrov-
[offer443] <!DOCTYPE html><html lang="ru" class="__variable_fe7774"><head><meta charSet="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/><link rel="preload" as="image" href="/pokrov-
[checkout443] <!DOCTYPE html><html lang="ru" class="__variable_fe7774"><head><meta charSet="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/><link rel="stylesheet" href="/_next/static/cs
[fkverify443] 1b55d34fd0acfa8360d43822d1d08018
sub_fetch_1 user=selected mode=token fmt=base64 lines=5 hosts=5 connect_json=1 outbounds=14
sub_fetch_2 user=selected mode=token fmt=base64 lines=5 hosts=5 connect_json=1 outbounds=14
```

Result: brain-origin deploy state and subscription/connect fetch behavior are
green for this check. The Q-004 live-deploy gate remains `MANUAL_OWNER_TEST`
until real Telegram/current-origin authenticated app-session evidence and owner
deploy approval are provided or explicitly skipped.
