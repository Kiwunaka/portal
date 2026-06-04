# Deployment And Access

Last updated: 2026-05-28

## Document Status

This file is living source of truth for deployment entrypoints, runtime access, and sensitive material locations.

## Client Lane Distinction

Wave 0 now separates active client truth from retained client evidence:

- new client development truth belongs to `POKROV-app/main`, with live local checkout path `C:/Users/kiwun/Documents/ai/POKROV-app`
- retired bootstrap provenance is summarized in `docs/archive/client-lanes/app-next-bootstrap-summary.md`
- retained bridge bundle lineage is archived under `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/`
- commands in this guide now describe the active `POKROV-app` lane, with archive notes called out explicitly when retained bridge evidence matters

## Release Metadata Home

Release metadata now lives under the canonical client repo.

- bridge-period metadata root: `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/<version>/`
- post-cutover metadata root: `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/<version>/`
- keep `release-links.env` in that versioned folder only as compatibility evidence when needed
- keep generated manifests in `release-manifests/` under that same versioned folder
- keep the stable root-orchestrator pointer at `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/release-handoff.json` when it is intentionally maintained

## Control Plane

Canonical control-plane host:

- `brain`: `82.21.114.104`

Key services expected there:

- `portal-api`
- `portal-bot`
- `portal-helpbot`
- `portal-feedbackbot`
- `caddy`
- `x-ui`

RF auxiliary hosts:

- `mini`
  dedicated external RU probe origin, universal operator sandbox, and owner-approved emergency RU bridge endpoint for non-US delivery reachability
- `rf1`
  reserve RF ingress for operator and VIP/manual access

RF access rule:

- do not place control-plane services on `mini` or `rf1`
- do not add `rf1` to the normal runtime delivery pool in phase 1
- keep a hard kill switch for the `rf1` VIP/manual contour so it can be withdrawn without touching the standard consumer path
- `rf1` reserve work remains backlog-only
- owner-approved exception on `2026-06-01`: `mini` may run `ru_bridge_relay` on `tcp/443` through Xray Reality as an emergency bridge to POKROV delivery nodes except US; do not add `mini` to the normal runtime delivery pool and do not move control-plane services onto it
- owner-approved exception on `2026-04-24`: the live Telegram-only MTProto proxy runs on the dedicated free node (`151.245.217.23:9443`) through `portal-mtproto.service`; this is not a control-plane service and must not displace the free pool's existing `x-ui` listener on `tcp/443`
- `mini` / `RFMINI` is the canonical RU-origin sandbox when SSH credentials are current; if access is blocked, label the release evidence as `RU-origin check: BLOCKED_BY_ACCESS`
- current `mini` SSH access, verified on `2026-06-01`: use `kiwunaka@176.123.166.119:22` with the retained local password bundle; `29374` opens TCP but resets before the SSH banner and should not be used as the primary SSH path
- RU probe readiness itself is a tracked operational dependency for release confidence and is scoped to `POKROV` public hosts, API health, and delivery-node reachability

## Operator Shell Policy

- prefer `bash` when it is the simplest reliable operator path
- use `powershell` when quoting, Windows path handling, SSH invocation, or local tooling behavior is more reliable there
- pick the shell that reduces operator error for the exact command rather than forcing one shell everywhere

## Sensitive Material Locations

These locations are intentionally preserved and must not be deleted during cleanup:

- `portal_bot/.env`
- `VPN NODE SSH KEYS/`
- `secrets for merchant/`
- `ops-local/`
- `external/client-fork/app/windows/sign.pfx`
- `external/client-fork/app/windows/sign.cer`

Rules:

- do not duplicate secret values into documentation
- do not print raw secrets into commit messages or reports
- document locations and usage only
- release gate and deploy handoffs may name secret locations, environment variable names, and redacted command shapes, but must not include raw token values, webhook payloads, subscription links, MTProto links, payment identifiers, Telegram IDs, or private keys
- if a command tail or remote log contains a bearer token, callback signature, provider payload, personal connection URL, or full user identifier, redact the value before moving it into `docs/`, work-order evidence, screenshots, or release-captain handoff

## Canonical Deploy Scripts

### Backend code deploy

- [remote_deploy_brain_portal_code.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_deploy_brain_portal_code.py)

Typical use:

```powershell
python scripts/remote_deploy_brain_portal_code.py --brain-ip 82.21.114.104 --restart portal-api,portal-bot,portal-helpbot,portal-feedbackbot
```

Repo-side deploy rule:

- the default restart set is `portal-api`, `portal-bot`, `portal-helpbot`, and `portal-feedbackbot`
- the deploy payload must include the full shared backend truth set under `/root/shared/`: `product-facts.json`, `public-urls.json`, `design-tokens.json`, `tariff-catalog.json`, `access-matrix.json`, `promo-slots.json`, and `support-ai-knowledge.json`
- the deploy step should be treated as failed if any requested unit does not become `active` after restart
- support AI is a `portal-api` and `portal-helpbot` runtime feature. It stays disabled unless the `brain` environment sets `SUPPORT_AI_ENABLED=true` plus an API key. The default route is OpenRouter `https://openrouter.ai/api/v1` with `deepseek/deepseek-v4-flash`; switch providers only through env overrides. Leave `SUPPORT_AI_OPENROUTER_DATA_COLLECTION` blank unless a specific OpenRouter route requires `deny` or `allow`; an unsupported strict policy can make OpenRouter return no matching endpoints.
- keep `SUPPORT_AI_MAX_CONTEXT_CHARS` at `32000` or higher when deploying the expanded support KB; lower values can truncate later troubleshooting topics before they reach the model.
- knowledge refresh is operator-side: use `python scripts/pokrov_support_ai_kb_refresh.py run-pi --apply`, review `shared/support-ai-knowledge.json`, then deploy backend code/shared runtime assets to `brain`

Observer-lite canary install:

```powershell
python scripts/remote_install_node_observer.py --brain-ip 82.21.114.104 --node-code pl --run-now
```

