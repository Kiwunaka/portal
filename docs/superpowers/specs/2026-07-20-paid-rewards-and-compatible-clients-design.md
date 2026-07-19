# Paid Rewards And Compatible Clients Rollout Design

**Status:** owner-approved design; implementation not started
**Date:** 2026-07-20
**Repository:** POKROV platform
**Base candidate:** `9eea588`
**Implementation branch:** `codex/rewards-rollout-integration`

This document records an approved implementation design. It does not override
the canonical product or architecture owners until the implementation and
their documentation updates land together. Runtime configuration and retained
candidate evidence remain authoritative for rollout claims.

## 1. Decision Summary

The platform will ship a paid-only rewards surface and correct the related
acquisition and compatibility guidance.

- The weekly wheel is available only to an account with a server-confirmed,
  currently active paid entitlement.
- The wheel cooldown is 168 hours per canonical account across Telegram and
  WebApp entry points.
- The wheel has four backend-owned outcomes:

  | Reward | Weight | Probability |
  | --- | ---: | ---: |
  | `+1 day` | 9,000 | 90% |
  | `+3 days` | 890 | 8.9% |
  | `+7 days` | 100 | 1% |
  | `+30 days` | 10 | 0.1% |

- The activity calendar is available to the same active-paid audience.
- One UTC-date check-in is accepted per account per day. Consecutive check-ins
  award `+1 day` at days 7, 14, 21, and 28, for at most four rewarded days in a
  28-day cycle. A missed UTC date starts a new cycle at day 1.
- Public acquisition copy may say "up to 10 days at the start" only when it
  immediately explains the two independent components: five trial days plus
  five days for the one-time Telegram channel bonus. Telegram alone is never
  described as a ten-day bonus.
- POKROV remains the primary client. Hiddify remains the first verified manual
  fallback. Karing and Happ are optional, best-effort compatibility choices in
  the closed manual-setup surface.
- The existing code-owned support agent on `master` is retained. This slice
  changes its approved knowledge only where the product facts or compatible
  client instructions change; it does not replace the runtime, provider
  adapter, safety policy, or evaluation harness.

## 2. Scope

### In scope

- One account-owned rewards authority used by the API and Telegram bot.
- Account-owned reward state, atomic cooldown/check-in enforcement, durable
  claim history, and account entitlement grants.
- Paid eligibility and independent kill switches for wheel and calendar.
- Safe WebApp rewards UI, including partial endpoint degradation.
- Correct channel-bonus offer/claim presentation, including grandfathered
  historical grants.
- Correct public copy for `5 + 5`, paid rewards, and the rare `+30 day`
  jackpot after the exact production configuration is verified.
- Karing and Happ manual import paths with format-specific private URLs.
- Canonical product, architecture, user, operations, shared-fact, and support
  knowledge updates required by the changed behavior.
- Focused backend, migration, API, bot, frontend, copy, and support-KB tests.

### Out of scope

- Changes to the separate `POKROV-app` repository. Its managed provisioning
  remains the primary client path and it does not expose raw subscription URLs.
- A new support-agent framework, model router, vector database, embeddings,
  MCP server, sidecar, or model-visible external tool.
- Reworking the current support-agent provider choice or enabling it without
  its existing candidate-specific gates and runtime credentials.
- A general split of the large `portal_bot/api.py`. This work extracts only the
  reward domain needed to prevent another independent implementation there.
- Deleting legacy reward fields or historical claims during rollout.
- Claiming device-level Karing or Happ compatibility without retained tests for
  the exact application versions.

## 3. Current Problems Being Corrected

The current platform has two wheel mutation paths. The Telegram bot enforces a
paid check but bypasses `BONUS_WHEEL_ENABLED`, uses a different random path, and
does not create `RewardClaim` history. The app API honors the flag and writes a
claim, but currently permits trial-only users and does not provide one
account-level concurrency boundary. Both mutate `User.last_wheel_spin`.

The calendar API currently reuses `User.streak_months` and
`User.streak_last_check`. The Telegram bot treats those fields as months of
paid continuity, so using them for daily check-ins corrupts an unrelated
product fact. The current default also awards one day on every daily check-in,
which can indefinitely sustain access.

