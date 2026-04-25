# Payment Provider Probe

- timestamp_local: `2026-04-26`
- origin: `brain` (`82.21.114.104`)
- command path: `scripts/freekassa_api_probe.py`
- source checked: `site`, `bot`
- method checked: `orders/create`
- result: `BLOCKED_BY_PROVIDER_STATUS`

## Evidence

- Brain SSH access succeeded with key authentication.
- The production API runtime reached the FreeKassa API for both `site` and `bot` sources.
- FreeKassa returned HTTP `401` with provider message `Merchant not activated` for both sources.

## Interpretation

- Checkout code path and server-side provider request wiring are reachable from the control-plane host.
- A live public-beta paid checkout smoke cannot be closed until the FreeKassa merchant is activated in the provider account or an approved active provider is configured.
- No real customer payment was attempted or completed by this probe.