### Static sites deploy

- [remote_deploy_brain_static_sites.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_deploy_brain_static_sites.py)
- static deploy packages `marketing/out` and `webapp/out` as local `tar.gz` bundles, uploads one archive per surface, extracts them into a versioned release directory, validates required files, then atomically switches `/var/www/portal/{marketing,webapp}` symlinks
- before bundling, static deploy appends the release id as `?v=<release>` to `/_next/static/*` references inside exported HTML so browsers do not keep stale cabinet chunks after a deploy; `app.pokrov.space` should also serve `Cache-Control: no-cache, must-revalidate` from Caddy

### Bot token / username switch

- [remote_switch_bot_tokens.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_switch_bot_tokens.py)

### Release orchestration

- [release_orchestrator.py](C:/Users/kiwun/Documents/ai/VPN/scripts/release_orchestrator.py)
- staged shortcuts:
  - `python scripts/release_orchestrator.py --stage gates`
  - `python scripts/release_orchestrator.py --brain-ip 82.21.114.104 --stage backend`
  - `python scripts/release_orchestrator.py --brain-ip 82.21.114.104 --stage static`
  - `python scripts/release_orchestrator.py --brain-ip 82.21.114.104 --stage deploy`
  - `python scripts/release_orchestrator.py --brain-ip 82.21.114.104 --stage verify`
- wrapper steps stream child output, print heartbeat lines during quiet long-running steps, and enforce per-step timeouts unless the matching `--*-timeout-sec 0` option is used
- the manual GitHub Actions release workflow passes dispatch inputs through step environment variables instead of interpolating them into shell source, scopes `NODE_PASS_BRAIN` only to the orchestrator step, and rejects secret-bearing remote runs unless `brain_ip` is the canonical `82.21.114.104` host with `pokrov.space` / `api.pokrov.space` domains

### Release handoff sync

- [remote_brain_apply_release_handoff.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_brain_apply_release_handoff.py)
- canonical client-owned metadata home: `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/`
- standard operator input: versioned `release-links.env` under that metadata home
- canonical stable metadata pointer when maintained: `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/release-handoff.json`
- schema reference: [release_handoff_metadata.schema.json](C:/Users/kiwun/Documents/ai/VPN/scripts/release_handoff_metadata.schema.json)

### API-only lifecycle smoke

- [api_lifecycle_smoke.py](C:/Users/kiwun/Documents/ai/VPN/scripts/api_lifecycle_smoke.py)

### Observer-lite node install

- [remote_install_node_observer.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_install_node_observer.py)

### Publishing and signing guide

- [publishing-and-signing-guide.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/publishing-and-signing-guide.md)

### Monitoring and visibility guide

- [monitoring-and-visibility.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/monitoring-and-visibility.md)

## Operator Handoff Runbooks

Use these when the release is blocked on one narrow operational step and the next person needs a simple checklist instead of the full guide:

- [Android Production Signing Handoff](C:/Users/kiwun/Documents/ai/VPN/docs/operations/android-production-signing-handoff.md)
- [Android Physical Device Audit Handoff](C:/Users/kiwun/Documents/ai/VPN/docs/operations/android-physical-device-audit-handoff.md)
- [Email Delivery Webhook Handoff](C:/Users/kiwun/Documents/ai/VPN/docs/operations/email-delivery-webhook-handoff.md)
- [Release Links And Final Handoff](C:/Users/kiwun/Documents/ai/VPN/docs/operations/release-links-and-final-handoff.md)
- [RU Origin Probe Handoff](C:/Users/kiwun/Documents/ai/VPN/docs/operations/ru-origin-probe-handoff.md)
- [Public Beta Release Runbook](C:/Users/kiwun/Documents/ai/VPN/docs/operations/public-beta-release-runbook.md)
- [Runtime App Download Smoke](C:/Users/kiwun/Documents/ai/VPN/docs/operations/runtime-app-download-smoke.md)
- [Lava.top Payment Operations](C:/Users/kiwun/Documents/ai/VPN/docs/operations/lavatop-payment-operations.md)

### Lava.top Checkout Enablement

The backend supports `lavatop` as the active RUB provider for public beta; public provider env must stay Lava-only (`RUB_PAYMENT_PROVIDER_ENABLED=lavatop`, `RUB_PAYMENT_PROVIDER_ORDER=lavatop`). As of `2026-05-15`, the authenticated cabinet beta path has redacted live evidence for invoice creation, authenticated success callback handling, invalid-auth rejection, account extension, and fulfillment idempotency. Required env is documented in [Lava.top Payment Operations](C:/Users/kiwun/Documents/ai/VPN/docs/operations/lavatop-payment-operations.md): `LAVATOP_API_KEY`, `LAVATOP_OFFER_ID` or per-plan `LAVATOP_OFFER_ID_<PLAN_CODE>`, and either `LAVATOP_WEBHOOK_API_KEY` or Basic webhook credentials. Anonymous public checkout also requires configured email delivery (`EMAIL_DELIVERY_WEBHOOK_URL` plus relay secret/SMTP env) before it can safely issue paid access keys.

Retained evidence: [Paid Checkout Launch Evidence - 2026-05-15](C:/Users/kiwun/Documents/ai/VPN/docs/audit-artifacts/paid-checkout-launch-evidence-brain-2026-05-15.json), [Brain Post-Deploy Live Probe - 2026-05-15](C:/Users/kiwun/Documents/ai/VPN/docs/audit-artifacts/brain-post-deploy-live-probe-2026-05-15.json), and [Live Payment And Email Confirmation - 2026-05-15](C:/Users/kiwun/Documents/ai/VPN/docs/audit-artifacts/live-payment-email-confirmation-2026-05-15.md). Failed-payment no-fulfillment and paid access-key delivery have beta evidence; refund/chargeback reconciliation remains an operator runbook requirement before stronger production checkout claims.

### External RU probe runner

