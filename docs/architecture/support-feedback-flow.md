# Support And Feedback Flow

Last updated: 2026-09-09

## Primary Paths

- Cabinet support tickets are the primary structured support path.
- `@pokrov_supportbot` is the official Telegram support fallback.
- `@pokrov_feedbackbot` handles feedback intake and public review moderation.
- `@pokrov_supportbot`, `/api/tickets`, and `/api/tickets/{ticket_id}/messages` may add an immediate AI support hint to user messages when `SUPPORT_AI_ENABLED=true`; the ticket remains open and operators still see the full thread.

## Canonical Support Ownership

- `support_tickets.account_id` and `support_attachments.owner_account_id` are nullable internal ownership projections. Telegram-shaped ticket, upload, and message sender fields remain compatibility attribution and notification hints; canonical UUIDs are not added to public ticket responses.
- New API, main-bot, and helpbot writes store canonical ownership when exact account evidence resolves to one account. Linked app, email, and Telegram sessions for that account can use the same account-owned ticket and private upload history.
- Authorization is account-first: admin bypass, then exact canonical account match. Exact legacy Telegram ID is accepted only while the corresponding ownership field is `NULL`; a matching legacy ID never overrides a different non-null owner, and read-only checks never claim ownership.
- A user write may claim an eligible `NULL` ticket only when the writer has the exact historical Telegram ID and an unambiguous canonical account. Continuation selects the newest active ticket by `updated_at DESC, id DESC`; it does not delete, close, merge, or move duplicate tickets or messages.
- Startup runs marker-gated `migration.support_account_ownership.v1` after account-foundation. It uses only exact direct-user, explicit linked-Telegram, and enabled Telegram-identity candidates, follows bounded merge chains, and records unresolved/conflicting rows as idempotent metadata-only account merge reviews. The direct backfill remains available for operator repair.
- Account merge moves only the two canonical ownership fields. Legacy attribution, support rows, messages, upload metadata, and files remain intact. Manual/test-user cleanup may remove only still-legacy `NULL`-owned tickets for that exact Telegram ID.
- Delivery is separate from authorization. Operator replies use bounded deterministic routing: an explicit linked Telegram target on the canonical account, then enabled Telegram-identity evidence, then the ticket's historical ID only when it is a real Telegram ID. If no real target exists, delivery is skipped with a metadata-only warning; synthetic app or email IDs are never treated as Telegram chats.

## Operator Support Work Boundary

- `SupportTicket` remains the only ticket root. Release 1.2 adds server-owned
  environment, priority, queue, assignment/team, waiting-on, SLA, escalation,
  incident/attempt links and optimistic `version` fields through rerunnable
  additive migrations; legacy rows are backfilled without replacing messages
  or attribution.
- `/api/admin/v2/support/tickets` owns queue ordering and filters. Claim,
  assignment and workflow updates use workspace Action Intents; compatible
  reply/status/internal-note routes use the same intent registry, idempotency
  and expected-version collision check.
- Internal notes are `visibility=internal`. Operator detail may request them;
  `tickets_repo.list_ticket_messages` excludes them by default, so API, main
  bot and helpbot user reads cannot expose operator-only text.
- User 360 always returns the safe account/ticket/observer projection. Opaque
  installation, session and attempt references plus bounded diagnostic
  fingerprints are read only when the operator has `support.sensitive.read`.
  Without it the service does not query Event rows and returns explicit
  `field_access=redacted`, not a false empty-data claim. It never returns
  arbitrary `meta_json`, raw device/install/session/trace values, IP, URL,
  config, key or token material.
- Correlated attempt search requires `support.sensitive.read`. Support-bundle
  summaries retain existing TTL, retention and access-audit limits; observer
  state is a read-only trusted signal. Neither projection changes ticket,
  account, entitlement or encrypted-bundle authority.
- The case summary uses the explicitly linked attempt. If that attempt is
  absent from the available data, the view states that it is missing; other
  user attempts remain available for an explicit link action. With no link,
  the latest user attempt is labelled as unlinked. Its displayed build comes
  from its own latest event, not from another support bundle.
