# Support And Feedback Flow

Last updated: 2026-05-08

## Primary Paths

- Cabinet support tickets are the primary structured support path.
- `@pokrov_supportbot` is the official Telegram support fallback.
- `@pokrov_feedbackbot` handles feedback intake and public review moderation.

## Beta Rules

- Do not request private subscription links, QR codes, payment card details, or raw Telegram init data in public chats.
- Attachments are protected support material, not public static files. Browser uploads return `/uploads/support/<file>` metadata, but the file route requires an authenticated user and is served only to the ticket owner or an admin after the file is attached to a ticket message.
- Web admin support triage loads a full ticket thread through `/api/admin/tickets/{ticket_id}` before reply/status work, including protected attachment previews and operator reply uploads via authenticated blob fetch.
- Operators should still avoid asking for sensitive screenshots unless required.
- Escalations should label current-origin, brain-origin, and RU-origin evidence separately.
