# Paid Rewards And Compatible Clients Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship one account-owned, paid-only weekly wheel and activity calendar, correct the `5 + 5` acquisition promise, and add safe Karing/Happ manual imports without changing the separate POKROV client or support-agent runtime.

**Architecture:** A focused `portal_bot/rewards_service.py` owns configuration, paid eligibility, row locking, reward grants, state, history, and account-merge reconciliation. FastAPI and Telegram become thin adapters; durable `reward_entitlement_sync` jobs project committed account grants to existing nodes; the WebApp consumes server-owned sectors and degrades feature by feature. Existing platform primitives, SQLAlchemy, the current worker, and Playwright are reused—no new runtime, framework, provider, vector store, or dependency is introduced.

**Tech Stack:** Python 3.12, SQLAlchemy, FastAPI, aiogram, pytest, Next.js/React/TypeScript, Playwright, existing POKROV migration and provisioning infrastructure.

## Global Constraints

- Work only in `C:\Users\kiwun\Documents\ai\VPN\.worktrees\final-platform-integration` on `codex/rewards-rollout-integration`; promote the platform through `master` only after all gates pass.
- The approved authority is `docs/superpowers/specs/2026-07-20-paid-rewards-and-compatible-clients-design.md` at commit `edef646` on base candidate `9eea588`.
- Do not edit `C:\Users\kiwun\Documents\ai\POKROV-app`; POKROV managed setup remains the primary client path.
- Do not cherry-pick design snapshots `4808003`, `9c74fa3`, `a916b39`, or `9691730`; inspect them only as references and reimplement against current contracts.
- Wheel preset is exactly `paid_weekly_v1`, ordered days `1/3/7/30`, weights `9000/890/100/10`, total `10000`, and cooldown `168` hours.
- Calendar accepts one backend-selected UTC date per canonical account, awards `+1` only on days `7/14/21/28`, and starts day `1` after a missed date or after completed day `28`.
- Both rewards require a current real paid interval; reward-tail, trial, free, bonus-only, expired, disabled, and merge-source accounts are ineligible.
- `RewardClaim` and `User.last_wheel_spin/streak_months/streak_last_check` remain legacy evidence. New rewards use `RewardAccountState` and account `EntitlementGrant` rows only.
- Every awarded grant and its `reward_entitlement_sync` job commit atomically. A retry cannot create a second grant or job.
- `BONUS_WHEEL_ENABLED` and `BONUS_CALENDAR_ENABLED` remain false by default and are enforced by both API and Telegram adapters.
- Public payloads expose ordered sectors but never weights. The WebApp never invents sectors, probabilities, reward mappings, or expiry values.
- Telegram offer is `5` days. “Up to 10 days at the start” is permitted only as explicit `5 trial + 5 Telegram`; historical `claimed_days=10` remains visible as a grandfathered grant.
- Karing uses `format=smart`; Happ uses `format=happ`; private subscription URLs never enter third-party links, analytics, logs, support messages, or deep links.
- Keep the current code-owned support agent. Only its allowlisted knowledge and deterministic tests change.
- No new package, agent framework, model router, external retrieval service, embeddings, sidecar, MCP server, or cleanup automation is allowed.
- Run Python checks with `C:\Users\kiwun\AppData\Local\Temp\pokrov-support-agent-venv-20260715\Scripts\python.exe`; its FastAPI/Starlette pair satisfies `portal_bot/requirements.txt`. Every pytest command uses process-local `--basetemp "$env:TEMP\pokrov-rewards-$PID"` to avoid foreign Windows temp ACLs. Do not install into or mutate global Python.
- Treat all other dirty files and worktrees as concurrent work. Stage only files named by the active task and never use destructive Git cleanup.
- Deploy and public availability claims require candidate-specific retained evidence. A local pass is not production proof.

---

## File Structure

### Create

- `portal_bot/rewards_service.py` — reward constants, typed results, account eligibility, locking, wheel/calendar mutations, backfill, history, and merge reconciliation.
- `portal_bot/tests/test_rewards_service.py` — deterministic domain, eligibility, concurrency, idempotency, UTC calendar, history, and achievement tests.
- `tests/test_reward_migrations.py` — SQLite/PostgreSQL schema-helper and legacy wheel timestamp backfill coverage.
- `webapp/src/components/cabinet/bonus-wheel.tsx` — fail-closed wheel rendering and committed-result animation.
- `webapp/src/app/(dashboard)/rewards/page.tsx` — independently loaded wheel, calendar, history, and entitlement refresh surface.
- `webapp/src/lib/subscription-format.ts` — `URL.searchParams.set` transformation for Karing/Happ.
- `webapp/e2e/rewards.spec.ts` — enabled/ineligible/partial-failure/invalid-sector/unknown-result reward cases.
- `scripts/reward_rollout.py` — read-only preflight plus explicitly confirmed backfill/config/flag operator actions with redacted evidence.
- `tests/test_reward_rollout.py` — dry-run, confirmation, quiesce, snapshot, hash, unresolved-account, and evidence tests.

### Modify

- `portal_bot/models.py` — `RewardAccountState` and account/grant columns on `NodeProvisioningJob`.
- `portal_bot/migrations.py` — additive SQLite/PostgreSQL table, columns, constraints, and indexes.
- `portal_bot/economy_service.py` — idempotent internal premium-bonus grant primitive using the existing additive projection.
- `portal_bot/node_provisioning_service.py` — durable reward enqueue, canonical-account prepare/execute/finalize fencing, retry, and manual review.
- `portal_bot/account_foundation_service.py` — reward-state/job merge reconciliation before generic account-owned row moves.
- `portal_bot/api.py` — exact admin wheel-config validation and thin reward/channel response adapters.
- `portal_bot/bot.py` — shared reward service and wheel kill-switch enforcement.
- `portal_bot/channel_bonus_service.py` — preserve actual historical claim size while presenting the current five-day offer.
- `portal_bot/.env.example` — retain both reward flags as false and document rollout-only enablement.
- `portal_bot/tests/test_app_first_api.py` — account-owned reward API contracts and no-public-weights proof.
- `tests/test_node_provisioning_service.py` — reward job retry/completion/manual-review/merge-fence cases.
- `tests/test_account_foundation.py` — deterministic state merge and running-job invalidation.
- `tests/test_api_auth_and_tickets.py` — strict admin preset, subscription format, and channel offer/claim fields.
- `tests/test_bot_paywall.py` — paid gate, shared cooldown, and disabled Telegram callback.
- `webapp/src/lib/api.ts` — typed wheel/calendar/history payloads and endpoint methods.
- `webapp/src/components/cabinet-shell.tsx` and `webapp/src/app/(dashboard)/page.tsx` — rewards navigation.
- `webapp/src/app/(dashboard)/subscription/page.tsx` — ordered Hiddify/Karing/Happ manual choices with local copy/QR controls.
- `webapp/src/app/(dashboard)/settings/page.tsx` — five-day Telegram fallback and separate claimed amount.
- `webapp/e2e/cabinet-flow.spec.ts` and `webapp/e2e/settings-email-link.spec.ts` — manual URL secrecy and corrected fixtures.
- `marketing/src/lib/seo-pages.ts`, `marketing/src/lib/marketing-site.ts`, `marketing/src/app/checkout/checkout-client.tsx`, `marketing/src/app/telegram/page.tsx`, and `marketing/src/app/vpn/page.tsx` — explicit `5 + 5` copy and rollout-gated paid-reward copy.
- `shared/support-ai-knowledge.json` — exact Karing/Happ formats, `5 + 5`, and paid-only reward knowledge.
- `tests/test_pokrov_support_ai_kb_refresh.py`, `tests/test_frontend_text_integrity.py`, and `tests/test_public_copy_guardrails.py` — knowledge and public-copy guardrails.
- `docs/product/portal-vpn-product.md`, `docs/architecture/app-first-and-bonus-flows.md`, `docs/architecture/system-overview.md`, `docs/architecture/api-contracts.md`, `docs/user/portal-vpn-user-guide-ru.md`, `docs/user/compatibility-clients-guide-ru.md`, `docs/operations/deployment-and-access.md`, `webapp/README.md`, and `marketing/README.md` — canonical behavior, operations, and user guidance.

### Final Interfaces

```text
# portal_bot/economy_service.py
resolve_canonical_account_id(session, *, account_id: str) -> str
grant_internal_bonus_days(
    session,
    *,
    account_id: str,
    source: str,
    plan_code: str,
    idempotency_key: str,
    days: int,
    legacy_tg_id: int | None,
    metadata: dict[str, Any],
    now: datetime,
) -> EntitlementGrant

# portal_bot/node_provisioning_service.py
enqueue_reward_entitlement_sync(
    session,
    *,
    account_id: str,
    entitlement_grant_id: str,
    now: datetime,
) -> NodeProvisioningJob

# portal_bot/rewards_service.py
parse_paid_weekly_config(payload: Mapping[str, object], *, explicit: bool) -> WheelConfig
evaluate_active_paid(session, *, account_id: str, now: datetime) -> PaidEligibility
backfill_reward_account_states(session, *, now: datetime) -> RewardBackfillResult
get_wheel_state(session, *, account_id: str, enabled: bool, config_payload: Mapping[str, object] | None, now: datetime) -> WheelState
spin_wheel(session, *, account_id: str, enabled: bool, config_payload: Mapping[str, object] | None, now: datetime, randbelow: Callable[[int], int] = secrets.randbelow) -> RewardMutation
get_calendar_state(session, *, account_id: str, enabled: bool, now: datetime) -> CalendarState
checkin_calendar(session, *, account_id: str, enabled: bool, now: datetime) -> RewardMutation
get_reward_history(session, *, account_id: str, limit: int = 50) -> Sequence[RewardHistoryEntry]
reconcile_reward_merge(session, *, source_account_id: str, target_account_id: str, now: datetime) -> None

# webapp/src/lib/subscription-format.ts
subscriptionUrlForFormat(rawUrl: string, format: "smart" | "happ"): string
```

---

### Task 1: Add the Account-Owned Reward Schema

**Files:**

- Modify: `portal_bot/models.py:797-818`
- Modify: `portal_bot/migrations.py:590-620,1117-1165,1313-1360,2269-2305`
- Create: `tests/test_reward_migrations.py`
- Modify: `tests/test_free_soft_profile_migrations.py`
- Modify: `tests/test_postgres_migration_helpers.py`

**Interfaces:**

- Consumes: existing `Account`, `EntitlementGrant`, `NodeProvisioningJob`, `run_migrations()`, and dialect-specific additive migration helpers.
- Produces: `RewardAccountState`, nullable indexed `NodeProvisioningJob.account_id`, nullable indexed `NodeProvisioningJob.entitlement_grant_id`, and additive schema usable by Tasks 2-6.

- [ ] **Step 1: Write failing model and migration tests**

Add these assertions to `tests/test_reward_migrations.py` and exercise both a fresh database and a legacy `node_provisioning_jobs` table:

