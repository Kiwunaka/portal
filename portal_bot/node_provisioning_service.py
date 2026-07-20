from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Sequence

from control_panel import ControlPanel
from economy_service import resolve_canonical_account_id
from free_cycle_service import FREE_CYCLE_DAYS, FREE_STANDARD_QUOTA_BYTES
from models import AccessKey, EntitlementGrant, Node, NodeProvisioningJob, User
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


class ProvisioningError(RuntimeError):
    def __init__(self, code: str):
        self.code = str(code or "provisioning_failed").strip()[:64] or "provisioning_failed"
        super().__init__(self.code)


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
    replacement_key_uuid: str | None = None
    superseded: bool = False


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
        code = "stale_lock_recovered"
        job.locked_at = None
        job.lock_token = None
        job.last_error_code = code
        job.updated_at = now
        if int(job.attempts or 0) >= int(max_attempts):
            job.status = "manual_review"
            job.manual_review_at = now
            job.next_run_at = None
            job.result_json = _result_json(outcome="manual_review", code=code, attempt=int(job.attempts or 0))
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
        node_code = str(job.node_code or key.node_code or "").strip()
        if user is None:
            raise ProvisioningError("rotation_user_missing")
        if not node_code:
            raise ProvisioningError("rotation_node_missing")
        replacement = str(job.replacement_key_uuid or "").strip()
        if not replacement:
            raise ProvisioningError("rotation_candidate_missing")
        return PreparedJob(
            job_id=int(job.id),
            job_type=job.job_type,
            tg_id=int(key.tg_id),
            key_id=int(key.id),
            client_uuid=str(key.key_uuid or ""),
            panel_email=str(key.panel_email or ""),
            sub_id=str(user.sub_token or user.tg_id),
            target_node_code=node_code,
            replacement_key_uuid=replacement,
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
        source_bindings=tuple(
            (str(source_node.code), node_access_role(source_node, strict=True))
            for source_node in sources
        ),
    )