The current code fallback gives the wheel a 5% 30-day jackpot. An existing
`AppSetting.wheel_config` overrides that fallback, so changing a constant alone
does not prove or change production behavior.

Several marketing surfaces still describe the Telegram channel reward as
`+10 days`, while the canonical current offer is `+5 days`. The combined
five-day trial and five-day Telegram reward may total ten days, but they are
separate eligibility and claim events. The settings page also falls back to
`10` when the API omits a value.

The WebApp manual setup currently presents Hiddify, v2rayN, and NekoBox. Happ
needs an explicit `format=happ` subscription response. Karing should use the
existing smart response through explicit `format=smart`. A plain subscription
URL is not interchangeable with the Happ URL.

## 4. Architecture

### 4.1 Reward domain boundary

Add a focused `portal_bot/rewards_service.py`. It owns:

- wheel configuration parsing and validation;
- cryptographically secure weighted selection;
- server-side paid-eligibility evaluation;
- account locking and reward-state transitions;
- account reward-grant creation and history projection;
- wheel/calendar state projection for API and bot consumers.

`portal_bot/api.py` and `portal_bot/bot.py` become thin adapters. They resolve
the authenticated canonical account, call this service, map typed outcomes to
their transport, and trigger the existing post-commit provisioning/sync path.
Neither adapter chooses rewards, calculates cooldowns, or directly extends
access.

This targeted extraction does not authorize an unrelated refactor of
`portal_bot/api.py`.

### 4.2 Canonical identity and paid eligibility

Every mutation resolves `User.account_id` through the existing account
foundation before reward logic runs. The service locks the canonical `Account`
row before locking or creating reward state. Telegram aliases, email sessions,
and app sessions for the same account therefore share one cooldown and one
calendar.

Eligibility is derived on the server from the current account entitlement
projection. The caller cannot supply paid status. The exact predicate is:

- the canonical `Account` exists with `status=active` and is not a merge source;
- at least one compatibility `User` projection for that account is active, has
  `sub_type=PAID`, and has `expiry_at > now`;
- the locked entitlement ledger has a non-reversed grant whose current interval
  contains `now`, whose `grant_kind=paid_access`, whose status is `active` or
  `grace`, and whose source is `provider_payment` or
  `compatibility_projection`.

The service rebuilds the account entitlement projection before evaluating this
predicate whenever the ledger may be stale. Free-only, trial-only, Telegram-
bonus-only, referral-bonus-only, expired, merged-away, disabled, and recovery-
only sessions are not eligible. A reward is appended to access, but once the
real `paid_access` interval ends and the projection becomes `BONUS`, the account
cannot earn another paid reward until a new paid interval begins. This avoids
implicit paid lineage and prevents rewards from sustaining their own
eligibility.

Read endpoints return `eligible=false` and a stable reason code. Mutation
endpoints repeat the eligibility check inside the locked transaction.

### 4.3 Data model and migration

Add one account-owned state table, `reward_account_states`:

- `account_id` primary key;
- `wheel_last_spin_at`;
- `wheel_last_grant_id`;
- `calendar_last_check_date`;
- `calendar_cycle_started_on`;
- `calendar_cycle_day`;
- `calendar_first_checkin_at`;
- `calendar_streak_7_unlocked_at`;
- `created_at` and `updated_at`.

`calendar_cycle_day` is the only current consecutive-day counter. Its invariant
is `0` with all calendar dates null, or `1..28` with
`calendar_cycle_started_on = calendar_last_check_date - (cycle_day - 1)`.
Completed day 28 remains readable until the next accepted UTC date starts a new
cycle. `calendar_first_checkin_at` and `calendar_streak_7_unlocked_at` are
write-once achievement facts and never reset with a cycle or missed day. No
redundant daily streak counter is introduced.

Do not extend `reward_claims`. Its non-null `tg_id` and Telegram-keyed unique
constraint make it a legacy ledger, so existing rows remain read-only history.
New account-owned reward claims are existing `EntitlementGrant` rows with
source `bonus_wheel` or `bonus_calendar`. Their metadata contains a version,
reward days, committed UTC timestamp, and the bounded wheel preset or calendar
milestone needed for safe history rendering. API history combines legacy
`RewardClaim` rows with the two new grant sources without rewriting or
double-counting old rows.

