# Worker 8 Visual Audit

Last updated: 2026-04-23

## Purpose

This folder captures editable journey diagrams and a route-and-contract audit for the POKROV migration wave.

The diagrams are based on:

- root canonical docs under `docs/`
- `webapp/README.md`
- actual route files in `marketing/src/app/`
- actual route files in `webapp/src/app/`
- live API decorators in `portal_bot/api.py`
- canonical hosts in `shared/public-urls.json`

## Scope Boundaries

This audit is intentionally limited to route structure, surface ownership, and contract flow.

Out of scope:

- UI review
- UX quality review
- copy review
- visual polish review

## Source Anchors Used

### Public and continuation surfaces

- marketing routes: `/`, `/checkout/`, `/install/`, `/devices/`, `/mobile/`, `/telegram/`, `/tiktok/`, `/youtube/`, `/offer/`, `/privacy/`
- webapp routes: `/`, `/dashboard/`, `/subscription/`, `/subscription/checkout/`, `/redeem/`, `/devices/`, `/dashboard/downloads/`, `/support/`, `/support/thread/`, `/pricing/`
- admin routes: `/admin/dashboard/`, `/admin/users/`, `/admin/bonuses/`, `/admin/referrals/`, `/admin/promos/`, `/admin/nodes/`, `/admin/network/`, `/admin/broadcast/`, `/admin/tickets/`

### Canonical hosts

- `https://pokrov.space/`
- `https://app.pokrov.space/`
- `https://api.pokrov.space/`
- `https://connect.pokrov.space/`
- `https://pay.pokrov.space/checkout/`

### Live API families used in the diagrams

- public catalog and plans: `/api/public/*`
- browser auth: `/api/auth/telegram/*`, `/api/auth/email/*`, `/api/auth/session`
- app-first bootstrap: `/api/client/session/start-trial`, `/api/client/profile/managed`, `/api/client/route-policy`
- commerce: `/api/payments/*`, `/api/access-keys/status/{key}`, `/api/access-keys/redeem`
- cabinet: `/api/dashboard`, `/api/client/apps`, `/api/nodes/status`
- Telegram link and reward: `/api/client/telegram/link`, `/api/channel/subscriber/check`, `/api/bonuses/channel/claim`
- support and feedback: `/api/tickets*`, `/api/reviews`, `/api/feedback`
- admin and operations: `/api/admin/*`

## Audit Summary

### Current state

- The implemented public route map already follows the `marketing -> app/webapp/Telegram continuation` split.
- The implemented consumer flow is not one straight line yet. It includes app-first bootstrap, public checkout, cabinet continuation, Telegram link/reward, browser auth, and compatibility continuation paths at the same time.
- The implemented admin surface is already web-first and broad enough to cover diagnostics, people, access, payments, network, messaging, and support, but the raw route tree still reads more like page inventory than operator task flow.

### Target state expressed by canon

- The preferred consumer path should compress into one calm default: `marketing -> install app -> start trial -> choose route mode -> connect`.
- Commerce should stay key-first: `marketing /checkout/ -> hosted checkout -> redeem in app or webapp -> managed premium refresh`.
- `webapp` should stay continuation-only for session, renewal continuation, redeem, support, downloads, and admin.
- Telegram should stay secondary: link, bonus claim, support fallback, and recovery continuation.
- The operator path should begin in web admin diagnostics, then branch by task into people, access/payments, network, messaging, or feedback.

### Main migration deltas the diagrams make visible

- The route inventory still keeps compatibility branches alive, especially `/pricing/` in `webapp`, Telegram web-login entry, bot handoff, and manual/recovery connect semantics.
- The target docs freeze a more opinionated sequence than the current route tree alone communicates.
- The admin IA already contains the target categories, so the main remaining gap is explanation and consistency rather than missing route families.

## Deliverables

- `super-detailed-user-route-map.md`
- `current-user-journey.md`
- `target-user-journey.md`
- `current-admin-operator-journey.md`
- `target-admin-operator-journey.md`
- `system-summary.mmd`
- `detailed-user-flows/06-master-current-target-supermap.mmd`
- `detailed-user-flows/07-app-bootstrap-route-mode-and-connect.mmd`
- `detailed-user-flows/08-browser-cabinet-checkout-and-redeem.mmd`
- `detailed-user-flows/09-telegram-support-recovery-and-operator.mmd`
- `detailed-user-flows/10-compatibility-manual-recovery-and-legacy-seams.mmd`
- `rendered/user-journey-current-target.png`
- `rendered/admin-journey-current-target.png`
- `rendered/system-summary.png`
- `rendered/system-overview-generated.png`

## Usage Note

Each Markdown diagram is Mermaid-ready and editable in place.

`system-summary.mmd` is a standalone Mermaid source file intended to be reusable for later bitmap rendering.

`super-detailed-user-route-map.md` is the consolidated entrypoint when you need one current+target artifact that also includes the operator lane, compatibility seams, source anchors, and flat branch notes.

The `06-10` Mermaid files under `detailed-user-flows/` are the editable source set behind that consolidated artifact:

- `06`: one master current+target system-of-journeys map
- `07`: app-first bootstrap, route-mode choice, connect, and access states
- `08`: cabinet auth, dashboard, checkout continuation, redeem, and return to active state
- `09`: Telegram bonus, support escalation, operator response, and review moderation touchpoints
- `10`: compatibility-only seams, manual recovery, legacy routes, and return to the primary story

The `rendered/` folder contains the combined current+target PNG exports plus one generated system overview image for stakeholder handoff.