```python
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from portal_bot.models import Base, NodeProvisioningJob, RewardAccountState


def test_reward_state_model_uses_one_row_per_account():
    assert RewardAccountState.__tablename__ == "reward_account_states"
    assert RewardAccountState.__table__.primary_key.columns.keys() == ["account_id"]
    assert {column.name for column in RewardAccountState.__table__.columns} == {
        "account_id",
        "wheel_last_spin_at",
        "wheel_last_grant_id",
        "calendar_last_check_date",
        "calendar_cycle_started_on",
        "calendar_cycle_day",
        "calendar_first_checkin_at",
        "calendar_streak_7_unlocked_at",
        "created_at",
        "updated_at",
    }


def test_fresh_schema_has_reward_job_account_and_grant_indexes(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'fresh.db'}")
    Base.metadata.create_all(engine)
    schema = inspect(engine)
    columns = {row["name"] for row in schema.get_columns("node_provisioning_jobs")}
    indexes = {row["name"] for row in schema.get_indexes("node_provisioning_jobs")}
    assert {"account_id", "entitlement_grant_id"} <= columns
    assert {"ix_node_provisioning_jobs_account_id", "ix_node_provisioning_jobs_entitlement_grant_id"} <= indexes


def test_calendar_state_rejects_day_outside_zero_to_twenty_eight(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'check.db'}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session.begin() as session:
        session.add(RewardAccountState(account_id="a" * 36, calendar_cycle_day=29))
        try:
            session.flush()
        except Exception as exc:
            assert "calendar_cycle_day" in str(exc).lower() or "check constraint" in str(exc).lower()
        else:
            raise AssertionError("calendar_cycle_day=29 must violate the schema invariant")
```

- [ ] **Step 2: Run the schema tests and verify they fail**

```powershell
& 'C:\Users\kiwun\AppData\Local\Temp\pokrov-support-agent-venv-20260715\Scripts\python.exe' -B -m pytest -p no:cacheprovider --basetemp "$env:TEMP\pokrov-rewards-$PID" tests/test_reward_migrations.py tests/test_free_soft_profile_migrations.py tests/test_postgres_migration_helpers.py -q
```

Expected: collection fails because `RewardAccountState` and the two job columns do not exist.

- [ ] **Step 3: Add the model and additive dialect migrations**

Add this model next to `NodeProvisioningJob`, import `CheckConstraint` only once, and add the two job columns:

```python
class RewardAccountState(Base):
    __tablename__ = "reward_account_states"
    __table_args__ = (
        CheckConstraint(
            "calendar_cycle_day IS NULL OR (calendar_cycle_day >= 0 AND calendar_cycle_day <= 28)",
            name="ck_reward_account_state_cycle_day",
        ),
    )

    account_id = Column(String(36), primary_key=True)
    wheel_last_spin_at = Column(DateTime, nullable=True)
    wheel_last_grant_id = Column(String(36), index=True, nullable=True)
    calendar_last_check_date = Column(Date, nullable=True)
    calendar_cycle_started_on = Column(Date, nullable=True)
    calendar_cycle_day = Column(Integer, default=0, nullable=False)
    calendar_first_checkin_at = Column(DateTime, nullable=True)
    calendar_streak_7_unlocked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, nullable=False)


class NodeProvisioningJob(Base):
    __tablename__ = "node_provisioning_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String(36), index=True, nullable=True)
    entitlement_grant_id = Column(String(36), index=True, nullable=True)
```

In `portal_bot/migrations.py`, extend the existing SQLite `ALTER TABLE` path and both fresh-table definitions with the same nullable columns, create the two named indexes idempotently, and create `reward_account_states` with `ck_reward_account_state_cycle_day`. The PostgreSQL helper must use `ADD COLUMN IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS`; do not drop or rewrite an existing table.

- [ ] **Step 4: Run focused migration coverage**

```powershell
& 'C:\Users\kiwun\AppData\Local\Temp\pokrov-support-agent-venv-20260715\Scripts\python.exe' -B -m pytest -p no:cacheprovider --basetemp "$env:TEMP\pokrov-rewards-$PID" tests/test_reward_migrations.py tests/test_free_soft_profile_migrations.py tests/test_postgres_migration_helpers.py tests/test_pokrov_migration_defaults.py -q
```

Expected: all selected tests pass and legacy job rows remain readable with both new columns null.

- [ ] **Step 5: Commit the schema slice**

```powershell
git add -- portal_bot/models.py portal_bot/migrations.py tests/test_reward_migrations.py tests/test_free_soft_profile_migrations.py tests/test_postgres_migration_helpers.py
git commit -m "feat(rewards): add account reward schema"
```

---

### Task 2: Add Atomic Bonus Grants and Durable Sync Enqueue

**Files:**

- Modify: `portal_bot/economy_service.py:498-592,617-680`
- Modify: `portal_bot/node_provisioning_service.py:1-75`
- Create: `portal_bot/tests/test_rewards_service.py`
- Modify: `tests/test_node_provisioning_service.py`

**Interfaces:**

- Consumes: `RewardAccountState`, `EntitlementGrant`, `_ensure_projection_baseline_grant()`, `_project_additive_days()`, and `rebuild_account_entitlement_projection()`.
- Produces: `resolve_canonical_account_id()`, `grant_internal_bonus_days()`, and `enqueue_reward_entitlement_sync()` with stable idempotency for Tasks 4-7.

- [ ] **Step 1: Write failing grant/enqueue idempotency tests**

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from portal_bot.models import Account, Base, EntitlementGrant, User


PAID_ACCOUNT_ID = "00000000-0000-4000-8000-000000000101"
PAID_TG_ID = 700101


@dataclass(frozen=True)
class SeededPaidAccount:
    id: str
    tg_id: int


@pytest.fixture
def now() -> datetime:
    return datetime(2026, 7, 20, 12, 0, 0)


@pytest.fixture
def reward_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'rewards.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    with Session() as session:
        yield session
        session.rollback()


@pytest.fixture
def paid_account(reward_session, now) -> SeededPaidAccount:
    reward_session.add(Account(id=PAID_ACCOUNT_ID, status="active", created_source="test", created_at=now, updated_at=now))
    reward_session.add(
        User(
            tg_id=PAID_TG_ID,
            account_id=PAID_ACCOUNT_ID,
            uuid="00000000-0000-4000-8000-000000000102",
            sub_type="PAID",
            current_plan_code="month",
            expiry_at=now + timedelta(days=30),
            is_active=True,
        )
    )
    reward_session.add(
        EntitlementGrant(
            id="00000000-0000-4000-8000-000000000103",
            account_id=PAID_ACCOUNT_ID,
            legacy_tg_id=PAID_TG_ID,
            idempotency_key="test-provider-payment:paid-account",
            source="provider_payment",
            status="active",
            grant_kind="paid_access",
            plan_code="month",
            starts_at=now - timedelta(days=1),
            expires_at=now + timedelta(days=30),
            activated_at=now - timedelta(days=1),
            duration_days=31,
            provider="test",
            created_at=now - timedelta(days=1),
            updated_at=now,
        )
    )
    reward_session.flush()
    return SeededPaidAccount(id=PAID_ACCOUNT_ID, tg_id=PAID_TG_ID)


@pytest.fixture
def paid_reward_session(reward_session, paid_account):
    return reward_session


def test_internal_reward_grant_and_sync_job_are_idempotent(reward_session, paid_account, now):
    from portal_bot.economy_service import grant_internal_bonus_days
    from portal_bot.node_provisioning_service import enqueue_reward_entitlement_sync

    first = grant_internal_bonus_days(
        reward_session,
        account_id=paid_account.id,
        source="bonus_wheel",
        plan_code="reward_wheel",
        idempotency_key="reward-wheel:v1:00000000-0000-4000-8000-000000000001",
        days=1,
        legacy_tg_id=paid_account.tg_id,
        metadata={"version": 1, "reward_days": 1, "committed_at": now.isoformat()},
        now=now,
    )
    first_job = enqueue_reward_entitlement_sync(
        reward_session,
        account_id=paid_account.id,
        entitlement_grant_id=first.id,
        now=now,
    )
    second = grant_internal_bonus_days(
        reward_session,
        account_id=paid_account.id,
        source="bonus_wheel",
        plan_code="reward_wheel",
        idempotency_key=first.idempotency_key,
        days=1,
        legacy_tg_id=paid_account.tg_id,
        metadata={"version": 1, "reward_days": 1, "committed_at": now.isoformat()},
        now=now,
    )
    second_job = enqueue_reward_entitlement_sync(
        reward_session,
        account_id=paid_account.id,
        entitlement_grant_id=second.id,
        now=now,
    )
    reward_session.flush()
    assert second.id == first.id
    assert second_job.id == first_job.id
    assert first.grant_kind == "premium_bonus"
    assert first.provider == "internal_economy"
    assert first_job.idempotency_key == f"reward-entitlement-sync:v1:{first.id}"
```

- [ ] **Step 2: Run the focused tests and verify missing imports**

```powershell
& 'C:\Users\kiwun\AppData\Local\Temp\pokrov-support-agent-venv-20260715\Scripts\python.exe' -B -m pytest -p no:cacheprovider --basetemp "$env:TEMP\pokrov-rewards-$PID" portal_bot/tests/test_rewards_service.py tests/test_node_provisioning_service.py -q
```

Expected: failure importing `grant_internal_bonus_days` or `enqueue_reward_entitlement_sync`.

- [ ] **Step 3: Add the strict grant primitive and queue helper**

Implement the economy boundary with this exact validation and durable identity:

```python
def grant_internal_bonus_days(
    session,
    *,
    account_id: str,
    source: str,
    plan_code: str,
    idempotency_key: str,
    days: int,
    legacy_tg_id: int | None,
    metadata: dict[str, Any],
    now: datetime,
) -> EntitlementGrant:
    if source not in {"bonus_wheel", "bonus_calendar"}:
        raise ValueError("reward_source_invalid")
    if int(days) not in {1, 3, 7, 30}:
        raise ValueError("reward_days_invalid")
    account_key = resolve_canonical_account_id(session, account_id=account_id)
    existing = session.query(EntitlementGrant).filter_by(idempotency_key=idempotency_key).one_or_none()
    if existing is not None:
        if existing.account_id != account_key or existing.source != source or int(existing.duration_days or 0) != int(days):
            raise ValueError("reward_idempotency_conflict")
        return existing
    _ensure_projection_baseline_grant(session, account_id=account_key, now=now)
    starts_at, expires_at = _project_additive_days(session, account_id=account_key, days=days, now=now)
    grant = EntitlementGrant(
        id=str(uuid.uuid4()),
        account_id=account_key,
        legacy_tg_id=legacy_tg_id,
        idempotency_key=idempotency_key,
        source=source,
        status="active",
        grant_kind="premium_bonus",
        plan_code=plan_code,
        starts_at=starts_at,
        expires_at=expires_at,
        activated_at=now,
        duration_days=int(days),
        provider="internal_economy",
        created_at=now,
        updated_at=now,
    )
    _set_grant_metadata(grant, metadata)
    session.add(grant)
    session.flush()
    rebuild_account_entitlement_projection(session, account_id=account_key, now=now)
    return grant
```

Add the enqueue helper without committing inside it:

```python
def enqueue_reward_entitlement_sync(
    session,
    *,
    account_id: str,
    entitlement_grant_id: str,
    now: datetime,
) -> NodeProvisioningJob:
    key = f"reward-entitlement-sync:v1:{entitlement_grant_id}"
    grant = session.get(EntitlementGrant, entitlement_grant_id)
    if grant is None or grant.account_id != str(account_id) or grant.source not in {"bonus_wheel", "bonus_calendar"}:
        raise ProvisioningError("reward_sync_grant_invalid")
    existing = session.query(NodeProvisioningJob).filter_by(idempotency_key=key).one_or_none()
    if existing is not None:
        if existing.entitlement_grant_id != entitlement_grant_id:
            raise ProvisioningError("reward_sync_idempotency_conflict")
        return existing
    job = NodeProvisioningJob(
        account_id=str(account_id),
        entitlement_grant_id=str(entitlement_grant_id),
        job_type="reward_entitlement_sync",
        status="queued",
        idempotency_key=key,
        attempts=0,
        next_run_at=now,
        created_at=now,
        updated_at=now,
    )
    session.add(job)
    session.flush()
    return job
