# Огонь VPN 0.84 — safe static domain inventory

Source: locally installed Google Play APK, package `com.ogonconnect.app`, base APK SHA-256 `0BE4CEAECA9A46C13FE591E48ADA070117E1AA135D1BEB5FE19A5A595FBDC396`.

Only URL schemes and hostnames are retained. Paths, query strings, credentials, VPN endpoints and response data are intentionally excluded. No listed host was probed.

## First-party/public hosts

- `api.ogonvpn.com`
- `ogonvpn.xyz`
- `t.me`

## Connectivity-check hosts found in `ConnectivityChecker`

- `captive.apple.com`
- `www.google.com`
- `ya.ru`

## Telemetry SDK hosts

- `bugsnag.com`
- `notify.bugsnag.com`
- `notify.bugsnag.smartbear.com`
- `otlp.bugsnag.com`
- `sessions.bugsnag.com`
- `sessions.bugsnag.smartbear.com`

## DNS-related hosts present in the package

- `dns.adguard-dns.com`
- `dns.google`
- `dns.quad9.net`

Presence alone does not prove that these are user-selectable or active in the captured configuration.

## Randomized `.xyz` host set

The package contains 62 randomized-looking `.xyz` hosts in the same DEX that contains the app's network layer:

- `axyno.xyz`
- `beherb.xyz`
- `corivex.xyz`
- `dorhex.xyz`
- `dudeforum.xyz`
- `feherb.xyz`
- `forhex.xyz`
- `gebrix.xyz`
- `gebron.xyz`
- `geharo.xyz`
- `gehira.xyz`
- `gehler.xyz`
- `gehlex.xyz`
- `gehlin.xyz`
- `gehmix.xyz`
- `gehory.xyz`
- `gehper.xyz`
- `gehrex.xyz`
- `gehura.xyz`
- `gehvox.xyz`
- `gehzar.xyz`
- `gehzen.xyz`
- `gehzor.xyz`
- `gexerb.xyz`
- `herbly.xyz`
- `herelo.xyz`
- `heremo.xyz`
- `herevo.xyz`
- `herexa.xyz`
- `herzan.xyz`
- `herzin.xyz`
- `herzon.xyz`
- `hyper0.xyz`
- `kerlix.xyz`
- `lerbix.xyz`
- `lohex.xyz`
- `luxerno.xyz`
- `nerbix.xyz`
- `nexvora.xyz`
- `nilvora.xyz`
- `norhex.xyz`
- `orinexa.xyz`
- `qevon.xyz`
- `qirevo.xyz`
- `qiventa.xyz`
- `quivano.xyz`
- `rohex.xyz`
- `ruxelo.xyz`
- `serbix.xyz`
- `sohex.xyz`
- `upherb.xyz`
- `venzora.xyz`
- `verbix.xyz`
- `verlix.xyz`
- `vorhex.xyz`
- `xerbit.xyz`
- `xerivon.xyz`
- `xyherb.xyz`
- `zavento.xyz`
- `zerivox.xyz`
- `zerlix.xyz`
- `zylor.xyz`

The code contains a `HostDiscoveryManager`, cached alive/dead/sticky-host state, batch and emergency scans, latency ranking, and a `SmartFallbackExecutor` that rewrites API requests to a selected host. Taken together, this strongly indicates an anti-blocking fallback pool, but the exact runtime ordering and whether every packaged hostname is active were not proven and are not inferred as fact.
