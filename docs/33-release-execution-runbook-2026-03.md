# Р•РґРёРЅС‹Р№ СЂРµР»РёР· 4ebur: Stage 2 Runbook (Execution)

РћР±РЅРѕРІР»РµРЅРѕ: 5 РјР°СЂС‚Р° 2026

Р­С‚РѕС‚ РґРѕРєСѓРјРµРЅС‚ Р·Р°РєСЂС‹РІР°РµС‚ СЃР»РµРґСѓСЋС‰РёР№ СЌС‚Р°Рї: Р±РµР·РѕРїР°СЃРЅР°СЏ РІС‹РєР»Р°РґРєР° СЃ quality gates Рё rollback-safe С‚РѕС‡РєР°РјРё.

## 1. РџСЂРµРґСѓСЃР»РѕРІРёСЏ
- Р’РµС‚РєР° СЃРѕРґРµСЂР¶РёС‚ РІСЃРµ РёР·РјРµРЅРµРЅРёСЏ СЌС‚Р°РїР° (critical fixes + admin MVP + metrics + docs).
- РЎРµРєСЂРµС‚С‹ РЅРµ С…СЂР°РЅСЏС‚СЃСЏ РІ СЂРµРїРѕР·РёС‚РѕСЂРёРё, С‚РѕР»СЊРєРѕ РІ env/secret manager.
- Р”РѕСЃС‚СѓРї Рє brain РїРѕ SSH РµСЃС‚СЊ Сѓ РѕРїРµСЂР°С‚РѕСЂР° (СЂСѓС‡РЅРѕРµ РІС‹РїРѕР»РЅРµРЅРёРµ).

## 2. Р›РѕРєР°Р»СЊРЅС‹Рµ РіРµР№С‚С‹ (РѕР±СЏР·Р°С‚РµР»СЊРЅРѕ)

### Р’Р°СЂРёР°РЅС‚ A: РѕРґРЅРёРј Р·Р°РїСѓСЃРєРѕРј
- РўРѕР»СЊРєРѕ quality gates:
  - `python scripts/release_orchestrator.py --gates-only`
- РџРѕР»РЅС‹Р№ СЂРµР»РёР·РЅС‹Р№ РїСЂРѕС…РѕРґ (gates -> deploy -> verify):
  - `python scripts/release_orchestrator.py --brain-ip <BRAIN_IP> --web-domain <WEB_DOMAIN> --api-domain <API_DOMAIN>`
- Dry-run (РїРѕРєР°Р·Р°С‚СЊ РІСЃРµ РєРѕРјР°РЅРґС‹ Р±РµР· РІС‹РїРѕР»РЅРµРЅРёСЏ):
  - `python scripts/release_orchestrator.py --brain-ip <BRAIN_IP> --web-domain <WEB_DOMAIN> --api-domain <API_DOMAIN> --dry-run`
- Verify-only (С‚РѕР»СЊРєРѕ РїРѕСЃС‚-СЂРµР»РёР·РЅР°СЏ РїСЂРѕРІРµСЂРєР°):
  - `python scripts/release_orchestrator.py --brain-ip <BRAIN_IP> --web-domain <WEB_DOMAIN> --api-domain <API_DOMAIN> --verify-only`

РћР¶РёРґР°РµРјРѕ:
- Exit code `0`.
- РћС‚С‡С‘С‚: `docs/audit-artifacts/release_gate_report.md`.

### Р’Р°СЂРёР°РЅС‚ B: РІСЂСѓС‡РЅСѓСЋ
1. `python -m unittest discover tests`
2. `python -m unittest tests.test_api_auth_and_tickets`
3. `cd webapp && npm.cmd run build`
4. `python scripts/admin_webapp_smoke.py`

## 3. Release-Р°СЂС‚РµС„Р°РєС‚С‹ РїРµСЂРµРґ РІС‹РєР»Р°РґРєРѕР№
1. РЎРѕС…СЂР°РЅРёС‚СЊ Р»РѕРєР°Р»СЊРЅС‹Р№ РѕС‚С‡С‘С‚ gate-check РІ `docs/audit-artifacts/`.
2. Р—Р°С„РёРєСЃРёСЂРѕРІР°С‚СЊ РІРµСЂСЃРёРё/РєРѕРјРјРёС‚ РґР»СЏ backend Рё webapp.
3. РџСЂРѕРІРµСЂРёС‚СЊ, С‡С‚Рѕ РІ РїСѓР±Р»РёС‡РЅС‹С… СЃСЃС‹Р»РєР°С… Р±РѕС‚ = `portal_privacy_bot`.

## 4. РџРѕСЂСЏРґРѕРє РІС‹РєР»Р°РґРєРё (СЂСѓС‡РЅРѕР№, Р±РµР· remote-exec Р°РіРµРЅС‚Р°)

### 4.1 Backend deploy
1. РћР±РЅРѕРІРёС‚СЊ РєРѕРґ `portal_bot/` РЅР° brain.
2. Р’С‹РїРѕР»РЅРёС‚СЊ РјРёРіСЂР°С†РёРё (РµСЃР»Рё РїСЂРёРјРµРЅРёРјРѕ РїРѕ release).
3. РџРµСЂРµР·Р°РїСѓСЃС‚РёС‚СЊ:
- `systemctl restart portal-api`
- `systemctl restart portal-bot`
- `systemctl restart portal-helpbot`

### 4.2 Static deploy
1. РћР±РЅРѕРІРёС‚СЊ `webapp/out` Рё `marketing/out`.
2. РџРµСЂРµР·Р°РіСЂСѓР·РёС‚СЊ web-serving СЃР»РѕР№ (РЅР°РїСЂРёРјРµСЂ, Caddy), РµСЃР»Рё РЅСѓР¶РЅРѕ.

