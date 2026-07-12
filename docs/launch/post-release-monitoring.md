# Post-Release Monitoring

Last updated: 2026-04-26

If a gated beta is announced later, monitor:

- app-first session creation and 5-day trial issuance;
- new Telegram +5-day reward claims and grandfathered issued +10-day grants;
- `/api/client/apps` download availability;
- provider order and callback states;
- support ticket volume and attachment handling;
- node freshness and per-node alerts;
- current-origin, brain-origin, and RU-origin reachability separately.

Do not upgrade to broad public release based on current-origin checks alone.