- [ru_probe_runner.py](C:/Users/kiwun/Documents/ai/VPN/scripts/ru_probe_runner.py)

Typical use from the external RU host:

```powershell
python scripts/ru_probe_runner.py --reserve-host rf1.pokrov.space --probe-host mini --out ops-local/ru-probe.json
python scripts/render_ru_probe_report.py --input ops-local/ru-probe.json
```

Current SSH note for running the probe remotely: `mini` is reachable as `kiwunaka@176.123.166.119:22`. Do not copy the password into docs or reports; use the retained local password bundle or an approved secret channel.

### RF Reserve Note

- [remote_install_mini_canary_stack.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_install_mini_canary_stack.py)
- [remote_apply_ru_bridge_relay.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_apply_ru_bridge_relay.py)

Status:

- previous `remote_install_mini_canary_stack.py` xhttp/hysteria experiments remain historical/operator tooling only
- `remote_apply_ru_bridge_relay.py` is the current owner-approved emergency bridge path: it syncs active user UUIDs from `brain`, installs/preserves `mini` Xray Reality on `tcp/443`, restricts bridge egress to POKROV target nodes, excludes `us`, and patches public bridge metadata into `network_rollout_config`
- rerun `remote_apply_ru_bridge_relay.py --apply --update-brain-rollout` after meaningful user growth or before relying on the bridge for a live incident, because `mini` authorizes the active UUID snapshot that was synced at apply time
- when bridge targets mix DNS hosts and raw IP hosts, keep Xray routing allow rules split by `domain` and `ip`; one rule containing both fields can fail to match the country-hop connection and make every `Белые списки` detour appear dead
- rollback is `defaults.transport_profile=legacy_reality_fallback`; enable or keep `ru_bridge_relay` only through an explicit cohort/carrier/default decision after verification

### Telegram MTProto proxy on free node

- [remote_install_mtproto_proxy.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_install_mtproto_proxy.py)

Current state:

- the dedicated free node (`151.245.217.23`) hosts `portal-mtproto.service` on `tcp/9443`
- `x-ui.service` continues to own `tcp/443` on the free node for normal free-pool delivery
- the previous `mini:443` MTProto attempt is disabled; this compatibility proxy is kept only on the dedicated free node
- the MTProto secret and share links live only in `/etc/portal-mtproto.env` on the free node; do not copy them into docs, commits, or handoff reports
- `portal-mtproto-config-refresh.timer` is enabled on the free node because it can reach `core.telegram.org`
- the official Telegram MTProxy source currently needs a PID namespace workaround on this host, so the systemd unit starts it through `unshare --fork --pid --mount-proc`

Typical install or refresh from the repository root:

```powershell
python scripts/remote_install_mtproto_proxy.py --node-code free --node-host 151.245.217.23 --ssh-port 29374 --listen-port 9443 --enable-refresh-timer
```

If the endpoint must be registered with Telegram, send `151.245.217.23:9443` or an approved DNS name that resolves to `151.245.217.23` and still uses port `9443`.

### Feedback bot service install

- [remote_install_feedbackbot_service.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_install_feedbackbot_service.py)

## Transport Rollout And Node Shaping

The transport rollout stays additive: the current Reality path remains in place while app-first cohorts are moved to `grpc_443_primary` through rollout policy and per-node transport catalogs.

Transport policy rule:

- `nodes.transport_profiles_json` is the canonical per-node transport catalog for rollout and should carry the fixed profile set `legacy_reality_fallback`, `grpc_443_primary`, `reserve_xhttp_cdn`, and `operator_lab`; `ru_bridge_relay` lives in `network_rollout_config` because it is a cross-node RU bridge, not a node-local delivery inbound
- legacy node fields such as `inbound_id`, `vless_port`, and `reality_*` remain compatibility input and should synthesize `legacy_reality_fallback` when the transport catalog is empty
- `AppSetting.network_rollout_config` is the operator-controlled rollout source of truth for `transport_profile`, `dns_policy`, `routing_mode_default`, and `ip_version_preference`
- `network_rollout_config` is a JSON policy blob with `version`, `defaults`, `carrier_overrides`, `cohort_overrides`, `reserve_xhttp_cdn`, `ru_bridge_relay`, `operator_lab`, `package_catalog_feed`, `routing_rules_feed`, and `support_recovery_order`
- `defaults` normally pin `routing_mode_default=all_except_ru`, `transport_profile=legacy_reality_fallback`, and `dns_policy=ru_direct_split`; live incident response may temporarily set `transport_profile=ru_bridge_relay`
- `carrier_overrides` and `cohort_overrides` may only change `transport_profile`, `dns_policy`, `routing_mode_default`, and `ip_version_preference`
- `reserve_xhttp_cdn` stays opt-in, disabled by default, and is intended only as a reserve path on eligible nodes until a later rollout wave promotes it explicitly
- `ru_bridge_relay` stays opt-in unless an incident commander explicitly promotes it; app-managed sing-box manifests expose countries at the top level and nested `Обычный` / `Белые списки` choices under non-US nodes, while US remains a direct-only target and is never routed through the RU bridge
- `operator_lab` remains allowlist-only, carries `enabled`, `allowlist_install_ids`, `allowlist_tg_ids`, `allowlist_node_codes`, and `expires_at`, and must stay hidden from public UI and mass session/profile payloads
- app-managed session and profile delivery should use the rollout-selected transport profile, while manual/export compatibility links stay on `legacy_reality_fallback` until the share-link parity wave lands
- `GET /api/client/profile/managed` is the primary app-managed provisioning endpoint; `subscription_url` stays manual/import fallback only
- as of `2026-06-02`, premium delivery nodes `pl`, `it`, `us`, `de`, and `nl` run 3x-ui `3.2.5` with Xray `26.6.x`; `free` remains the dedicated free-pool fallback lane unless a separate free-node rollout is explicitly requested
- 3x-ui `3.x` requires CSRF for session-authenticated unsafe panel API requests; `PanelClient` must fetch `/csrf-token`, send `X-CSRF-Token` on panel POSTs, and keep an unsafe cookie jar for IP-based panel hosts such as `de`
- when backfilling many existing users into one 3x-ui inbound, create clients sequentially and verify the panel client count against `user_nodes`; concurrent `addClient` calls mutate the same inbound settings document and can leave database mappings ahead of actual panel clients

