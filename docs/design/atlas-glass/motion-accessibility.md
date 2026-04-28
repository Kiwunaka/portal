# POKROV Atlas Glass Motion And Accessibility

Last updated: 2026-04-28

## Motion Tokens

- Fast: 160ms for tap, button hover, nav hover.
- Standard: 220ms for route/page/card enter and hover.
- Slow: 320ms maximum for dialogs, drawers, and large panels.
- Skeleton shimmer: 1200-1600ms, disabled under reduced motion.
- Easing: `cubic-bezier(0.22, 1, 0.36, 1)`.

## Patterns

- Route/page: fade plus `translateY(6-8px)`; optional scale `0.996`; standard duration.
- Cards: consumer hover may lift by 1px; admin should be static or near-static.
- Nav: background/color transition, active indicator 180-220ms.
- Drawers/dialogs: opacity plus small translate, focus trap, Escape close, return focus.
- Admin tables: no cascades, parallax, shimmer, animated reordering, or large scroll-tied motion.

## Reduced Motion

- Framer Motion must use `useReducedMotion()` or equivalent.
- CSS reduced motion disables animations and uses near-zero transitions.
- Marketing hover/reveal effects must respect reduced motion.
- Skeletons become static blocks.

## Accessibility Checklist

- Every interactive control needs visible `:focus-visible`.
- Icon-only buttons require `aria-label`.
- Loading regions use `aria-busy` and `aria-live=\"polite\"`.
- Success/error messages use `role=\"status\"` or `role=\"alert\"`.
- Clickable table rows must be keyboard reachable, or action buttons/links must live inside cells.
- Theme controls keep pressed/selected state accessible.