- Known-issue lookup follows the bundle's error code, app version, build and
  platform together. A changed scope clears the previous result and triggers
  a fresh lookup, even when the error code is unchanged. This projection does
  not establish an effective runtime profile or current protection proof.

### Temporary support mode and short code

- The ordinary diagnostics screen always generates a local `PSD1-*` short code
  that summarizes only platform, route/connection class, app/build, issue and
  expiry date, plus a 16-bit diagnostic hash prefix. Copying or decoding it
  uploads no file and reveals no account, device, installation, package,
  destination or configuration identity.
- L2 may issue `support.mode.issue` only for an existing case through the v2
  Action Intent lifecycle. The one-time `PSM1-*` activation code is not stored
  in plaintext. Redemption is owner-bound, exact-build, expiring and one-time;
  mismatched audience cannot consume the code.
- The client independently verifies the Ed25519 signature, exact audience,
  schema, nonce, issuance time and expiry, then shows categories, TTL and caps
  and requires explicit user confirmation. A persistent indicator remains
  visible until manual or automatic disable.
- Support mode permits only the signed category/collector pairs. It cannot run
  commands, mutate VPN/routes/DNS, read user files, capture packets or
  destinations, disclose credentials/configuration, hide itself or extend its
  TTL. It expires within 30 minutes and enforces at most two bundles plus the
  signed per-bundle and cumulative byte ceilings.
- Both direct upload and manual Android/Windows export still use the same exact
  preview/redaction pipeline and a verified recipient key. The only host file
  is the encrypted `.pokrov-support` envelope; cancellation or failure must not
  create or claim a plaintext artifact.

## AI Support Helper

