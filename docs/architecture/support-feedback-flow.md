# Support And Feedback Flow

Last updated: 2026-07-08

## Primary Paths

- Cabinet support tickets are the primary structured support path.
- `@pokrov_supportbot` is the official Telegram support fallback.
- `@pokrov_feedbackbot` handles feedback intake and public review moderation.
- `@pokrov_supportbot`, `/api/tickets`, and `/api/tickets/{ticket_id}/messages` may add an immediate AI support hint to text-only user messages when `SUPPORT_AI_ENABLED=true`; the ticket remains open and operators still see the full thread.

## AI Support Helper

- Runtime home: `portal-api` and `portal-helpbot` on `brain`.
- Code: `portal_bot/support_ai_service.py`, `portal_bot/api.py`, and `portal_bot/helpbot.py`.
- Deployable knowledge base: `shared/support-ai-knowledge.json`, uploaded to `/root/shared/support-ai-knowledge.json`.
- Default provider/model route: OpenRouter chat completions at `https://openrouter.ai/api/v1` with `deepseek/deepseek-v4-flash`.
- The helper is disabled by default. Enable it only through server env with `SUPPORT_AI_ENABLED=true` and `SUPPORT_AI_API_KEY` or `OPENROUTER_API_KEY`.
- OpenRouter provider privacy routing is optional. Leave `SUPPORT_AI_OPENROUTER_DATA_COLLECTION` blank for default routing; set it to `deny` or `allow` only when the chosen model route is known to support that policy.
- The helper sends only redacted text and the sanitized support knowledge base to the model; it must not read repo docs, secrets, databases, ticket attachments, raw connection links, QR codes, card details, Telegram init data, or payment payloads.
- AI responses are stored as support ticket messages with sender role `assistant`, so the admin history does not confuse model output with a human operator response.
- WebApp and app surfaces that use the ticket API receive the same `assistant` messages in normal ticket payloads. Current client surfaces that open `@pokrov_supportbot` receive the same helper through the Telegram fallback path.
- Ticket attachments are private backend files, not public static assets. New uploads use `POST /api/tickets/uploads`; downloads use authenticated `GET /api/tickets/attachments/{stored_name}` and require the account owner or admin.
- Telegram support ticket replies in both `@pokrov_supportbot` and the main bot admin queue accept text, photo, document, and video messages; captions are stored as the message body, and attachment metadata is retained on the ticket message.
- User upload MIME policy is intentionally narrow: PNG, JPEG, WebP, PDF, and UTF-8 TXT after magic-byte checks. SVG, HTML, video, and opaque octet-stream uploads are rejected.
- AI ticket messages use safe plaintext mini-formatting only: short labels, line breaks, numbered steps, bullets, inline bold/code markers. The WebApp renders those markers as structured blocks without accepting raw HTML.
- `@pokrov_supportbot` renders AI mini-formatting through escaped Telegram HTML and attaches quick follow-up buttons: `Не получилось`, `Дайте шаги`, `Оператор`, and `Открыть обращение`. Buttons either put the user into the same ticket reply flow or append a safe operator-request message to the ticket.
- Current support knowledge covers the app-first path plus beta manual setup through compatible clients such as `Hiddify`, `Happ`, `v2rayNG`, `v2rayN`, `Streisand`, `NekoBox`, `NekoRay`, `Shadowrocket`, `FoXray`, and `V2Box`; account-specific and unclear cases still escalate to operators.
- `SUPPORT_AI_MAX_CONTEXT_CHARS` defaults to `32000`, so the runtime can send the expanded support KB without loading the entire repository or secret-bearing docs into user requests.
- Pi is an operator-side knowledge curation harness for refreshing `shared/support-ai-knowledge.json`; it is not invoked inside each production user request.

## Pi Knowledge Refresh

Use [pokrov_support_ai_kb_refresh.py](C:/Users/kiwun/Documents/ai/VPN/scripts/pokrov_support_ai_kb_refresh.py) to build a Pi prompt from allowlisted canon docs, run Pi with OpenRouter/DeepSeek, validate the JSON response, and update `shared/support-ai-knowledge.json`.

```powershell
python scripts/pokrov_support_ai_kb_refresh.py inventory
python scripts/pokrov_support_ai_kb_refresh.py prompt --output .tmp/support-ai-kb-prompt.md
python scripts/pokrov_support_ai_kb_refresh.py run-pi --apply
```

Review the diff before deployment. The script intentionally excludes secret and evidence paths.

## Beta Rules

- Do not request private subscription links, QR codes, payment card details, or raw Telegram init data in public chats.
- Attachments are a privacy-hardening area; operators should avoid asking for sensitive screenshots unless required.
- Escalations should label current-origin, brain-origin, and RU-origin evidence separately.
- Do not describe the AI helper as a resolved-ticket path; account, payment, attachment-based, and unclear cases remain manual support.