Before reward-state backfill, the existing account-foundation backfill must
finish. Any `User` without a canonical `account_id`, any unresolved merge
review, or any invalid merge chain is counted and retained for manual review;
the reward flags remain disabled while that count is non-zero. Reward migration
does not create an ad-hoc account.

The migration then backfills `wheel_last_spin_at` with the latest legacy
`User.last_wheel_spin` across users linked to each canonical account and records
the source count in secret-free evidence. It deliberately does not import
`streak_months` or `streak_last_check` into the daily calendar, because those
fields represent paid-month continuity. Legacy fields remain in place until a
separately approved cleanup proves that all consumers have migrated.

Account merge handling is part of this slice. Under the existing ordered
account locks, the merge hook locks both reward-state rows before moving
account-owned rows. It keeps the later wheel timestamp and its matching grant
pointer. For calendar state it keeps the row with the later last-check date;
when dates tie, it keeps the greater cycle day, then the earlier cycle start as
the deterministic tie-breaker. The losing state is deleted only after the
winner is stored on the target account. Existing reward `EntitlementGrant`
rows move through the account-foundation grant path and keep their globally
unique idempotency keys. Merge tests prove that cooldown/calendar progress
cannot reset and that no already-earned milestone is awarded again. Pending
`reward_entitlement_sync` jobs are reassigned to the target account under the
same grant-based idempotency key; they are not duplicated. The earliest
non-null write-once achievement timestamps survive the merge.

Each awarded reward creates an account `EntitlementGrant` with:

- source `bonus_wheel` or `bonus_calendar`;
- kind `premium_bonus`;
- a stable, globally unique idempotency key;
- exact duration and timestamps;
- provider `internal_economy`.

The service reuses the existing additive entitlement projection rather than
mutating `User.expiry_at` as independent truth. `User` remains a compatibility
projection rebuilt by the economy layer.

Every awarded reward also creates a queued `reward_entitlement_sync`
`NodeProvisioningJob` in the same database transaction as its grant and state
change. The job key is derived from the grant id, so grant, durable
reconciliation intent, and idempotency commit atomically. There is no
post-commit enqueue gap.

### 4.4 Wheel transaction

The wheel configuration is versioned as `paid_weekly_v1`. This preset is valid
only when it has exactly the four ordered outcomes `1/3/7/30`, exact weights
`9000/890/100/10`, a total of 10,000, and a cooldown of 168 hours. A stored
`paid_weekly_v1` that drifts from any of those values is invalid and fails
closed; generic syntactic validation is insufficient. The code fallback and
the intended production `AppSetting.wheel_config` use the same values, but
production is not considered configured until a guarded operator step records
the previous value, writes the exact new value, reads it back, and retains a
secret-free hash/result. The admin write boundary rejects a
`paid_weekly_v1` payload with any different outcome, order, weight, total, or
cooldown instead of storing a value that will fail later.

Within one transaction the service:

1. locks the canonical account and its reward state;
2. rechecks active-paid eligibility and `BONUS_WHEEL_ENABLED`;
3. rejects an unexpired cooldown without drawing a reward;
4. selects from the validated server-only weights with `secrets`;
5. generates a UUID-backed `reward-wheel:v1:<event-id>` idempotency key,
   creates the entitlement grant, and stores its id in
   `wheel_last_grant_id`;
6. creates the grant-keyed queued `reward_entitlement_sync` job;
7. advances `wheel_last_spin_at` and rebuilds entitlement projection;
8. commits state, grant, and sync job once.

Telegram and WebApp both call this path. The public state contains ordered
sectors `[1, 3, 7, 30]`, but never weights or internal random values.

### 4.5 Calendar transaction

Calendar dates are UTC dates selected by the backend. The client timezone and
client-provided date never decide eligibility.

Within one transaction the service:

1. locks the canonical account and its reward state;
2. rechecks active-paid eligibility and `BONUS_CALENDAR_ENABLED`;
3. returns the current state unchanged when today's UTC date was already
   checked in;
