# Client Release-First Wave Design

Date: 2026-04-03
Status: approved for first implementation wave
Scope: `external/client-fork/app/`

## Goal

Ship the first consumer-facing cleanup wave for `POKROV VPN` without introducing a new payment architecture.

This wave must make the app feel coherent for public users on `Android` and `Windows` while preserving the existing app-first backend contracts.

## Product decisions

- Payment continues through the existing backend checkout flow on `https://pay.pokrov.space/checkout/`.
- The client opens checkout in the browser or external application rather than attempting native store billing.
- Telegram remains optional for first use and is only used for linking, bonus claim, recovery, and support continuation.
- Internal `hiddify` package and import names are not part of this wave unless they leak into user-facing UI or release metadata.

## Wave 1 deliverables

### 1. Checkout flow

- Keep plan and renewal actions inside the client UX.
- When the user taps purchase or renewal actions, open the canonical checkout URL with the selected plan in the external browser.
- Keep bot payment as a secondary fallback action, not the primary CTA.
- Align button labels and helper copy with an app-first consumer flow.

### 2. Profile and account clarity

- Turn the profile screen into one coherent account surface.
- Show account, device, plan, remaining traffic, Telegram bonus status, downloads, and advanced entry in a clearer structure.
- Remove legacy or misleading copy, including old bot naming and broken encoding.
- Keep manual subscription links available only as recovery or advanced material.

### 3. Support usability

- Replace the current dead-end in-app composer feel with a useful escalation flow.
- Keep one prominent support action that routes users into Telegram support or email with prepared context.
- Keep diagnostics copy action available.
- Surface current device/account context clearly enough for support continuation.

### 4. Portal wording and branding cleanup

- Normalize visible `POKROV VPN` naming across home, quick connect, profile, support, and subscription screens.
- Remove visible `PORTAL` and old bot references from portal-specific screens and tests.
- Keep Russian as a first-class path, but this wave may first normalize the existing portal copy in the current UI language while removing broken or misleading strings.

### 5. Tests and docs

- Update widget tests for portal screens to match the new user-facing copy and actions.
- Update client docs when the user-facing contract changes, especially around checkout and support behavior.

## Non-goals for this wave

- Native Google Play or Microsoft Store billing.
- Full internal package rename away from `hiddify`.
- Large routing or state-management rewrites outside the portal surface.
- Re-architecting support into a realtime in-app chat system.

## Validation

- Targeted Flutter portal widget tests pass.
- User-facing portal screens reflect `POKROV VPN` consumer copy.
- Checkout actions open canonical external checkout links.
- Telegram link and bonus entrypoints remain visible and correct.
- Support screen no longer implies an in-app chat that does not exist.
