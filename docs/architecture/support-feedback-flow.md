# Support And Feedback Flow

Last updated: 2026-07-14

## Primary Paths

- Cabinet support tickets are the primary structured support path.
- `@pokrov_supportbot` is the official Telegram support fallback.
- `@pokrov_feedbackbot` handles feedback intake and public review moderation.
- `@pokrov_supportbot`, `/api/tickets`, and `/api/tickets/{ticket_id}/messages` may add an immediate AI support hint to text-only user messages when `SUPPORT_AI_ENABLED=true`; the ticket remains open and operators still see the full thread.

## Canonical Support Ownership

- `support_tickets.account_id` and `support_attachments.owner_account_id` are nullable internal ownership projections. Telegram-shaped ticket, upload, and message sender fields remain compatibility attribution and notification hints; canonical UUIDs are not added to public ticket responses.
- New API, main-bot, and helpbot writes store canonical ownership when exact account evidence resolves to one account. Linked app, email, and Telegram sessions for that account can use the same account-owned ticket and private upload history.
- Authorization is account-first: admin bypass, then exact canonical account match. Exact legacy Telegram ID is accepted only while the corresponding ownership field is `NULL`; a matching legacy ID never overrides a different non-null owner, and read-only checks never claim ownership.
- A user write may claim an eligible `NULL` ticket only when the writer has the exact historical Telegram ID and an unambiguous canonical account. Continuation selects the newest active ticket by `updated_at DESC, id DESC`; it does not delete, close, merge, or move duplicate tickets or messages.
- Startup runs marker-gated `migration.support_account_ownership.v1` after account-foundation. It uses only exact direct-user, explicit linked-Telegram, and enabled Telegram-identity candidates, follows bounded merge chains, and records unresolved/conflicting rows as idempotent metadata-only account merge reviews. The direct backfill remains available for operator repair.
- Account merge moves only the two canonical ownership fields. Legacy attribution, support rows, messages, upload metadata, and files remain intact. Manual/test-user cleanup may remove only still-legacy `NULL`-owned tickets for that exact Telegram ID.
- Delivery is separate from authorization. Operator replies use bounded deterministic routing: an explicit linked Telegram target on the canonical account, then enabled Telegram-identity evidence, then the ticket's historical ID only when it is a real Telegram ID. If no real target exists, delivery is skipped with a metadata-only warning; synthetic app or email IDs are never treated as Telegram chats.

## AI Support Helper

- Runtime home: `portal-api` and `portal-helpbot` on `brain`.
- Code: `portal_bot/support_ai_service.py`, `portal_bot/api.py`, and `portal_bot/helpbot.py`.
- Deployable knowledge base: `shared/support-ai-knowledge.json`, uploaded to `/root/shared/support-ai-knowledge.json`.
- Default provider/model route: OpenRouter chat completions at `https://openrouter.ai/api/v1` with `deepseek/deepseek-v4-flash`.
- The helper is disabled by default. Enable it only through server env with `SUPPORT_AI_ENABLED=true` and `SUPPORT_AI_API_KEY` or `OPENROUTER_API_KEY`.
- OpenRouter provider privacy routing is optional. Leave `SUPPORT_AI_OPENROUTER_DATA_COLLECTION` blank for default routing; set it to `deny` or `allow` only when the chosen model route is known to support that policy.
- The helper sends only sanitized text and the bounded support knowledge base to the model; it must not read repo docs, secrets, databases, ticket attachments, raw connection links, QR codes, card details, Telegram init data, or payment payloads.
- One support sanitizer runs before truncation on both outbound user text and inbound model text. Input and output are bounded to 65,536 characters; NFKC is incremental and fails closed before expansion crosses that bound. Normal work uses at most three percent-decode passes, one non-recursive decoded URL rescan, plus bounded JSON-escape, HTML-entity, zero-width, IDNA separator, fullwidth, quote, and dash normalization. A linear structural probe rejects residual nested percent-encoded URL signatures after that budget instead of decoding them further. Model chunks are sliced before concatenation, and provider bodies are capped at 262,144 streamed bytes before JSON parsing.
- Stable placeholders cover Unicode email, proxy links, structurally classified token-bearing HTTP(S) URLs, `PKR-` recovery codes, `POKROV-` activation keys, hyphenated or compact UUIDs, `pkr_rt_` refresh tokens, signed/JWT-like session tokens, API/private keys, English or Russian labelled credentials, Basic/Bearer authorization, and long digit forms. Telegram init data requires a realistic numeric `auth_date` plus 64-hex `hash`; `query_id`, `user`, and `signature` are optional. A recognized labelled or raw blob is replaced through the end of its line even when a top-level pipe or HTML-escaped separator precedes optional fields. Empty/placeholder prose is preserved.
- After normalization and whole-line Telegram handling, one bounded scanner emits alternating non-URL and URL spans. Generic redaction runs only on non-URL spans; safe URLs are emitted directly and private URLs are replaced directly, without shield markers. Authority is validated before host trust on every supported decode layer; malformed ports, encoded delimiters, quote/space userinfo confusion, and residual deeper encoding fail closed. Userinfo, canonical sensitive query/fragment keys, semicolon or quoted nested assignments, keyless session tokens, nested proxy/subscription URLs, POKROV endpoint tokens, and `/sub/` or `/subscription/` token segments are private. Only exact known public-reference hosts (`github.com`, `pokrov.space`, `www.pokrov.space`, `docs.pokrov.space`, and `status.pokrov.space`) are trusted; leading/trailing dots and arbitrary `docs.*`/`status.*` hosts are not. Genuine GitHub commit and public docs references remain readable, while ticket UUID URLs remain private.
- Only sanitized model output can be returned and stored as a support ticket message with sender role `assistant`, so the admin history does not confuse model output with a human operator response or retain model-echoed credentials.
- Provider HTTP, oversized-body, and request failures log only a bounded status and fixed error code. Provider bodies and exception detail are neither logged nor used as ticket text because they may echo user input. API/helpbot persistence and rollback failures expose only `support_reply_persist_error`; cleanup failure exposes only `support_reply_cleanup_error`; and the SQLAlchemy engine hides statement parameters in rendered exceptions.
- WebApp and app surfaces that use the ticket API receive the same `assistant` messages in normal ticket payloads. Current client surfaces that open `@pokrov_supportbot` receive the same helper through the Telegram fallback path.
- Ticket attachments are private backend files, not public static assets. New uploads use `POST /api/tickets/uploads`; downloads use authenticated `GET /api/tickets/attachments/{stored_name}` and require the account owner or admin.
- Recovery sessions have a narrower text-only support projection: upload, attachment download, and standalone `/api/client/support/assistant` return `403 recovery_scope_forbidden`; nonempty media fields on ticket create/message are rejected; all recovery ticket responses omit historical and new message media metadata. Normal client and admin attachment behavior remains unchanged.
- Normal sessions retain standalone assistant `safeDiagnostics` compatibility. The active Android/Windows adapter currently always sends app diagnostics and uses the standalone assistant path, so this platform slice is not promotable for recovery UX until a separate recovery-aware client slice omits diagnostics/media and uses ticket text endpoints instead. That client repository is outside this task.
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