async def _compensate_superseded_free_job(prepared: PreparedJob, panel) -> None:
    failure_code = ""
    try:
        target_disabled = await panel.set_user_profile_enabled_on_node(
            tg_id=prepared.tg_id,
            node_code=str(prepared.target_node_code or ""),
            expected_access_role=str(prepared.target_role or ""),
            enable=False,
            sub_id=prepared.sub_id,
        )
    except Exception:
        target_disabled = False
    if not target_disabled:
        failure_code = "superseded_target_disable_failed"
    paid_sources = tuple(binding for binding in prepared.source_bindings if binding[1] == PAID_ROLE)
    restore_sources = paid_sources or prepared.source_bindings
    restored_any = False
    for source_node_code, source_role in restore_sources:
        try:
            restored = await panel.set_user_profile_enabled_on_node(
                tg_id=prepared.tg_id,
                node_code=source_node_code,
                expected_access_role=source_role,
                enable=True,
                sub_id=prepared.sub_id,
            )
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
) -> str:
    if prepared.superseded:
        return "superseded"
    if prepared.job_type == "reward_entitlement_sync":
        if superseded_check is not None and superseded_check():
            return "superseded"
        for tg_id in prepared.reward_tg_ids:
            if superseded_check is not None and superseded_check():
                return "superseded"
            try:
                updated = await panel.update_client_traffic(int(tg_id), 0)
            except Exception as exc:
                raise ProvisioningError("reward_sync_failed") from exc
            if not updated:
                raise ProvisioningError("reward_sync_failed")
        return "synced"
    if prepared.job_type == "rotate_access_key":
        ok = await panel.rotate_user_key_on_node(
            tg_id=prepared.tg_id,
            node_code=str(prepared.target_node_code or ""),
            new_key_uuid=str(prepared.replacement_key_uuid or ""),
            sub_id=prepared.sub_id,
        )
        if not ok:
            raise ProvisioningError("rotation_panel_failed")
        return "rotated"

    total_bytes = 0 if prepared.target_role == FREE_SOFT_ROLE else FREE_STANDARD_QUOTA_BYTES
    ensured = await panel.ensure_user_profile_on_node(
        tg_id=prepared.tg_id,
        client_uuid=prepared.client_uuid,
        email=prepared.panel_email,
        sub_id=prepared.sub_id,
        node_code=str(prepared.target_node_code or ""),
        expected_access_role=str(prepared.target_role or ""),
        total_bytes=total_bytes,
        limit_ip=1,
    )
    if not ensured:
        raise ProvisioningError("target_ensure_failed")
    confirmed = await panel.confirm_user_profile_on_node(
        tg_id=prepared.tg_id,
        client_uuid=prepared.client_uuid,
        email=prepared.panel_email,
        node_code=str(prepared.target_node_code or ""),
        expected_access_role=str(prepared.target_role or ""),
        total_bytes=total_bytes,
        limit_ip=1,
    )
    if not confirmed:
        raise ProvisioningError("target_confirm_failed")
    if prepared.job_type == "free_to_standard":
        reset_ok = await panel.reset_user_profile_traffic_on_node(
            tg_id=prepared.tg_id,
            node_code=str(prepared.target_node_code or ""),
            expected_access_role=FREE_STANDARD_ROLE,
        )
        if not reset_ok:
            raise ProvisioningError("target_traffic_reset_failed")
    if superseded_check is not None and superseded_check():
        await _compensate_superseded_free_job(prepared, panel)
        return "superseded"
    source_bindings = prepared.source_bindings
    if not source_bindings and prepared.source_node_code:
        source_bindings = ((prepared.source_node_code, str(prepared.source_role or "")),)
    for source_node_code, source_role in source_bindings:
        if source_node_code == prepared.target_node_code:
            continue
        disabled = await panel.set_user_profile_enabled_on_node(
            tg_id=prepared.tg_id,
            node_code=source_node_code,
            expected_access_role=source_role,
            enable=False,
            sub_id=prepared.sub_id,
        )
        if not disabled:
            raise ProvisioningError("source_disable_failed")
        if superseded_check is not None and superseded_check():
            await _compensate_superseded_free_job(prepared, panel)
            return "superseded"
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
        key.key_uuid = str(prepared.replacement_key_uuid or "")
        key.state = "active"
        key.rotated_at = now
        key.updated_at = now
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
            outcome = "superseded"
        else:
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


def _mark_completed_compensation_failure(
    session,
    *,
    claim: ClaimedJob,
    code: str,
    now: datetime,
) -> bool:
    job = _lock_exact_query(
        session.query(NodeProvisioningJob).filter(NodeProvisioningJob.id == int(claim.id)),
        session,
    ).first()
    if job is None or job.status != "succeeded":
        return False
    normalized = str(code or "superseded_compensation_failed").strip()[:64]
    job.status = "manual_review"
    job.manual_review_at = now
    job.last_error_code = normalized
    job.result_json = _result_json(outcome="manual_review", code=normalized, attempt=int(job.attempts or 0))
    job.updated_at = now
    return True


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
    if normalized.startswith("superseded_"):
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
        try:
            with session_factory() as session:
                prepared = _prepare_job(session, claim)
            outcome = await _execute_panel(
                prepared,
                panel,
                superseded_check=lambda: _claim_was_superseded(
                    session_factory,
                    claim=claim,
                    prepared=prepared,
                ),
            )
            finalized_at = current if now is not None else _utcnow()
            with session_factory() as session:
                finalized_outcome = _finalize_success(
                    session,
                    claim=claim,
                    prepared=prepared,
                    outcome=outcome,
                    now=finalized_at,
                )
                session.commit()
            if finalized_outcome == "superseded" and outcome != "superseded":
                try:
                    await _compensate_superseded_free_job(prepared, panel)
                except ProvisioningError as exc:
                    with session_factory() as session:
                        marked = _mark_completed_compensation_failure(
                            session,
                            claim=claim,
                            code=exc.code,
                            now=finalized_at,
                        )
                        session.commit()
                    if marked:
                        result["manual_review"] = int(result["manual_review"]) + 1
                    continue
            if finalized_outcome != "claim_lost":
                result["succeeded"] = int(result["succeeded"]) + 1
        except ProvisioningError as exc:
            failure_code = exc.code
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