- Runtime home: `portal-api` and `portal-helpbot` on `brain`.
- Runtime facade and legacy helper: `portal_bot/support_agent_service.py` and `portal_bot/support_ai_service.py`; bounded harness: `portal_bot/support_agent_harness.py`; bounded OpenAI-compatible adapter: `portal_bot/support_agent_provider.py`.
- Deployable allowlisted assets are `shared/support-agent-policy.json` and `shared/support-ai-knowledge.json`, uploaded under `/root/shared/`.
- The selected support profile is `deepseek-v4.1-flash` with high reasoning, sent as `deepseek/deepseek-v4.1-flash` through the exact OpenRouter base. Text synthesis and isolated attachment analysis use the same model. Its endpoint requires `json_object` and `data_collection=allow`; local closed-schema and safety validation remains mandatory. The owner selected this route after the model-matrix disclosure on 2026-09-10. The older 0731 and Vision Exp profiles remain available with medium reasoning for rollback; Vision Exp retains Fireworks preference and collection denied. Other profiles fail closed. Credentials stay in the server environment.
- No support request sends `max_tokens` or another completion-token cap; `SUPPORT_AI_MAX_OUTPUT_TOKENS` has been removed. Private reasoning is excluded from returned content. Provider timeout (45 seconds), total deadline (50 seconds), streamed-body and safety limits remain. Validated replies may contain up to 12,000 characters; Telegram sends them in ordered chunks with follow-up buttons on the last chunk. Persistent ticket history retains the complete answer; short process memory retains the first 1,200 characters.
- The feature is disabled by default. `SUPPORT_AI_ENABLED=false` always selects deterministic local fallback. With it enabled, `SUPPORT_AI_AGENT_ENABLED=false` selects the legacy one-call helper and `SUPPORT_AI_AGENT_ENABLED=true` selects the bounded harness. The legacy and harness paths never run together.
- Before any provider call, code retrieves at most three topics from the validated public-support KB. `confident` routing requires both an active high-precision intent rule and the expected topic-body fingerprint; all other supported retrieval is only candidate context. Ten narrow `confident` topics have an additional direct-render allowlist: for a new session, their fingerprint-bound user-facing body is returned by code with zero provider requests. WARP, location choice, both route modes, notifications, trial limitations, Telegram bonus, and payment-not-applied questions also have fingerprint-bound confident routing so the provider can give concrete public diagnostics and a provider failure can still return those safe steps before human handoff. For a bounded follow-up with no explicit new intent, the established active session issue is pinned as the first candidate source without upgrading confidence; an explicit new intent replaces it. Model-visible topic copy names official surfaces without embedding literal domains or URLs that the output contract forbids.
- Candidate answers retain context provenance but no grounding claim and therefore receive only generic public actions. Confident answers may use the single code-owned grounding topic to select existing topic-specific actions; model text never selects actions, source labels, or escalation metadata.
- When synthesis is needed, DeepSeek receives exactly two messages: one cache-stable system prefix containing policy and bundle fingerprints, and one volatile user JSON envelope containing only the selected topic bodies, bounded session state, and current question. The global KB index is never sent. The model may return only `schema_version`, `status`, and `reply`; retrieval, provenance, state, actions, and escalation remain code-owned.
- Provider output must be either the bare JSON object or one JSON object inside a single `json`/plain Markdown fence with no surrounding prose or nested fence. Code unwraps only that exact transport artifact, then applies the same duplicate-key, closed-schema, semantic-action, redaction, and output-safety validation; every other wrapper still fails closed.
- A text-only eligible message makes at most one OpenAI-compatible Chat Completions request. Authorized ticket attachments may add one isolated Vision analysis per file (two files maximum) before the final synthesis; all calls and reported usage are counted in the same run. The harness has no provider retry, model-visible tool, tool continuation or model-directed command execution.
- Main synthesis context may contain only the validated operating policy, bounded retrieved public-support topics, redacted process-local session state, the redacted user question, and an allowlisted scalar snapshot for the authenticated account. The endpoint, not the model, reads that snapshot. The ticket case path additionally admits the bounded evidence described below; its isolated Vision stage receives authorized attachment images. Main synthesis has no arbitrary database/API access, raw attachment, key/config, QR, Telegram init data, payment payload, shell, network-tool, arbitrary-file, command-execution, or cross-account access. Read-only account questions use only those supplied scalars; unresolved anomalies still require an operator.
- Client `safeDiagnostics` is admitted through a fixed allowlist. The authenticated endpoint then overrides any colliding account keys with server-owned access, days-left, normalized plan, active-device count, Telegram-link/bonus state, bounded panel-runtime facts, and the currently applicable public promo-code snapshot. The client may supply only its user-visible active-connection flag and location label for the current device. Raw identifiers, usernames, email, node hosts/IPs, URLs, configs, and panel payloads are excluded. These values may enter only the current request and are never retained in process-local agent memory or value-bearing logs.
- Questions about the current node/location and available public promo codes are rendered by code before retrieval or provider synthesis. The former uses only the current client's active flag and public location label; the latter uses only server-owned campaigns eligible for the authenticated account. Neither path exposes topology, provider records, payment data, or another account, and both make zero provider requests.
- Harness continuity is owner- and surface-scoped, process-local RAM only: 60-minute TTL, at most six safe messages per session, 256 sessions, and six requests per authenticated owner per rolling minute. Attempted-step codes remain code-owned session state. A newly reported completed step with no outcome and a first clean negative outcome are acknowledged by fixed code-owned copy, persisted, and returned with zero provider requests. A negative outcome after support was already contacted, or the second negative outcome for one established issue, causes sticky human transfer. Other follow-ups may use synthesis, whose policy requires DeepSeek not to repeat attempted steps. The runtime allows at most two concurrent runs.
- A resolution-only follow-up such as `всё решено` is acknowledged by code with zero provider requests; mixed messages such as `заработало, но...` continue through normal retrieval. This prevents promotions or unrelated troubleshooting after success and reduces token use in completed sessions.
- Model `status=escalate` offers human transfer for that turn but does not permanently disable the assistant for an unrelated later question. Explicit human requests and the established repeated-failure rules remain sticky. On provider, parse, or output-safety failure, code may render a local KB answer only when routing is confident and its fingerprint still matches; candidate, missing-source, unresolved account/payment anomalies, rate, concurrency, and other insufficient-evidence paths offer transfer instead of guessing. Model answers and grounded local answers pass the same semantic action validator. For an otherwise safe answer, code replaces the complete `Если не поможет` tail with the fixed `Напишите в поддержку.` footer before semantic action validation. Output validation still rejects unsafe raw text plus full URLs, scheme-less domains, delete/reset/logout/reinstall steps, credential lifecycle claims, unqualified full-tunnel claims, automatic-profile claims, false transfer or future-action claims outside that replaced footer, sentence-local infrastructure promises, internal KB directions copied as user text, and context-sensitive battery or bonus advice not present in the selected topic bodies before any reply can be returned or stored.
- App, ticket, and helpbot public response shapes and action objects remain unchanged. Flutter assistant-sheet token plumbing remains owned by the separate active-client plan in the `POKROV-app` repository.
- These repository checks prove the bounded implementation, not production provider flags, credential availability, route availability, deploy state, or readiness. Live readiness requires retained evidence for the exact committed route/model/payload/policy/KB/retriever candidate.
- One support sanitizer runs before truncation on both outbound user text and inbound model text. Input and output are bounded to 65,536 characters; NFKC is incremental and fails closed before expansion crosses that bound. Normal work uses at most three percent-decode passes, one non-recursive decoded URL rescan, plus bounded JSON-escape, HTML-entity, zero-width, IDNA separator, fullwidth, quote, and dash normalization. A linear structural probe rejects residual nested percent-encoded URL signatures after that budget instead of decoding them further. Model chunks are sliced before concatenation, and provider bodies are capped at 262,144 streamed bytes before JSON parsing.
- Stable placeholders cover Unicode email, proxy links, structurally classified token-bearing HTTP(S) URLs, `PKR-` recovery codes, `POKROV-` activation keys, hyphenated or compact UUIDs, `pkr_rt_` refresh tokens, signed/JWT-like session tokens, API/private keys, English or Russian labelled credentials, Basic/Bearer authorization, and long digit forms. Telegram init data requires a realistic numeric `auth_date` plus 64-hex `hash`; `query_id`, `user`, and `signature` are optional. A recognized labelled or raw blob is replaced through the end of its line even when a top-level pipe or HTML-escaped separator precedes optional fields. Empty/placeholder prose is preserved.
- After normalization and whole-line Telegram handling, one bounded scanner emits alternating non-URL and URL spans. Generic redaction runs only on non-URL spans; safe URLs are emitted directly and private URLs are replaced directly, without shield markers. Authority is validated before host trust on every supported decode layer; malformed ports, encoded delimiters, quote/space userinfo confusion, and residual deeper encoding fail closed. Userinfo, canonical sensitive query/fragment keys, semicolon or quoted nested assignments, keyless session tokens, nested proxy/subscription URLs, POKROV endpoint tokens, and `/sub/` or `/subscription/` token segments are private. Only exact known public-reference hosts (`github.com`, `pokrov.space`, `www.pokrov.space`, `docs.pokrov.space`, and `status.pokrov.space`) are trusted; leading/trailing dots and arbitrary `docs.*`/`status.*` hosts are not. Genuine GitHub commit and public docs references remain readable, while ticket UUID URLs remain private.
- Only sanitized model output can be returned and stored as a support ticket message with sender role `assistant`, so the admin history does not confuse model output with a human operator response or retain model-echoed credentials.
- Provider HTTP, oversized-body, and request failures log only a bounded status and fixed error code. Provider bodies and exception detail are neither logged nor used as ticket text because they may echo user input. API/helpbot persistence and rollback failures expose only `support_reply_persist_error`; cleanup failure exposes only `support_reply_cleanup_error`; and the SQLAlchemy engine hides statement parameters in rendered exceptions.
- WebApp and app surfaces that use the ticket API receive the same `assistant` messages in normal ticket payloads. Current client surfaces that open `@pokrov_supportbot` receive the same helper through the Telegram fallback path.
- The current closed live-eval corpus contains 12 ordered smoke cases, 49 normal support cases, 12 adversarial cases, and 10 session cases. The normal set includes the active WARP and notification diagnostics. The retired Karing route is intentionally absent from both the current KB and this corpus; dated design specs retain their historical snapshots as design evidence.
- Ticket attachments are private backend files, not public static assets. New uploads use `POST /api/tickets/uploads` and return a staged opaque `attachment_id`; create/reply sends that ID without echoing the private media triplet. Downloads use authenticated `GET /api/tickets/attachments/{stored_name}`.
- Staging defaults are 24 hours, five pending files, and 50 MiB pending bytes through `SUPPORT_PENDING_UPLOAD_TTL_HOURS`, `SUPPORT_PENDING_UPLOAD_MAX_COUNT`, and `SUPPORT_PENDING_UPLOAD_MAX_BYTES`. Quota is canonical-account first, otherwise exact legacy Telegram owner, and counts only unexpired unbound rows. Admission cleanup is restricted to that same owner and removes only expired unbound rows with non-null expiry and their files; it does not sweep another owner, legacy null-expiry, or bound history.
- Upload storage fsyncs an exclusive temporary file in the final directory, atomically renames it, and fsyncs the parent directory on POSIX before attempting the attachment-row commit. Temporary paths are cleaned on failure. After rename, persistence and ambiguous commit-acknowledgement failures preserve the final file: a committed row cannot be manufactured with a missing file, while a rowless final remains until the safety-grace reconciler verifies and removes it. The message and conditional attachment bind commit together; concurrent losers receive `409 support_attachment_already_bound` without a duplicate message/ticket mutation.
- Bound attachment reads inherit bound-ticket authorization, including normal admin access. Unbound/legacy rows retain exact owner/admin fallback, except an explicit-expiry unbound row returns `404` after expiry. Recovery is explicitly denied and cannot acquire admin bypass from a synthetic numeric ID.
- The supervised worker owns global reconciliation. Defaults are a 900-second interval, 3600-second safety grace, 100-row expired batch, 500 selected file candidates, and 500 DB rows per run. It never deletes bound or null-expiry rows, removes old temp and rowless canonical files only after grace, validates exact canonical basenames before unlink, and reports integer-only counts including missing DB-row files. Each process-local cycle freezes a filesystem mtime cutoff and DB max-ID high-water, then advances lexicographic and ID cursors through bounded processing windows; newer entries cannot prolong the active cycle, and integer wrap flags expose completion. Restart discards the snapshot and starts a new cycle. File selection memory is bounded by the configured limit, but each run enumerates the full upload directory once, so enumeration cost is `O(total entries)`. Local wiring tests do not prove production scheduling or large-directory latency.
- Old WebApp clients may submit the exact persisted `support/{stored_name}` triplet during rolling deployment. Ownership and supplied metadata are verified semantically, then canonicalized from the row. Forged/mismatched private references are rejected; non-private Telegram/client triplets remain compatible.
- Release 1.2 support bundles use the closed contracts in
  `shared/contracts/support/`: an Ed25519-signed X25519 recipient key set and,
  only for the extended profile, an Ed25519-signed collection policy valid for
  at most 30 minutes. The client preview and encrypted payload must derive from
  the same deterministic manifest and per-file hashes. Plaintext ZIP/chat
  fallback, arbitrary filesystem collection, raw config, destination history,
  credentials, IP addresses, domains and email addresses are forbidden.
