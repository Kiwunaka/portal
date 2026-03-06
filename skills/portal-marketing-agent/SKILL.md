---
name: portal-marketing-agent
description: Maintain the shared PORTAL copy catalog and write friendly, sales-focused RU copy for bot, WebApp, and marketing without public technical jargon.
---

# PORTAL Marketing Agent

## Purpose

Use this skill when updating copy for:
- `marketing/`
- `webapp/`
- `portal_bot/`
- `copy/catalog.ru.json`

The shared copy catalog is the master source of truth. Update catalog entries first, then wire UI/bot surfaces to catalog keys.

## Voice

- Language: Russian
- Tone: friendly, premium, calm, trustworthy
- Goal: reduce friction, increase confidence, make next action obvious
- Avoid public technical jargon like `checkout`, `widget`, `fallback`, `tg_id`
- Public copy must not use the word `VPN`

## Workflow

1. Update `copy/catalog.ru.json`
2. Keep strings short-first
3. Prefer benefit framing over feature dumping
4. Keep legal wording plain-language when possible
5. Use DB templates only as an override layer, not as the primary content store

## Required checks

- No public `VPN` wording
- No mojibake or broken Cyrillic
- No exaggerated guarantees
- CTA should be clear in 2-4 words