Rollout order:

1. Wave 0, code-first
   - migrate `nodes.transport_profiles_json`
   - backfill `legacy_reality_fallback` from the legacy node fields
   - seed `reserve_xhttp_cdn` metadata on eligible nodes without enabling it for public cohorts
   - ship backend changes for multi-inbound sync and `network_rollout_config`
   - expose rollout config and node transport health in admin/web surfaces
   - update the canonical docs in this task
2. Wave 1, deploy-first
   - run local tests and smokes
   - run `release_orchestrator.py --gates-only`
   - deploy the brain portal code
   - deploy static sites if the admin surface or public visibility changed
   - run `verify_brain_ready.py`
3. Wave 2, infra canary
   - choose one premium node as the canary
   - install the node-local transport front on public `:443` with `scripts/remote_apply_transport_front.py`
   - move the live `legacy_reality_fallback` listener behind the transport front on a loopback backend port
   - add the `grpc_443_primary` inbound on its loopback backend port behind the same transport front
   - prepare the reserve backend `reserve_xhttp_cdn` on its loopback port and SNI mapping, but keep the rollout flag disabled unless the explicit reserve test is requested
   - seed the node transport catalog with `legacy_reality_fallback`, `grpc_443_primary`, and reserve metadata
   - run `scripts/remote_transport_front_smoke.py` against the canary SNI names before cohort enablement
   - apply the qdisc profile and run the saturation smoke
   - enable `grpc_443_primary` only for a small RU-risk allowlist through `network_rollout_config`
4. Wave 3, fleet expansion
   - repeat inbound and qdisc rollout on the remaining premium nodes
   - move failover by `subnet`, then by `hoster_family`, then by country
   - after parity, switch `defaults.transport_profile` to `grpc_443_primary` for the RU-risk cohort
5. Wave 4, operator lab
   - add `operator_lab` on one controlled node only
   - open it through allowlist entries only
   - keep it out of public UI and non-operator payloads

Rollback shape:

- restore `defaults.transport_profile` to `legacy_reality_fallback`
- set `operator_lab.enabled=false`
- run `scripts/remote_apply_node_qdisc.py rollback`
- keep `nodes.transport_profiles_json` in place as dormant metadata instead of deleting it

Reserve-path rule:

- `reserve_xhttp_cdn` is prepared for operator-directed fallback only
- current reserve SNI is `cdn.connect.pokrov.space`
- the current transport-front template maps that reserve SNI to the loopback reserve backend
- when the reserve profile is selected, the client uses `transport_kind=xhttp` and `engine_hint=xray`; this does not change the default public `sing-box` path

Node shaping repo truth:

- `infra/node-qdisc-profiles.json` records `node_code`, `iface`, `uplink_mbps`, `target_rate_mbps`, and `preferred_qdisc`
- `target_rate_mbps` is fixed at `85%` of the confirmed sustainable uplink for each live node
- `scripts/remote_apply_node_qdisc.py` supports `install`, `apply`, `show`, `disable`, `rollback`, and `uninstall`
- `install` and `disable` control reboot persistence through `infra/portal-node-qdisc.service`; `rollback` removes the active qdisc without deleting the repo-truth profile
- node selection must come from explicit `NODE_CODE` provisioning or the built-in alias normalization such as `PLnode -> pl` and `FREENLnode -> free`
- if `sch_cake` is present, the script applies `CAKE nat triple-isolate`
- if `sch_cake` is unavailable, the script falls back to `fq_codel` and must report that fallback explicitly
- `scripts/remote_node_qdisc_smoke.py` runs one heavy egress flow plus parallel small HTTPS probes, records p95 latency / TTFB, and fails the gate if the heavy flow never materializes or starvation exceeds the configured thresholds
- `infra/portal-node-qdisc.service` restores the configured qdisc after reboot

## Current Bridge-Period Local Build Matrix

Canonical repo-local build and packaging commands for this wave:

- `python scripts/run_client_release_gate.py preflight`
- `python scripts/run_client_release_gate.py test --suite portal`
- `python scripts/run_client_release_gate.py test --suite full`
- `python scripts/run_client_release_gate.py build --target windows`
- `python scripts/run_client_release_gate.py build --target android-apk`
- `python scripts/run_client_release_gate.py build --target android-aab`
- `dart pub global run msix:create --build-windows false`

Current local-build notes:

- Android outside-store public beta is owner-attested for the `2026-05-15` launch decision; raw `python scripts/android_localhost_audit.py` evidence on a release-installed physical build remains required before stronger Android safety, store, or stable claims
- the platform-owned `run_client_release_gate.py` wrapper now targets `C:/Users/kiwun/Documents/ai/POKROV-app` by default; it validates the clean-room seed workspace, runs the `POKROV-app` test lane, and produces `POKROV-app` Android or Windows engineering artifacts
- raw Android wrapper artifacts are produced under `C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/build/app/outputs/...`; their presence alone does not prove production signing or publication readiness
- local Android builds may fall back to the debug keystore when the production release keystore is unavailable; that is valid for local smoke only, not for publication
- production Android signing still requires the local `android/key.properties` path or equivalent secret injection outside git
- raw Windows wrapper outputs are produced under `C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/build/windows/x64/runner/Release/...`
- the wrapper-driven Windows setup EXE, portable ZIP, and manifest are produced under `C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/build/release_bundle/`
- after the final green rerun, store the active client-lane bundle under `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/<version>/`, write the matching `release-handoff.json` plus any compatibility `release-links.env` there, and clean raw `build/` and `dist/` outputs as disposable local artifacts
- Android validation evidence hygiene is stricter: retain formal evidence in `ops-local/android-localhost-audit*.json` and in any intentionally promoted records under `docs/audit-artifacts/`
- repo-local Android screenshots, UI XML dumps, logcat captures, and ad hoc runtime snapshots created during one validation pass are disposable scratch unless they are intentionally promoted into `docs/audit-artifacts/`
- machine-local Android tooling noise such as `C:\Windows\adb.exe`, `%TEMP%`, SDK install directories, and `~/.android` is outside repo cleanup scope and must not be treated as repo evidence or repo cleanup targets
- the repo-local MSIX smoke path is intentionally unsigned by default through `sign_msix: false`; signing still belongs to the release handoff
- public Windows and Android labels, Windows package identity, executable naming, installer names, and protocol activation must read as `POKROV` / `pokrov`
- explicit legacy compatibility handlers such as hidden Android import continuity may remain only where separately documented and not as the Windows packaged identity truth
- retained bridge bundle notes belong in the mirrored archive README under `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/<version>/`

