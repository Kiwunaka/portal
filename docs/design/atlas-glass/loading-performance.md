# POKROV Atlas Glass Loading And Performance

Last updated: 2026-04-28

## Rules

- Full-screen loader is allowed only on true cold start when no useful session state exists.
- Internal cabinet navigation must keep the shell, navigation, and last good in-memory dashboard/user data visible.
- Never show fake progress percentages.
- Use page-shaped skeletons for content areas.
- Store only theme preference in browser storage; dashboard/user data stays in React memory.

## Current Risks

- `CabinetShell` historically replaced the full cabinet when `loading` was true.
- Route transition keyed by pathname can remount too much of the tree if placed above the persistent shell.
- Bottom mobile navigation was Telegram-context-only; Atlas direction needs persistent app-like mobile navigation.
- Entry and admin loaders need to distinguish cold auth/bootstrap from warm refresh.

## Performance Targets

- Route feedback under 150ms.
- LCP under 2.5s.
- INP under 200ms.
- CLS under 0.1.
- Avoid avoidable sequential fetch chains.

## Implementation Guidance

- Keep `fetchAuthSession` as the first auth gate.
- If auth session contains Telegram id, fetch dashboard and profile in parallel.
- If auth session lacks id, keep the existing dashboard -> user fallback unless backend contract changes.
- Track `initializing` and `refreshing` separately.
- Render last-good shell state during refresh and show subtle route/content activity.
