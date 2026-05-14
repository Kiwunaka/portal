# Post-Release Monitoring

Last updated: 2026-04-26

If a gated beta is announced later, monitor:

- app-first session creation and 5-day trial issuance;
- Telegram +10-day reward claims;
- `/api/client/apps` download availability;
- provider order and callback states;
- support ticket volume and attachment handling;
- node freshness and per-node alerts;
- current-origin, brain-origin, and RU-origin reachability separately.

Do not upgrade to broad public release based on current-origin checks alone.