### 4.3 Metrics timer
1. Р•СЃР»Рё `portal-node-metrics.timer` РЅРµ Р°РєС‚РёРІРµРЅ:
- `python scripts/remote_install_node_metrics_timer.py --brain-ip <BRAIN_IP>`
2. РџСЂРѕРІРµСЂРёС‚СЊ:
- `systemctl is-enabled portal-node-metrics.timer`
- `systemctl is-active portal-node-metrics.timer`
- `journalctl -u portal-node-metrics.service -n 50 --no-pager`

## 5. Post-deploy sanity

### 5.1 API / subscription
- `curl -fsS https://<API_DOMAIN>/api/health`
- РџСЂРѕРІРµСЂРєР° `/s8Kx2mP7qR4wT/{token}` РЅР° С‚РµСЃС‚-РїРѕР»СЊР·РѕРІР°С‚РµР»Рµ.

### 5.2 Checkout / callbacks
- РўРµСЃС‚РѕРІС‹Р№ create order (RUB) С‡РµСЂРµР· СЂР°Р±РѕС‡РёР№ flow.
- РџСЂРѕРІРµСЂРєР° notify/callback idempotency Рё Р°РєС‚РёРІР°С†РёРё РїРѕРґРїРёСЃРєРё.

### 5.3 Admin webapp
- РђРґРјРёРЅ РІРёРґРёС‚ РІСЃРµ `/admin/*` СЂР°Р·РґРµР»С‹.
- РќРµ-Р°РґРјРёРЅ СЂРµРґРёСЂРµРєС‚РёС‚СЃСЏ РІ `/dashboard/`.

### 5.4 Metrics
- `GET /api/admin/metrics/status` -> `fresh`.
- `GET /api/admin/metrics/timeseries?...` РІРѕР·РІСЂР°С‰Р°РµС‚ С‚РѕС‡РєРё.

## 6. Rollback-safe С‚РѕС‡РєРё
1. Р”Рѕ backend restart.
2. РџРѕСЃР»Рµ backend restart, РґРѕ static update.
3. РџРѕСЃР»Рµ static update, РґРѕ metrics timer changes.

Rollback:
- Р’РѕР·РІСЂР°С‚ РЅР° РїСЂРµРґС‹РґСѓС‰РёР№ backend/static bundle.
- Р РµСЃС‚Р°СЂС‚ СЃРµСЂРІРёСЃРѕРІ.
- РџРѕРІС‚РѕСЂРЅС‹Р№ sanity-check СЂР°Р·РґРµР»Р° 5.

## 7. РРЅС†РёРґРµРЅС‚РЅС‹Рµ С€Р°Р±Р»РѕРЅС‹ (РєСЂР°С‚РєРѕ)

### 7.1 РЎРёРјРїС‚РѕРј: channel bonus revoke РЅРµ СЃСЂР°Р±Р°С‚С‹РІР°РµС‚
- РЎРјРѕС‚СЂРµС‚СЊ Р»РѕРіРё worker РїРѕ `channel_bonus_guard`:
  - `raw_status`
  - `normalized_reason`
  - `action`

### 7.2 РЎРёРјРїС‚РѕРј: РѕС€РёР±РєР° РѕР±РЅРѕРІР»РµРЅРёСЏ РїРѕРґРїРёСЃРєРё РїРѕ РєР»СЋС‡Сѓ
- РЎРІРµСЂРёС‚СЊ `sub_token` РІ Р‘Р” Рё `subId` РІ panel.
- РџСЂРѕРІРµСЂРёС‚СЊ Р»РѕРіРё forced sync РІ `control_panel.py`/`panel_client.py`.

### 7.3 РЎРёРјРїС‚РѕРј: stale metrics
- РџСЂРѕРІРµСЂРёС‚СЊ `portal-node-metrics.timer` + service journal.
- РџСЂРѕРІРµСЂРёС‚СЊ collector Рё СЃРІРµР¶РµСЃС‚СЊ API.

## 8. РњРёРЅРё-С‡РµРєР»РёСЃС‚ СЂРµР»РёР·-РјРµРЅРµРґР¶РµСЂР°
1. Р›РѕРєР°Р»СЊРЅС‹Рµ РіРµР№С‚С‹ PASS.
2. Backend РїРµСЂРµР·Р°РїСѓС‰РµРЅ Р±РµР· РѕС€РёР±РѕРє.
3. Static РІС‹РєР»Р°РґРєР° Р·Р°РІРµСЂС€РµРЅР°.
4. Checkout + callback + subscription flow Р·РµР»С‘РЅС‹Рµ.
5. `/api/admin/metrics/status` СЃРІРµР¶РёР№.
6. Р РµР·СѓР»СЊС‚Р°С‚С‹ sanity Рё РІСЂРµРјСЏ РїСЂРѕРІРµСЂРєРё Р·Р°С„РёРєСЃРёСЂРѕРІР°РЅС‹ РІ `docs/audit-artifacts/`.

## 9. GitHub Р°РІС‚РѕРјР°С‚РёР·Р°С†РёСЏ
- Manual Р·Р°РїСѓСЃРє РѕСЂРєРµСЃС‚СЂР°С‚РѕСЂР°: `.github/workflows/release-orchestrator-manual.yml` (`workflow_dispatch`, СЂРµР¶РёРјС‹ `dry-run` / `verify-only` / `full`).
- Weekly snapshot quick-gate РѕС‚С‡С‘С‚Р°: `.github/workflows/weekly-release-gate-snapshot.yml`.
- Weekly-РѕС‚С‡РµС‚С‹ РєРѕРјРјРёС‚СЏС‚СЃСЏ РІ РѕС‚РґРµР»СЊРЅСѓСЋ РІРµС‚РєСѓ: `reports/release-gates-weekly`.