```

Rename the existing private `_canonical_account_id()` to the public
`resolve_canonical_account_id(session, *, account_id: str) -> str` and update
its economy-service callers. Both the reward service and provisioning worker
must import this one resolver; do not create a second merge-chain walker.

- [ ] **Step 4: Prove grant, projection, and enqueue atomicity**

Add a rollback test that raises after enqueue and asserts zero `bonus_wheel` grants and zero `reward_entitlement_sync` jobs in a fresh session. Then run:

```powershell
& 'C:\Users\kiwun\AppData\Local\Temp\pokrov-support-agent-venv-20260715\Scripts\python.exe' -B -m pytest -p no:cacheprovider --basetemp "$env:TEMP\pokrov-rewards-$PID" portal_bot/tests/test_rewards_service.py tests/test_node_provisioning_service.py portal_bot/tests/test_app_first_service.py -q
```

Expected: all selected tests pass; rollback leaves no partial grant, projection, or job.

- [ ] **Step 5: Commit the economy boundary**

```powershell
git add -- portal_bot/economy_service.py portal_bot/node_provisioning_service.py portal_bot/tests/test_rewards_service.py tests/test_node_provisioning_service.py
git commit -m "feat(rewards): add atomic bonus grant queue"
```

---

### Task 3: Add Configuration, Paid Eligibility, State, and Backfill

**Files:**

- Create: `portal_bot/rewards_service.py`
- Modify: `portal_bot/tests/test_rewards_service.py`
- Modify: `tests/test_reward_migrations.py`

**Interfaces:**

- Consumes: Task 1 state model and Task 2 grant/queue boundaries.
- Produces: `WheelConfig`, `PaidEligibility`, `RewardBackfillResult`, `parse_paid_weekly_config()`, `evaluate_active_paid()`, `backfill_reward_account_states()`, and locked state helpers for Tasks 4-7.

- [ ] **Step 1: Write exact preset and eligibility matrix tests**

```python
def seed_reward_identity(
    session,
    *,
    now: datetime,
    account_status: str,
    sub_type: str,
    grant_source: str,
    grant_kind: str,
) -> str:
    account_id = str(uuid.uuid4())
    tg_id = 710000 + session.query(Account).count()
    session.add(
        Account(
            id=account_id,
            status=account_status,
            created_source="test",
            created_at=now,
            updated_at=now,
        )
    )
    session.add(
        User(
            tg_id=tg_id,
            account_id=account_id,
            uuid=str(uuid.uuid4()),
            sub_type=sub_type,
            current_plan_code="test",
            expiry_at=now + timedelta(days=30),
            is_active=True,
        )
    )
    session.add(
        EntitlementGrant(
            id=str(uuid.uuid4()),
            account_id=account_id,
            legacy_tg_id=tg_id,
            idempotency_key=f"eligibility-test:{account_id}",
            source=grant_source,
            status="active",
            grant_kind=grant_kind,
            plan_code="test",
            starts_at=now - timedelta(days=1),
            expires_at=now + timedelta(days=30),
            activated_at=now - timedelta(days=1),
            duration_days=31,
            provider="test",
            created_at=now - timedelta(days=1),
            updated_at=now,
        )
    )
    session.flush()
    return account_id


@pytest.mark.parametrize(
    ("patch", "code"),
    (
        ({"preset": "balanced"}, "wheel_preset_invalid"),
        ({"cooldown_hours": 167}, "wheel_cooldown_invalid"),
        ({"weights": [{"days": 1, "weight": 8999}, {"days": 3, "weight": 891}, {"days": 7, "weight": 100}, {"days": 30, "weight": 10}]}, "wheel_weights_invalid"),
        ({"weights": [{"days": 3, "weight": 890}, {"days": 1, "weight": 9000}, {"days": 7, "weight": 100}, {"days": 30, "weight": 10}]}, "wheel_outcome_order_invalid"),
    ),
)
def test_paid_weekly_v1_rejects_drift(patch, code):
    from portal_bot.rewards_service import InvalidWheelConfig, PAID_WEEKLY_V1, parse_paid_weekly_config

    payload = dict(PAID_WEEKLY_V1)
    payload.update(patch)
    with pytest.raises(InvalidWheelConfig, match=code):
        parse_paid_weekly_config(payload, explicit=True)


@pytest.mark.parametrize(
    ("account_status", "sub_type", "grant_source", "grant_kind", "expected_reason"),
    (
        ("active", "PAID", "provider_payment", "paid_access", "eligible"),
        ("active", "PAID", "compatibility_projection", "paid_access", "eligible"),
        ("active", "TRIAL", "trial_activation", "premium_trial", "active_paid_required"),
        ("active", "BONUS", "bonus_wheel", "premium_bonus", "active_paid_required"),
        ("active", "PAID", "bonus_calendar", "premium_bonus", "active_paid_required"),
        ("blocked", "PAID", "provider_payment", "paid_access", "account_inactive"),
    ),
)
def test_active_paid_predicate_is_server_owned(
    reward_session,
    now,
    account_status,
    sub_type,
    grant_source,
    grant_kind,
    expected_reason,
):
    account_id = seed_reward_identity(
        reward_session,
        now=now,
        account_status=account_status,
        sub_type=sub_type,
        grant_source=grant_source,
        grant_kind=grant_kind,
    )
    result = evaluate_active_paid(reward_session, account_id=account_id, now=now)
    assert result.reason == expected_reason
    assert result.eligible is (expected_reason == "eligible")
```

Add backfill coverage proving the maximum alias timestamp is retained, monthly streak fields are ignored, and unresolved account/merge-chain counts block readiness.

- [ ] **Step 2: Run and verify the new service is absent**

```powershell
& 'C:\Users\kiwun\AppData\Local\Temp\pokrov-support-agent-venv-20260715\Scripts\python.exe' -B -m pytest -p no:cacheprovider --basetemp "$env:TEMP\pokrov-rewards-$PID" portal_bot/tests/test_rewards_service.py tests/test_reward_migrations.py -q
```

Expected: collection fails because `portal_bot.rewards_service` does not exist.

- [ ] **Step 3: Add immutable domain constants and strict parser**

```python
import json
import secrets
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta


PAID_WEEKLY_V1: dict[str, object] = {
    "preset": "paid_weekly_v1",
    "cooldown_hours": 168,
    "weights": [
        {"days": 1, "weight": 9000},
        {"days": 3, "weight": 890},
        {"days": 7, "weight": 100},
        {"days": 30, "weight": 10},
    ],
}
PAID_GRANT_SOURCES = frozenset({"provider_payment", "compatibility_projection"})
WHEEL_SECTORS = (1, 3, 7, 30)
CALENDAR_MILESTONES = frozenset({7, 14, 21, 28})


