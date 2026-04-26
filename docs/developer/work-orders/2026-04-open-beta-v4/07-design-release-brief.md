# Design Release Brief

Status: active  
Date: 2026-04-26

## Direction

POKROV should read as calm, premium, trustworthy, and practical:

- white, mint, and deep green visual system;
- clear hierarchy and restrained motion;
- one-tap connection affordance in client surfaces;
- dense but calm admin views;
- no public transport jargon in first-layer UI.

## Required Design Truth

- Root `DESIGN.md`.
- `shared/design-tokens.json`.
- `shared/design-tokens.schema.json`.
- Client `POKROV-app/DESIGN.md`.
- Client `docs/design/DESIGN.md`.

Generated assets require prompt, source/reference note, final dimensions, and review note before shipping.

## Open Beta Visual Criteria

- Use `POKROV` as the public product line.
- Avoid direct public product descriptions using `VPN`; keep it only in legacy names, compatibility labels, and unavoidable technical identifiers.
- Prefer a practical premium interface over marketing spectacle: calm spacing, clear action hierarchy, and readable operational states.
- Keep the first viewport product-specific: users should immediately understand that this is the POKROV app/cabinet/checkout/support surface.
- Do not ship generated visuals without source prompt, intended use, dimensions, and approval note.

## Required Follow-up Work

| ID | Work | Label |
| --- | --- | --- |
| D-001 | Add root `DESIGN.md` as the repo-wide visual contract. | in scope |
| D-002 | Add `shared/design-tokens.schema.json` and validate token shape. | in scope |
| D-003 | Add client `DESIGN.md` and `docs/design/DESIGN.md`. | in scope |
| D-004 | Audit and fix visible mojibake in marketing/cabinet/admin copy. | deferred to UI copy pass unless touched by release work |
| D-005 | Sync Flutter shell colors from shared tokens instead of hard-coded values. | deferred to client UI refactor |
| D-006 | Produce screenshot matrix for desktop/mobile marketing, cabinet, checkout, admin, Android, and Windows. | blocked by local/browser/device availability |