- The authenticated support-bundle lane distributes the signed public key set,
  creates or reuses a case-bound short-lived upload ticket, accepts sequential
  resumable ciphertext chunks, exposes the authoritative resume offset and
  queues completion. The client persists only the encrypted envelope in its
  private outbox before network use and retains it for an explicit later retry
  when offline. Ticket, chunk replay and completion are idempotent; the short
  scalar diagnostics summary remains a separately labelled fallback.
- The API process never decrypts or parses bundle content. The opt-in isolated
  worker owns mounted private keys, complete-ciphertext integrity checks,
  in-memory decryption, closed manifest/file/redaction validation and hostile
  corpus rejection. Accepted storage contains only the original encrypted
  envelope; rejected objects stay encrypted in private quarantine. Production
  signing/recipient keys, custody/rotation, deployed private storage, worker
  schedule and a real successful upload remain exact-candidate `I4` gates.
- Support L1 reads only the closed bundle summary/timeline and cannot obtain a
  download grant. Explicitly allowlisted L2/SRE actors may issue one-time,
  15-minute-maximum grants for a fixed reason and download only the original
  checksum-verified ciphertext. Grant, download, and retention-hold changes are
  audited against the bundle's existing support case. The worker deletes only
  eligible unheld accepted/quarantine/audit data in bounded batches and reports
  integer counters; production scheduling, permissions, backlog, and real
  operator-role evidence remain unproved until retained separately.