class RewardDomainError(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class InvalidWheelConfig(RewardDomainError):
    pass


class RewardForbidden(RewardDomainError):
    pass


class RewardDisabled(RewardDomainError):
    def __init__(self, feature: str):
        self.feature = feature
        super().__init__("bonus_feature_disabled")


class RewardConflict(RewardDomainError):
    def __init__(
        self,
        code: str,
        *,
        next_allowed_at: datetime,
        last_reward_days: int | None,
    ) -> None:
        self.next_allowed_at = next_allowed_at
        self.last_reward_days = last_reward_days
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class WheelConfig:
    preset: str
    cooldown_hours: int
    outcomes: Sequence[tuple[int, int]]


@dataclass(frozen=True, slots=True)
class PaidEligibility:
    eligible: bool
    reason: str
    account_id: str
    legacy_tg_id: int | None


@dataclass(frozen=True, slots=True)
class WheelState:
    enabled: bool
    eligible: bool
    reason: str
    can_spin: bool
    sectors: Sequence[int]
    cooldown_hours: int
    last_spin_at: datetime | None
    next_spin_at: datetime | None
    last_reward_days: int | None
    sync_state: str


@dataclass(frozen=True, slots=True)
class CalendarState:
    enabled: bool
    eligible: bool
    reason: str
    checked_in_today: bool
    cycle_started_on: date | None
    cycle_day: int
    next_milestone: int | None
    achievements: Mapping[str, bool]
    sync_state: str


@dataclass(frozen=True, slots=True)
class RewardMutation:
    feature: str
    account_id: str
    grant_id: str | None
    reward_days: int
    sync_state: str
    wheel_last_spin_at: datetime | None = None
    wheel_next_spin_at: datetime | None = None
    calendar_cycle_started_on: date | None = None
    calendar_cycle_day: int = 0
    already_checked_in: bool = False
    achievements: Mapping[str, bool] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RewardHistoryEntry:
    durable_id: str
    source: str
    reward_days: int
    committed_at: datetime
    metadata: Mapping[str, object]


def reward_sync_state(job: NodeProvisioningJob | None) -> str:
    if job is None:
        return "not_required"
    if job.status == "completed":
        return "synced"
    if job.status == "manual_review":
        return "manual_review"
    return "sync_pending"


def validate_calendar_state(state: RewardAccountState) -> None:
    cycle_day = int(state.calendar_cycle_day or 0)
    if cycle_day == 0:
        if state.calendar_last_check_date is None and state.calendar_cycle_started_on is None:
            return
        raise RewardDomainError("calendar_state_invalid")
    if not 1 <= cycle_day <= 28:
        raise RewardDomainError("calendar_state_invalid")
    if state.calendar_last_check_date is None or state.calendar_cycle_started_on is None:
        raise RewardDomainError("calendar_state_invalid")
    expected_start = state.calendar_last_check_date - timedelta(days=cycle_day - 1)
    if state.calendar_cycle_started_on != expected_start:
        raise RewardDomainError("calendar_state_invalid")


def _locked_reward_state(session, *, account_id: str, now: datetime) -> RewardAccountState:
    state = (
        session.query(RewardAccountState)
        .filter(RewardAccountState.account_id == account_id)
        .with_for_update()
        .one_or_none()
    )
    if state is None:
        state = RewardAccountState(
            account_id=account_id,
            calendar_cycle_day=0,
            created_at=now,
            updated_at=now,
        )
        session.add(state)
        session.flush()
    validate_calendar_state(state)
    return state


def parse_paid_weekly_config(payload: Mapping[str, object], *, explicit: bool) -> WheelConfig:
    candidate = dict(payload)
    if candidate.get("preset") != "paid_weekly_v1":
        raise InvalidWheelConfig("wheel_preset_invalid")
    if candidate.get("cooldown_hours") != 168:
        raise InvalidWheelConfig("wheel_cooldown_invalid")
    raw = candidate.get("weights")
    if not isinstance(raw, list) or [row.get("days") for row in raw if isinstance(row, dict)] != [1, 3, 7, 30]:
        raise InvalidWheelConfig("wheel_outcome_order_invalid")
    outcomes = tuple((int(row["days"]), int(row["weight"])) for row in raw if isinstance(row, dict))
    if outcomes != ((1, 9000), (3, 890), (7, 100), (30, 10)) or sum(weight for _days, weight in outcomes) != 10000:
        raise InvalidWheelConfig("wheel_weights_invalid")
    return WheelConfig(preset="paid_weekly_v1", cooldown_hours=168, outcomes=outcomes)


def evaluate_active_paid(session, *, account_id: str, now: datetime) -> PaidEligibility:
    try:
        account_key = resolve_canonical_account_id(session, account_id=account_id)
    except ValueError as exc:
        return PaidEligibility(False, str(exc), str(account_id), None)
    account = (
        session.query(Account)
        .filter(Account.id == account_key)
        .with_for_update()
        .one_or_none()
    )
    if account is None:
        return PaidEligibility(False, "account_not_found", account_key, None)
    if account.status != "active" or account.merged_into_account_id is not None:
        return PaidEligibility(False, "account_inactive", account_key, None)
    rebuild_account_entitlement_projection(session, account_id=account_key, now=now)
    paid_users = (
        session.query(User)
        .filter(
            User.account_id == account_key,
            User.is_active.is_(True),
            User.sub_type == "PAID",
            User.expiry_at.isnot(None),
            User.expiry_at > now,
        )
        .order_by(User.tg_id.asc())
        .with_for_update()
        .all()
    )
    paid_grant = (
        session.query(EntitlementGrant)
        .filter(
            EntitlementGrant.account_id == account_key,
            EntitlementGrant.status.in_(["active", "grace"]),
            EntitlementGrant.reversed_at.is_(None),
            EntitlementGrant.grant_kind == "paid_access",
            EntitlementGrant.source.in_(sorted(PAID_GRANT_SOURCES)),
            EntitlementGrant.starts_at.isnot(None),
            EntitlementGrant.starts_at <= now,
            EntitlementGrant.expires_at.isnot(None),
            EntitlementGrant.expires_at > now,
        )
        .with_for_update()
        .first()
    )
    if not paid_users or paid_grant is None:
        return PaidEligibility(False, "active_paid_required", account_key, None)
    return PaidEligibility(True, "eligible", account_key, int(paid_users[0].tg_id))
```

This resolves a merge source to its target, then locks the active canonical account, compatibility projection, and current paid ledger. Reward grants never satisfy the paid-ledger query.

Add parameterized tests for `validate_calendar_state()` covering empty day zero, forbidden dates on day zero, missing dates on a positive day, and the exact `last_check - (cycle_day - 1)` equation. Call the validator after every state load, transition, backfill, and merge; corrupted state fails closed instead of being normalized silently.

- [ ] **Step 4: Add deterministic backfill with readiness counters**

`backfill_reward_account_states()` must return this exact result and update only `wheel_last_spin_at`:

```python
@dataclass(frozen=True, slots=True)
class RewardBackfillResult:
    canonical_accounts: int
    states_created: int
    wheel_sources_seen: int
    wheel_states_updated: int
    unresolved_users: int
    invalid_merge_chains: int

    @property
    def ready(self) -> bool:
        return self.unresolved_users == 0 and self.invalid_merge_chains == 0
```

For each canonical account, lock/create one state, calculate `max(user.last_wheel_spin)` across aliases, and never read or write `streak_months` or `streak_last_check`. If `ready` is false, return counts without marking rollout ready; do not invent accounts.

- [ ] **Step 5: Run domain configuration, eligibility, and backfill tests**

```powershell
& 'C:\Users\kiwun\AppData\Local\Temp\pokrov-support-agent-venv-20260715\Scripts\python.exe' -B -m pytest -p no:cacheprovider --basetemp "$env:TEMP\pokrov-rewards-$PID" portal_bot/tests/test_rewards_service.py tests/test_reward_migrations.py tests/test_account_foundation.py -q
```

Expected: all selected tests pass; no test observes monthly streak-field mutation.

- [ ] **Step 6: Commit the reward foundation**

```powershell
git add -- portal_bot/rewards_service.py portal_bot/tests/test_rewards_service.py tests/test_reward_migrations.py
git commit -m "feat(rewards): add paid reward authority"
```

---

### Task 4: Implement the Weekly Wheel Transaction

**Files:**

- Modify: `portal_bot/rewards_service.py`
- Modify: `portal_bot/tests/test_rewards_service.py`

**Interfaces:**

- Consumes: `parse_paid_weekly_config()`, `evaluate_active_paid()`, `grant_internal_bonus_days()`, and `enqueue_reward_entitlement_sync()`.
- Produces: `WheelState`, `RewardMutation`, `get_wheel_state()`, and `spin_wheel()` for API and Telegram.

- [ ] **Step 1: Write deterministic boundary, cooldown, and double-spin tests**

```python
@pytest.mark.parametrize(
    ("draw", "days"),
    ((0, 1), (8999, 1), (9000, 3), (9889, 3), (9890, 7), (9989, 7), (9990, 30), (9999, 30)),
)
def test_wheel_secure_draw_boundaries(paid_reward_session, now, draw, days):
    result = spin_wheel(
        paid_reward_session,
        account_id=PAID_ACCOUNT_ID,
        enabled=True,
        config_payload=PAID_WEEKLY_V1,
        now=now,
        randbelow=lambda upper: draw if upper == 10000 else -1,
    )
    assert result.reward_days == days
    assert result.sync_state == "sync_pending"


def test_wheel_retry_returns_authoritative_cooldown_without_second_draw(paid_reward_session, now):
    draws = iter((9999,))
    first = spin_wheel(
        paid_reward_session,
        account_id=PAID_ACCOUNT_ID,
        enabled=True,
        config_payload=PAID_WEEKLY_V1,
        now=now,
        randbelow=lambda upper: next(draws),
    )
    with pytest.raises(RewardConflict) as exc:
        spin_wheel(
            paid_reward_session,
            account_id=PAID_ACCOUNT_ID,
            enabled=True,
            config_payload=PAID_WEEKLY_V1,
            now=now + timedelta(seconds=1),
            randbelow=lambda upper: next(draws),
        )
    assert exc.value.code == "wheel_cooldown_active"
    assert exc.value.last_reward_days == first.reward_days
    assert exc.value.next_allowed_at == now + timedelta(hours=168)
```

Add two-session concurrency coverage asserting one `bonus_wheel` grant, one job, and one winning mutation. PostgreSQL uses `FOR UPDATE`; SQLite coverage must use the repository's serialized write fixture rather than claiming row-lock parity.

- [ ] **Step 2: Run and verify wheel entry points are absent**

```powershell
& 'C:\Users\kiwun\AppData\Local\Temp\pokrov-support-agent-venv-20260715\Scripts\python.exe' -B -m pytest -p no:cacheprovider --basetemp "$env:TEMP\pokrov-rewards-$PID" portal_bot/tests/test_rewards_service.py -k "wheel" -q
```

Expected: failure importing `spin_wheel` or `get_wheel_state`.

- [ ] **Step 3: Implement the single locked wheel path**

The mutation order must be encoded exactly as follows:

```python
def _reward_days_for_draw(config: WheelConfig, draw: int) -> int:
    if not 0 <= draw < 10000:
        raise RewardDomainError("wheel_draw_invalid")
    cursor = 0
    for days, weight in config.outcomes:
        cursor += weight
        if draw < cursor:
            return days
    raise RewardDomainError("wheel_draw_invalid")


def _last_wheel_reward_days(session, state: RewardAccountState) -> int | None:
    if not state.wheel_last_grant_id:
        return None
    grant = session.get(EntitlementGrant, state.wheel_last_grant_id)
    if grant is None or grant.source != "bonus_wheel":
        return None
    return int(grant.duration_days or 0) or None


def spin_wheel(
    session,
    *,
    account_id: str,
    enabled: bool,
    config_payload: Mapping[str, object] | None,
    now: datetime,
    randbelow: Callable[[int], int] = secrets.randbelow,
) -> RewardMutation:
    if not enabled:
        raise RewardDisabled("wheel")
    config = (
        parse_paid_weekly_config(PAID_WEEKLY_V1, explicit=False)
        if config_payload is None
        else parse_paid_weekly_config(config_payload, explicit=True)
    )
    eligibility = evaluate_active_paid(session, account_id=account_id, now=now)
    if not eligibility.eligible:
        raise RewardForbidden(eligibility.reason)
    state = _locked_reward_state(session, account_id=eligibility.account_id, now=now)
    next_spin_at = state.wheel_last_spin_at + timedelta(hours=168) if state.wheel_last_spin_at else None
    if next_spin_at is not None and next_spin_at > now:
        raise RewardConflict(
            "wheel_cooldown_active",
            next_allowed_at=next_spin_at,
            last_reward_days=_last_wheel_reward_days(session, state),
        )
    draw = randbelow(10000)
    reward_days = _reward_days_for_draw(config, draw)
    event_id = str(uuid.uuid4())
    grant = grant_internal_bonus_days(
        session,
        account_id=eligibility.account_id,
        source="bonus_wheel",
        plan_code="reward_wheel",
        idempotency_key=f"reward-wheel:v1:{event_id}",
        days=reward_days,
        legacy_tg_id=eligibility.legacy_tg_id,
        metadata={"version": 1, "preset": config.preset, "reward_days": reward_days, "committed_at": now.isoformat()},
        now=now,
    )
    job = enqueue_reward_entitlement_sync(
        session,
        account_id=eligibility.account_id,
        entitlement_grant_id=grant.id,
        now=now,
    )
    state.wheel_last_spin_at = now
    state.wheel_last_grant_id = grant.id
    state.updated_at = now
    session.flush()
    return RewardMutation(
        feature="wheel",
        account_id=eligibility.account_id,
        grant_id=grant.id,
        reward_days=reward_days,
        sync_state=reward_sync_state(job),
        wheel_last_spin_at=now,
        wheel_next_spin_at=now + timedelta(hours=config.cooldown_hours),
    )
```

`get_wheel_state()` must return `[1, 3, 7, 30]`, never the weights; an invalid explicit setting returns `enabled=false`, `reason=wheel_config_invalid`, and no sectors. Log one secret-free operator event containing only event code, preset name, and validation code; never log the stored JSON. Add a `caplog` assertion for that bounded event.

- [ ] **Step 4: Run all wheel service tests**

```powershell
& 'C:\Users\kiwun\AppData\Local\Temp\pokrov-support-agent-venv-20260715\Scripts\python.exe' -B -m pytest -p no:cacheprovider --basetemp "$env:TEMP\pokrov-rewards-$PID" portal_bot/tests/test_rewards_service.py -k "wheel or eligibility" -q
```

Expected: all selected tests pass with deterministic boundary coverage and one durable grant/job per event.

- [ ] **Step 5: Commit the wheel domain**

```powershell
git add -- portal_bot/rewards_service.py portal_bot/tests/test_rewards_service.py
git commit -m "feat(rewards): centralize paid weekly wheel"
```

---

### Task 5: Implement Calendar, Achievements, and Unified History

**Files:**

- Modify: `portal_bot/rewards_service.py`
- Modify: `portal_bot/tests/test_rewards_service.py`

**Interfaces:**

- Consumes: Task 3 paid eligibility/state and Task 2 grant/queue boundaries.
- Produces: `CalendarState`, `checkin_calendar()`, `get_calendar_state()`, and `get_reward_history()` for Tasks 7-8.

- [ ] **Step 1: Write UTC, milestone, reset, and history tests**

```python
def test_calendar_awards_only_four_milestones_and_resets_after_day_twenty_eight(paid_reward_session, now):
    awarded = []
    for offset in range(28):
        result = checkin_calendar(
            paid_reward_session,
            account_id=PAID_ACCOUNT_ID,
            enabled=True,
            now=now + timedelta(days=offset),
        )
        if result.reward_days:
            awarded.append((result.calendar_cycle_day, result.reward_days))
    assert awarded == [(7, 1), (14, 1), (21, 1), (28, 1)]
    next_cycle = checkin_calendar(
        paid_reward_session,
        account_id=PAID_ACCOUNT_ID,
        enabled=True,
        now=now + timedelta(days=28),
    )
    assert next_cycle.calendar_cycle_day == 1
    assert next_cycle.reward_days == 0


def test_calendar_same_utc_date_is_idempotent(paid_reward_session, now):
    first = checkin_calendar(paid_reward_session, account_id=PAID_ACCOUNT_ID, enabled=True, now=now)
    second = checkin_calendar(
        paid_reward_session,
        account_id=PAID_ACCOUNT_ID,
        enabled=True,
        now=now.replace(hour=23, minute=59),
    )
    assert first.calendar_cycle_day == second.calendar_cycle_day == 1
    assert second.already_checked_in is True
    assert second.grant_id is None


def test_calendar_gap_resets_cycle_but_achievements_remain_unlocked(paid_reward_session, now):
    for offset in range(7):
        checkin_calendar(paid_reward_session, account_id=PAID_ACCOUNT_ID, enabled=True, now=now + timedelta(days=offset))
    reset = checkin_calendar(
        paid_reward_session,
        account_id=PAID_ACCOUNT_ID,
        enabled=True,
        now=now + timedelta(days=9),
    )
    assert reset.calendar_cycle_day == 1
    assert reset.achievements["first_checkin"] is True
    assert reset.achievements["streak_7"] is True
```

Add history coverage with one legacy `RewardClaim`, one wheel grant, and one calendar grant; assert three distinct rows labelled by durable source and no date/value deduplication.

- [ ] **Step 2: Run and verify calendar entry points are absent**

```powershell
& 'C:\Users\kiwun\AppData\Local\Temp\pokrov-support-agent-venv-20260715\Scripts\python.exe' -B -m pytest -p no:cacheprovider --basetemp "$env:TEMP\pokrov-rewards-$PID" portal_bot/tests/test_rewards_service.py -k "calendar or history or achievement" -q
```

Expected: failure importing calendar/history entry points.

- [ ] **Step 3: Implement the calendar transition and stable milestone key**

```python
def _next_calendar_position(state: RewardAccountState, today: date) -> tuple[date, int]:
    if state.calendar_last_check_date == today:
        return state.calendar_cycle_started_on or today, int(state.calendar_cycle_day or 1)
    consecutive = state.calendar_last_check_date == today - timedelta(days=1)
    if consecutive and int(state.calendar_cycle_day or 0) < 28:
        return state.calendar_cycle_started_on or today, int(state.calendar_cycle_day or 0) + 1
    return today, 1


def _calendar_grant_key(*, origin_account_id: str, cycle_start: date, milestone: int) -> str:
    return f"reward-calendar:v1:{origin_account_id}:{cycle_start.isoformat()}:{milestone}"


def _reward_job_for_grant(session, grant_id: str | None) -> NodeProvisioningJob | None:
    if not grant_id:
        return None
    return (
        session.query(NodeProvisioningJob)
        .filter(NodeProvisioningJob.entitlement_grant_id == grant_id)
        .one_or_none()
    )


def _calendar_grant_for_position(
    session,
    *,
    account_id: str,
    cycle_start: date,
    milestone: int,
) -> EntitlementGrant | None:
    rows = (
        session.query(EntitlementGrant)
        .filter(
            EntitlementGrant.account_id == account_id,
            EntitlementGrant.source == "bonus_calendar",
        )
        .order_by(EntitlementGrant.created_at.desc(), EntitlementGrant.id.desc())
        .limit(64)
        .all()
    )
    for row in rows:
        try:
            metadata = json.loads(row.metadata_json or "{}")
        except (TypeError, json.JSONDecodeError):
            continue
        if not isinstance(metadata, dict):
            continue
        if metadata.get("cycle_start") == cycle_start.isoformat() and metadata.get("milestone") == milestone:
            return row
    return None


def checkin_calendar(
    session,
    *,
    account_id: str,
    enabled: bool,
    now: datetime,
) -> RewardMutation:
    if not enabled:
        raise RewardDisabled("calendar")
    eligibility = evaluate_active_paid(session, account_id=account_id, now=now)
    if not eligibility.eligible:
        raise RewardForbidden(eligibility.reason)
    state = _locked_reward_state(session, account_id=eligibility.account_id, now=now)
    today = now.date()
    if state.calendar_last_check_date == today:
        grant = None
        if int(state.calendar_cycle_day or 0) in CALENDAR_MILESTONES and state.calendar_cycle_started_on:
            grant = _calendar_grant_for_position(
                session,
                account_id=eligibility.account_id,
                cycle_start=state.calendar_cycle_started_on,
                milestone=int(state.calendar_cycle_day),
            )
        job = _reward_job_for_grant(session, grant.id if grant else None)
        return RewardMutation(
            feature="calendar",
            account_id=eligibility.account_id,
            grant_id=grant.id if grant else None,
            reward_days=int(grant.duration_days or 0) if grant else 0,
            sync_state=reward_sync_state(job),
            calendar_cycle_started_on=state.calendar_cycle_started_on,
            calendar_cycle_day=int(state.calendar_cycle_day or 0),
            already_checked_in=True,
            achievements={
                "first_checkin": state.calendar_first_checkin_at is not None,
                "streak_7": state.calendar_streak_7_unlocked_at is not None,
            },
        )
    cycle_start, cycle_day = _next_calendar_position(state, today)
    state.calendar_cycle_started_on = cycle_start
    state.calendar_cycle_day = cycle_day
    state.calendar_last_check_date = today
    if state.calendar_first_checkin_at is None:
        state.calendar_first_checkin_at = now
    if cycle_day >= 7 and state.calendar_streak_7_unlocked_at is None:
        state.calendar_streak_7_unlocked_at = now
    grant = None
    job = None
    if cycle_day in CALENDAR_MILESTONES:
        grant_key = _calendar_grant_key(
            origin_account_id=eligibility.account_id,
            cycle_start=cycle_start,
            milestone=cycle_day,
        )
        grant = grant_internal_bonus_days(
            session,
            account_id=eligibility.account_id,
            source="bonus_calendar",
            plan_code="reward_calendar",
            idempotency_key=grant_key,
            days=1,
            legacy_tg_id=eligibility.legacy_tg_id,
            metadata={
                "version": 1,
                "origin_account_id": eligibility.account_id,
                "cycle_start": cycle_start.isoformat(),
                "milestone": cycle_day,
                "reward_days": 1,
                "committed_at": now.isoformat(),
            },
            now=now,
        )
        job = enqueue_reward_entitlement_sync(
            session,
            account_id=eligibility.account_id,
            entitlement_grant_id=grant.id,
            now=now,
        )
    state.updated_at = now
    validate_calendar_state(state)
    session.flush()
    return RewardMutation(
        feature="calendar",
        account_id=eligibility.account_id,
        grant_id=grant.id if grant else None,
        reward_days=int(grant.duration_days or 0) if grant else 0,
        sync_state=reward_sync_state(job),
        calendar_cycle_started_on=cycle_start,
        calendar_cycle_day=cycle_day,
        already_checked_in=False,
        achievements={
            "first_checkin": True,
            "streak_7": state.calendar_streak_7_unlocked_at is not None,
        },
    )
```

The backend `now` is the only date source. Use the canonical account id locked at the award event as `origin_account_id` in both the stable grant key and metadata; later account merges move the row without rewriting that identity. Add a same-day day-7 retry test proving the original grant id and one pending/synced job are returned without inserting another row.

- [ ] **Step 4: Add unified history and state projection**

`get_reward_history()` must collect legacy `RewardClaim` rows for every compatibility `tg_id` currently owned by the canonical account, then combine them with its account grants. Sort by committed time descending and emit `durable_id` as `legacy_reward_claim:<id>` or `account_entitlement_grant:<uuid>`. Parse only bounded known metadata, use `duration_days` as the authoritative fallback, and never merge entries merely because date and reward size match.

- [ ] **Step 5: Run the complete reward-domain suite**

```powershell
& 'C:\Users\kiwun\AppData\Local\Temp\pokrov-support-agent-venv-20260715\Scripts\python.exe' -B -m pytest -p no:cacheprovider --basetemp "$env:TEMP\pokrov-rewards-$PID" portal_bot/tests/test_rewards_service.py -q
```

Expected: all reward tests pass, including day 28 readability, next-day reset, four-day cap, write-once achievements, and legacy/new history.

- [ ] **Step 6: Commit calendar and history**

```powershell
git add -- portal_bot/rewards_service.py portal_bot/tests/test_rewards_service.py
git commit -m "feat(rewards): add paid activity calendar"
```

---

### Task 6: Process Reward Sync Jobs and Fence Account Merges

**Files:**

- Modify: `portal_bot/node_provisioning_service.py:23-59,144-173,238-330,485-565`
- Modify: `portal_bot/account_foundation_service.py:946-1040`
- Modify: `portal_bot/rewards_service.py`
- Modify: `tests/test_node_provisioning_service.py`
- Modify: `tests/test_account_foundation.py`

**Interfaces:**

- Consumes: Task 1 job ownership columns and Task 3-5 account state/grants.
- Produces: worker support for `reward_entitlement_sync` and `reconcile_reward_merge()` with lock-token invalidation.

- [ ] **Step 1: Write retry, finalize-fence, and merge tests**

```python
def test_reward_sync_finalize_requires_same_token_and_canonical_account(session, seeded_reward_job, now):
    claim = _claim_next_job(session, now=now, max_attempts=3)
    prepared = _prepare_job(session, claim)
    seeded_reward_job.account_id = TARGET_ACCOUNT_ID
    seeded_reward_job.status = "queued"
    seeded_reward_job.lock_token = None
    session.flush()
    assert _finalize_success(session, claim=claim, prepared=prepared, outcome="synced", now=now) == "claim_lost"
    assert seeded_reward_job.completed_at is None


def test_account_merge_keeps_strongest_reward_state_and_requeues_running_job(session, now):
    reconcile_reward_merge(
        session,
        source_account_id=SOURCE_ACCOUNT_ID,
        target_account_id=TARGET_ACCOUNT_ID,
        now=now,
    )
    state = session.get(RewardAccountState, TARGET_ACCOUNT_ID)
    job = session.query(NodeProvisioningJob).filter_by(entitlement_grant_id=REWARD_GRANT_ID).one()
    assert state.wheel_last_spin_at == LATER_WHEEL_AT
    assert state.wheel_last_grant_id == LATER_WHEEL_GRANT_ID
    assert state.calendar_cycle_day == 14
    assert state.calendar_first_checkin_at == EARLIEST_FIRST_CHECKIN_AT
    assert job.account_id == TARGET_ACCOUNT_ID
    assert job.status == "queued"
    assert job.lock_token is None
```

Add parameterized worker tests for successful completion, bounded retry/backoff, and terminal `manual_review` after the existing maximum attempt count.

- [ ] **Step 2: Run and verify the worker rejects the new job type**

```powershell
& 'C:\Users\kiwun\AppData\Local\Temp\pokrov-support-agent-venv-20260715\Scripts\python.exe' -B -m pytest -p no:cacheprovider --basetemp "$env:TEMP\pokrov-rewards-$PID" tests/test_node_provisioning_service.py tests/test_account_foundation.py -k "reward" -q
```

Expected: failure with `job_type_unsupported` or missing `reconcile_reward_merge`.

- [ ] **Step 3: Extend claimed/prepared data and canonical prepare**

Add `reward_entitlement_sync` to `SUPPORTED_JOB_TYPES`. Replace the prepared-job declaration with fields that support both existing single-user work and account reward sync:

```python
@dataclass(frozen=True)
class PreparedJob:
    job_id: int
    job_type: str
    tg_id: int | None = None
    key_id: int | None = None
    client_uuid: str = ""
    panel_email: str = ""
    sub_id: str = ""
    account_id: str | None = None
    entitlement_grant_id: str | None = None
    reward_tg_ids: Sequence[int] = ()
    source_node_code: str | None = None
    source_role: str | None = None
    target_node_code: str | None = None
    target_role: str | None = None
    source_bindings: Sequence[tuple[str, str]] = ()
    replacement_key_uuid: str | None = None
    superseded: bool = False
```

For reward jobs, `_prepare_job()` must call `resolve_canonical_account_id()`, verify the grant belongs to it, collect active compatibility users under that account, and return their Telegram ids without exposing subscription URLs. Extend `_claim_was_superseded()` with a reward branch that opens a fresh session, verifies the original running status/token, resolves `job.account_id` again, and compares it with `prepared.account_id`.

In `_execute_panel()`, invoke `superseded_check()` immediately before the first reward external call and again before each alias. If it reports stale ownership, return `"superseded"` without another call. Otherwise call `await panel.update_client_traffic(tg_id, 0)` for each collected compatibility user. Require every call to return true; a false result or exception raises `ProvisioningError("reward_sync_failed")` so the existing retry/backoff/manual-review path owns recovery.

- [ ] **Step 4: Fence finalization and implement deterministic merge reconciliation**

Before reward finalization, lock the job and resolve its canonical account again. Finalize only when all three values still match: `status == "running"`, the original lock token, and `job.account_id == prepared.account_id == canonical_account_id`.

`reconcile_reward_merge()` must:

```python
def _calendar_rank(state: RewardAccountState) -> tuple[date, int, int]:
    last_check = state.calendar_last_check_date or date.min
    cycle_day = int(state.calendar_cycle_day or 0)
    cycle_start_rank = -(state.calendar_cycle_started_on or date.max).toordinal()
    return last_check, cycle_day, cycle_start_rank
```

- keep the later wheel time and its matching grant pointer;
- keep the calendar row with later last check, then greater day, then earlier cycle start;
- retain the earliest non-null achievement timestamps;
- move pending/retrying/running reward jobs to the target, clear `locked_at/lock_token`, set `status="queued"`, and set `next_run_at=now`;
- delete the losing state only after the target state is flushed;
- let the existing generic account-foundation path move `EntitlementGrant` rows without changing idempotency keys.

Call this helper inside `_move_account_owned_rows()` before generic grant reassignment.

- [ ] **Step 5: Run worker and account-foundation regressions**

```powershell
& 'C:\Users\kiwun\AppData\Local\Temp\pokrov-support-agent-venv-20260715\Scripts\python.exe' -B -m pytest -p no:cacheprovider --basetemp "$env:TEMP\pokrov-rewards-$PID" tests/test_node_provisioning_service.py tests/test_account_foundation.py portal_bot/tests/test_rewards_service.py -q
```

Expected: all selected tests pass, including the stale-worker finalize rejection and rerunnable merge.

- [ ] **Step 6: Commit durable sync and merge fencing**

```powershell
git add -- portal_bot/node_provisioning_service.py portal_bot/account_foundation_service.py portal_bot/rewards_service.py tests/test_node_provisioning_service.py tests/test_account_foundation.py
git commit -m "feat(rewards): reconcile grants through durable jobs"
```

---

### Task 7: Replace API and Telegram Reward Mutators with Thin Adapters

**Files:**

- Modify: `portal_bot/api.py:672-790,13476-14030,17145-17195`
- Modify: `portal_bot/bot.py:2468-2515,4826-5145`
- Modify: `portal_bot/channel_bonus_service.py:1-170`
- Modify: `portal_bot/tests/test_app_first_api.py:1522-1668`
- Modify: `tests/test_api_auth_and_tickets.py:4655-4745`
- Modify: `tests/test_bot_paywall.py`

**Interfaces:**

- Consumes: all Task 3-6 reward-service entry points.
- Produces: stable HTTP/bot behavior, strict admin config, public sectors without weights, and separate `offer_days`/`claimed_days`.

- [ ] **Step 1: Rewrite failing adapter contract tests**

```python
def test_paid_reward_api_exposes_sectors_without_weights(app_client, paid_app_session):
    response = app_client.get("/api/bonuses/wheel/state", headers=paid_app_session)
    assert response.status_code == 200
    payload = response.json()
    assert payload["enabled"] is True
    assert payload["eligible"] is True
    assert payload["sectors"] == [1, 3, 7, 30]
    assert "weights" not in payload
    assert "probability" not in json.dumps(payload).lower()


@pytest.mark.parametrize("sub_type", ("FREE", "TRIAL", "BONUS"))
def test_non_paid_reward_mutation_is_forbidden(app_client, app_session_for_type, sub_type):
    response = app_client.post("/api/bonuses/wheel/spin", headers=app_session_for_type(sub_type))
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "active_paid_required"


def test_channel_bonus_separates_current_offer_from_grandfathered_claim(app_client, grandfathered_session):
    payload = app_client.get("/api/bonuses", headers=grandfathered_session).json()["channel"]
    assert payload["offer_days"] == 5
    assert payload["claimed_days"] == 10
```

Add bot tests proving a disabled callback never calls `spin_wheel()`, aliases share the same cooldown, and trial users are rejected.

- [ ] **Step 2: Run adapter tests and verify old behavior fails**

```powershell
& 'C:\Users\kiwun\AppData\Local\Temp\pokrov-support-agent-venv-20260715\Scripts\python.exe' -B -m pytest -p no:cacheprovider --basetemp "$env:TEMP\pokrov-rewards-$PID" portal_bot/tests/test_app_first_api.py tests/test_api_auth_and_tickets.py tests/test_bot_paywall.py -k "wheel or calendar or channel_bonus" -q
```

Expected: failures show trial eligibility, direct `User` mutation/legacy claims, Telegram flag bypass, or missing offer/claim separation.

- [ ] **Step 3: Replace FastAPI reward helpers and routes**

Delete reward selection, direct expiry extension, and calendar streak logic from `portal_bot/api.py`. Keep route paths stable and map service exceptions exactly:

```python
def _reward_http_error(exc: RewardDomainError) -> HTTPException:
    if isinstance(exc, RewardForbidden):
        return HTTPException(status_code=403, detail={"code": "active_paid_required"})
    if isinstance(exc, RewardConflict):
        return HTTPException(
            status_code=409,
            detail={"code": exc.code, "next_spin_at": _iso(exc.next_allowed_at), "last_reward_days": exc.last_reward_days},
        )
    if isinstance(exc, RewardDisabled):
        return HTTPException(
            status_code=403,
            detail={"code": "bonus_feature_disabled", "feature": exc.feature},
        )
    return HTTPException(status_code=503, detail={"code": "reward_state_unavailable"})
```

Read routes commit no mutation beyond the existing projection rebuild contract. Mutation routes open one DB transaction, call the service once, commit once, and return the committed `reward_days`, `grant_id`, `sync_state`, and authoritative state. Remove the one-shot API `_sync_user_after_paid_bonus` call from reward routes.

- [ ] **Step 4: Enforce exact admin configuration and Telegram parity**

Set the API fallback to `PAID_WEEKLY_V1`. Admin writes call `parse_paid_weekly_config(payload, explicit=True)` before storing JSON and return `400 wheel_config_invalid` on any drift.

Telegram obtains the canonical account, passes `BONUS_WHEEL_ENABLED` to the same service, and renders returned state/result only. Remove its local random draw, direct `last_wheel_spin` update, direct expiry mutation, and one-shot panel sync. The adapters may maintain legacy `first_wheel`, `first_checkin`, and `streak_7` achievement rows as compatibility projections in the same transaction, but reward state never reads those rows. Calendar remains WebApp/API-only unless a separately approved bot surface is added.

- [ ] **Step 5: Run backend/API/bot gates**

```powershell
& 'C:\Users\kiwun\AppData\Local\Temp\pokrov-support-agent-venv-20260715\Scripts\python.exe' -B -m pytest -p no:cacheprovider --basetemp "$env:TEMP\pokrov-rewards-$PID" portal_bot/tests/test_rewards_service.py portal_bot/tests/test_app_first_api.py portal_bot/tests/test_app_first_service.py tests/test_api_auth_and_tickets.py tests/test_bot_paywall.py tests/test_subscription_preview_api.py -q
```

Expected: all selected tests pass; `rg.exe -n "random\.|last_wheel_spin\s*=|streak_months\s*=|streak_last_check\s*=" portal_bot/api.py portal_bot/bot.py` returns no active reward mutation path.

- [ ] **Step 6: Commit transport adapters**

```powershell
git add -- portal_bot/api.py portal_bot/bot.py portal_bot/channel_bonus_service.py portal_bot/tests/test_app_first_api.py tests/test_api_auth_and_tickets.py tests/test_bot_paywall.py
git commit -m "refactor(rewards): share api and telegram authority"
```

---

### Task 8: Build the Fail-Closed WebApp Rewards Surface

**Files:**

- Modify: `webapp/src/lib/api.ts:573-625,2189-2210`
- Create: `webapp/src/components/cabinet/bonus-wheel.tsx`
- Create: `webapp/src/app/(dashboard)/rewards/page.tsx`
- Modify: `webapp/src/components/cabinet-shell.tsx`
- Modify: `webapp/src/app/(dashboard)/page.tsx`
- Create: `webapp/e2e/rewards.spec.ts`
- Modify: `webapp/README.md`

**Interfaces:**

- Consumes: Task 7 state/mutation payloads.
- Produces: independently degraded wheel/calendar cards and server-authoritative refresh behavior.

- [ ] **Step 1: Add failing E2E cases for every fail-closed state**

```typescript
test("keeps calendar usable when wheel state fails", async ({ page }) => {
  await registerRewardMocks(page, { wheelStatus: 503, calendarDay: 6 });
  await page.goto("/rewards/");
  await expect(page.getByText("Колесо временно недоступно")).toBeVisible();
  await expect(page.getByRole("button", { name: "Отметить день" })).toBeEnabled();
});

test("does not invent sectors or animate an unknown committed reward", async ({ page }) => {
  await registerRewardMocks(page, { sectors: [1, 3, 7], spinRewardDays: 30 });
  await page.goto("/rewards/");
  await page.getByRole("button", { name: "Крутить колесо" }).click();
  await expect(page.getByText("Начислено +30 дней")).toBeVisible();
  await expect(page.getByText("Не удалось синхронизировать сектора")).toBeVisible();
  await expect(page.locator('[data-spinning="true"]')).toHaveCount(0);
});

test("renders one sector as a guaranteed reward card", async ({ page }) => {
  await registerRewardMocks(page, { sectors: [1] });
  await page.goto("/rewards/");
  await expect(page.getByText("Гарантированная награда: +1 день")).toBeVisible();
  await expect(page.locator("svg[data-wheel]")).toHaveCount(0);
});
```

Add cases for missing/duplicate/non-positive/excessive sectors, free/trial/expired ineligibility, disabled features, same-day calendar response, and dashboard/entitlement refetch after success.

- [ ] **Step 2: Run the reward E2E and verify the page is absent**

```powershell
Set-Location webapp
npm.cmd run test:e2e:cabinet -- --grep "rewards"
Set-Location ..
```

Expected: failure because `/rewards/` and reward mocks/components do not exist.

- [ ] **Step 3: Add closed TypeScript contracts and endpoint functions**

```typescript
export type RewardSyncState = "not_required" | "sync_pending" | "synced" | "manual_review";

export type BonusWheelState = {
  enabled: boolean;
  eligible: boolean;
  reason: string;
  can_spin: boolean;
  sectors: number[];
  cooldown_hours: number;
  last_spin_at: string | null;
  next_spin_at: string | null;
  last_reward_days: number | null;
  sync_state: RewardSyncState;
};

export type BonusCalendarState = {
  enabled: boolean;
  eligible: boolean;
  reason: string;
  checked_in_today: boolean;
  cycle_started_on: string | null;
  cycle_day: number;
  next_milestone: number | null;
  achievements: { first_checkin: boolean; streak_7: boolean };
  sync_state: RewardSyncState;
};

export function fetchBonusWheelState(): Promise<BonusWheelState> {
  return apiFetch("/api/bonuses/wheel/state");
}

export function spinBonusWheel(): Promise<BonusWheelState & { reward_days: number; grant_id: string }> {
  return apiFetch("/api/bonuses/wheel/spin", { method: "POST" });
}
```

Add matching calendar/history types and methods with the exact API route names.

- [ ] **Step 4: Implement fail-closed sector validation and independent loading**

```typescript
export function validateRewardSectors(raw: unknown): number[] | null {
  if (!Array.isArray(raw) || raw.length === 0 || raw.length > 12) return null;
  const sectors = raw.map(Number);
  if (sectors.some((value) => !Number.isInteger(value) || value <= 0 || value > 365)) return null;
  if (new Set(sectors).size !== sectors.length) return null;
  return sectors;
}
```

Use `Promise.allSettled` so one endpoint failure cannot hide another feature. Zero/invalid sectors disable interaction; one sector renders a card; two or more render equal visual geometry with the explicit text “Размер сектора не означает вероятность”. On mutation success, verify `reward_days` is present in the current sectors before animation; otherwise keep the backend result text, show sync error, refetch wheel/dashboard, and never choose index zero. The repository has no frontend unit runner, so keep these deterministic cases in the existing Playwright harness and add no testing dependency.

- [ ] **Step 5: Run WebApp verification**

```powershell
Set-Location webapp
npm.cmd run lint
npm.cmd run build
npm.cmd run test:e2e:cabinet
Set-Location ..
```

Expected: lint/build/cabinet E2E all pass with no hydration or console errors.

- [ ] **Step 6: Commit the rewards UI**

```powershell
git add -- webapp/src/lib/api.ts webapp/src/components/cabinet/bonus-wheel.tsx 'webapp/src/app/(dashboard)/rewards/page.tsx' webapp/src/components/cabinet-shell.tsx 'webapp/src/app/(dashboard)/page.tsx' webapp/e2e/rewards.spec.ts webapp/README.md
git commit -m "feat(webapp): add paid rewards hub"
```

---

### Task 9: Add Safe Karing and Happ Manual Imports

**Files:**

- Create: `webapp/src/lib/subscription-format.ts`
- Modify: `webapp/src/app/(dashboard)/subscription/page.tsx:220-304`
- Modify: `webapp/e2e/cabinet-flow.spec.ts:726-758`
- Modify: `tests/test_api_auth_and_tickets.py`
- Modify: `docs/user/compatibility-clients-guide-ru.md`

**Interfaces:**

- Consumes: the authenticated private subscription URL already returned by the cabinet API.
- Produces: `subscriptionUrlForFormat()` and manual order Hiddify, Karing, Happ, then existing advanced clients.

- [ ] **Step 1: Add failing URL and secrecy E2E tests**

```typescript
test("builds Karing and Happ URLs without leaking them to third parties", async ({ page }) => {
  const privateUrl = "https://connect.pokrov.space/token-value?existing=1#manual";
  await registerCabinetMocks(page, { subscriptionUrl: privateUrl });
  await page.goto("/subscription/#manual-setup");
  await page.getByRole("button", { name: "Показать" }).click();
  await expect(page.getByTestId("karing-subscription-url")).toContainText("existing=1&format=smart");
  await expect(page.getByTestId("happ-subscription-url")).toContainText("existing=1&format=happ");
  for (const link of await page.locator('a[target="_blank"]').all()) {
    const href = (await link.getAttribute("href")) || "";
    expect(href).not.toContain("token-value");
    expect(href).not.toContain("connect.pokrov.space");
  }
});
```

Add a request listener that asserts analytics/beacon URLs and request bodies never contain `token-value`.

- [ ] **Step 2: Run the manual-setup test and verify Karing/Happ are absent**

```powershell
Set-Location webapp
npm.cmd run test:e2e:cabinet -- --grep "Karing and Happ"
Set-Location ..
```

Expected: failure because the format helper and client rows do not exist.

- [ ] **Step 3: Add one query-safe URL helper**

```typescript
export function subscriptionUrlForFormat(rawUrl: string, format: "smart" | "happ"): string {
  const url = new URL(rawUrl);
  if (url.protocol !== "https:") throw new Error("subscription_url_protocol_invalid");
  url.searchParams.set("format", format);
  return url.toString();
}
```

Compute Karing/Happ values only while the authenticated manual section is open. Each row gets its own local QR/copy control. External download buttons use official public project pages only; do not create third-party deep links containing the subscription value.

- [ ] **Step 4: Update guidance and run verification**

Document POKROV as primary, Hiddify as verified fallback, and Karing/Happ as best-effort with exact formats. Then run:

```powershell
Set-Location webapp
npm.cmd run lint
npm.cmd run build
npm.cmd run test:e2e:cabinet
Set-Location ..
& 'C:\Users\kiwun\AppData\Local\Temp\pokrov-support-agent-venv-20260715\Scripts\python.exe' -B -m pytest -p no:cacheprovider --basetemp "$env:TEMP\pokrov-rewards-$PID" tests/test_api_auth_and_tickets.py -k "subscription or compatible" -q
```

Expected: all selected checks pass; private tokens appear only inside the opened authenticated manual section.

- [ ] **Step 5: Commit compatible clients**

```powershell
git add -- webapp/src/lib/subscription-format.ts 'webapp/src/app/(dashboard)/subscription/page.tsx' webapp/e2e/cabinet-flow.spec.ts tests/test_api_auth_and_tickets.py docs/user/compatibility-clients-guide-ru.md
git commit -m "feat(webapp): add safe Karing and Happ imports"
```

---

### Task 10: Correct Product Copy, Support Knowledge, and Canonical Docs

**Files:**

- Modify: `shared/support-ai-knowledge.json`
- Modify: `webapp/src/app/(dashboard)/settings/page.tsx`
- Modify: `webapp/e2e/cabinet-flow.spec.ts`
- Modify: `webapp/e2e/settings-email-link.spec.ts`
- Modify: `marketing/src/lib/seo-pages.ts`
- Modify: `marketing/src/lib/marketing-site.ts`
- Modify: `marketing/src/app/checkout/checkout-client.tsx`
- Modify: `marketing/src/app/telegram/page.tsx`
- Modify: `marketing/src/app/vpn/page.tsx`
- Modify: `tests/test_pokrov_support_ai_kb_refresh.py`
- Modify: `tests/test_frontend_text_integrity.py`
- Modify: `tests/test_public_copy_guardrails.py`
- Modify: `docs/product/portal-vpn-product.md`
- Modify: `docs/architecture/app-first-and-bonus-flows.md`
- Modify: `docs/architecture/system-overview.md`
- Modify: `docs/architecture/api-contracts.md`
- Modify: `docs/user/portal-vpn-user-guide-ru.md`
- Modify: `docs/operations/deployment-and-access.md`
- Modify: `marketing/README.md`

**Interfaces:**

- Consumes: implemented reward/channel/client behavior from Tasks 7-9 and current `shared/product-facts.json` values.
- Produces: one truthful `5 + 5` message, rollout-gated paid-reward copy, exact support topics, and canonical ownership documentation.

- [ ] **Step 1: Add copy and support-KB guardrails before editing strings**

```python
def test_telegram_ten_day_claim_requires_explicit_five_plus_five_decomposition():
    forbidden = re.compile(r"(?:telegram|телеграм|канал).{0,80}(?:\+?10|десят)", re.IGNORECASE | re.DOTALL)
    allowed = re.compile(r"5.{0,80}(?:пробн|бесплат).{0,120}5.{0,80}(?:telegram|телеграм|канал)", re.IGNORECASE | re.DOTALL)
    paths = [
        ROOT / "marketing/src/lib/seo-pages.ts",
        ROOT / "marketing/src/lib/marketing-site.ts",
        ROOT / "marketing/src/app/checkout/checkout-client.tsx",
        ROOT / "marketing/src/app/telegram/page.tsx",
        ROOT / "marketing/src/app/vpn/page.tsx",
        ROOT / "webapp/src/app/(dashboard)/settings/page.tsx",
    ]
    violations = [
        path.relative_to(ROOT).as_posix()
        for path in paths
        if forbidden.search(path.read_text(encoding="utf-8"))
        and not allowed.search(path.read_text(encoding="utf-8"))
    ]
    assert violations == []


def test_support_kb_has_exact_compatible_client_formats():
    payload = json.loads((ROOT / "shared/support-ai-knowledge.json").read_text(encoding="utf-8"))
    serialized = json.dumps(payload, ensure_ascii=False).lower()
    assert "hiddify" in serialized
    assert "karing" in serialized and "format=smart" in serialized
    assert "happ" in serialized and "format=happ" in serialized
    assert "замените ?" not in serialized
    assert "второй ?" not in serialized
```

Add a guard proving paid-reward public availability copy is absent unless the marketing rollout gate is true, while the factual `5 + 5` correction is always rendered.

- [ ] **Step 2: Run copy/KB tests and capture current false claims**

```powershell
& 'C:\Users\kiwun\AppData\Local\Temp\pokrov-support-agent-venv-20260715\Scripts\python.exe' -B -m pytest -p no:cacheprovider --basetemp "$env:TEMP\pokrov-rewards-$PID" tests/test_frontend_text_integrity.py tests/test_public_copy_guardrails.py tests/test_pokrov_support_ai_kb_refresh.py -q
```

Expected: failures identify direct Telegram `+10`, missing Karing format knowledge, or unguarded paid-reward availability wording.

- [ ] **Step 3: Normalize the product promise and historical claim rendering**

Use this exact public meaning everywhere:

```text
До 10 дней на старте: 5 дней бесплатно в приложении и ещё 5 дней после привязки Telegram и подтверждения подписки на канал.
```

Settings uses `offer_days ?? 5` and renders `claimed_days` separately when present. Do not replace legitimate referral-ten-day or grandfathered `claimed_days=10` fixtures.

- [ ] **Step 4: Gate paid-reward marketing and update support knowledge**

Add one existing-style marketing environment gate, default false, named `NEXT_PUBLIC_PAID_REWARDS_MARKETING_ENABLED`. Only when it is exactly `"1"` may marketing render:

```text
Для активной платной подписки доступны еженедельное колесо бонусов и календарь активности. В колесе возможен редкий джекпот +30 дней.
```

Do not publish weights. Update support KB topics for paid-only rewards, Karing `format=smart`, Happ `format=happ`, Hiddify precedence, and escalation when account eligibility or compatibility cannot be established from allowlisted knowledge. Do not change support provider/runtime/policy/evaluation code.

- [ ] **Step 5: Update canonical owners with implementation and rollout truth**

Document:

- account-owned state/grants/jobs and legacy evidence boundaries;
- exact active-paid predicate and reward-tail denial;
- wheel/calendar API fields and stable errors;
- worker retry/manual-review and merge fencing;
- feature flags false by default, bot quiesce requirement, config snapshot/readback, marketing gate, and safe rollback;
- POKROV/Hiddify/Karing/Happ order and private-URL rules.

Keep release status as implementation/local evidence until a deployed candidate is actually verified.

- [ ] **Step 6: Run copy, support, marketing, and docs gates**

```powershell
& 'C:\Users\kiwun\AppData\Local\Temp\pokrov-support-agent-venv-20260715\Scripts\python.exe' -B -m pytest -p no:cacheprovider --basetemp "$env:TEMP\pokrov-rewards-$PID" tests/test_frontend_text_integrity.py tests/test_public_copy_guardrails.py tests/test_pokrov_support_ai_kb_refresh.py tests/test_support_agent_safety.py tests/test_support_agent_grounding.py tests/test_support_agent_state.py tests/test_support_agent_harness.py tests/test_pokrov_support_agent_eval.py tests/test_client_ui_api_additions.py tests/test_helpbot_lifecycle.py tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q
& 'C:\Users\kiwun\AppData\Local\Temp\pokrov-support-agent-venv-20260715\Scripts\python.exe' -B scripts/agent_context_packet_audit.py --platform-context-root .
Set-Location marketing
npm.cmd run lint
npm.cmd run build
npm.cmd run check:seo
npm.cmd run check:responsive
Set-Location ..
git diff --check
```

Expected: all tests and marketing gates pass; context audit reports success; diff check is clean.

- [ ] **Step 7: Commit product truth and docs**

```powershell
git add -- shared/support-ai-knowledge.json 'webapp/src/app/(dashboard)/settings/page.tsx' webapp/e2e/cabinet-flow.spec.ts webapp/e2e/settings-email-link.spec.ts marketing/src/lib/seo-pages.ts marketing/src/lib/marketing-site.ts marketing/src/app/checkout/checkout-client.tsx marketing/src/app/telegram/page.tsx marketing/src/app/vpn/page.tsx tests/test_pokrov_support_ai_kb_refresh.py tests/test_frontend_text_integrity.py tests/test_public_copy_guardrails.py docs/product/portal-vpn-product.md docs/architecture/app-first-and-bonus-flows.md docs/architecture/system-overview.md docs/architecture/api-contracts.md docs/user/portal-vpn-user-guide-ru.md docs/operations/deployment-and-access.md marketing/README.md
git commit -m "docs(product): align rewards and acquisition truth"
```

---

### Task 11: Add Guarded Rollout Operations and Verify the Candidate

**Files:**

- Create: `scripts/reward_rollout.py`
- Create: `tests/test_reward_rollout.py`
- Modify: `portal_bot/.env.example:258-259`
- Modify: `docs/operations/deployment-and-access.md`
- Modify: `docs/README.md` only if its current reward workstream classification changes after implementation.
- Generate after real checks: `docs/audit-artifacts/rewards/<candidate>/` with secret-free JSON/Markdown evidence.

**Interfaces:**

- Consumes: all preceding implementation and canonical documentation.
- Produces: read-only preflight, explicitly confirmed mutations, candidate-specific evidence, and an honest deploy/rollback handoff.

- [ ] **Step 1: Write rollout-script safety tests**

```python
def test_preflight_blocks_unresolved_accounts_and_running_legacy_bot(fake_runtime, tmp_path):
    result = run_preflight(fake_runtime(unresolved_users=1, legacy_bot_mutator_count=1), evidence_dir=tmp_path)
    assert result.status == "BLOCKED"
    assert result.codes == ("account_foundation_unresolved", "legacy_bot_not_quiesced")


def test_apply_requires_exact_confirmation(fake_runtime, tmp_path):
    with pytest.raises(SystemExit, match="explicit confirmation required"):
        main(["configure", "--evidence-dir", str(tmp_path)], runtime=fake_runtime())


def test_configure_snapshots_and_hashes_exact_preset_without_secrets(fake_runtime, tmp_path):
    runtime = fake_runtime(previous_wheel_config={"preset": "legacy"})
    result = main(
        ["configure", "--confirm-apply", "paid_weekly_v1", "--evidence-dir", str(tmp_path)],
        runtime=runtime,
    )
    assert result.readback == PAID_WEEKLY_V1
    evidence = json.loads((tmp_path / "wheel-config.json").read_text(encoding="utf-8"))
    assert evidence["preset"] == "paid_weekly_v1"
    assert evidence["sha256"] == hashlib.sha256(canonical_json(PAID_WEEKLY_V1)).hexdigest()
    assert "token" not in json.dumps(evidence).lower()
```

- [ ] **Step 2: Run and verify the operator script is absent**

```powershell
& 'C:\Users\kiwun\AppData\Local\Temp\pokrov-support-agent-venv-20260715\Scripts\python.exe' -B -m pytest -p no:cacheprovider --basetemp "$env:TEMP\pokrov-rewards-$PID" tests/test_reward_rollout.py -q
```

Expected: collection fails because `scripts.reward_rollout` does not exist.

- [ ] **Step 3: Implement read-only preflight and explicit subcommands**

The script exposes only these commands:

```text
reward_rollout.py preflight --candidate <sha> --evidence-dir <path>
reward_rollout.py backfill --candidate <sha> --confirm-apply reward-state-v1 --evidence-dir <path>
reward_rollout.py configure --candidate <sha> --confirm-apply paid_weekly_v1 --evidence-dir <path>
reward_rollout.py verify --candidate <sha> --evidence-dir <path>
```

`preflight` is read-only and fails unless both feature flags are false, account-foundation unresolved counts are zero, the exact candidate is reported by every API/bot instance, and no legacy bot reward mutator is accepting callbacks. `backfill` calls `backfill_reward_account_states()` in one guarded transaction. `configure` snapshots the previous setting, writes exact `PAID_WEEKLY_V1`, reads it back, and retains only canonical JSON hashes/counts. The script never accepts secrets on the command line and never enables marketing or production flags automatically.

- [ ] **Step 4: Run focused backend, frontend, support, docs, and operations regressions**

```powershell
& 'C:\Users\kiwun\AppData\Local\Temp\pokrov-support-agent-venv-20260715\Scripts\python.exe' -B -m pytest -p no:cacheprovider --basetemp "$env:TEMP\pokrov-rewards-$PID" portal_bot/tests/test_rewards_service.py portal_bot/tests/test_app_first_api.py portal_bot/tests/test_app_first_service.py tests/test_reward_migrations.py tests/test_node_provisioning_service.py tests/test_account_foundation.py tests/test_api_auth_and_tickets.py tests/test_bot_paywall.py tests/test_subscription_preview_api.py tests/test_reward_rollout.py tests/test_frontend_text_integrity.py tests/test_public_copy_guardrails.py tests/test_pokrov_support_ai_kb_refresh.py tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q
& 'C:\Users\kiwun\AppData\Local\Temp\pokrov-support-agent-venv-20260715\Scripts\python.exe' -B scripts/agent_context_packet_audit.py --platform-context-root .
Set-Location webapp
npm.cmd run lint
npm.cmd run build
npm.cmd run test:e2e:cabinet
Set-Location ../marketing
npm.cmd run lint
npm.cmd run build
npm.cmd run check:seo
npm.cmd run check:responsive
Set-Location ..
git diff --check
```

Expected: every command exits zero. Record exact counts and versions; do not convert an unavailable live/provider/device check into PASS.

- [ ] **Step 5: Run the complete relevant regression gates before promotion**

```powershell
& 'C:\Users\kiwun\AppData\Local\Temp\pokrov-support-agent-venv-20260715\Scripts\python.exe' -B -m pytest -p no:cacheprovider --basetemp "$env:TEMP\pokrov-rewards-$PID" portal_bot/tests tests -q
Set-Location webapp
npm.cmd run test:e2e
Set-Location ..
git status --short --branch
$mergeBase = git merge-base master HEAD
git diff --stat $mergeBase HEAD
git log --oneline master..HEAD
```

Expected: Python and full WebApp E2E pass; only this plan's commits appear over `master`; the worktree is clean after the final commit.

- [ ] **Step 6: Commit rollout tooling before any live mutation**

```powershell
git add -- scripts/reward_rollout.py tests/test_reward_rollout.py portal_bot/.env.example docs/operations/deployment-and-access.md docs/README.md
git commit -m "ops(rewards): add guarded rollout controls"
```

- [ ] **Step 7: Promote, push, and deploy only after evidence-backed approval**

From the clean platform promotion worktree, merge `codex/rewards-rollout-integration` into `master` without rewriting concurrent history, rerun the focused candidate gate, and push `master`. Then execute the documented rollout in order: quiesce legacy bot, preflight, migration/backfill, disabled deploy, exact config snapshot/readback, wheel enable/smoke, calendar enable/smoke, and only then marketing enable/build/deploy.

Retain evidence labels for the exact candidate and environment: `PASS`, `MANUAL_OWNER_TEST`, `OPERATOR_ATTESTED`, `SKIPPED_BY_OWNER`, `SKIPPED_BY_OPERATOR`, `BLOCKED_BY_ACCESS`, or `NOT_REQUESTED`. Rollback disables both new flags on the new candidate first; never restart an unpatched legacy bot that ignores the kill switch.

---

## Final Acceptance Review

- [ ] API and Telegram share one locked account reward service, paid predicate, wheel switch, exact preset, cooldown, grant, and durable job.
- [ ] Calendar never reads/writes monthly paid-streak fields and awards exactly four one-day milestones per completed cycle.
- [ ] Trial/free/bonus-tail/expired/merged/disabled accounts cannot mutate either reward.
- [ ] Merge reconciliation cannot reset cooldown/calendar or let a stale worker finalize the source account.
- [ ] Public clients receive sectors but no weights, and fail closed on missing/invalid/unknown sector state.
- [ ] Telegram is five days; “up to ten” is always decomposed as `5 + 5`; grandfathered claims keep their actual amount.
- [ ] Karing/Happ get exact format-specific URLs only inside the authenticated manual surface, with no third-party leakage.
- [ ] Existing support-agent safety, grounding, evaluation, and handoff suites remain green without runtime/provider changes.
- [ ] Canonical docs describe implemented behavior and retain honest rollout/evidence boundaries.
- [ ] No POKROV-app edit, new dependency, agent framework, vector store, or external retrieval service appears in the diff.
- [ ] Push/deploy claims are made only for commands actually run against the exact candidate and environment.
