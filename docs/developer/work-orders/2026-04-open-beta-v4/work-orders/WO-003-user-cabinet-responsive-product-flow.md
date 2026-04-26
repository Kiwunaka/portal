# WO-003 User Cabinet Responsive Product Flow

Status: pending research
Owner: W03

## Scope

- `webapp/` user routes.
- Dashboard, subscription, downloads, devices, statistics, support, redeem, checkout continuation.
- Shared copy and runtime app download payloads where needed.

## Acceptance

- Cabinet remains continuation-first and does not become a second landing page.
- Trial, paid, key, redeem, and bonus states are clear.
- Downloads are truthful for Android and Windows gate status.
- Support ticket flow is usable on mobile.

## Verification

```powershell
Push-Location webapp
npm.cmd run build
npm.cmd run test:e2e
Pop-Location
```