Current brand-source rule for release assets:

- start raster regeneration from [external/logogo.png](C:/Users/kiwun/Documents/ai/VPN/external/logogo.png)
- start vector regeneration from [logo/logoclear.svg](C:/Users/kiwun/Documents/ai/VPN/logo/logoclear.svg) and [logo/logowithtext.svg](C:/Users/kiwun/Documents/ai/VPN/logo/logowithtext.svg)
- do not ship stale derived launcher, splash, tray, favicon, or share-preview assets after those masters change

## Current Unclosed Release Blockers

As of `2026-05-15`, the outside-store Android + Windows public beta has a retained `GO` evidence pack. The documented green beta snapshot is not the same thing as a stable, store, trusted-signing, RU-origin, or raw-device release handoff.

Still required before a stronger public promotion, new exact release candidate, store/trusted release, or node enablement that depends on new node state:

- live deploy of the released backend and static surfaces
- live node enablement where the rollout depends on new node state
- separate `current-origin check`, `brain-origin check`, and `RU-origin check` evidence lines
- Android production signing instead of debug-keystore fallback
- confirmation that the final signed Android artifacts are actually production-ready
- raw physical-device `python scripts/android_localhost_audit.py` on the release-installed Android build if replacing the current beta owner attestation or making stronger Android claims
- live Windows and Android scenario evidence on real devices and in a real network after the current UI pass
- live transactional sender readiness for public email registration or recovery mail must stay green; as of `2026-05-15`, a real verify-email delivery and public email registration flow were confirmed for beta, but reset and paid-key delivery should still be checked before broad launch language
- final release handoff with published URLs, runtime sync, and redeployed static download surfaces for any new artifact or URL change

Release handoff shortcuts:

- Android signing: [android-production-signing-handoff.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/android-production-signing-handoff.md)
- Android physical-device audit: [android-physical-device-audit-handoff.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/android-physical-device-audit-handoff.md)
- email sender and webhook: [email-delivery-webhook-handoff.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/email-delivery-webhook-handoff.md)
- release URL sync: [release-links-and-final-handoff.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/release-links-and-final-handoff.md)
- RU-origin evidence: [ru-origin-probe-handoff.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/ru-origin-probe-handoff.md)

## Release Rule

For release-oriented work, default completion includes:

- code or config change
- tests or smoke checks
- push
- deploy

If deploy is blocked, record:

- what changed
- what was verified
- what remains blocked
- rollback-safe state

## Paid Beta Deploy And Rollback Checklist

Before any paid beta deploy, capture:

- local platform branch, local HEAD, `origin/master` HEAD, and whether the branch is behind the promoted platform line
- if a client artifact or handoff is part of the deploy, local client branch, local HEAD, `origin/main` HEAD, and the exact `POKROV-app` release metadata path
- exact dirty patch state for any local dirty beta candidate, including generated report path and changed-file list
- selected gate scope: full or quick, client platform build gates included or not included, Android physical audit included or blocked, and payment callback suite status
- production database backup proof before migrations or data-shaping changes, plus the restore or rollback confidence level
- deployed version or commit before change, new version or commit after change, static artifact identifiers, and release-handoff file or env source if used
- emergency switch evidence for checkout disable, trial disable, download disable, Telegram bonus pause, payment webhook fulfillment pause, and manual access extension/revoke
- current deployed runtime state for `portal-api`, `portal-bot`, `portal-helpbot`, `portal-feedbackbot`, `caddy`, `x-ui`, metrics timers, and observer timers when they are in scope

Rollback is acceptable only when the handoff states:

- backend rollback command or previous deployed commit/package path
- static rollback source, including the preserved static backup directory when static surfaces changed
- release-handoff rollback source for `APP_*` download URLs when artifact links changed
- node rollout rollback path, including `remote_apply_node_qdisc.py disable` and `remote_apply_node_qdisc.py rollback` when qdisc was touched
- transport rollback path, including restoring `defaults.transport_profile=legacy_reality_fallback` and leaving dormant node catalog metadata intact
- database rollback position, restore source, or explicit no-migration/no-DB-change statement
- verification commands to rerun after rollback from `current-origin`, `brain-origin`, and RU-origin where access allows

If any live check is blocked by access, label it as `BLOCKED_BY_ACCESS` instead of implying a pass. If a check is intentionally skipped because it is outside the selected gate scope, label it as `NOT_REQUESTED` or `SKIPPED` and explain why it is still required before public or paid-beta signoff.

## Current Deploy Contour

The documented full release wrapper can currently chain:

- local gates
- optional `APP_*` runtime handoff sync
- backend deploy to `brain`
- static marketing and webapp deploy
- optional qdisc or observer rollout helpers
- brain-local readiness verification

Current contour rule:

- `scripts/release_orchestrator.py` does not publish Android or Windows binaries, does not create final signed artifacts, and does not by itself close the public release handoff
- `scripts/verify_brain_ready.py` is brain-local verification, not a replacement for separate `current-origin` or `RU-origin` evidence
- transport or node rollout helpers can support enablement, but they do not by themselves prove live node enablement unless the runtime pool and smoke evidence are also updated