- The accepted bundle's `proof_outcome` comes only from
  `network/summary.json.egress_state`; unrelated operational events do not
  replace it. An unknown egress state remains `unknown`. `last_phase` and
  `last_error_code` describe the last available event independently, or are
  null when there are no events. The reduced support event schema contains no
  attempt identity or authoritative count, so `observed_attempts` is null;
  stage-start events and connection state are not a connection denominator.
  These are historical client-reported bundle facts, not current runtime proof.
- Recovery sessions have a narrower text-only support projection: upload, attachment download, and standalone `/api/client/support/assistant` return `403 recovery_scope_forbidden`; nonempty media fields on ticket create/message are rejected; all recovery ticket responses omit historical and new message media metadata. Normal client and admin attachment behavior remains unchanged.
- Normal sessions retain standalone assistant `safeDiagnostics` compatibility. The active Android/Windows adapter currently always sends app diagnostics and uses the standalone assistant path, so this platform slice is not promotable for recovery UX until a separate recovery-aware client slice omits diagnostics/media and uses ticket text endpoints instead. That client repository is outside this task.
- Telegram support ticket replies in both `@pokrov_supportbot` and the main bot admin queue accept text, photo, document, and video messages; captions are stored as the message body, and attachment metadata is retained on the ticket message.
- User upload MIME policy is intentionally narrow: PNG, JPEG, WebP, PDF, and UTF-8 TXT after magic-byte checks. SVG, HTML, video, and opaque octet-stream uploads are rejected.
- AI ticket messages use safe plaintext mini-formatting only: short labels, line breaks, numbered steps, bullets, inline bold/code markers. The WebApp renders those markers as structured blocks without accepting raw HTML.
- `@pokrov_supportbot` renders AI mini-formatting through escaped Telegram HTML and attaches quick follow-up buttons: `Не получилось`, `Дайте шаги`, `Оператор`, and `Открыть обращение`. Buttons either put the user into the same ticket reply flow or append a safe operator-request message to the ticket.
- Current support knowledge covers the app-first path plus beta manual setup through compatible clients such as `Hiddify`, `Happ`, `v2rayNG`, `v2rayN`, `Streisand`, `NekoBox`, `NekoRay`, `Shadowrocket`, `FoXray`, and `V2Box`; safe same-account scalar questions may be answered in-app, while mutations, unresolved anomalies, and unclear cases still go to operators.
- The text synthesis serialized-input ceiling is 30,000 characters with a 512-character provider-envelope reserve. Environment values may lower the 30,000-character ceiling but cannot raise it. Isolated Vision requests instead carry at most three inline images of up to 2 MiB each, plus the fixed prompt/schema; they do not carry the main synthesis context.
- Knowledge refresh is an operator-side xCody operation and is never invoked inside a user request.