4. advances the streak for the immediately following date, or resets it to day
   1 after a gap;
5. sets `calendar_first_checkin_at` on the first accepted check-in and sets
   `calendar_streak_7_unlocked_at` when day 7 is first reached; neither is ever
   cleared;
6. awards one day only at cycle days 7, 14, 21, and 28, using
   `reward-calendar:v1:<origin-account-id>:<cycle-start>:<milestone>` as the
   stable grant key;
7. creates the grant-keyed queued `reward_entitlement_sync` job in the same
   transaction whenever a milestone creates a grant;
8. closes the cycle after day 28 so the next accepted UTC date begins day 1;
9. commits state and, when awarded, grant plus sync job once.

There is no daily access award outside those four milestones. Monthly paid
streak fields are not read or written by this flow. Current streak UI uses
`calendar_cycle_day`; unlocked `first_checkin` and `streak_7` achievements use
the write-once state timestamps and therefore never relock. The adapter may
write the existing legacy `Achievement` rows as a compatibility projection,
but it never treats that Telegram-keyed table as account truth. Reward history
and total awarded days use the account reward grants. A daily non-milestone
check-in does not create a fake claim.

### 4.6 Feature switches

`BONUS_WHEEL_ENABLED` and `BONUS_CALENDAR_ENABLED` remain independent emergency
kill switches and remain false by default in source examples. Both the API and
Telegram adapters must honor the wheel switch. Production enables the features
only after migrations, exact config verification, focused smokes, and a
rollback snapshot pass.

## 5. API And UI Contract

### 5.1 API state

Reward summary and feature-state responses expose:

- `enabled` and `eligible` separately;
- a stable eligibility/rejection reason;
- authoritative cooldown/check-in timestamps in UTC;
- ordered wheel sectors without weights;
- calendar cycle/streak state and the next milestone;
- the actual awarded days from the committed reward grant;
- provisioning state when post-commit synchronization is pending.

Reward history labels each entry by `legacy_reward_claim`, `bonus_wheel`, or
`bonus_calendar`. The adapter deduplicates by durable row identity only; it
does not infer duplicates from equal dates or equal reward sizes.

The channel-bonus contract separates `offer_days=5` from
`claimed_days=<actual historical grant>`. A grandfathered ten-day claim remains
visible as ten days already granted without changing the current five-day
offer.

### 5.2 Fail-closed WebApp behavior

The rewards UI is loaded feature by feature. Failure of one optional endpoint
does not hide successful independent rewards.

- No valid server sectors means no interactive wheel.
- One sector renders as a non-wheel guaranteed-reward card.
- Duplicate, non-positive, excessive, or otherwise invalid sectors disable the
  wheel and show a synchronization error.
- If the committed `reward_days` is not in the current server sectors, the UI
  does not animate or map it to sector zero. It shows a synchronization error,
  refetches authoritative state, and preserves the backend result text.
- Sector geometry is never described as probability. The UI states that visual
  sector size does not represent chance.
- Successful mutations refetch dashboard/entitlement and reward state instead
  of inventing a local expiry or calendar result.
- Disabled and ineligible states are visible but not actionable; they do not
  become generic network failures.

## 6. Karing And Happ Manual Setup

POKROV managed setup remains the primary action. The collapsed manual section
orders alternatives as:

1. Hiddify — verified fallback;
2. Karing — optional/best-effort;
3. Happ — optional/best-effort;
4. existing platform-specific advanced clients where still applicable.

A shared URL helper parses the private subscription URL and uses
`URL.searchParams.set`, preserving other query parameters and fragments:

- Karing receives `format=smart`;
- Happ receives `format=happ`.

The private URL or QR is copied/rendered only inside the authenticated POKROV
surface. It is never appended to an external download link, analytics event,
log, support message, or deep link to a third-party site. Download buttons use
only official public project pages. Copy explicitly warns that Karing/Happ are
best-effort and tells the user to return to POKROV or Hiddify if import or
whitelist behavior is incomplete.

The platform support KB receives the same exact format instructions. Its tests
must require all three compatible-client topics and prevent wording that tells
users to replace a URL suffix with a second `?`.

