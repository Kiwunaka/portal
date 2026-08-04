from __future__ import annotations

import asyncio
import hashlib
import json
import uuid
from contextlib import suppress
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Sequence

from control_panel import ControlPanel
from economy_service import resolve_canonical_account_id
from free_cycle_service import FREE_CYCLE_DAYS, FREE_STANDARD_QUOTA_BYTES
from models import AccessKey, EntitlementGrant, Node, NodeProvisioningJob, User, UserNode
from node_policy import (
    FREE_SOFT_ROLE,
    FREE_STANDARD_ROLE,
    PAID_ROLE,
    NodeAccessRoleError,
    node_access_role,
    nodes_for_access_role,
    validate_node_access_roles,
)


SUPPORTED_JOB_TYPES = frozenset(
    {
        "free_to_soft",
        "free_to_standard",
        "rotate_access_key",
        "reward_entitlement_sync",
    }
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _rotation_uuid_fingerprint(value: str) -> str:
    return hashlib.sha256(str(value or "").strip().encode("utf-8")).hexdigest()


class ProvisioningError(RuntimeError):
    def __init__(self, code: str):
        self.code = str(code or "provisioning_failed").strip()[:64] or "provisioning_failed"
        super().__init__(self.code)


class ClaimLostError(ProvisioningError):
    def __init__(self) -> None:
        super().__init__("job_claim_lost")


def enqueue_reward_entitlement_sync(
    session,
    *,
    account_id: str,
    entitlement_grant_id: str,
    now: datetime,
) -> NodeProvisioningJob:
    account_key = str(account_id)
    grant_id = str(entitlement_grant_id)
    key = f"reward-entitlement-sync:v1:{grant_id}"
    grant = session.get(EntitlementGrant, grant_id)
    if (
        grant is None
        or str(grant.account_id) != account_key
        or str(grant.source) not in {"bonus_wheel", "bonus_calendar"}
    ):
        raise ProvisioningError("reward_sync_grant_invalid")

    existing = (
        session.query(NodeProvisioningJob)
        .filter_by(idempotency_key=key)
        .one_or_none()
    )
    if existing is not None:
        if (
            str(existing.entitlement_grant_id) != grant_id
            or str(existing.account_id) != account_key
        ):
            raise ProvisioningError("reward_sync_idempotency_conflict")
        return existing

    job = NodeProvisioningJob(
        account_id=account_key,
        entitlement_grant_id=grant_id,
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


@dataclass(frozen=True)
class ClaimedJob:
    id: int
    lock_token: str
    job_type: str
    attempts: int


def _renew_job_claim(
    session_factory,
    *,
    claim: ClaimedJob,
    now: datetime,
) -> bool:
    with session_factory() as session:
        updated = (
            session.query(NodeProvisioningJob)
            .filter(NodeProvisioningJob.id == int(claim.id))
            .filter(NodeProvisioningJob.status == "running")
            .filter(NodeProvisioningJob.lock_token == claim.lock_token)
            .update(
                {
                    NodeProvisioningJob.locked_at: now,
                    NodeProvisioningJob.updated_at: now,
                },
                synchronize_session=False,
            )
        )
        if int(updated or 0) != 1:
            session.rollback()
            return False
        session.commit()
        return True


@dataclass(frozen=True)
class ClaimLease:
    session_factory: Callable[[], Any]
    claim: ClaimedJob
    heartbeat_interval_seconds: float
    clock: Callable[[], datetime] = _utcnow

    def renew(self) -> None:
        try:
            owned = _renew_job_claim(
                self.session_factory,
                claim=self.claim,
                now=self.clock(),
            )
        except Exception as exc:
            raise ClaimLostError() from exc
        if not owned:
            raise ClaimLostError()

    async def run(self, operation: Callable[[], Awaitable[Any]]) -> Any:
        self.renew()
        task = asyncio.ensure_future(operation())
        try:
            while True:
                done, _pending = await asyncio.wait(
                    (task,),
                    timeout=max(0.1, float(self.heartbeat_interval_seconds)),
                )
                if task in done:
                    result = await task
                    self.renew()
                    return result
                self.renew()
        except BaseException:
            if not task.done():
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task
            raise


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
    source_bindings: tuple[tuple[str, str], ...] = ()
    target_preimage_state: str | None = None
    source_preimage_states: tuple[tuple[str, str, str], ...] = ()
    replacement_key_uuid: str | None = None
    rotation_pooled: bool = False
    rotation_updates_subscription_uuid: bool = False
    superseded: bool = False


_PANEL_PROFILE_STATES = frozenset({"absent", "disabled", "enabled"})


def _result_json(*, outcome: str, code: str, attempt: int) -> str:
    return json.dumps(
        {
            "outcome": str(outcome or "unknown")[:32],
            "code": str(code or "unknown")[:64],
            "attempt": max(0, int(attempt)),
        },
        ensure_ascii=True,
        separators=(",", ":"),
    )


def _decoded_panel_preimage(
    desired: dict[str, Any],
    *,
    target_node_code: str,
    target_role: str,
    source_bindings: tuple[tuple[str, str], ...],
) -> tuple[str | None, tuple[tuple[str, str, str], ...]]:
    raw = desired.get("panel_preimage")
    if raw is None:
        return None, ()
    if not isinstance(raw, dict):
        raise ProvisioningError("free_panel_preimage_invalid")
    try:
        version = int(raw.get("version") or 0)
    except (TypeError, ValueError):
        raise ProvisioningError("free_panel_preimage_invalid") from None
    if version != 1:
        raise ProvisioningError("free_panel_preimage_invalid")
    target = raw.get("target")
    sources = raw.get("sources")
    if not isinstance(target, dict) or not isinstance(sources, list):
        raise ProvisioningError("free_panel_preimage_invalid")
    target_state = str(target.get("state") or "").strip().lower()
    if (
        str(target.get("node_code") or "").strip() != str(target_node_code or "").strip()
        or str(target.get("access_role") or "").strip().lower() != str(target_role or "").strip().lower()
        or target_state not in _PANEL_PROFILE_STATES
    ):
        raise ProvisioningError("free_panel_preimage_invalid")
    decoded_sources: list[tuple[str, str, str]] = []
    for source in sources:
        if not isinstance(source, dict):
            raise ProvisioningError("free_panel_preimage_invalid")
        item = (
            str(source.get("node_code") or "").strip(),
            str(source.get("access_role") or "").strip().lower(),
            str(source.get("state") or "").strip().lower(),
        )
        if not item[0] or not item[1] or item[2] not in _PANEL_PROFILE_STATES:
            raise ProvisioningError("free_panel_preimage_invalid")
        decoded_sources.append(item)
    if tuple((code, role) for code, role, _state in decoded_sources) != tuple(source_bindings):
        raise ProvisioningError("free_panel_preimage_invalid")
    return target_state, tuple(decoded_sources)


def _retry_delay_seconds(attempt: int) -> int:
    return min(3600, 15 * (2 ** max(0, min(8, int(attempt) - 1))))


def _lock_query(query, session):
    dialect = str(getattr(getattr(session, "bind", None), "dialect", None).name or "")
    if dialect == "postgresql":
        return query.with_for_update(skip_locked=True)
    return query.with_for_update()


def _lock_exact_query(query, session):
    # Exact finalization rows must wait for concurrent entitlement writes. Using
    # SKIP LOCKED here would turn a payment lock into a false "missing" row.
    return query.with_for_update()


def _mark_user_error(session, *, job: NodeProvisioningJob, code: str, now: datetime) -> None:
    if job.job_type not in {"free_to_soft", "free_to_standard"} or job.tg_id is None:
        return
    user = session.query(User).filter(User.tg_id == int(job.tg_id)).first()
    if user is None:
        return
    user.free_profile_state = "error"
    user.free_profile_source = "provisioning_error"
    user.free_profile_state_changed_at = now
    user.free_profile_job_id = int(job.id)
    user.free_profile_error_code = str(code or "provisioning_failed")[:64]


def _recover_stale_jobs(
    session,
    *,
    now: datetime,
    stale_after_seconds: int,
    max_attempts: int,
    limit: int,
) -> dict[str, int]:
    cutoff = now - timedelta(seconds=max(30, int(stale_after_seconds)))
    rows = _lock_query(
        session.query(NodeProvisioningJob)
        .filter(NodeProvisioningJob.status == "running")
        .filter(NodeProvisioningJob.locked_at.isnot(None))
        .filter(NodeProvisioningJob.locked_at <= cutoff)
        .order_by(NodeProvisioningJob.id.asc()),
        session,
    ).limit(max(1, min(1000, int(limit)))).all()
    recovered = 0
    manual_review = 0
    for job in rows:
        pending_code = str(job.last_error_code or "")
        compensation_pending = pending_code in {
            "superseded_compensation_pending",
            "source_disable_compensation_pending",
        }
        code = (
            (
                "source_disable_compensation_stale"
                if pending_code == "source_disable_compensation_pending"
                else "superseded_compensation_stale"
            )
            if compensation_pending
            else "stale_lock_recovered"
        )
        job.locked_at = None
        job.lock_token = None
        job.last_error_code = code
        job.updated_at = now
        if compensation_pending or int(job.attempts or 0) >= int(max_attempts):
            job.status = "manual_review"
            job.manual_review_at = now
            job.next_run_at = None
            job.result_json = _result_json(outcome="manual_review", code=code, attempt=int(job.attempts or 0))
            if pending_code == "source_disable_compensation_pending" or not compensation_pending:
                _mark_user_error(session, job=job, code=code, now=now)
            manual_review += 1
        else:
            job.status = "queued"
            job.next_run_at = now
            job.result_json = _result_json(outcome="retry", code=code, attempt=int(job.attempts or 0))
            recovered += 1
    return {"recovered": recovered, "manual_review": manual_review}


def _claim_next_job(session, *, now: datetime, max_attempts: int) -> ClaimedJob | None:
    query = (
        session.query(NodeProvisioningJob)
        .filter(NodeProvisioningJob.status == "queued")
        .filter(NodeProvisioningJob.attempts < int(max_attempts))
        .filter(
            (NodeProvisioningJob.next_run_at.is_(None))
            | (NodeProvisioningJob.next_run_at <= now)
        )
        .order_by(NodeProvisioningJob.created_at.asc(), NodeProvisioningJob.id.asc())
    )
    job = _lock_query(query, session).first()
    if job is None:
        return None
    job.status = "running"
    job.attempts = int(job.attempts or 0) + 1
    job.locked_at = now
    job.lock_token = uuid.uuid4().hex
    job.next_run_at = None
    job.updated_at = now
    job.last_error_code = None
    if job.job_type == "rotate_access_key" and not str(job.replacement_key_uuid or "").strip():
        job.replacement_key_uuid = str(uuid.uuid4())
    if job.job_type == "rotate_access_key":
        desired: dict[str, Any] = {}
        try:
            parsed = json.loads(str(job.desired_state_json or "{}"))
            if isinstance(parsed, dict):
                desired = parsed
        except (TypeError, ValueError, json.JSONDecodeError):
            desired = {}
        key = _lock_exact_query(
                session.query(AccessKey).filter(AccessKey.id == int(job.key_id or 0)),
                session,
            ).first()
        if isinstance(desired.get("rotation"), dict):
            rotation = desired["rotation"]
            legacy_old_uuid = str(rotation.pop("old_uuid", "") or "").strip()
            if legacy_old_uuid:
                rotation["old_uuid_sha256"] = _rotation_uuid_fingerprint(legacy_old_uuid)
                job.desired_state_json = json.dumps(desired, sort_keys=True, separators=(",", ":"))
        if not isinstance(desired.get("rotation"), dict):
            user = (
                _lock_exact_query(session.query(User).filter(User.tg_id == int(key.tg_id)), session).first()
                if key is not None
                else None
            )
            if key is not None and user is not None:
                old_uuid = str(key.key_uuid or "").strip()
                node_code = str(key.node_code or "").strip().lower()
                desired["rotation"] = {
                    "old_uuid_sha256": _rotation_uuid_fingerprint(old_uuid),
                    "scope": "pooled" if not node_code else f"node:{node_code}",
                    "updates_subscription_uuid": bool(
                        old_uuid
                        and str(user.uuid or "").strip() == old_uuid
                        and (bool(key.is_primary) or not node_code)
                    ),
                }
                job.desired_state_json = json.dumps(desired, sort_keys=True, separators=(",", ":"))
    session.flush()
    return ClaimedJob(
        id=int(job.id),
        lock_token=str(job.lock_token),
        job_type=str(job.job_type),
        attempts=int(job.attempts),
    )


def _move_exhausted_jobs_to_manual_review(
    session,
    *,
    now: datetime,
    max_attempts: int,
    limit: int,
) -> int:
    rows = _lock_query(
        session.query(NodeProvisioningJob)
        .filter(NodeProvisioningJob.status == "queued")
        .filter(NodeProvisioningJob.attempts >= int(max_attempts))
        .order_by(NodeProvisioningJob.created_at.asc(), NodeProvisioningJob.id.asc()),
        session,
    ).limit(max(1, min(1000, int(limit)))).all()
    for job in rows:
        job.status = "manual_review"
        job.manual_review_at = now
        job.next_run_at = None
        job.locked_at = None
        job.lock_token = None
        job.last_error_code = "attempts_exhausted"
        job.result_json = _result_json(
            outcome="manual_review",
            code="attempts_exhausted",
            attempt=int(job.attempts or 0),
        )
        job.updated_at = now
        _mark_user_error(session, job=job, code="attempts_exhausted", now=now)
    return len(rows)


def _choose_role_node(nodes: list[Node], role: str, *, preferred_code: str = "") -> Node:
    try:
        candidates = nodes_for_access_role(nodes, role, required=True)
    except NodeAccessRoleError as exc:
        raise ProvisioningError(f"{role}_role_missing") from exc
    preferred = str(preferred_code or "").strip().lower()
    if preferred:
        for node in candidates:
            if str(node.code or "").strip().lower() == preferred:
                return node
    return sorted(candidates, key=lambda row: str(row.code or ""))[0]


def _exact_role_node(nodes: list[Node], *, node_code: str, role: str) -> Node:
    wanted = str(node_code or "").strip().lower()
    for node in nodes_for_access_role(nodes, role, required=True):
        if str(node.code or "").strip().lower() == wanted:
            return node
    raise ProvisioningError(f"{role}_source_missing")


def _primary_key(session, *, tg_id: int) -> AccessKey | None:
    return (
        session.query(AccessKey)
        .filter(AccessKey.tg_id == int(tg_id))
        .filter(AccessKey.state.in_(["active", "rotation_requested"]))
        .order_by(AccessKey.is_primary.desc(), AccessKey.id.asc())
        .first()
    )


def _prepare_job(session, claim: ClaimedJob) -> PreparedJob:
    job = session.query(NodeProvisioningJob).filter(NodeProvisioningJob.id == int(claim.id)).first()
    if job is None or str(job.lock_token or "") != claim.lock_token or job.status != "running":
        raise ProvisioningError("job_claim_lost")
    if job.job_type not in SUPPORTED_JOB_TYPES:
        raise ProvisioningError("job_type_unsupported")

    if job.job_type == "reward_entitlement_sync":
        try:
            account_id = resolve_canonical_account_id(
                session,
                account_id=str(job.account_id or ""),
            )
        except ValueError as exc:
            raise ProvisioningError(str(exc)) from exc
        grant = session.get(EntitlementGrant, str(job.entitlement_grant_id or ""))
        if (
            grant is None
            or str(grant.account_id) != account_id
            or str(grant.source) not in {"bonus_wheel", "bonus_calendar"}
        ):
            raise ProvisioningError("reward_sync_grant_invalid")
        reward_tg_ids = tuple(
            int(row[0])
            for row in (
                session.query(User.tg_id)
                .filter(
                    User.account_id == account_id,
                    User.is_active.is_(True),
                )
                .order_by(User.tg_id.asc())
                .all()
            )
        )
        if not reward_tg_ids:
            raise ProvisioningError("reward_sync_users_missing")
        return PreparedJob(
            job_id=int(job.id),
            job_type=job.job_type,
            account_id=account_id,
            entitlement_grant_id=str(grant.id),
            reward_tg_ids=reward_tg_ids,
        )

    if job.job_type == "rotate_access_key":
        key = session.query(AccessKey).filter(AccessKey.id == int(job.key_id or 0)).first()
        if key is None:
            raise ProvisioningError("rotation_key_missing")
        user = session.query(User).filter(User.tg_id == int(key.tg_id)).first()
        if user is None:
            raise ProvisioningError("rotation_user_missing")
        key_node_code = str(key.node_code or "").strip()
        replacement = str(job.replacement_key_uuid or "").strip()
        if not replacement:
            raise ProvisioningError("rotation_candidate_missing")
        desired: dict[str, Any] = {}
        try:
            parsed = json.loads(str(job.desired_state_json or "{}"))
            if isinstance(parsed, dict):
                desired = parsed
        except (TypeError, ValueError, json.JSONDecodeError):
            pass
        rotation = desired.get("rotation") if isinstance(desired.get("rotation"), dict) else {}
        expected_old_fingerprint = str(rotation.get("old_uuid_sha256") or "").strip().lower()
        scope = str(rotation.get("scope") or "").strip().lower()
        if len(expected_old_fingerprint) != 64 or not scope:
            raise ProvisioningError("rotation_snapshot_missing")
        old_key_uuid = str(key.key_uuid or "").strip()
        pooled_rotation = scope == "pooled"
        expected_node_code = scope.removeprefix("node:") if scope.startswith("node:") else ""
        if not pooled_rotation and not expected_node_code:
            raise ProvisioningError("rotation_snapshot_invalid")
        if pooled_rotation != (not key_node_code) or (
            not pooled_rotation and key_node_code.lower() != expected_node_code
        ):
            raise ProvisioningError("rotation_scope_changed")
        if _rotation_uuid_fingerprint(old_key_uuid) != expected_old_fingerprint:
            raise ProvisioningError("rotation_key_changed")
        updates_subscription_uuid = bool(rotation.get("updates_subscription_uuid"))
        if updates_subscription_uuid and str(user.uuid or "").strip() != old_key_uuid:
            raise ProvisioningError("rotation_user_changed")
        return PreparedJob(
            job_id=int(job.id),
            job_type=job.job_type,
            tg_id=int(key.tg_id),
            key_id=int(key.id),
            client_uuid=old_key_uuid,
            panel_email=str(key.panel_email or ""),
            sub_id=str(user.sub_token or user.tg_id),
            target_node_code=expected_node_code,
            replacement_key_uuid=replacement,
            rotation_pooled=pooled_rotation,
            rotation_updates_subscription_uuid=updates_subscription_uuid,
        )

    user = session.query(User).filter(User.tg_id == int(job.tg_id or 0)).first()
    if user is None:
        raise ProvisioningError("free_profile_user_missing")
    plan_code = str(user.current_plan_code or "").strip().lower()
    if str(user.sub_type or "").strip().upper() != "FREE" or plan_code in {"trial", "channel_bonus", "start_99"}:
        return PreparedJob(
            job_id=int(job.id),
            job_type=job.job_type,
            tg_id=int(user.tg_id),
            key_id=None,
            client_uuid="",
            panel_email="",
            sub_id="",
            superseded=True,
        )

    nodes = session.query(Node).filter(Node.enabled == True).order_by(Node.code.asc()).all()
    try:
        validate_node_access_roles(nodes)
    except NodeAccessRoleError as exc:
        raise ProvisioningError("node_access_role_invalid") from exc
    key = _primary_key(session, tg_id=int(user.tg_id))
    client_uuid = str(getattr(key, "key_uuid", None) or user.uuid or "").strip()
    panel_email = str(getattr(key, "panel_email", None) or user.email or f"User_{int(user.tg_id)}").strip()
    if not client_uuid:
        raise ProvisioningError("free_profile_credential_missing")

    if job.job_type == "free_to_soft":
        target_role = FREE_SOFT_ROLE
        source_role = FREE_STANDARD_ROLE
        preferred_source = str(user.free_profile_standard_node_code or getattr(key, "node_code", None) or "")
    else:
        target_role = FREE_STANDARD_ROLE
        source_role = str(user.free_profile_active_role or FREE_STANDARD_ROLE).strip().lower()
        preferred_source = str(user.free_profile_soft_node_code or getattr(key, "node_code", None) or "")
    target = _choose_role_node(
        nodes,
        target_role,
        preferred_code=(
            str(user.free_profile_soft_node_code or "")
            if target_role == FREE_SOFT_ROLE
            else str(user.free_profile_standard_node_code or "")
        ),
    )
    desired: dict[str, Any] = {}
    try:
        parsed = json.loads(str(job.desired_state_json or "{}"))
        if isinstance(parsed, dict):
            desired = parsed
    except (TypeError, ValueError, json.JSONDecodeError):
        desired = {}
    requested_bindings = desired.get("source_bindings")
    sources: list[Node] = []
    if job.job_type == "free_to_standard" and isinstance(requested_bindings, list):
        for raw in requested_bindings:
            if not isinstance(raw, dict):
                continue
            code = str(raw.get("node_code") or "").strip()
            role = str(raw.get("access_role") or "").strip().lower()
            if code and role:
                sources.append(_exact_role_node(nodes, node_code=code, role=role))
    if not sources:
        sources.append(_choose_role_node(nodes, source_role, preferred_code=preferred_source))
    if int(target.inbound_id or 0) <= 0 or any(int(source.inbound_id or 0) <= 0 for source in sources):
        raise ProvisioningError("node_inbound_invalid")
    source = sources[0]
    source_bindings = tuple(
        (str(source_node.code), node_access_role(source_node, strict=True))
        for source_node in sources
    )
    target_preimage_state, source_preimage_states = _decoded_panel_preimage(
        desired,
        target_node_code=str(target.code),
        target_role=node_access_role(target, strict=True),
        source_bindings=source_bindings,
    )
    return PreparedJob(
        job_id=int(job.id),
        job_type=job.job_type,
        tg_id=int(user.tg_id),
        key_id=int(key.id) if key is not None else None,
        client_uuid=client_uuid,
        panel_email=panel_email,
        sub_id=str(user.sub_token or user.tg_id),
        source_node_code=str(source.code),
        source_role=node_access_role(source, strict=True),
        target_node_code=str(target.code),
        target_role=node_access_role(target, strict=True),
        source_bindings=source_bindings,
        target_preimage_state=target_preimage_state,
        source_preimage_states=source_preimage_states,
    )


async def _run_panel_operation(
    operation: Callable[[], Awaitable[Any]],
    *,
    claim_lease: ClaimLease | None,
) -> Any:
    if claim_lease is None:
        return await operation()
    return await claim_lease.run(operation)


def _persisted_free_panel_preimage(
    session_factory,
    *,
    claim: ClaimedJob,
    prepared: PreparedJob,
) -> tuple[str, PreparedJob | None]:
    try:
        with session_factory() as session:
            job = session.query(NodeProvisioningJob).filter(NodeProvisioningJob.id == int(claim.id)).first()
            if job is None or job.status != "running" or str(job.lock_token or "") != claim.lock_token:
                return "claim_lost", None
            desired: dict[str, Any] = {}
            try:
                parsed = json.loads(str(job.desired_state_json or "{}"))
                if isinstance(parsed, dict):
                    desired = parsed
            except (TypeError, ValueError, json.JSONDecodeError):
                return "ambiguous", None
            target_state, source_states = _decoded_panel_preimage(
                desired,
                target_node_code=str(prepared.target_node_code or ""),
                target_role=str(prepared.target_role or ""),
                source_bindings=prepared.source_bindings,
            )
            if target_state is None:
                return "current", None
            return (
                "persisted",
                replace(
                    prepared,
                    target_preimage_state=target_state,
                    source_preimage_states=source_states,
                ),
            )
    except Exception:
        return "ambiguous", None


async def _ensure_free_panel_preimage(
    prepared: PreparedJob,
    panel,
    *,
    session_factory,
    claim: ClaimedJob,
    claim_lease: ClaimLease,
) -> PreparedJob:
    if prepared.job_type not in {"free_to_soft", "free_to_standard"} or prepared.superseded:
        return prepared
    if prepared.target_preimage_state is not None:
        return prepared

    async def observe(node_code: str, role: str) -> str:
        try:
            state = await _run_panel_operation(
                lambda: panel.get_user_profile_state_on_node(
                    tg_id=int(prepared.tg_id or 0),
                    client_uuid=prepared.client_uuid,
                    email=prepared.panel_email,
                    node_code=node_code,
                    expected_access_role=role,
                ),
                claim_lease=claim_lease,
            )
        except ClaimLostError:
            raise
        except Exception as exc:
            raise ProvisioningError("free_panel_preimage_failed") from exc
        normalized = str(state or "").strip().lower()
        if normalized not in _PANEL_PROFILE_STATES:
            raise ProvisioningError("free_panel_preimage_failed")
        return normalized

    target_state = await observe(
        str(prepared.target_node_code or ""),
        str(prepared.target_role or ""),
    )
    observed_sources: list[tuple[str, str, str]] = []
    for node_code, role in prepared.source_bindings:
        observed_sources.append((node_code, role, await observe(node_code, role)))
    source_states = tuple(observed_sources)
    captured = replace(
        prepared,
        target_preimage_state=target_state,
        source_preimage_states=source_states,
    )
    payload = {
        "version": 1,
        "target": {
            "node_code": str(captured.target_node_code or ""),
            "access_role": str(captured.target_role or ""),
            "state": target_state,
        },
        "sources": [
            {"node_code": node_code, "access_role": role, "state": state}
            for node_code, role, state in source_states
        ],
    }
    for _attempt in range(2):
        try:
            with session_factory() as session:
                job = _lock_exact_query(
                    session.query(NodeProvisioningJob).filter(NodeProvisioningJob.id == int(claim.id)),
                    session,
                ).first()
                if job is None or job.status != "running" or str(job.lock_token or "") != claim.lock_token:
                    raise ClaimLostError()
                desired: dict[str, Any] = {}
                try:
                    parsed = json.loads(str(job.desired_state_json or "{}"))
                    if isinstance(parsed, dict):
                        desired = parsed
                except (TypeError, ValueError, json.JSONDecodeError) as exc:
                    raise ProvisioningError("free_panel_preimage_invalid") from exc
                existing_state, existing_sources = _decoded_panel_preimage(
                    desired,
                    target_node_code=str(captured.target_node_code or ""),
                    target_role=str(captured.target_role or ""),
                    source_bindings=captured.source_bindings,
                )
                if existing_state is not None:
                    return replace(
                        captured,
                        target_preimage_state=existing_state,
                        source_preimage_states=existing_sources,
                    )
                desired["panel_preimage"] = payload
                job.desired_state_json = json.dumps(desired, sort_keys=True, separators=(",", ":"))
                session.commit()
                return captured
        except ClaimLostError:
            raise
        except ProvisioningError:
            raise
        except Exception:
            state, persisted = _persisted_free_panel_preimage(
                session_factory,
                claim=claim,
                prepared=captured,
            )
            if state == "persisted" and persisted is not None:
                return persisted
            if state == "claim_lost":
                raise ClaimLostError()
            if state != "current":
                raise ProvisioningError("free_panel_preimage_uncertain")
    raise ProvisioningError("free_panel_preimage_uncertain")


async def _restore_profile_state_and_confirm(
    prepared: PreparedJob,
    panel,
    *,
    node_code: str,
    role: str,
    expected_state: str,
    claim_lease: ClaimLease | None,
) -> bool:
    if expected_state not in _PANEL_PROFILE_STATES:
        return False
    try:
        await _run_panel_operation(
            lambda: panel.restore_user_profile_state_on_node(
                tg_id=int(prepared.tg_id or 0),
                client_uuid=prepared.client_uuid,
                email=prepared.panel_email,
                sub_id=prepared.sub_id,
                node_code=node_code,
                expected_access_role=role,
                state=expected_state,
            ),
            claim_lease=claim_lease,
        )
    except ClaimLostError:
        raise
    except Exception:
        pass
    try:
        observed = await _run_panel_operation(
            lambda: panel.get_user_profile_state_on_node(
                tg_id=int(prepared.tg_id or 0),
                client_uuid=prepared.client_uuid,
                email=prepared.panel_email,
                node_code=node_code,
                expected_access_role=role,
            ),
            claim_lease=claim_lease,
        )
    except ClaimLostError:
        raise
    except Exception:
        return False
    return str(observed or "").strip().lower() == expected_state


async def _compensate_failed_free_transition(
    prepared: PreparedJob,
    panel,
    *,
    claim_lease: ClaimLease,
) -> bool:
    if prepared.target_preimage_state not in _PANEL_PROFILE_STATES:
        return False

    complete = await _restore_profile_state_and_confirm(
        prepared,
        panel,
        claim_lease=claim_lease,
        node_code=str(prepared.target_node_code or ""),
        role=str(prepared.target_role or ""),
        expected_state=str(prepared.target_preimage_state),
    )
    expected_sources = {
        (node_code, role): state
        for node_code, role, state in prepared.source_preimage_states
    }
    if set(expected_sources) != set(prepared.source_bindings):
        return False
    for node_code, role in reversed(prepared.source_bindings):
        restored = await _restore_profile_state_and_confirm(
            prepared,
            panel,
            node_code=node_code,
            role=role,
            expected_state=expected_sources[(node_code, role)],
            claim_lease=claim_lease,
        )
        complete = complete and restored
    return complete


async def _compensate_superseded_free_job(
    prepared: PreparedJob,
    panel,
    *,
    claim_lease: ClaimLease | None = None,
) -> None:
    if prepared.target_preimage_state not in _PANEL_PROFILE_STATES:
        raise ProvisioningError("superseded_target_preimage_missing")
    target_restored = await _restore_profile_state_and_confirm(
        prepared,
        panel,
        node_code=str(prepared.target_node_code or ""),
        role=str(prepared.target_role or ""),
        expected_state=str(prepared.target_preimage_state),
        claim_lease=claim_lease,
    )
    failure_code = "" if target_restored else "superseded_target_restore_failed"
    paid_sources = tuple(binding for binding in prepared.source_bindings if binding[1] == PAID_ROLE)
    restore_sources = paid_sources or prepared.source_bindings
    restored_any = False
    for source_node_code, source_role in restore_sources:
        try:
            restored = await _run_panel_operation(
                lambda source_node_code=source_node_code, source_role=source_role: (
                    panel.set_user_profile_enabled_on_node(
                        tg_id=prepared.tg_id,
                        node_code=source_node_code,
                        expected_access_role=source_role,
                        enable=True,
                        sub_id=prepared.sub_id,
                    )
                ),
                claim_lease=claim_lease,
            )
        except ClaimLostError:
            raise
        except Exception:
            restored = False
        restored_any = restored_any or bool(restored)
    if not restored_any and not failure_code:
        failure_code = "superseded_source_restore_failed"
    if failure_code:
        raise ProvisioningError(failure_code)


async def _execute_panel(
    prepared: PreparedJob,
    panel,
    *,
    superseded_check: Callable[[], bool] | None = None,
    claim_lease: ClaimLease | None = None,
) -> str:
    if claim_lease is not None:
        claim_lease.renew()
    if prepared.superseded:
        return "superseded"
    if prepared.job_type == "reward_entitlement_sync":
        if superseded_check is not None and superseded_check():
            return "superseded"
        for tg_id in prepared.reward_tg_ids:
            if superseded_check is not None and superseded_check():
                return "superseded"
            try:
                updated = await _run_panel_operation(
                    lambda tg_id=tg_id: panel.update_client_traffic(int(tg_id), 0),
                    claim_lease=claim_lease,
                )
            except ClaimLostError:
                raise
            except Exception as exc:
                raise ProvisioningError("reward_sync_failed") from exc
            if not updated:
                raise ProvisioningError("reward_sync_failed")
        return "synced"
    if prepared.job_type == "rotate_access_key":
        if not prepared.rotation_pooled:
            panel_result = await _run_panel_operation(
                lambda: panel.rotate_user_key_on_node(
                    tg_id=prepared.tg_id,
                    node_code=str(prepared.target_node_code or ""),
                    old_key_uuid=prepared.client_uuid,
                    new_key_uuid=str(prepared.replacement_key_uuid or ""),
                    sub_id=prepared.sub_id,
                ),
                claim_lease=claim_lease,
            )
        if prepared.rotation_pooled:
            panel_result = await _run_panel_operation(
                lambda: panel.rotate_user_key_on_existing_nodes(
                    tg_id=prepared.tg_id,
                    old_key_uuid=prepared.client_uuid,
                    new_key_uuid=str(prepared.replacement_key_uuid or ""),
                    sub_id=prepared.sub_id,
                ),
                claim_lease=claim_lease,
            )
        status = str(getattr(panel_result, "status", "succeeded" if bool(panel_result) else "retry"))
        code = str(getattr(panel_result, "code", "rotation_panel_failed"))[:64]
        if status != "succeeded":
            raise ProvisioningError(code or "rotation_panel_failed")
        return "rotated"

    total_bytes = 0 if prepared.target_role == FREE_SOFT_ROLE else FREE_STANDARD_QUOTA_BYTES
    ensured = await _run_panel_operation(
        lambda: panel.ensure_user_profile_on_node(
            tg_id=prepared.tg_id,
            client_uuid=prepared.client_uuid,
            email=prepared.panel_email,
            sub_id=prepared.sub_id,
            node_code=str(prepared.target_node_code or ""),
            expected_access_role=str(prepared.target_role or ""),
            total_bytes=total_bytes,
            limit_ip=1,
        ),
        claim_lease=claim_lease,
    )
    if not ensured:
        raise ProvisioningError("target_ensure_failed")
    confirmed = await _run_panel_operation(
        lambda: panel.confirm_user_profile_on_node(
            tg_id=prepared.tg_id,
            client_uuid=prepared.client_uuid,
            email=prepared.panel_email,
            node_code=str(prepared.target_node_code or ""),
            expected_access_role=str(prepared.target_role or ""),
            total_bytes=total_bytes,
            limit_ip=1,
        ),
        claim_lease=claim_lease,
    )
    if not confirmed:
        raise ProvisioningError("target_confirm_failed")
    if prepared.job_type == "free_to_standard":
        reset_ok = await _run_panel_operation(
            lambda: panel.reset_user_profile_traffic_on_node(
                tg_id=prepared.tg_id,
                node_code=str(prepared.target_node_code or ""),
                expected_access_role=FREE_STANDARD_ROLE,
            ),
            claim_lease=claim_lease,
        )
        if not reset_ok:
            raise ProvisioningError("target_traffic_reset_failed")
    if superseded_check is not None and superseded_check():
        return "superseded_compensation_required"
    source_bindings = prepared.source_bindings
    if not source_bindings and prepared.source_node_code:
        source_bindings = ((prepared.source_node_code, str(prepared.source_role or "")),)
    for source_node_code, source_role in source_bindings:
        if source_node_code == prepared.target_node_code:
            continue
        try:
            disabled = await _run_panel_operation(
                lambda source_node_code=source_node_code, source_role=source_role: (
                    panel.set_user_profile_enabled_on_node(
                        tg_id=prepared.tg_id,
                        node_code=source_node_code,
                        expected_access_role=source_role,
                        enable=False,
                        sub_id=prepared.sub_id,
                    )
                ),
                claim_lease=claim_lease,
            )
        except ClaimLostError:
            raise
        except Exception as exc:
            raise ProvisioningError("source_disable_failed") from exc
        if not disabled:
            raise ProvisioningError("source_disable_failed")
        if superseded_check is not None and superseded_check():
            return "superseded_compensation_required"
    return "soft_active" if prepared.job_type == "free_to_soft" else "standard"


def _claim_was_superseded(session_factory, *, claim: ClaimedJob, prepared: PreparedJob) -> bool:
    if prepared.job_type == "reward_entitlement_sync":
        with session_factory() as session:
            job = (
                session.query(NodeProvisioningJob)
                .filter(NodeProvisioningJob.id == int(claim.id))
                .first()
            )
            if (
                job is None
                or job.status != "running"
                or str(job.lock_token or "") != claim.lock_token
            ):
                return True
            try:
                canonical_account_id = resolve_canonical_account_id(
                    session,
                    account_id=str(job.account_id or ""),
                )
            except ValueError:
                return True
            return (
                str(job.account_id or "") != str(prepared.account_id or "")
                or canonical_account_id != str(prepared.account_id or "")
                or str(job.entitlement_grant_id or "")
                != str(prepared.entitlement_grant_id or "")
            )
    if prepared.job_type not in {"free_to_soft", "free_to_standard"}:
        return False
    with session_factory() as session:
        job = session.query(NodeProvisioningJob).filter(NodeProvisioningJob.id == int(claim.id)).first()
        user = session.query(User).filter(User.tg_id == int(prepared.tg_id)).first()
        if job is None or job.status != "running" or str(job.lock_token or "") != claim.lock_token:
            return True
        if user is None:
            return True
        plan_code = str(user.current_plan_code or "").strip().lower()
        still_free = str(user.sub_type or "").strip().upper() == "FREE" and plan_code not in {
            "trial",
            "channel_bonus",
            "start_99",
        }
        job_is_current = int(user.free_profile_job_id or job.id) == int(job.id)
        return not still_free or not job_is_current


def _finalize_success(
    session,
    *,
    claim: ClaimedJob,
    prepared: PreparedJob,
    outcome: str,
    now: datetime,
) -> str:
    job = _lock_exact_query(
        session.query(NodeProvisioningJob).filter(NodeProvisioningJob.id == int(claim.id)),
        session,
    ).first()
    if job is None or job.status != "running" or str(job.lock_token or "") != claim.lock_token:
        return "claim_lost"

    if prepared.job_type == "reward_entitlement_sync":
        try:
            canonical_account_id = resolve_canonical_account_id(
                session,
                account_id=str(job.account_id or ""),
            )
        except ValueError:
            return "claim_lost"
        if (
            str(job.account_id or "") != str(prepared.account_id or "")
            or canonical_account_id != str(prepared.account_id or "")
            or str(job.entitlement_grant_id or "")
            != str(prepared.entitlement_grant_id or "")
        ):
            return "claim_lost"
        grant = _lock_exact_query(
            session.query(EntitlementGrant).filter(
                EntitlementGrant.id == str(prepared.entitlement_grant_id or "")
            ),
            session,
        ).first()
        if (
            grant is None
            or str(grant.account_id) != canonical_account_id
            or str(grant.source) not in {"bonus_wheel", "bonus_calendar"}
        ):
            return "claim_lost"
    elif prepared.job_type == "rotate_access_key":
        key = _lock_exact_query(
            session.query(AccessKey).filter(AccessKey.id == int(prepared.key_id or 0)),
            session,
        ).first()
        if key is None:
            raise ProvisioningError("rotation_key_missing_finalize")
        old_key_uuid = str(prepared.client_uuid or "").strip()
        if not old_key_uuid or str(key.key_uuid or "").strip() != old_key_uuid:
            raise ProvisioningError("rotation_key_changed")
        current_node_code = str(key.node_code or "").strip()
        if prepared.rotation_pooled:
            if current_node_code:
                raise ProvisioningError("rotation_scope_changed")
        elif current_node_code.lower() != str(prepared.target_node_code or "").strip().lower():
            raise ProvisioningError("rotation_node_changed")
        replacement_key_uuid = str(prepared.replacement_key_uuid or "").strip()
        if not replacement_key_uuid:
            raise ProvisioningError("rotation_candidate_missing_finalize")
        key.key_uuid = str(prepared.replacement_key_uuid or "")
        key.state = "active"
        key.rotated_at = now
        key.updated_at = now
        if prepared.rotation_updates_subscription_uuid:
            user = _lock_exact_query(
                session.query(User).filter(User.tg_id == int(prepared.tg_id or 0)),
                session,
            ).first()
            if user is None or str(user.uuid or "").strip() != old_key_uuid:
                raise ProvisioningError("rotation_user_changed")
            user.uuid = replacement_key_uuid
            mappings = _lock_exact_query(
                session.query(UserNode).filter(
                    UserNode.tg_id == int(prepared.tg_id or 0),
                    UserNode.client_uuid == old_key_uuid,
                ),
                session,
            ).all()
            for mapping in mappings:
                mapping.client_uuid = replacement_key_uuid
        session.flush()
        if prepared.rotation_pooled:
            old_uuid_persisted = (
                session.query(User).filter(User.uuid == old_key_uuid).count()
                + session.query(AccessKey).filter(AccessKey.key_uuid == old_key_uuid).count()
                + session.query(UserNode).filter(UserNode.client_uuid == old_key_uuid).count()
            )
            if old_uuid_persisted:
                raise ProvisioningError("rotation_old_uuid_persisted")
        job.replacement_key_uuid = None
    elif not prepared.superseded:
        user = _lock_exact_query(
            session.query(User).filter(User.tg_id == int(prepared.tg_id)),
            session,
        ).first()
        if user is None:
            raise ProvisioningError("free_profile_user_missing_finalize")
        plan_code = str(user.current_plan_code or "").strip().lower()
        still_free = str(user.sub_type or "").strip().upper() == "FREE" and plan_code not in {
            "trial",
            "channel_bonus",
            "start_99",
        }
        job_is_current = int(user.free_profile_job_id or job.id) == int(job.id)
        if not still_free or not job_is_current:
            if outcome != "superseded":
                job.last_error_code = "superseded_compensation_pending"
                job.result_json = _result_json(
                    outcome="pending",
                    code="superseded_compensation_pending",
                    attempt=claim.attempts,
                )
                job.updated_at = now
                return "superseded_compensation_required"
            outcome = "superseded"
        else:
            if outcome == "superseded":
                raise ProvisioningError("free_profile_state_changed")
            user.free_profile_state = "soft_active" if prepared.job_type == "free_to_soft" else "standard"
            user.free_profile_active_role = (
                FREE_SOFT_ROLE if prepared.job_type == "free_to_soft" else FREE_STANDARD_ROLE
            )
            user.free_profile_source = "provisioning_confirmed"
            user.free_profile_state_changed_at = now
            user.free_profile_job_id = int(job.id)
            user.free_profile_error_code = None
            if prepared.target_role == FREE_SOFT_ROLE:
                user.free_profile_soft_node_code = prepared.target_node_code
            else:
                user.free_profile_standard_node_code = prepared.target_node_code
                user.free_profile_observed_bytes = 0
                user.free_profile_observed_at = now
                user.free_profile_observation_source = "cycle_reset"
                user.free_cycle_last_reset_at = now
                user.free_cycle_next_reset_at = now + timedelta(days=FREE_CYCLE_DAYS)
            if prepared.key_id is not None:
                key = _lock_exact_query(
                    session.query(AccessKey).filter(AccessKey.id == int(prepared.key_id)),
                    session,
                ).first()
                if key is not None:
                    key.node_code = prepared.target_node_code
                    key.pool_code = "free_pool"
                    key.state = "active"
                    key.provisioned_at = now
                    key.updated_at = now

    success_status = (
        "completed" if prepared.job_type == "reward_entitlement_sync" else "succeeded"
    )
    job.status = success_status
    job.result_json = _result_json(
        outcome=success_status,
        code=outcome,
        attempt=claim.attempts,
    )
    job.last_error_code = None
    job.next_run_at = None
    job.locked_at = None
    job.lock_token = None
    job.completed_at = now
    job.updated_at = now
    return outcome


def _finalize_failure(
    session,
    *,
    claim: ClaimedJob,
    code: str,
    now: datetime,
    max_attempts: int,
) -> str:
    job = _lock_exact_query(
        session.query(NodeProvisioningJob).filter(NodeProvisioningJob.id == int(claim.id)),
        session,
    ).first()
    if job is None or job.status != "running" or str(job.lock_token or "") != claim.lock_token:
        return "claim_lost"
    normalized = str(code or "provisioning_failed").strip()[:64] or "provisioning_failed"
    job.last_error_code = normalized
    job.locked_at = None
    job.lock_token = None
    job.updated_at = now
    immediate_manual_codes = {
        "rotation_compensation_failed",
        "rotation_panel_manual_review",
        "rotation_runtime_apply_failed",
        "rotation_key_changed",
        "rotation_scope_changed",
        "rotation_user_changed",
        "rotation_finalize_manual_review",
        "source_disable_compensation_failed",
        "source_disable_compensation_uncertain",
    }
    if normalized in {"source_disable_compensation_failed", "source_disable_compensation_uncertain"}:
        _mark_user_error(session, job=job, code=normalized, now=now)
    if normalized.startswith("superseded_") or normalized in immediate_manual_codes:
        job.status = "manual_review"
        job.manual_review_at = now
        job.next_run_at = None
        job.result_json = _result_json(outcome="manual_review", code=normalized, attempt=int(job.attempts or 0))
        return "manual_review"
    _mark_user_error(session, job=job, code=normalized, now=now)
    if int(job.attempts or 0) >= int(max_attempts):
        job.status = "manual_review"
        job.manual_review_at = now
        job.next_run_at = None
        job.result_json = _result_json(outcome="manual_review", code=normalized, attempt=int(job.attempts or 0))
        return "manual_review"
    job.status = "queued"
    job.next_run_at = now + timedelta(seconds=_retry_delay_seconds(int(job.attempts or 0)))
    job.result_json = _result_json(outcome="retry", code=normalized, attempt=int(job.attempts or 0))
    return "retry"


def _claim_state_after_finalize_error(
    session_factory,
    *,
    claim: ClaimedJob,
    now: datetime,
    pending_code: str = "superseded_compensation_pending",
) -> str:
    try:
        with session_factory() as session:
            job = _lock_exact_query(
                session.query(NodeProvisioningJob).filter(NodeProvisioningJob.id == int(claim.id)),
                session,
            ).first()
            if job is None:
                return "ambiguous"
            if job.status != "running" or str(job.lock_token or "") != claim.lock_token:
                if job.status == "manual_review" and str(job.last_error_code or "").endswith(
                    ("_compensation_stale", "_compensation_uncertain", "_compensation_failed")
                ):
                    return "manual_review"
                return "claim_lost"
            if str(job.last_error_code or "") != str(pending_code or ""):
                return "current"
            job.locked_at = now
            job.updated_at = now
            session.commit()
            return "compensation_pending"
    except Exception:
        return "ambiguous"


def _mark_finalize_uncertain_manual_review(
    session_factory,
    *,
    claim: ClaimedJob,
    now: datetime,
    code: str = "superseded_compensation_uncertain",
) -> bool:
    try:
        with session_factory() as session:
            job = _lock_exact_query(
                session.query(NodeProvisioningJob).filter(NodeProvisioningJob.id == int(claim.id)),
                session,
            ).first()
            if (
                job is None
                or job.status != "running"
                or str(job.lock_token or "") != claim.lock_token
            ):
                return False
            normalized_code = str(code or "provisioning_compensation_uncertain")[:64]
            job.status = "manual_review"
            job.manual_review_at = now
            job.next_run_at = None
            job.locked_at = None
            job.lock_token = None
            job.last_error_code = normalized_code
            job.result_json = _result_json(
                outcome="manual_review",
                code=normalized_code,
                attempt=int(job.attempts or 0),
            )
            job.updated_at = now
            if normalized_code.startswith("source_disable_compensation_"):
                _mark_user_error(session, job=job, code=normalized_code, now=now)
            session.commit()
            return True
    except Exception:
        return False


def _persist_compensation_marker(
    session_factory,
    *,
    claim: ClaimedJob,
    now: datetime,
    pending_code: str,
    uncertain_code: str,
) -> None:
    for _attempt in range(2):
        try:
            with session_factory() as session:
                job = _lock_exact_query(
                    session.query(NodeProvisioningJob).filter(NodeProvisioningJob.id == int(claim.id)),
                    session,
                ).first()
                if job is None or job.status != "running" or str(job.lock_token or "") != claim.lock_token:
                    raise ClaimLostError()
                job.last_error_code = pending_code
                job.result_json = _result_json(
                    outcome="pending",
                    code=pending_code,
                    attempt=int(job.attempts or 0),
                )
                job.locked_at = now
                job.updated_at = now
                session.commit()
                return
        except ClaimLostError:
            raise
        except Exception as exc:
            state = _claim_state_after_finalize_error(
                session_factory,
                claim=claim,
                now=now,
                pending_code=pending_code,
            )
            if state == "compensation_pending":
                return
            if state == "claim_lost":
                raise ClaimLostError() from exc
            if state != "current":
                _mark_finalize_uncertain_manual_review(
                    session_factory,
                    claim=claim,
                    now=now,
                    code=uncertain_code,
                )
                raise ClaimLostError() from exc
    marked = _mark_finalize_uncertain_manual_review(
        session_factory,
        claim=claim,
        now=now,
        code=uncertain_code,
    )
    if marked:
        raise ClaimLostError()
    raise ClaimLostError()


def _persist_source_compensation_marker(
    session_factory,
    *,
    claim: ClaimedJob,
    now: datetime,
) -> None:
    _persist_compensation_marker(
        session_factory,
        claim=claim,
        now=now,
        pending_code="source_disable_compensation_pending",
        uncertain_code="source_disable_compensation_uncertain",
    )


def _persist_superseded_compensation_marker(
    session_factory,
    *,
    claim: ClaimedJob,
    now: datetime,
) -> None:
    _persist_compensation_marker(
        session_factory,
        claim=claim,
        now=now,
        pending_code="superseded_compensation_pending",
        uncertain_code="superseded_compensation_uncertain",
    )


def _rotation_db_still_expected(session_factory, *, prepared: PreparedJob) -> bool:
    with session_factory() as session:
        key = session.query(AccessKey).filter(AccessKey.id == int(prepared.key_id or 0)).first()
        if key is None or str(key.key_uuid or "").strip() != str(prepared.client_uuid or "").strip():
            return False
        current_node_code = str(key.node_code or "").strip().lower()
        if prepared.rotation_pooled:
            if current_node_code:
                return False
        elif current_node_code != str(prepared.target_node_code or "").strip().lower():
            return False
        if prepared.rotation_updates_subscription_uuid:
            user = session.query(User).filter(User.tg_id == int(prepared.tg_id or 0)).first()
            if user is None or str(user.uuid or "").strip() != str(prepared.client_uuid or "").strip():
                return False
        return True


def _rotation_db_fully_finalized(session_factory, *, claim: ClaimedJob, prepared: PreparedJob) -> bool:
    with session_factory() as session:
        job = session.query(NodeProvisioningJob).filter(NodeProvisioningJob.id == int(claim.id)).first()
        key = session.query(AccessKey).filter(AccessKey.id == int(prepared.key_id or 0)).first()
        replacement = str(prepared.replacement_key_uuid or "").strip()
        if (
            job is None
            or key is None
            or job.status != "succeeded"
            or str(key.key_uuid or "").strip() != replacement
            or str(key.state or "") != "active"
            or job.replacement_key_uuid is not None
        ):
            return False
        if prepared.rotation_updates_subscription_uuid:
            user = session.query(User).filter(User.tg_id == int(prepared.tg_id or 0)).first()
            if user is None or str(user.uuid or "").strip() != replacement:
                return False
            if session.query(UserNode).filter(UserNode.client_uuid == str(prepared.client_uuid or "")).count():
                return False
        return True


async def _compensate_rotation_after_finalize_failure(
    prepared: PreparedJob,
    panel,
    *,
    claim_lease: ClaimLease | None = None,
) -> bool:
    try:
        if prepared.rotation_pooled:
            result = await _run_panel_operation(
                lambda: panel.rollback_user_key_rotation_on_existing_nodes(
                    tg_id=int(prepared.tg_id or 0),
                    old_key_uuid=prepared.client_uuid,
                    new_key_uuid=str(prepared.replacement_key_uuid or ""),
                    sub_id=prepared.sub_id,
                ),
                claim_lease=claim_lease,
            )
        else:
            result = await _run_panel_operation(
                lambda: panel.rollback_user_key_rotation_on_node(
                    tg_id=int(prepared.tg_id or 0),
                    node_code=str(prepared.target_node_code or ""),
                    old_key_uuid=prepared.client_uuid,
                    new_key_uuid=str(prepared.replacement_key_uuid or ""),
                    sub_id=prepared.sub_id,
                ),
                claim_lease=claim_lease,
            )
    except ClaimLostError:
        raise
    except Exception:
        return False
    if isinstance(result, bool):
        return result
    return bool(getattr(result, "succeeded", False))


async def process_node_provisioning_jobs(
    session_factory,
    *,
    panel_factory: Callable[[], Any] = ControlPanel,
    now: datetime | None = None,
    limit: int = 20,
    max_attempts: int = 5,
    stale_after_seconds: int = 300,
) -> dict[str, int | bool]:
    current = now or _utcnow()
    bounded_limit = max(1, min(100, int(limit)))
    bounded_attempts = max(1, min(20, int(max_attempts)))
    heartbeat_interval_seconds = max(
        1.0,
        min(30.0, max(30, int(stale_after_seconds)) / 3.0),
    )
    result = {
        "ok": True,
        "claimed": 0,
        "succeeded": 0,
        "retried": 0,
        "manual_review": 0,
        "stale_recovered": 0,
    }

    with session_factory() as session:
        exhausted = _move_exhausted_jobs_to_manual_review(
            session,
            now=current,
            max_attempts=bounded_attempts,
            limit=bounded_limit,
        )
        recovered = _recover_stale_jobs(
            session,
            now=current,
            stale_after_seconds=stale_after_seconds,
            max_attempts=bounded_attempts,
            limit=bounded_limit,
        )
        result["stale_recovered"] = int(recovered["recovered"])
        result["manual_review"] = int(exhausted) + int(recovered["manual_review"])
        session.commit()

    for _ in range(bounded_limit):
        with session_factory() as session:
            claim = _claim_next_job(session, now=current, max_attempts=bounded_attempts)
            session.commit()
        if claim is None:
            break
        result["claimed"] = int(result["claimed"]) + 1
        panel = panel_factory()
        claim_lease = ClaimLease(
            session_factory=session_factory,
            claim=claim,
            heartbeat_interval_seconds=heartbeat_interval_seconds,
        )
        prepared: PreparedJob | None = None
        panel_rotation_succeeded = False
        try:
            claim_lease.renew()
            with session_factory() as session:
                prepared = _prepare_job(session, claim)
            prepared = await _ensure_free_panel_preimage(
                prepared,
                panel,
                session_factory=session_factory,
                claim=claim,
                claim_lease=claim_lease,
            )
            outcome = await _execute_panel(
                prepared,
                panel,
                superseded_check=lambda: _claim_was_superseded(
                    session_factory,
                    claim=claim,
                    prepared=prepared,
                ),
                claim_lease=claim_lease,
            )
            if outcome == "superseded_compensation_required":
                claim_lease.renew()
                marker_at = current if now is not None else _utcnow()
                _persist_superseded_compensation_marker(
                    session_factory,
                    claim=claim,
                    now=marker_at,
                )
                await _compensate_superseded_free_job(
                    prepared,
                    panel,
                    claim_lease=claim_lease,
                )
                outcome = "superseded"
            panel_rotation_succeeded = prepared.job_type == "rotate_access_key"
            finalized_at = current if now is not None else _utcnow()
            try:
                claim_lease.renew()
                with session_factory() as session:
                    finalized_outcome = _finalize_success(
                        session,
                        claim=claim,
                        prepared=prepared,
                        outcome=outcome,
                        now=finalized_at,
                    )
                    session.commit()
            except Exception as finalize_exc:
                if not panel_rotation_succeeded:
                    claim_state = _claim_state_after_finalize_error(
                        session_factory,
                        claim=claim,
                        now=finalized_at,
                    )
                    if claim_state == "compensation_pending":
                        finalized_outcome = "superseded_compensation_required"
                    elif claim_state == "current":
                        raise
                    else:
                        marked = _mark_finalize_uncertain_manual_review(
                            session_factory,
                            claim=claim,
                            now=finalized_at,
                        )
                        if marked:
                            result["manual_review"] = int(result["manual_review"]) + 1
                        raise ClaimLostError() from finalize_exc
                elif _rotation_db_fully_finalized(session_factory, claim=claim, prepared=prepared):
                    finalized_outcome = "rotated"
                elif not _rotation_db_still_expected(session_factory, prepared=prepared):
                    raise ProvisioningError("rotation_finalize_manual_review") from finalize_exc
                else:
                    compensated = await _compensate_rotation_after_finalize_failure(
                        prepared,
                        panel,
                        claim_lease=claim_lease,
                    )
                    if not compensated or not _rotation_db_still_expected(session_factory, prepared=prepared):
                        raise ProvisioningError("rotation_finalize_manual_review") from finalize_exc
                    raise ProvisioningError("rotation_finalize_failed") from finalize_exc
            if finalized_outcome == "claim_lost":
                raise ClaimLostError()
            if finalized_outcome == "superseded_compensation_required":
                await _compensate_superseded_free_job(
                    prepared,
                    panel,
                    claim_lease=claim_lease,
                )
                claim_lease.renew()
                finalized_at = current if now is not None else _utcnow()
                with session_factory() as session:
                    finalized_outcome = _finalize_success(
                        session,
                        claim=claim,
                        prepared=prepared,
                        outcome="superseded",
                        now=finalized_at,
                    )
                    session.commit()
                if finalized_outcome == "claim_lost":
                    raise ClaimLostError()
            if finalized_outcome != "claim_lost":
                result["succeeded"] = int(result["succeeded"]) + 1
        except ClaimLostError:
            continue
        except ProvisioningError as exc:
            failure_code = exc.code
            if failure_code == "source_disable_failed" and prepared is not None:
                try:
                    claim_lease.renew()
                    marker_at = current if now is not None else _utcnow()
                    _persist_source_compensation_marker(
                        session_factory,
                        claim=claim,
                        now=marker_at,
                    )
                    compensated = await _compensate_failed_free_transition(
                        prepared,
                        panel,
                        claim_lease=claim_lease,
                    )
                except ClaimLostError:
                    continue
                except Exception:
                    compensated = False
                if not compensated:
                    failure_code = "source_disable_compensation_failed"
            try:
                claim_lease.renew()
            except ClaimLostError:
                continue
            with session_factory() as session:
                state = _finalize_failure(
                    session,
                    claim=claim,
                    code=failure_code,
                    now=current,
                    max_attempts=bounded_attempts,
                )
                session.commit()
            if state == "manual_review":
                result["manual_review"] = int(result["manual_review"]) + 1
            elif state == "retry":
                result["retried"] = int(result["retried"]) + 1
            continue
        except Exception:
            claim_state = _claim_state_after_finalize_error(
                session_factory,
                claim=claim,
                now=current,
            )
            if claim_state != "current":
                marked = _mark_finalize_uncertain_manual_review(
                    session_factory,
                    claim=claim,
                    now=current,
                )
                if marked:
                    result["manual_review"] = int(result["manual_review"]) + 1
                continue
            try:
                claim_lease.renew()
            except ClaimLostError:
                continue
            with session_factory() as session:
                state = _finalize_failure(
                    session,
                    claim=claim,
                    code="panel_exception",
                    now=current,
                    max_attempts=bounded_attempts,
                )
                session.commit()
            if state == "manual_review":
                result["manual_review"] = int(result["manual_review"]) + 1
            elif state == "retry":
                result["retried"] = int(result["retried"]) + 1
            continue
        finally:
            try:
                await panel.close()
            except Exception:
                pass
    return result