## Read-only ticket case context

With the agent enabled, normal ticket API and helpbot messages use
`support_case_context.py` inside the existing rate, concurrency and deadline
limits. The server verifies canonical ticket ownership (exact legacy owner only
for a null account). It reads access expiry, verified identity kinds, the five
latest same-account orders, payment-processing flags, eight account event
codes, five operator action codes, six public messages and two diagnostic
bundle summaries. Internal notes, raw event/provider payloads, identifiers,
encrypted bundle contents and arbitrary server logs are excluded.

For at most two recent Lava.top orders, the server may GET the stored invoice
reference and admit only a closed status. No provider mutation or reconciliation
runs. A stored paid order, a live provider confirmation and a user receipt are
separate evidence sources; unavailable live reads do not mean payment failed.
Unknown purchases through an unlinked login require owner verification by an
operator, not a cross-account search driven by the model.

The latest two public user attachments are read only after ticket authorization.
Private web files require an exact bound attachment row and a confined storage
path; Telegram downloads use the receiving helpbot. Files are limited to 2 MiB.
TXT is decoded and sanitized locally. PNG/JPEG/WebP images retain the 12-megapixel
input limit and are sent as inline bytes to the exact supported Vision route.
PDFs are rasterized into at most three 1800-pixel JPEG pages and sent in one
Vision request per file. Production requires `poppler-utils` and the existing
Pillow dependency; Tesseract/OCR is no longer used. The owner explicitly approved
external processing of user attachments on 2026-09-09. Original image contents
therefore reach the provider; subsequent sanitization is an output boundary,
not a claim that the provider never sees PII. Private download URLs, bot tokens,
account facts and unrelated history are never sent to this analysis stage.