Current product release scope:

- full public `v1`: `Android + Windows`
- `iOS` and `macOS`: readiness-only in this wave

## Post-Deploy Checks

At minimum, verify:

- backend health endpoint
- app-first `start-trial`
- support ticket creation
- canonical `connect.pokrov.space` subscription endpoint availability
- legacy `api.pokrov.space` subscription compatibility
- `GET /api/client/apps`
- `GET /api/payments/providers`
- checkout continuation from session or ticket
- Telegram linking / channel bonus path
- API-only lifecycle smoke for bonuses, checkout order creation, callback success, and post-payment dashboard state
- `portal-api`, `portal-bot`, and `portal-helpbot` service status
- `portal-feedbackbot` service status
- `verify_brain_ready.py` should fail the repo-side handoff if any required control-plane unit is inactive, if required listeners on `443` or `8444` are missing, or if the built-in HTTP and subscription probes fail
- marketing and checkout probes should use route/function markers such as `Android + Windows`, `app.pokrov.space`, `checkout-shell`, `ключ доступа`, and canonical URLs, not old hero copy that can change without a deploy failure
- transport rollout verification on the canary node with `scripts/remote_apply_node_qdisc.py show`
- transport front verification with `scripts/remote_transport_front_smoke.py`
- `tc -s qdisc` on the shaped interface
- `scripts/remote_node_qdisc_smoke.py` results for heavy-flow saturation and small-probe latency
- when observer-lite is enabled on any node, `portal-node-observer.timer` freshness on that node plus `/api/admin/metrics/status` and `/api/admin/nodes/health` observer fields
- after any REALITY target rotation, verify the node inbound `dest/serverNames`, the `brain` `nodes.reality_sni` row, and `python scripts/predeploy_node_readiness.py --brain-ip 82.21.114.104` in the same handoff

Release gate rule:

- full `release_gate_check.py` should stay green; by default that means the release `pytest` matrix, admin/auth regression, `client_security_smoke.py`, `python scripts/run_client_release_gate.py test --suite full`, `api_lifecycle_smoke.py`, link checks, marketing/webapp production builds, admin webapp smoke, browser E2E from `webapp/e2e/`, and `ui_visual_smoke.py`
- the release gate report must classify what the run actually proved: `current-origin check`, `brain-origin check`, `RU-origin check`, Android physical audit, runtime app-download smoke, and client platform builds must show `PASS`, `FAIL`, `BLOCKED_BY_ACCESS`, `SKIPPED`, or `NOT_REQUESTED` rather than relying on one global pass/fail line
- `python scripts/run_client_release_gate.py preflight` should be green before trusting any wrapper-driven client gate result; a missing or incomplete `POKROV-app` seed workspace is a release blocker even if other repo-local tests happen to pass
- marketing release readiness also requires `python scripts/check-links.py` and `python scripts/ui_visual_smoke.py` to stay green after every CTA, legal, SEO, or branding change
- `verify_brain_ready.py` should validate both the canonical connect host and the legacy API compatibility path before a release is considered healthy
- the default full backend deploy and verify contour should include `portal-feedbackbot`, not just `portal-api`, `portal-bot`, and `portal-helpbot`
- `client_security_smoke.py` is the static repo-level gate for default local-surface settings, routing preset groundwork, and known localhost control paths; it does not replace the Android release-build port and reachability audit
- set `ANDROID_AUDIT_SERIAL=<device-serial>` when running `release_gate_check.py` if you want the opt-in adb localhost audit folded into the same markdown report
- set `ANDROID_AUDIT_CONNECT_WAIT_SEC` and `ANDROID_AUDIT_DISCONNECT_WAIT_SEC` when the adb localhost audit needs non-default timing in the same report
- set `ANDROID_AUDIT_PACKAGE=space.pokrov.pokrov_android_shell` for the active Android shell unless a release candidate deliberately changes the package id
- when `TELEGRAM_INIT_DATA` is available, retain evidence through `python scripts/runtime_app_download_smoke.py --redact --check-providers --require-release-handoff`
- add `--client-platform-gates windows,android-apk,android-aab` or set `CLIENT_PLATFORM_GATES` when you want the same markdown report to include artifact-producing client builds
- the latest documented `release_orchestrator.py --gates-only` success is a local-only proof and does not replace live deploy, live node enablement, or three-origin network evidence
- Android outside-store beta currently relies on owner attestation; a trusted/stable/store Android release must also include a release-build localhost-listener audit covering proxy, DNS, command-server, and admin/control surfaces before connect, after connect, and after disconnect; green repo/static gates are necessary but not sufficient
- the Android release gate fails if an unauthenticated local SOCKS, HTTP proxy, Clash API, command, or similar admin surface remains reachable
- public client release validation must include routing preset smoke for `Full tunnel` and `All except RU`, plus DNS split and leak checks on Android and Windows
- `Blocked only` remains internal or compatibility-only until geo assets and DNS behavior are complete enough for honest public verification

Current local gate entrypoints:

```powershell
python scripts/release_gate_check.py
python scripts/release_gate_check.py --client-platform-gates windows,android-apk,android-aab
python scripts/release_orchestrator.py --gates-only
```

Notes:

- `release_gate_check.py` is the canonical local report generator for the public-v1 gate set.
- `release_gate_check.py --quick` swaps the default full client Flutter suite for `python scripts/run_client_release_gate.py test --suite portal`.
- on Windows, `release_gate_check.py` injects a repo-local disposable `--basetemp` for its `python -m pytest ...` gates so a broken workstation-level `%TEMP%\\pytest-of-<user>\\pytest-current` symlink does not pollute the release handoff tail.
- `release_orchestrator.py --gates-only` is the one-command wrapper for the same gate pack, but it intentionally exits before release handoff sync, backend deploy, static deploy, and post-deploy verify.
- `release_orchestrator.py --stage backend|static|deploy|verify` is the preferred recovery path when a previous full run timed out after a known completed phase; `deploy` means backend plus static, with gates and verify skipped.
- `release_orchestrator.py` streams child output and emits quiet-step heartbeats; tune `--gate-timeout-sec`, `--backend-timeout-sec`, `--static-timeout-sec`, `--verify-timeout-sec`, or `--step-timeout-sec` when a release lane is expected to exceed the default timeout.
- latest verified local run: `python scripts/release_orchestrator.py --gates-only` exited `0` on `2026-04-13`; see `docs/audit-artifacts/release_gate_report.md` for the current local gate snapshot
- pass `--brain-ip 82.21.114.104` to either command when you also want `predeploy_node_readiness.py` folded into the same run.
- `--release-metadata-file` and `--release-env-file` cannot be combined with `--gates-only`; use the full `release_orchestrator.py` flow when you need runtime `APP_*` download URLs synced onto brain before deploy or verify.
- the full `release_orchestrator.py` flow uses the same default backend restart set as `remote_deploy_brain_portal_code.py`, including `portal-feedbackbot`
- `--brain-ip` is required for the full remote contour, including release handoff sync, backend deploy, post-deploy verify, observer-timer ensure, metrics-timer ensure, and qdisc rollout lanes
- without `ANDROID_AUDIT_SERIAL`, a green gate report does not replace the required on-device Android localhost audit
- emulator-backed adb audits are preflight only and do not clear public Android release
- when node reachability is part of a release handoff, report `current-origin`, `brain-origin`, and `RU-origin` results separately instead of collapsing them into one verdict

## Telegram OAuth / OIDC Runtime

`POKROV` now supports Telegram OAuth / OIDC for web login.

Runtime env on `brain` must include:

- `TELEGRAM_OAUTH_CLIENT_ID`
- `TELEGRAM_OAUTH_CLIENT_SECRET`
- `TELEGRAM_OAUTH_REDIRECT_URI`

Current canonical redirect URI:

- `https://app.pokrov.space/`

Current trusted origins in `BotFather` should include:

- `https://pokrov.space/`
- `https://app.pokrov.space/`

Current official public surfaces:

- marketing and public site: `https://pokrov.space/`
- user cabinet and web login: `https://app.pokrov.space/`
- public API host: `https://api.pokrov.space/`

Hostname role policy:

- `pokrov.space` is the canonical public hostname family
- `kiwunaka.space` remains compatibility-only for migration and older subscriptions
- support, onboarding, release notes, and new links must always prefer `pokrov.space`

Web runtime rule:

- `https://api.pokrov.space/` is the canonical API base for browser flows
- `app.pokrov.space` may host the UI, but it must not be treated as an API origin when it returns HTML

Migration-only legacy note:

- `kiwunaka.space` hosts remain compatibility surfaces for older subscriptions during cutover
- do not use `kiwunaka.space` in new release copy, onboarding copy, or fresh distribution links

Monitoring note:

- the external RU probe runbook, hostname migration visibility, and device/session visibility rules live in [Monitoring And Visibility](C:/Users/kiwun/Documents/ai/VPN/docs/operations/monitoring-and-visibility.md)

Safe deploy note:

- use local env injection for the client secret
- do not write raw OAuth secrets into docs, commits, or terminal summaries

## Retained Bridge Bundle Archive

Retained archive home:

- `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/`

Development-truth note:

- this section describes retained bridge evidence only
- new client development truth is `POKROV-app/main`
- retired bootstrap provenance now lives in `docs/archive/client-lanes/app-next-bootstrap-summary.md`

Important outputs:

- versioned bridge bundle mirrors and checksums under `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/<version>/`
- release metadata preserved with that same versioned bundle when rollback-safe evidence matters

Do not delete release artifacts if they are still being distributed or verified.

Related guide:

- [Publishing And Signing Guide](C:/Users/kiwun/Documents/ai/VPN/docs/operations/publishing-and-signing-guide.md)

## Active Client Release Path

Default release slug in this repo:

- `pokrov`

Default artifact names:

- `pokrov-android-universal.apk`
- `pokrov-android-market.aab`
- `pokrov-windows-setup-x64.exe`
- `pokrov-windows-setup-x64.msix`
- `pokrov-windows-portable-x64.zip`

Current public download surfaces expose only:

- Android `Play` / `APK` / mirror URL
- Windows `EXE` / mirror URL
- install/docs fallback via `APP_DOCS_URL`

Treat `AAB`, `MSIX`, and portable `ZIP` as release/store/operator artifacts unless a later runtime payload and public surface explicitly expose them.

Canonical local client verification commands:

```powershell
python scripts/run_client_release_gate.py preflight
python scripts/run_client_release_gate.py test --suite portal
python scripts/run_client_release_gate.py test --suite full
python scripts/run_client_release_gate.py build --target windows
python scripts/run_client_release_gate.py build --target android-apk
python scripts/run_client_release_gate.py build --target android-aab
```

Client verification notes:

- `run_client_release_gate.py` is the canonical root-level wrapper for the platform-owned client gate lane and targets `C:/Users/kiwun/Documents/ai/POKROV-app` automatically.
- `python scripts/run_client_release_gate.py preflight` is the fastest repo-local proof that the `POKROV-app` seed workspace, host shells, and wrapper scripts are present before client gates run.
- `python scripts/run_client_release_gate.py test --suite full` delegates to `C:/Users/kiwun/Documents/ai/POKROV-app/scripts/run-tests.ps1`, while `--suite portal` runs the narrower Flutter lane in `packages/app_shell`, `apps/android_shell`, and `apps/windows_shell`.
- `python scripts/run_client_release_gate.py build --target windows` delegates to `C:/Users/kiwun/Documents/ai/POKROV-app/scripts/build-windows-release.ps1 -SyncRuntime -SkipTests -SkipAnalyze` and expects the unsigned setup EXE, portable ZIP, and manifest under `apps/windows_shell/build/release_bundle/`.
- `python scripts/run_client_release_gate.py build --target android-apk` and `--target android-aab` now build the `POKROV-app` Android shell and verify the raw outputs under `apps/android_shell/build/app/outputs/...`; they no longer refresh any retired bridge working-set paths.
- after those commands succeed, write the active client-lane bundle into `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/<version>/`, keep the client-owned `release-handoff.json` beside it, and only then hand alpha/beta builds to testers.
- if `preflight` fails, inspect the `POKROV-app` seed workspace first; that fix belongs in the canonical client repo instead of as an ad hoc root-repo override.
- any direct commands against retired bridge material are archive or rollback exceptions only; the wrapper commands above are the release-workflow truth documented for operators and CI.

