# Performance Budget

Status: active  
Date: 2026-04-26

| Surface | Budget | Gate |
| --- | --- | --- |
| Marketing LCP mobile | <= 2.5s | Lighthouse/WebPageTest when available |
| Marketing CLS | <= 0.1 max | Visual smoke and browser check |
| Marketing initial JS | <= 120 kB first-load target | `npm.cmd run build` output review |
| API health/status | <= 100 ms p95 target | smoke and metrics |
| API session/bootstrap | <= 500 ms p95 target | lifecycle smoke |
| API order create | <= 1500 ms target | provider smoke when available |
| Android cold start | <= 2.5s target | physical release audit |
| Connect to stable state | <= 15s p95 beta | Android/Windows runtime smoke |

Missing production telemetry must be labeled `needs local run` or `blocked by missing access`.

## Current Evidence State

| Surface | State | Note |
| --- | --- | --- |
| Marketing JS budget | needs local run | Prior research found first-load JS under 120 kB, but this branch still needs a fresh build report. |
| Marketing LCP/CLS | needs local run | Requires browser/Lighthouse or equivalent rendered smoke after UI changes. |
| Webapp admin/cabinet build | needs local run | Required after responsive or copy changes. |
| API p95 health/session/order | blocked by missing access | Needs production/staging telemetry or a controlled live smoke. |
| Android cold start/connect | blocked by missing access | Requires physical release-installed build. |
| Windows connect | blocked by missing access | Requires signed or explicitly gated unsigned handoff. |
| RU-origin POKROV/Telegram reachability | blocked by missing access | Requires external RU probe, not local or brain-origin substitution. |

## Acceptance Labels

- `pass`: measured in this branch or attached as fresh evidence.
- `needs local run`: available without secrets but not yet executed.
- `blocked by missing access`: depends on live provider, server, physical device, signing, or external probe access.
- `deferred`: intentionally outside Open Beta v4 scope and not required for launch decision.