Vision receives only a fixed internal extraction prompt and the images, with no
tools or ability to send messages. Its closed JSON contains `visible_text`
(1200 characters), `visual_details` (600) and `uncertainty` (200); code rejects
extra fields, invalid types and raw replies over 16,000 characters, then redacts
credentials and PII before bounding each field to its projection limit. A slightly
longer field no longer discards the entire file. Code passes only that projection to the main support synthesis. The
intermediate response is not stored as a ticket message or returned directly
to the user. It remains untrusted evidence, including any instructions depicted
in the attachment. PDF projections explicitly state the three-page limit.
Final case validation also rejects the observed unsupported assertion that a
receipt or screenshot itself confirms payment; rejection returns the existing
local account/payment summary. This narrow regression guard does not establish
complete semantic correctness of model-generated prose.

The two bounded attachment jobs and up to two live invoice reads run in
parallel. Each attachment has a 22-second total budget, with at most 18 seconds
for its provider call and eight seconds for PDF conversion; the existing
25-second case-load and 50-second total harness deadlines still apply. An
attachment failure is labelled `unreadable_or_over_limit` while completed
payment/access facts remain available. No local OCR or alternate-provider
fallback runs. Only the supported multimodal profiles can analyze attachments.

The model may summarize the collected facts without a KB keyword match. It has
no model-visible tools or write access. Unresolved discrepancies retain a useful
summary for the operator; provider/output-validation failure returns a local
summary of collected payment/access facts. Assigned, in-progress and closed
tickets suppress AI. Before persistence, the latest public user message must
still match the pre-generation revision; a newer user/operator/assistant message
discards the stale reply. Recovery sessions retain text-only KB handling and
never enter the case/file/diagnostic loader. Standalone app assistant behavior
is unchanged.

## xCody Knowledge Refresh

Use [pokrov_support_ai_kb_refresh.py](../../scripts/pokrov_support_ai_kb_refresh.py) to project the exact six public-support sources, reject unsafe content before HTTP, call xCody once through OpenAI Chat Completions, validate the closed KB schema, and optionally update `shared/support-ai-knowledge.json` atomically.

```powershell
python scripts/pokrov_support_ai_kb_refresh.py inventory
python scripts/pokrov_support_ai_kb_refresh.py run-xcody --dry-run
$env:XCODY_API_KEY = "<owner-provided-at-runtime>"
python scripts/pokrov_support_ai_kb_refresh.py run-xcody --apply
```

The dry-run requires no key and prints only aggregate audit fields, never source bodies. The refresh allowlist excludes architecture, operations, evidence, agent-instruction, credential, and private customer/provider paths. Review the resulting KB diff before any separately authorized deployment.

## Beta Rules

- Do not request private subscription links, QR codes, payment card details, or raw Telegram init data in public chats.
- Attachments are a privacy-hardening area; operators should avoid asking for sensitive screenshots unless required.
- Escalations should label current-origin, brain-origin, and RU-origin evidence separately.
- Do not describe the AI helper as a resolved-ticket path; it may read only the bounded same-account facts above. Account mutations and resolution of payment disputes or unclear anomalies remain manual support; the case path collects evidence first.