## 7. Marketing And Product Truth

The shared product fact remains:

> До 10 дней на старте: 5 дней бесплатно в приложении и ещё 5 дней после
> привязки Telegram и подтверждения подписки на канал.

Required corrections include SEO metadata, Telegram landing, checkout help,
VPN long-form copy, WebApp settings fallbacks, E2E fixtures, copy catalog, and
support knowledge. No surface may shorten this to "Telegram bonus +10 days".

After the paid gate, exact production wheel configuration, and both feature
flags are verified for the deployed candidate, public copy may say:

> Для активной платной подписки доступны еженедельное колесо бонусов и
> календарь активности. В колесе возможен редкий джекпот +30 дней.

The copy does not publish internal weights. If either feature remains disabled
in the target environment, its availability claim is withheld from that
environment's public release.

## 8. Existing Support Agent Boundary

The current code-owned support mini-agent is already implemented and hardened
on the base candidate. This work does not cherry-pick an older design-only
snapshot or introduce a second support runtime.

Only the allowlisted product knowledge and its deterministic tests change:

- combined `5 + 5` wording;
- paid-only wheel and calendar availability after rollout;
- Karing `format=smart` and Happ `format=happ` instructions;
- escalation when compatibility or account state cannot be established from
  approved knowledge.

The existing redaction, grounding, local fallback, session, rate/concurrency,
provider, evaluation, and human-handoff contracts remain unchanged and must
continue to pass their current gates.

## 9. Error And Recovery Semantics

- Disabled feature: read returns `enabled=false`; mutation returns the existing
  stable feature-disabled error without mutation.
- Ineligible account: read returns `eligible=false`; mutation returns `403`
  with `active_paid_required`.
- Wheel cooldown: `409` with authoritative `next_spin_at`; no random draw or
  partial grant. The response/state includes the last committed reward resolved
  through `wheel_last_grant_id`, so a retry after a lost response can reconcile
  without another spin.
- Same-day calendar retry: idempotent success with `already_checked_in=true`;
  no second reward grant.
- Invalid stored wheel configuration: fail closed, emit a secret-free operator
  event, and expose no interactive wheel. Do not silently substitute a fallback
  after an invalid explicit production setting is found.
- Database failure before commit: no reward grant, state, or entitlement change.
- Provisioning is asynchronous after the atomic reward commit. This slice adds
  a `reward_entitlement_sync` job to the existing `NodeProvisioningJob` queue,
  with nullable indexed `account_id` and `entitlement_grant_id`, a grant-based
  unique idempotency key, bounded retry/backoff, and terminal manual-review
  state. The response reports
  `sync_pending` for queued/running/retry jobs and `synced` only after durable
  completion. A mutation retry cannot grant or enqueue twice.
- The worker resolves the canonical account immediately before its external
  call and rechecks it before finalization. Account merge invalidates the lock
  token of a queued, retrying, or running source-owned reward job, moves it to
  the target account, and returns it to `queued`. A stale worker may finish an
  idempotent external call, but it cannot mark the invalidated source job
  complete because finalization requires the same `running` status, lock token,
  and canonical `account_id`. The target-owned retry is the only finalizer.
- Unknown client reward: preserve the committed backend result, suppress wheel
  animation, refetch, and surface a synchronization error.

## 10. Verification Strategy

### Backend and migration

- deterministic boundary tests for weights `9000/890/100/10` and secure draw
  integration without statistical/flaky assertions;
- paid, free, trial, bonus-only, expired, disabled, and merged-account
  eligibility tests;
- shared-account/API/bot cooldown tests;
- concurrent double-spin and double-check-in tests proving one reward grant;
- calendar UTC, same-day retry, missed-day reset, milestones, day-28 reset, and
  four-day cap tests;
- migration tests proving latest wheel timestamp backfill and deliberate
  non-import of monthly streak fields;
- entitlement projection/idempotency and durable reward-sync queue tests,
  including retry, completion, and terminal manual review;
- account-foundation preflight and post-rollout merge reconciliation tests,
  including a merge racing a claimed/running sync job;