Signed release path:

- Android signing requires `ANDROID_SIGNING_KEY`, `ANDROID_SIGNING_STORE_PASSWORD`, `ANDROID_SIGNING_KEY_PASSWORD`, `ANDROID_SIGNING_KEY_ALIAS`
- Windows signing requires `WINDOWS_SIGNING_KEY`, `WINDOWS_SIGNING_PASSWORD`
- without those secrets, local builds are valid only as unsigned smoke artifacts
- current `POKROV-app` Android shell package and namespace are `space.pokrov.pokrov_android_shell`; set `ANDROID_AUDIT_PACKAGE` to that value unless a release candidate intentionally changes package identity

Android release-block rule:

- do not publish Android as a trusted, store, stable, or raw-audited release until the release-build audit proves that localhost proxy, local DNS, libbox command, Clash API, and equivalent control surfaces are either unavailable to other apps or protected to an acceptable standard
- if that proof is missing, keep Android limited to the documented outside-store beta/owner-attested posture even if the app otherwise builds and signs correctly

Release handoff after publishing artifacts:

```powershell
pwsh external/client-fork/scripts/release_handoff.ps1 `
  -AndroidApkUrl "https://github.com/<org>/<repo>/releases/download/<tag>/pokrov-android-universal.apk" `
  -WindowsExeUrl "https://github.com/<org>/<repo>/releases/download/<tag>/pokrov-windows-setup-x64.exe" `
  -OutEnvPath "C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/<version>/release-links.env" `
  -ManifestDir "C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/<version>/release-manifests"
```

```powershell
python external/client-fork/scripts/check_release_urls.py --env-file "C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/<version>/release-links.env"
```

Then copy the resulting URLs into runtime env:

- `APP_ANDROID_PLAY_URL`
- `APP_ANDROID_APK_URL`
- `APP_ANDROID_MIRROR_URL`
- `APP_WINDOWS_EXE_URL`
- `APP_WINDOWS_MIRROR_URL`
- `APP_DOCS_URL`

Preferred automation path:

```powershell
python scripts/remote_brain_apply_release_handoff.py `
  --brain-ip 82.21.114.104 `
  --env-file "C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/<version>/release-links.env"
```

Or as part of the main rollout:

```powershell
python scripts/release_orchestrator.py `
  --brain-ip 82.21.114.104 `
  --release-env-file "C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/<version>/release-links.env"
```

Distribution rule until store URLs are live:

- GitHub release artifacts are the canonical Android and Windows binary source
- runtime app, bot, and authenticated WebApp download surfaces must read from the same release handoff URLs
- the versioned `release-links.env` under `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/...` is the canonical metadata input for that sync
- `remote_brain_apply_release_handoff.py` does not rebuild static exports by itself
- if public Android or Windows URLs changed, rebuild and redeploy static marketing outputs so `NEXT_PUBLIC_APP_*` stays aligned with the same release handoff values

## Existing User Cutover

Release communication for existing users must explicitly say:

- `POKROV` is the official public app line
- Android and Windows should be treated as a fresh install path
- existing `kiwunaka.space` profiles stay temporarily compatible during migration, but they are legacy compatibility hosts rather than current public entrypoints
- users should install the new app, connect successfully, and only then remove the old app

Recommended migration order:

1. publish new Android and Windows artifacts
2. update runtime download URLs from release handoff
3. post migration notice in `@pokrov_vpn`
4. answer support with the same canonical instructions
5. keep old `kiwunaka.space` subscription hosts active until most users rotate to new profiles

Operator message template:

```text
POKROV is now the official app.

If you used the old app, install the new POKROV release as a separate app.
Do not delete the old app first.

1. Install POKROV
2. Open it and activate or import your access
3. Confirm that the new app connects successfully
4. Only after that remove the old app if you want

Old subscription links continue to work temporarily during migration.
If you need help, contact @pokrov_supportbot.
```

## Current Telegram Runtime Alignment

Current operational state:

- active public channel: `@pokrov_vpn`
- `@pokrov_vpnbot` is an administrator in that channel
- `@pokrov_feedbackbot` handles feedback intake for reviews and product suggestions
- production env should keep `PUBLIC_CHANNEL=pokrov_vpn`
- production env should keep `NEWS_CHANNEL_ID=@pokrov_vpn`

Post-deploy checks should also confirm:

- the public review feed loads with masked usernames
- featured review cards on the public homepage use the approved review copy
- download links across app, bot, and authenticated WebApp point to the same current Android and Windows artifacts
- marketing homepage download CTA point to the current built release URL or the install/docs fallback, never directly to `connect.pokrov.space`
- public `Открыть кабинет` CTA on `pokrov.space` points to `https://app.pokrov.space/`
- public pricing CTA enter through `https://pokrov.space/checkout/` with plan context, then continue via personal cabinet or Telegram route
- `robots.txt`, `sitemap.xml`, `manifest.webmanifest`, `favicon.ico`, and `apple-icon.png` return dedicated content instead of homepage HTML
- public homepage and SEO landing pages emit canonical, Open Graph, Twitter, and JSON-LD metadata
- node health findings are reported with explicit `current-origin`, `brain-origin`, and `RU-origin` check labels
