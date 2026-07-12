# Generated Assets Policy

Last updated: 2026-07-12

Document class: CANONICAL

Generated assets are allowed for POKROV only when they are traceable, reviewed, and truthful for the release scope.

## Public Wording Boundary

Visible `VPN` / `ВПН` wording is allowed on dedicated SEO/search-intent
surfaces when it is useful to users and tied to the real POKROV app flow.
Hidden text, cloaking, keyword stuffing, unsupported “best” claims, and
unsupported release, payment, store, signing, device-audit, or RU-origin
claims remain forbidden.

## Required Metadata

Every generated asset intended for public, client, store, social, or support use needs:

- asset path;
- generator or tool;
- prompt or source-reference note;
- source/master asset reference;
- dimensions and export format;
- intended surface;
- reviewer and date;
- release-scope note.

## Blocked Uses

Do not use generated assets that:

- show Android or Windows availability that is not supported by release evidence;
- imply store approval before store metadata and approval gates are green;
- use visible `VPN` / `ВПН` wording outside the scoped boundary above;
- obscure UI state needed to understand checkout, downloads, or support limitations.

## Evidence Location

Store each new repo-side generated-asset evidence packet under:

- `docs/design/generated/<YYYY-MM-DD>-<packet>/`

Keep prompt/reference, source master, derived outputs, review note, and release-scope note together in that packet.

An active WO may link to its packet; never append new evidence to a completed WO.

Keep client release evidence authority in the client repository only where the active client release guide requires it.