- write-once first-check-in/streak-7 achievement tests across missed days,
  completed cycles, aliases, and account merges;
- API contract tests proving public payloads contain sectors but no weights.

### Frontend and copy

- component/unit tests for missing, one, invalid, and changed sectors;
- unknown-result and partial-endpoint-degradation tests;
- E2E for paid-enabled and free/trial/expired-disabled surfaces;
- exact Karing/Happ URL transformation tests, including existing query and
  fragment preservation;
- E2E proof that third-party `href` and analytics never contain subscription
  tokens;
- copy guardrails rejecting direct Telegram `+10` claims while permitting the
  explicitly decomposed `5 + 5` statement;
- marketing and WebApp build/lint/E2E gates from the task router.

### Support and documentation

- support KB topic coverage for Hiddify, Karing, Happ, `5 + 5`, and paid
  rewards;
- the existing deterministic support-agent safety, semantic, and load suites;
- canonical documentation links/contract checks and `git diff --check`.

## 11. Rollout And Rollback

1. Set the API reward flags false, stop every Telegram bot instance that can
   accept legacy wheel callbacks, and confirm no old reward mutator remains.
   Because the old bot ignores `BONUS_WHEEL_ENABLED`, this quiesce is mandatory;
   if it cannot be proven, rollout stops before backfill.
2. Complete account-foundation backfill and resolve or explicitly block every
   user without a canonical account. Retain the zero-unresolved preflight.
3. Run the additive reward-state/job migration and legacy wheel-timestamp
   backfill while mutations remain quiesced.
4. Deploy the reward service, API/bot adapters, durable sync worker support,
   and fail-closed UI with both reward flags disabled. Restart all bot/API
   instances on the exact same candidate before accepting reward traffic.
5. Verify migration counts, account-merge behavior, paid denial/allow behavior,
   API payloads, bot flag behavior, worker retries, and WebApp disabled states.
6. Snapshot the existing production `wheel_config`, write
   `paid_weekly_v1` with `9000/890/100/10`, read it back, and retain the
   secret-free result/hash.
7. Enable wheel for `active_paid`, run API and Telegram smokes, and verify one
   account shares one cooldown.
8. Enable calendar for `active_paid`, run UTC/idempotency/milestone smokes using
   an isolated fixture or approved test account without manufacturing a public
   production pass.
9. Publish paid-rewards marketing copy only after steps 1-8 pass. The `5 + 5`
   correction may publish earlier because it fixes an existing false claim.
10. Retain candidate-specific evidence and label manual/provider/deploy checks
   honestly.

Rollback first disables the two independent flags on the new candidate and
verifies that its API and bot adapters reject mutations. Disabling flags while
keeping the new candidate running is the default incident response.

Application rollback to a legacy bot is not automatically safe because that
bot ignores `BONUS_WHEEL_ENABLED`. Before any such rollback, stop every bot
instance and keep the legacy wheel callback unavailable. Do not restart a
legacy bot until a compatibility patch makes it honor the kill switch, or until
the new reward service candidate is restored. The additive schema may remain.
Restore the snapshotted wheel configuration only if the product owner
explicitly requests the previous economy. Reward grants already committed are
not deleted or reversed during ordinary rollback.

## 12. Acceptance Criteria

- API and Telegram wheel entry points use one account-owned service and honor
  the same kill switch, paid gate, weights, cooldown, ledger, and entitlement
  projection.
- The calendar cannot mutate monthly paid-streak fields and cannot award more
  than four days per completed 28-day cycle.
- Trial/free/bonus-only/expired accounts cannot mutate either paid reward.
- Public clients never receive probability weights and never invent sectors or
  reward mappings.
- Direct Telegram `+10` marketing claims are removed; combined `5 + 5` wording
  is consistent across product, WebApp, marketing, and support knowledge.
- Karing/Happ manual URLs use exact formats without leaking a private
  subscription URL to third parties.
- Current support-agent safety and quality gates remain green.
- No new agent framework, vector store, external retrieval service, or client-
  repository change is introduced.
- Push and deployment occur only after focused and relevant regression gates
  pass and candidate-specific evidence is retained.
