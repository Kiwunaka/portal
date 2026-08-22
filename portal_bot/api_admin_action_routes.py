"""Guarded administrative action-intent orchestration and HTTP bindings.

Loaded after the base admin slice and before guarded network routes. Public
symbols are re-exported through the legacy ``api`` composition root.
"""

try:
    from .module_slices import bootstrap_slice
except ImportError:
    from module_slices import bootstrap_slice

bootstrap_slice(globals())

def _raise_action_intent_http(error: ActionIntentError) -> None:
    detail: dict[str, Any] = {
        "code": str(error.code),
        "message": str(error.message),
    }
    if error.intent_id:
        detail["intent_id"] = str(error.intent_id)
    if error.audit_id is not None:
        detail["audit_id"] = int(error.audit_id)
    raise HTTPException(
        status_code=int(error.status_code),
        detail=detail,
    )


def _raise_action_intent_header_required(
    *,
    actor_tg_id: int,
    intent_id: str,
    code: str,
    message: str,
) -> None:
    owned_intent_id, audit_id = _action_intent_error_identifiers(
        session_factory=SessionLocal,
        actor_tg_id=actor_tg_id,
        intent_id=intent_id,
    )
    _raise_action_intent_http(
        ActionIntentError(
            code,
            status_code=428,
            message=message,
            intent_id=owned_intent_id,
            audit_id=audit_id,
        )
    )


_OPERATOR_WORK_ACTIONS = frozenset(
    {
        "operator_task.create",
        "operator_task.update",
        "incident.create",
        "incident.update",
        "incident.link",
        "incident.compensate",
        "alert.ack",
        "alert.create_incident",
        "alert.link_incident",
        "alert.false_positive",
    }
)


def _operator_action_payload_for_actor(
    session,
    *,
    actor_tg_id: int,
    action: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    normalized_action = str(action or "").strip().lower()
    if normalized_action not in _OPERATOR_WORK_ACTIONS:
        return dict(payload)
    operator = (
        session.query(AdminOperator)
        .filter(
            AdminOperator.legacy_actor_tg_id == int(actor_tg_id),
            AdminOperator.status == "active",
        )
        .one_or_none()
    )
    if operator is None:
        raise ActionIntentError(
            "operator_identity_required",
            status_code=409,
            message="Сначала откройте Operator Center и создайте защищённую операторскую сессию.",
        )
    enriched = dict(payload)
    enriched.update(
        {
            "_environment": str(_ADMIN_V2_RUNTIME.config.environment),
            "_operator_id": str(operator.id),
            "_actor_tg_id": int(actor_tg_id),
        }
    )
    return enriched


def _stored_operator_intent_command(
    *,
    actor_tg_id: int,
    request: Request,
    action: str,
    target_type: str,
    target_id: str | None = None,
) -> tuple[str, dict[str, Any]]:
    intent_id = str(request.headers.get("X-Admin-Intent-Id") or "").strip()
    if not intent_id:
        raise HTTPException(
            status_code=428,
            detail={
                "code": "intent_required",
                "message": "Сначала создайте защищённое намерение через серверный предпросмотр.",
            },
        )
    session = SessionLocal()
    try:
        intent = (
            session.query(AdminActionIntent)
            .filter(
                AdminActionIntent.id == intent_id,
                AdminActionIntent.actor_tg_id == int(actor_tg_id),
            )
            .one_or_none()
        )
        if (
            intent is None
            or str(intent.action) != str(action)
            or str(intent.target_type) != str(target_type)
            or (target_id is not None and str(intent.target_id) != str(target_id))
        ):
            raise HTTPException(
                status_code=409,
                detail={"code": "intent_mismatch", "message": "Intent выпущен для другой команды."},
            )
        try:
            payload = json.loads(str(intent.canonical_payload_json or "{}"))
        except (TypeError, ValueError):
            payload = None
        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=409,
                detail={"code": "intent_payload_invalid", "message": "Payload intent недоступен."},
            )
        return str(intent.target_id), payload
    finally:
        session.close()
async def _execute_node_resync_external(context: dict[str, Any]) -> dict[str, Any]:
    execution = context.get("execution")
    if not isinstance(execution, dict):
        raise RuntimeError("missing frozen resync execution context")
    source_node_id = int(execution.get("source_node_id") or 0)
    source_code = str(execution.get("source_node_code") or "").strip().lower()
    selection = execution.get("selection")
    dry_run = bool(execution.get("dry_run", False))
    if source_node_id <= 0 or not source_code or not isinstance(selection, list):
        raise RuntimeError("invalid frozen resync execution context")

    selected_count = len(selection)
    skipped = sum(
        1
        for item in selection
        if isinstance(item, dict) and not item.get("target_nodes")
    )
    if dry_run:
        return {
            "ok": True,
            "code": "resync_dry_run_completed",
            "count": selected_count,
            "changed": 0,
            "failed": 0,
            "skipped": skipped,
        }

    panel = ControlPanel()
    migrated = 0
    failed = 0
    try:
        await panel.login()
        for item in selection:
            if not isinstance(item, dict):
                raise RuntimeError("invalid frozen resync item")
            source_user_node_id = int(item.get("source_user_node_id") or 0)
            recipient_fingerprint = str(item.get("recipient_fingerprint") or "")
            raw_target_nodes = item.get("target_nodes")
            if not isinstance(raw_target_nodes, list):
                raise RuntimeError("invalid frozen target nodes")
            target_nodes: list[dict[str, Any]] = []
            seen_target_ids: set[int] = set()
            seen_target_codes: set[str] = set()
            for raw_target in raw_target_nodes:
                if not isinstance(raw_target, dict):
                    raise RuntimeError("invalid frozen target node")
                target_node_id = int(raw_target.get("id") or 0)
                target_code = str(raw_target.get("code") or "").strip().lower()
                if (
                    target_node_id <= 0
                    or not target_code
                    or target_node_id in seen_target_ids
                    or target_code in seen_target_codes
                ):
                    raise RuntimeError("invalid frozen target node")
                seen_target_ids.add(target_node_id)
                seen_target_codes.add(target_code)
                target_nodes.append({"id": target_node_id, "code": target_code})
            target_codes = [str(target["code"]) for target in target_nodes]
            if source_user_node_id <= 0:
                raise RuntimeError("invalid frozen source mapping")
            if not target_nodes:
                continue

            session = SessionLocal()
            try:
                row = (
                    session.query(UserNode, User)
                    .join(User, User.tg_id == UserNode.tg_id)
                    .filter(
                        UserNode.id == source_user_node_id,
                        UserNode.node_id == source_node_id,
                    )
                    .first()
                )
                if row is None:
                    failed += 1
                    continue
                source_mapping, user = row
                source_node = session.query(Node).filter(Node.id == source_node_id).first()
                if (
                    source_node is None
                    or str(source_node.code or "").strip().lower() != source_code
                ):
                    failed += 1
                    continue
                tg_id = int(user.tg_id)
                client_uuid = str(user.uuid)
                panel_email = str(user.email)
                sub_id = str(getattr(user, "sub_token", "") or user.tg_id)
                current_recipient_fingerprint = _node_resync_recipient_fingerprint(
                    tg_id=tg_id,
                    mapping_client_uuid=str(source_mapping.client_uuid or ""),
                    mapping_panel_email=str(source_mapping.panel_email or ""),
                    user_uuid=client_uuid,
                    user_email=panel_email,
                    sub_id=sub_id,
                )
                if not hmac.compare_digest(
                    recipient_fingerprint,
                    current_recipient_fingerprint,
                ):
                    failed += 1
                    continue
            finally:
                session.close()

            ensure_results = await panel.ensure_user_on_all_nodes(
                tg_id=tg_id,
                client_uuid=client_uuid,
                email=panel_email,
                sub_id=sub_id,
                enable=True,
                only_node_codes=target_codes,
            )
            successful_codes = {
                str(code or "").strip().lower()
                for code, value in ensure_results.items()
                if bool(value) and str(code or "").strip().lower() in seen_target_codes
            }
            if not successful_codes:
                failed += 1
                continue

            disable_results = await panel.set_existing_user_enabled_on_nodes(
                tg_id=tg_id,
                node_codes=[source_code],
                enable=False,
                sub_id=sub_id,
            )
            source_disabled = any(
                str(code or "").strip().lower() == source_code and bool(value)
                for code, value in disable_results.items()
            )
            if not source_disabled:
                failed += 1
                continue

            session = SessionLocal()
            try:
                target_ids = [int(target["id"]) for target in target_nodes]
                dialect = str(session.get_bind().dialect.name)
                if dialect == "postgresql":
                    for locked_node_id in sorted({source_node_id, *target_ids}):
                        session.execute(
                            sql_text(
                                "SELECT pg_advisory_xact_lock(:lock_namespace, :node_id)"
                            ),
                            {
                                "lock_namespace": NODE_MAPPING_LOCK_NAMESPACE,
                                "node_id": int(locked_node_id),
                            },
                        )
                source_query = session.query(Node).filter(Node.id == source_node_id)
                target_query = session.query(Node).filter(Node.id.in_(target_ids))
                if dialect == "postgresql":
                    source_query = source_query.with_for_update()
                    target_query = target_query.with_for_update()
                current_source = source_query.first()
                current_targets = target_query.all()
                current_by_id = {int(node.id): node for node in current_targets}
                frozen_targets_match = (
                    current_source is not None
                    and str(current_source.code or "").strip().lower() == source_code
                    and len(current_by_id) == len(target_nodes)
                    and all(
                        int(target["id"]) in current_by_id
                        and str(current_by_id[int(target["id"])].code or "").strip().lower()
                        == str(target["code"])
                        for target in target_nodes
                    )
                )
                if not frozen_targets_match:
                    session.rollback()
                    failed += 1
                    continue
                successful_targets = [
                    current_by_id[int(target["id"])]
                    for target in target_nodes
                    if str(target["code"]) in successful_codes
                ]
                successful_targets_valid = bool(successful_targets) and all(
                    bool(target.enabled)
                    and bool(target.accepting_new_clients)
                    and not bool(target.is_draining)
                    for target in successful_targets
                )
                if not successful_targets_valid:
                    session.rollback()
                    failed += 1
                    continue
                existing_node_ids = {
                    int(row.node_id)
                    for row in session.query(UserNode)
                    .filter(UserNode.tg_id == tg_id)
                    .all()
                }
                for target_node in successful_targets:
                    if int(target_node.id) in existing_node_ids:
                        continue
                    session.add(
                        UserNode(
                            tg_id=tg_id,
                            node_id=int(target_node.id),
                            client_uuid=client_uuid,
                            panel_email=panel_email,
                        )
                    )
                deleted = session.query(UserNode).filter(
                    UserNode.id == source_user_node_id,
                    UserNode.node_id == source_node_id,
                ).delete(synchronize_session=False)
                if deleted != 1:
                    session.rollback()
                    failed += 1
                    continue
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
            migrated += 1
    finally:
        await panel.close()

    return {
        "ok": failed == 0,
        "code": "resync_completed" if failed == 0 else "resync_partial",
        "count": selected_count,
        "changed": migrated,
        "failed": failed,
        "skipped": skipped,
    }


_TASK20_DB_ACTIONS = frozenset(
    {
        "plan.create",
        "plan.update",
        "plan.delete",
        "live_update.create",
        "live_update.update",
        "live_update.delete",
        "start_link.create",
        "start_link.update",
        "start_link.delete",
        "wheel_config.update",
        "network_rollout_config.update",
        "warp_material.replace",
        "awg2_lab_material.replace",
        "promo_slots.update",
        "loyalty_config.update",
        "campaign.create",
        "campaign.update",
        "campaign.delete",
        "template.create",
        "template.update",
        "template.delete",
        "access_key.issue",
        "gift_code.create",
    }
)


def _execute_task20_admin_action_db(
    session,
    state,
    runtime: dict[str, Any],
    *,
    actor_tg_id: int,
    action: str,
) -> dict[str, Any]:
    now = _utcnow()

    if action in {"plan.create", "plan.update", "plan.delete"}:
        row = state.entity
        if action == "plan.delete":
            if row is None:
                raise ActionIntentError("target_not_found", status_code=404, message="План не найден.")
            code = str(row.code or "").strip().lower()
            session.delete(row)
            session.flush()
            return {"code": code, "deleted": True}
        if action == "plan.create":
            if row is not None:
                raise ActionIntentError("target_exists", status_code=409, message="План уже существует.")
            row = PlanCatalog(code=str(runtime["code"]), created_at=now)
            session.add(row)
        for field in (
            "label",
            "amount_rub",
            "amount_stars",
            "days",
            "device_limit",
            "node_policy",
            "badge",
            "is_active",
            "sort_order",
        ):
            if field in runtime:
                setattr(row, field, runtime[field])
        row.updated_at = now
        session.flush()
        return {"code": str(row.code or "").strip().lower()}

    if action in {"live_update.create", "live_update.update", "live_update.delete"}:
        row = state.entity
        if action == "live_update.delete":
            if row is None:
                raise ActionIntentError("target_not_found", status_code=404, message="Новость не найдена.")
            update_id = int(row.id)
            session.delete(row)
            session.flush()
            return {"id": update_id, "deleted": True}
        if action == "live_update.create":
            row = LiveUpdate(created_at=now, updated_at=now)
            session.add(row)
        for field in ("title", "summary", "is_active", "sort_order"):
            if field in runtime:
                setattr(row, field, runtime[field])
        if "link" in runtime and runtime["link"] is not None:
            row.link = str(runtime["link"])
        if "channel_username" in runtime:
            row.channel_username = runtime["channel_username"]
        if "post_id" in runtime:
            row.post_id = runtime["post_id"]
        if "published_at" in runtime:
            row.published_at = (
                datetime.fromisoformat(str(runtime["published_at"]))
                if runtime["published_at"]
                else None
            )
        row.link = _build_tg_post_link(
            channel_username=getattr(row, "channel_username", None),
            post_id=getattr(row, "post_id", None),
            fallback_link=str(getattr(row, "link", "") or "").strip(),
        )
        if not str(row.link or "").strip():
            raise ActionIntentError("invalid_payload", status_code=422, message="Нужна ссылка или Telegram post target.")
        row.updated_at = now
        session.flush()
        source_draft_id = int(runtime.get("source_draft_id") or 0)
        if source_draft_id:
            draft = (
                session.query(NewsDraft)
                .filter(NewsDraft.id == source_draft_id)
                .with_for_update()
                .first()
            )
            if draft is None:
                raise ActionIntentError("target_not_found", status_code=404, message="Черновик новости не найден.")
            if str(draft.status or "").strip().lower() != "pending" or draft.live_update_id is not None:
                raise ActionIntentError("state_changed", status_code=409, message="Черновик уже обработан.")
            draft.status = "approved"
            draft.reviewed_by_tg_id = int(actor_tg_id)
            draft.reviewed_at = now
            draft.live_update_id = int(row.id)
            session.flush()
        return {"id": int(row.id), "source_draft_id": source_draft_id or None}

    if action in {"start_link.create", "start_link.update", "start_link.delete"}:
        row = state.entity
        if action == "start_link.delete":
            if row is None:
                raise ActionIntentError("target_not_found", status_code=404, message="Start link не найден.")
            row.is_active = False
            row.updated_at = now
            session.flush()
            return {"id": int(row.id), "code": str(row.code or "").strip().lower(), "deleted": True}
        if action == "start_link.create":
            row = StartLink(code=str(runtime["code"]), created_at=now, updated_at=now)
            session.add(row)
        if "code" in runtime and str(runtime["code"]) != str(row.code or "").strip().lower():
            duplicate = session.query(StartLink.id).filter(
                func.lower(StartLink.code) == str(runtime["code"]),
                StartLink.id != int(row.id),
            ).first()
            if duplicate:
                raise ActionIntentError("target_exists", status_code=409, message="Start link уже существует.")
            row.code = str(runtime["code"])
        for field in ("description", "target_action", "is_active"):
            if field in runtime:
                setattr(row, field, runtime[field])
        row.updated_at = now
        session.flush()
        return {"id": int(row.id), "code": str(row.code or "").strip().lower()}

    if action == "wheel_config.update":
        try:
            config = parse_paid_weekly_config(runtime, explicit=True)
        except InvalidWheelConfig:
            raise ActionIntentError(
                "wheel_config_invalid",
                status_code=400,
                message="wheel_config_invalid",
            ) from None
        normalized = {
            "preset": config.preset,
            "weights": [
                (
                    {"days": int(outcome.value), "weight": int(outcome.weight)}
                    if config.preset == "paid_weekly_v1"
                    else {
                        "kind": outcome.kind,
                        "value": int(outcome.value),
                        "weight": int(outcome.weight),
                    }
                )
                for outcome in config.outcomes
            ],
            "cooldown_hours": int(config.cooldown_hours),
        }
        _set_app_setting_json(s=session, key="wheel_config", value=normalized)
        session.flush()
        return {"wheel_config": normalized}

    if action == "network_rollout_config.update":
        normalized = normalized_network_rollout_config(runtime)
        _set_app_setting_json(s=session, key=NETWORK_ROLLOUT_CONFIG_KEY, value=normalized)
        session.flush()
        return {"network_rollout_config": normalized}

    if action == "promo_slots.update":
        normalized = _normalized_promo_slots_config(runtime, strict=True)
        _set_app_setting_json(
            s=session,
            key=PROMO_SLOTS_CONFIG_KEY,
            value={"assignments": normalized.get("assignments") or []},
        )
        session.flush()
        return {"promo_slots": normalized}

    if action == "loyalty_config.update":
        normalized = _normalized_loyalty_config(runtime)
        _set_app_setting_json(s=session, key="loyalty_config", value=normalized)
        session.flush()
        return {"loyalty_config": normalized}

    if action == "warp_material.replace":
        user = state.entity
        install_id = str(runtime.get("install_id") or getattr(user, "app_install_id", "") or "").strip() or None
        limit, window_seconds = _warp_material_provision_limit()
        if limit and _warp_event_count(
            session,
            user=user,
            install_id=install_id,
            event_name="material_provisioned",
            window_seconds=window_seconds,
        ) >= limit:
            raise ActionIntentError(
                "warp_material_rate_limited",
                status_code=429,
                message="Лимит замены WARP material исчерпан.",
            )
        try:
            row = provision_warp_material(
                session,
                user=user,
                install_id=install_id,
                wireguard_config=dict(runtime["wireguard_config"]),
                account=dict(runtime.get("account") or {}),
                source=str(runtime["source"]),
                mode=str(runtime["mode"]),
            )
            session.flush()
            policy = public_warp_policy_for_user(
                session,
                user=user,
                install_id=install_id,
                rollout_config=load_network_rollout_config(session=session),
            )
            record_warp_event(
                session,
                user=user,
                install_id=install_id,
                policy=policy,
                event_name="material_provisioned",
                state="ready_to_consent",
                reason_code="admin_provisioned",
                consented=False,
                meta={"source": "admin", "actor_tg_id": int(actor_tg_id), "material_id": int(row.id or 0)},
            )
            session.flush()
        except ValueError:
            raise ActionIntentError("invalid_warp_material", status_code=422, message="WARP material не прошёл проверку.") from None
        except RuntimeError:
            raise ActionIntentError("warp_material_store_unavailable", status_code=503, message="Хранилище WARP material недоступно.") from None
        material = warp_material_public_payload(row, policy=policy)
        status = build_warp_status(session, user=user, install_id=install_id, policy=policy)
        return {"material": material, "warp_status": status}

    if action == "awg2_lab_material.replace":
        try:
            row = replace_awg2_lab_material(
                session,
                tg_id=int(runtime["tg_id"]),
                install_id=str(runtime["install_id"]),
                generation=str(runtime["generation"]),
                endpoint_revision=str(runtime["endpoint_revision"]),
                server_record_id=str(runtime["server_record_id"]),
                node_code=str(runtime["node_code"]),
                endpoint=dict(runtime["endpoint"]),
            )
            session.flush()
        except Awg2LabError:
            raise ActionIntentError(
                "invalid_awg2_lab_material",
                status_code=422,
                message="AWG2 lab material не прошёл проверку.",
            ) from None
        return {"material": safe_awg2_material_summary(row)}

    if action in {"campaign.create", "campaign.update", "campaign.delete"}:
        row = state.entity
        decision = dict(state.context.get("policy") or {})
        after_runtime = dict(state.context.get("after_runtime") or {})
        if action == "campaign.delete":
            if row is None:
                raise ActionIntentError("target_not_found", status_code=404, message="Кампания не найдена.")
            if str(getattr(row, "lifecycle_status", "") or "").strip().lower() == "killed":
                return {
                    "id": int(row.id),
                    "public_id": str(getattr(row, "public_id", "") or "") or None,
                    "revision": max(1, int(getattr(row, "revision", 1) or 1)),
                    "lifecycle_status": "killed",
                    "killed": True,
                }
            row.is_active = False
            row.lifecycle_status = "killed"
            row.state_reason = "owner_killed"
            row.killed_at = now
            row.last_policy_evaluated_at = now
            row.capacity_band = str((decision.get("capacity") or {}).get("band") or "unknown")
            row.revision = max(1, int(getattr(row, "revision", 1) or 1)) + 1
            row.updated_at = now
            session.flush()
            return {
                "id": int(row.id),
                "public_id": str(getattr(row, "public_id", "") or "") or None,
                "revision": int(row.revision),
                "lifecycle_status": "killed",
                "killed": True,
                "deleted": True,
            }
        requested_lifecycle = str(after_runtime.get("lifecycle_status") or "draft").strip().lower()
        if requested_lifecycle == "live" and not bool(decision.get("activation_allowed")):
            raise ActionIntentError(
                "campaign_policy_blocked",
                status_code=409,
                message=(
                    "Кампания не может стать live: "
                    + str(decision.get("reason_code") or "policy_blocked")
                    + "."
                ),
            )
        if action == "campaign.create":
            row = IncentiveCampaign(
                public_id=str(after_runtime["public_id"]),
                campaign_type=str(runtime["campaign_type"]),
                target_value=str(runtime["target_value"]),
                activations_count=0,
                paid_conversions_count=0,
                revision=1,
                created_by=int(actor_tg_id),
                created_at=now,
                updated_at=now,
            )
            session.add(row)
        for field in ("name", "segment", "max_activations", "auto_disable", "is_active"):
            if field in runtime:
                setattr(row, field, runtime[field])
        for field in ("starts_at", "ends_at"):
            if field in runtime:
                setattr(row, field, datetime.fromisoformat(str(runtime[field])) if runtime[field] else None)
        if row.starts_at and row.ends_at and row.starts_at > row.ends_at:
            raise ActionIntentError("invalid_payload", status_code=422, message="starts_at должен быть не позже ends_at.")
        if "metadata" in runtime:
            row.metadata_json = json.dumps(runtime["metadata"], ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        row.objective = str(after_runtime.get("objective") or "retention")
        row.lifecycle_status = requested_lifecycle
        row.commercial_revision = str(after_runtime.get("commercial_revision") or "") or None
        row.legal_profile_status = str(after_runtime.get("legal_profile_status") or "missing")
        row.channels_json = json.dumps(
            normalize_campaign_channels(after_runtime.get("channels")),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        row.seller_profile_id = str(after_runtime.get("seller_profile_id") or "") or None
        row.terms_revision = str(after_runtime.get("terms_revision") or "") or None
        row.paid_cap = max(0, int(after_runtime.get("paid_cap") or 0))
        row.capacity_guard_enabled = bool(after_runtime.get("capacity_guard_enabled", True))
        row.capacity_band = str((decision.get("capacity") or {}).get("band") or "unknown")
        row.last_policy_evaluated_at = now
        reason_by_lifecycle = {
            "draft": "draft",
            "review": "pending_review",
            "approved": "approved_not_live",
            "live": "ready",
            "paused": "owner_paused",
            "ended": "ended",
        }
        requested_reason = str(after_runtime.get("state_reason") or "").strip().lower()
        row.state_reason = (
            requested_reason
            if requested_lifecycle == "paused" and requested_reason
            else reason_by_lifecycle.get(requested_lifecycle, "legacy_unclassified")
        )
        row.is_active = requested_lifecycle == "live"
        if action == "campaign.update":
            row.revision = max(1, int(getattr(row, "revision", 1) or 1)) + 1
        row.updated_at = now
        session.flush()
        return {
            "id": int(row.id),
            "public_id": str(row.public_id),
            "revision": int(row.revision),
            "lifecycle_status": str(row.lifecycle_status),
            "policy": decision,
        }

    if action in {"template.create", "template.update", "template.delete"}:
        row = state.entity
        if action == "template.delete":
            if row is None:
                raise ActionIntentError("target_not_found", status_code=404, message="Шаблон не найден.")
            key = str(row.key or "").strip().lower()
            session.delete(row)
            session.flush()
            return {"key": key, "deleted": True}
        if action == "template.create":
            row = Template(key=str(runtime["key"]), text=str(runtime["text"]), created_at=now)
            session.add(row)
        new_key = runtime.get("new_key")
        if new_key and str(new_key) != str(row.key or "").strip().lower():
            duplicate = session.query(Template.id).filter(
                func.lower(Template.key) == str(new_key),
                Template.id != int(row.id),
            ).first()
            if duplicate:
                raise ActionIntentError("target_exists", status_code=409, message="Ключ шаблона уже существует.")
            row.key = str(new_key)
        if "text" in runtime:
            row.text = str(runtime["text"])
        session.flush()
        return {"key": str(row.key or "").strip().lower()}

    if action == "access_key.issue":
        plan_code = str(runtime["plan_code"])
        plan = _resolve_plan_config(s=session, code=plan_code)
        normalized_plan = _normalized_plan_payload(plan, fallback_code=plan_code)
        if not normalized_plan:
            raise ActionIntentError("invalid_payload", status_code=422, message="plan_code не поддерживается.")
        issued: list[dict[str, Any]] = []
        issued_rows: list[GiftCard] = []
        for _ in range(int(runtime["quantity"])):
            code = _generate_gift_code_for_admin(session)
            row = GiftCard(
                code=code,
                card_type=normalized_plan["code"],
                created_by=int(actor_tg_id),
                created_at=now,
            )
            session.add(row)
            issued_rows.append(row)
            issued.append({"key": code, "plan": normalized_plan, "issued_at": _safe_iso(now)})
        session.flush()
        return {
            "plan": normalized_plan,
            "issued": issued,
            "_issued_card_ids": [int(row.id) for row in issued_rows],
        }

    if action == "gift_code.create":
        card_type = str(runtime["card_type"])
        card = GIFT_CARD_TYPES.get(card_type)
        if not card:
            raise ActionIntentError("invalid_payload", status_code=422, message="card_type не поддерживается.")
        code = _generate_gift_code_for_admin(session)
        row = GiftCard(
            code=code,
            card_type=card_type,
            created_by=int(actor_tg_id),
            created_at=now,
        )
        session.add(row)
        session.flush()
        return {
            "_issued_card_ids": [int(row.id)],
            "gift_code": {
                "code": code,
                "card_type": card_type,
                "days": int(card.get("days", 0)),
                "stars": int(card.get("stars", 0)),
            }
        }

    raise ActionIntentError("executor_unavailable", status_code=503, message="DB-исполнитель действия недоступен.")


def _execute_admin_client_action_db(
    session,
    state,
    payload: dict[str, Any],
    _runtime_payload: dict[str, Any],
    *,
    actor_tg_id: int,
    action: str,
) -> dict[str, Any]:
    if action in _TASK20_DB_ACTIONS:
        return _execute_task20_admin_action_db(
            session,
            state,
            dict(_runtime_payload),
            actor_tg_id=actor_tg_id,
            action=action,
        )

    if action == "user.migration_code":
        user = state.entity
        now = _utcnow()
        ensure_user_account_foundation(session, user, now=now)
        account_id = str(user.account_id or "").strip()
        if not account_id:
            raise ActionIntentError(
                "account_not_ready",
                status_code=409,
                message="Аккаунт пользователя ещё не подготовлен для переноса.",
            )
        issued = device_pairing_service.issue_pairing_code(
            session,
            account_id=account_id,
            issued_by_session_id=None,
            now=now,
        )
        return {
            "code": "migration_code_issued",
            "tg_id": int(user.tg_id),
            "pairing_code": issued.code,
            "code_hint": str(issued.row.code_hint),
            "expires_at": _safe_iso(issued.row.expires_at),
            "ttl_seconds": int(device_pairing_service.PAIRING_CODE_TTL_SECONDS),
        }

    if action == "payment.reconcile":
        order = state.entity
        next_status = str(state.context["to_status"])
        operator_note = str(_runtime_payload["note"])
        order_meta = _json_obj(order.meta_json)
        existing = order_meta.get("admin_reconciliations")
        reconciliations = [
            item
            for item in (existing[-49:] if isinstance(existing, list) else [])
            if isinstance(item, dict)
        ]
        reconciliations.append(
            {
                "at": _safe_iso(_utcnow()),
                "actor_tg_id": int(actor_tg_id),
                "from_status": str(state.context["from_status"]),
                "to_status": next_status,
                "note": operator_note,
            }
        )
        order_meta["admin_reconciliations"] = reconciliations
        order.meta_json = json.dumps(order_meta, ensure_ascii=False, separators=(",", ":"))
        order.status = next_status
        if next_status == "paid" and not order.paid_at:
            order.paid_at = _utcnow()
        session.flush()
        return {
            "order_db_id": int(order.id),
            "provider": str(order.provider or ""),
            "order_id": str(order.order_id or ""),
            "order_status": str(order.status or ""),
        }

    if action in {"promo.create", "promo.update", "promo.delete"}:
        promo = state.entity
        if action == "promo.delete":
            if promo is None:
                raise ActionIntentError(
                    "target_not_found",
                    status_code=404,
                    message="Промокод не найден.",
                )
            deleted_code = str(promo.code or "").upper()
            session.delete(promo)
            session.flush()
            return {"code": deleted_code, "deleted": True}

        after = dict(state.context["after_snapshot"])
        if action == "promo.create":
            if promo is not None:
                raise ActionIntentError(
                    "target_exists",
                    status_code=409,
                    message="Промокод уже существует.",
                )
            promo = PromoCode(created_at=_utcnow())
            session.add(promo)
        promo.code = str(after["promo_code"])
        promo.promo_type = str(after["promo_type"])
        promo.value = int(after["value"])
        promo.uses_left = int(after["uses_left"])
        promo.expires_at = (
            datetime.fromisoformat(str(after["expires_at"]))
            if after.get("expires_at")
            else None
        )
        session.flush()
        return {"code": str(promo.code or "").upper(), "deleted": False}

    if action == "referral.process":
        now = _utcnow()
        processed = 0
        rewarded = 0
        waiting = 0
        rejected = 0
        queue_ids: list[int] = []
        for row in list(state.entity):
            processed += 1
            queue_ids.append(int(row.id))
            referred = session.query(User).filter(User.tg_id == int(row.referred_tg_id)).first()
            referrer = session.query(User).filter(User.tg_id == int(row.referrer_tg_id)).first()
            if referred is None or referrer is None:
                row.status = "rejected_missing_user"
                row.processed_at = now
                rejected += 1
                continue
            has_activity = (
                session.query(Event.id)
                .filter(
                    Event.tg_id == int(referred.tg_id),
                    Event.created_at >= (row.queued_at or (now - timedelta(days=1))),
                    Event.event_name.in_(["connected_ok", "clicked_connect"]),
                )
                .first()
                is not None
            )
            age_hours = max(
                0,
                int((now - (row.queued_at or now)).total_seconds() // 3600),
            )
            if not has_activity and not bool(payload["force_without_activity"]):
                if age_hours >= int(REFERRAL_ANTIFRAUD_MAX_WAIT_HOURS):
                    row.status = "rejected_no_activity"
                    row.processed_at = now
                    rejected += 1
                else:
                    row.ready_at = now + timedelta(hours=6)
                    waiting += 1
                continue
            ref_sub = str(referrer.sub_type or "").upper().strip()
            ref_expiry = referrer.expiry_at if referrer.expiry_at and referrer.expiry_at > now else None
            if not (bool(referrer.is_active) and ref_sub == "PAID" and ref_expiry):
                row.status = "rejected_referrer_inactive"
                row.processed_at = now
                rejected += 1
                continue
            row_meta = _json_obj(getattr(row, "meta", None))
            if not bool(row_meta.get("counted")):
                referrer.referral_count = int(referrer.referral_count or 0) + 1
            referrer.expiry_at = ref_expiry + timedelta(days=max(1, int(REFERRAL_BONUS_DAYS)))
            referrer.is_active = True
            row.status = "rewarded"
            row.processed_at = now
            rewarded += 1
        session.flush()
        return {
            "processed": processed,
            "rewarded": rewarded,
            "waiting": waiting,
            "rejected": rejected,
            "queue_ids": queue_ids,
        }

    if action in {"provider_quota.create", "provider_quota.update"}:
        node_code = str(state.context["node_code"])
        row = state.entity
        before = _provider_quota_audit_payload(row)
        now = _utcnow()
        if action == "provider_quota.create":
            if row is not None:
                raise ActionIntentError(
                    "target_exists",
                    status_code=409,
                    message="Квота провайдера для этой ноды уже настроена.",
                )
            row = ProviderTrafficQuota(node_code=node_code, created_at=now)
            session.add(row)
            quota_action = "create"
        else:
            if row is None:
                raise ActionIntentError(
                    "target_not_found",
                    status_code=404,
                    message="Квота провайдера не найдена.",
                )
            quota_action = "update"
        proposed = dict(state.context.get("proposed_config") or {})
        row.included_bytes = int(proposed["included_bytes"])
        row.reset_day = int(proposed["reset_day"])
        row.timezone = str(proposed["timezone"])
        row.warning_ratio = float(proposed["warning_ratio"])
        row.critical_ratio = float(proposed["critical_ratio"])
        row.enabled = bool(proposed["enabled"])
        row.notes = proposed.get("notes")
        row.updated_by = int(actor_tg_id)
        row.updated_at = now
        session.flush()
        after = _provider_quota_safe_payload(row)
        assert after is not None
        _add_provider_quota_audit(
            s=session,
            quota=row,
            node_code=node_code,
            actor=actor_tg_id,
            action=quota_action,
            before=before,
            after=after,
        )
        return {"quota": after, "node_code": node_code}

    if action == "provider_quota.delete":
        row = state.entity
        node_code = str(state.context["node_code"])
        if row is None:
            raise ActionIntentError(
                "target_not_found",
                status_code=404,
                message="Квота провайдера не найдена.",
            )
        before = _provider_quota_audit_payload(row)
        _add_provider_quota_audit(
            s=session,
            quota=row,
            node_code=node_code,
            actor=actor_tg_id,
            action="delete",
            before=before,
            after=None,
        )
        session.delete(row)
        session.flush()
        return {"node_code": node_code, "deleted": True}

    if action == "user.extend":
        user = state.entity
        now = _utcnow()
        current = user.expiry_at if user.expiry_at and user.expiry_at > now else now
        candidate = current + timedelta(days=int(payload["delta_days"]))
        if candidate <= now:
            if not bool(payload["allow_deactivate"]):
                raise ActionIntentError(
                    "would_deactivate",
                    status_code=409,
                    message="Операция деактивирует пользователя; подтвердите allow_deactivate=true.",
                )
            user.expiry_at = now
            user.is_active = False
        else:
            user.expiry_at = candidate
            user.is_active = True
            if int(payload["delta_days"]) > 0 and not bool(state.public_snapshot.get("manual_test")):
                plan_code = str(getattr(user, "current_plan_code", "") or "").strip().lower()
                user.sub_type = "PAID"
                if plan_code in {"", "free", "free_monthly", "free_retired", "trial"}:
                    user.current_plan_code = "admin_grant"
        session.flush()
        return {
            "expiry_at": _safe_iso(user.expiry_at),
            "is_active": bool(user.is_active),
            "delta_days": int(payload["delta_days"]),
            "sub_type": str(getattr(user, "sub_type", "") or ""),
            "current_plan_code": str(getattr(user, "current_plan_code", "") or ""),
        }

    if action == "user.key_limits":
        tg_id = int(state.context["tg_id"])
        node = str(payload["node_code"])
        row = (
            session.query(UserKeyPolicy)
            .filter(
                UserKeyPolicy.tg_id == tg_id,
                func.lower(UserKeyPolicy.node_code) == node,
            )
            .first()
        )
        if row is None:
            row = UserKeyPolicy(tg_id=tg_id, node_code=node)
            session.add(row)
        row.burst_mbps = payload["burst_mbps"]
        row.soft_cap_gb = payload["soft_cap_gb"]
        row.hard_cap_gb = payload["hard_cap_gb"]
        row.notify_soft = bool(payload["notify_soft"])
        row.notify_hard = bool(payload["notify_hard"])
        row.auto_disable_on_hard = bool(payload["auto_disable_on_hard"])
        row.updated_by = int(actor_tg_id)
        row.updated_at = _utcnow()
        session.flush()
        row_payload = _serialize_key_policy(row)
        session.add(
            KeyActionHistory(
                tg_id=tg_id,
                node_code=node,
                action="key_limits_update",
                actor_tg_id=int(actor_tg_id),
                source="admin",
                meta=json.dumps(
                    {"policy": row_payload, "apply_now": False, "applied": None},
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                created_at=_utcnow(),
            )
        )
        return {"policy": row_payload, "applied": None}

    if action == "user.preset_run" and payload["preset"] == "extend_1d":
        user = state.entity
        now = _utcnow()
        base = user.expiry_at if user.expiry_at and user.expiry_at > now else now
        user.expiry_at = base + timedelta(days=1)
        user.is_active = True
        session.flush()
        return {
            "preset": "extend_1d",
            "expiry_at": _safe_iso(user.expiry_at),
        }

    if action == "user.bulk_key_action" and bool(payload["dry_run"]):
        return {
            "action": str(payload["action"]),
            "dry_run": True,
            "users": int(state.context["selected_count"]),
            "selection_hash": str(state.context["selection_hash"]),
            "preview_tg_ids": [
                int(value)
                for value in list(state.context["selected_tg_ids"])[:50]
            ],
        }

    if action == "key.rotate":
        key_row = state.entity
        if bool(payload["dry_run"]):
            return {
                "dry_run": True,
                "key_id": int(key_row.id),
                "tg_id": int(key_row.tg_id),
                "node_code": str(key_row.node_code or "") or None,
                "planned_job_type": "rotate_access_key",
            }
        key_row.state = "rotation_requested"
        key_row.updated_at = _utcnow()
        job = NodeProvisioningJob(
            tg_id=int(key_row.tg_id),
            key_id=int(key_row.id),
            node_code=str(key_row.node_code or "") or None,
            job_type="rotate_access_key",
            status="queued",
            desired_state_json=json.dumps(
                {
                    "reason_sha256": str(payload["reason"]["sha256"]),
                    "reason_length": int(payload["reason"]["length"]),
                    "requested_by": int(actor_tg_id),
                    "pool_code": str(key_row.pool_code or ""),
                },
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            created_at=_utcnow(),
            updated_at=_utcnow(),
        )
        session.add(job)
        session.flush()
        return {
            "key_id": int(key_row.id),
            "job_id": int(job.id),
            "job_status": "queued",
        }

    if action == "ticket.status":
        ticket = state.entity
        expected_version = payload.get("expected_version")
        if expected_version is not None and max(1, int(getattr(ticket, "version", 1) or 1)) != int(expected_version):
            raise ActionIntentError(
                "stale_version",
                status_code=409,
                message="Обращение изменилось; обновите карточку и повторите действие.",
            )
        new_status = str(payload["status"])
        set_ticket_status(
            session,
            ticket=ticket,
            status=new_status,
            assigned_admin_tg_id=(
                int(actor_tg_id) if new_status == STATUS_IN_PROGRESS else None
            ),
        )
        session.flush()
        return {"ticket_id": int(ticket.id), "ticket_version": max(1, int(getattr(ticket, "version", 1) or 1))}

    raise ActionIntentError(
        "executor_unavailable",
        status_code=503,
        message="DB-исполнитель действия недоступен.",
    )


async def _execute_admin_client_action_external(
    context: dict[str, Any],
) -> dict[str, Any]:
    action = str(context["action"])
    actor = int(context["actor_tg_id"])
    runtime = dict(context.get("runtime_payload") or {})
    execution = dict(context.get("execution") or {})

    if action == "emergency_catalog.stage":
        try:
            config = load_emergency_catalog_worker_config()
            bundle = await fetch_approved_source_bundle()
            session = SessionLocal()
            try:
                staged = stage_snapshot(
                    session,
                    materials=bundle.materials,
                    source_revision=bundle.source_revision,
                    source_digest=bundle.source_digest,
                    crypto=config.crypto,
                    expected_payload_sha256=config.expected_payload_sha256,
                )
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
        except Exception:
            return {
                "ok": False,
                "code": "emergency_catalog_stage_failed",
                "failed": 1,
            }
        return {
            "ok": True,
            "code": "emergency_catalog_staged" if staged.created else "emergency_catalog_unchanged",
            "count": len(bundle.materials),
            "changed": int(staged.created),
        }

    if action == "user.manual_create":
        tg_id = int(execution["candidate_tg_id"])
        session = SessionLocal()
        try:
            if session.query(User).filter(User.tg_id == tg_id).first() is not None:
                return {"ok": False, "code": "manual_id_conflict", "tg_id": tg_id}
            now = _utcnow()
            user = User(
                tg_id=tg_id,
                username=None,
                uuid=str(uuid.uuid4()),
                email=f"MANUAL_{abs(tg_id)}",
                sub_type="MANUAL",
                current_plan_code="manual",
                created_at=now,
                expiry_at=now + timedelta(days=int(runtime["days"])),
                is_active=True,
                stars_paid=0,
                total_gb=0,
                trial_used=False,
                tos_accepted=True,
                first_purchase_done=True,
                sub_token=_generate_sub_token(),
                is_manual=True,
                created_by_admin=actor,
                display_name=str(runtime["display_name"]),
            )
            session.add(user)
            ensure_user_account_foundation(session, user, now=now)
            session.commit()
            session.refresh(user)
            user_uuid = str(user.uuid or "")
            email = str(user.email or "")
            sub_token = str(user.sub_token or "")
        except IntegrityError:
            session.rollback()
            return {"ok": False, "code": "manual_id_conflict", "tg_id": tg_id}
        finally:
            session.close()
        panel = ControlPanel()
        try:
            await panel.login()
            synced = await panel.ensure_user_on_all_nodes(
                tg_id=tg_id,
                client_uuid=user_uuid,
                email=email,
                sub_id=sub_token or str(tg_id),
                enable=True,
                only_node_codes=None,
            )
            sync_ok = bool(any(synced.values())) if synced else False
        finally:
            await panel.close()
        _key_history_log(
            tg_id=tg_id,
            action="manual_create",
            actor_tg_id=actor,
            meta={"days": int(runtime["days"]), "sync_ok": sync_ok},
        )
        return {
            "ok": True,
            "code": "manual_created",
            "tg_id": tg_id,
            "sync_ok": sync_ok,
        }

    if action == "user.block":
        tg_id = int(execution["tg_id"])
        active = not bool(runtime["blocked"])
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.tg_id == tg_id).first()
            if user is None:
                return {"ok": False, "code": "user_not_found", "tg_id": tg_id}
            user.is_active = active
            user_uuid = str(user.uuid or "")
            session.commit()
        finally:
            session.close()
        panel = ControlPanel()
        try:
            await panel.login()
            await panel.enable_client(user_uuid, enable=active)
        finally:
            await panel.close()
        _key_history_log(
            tg_id=tg_id,
            action="manual_block" if runtime["blocked"] else "manual_unblock",
            actor_tg_id=actor,
            meta={"blocked": bool(runtime["blocked"])},
        )
        return {
            "ok": True,
            "code": "user_block_updated",
            "tg_id": tg_id,
            "is_active": active,
        }

    if action == "user.regenerate_token":
        tg_id = int(execution["tg_id"])
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.tg_id == tg_id).first()
            if user is None:
                return {"ok": False, "code": "user_not_found", "tg_id": tg_id}
            user.sub_token = _generate_sub_token()
            user_uuid = str(user.uuid or "")
            active = bool(user.is_active)
            session.commit()
        finally:
            session.close()
        _process_referral_bonus_queue(limit=100, force_without_activity=False)
        sync_ok = False
        if user_uuid:
            panel = ControlPanel()
            try:
                await panel.login()
                sync_ok = bool(await panel.enable_client(user_uuid, enable=active))
            finally:
                await panel.close()
        _key_history_log(
            tg_id=tg_id,
            action="token_regenerate",
            actor_tg_id=actor,
            meta={"sync_ok": sync_ok},
        )
        return {
            "ok": True,
            "code": "token_regenerated",
            "tg_id": tg_id,
            "sync_ok": sync_ok,
        }

    if action in {"user.safe_delete", "user.delete_test"}:
        tg_id = int(execution["tg_id"])
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.tg_id == tg_id).first()
            if user is None:
                return {"ok": False, "code": "user_not_found", "tg_id": tg_id}
            if not _is_manual_test_user(user):
                return {"ok": False, "code": "user_not_deletable", "tg_id": tg_id}
            session.query(UserNode).filter(UserNode.tg_id == tg_id).delete(
                synchronize_session=False
            )
            session.query(UserKeyPolicy).filter(UserKeyPolicy.tg_id == tg_id).delete(
                synchronize_session=False
            )
            session.query(KeyActionHistory).filter(KeyActionHistory.tg_id == tg_id).delete(
                synchronize_session=False
            )
            session.query(Event).filter(Event.tg_id == tg_id).delete(
                synchronize_session=False
            )
            session.delete(user)
            session.commit()
        finally:
            session.close()
        panel_deleted = False
        panel = ControlPanel()
        try:
            await panel.login()
            panel_deleted = bool(await panel.delete_client(tg_id))
        except Exception as exc:
            logger.warning(
                "admin guarded delete panel cleanup failed tg_id=%s error_type=%s intent_id=%s",
                tg_id,
                type(exc).__name__,
                str(context.get("action_intent_id") or ""),
            )
        finally:
            await panel.close()
        return {
            "ok": True,
            "code": "user_deleted",
            "tg_id": tg_id,
            "panel_deleted": panel_deleted,
        }

    if action in {
        "user.key_toggle",
        "user.key_reset_traffic",
        "user.key_resync_subid",
    }:
        tg_id = int(execution["tg_id"])
        node_code = str(runtime["node_code"])
        hard_cap = dict(execution.get("hard_caps") or {}).get(node_code)
        sub_id = str(execution.get("sub_token") or tg_id)
        panel = ControlPanel()
        try:
            await panel.login()
            if action == "user.key_toggle":
                changed = await panel.set_user_key_enabled_on_node(
                    tg_id=tg_id,
                    node_code=node_code,
                    enable=bool(runtime["enable"]),
                    sub_id=sub_id,
                    hard_cap_gb=hard_cap,
                )
            elif action == "user.key_reset_traffic":
                changed = await panel.reset_user_key_traffic_on_node(
                    tg_id=tg_id,
                    node_code=node_code,
                )
            else:
                changed = await panel.resync_user_key_subid_on_node(
                    tg_id=tg_id,
                    node_code=node_code,
                    sub_id=sub_id,
                    hard_cap_gb=hard_cap,
                )
        finally:
            await panel.close()
        if changed is None:
            return {
                "ok": False,
                "code": "key_not_found",
                "tg_id": tg_id,
                "node_code": node_code,
            }
        if not changed:
            return {
                "ok": False,
                "code": "panel_update_failed",
                "tg_id": tg_id,
                "node_code": node_code,
            }
        history_action = {
            "user.key_toggle": "key_enable" if runtime["enable"] else "key_disable",
            "user.key_reset_traffic": "key_reset_traffic",
            "user.key_resync_subid": "key_resync_subid",
        }[action]
        _key_history_log(
            tg_id=tg_id,
            action=history_action,
            node_code=node_code,
            actor_tg_id=actor,
            meta=(
                {"enabled": bool(runtime["enable"])}
                if action == "user.key_toggle"
                else None
            ),
        )
        result: dict[str, Any] = {
            "ok": True,
            "code": "key_updated",
            "tg_id": tg_id,
            "node_code": node_code,
        }
        if action == "user.key_toggle":
            result["enabled"] = bool(runtime["enable"])
        return result

    if action == "user.key_limits":
        tg_id = int(execution["tg_id"])
        node_code = str(runtime["node_code"])
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.tg_id == tg_id).first()
            if user is None:
                return {"ok": False, "code": "user_not_found", "tg_id": tg_id}
            row = (
                session.query(UserKeyPolicy)
                .filter(
                    UserKeyPolicy.tg_id == tg_id,
                    func.lower(UserKeyPolicy.node_code) == node_code,
                )
                .first()
            )
            if row is None:
                row = UserKeyPolicy(tg_id=tg_id, node_code=node_code)
                session.add(row)
            row.burst_mbps = runtime["burst_mbps"]
            row.soft_cap_gb = runtime["soft_cap_gb"]
            row.hard_cap_gb = runtime["hard_cap_gb"]
            row.notify_soft = bool(runtime["notify_soft"])
            row.notify_hard = bool(runtime["notify_hard"])
            row.auto_disable_on_hard = bool(runtime["auto_disable_on_hard"])
            row.updated_by = actor
            row.updated_at = _utcnow()
            sub_id = str(user.sub_token or user.tg_id)
            row_payload = _serialize_key_policy(row)
            session.commit()
        finally:
            session.close()
        panel = ControlPanel()
        try:
            await panel.login()
            applied = await panel.apply_user_key_limits_on_node(
                tg_id=tg_id,
                node_code=node_code,
                hard_cap_gb=runtime["hard_cap_gb"],
                sub_id=sub_id,
            )
        finally:
            await panel.close()
        _key_history_log(
            tg_id=tg_id,
            action="key_limits_update",
            node_code=node_code,
            actor_tg_id=actor,
            meta={"policy": row_payload, "apply_now": True, "applied": applied},
        )
        return {
            "ok": True,
            "code": "key_limits_updated",
            "tg_id": tg_id,
            "node_code": node_code,
            "applied": applied,
        }

    if action == "user.loyalty_grant":
        tg_id = int(execution["tg_id"])
        tier_days = int(runtime["tier_days"])
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.tg_id == tg_id).first()
            if user is None:
                return {"ok": False, "code": "user_not_found", "tg_id": tg_id}
            loyalty = _user_loyalty_snapshot(s=session, user=user)
            tier = next(
                (
                    row
                    for row in loyalty.get("tiers", [])
                    if int(row.get("days") or 0) == tier_days
                ),
                None,
            )
            if tier is None:
                return {"ok": False, "code": "tier_not_found", "tg_id": tg_id}
            if not bool(tier.get("unlocked")):
                return {"ok": False, "code": "tier_locked", "tg_id": tg_id}
            if bool(tier.get("claimed")):
                return {"ok": False, "code": "tier_claimed", "tg_id": tg_id}
            now = _utcnow()
            base = user.expiry_at if user.expiry_at and user.expiry_at > now else now
            user.expiry_at = base + timedelta(days=max(1, int(tier.get("bonus_days") or 0)))
            user.is_active = True
            session.add(
                RewardClaim(
                    tg_id=tg_id,
                    reward_key=str(tier.get("reward_key") or ""),
                    meta=json.dumps({"tier": tier_days}, ensure_ascii=False),
                )
            )
            session.commit()
            try:
                sync_ok = bool(await _sync_user_after_paid_bonus(user))
            except Exception as exc:
                logger.warning(
                    "loyalty grant sync failed tg_id=%s error_type=%s intent_id=%s",
                    tg_id,
                    type(exc).__name__,
                    str(context.get("action_intent_id") or ""),
                )
                sync_ok = False
        except IntegrityError:
            session.rollback()
            return {"ok": False, "code": "tier_claimed", "tg_id": tg_id}
        finally:
            session.close()
        return {
            "ok": True,
            "code": "loyalty_granted",
            "tg_id": tg_id,
            "tier_days": tier_days,
            "sync_ok": sync_ok,
        }

    if action == "user.preset_run":
        tg_id = int(execution["tg_id"])
        preset = str(runtime["preset"])
        if preset == "send_guide":
            ok = await _telegram_send_message(
                tg_id,
                "Инструкция по подключению:\n"
                "1) Откройте раздел Устройства.\n"
                "2) Импортируйте ключ.\n"
                "3) Проверьте статус и перезапустите приложение.",
            )
            return {
                "ok": bool(ok),
                "code": "guide_sent" if ok else "telegram_failed",
                "tg_id": tg_id,
                "preset": preset,
            }
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.tg_id == tg_id).first()
            if user is None:
                return {"ok": False, "code": "user_not_found", "tg_id": tg_id}
            nodes = enabled_nodes(session)
        finally:
            session.close()
        keys_state = await _admin_user_keys_state(user, nodes=nodes)
        keys = [row for row in keys_state.get("keys", []) if bool(row.get("exists"))]
        expected_sub_id = str(user.sub_token or user.tg_id)
        changed = 0
        failed = 0
        panel = ControlPanel()
        try:
            await panel.login()
            if preset == "reset_key":
                for key in keys:
                    code = str(key.get("node_code") or "")
                    ok = await panel.reset_user_key_traffic_on_node(
                        tg_id=tg_id,
                        node_code=code,
                    )
                    if ok:
                        changed += 1
                        _key_history_log(
                            tg_id=tg_id,
                            action="key_reset_traffic",
                            node_code=code,
                            actor_tg_id=actor,
                            source="preset",
                        )
                    else:
                        failed += 1
            elif preset == "rotate_link":
                rotate_session = SessionLocal()
                try:
                    db_user = rotate_session.query(User).filter(User.tg_id == tg_id).first()
                    if db_user is None:
                        return {"ok": False, "code": "user_not_found", "tg_id": tg_id}
                    db_user.sub_token = _generate_sub_token()
                    rotate_session.commit()
                    expected_sub_id = str(db_user.sub_token or db_user.tg_id)
                finally:
                    rotate_session.close()
                for key in keys:
                    code = str(key.get("node_code") or "")
                    cap_session = SessionLocal()
                    try:
                        hard_cap = _get_user_node_hard_cap_gb(
                            s=cap_session,
                            tg_id=tg_id,
                            node_code=code,
                        )
                    finally:
                        cap_session.close()
                    ok = await panel.resync_user_key_subid_on_node(
                        tg_id=tg_id,
                        node_code=code,
                        sub_id=expected_sub_id,
                        hard_cap_gb=hard_cap,
                    )
                    if ok:
                        changed += 1
                        _key_history_log(
                            tg_id=tg_id,
                            action="key_resync_subid",
                            node_code=code,
                            actor_tg_id=actor,
                            source="preset",
                        )
                    else:
                        failed += 1
                _key_history_log(
                    tg_id=tg_id,
                    action="token_regenerate",
                    actor_tg_id=actor,
                    source="preset",
                )
        finally:
            await panel.close()
        return {
            "ok": failed == 0,
            "code": "preset_completed" if failed == 0 else "preset_partial",
            "tg_id": tg_id,
            "preset": preset,
            "changed": changed,
            "failed": failed,
        }

    if action == "user.bulk_key_action":
        selected = [int(value) for value in execution["selected_tg_ids"]]
        bulk_action = str(execution["action"])
        if len(selected) > 50 and not bool(execution["force"]):
            return {
                "ok": False,
                "code": "force_required",
                "action": bulk_action,
                "users": len(selected),
                "requires_force": True,
            }
        panel = ControlPanel()
        changed = 0
        failed = 0
        details: list[dict[str, int]] = []
        try:
            await panel.login()
            for tg_id in selected:
                user_changed = 0
                user_failed = 0
                session = SessionLocal()
                try:
                    user = session.query(User).filter(User.tg_id == tg_id).first()
                    if user is None:
                        failed += 1
                        user_failed += 1
                        details.append(
                            {"tg_id": tg_id, "changed": 0, "failed": user_failed}
                        )
                        continue
                    sub_id = str(user.sub_token or user.tg_id)
                finally:
                    session.close()
                node_codes = list(execution["node_codes"])
                if not node_codes:
                    snapshots = await panel.get_user_key_snapshots(tg_id=tg_id)
                    node_codes = [
                        str(row.get("node_code") or "").strip().lower()
                        for row in snapshots
                        if str(row.get("node_code") or "").strip()
                    ]
                for node_code in node_codes:
                    cap_session = SessionLocal()
                    try:
                        hard_cap = _get_user_node_hard_cap_gb(
                            s=cap_session,
                            tg_id=tg_id,
                            node_code=node_code,
                        )
                    finally:
                        cap_session.close()
                    if bulk_action == "disable":
                        ok = await panel.set_user_key_enabled_on_node(
                            tg_id=tg_id,
                            node_code=node_code,
                            enable=False,
                            sub_id=sub_id,
                            hard_cap_gb=hard_cap,
                        )
                    elif bulk_action == "enable":
                        ok = await panel.set_user_key_enabled_on_node(
                            tg_id=tg_id,
                            node_code=node_code,
                            enable=True,
                            sub_id=sub_id,
                            hard_cap_gb=hard_cap,
                        )
                    elif bulk_action == "reset":
                        ok = await panel.reset_user_key_traffic_on_node(
                            tg_id=tg_id,
                            node_code=node_code,
                        )
                    else:
                        ok = await panel.resync_user_key_subid_on_node(
                            tg_id=tg_id,
                            node_code=node_code,
                            sub_id=sub_id,
                            hard_cap_gb=hard_cap,
                        )
                    if ok:
                        changed += 1
                        user_changed += 1
                        _key_history_log(
                            tg_id=tg_id,
                            action={
                                "disable": "key_disable",
                                "enable": "key_enable",
                                "reset": "key_reset_traffic",
                                "resync": "key_resync_subid",
                            }[bulk_action],
                            node_code=node_code,
                            actor_tg_id=actor,
                            source="bulk",
                        )
                    else:
                        failed += 1
                        user_failed += 1
                details.append(
                    {
                        "tg_id": tg_id,
                        "changed": user_changed,
                        "failed": user_failed,
                    }
                )
        finally:
            await panel.close()
        return {
            "ok": failed == 0,
            "code": "bulk_completed" if failed == 0 else "bulk_partial",
            "action": bulk_action,
            "users": len(selected),
            "changed": changed,
            "failed": failed,
            "details": details,
        }

    if action == "node.sync_global":
        selection = [dict(item) for item in execution["selection"]]
        if len(selection) != int(execution["selected_count"]):
            raise RuntimeError("frozen global sync selection is unavailable")
        panel = ControlPanel()
        changed = 0
        failed = 0
        try:
            await panel.login()
            for item in selection:
                ok = await panel.enable_client(str(item["uuid"]), True)
                if ok:
                    changed += 1
                else:
                    failed += 1
        finally:
            await panel.close()
        return {
            "ok": failed == 0,
            "code": "global_sync_completed" if failed == 0 else "global_sync_partial",
            "count": len(selection),
            "changed": changed,
            "failed": failed,
        }

    if action == "broadcast.send":
        recipients = [int(value) for value in execution["selected_tg_ids"]]
        if (
            recipients != sorted(set(recipients))
            or len(recipients) != int(execution["recipient_count"])
        ):
            raise RuntimeError("frozen broadcast plan is unavailable")
        execution_intent_id = str(context.get("action_intent_id") or "")
        retry_intent_id = str(execution.get("retry_intent_id") or "")
        campaign_intent_id = execution_intent_id
        if retry_intent_id:
            lookup_session = SessionLocal()
            try:
                source = (
                    lookup_session.query(AdminBroadcastDeliveryAttempt.campaign_intent_id)
                    .filter(AdminBroadcastDeliveryAttempt.intent_id == retry_intent_id)
                    .order_by(AdminBroadcastDeliveryAttempt.id.asc())
                    .first()
                )
            finally:
                lookup_session.close()
            if source is None:
                raise RuntimeError("broadcast retry source is unavailable")
            campaign_intent_id = str(source[0])
        for tg_id in recipients:
            attempt_session = SessionLocal()
            try:
                existing = (
                    attempt_session.query(AdminBroadcastDeliveryAttempt)
                    .filter(
                        AdminBroadcastDeliveryAttempt.campaign_intent_id
                        == campaign_intent_id,
                        AdminBroadcastDeliveryAttempt.tg_id == tg_id,
                    )
                    .order_by(AdminBroadcastDeliveryAttempt.attempt_number.asc())
                    .all()
                )
                if any(str(row.status) == "sent" for row in existing):
                    continue
                attempt_number = max(
                    [int(row.attempt_number) for row in existing] or [0]
                ) + 1
            finally:
                attempt_session.close()
            if attempt_number > 20:
                raise RuntimeError("broadcast retry limit reached")
            started_at = _utcnow()
            delivery = await _telegram_send_message_detailed(
                tg_id,
                str(runtime["text"]),
                disable_web_page_preview=True,
            )
            finished_at = _utcnow()
            save_session = SessionLocal()
            try:
                save_session.add(
                    AdminBroadcastDeliveryAttempt(
                        intent_id=execution_intent_id,
                        campaign_intent_id=campaign_intent_id,
                        tg_id=tg_id,
                        attempt_number=attempt_number,
                        status="sent" if delivery.sent else "failed",
                        reason_code=str(delivery.reason_code),
                        retryable=bool(delivery.retryable),
                        http_status=delivery.http_status,
                        telegram_error_code=delivery.telegram_error_code,
                        retry_after_seconds=delivery.retry_after_seconds,
                        message_id=delivery.message_id,
                        provider_error_hash=delivery.provider_error_hash,
                        duration_ms=int(delivery.duration_ms),
                        started_at=started_at,
                        finished_at=finished_at,
                    )
                )
                save_session.commit()
            except Exception:
                save_session.rollback()
                raise
            finally:
                save_session.close()
        summary = _broadcast_delivery_summary(campaign_intent_id=campaign_intent_id)
        state_session = SessionLocal()
        try:
            selected_rows = (
                state_session.query(AdminBroadcastDeliveryAttempt)
                .filter(
                    AdminBroadcastDeliveryAttempt.campaign_intent_id == campaign_intent_id,
                    AdminBroadcastDeliveryAttempt.tg_id.in_(recipients),
                )
                .order_by(
                    AdminBroadcastDeliveryAttempt.tg_id.asc(),
                    AdminBroadcastDeliveryAttempt.attempt_number.asc(),
                )
                .all()
            )
        finally:
            state_session.close()
        selected_by_recipient: dict[int, list[AdminBroadcastDeliveryAttempt]] = {}
        for row in selected_rows:
            selected_by_recipient.setdefault(int(row.tg_id), []).append(row)
        sent = sum(
            1
            for attempts in selected_by_recipient.values()
            if any(str(row.status) == "sent" for row in attempts)
        )
        failed = len(recipients) - sent
        return {
            "ok": failed == 0,
            "code": "broadcast_sent" if failed == 0 else "broadcast_partial",
            "attempted": len(recipients),
            "sent": sent,
            "failed": failed,
            "retryable_failed": int(summary["retryable_failed"]),
            "terminal_failed": int(summary["terminal_failed"]),
            "reason_counts": dict(summary["reason_counts"]),
        }

    if action == "user.message":
        tg_id = int(execution["tg_id"])
        ok = await _telegram_send_message(tg_id, str(runtime["text"]))
        return {
            "ok": bool(ok),
            "code": "message_sent" if ok else "telegram_failed",
            "tg_id": tg_id,
        }

    if action == "ticket.reply":
        ticket_id = int(execution["ticket_id"])
        user_tg_id = int(execution["user_tg_id"])
        expected_version = execution.get("expected_version")
        message_payload = TicketMessageIn(
            body=str(runtime["body"]),
            attachment_id=runtime.get("attachment_id"),
            media_type=runtime.get("media_type"),
            media_file_id=runtime.get("media_file_id"),
            media_payload=runtime.get("media_payload"),
        )
        reference = _support_attachment_reference(message_payload)
        with _support_attachment_bind_lock(reference):
            session = SessionLocal()
            try:
                account_id = resolve_support_account_id(session, user_tg_id=actor)
                ticket = get_ticket_by_id(session, ticket_id)
                if ticket is None:
                    return {"ok": False, "code": "ticket_not_found", "ticket_id": ticket_id}
                if expected_version is not None and max(1, int(getattr(ticket, "version", 1) or 1)) != int(expected_version):
                    return {"ok": False, "code": "ticket_version_conflict", "ticket_id": ticket_id}
                attachment, media = _resolve_ticket_attachment(
                    session,
                    payload=message_payload,
                    actor_tg_id=actor,
                    account_id=account_id,
                )
                message = add_ticket_message(
                    session,
                    ticket_id=ticket_id,
                    sender_tg_id=actor,
                    sender_role="admin",
                    body=message_payload.body,
                    macro_code=runtime.get("macro_code"),
                    **media,
                )
                if attachment is not None:
                    _bind_ticket_attachment(
                        session,
                        row=attachment,
                        ticket_id=ticket_id,
                        message_id=int(message.id),
                    )
                set_ticket_status(
                    session,
                    ticket=ticket,
                    status=STATUS_IN_PROGRESS,
                    assigned_admin_tg_id=actor,
                )
                session.commit()
                ticket_version = max(1, int(getattr(ticket, "version", 1) or 1))
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
        sent = await _telegram_send_message(
            user_tg_id,
            f"💬 Ответ оператора в обращении #{ticket_id}.",
        )
        return {
            "ok": bool(sent),
            "code": "ticket_replied" if sent else "telegram_failed",
            "ticket_id": ticket_id,
            "ticket_version": ticket_version,
        }

    if action == "ticket.note":
        ticket_id = int(execution["ticket_id"])
        expected_version = int(execution["expected_version"])
        session = SessionLocal()
        try:
            ticket = get_ticket_by_id(session, ticket_id)
            if ticket is None:
                return {"ok": False, "code": "ticket_not_found", "ticket_id": ticket_id}
            if max(1, int(getattr(ticket, "version", 1) or 1)) != expected_version:
                return {"ok": False, "code": "ticket_version_conflict", "ticket_id": ticket_id}
            add_ticket_message(
                session,
                ticket_id=ticket_id,
                sender_tg_id=actor,
                sender_role="admin",
                body=str(runtime["body"]),
                visibility="internal",
                macro_code=runtime.get("macro_code"),
            )
            session.commit()
            return {
                "ok": True,
                "code": "ticket_note_added",
                "ticket_id": ticket_id,
                "ticket_version": max(1, int(getattr(ticket, "version", 1) or 1)),
            }
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    raise RuntimeError("guarded external executor is unavailable")


async def _execute_admin_post_commit(context: dict[str, Any]) -> dict[str, Any]:
    action = str(context.get("action") or "")
    if action == "user.extend":
        execution = dict(context.get("execution") or {})
        tg_id = int(execution["tg_id"])
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.tg_id == tg_id).first()
            if user is None:
                return {"ok": False, "code": "user_missing"}
            client_uuid = str(user.uuid or "")
            email = str(user.email or f"User_{tg_id}")
            sub_id = str(user.sub_token or tg_id)
            access_status = effective_user_access_status(user)
        finally:
            session.close()

        panel = ControlPanel()
        results: dict[str, bool] = {}
        try:
            nodes = await panel.refresh()
            node_codes = [
                str(getattr(node, "code", "") or "").strip()
                for node in nodes
                if str(getattr(node, "code", "") or "").strip()
            ]
            if access_status in {"TRIAL", "PAID"}:
                results = await panel.ensure_user_on_all_nodes(
                    tg_id=tg_id,
                    client_uuid=client_uuid,
                    email=email,
                    sub_id=sub_id,
                    enable=True,
                    only_node_codes=None,
                )
            elif node_codes:
                results = await panel.set_existing_user_enabled_on_nodes(
                    tg_id=tg_id,
                    node_codes=node_codes,
                    enable=False,
                    sub_id=sub_id,
                )
        finally:
            await panel.close()
        sync_ok = bool(results) and all(bool(value) for value in results.values())
        _key_history_log(
            tg_id=tg_id,
            action="admin_extend_access_sync",
            actor_tg_id=int(context.get("actor_tg_id") or 0),
            meta={
                "access_status": access_status,
                "nodes_attempted": len(results),
                "nodes_ok": sum(1 for value in results.values() if bool(value)),
                "sync_ok": sync_ok,
            },
        )
        return {"ok": sync_ok, "code": "access_synced" if sync_ok else "access_sync_partial"}

    if action != "ticket.status":
        return {"ok": True, "code": "post_commit_not_required"}
    execution = dict(context.get("execution") or {})
    ticket_id = int(execution["ticket_id"])
    user_tg_id = int(execution["user_tg_id"])
    sent = await _telegram_send_message(
        user_tg_id,
        f"✅ Обращение #{ticket_id} закрыто оператором.",
    )
    return {"ok": bool(sent), "code": "ticket_close_notified" if sent else "telegram_failed"}


def _saved_bulk_preview_ids(value: object) -> list[int]:
    if not isinstance(value, list) or len(value) > 50:
        return []
    ids: list[int] = []
    for item in value:
        if type(item) is not int or not -(2**63) <= item < 2**63:
            return []
        ids.append(int(item))
    return ids if len(set(ids)) == len(ids) else []


def _saved_bulk_details(value: object) -> list[dict[str, int]]:
    if not isinstance(value, list) or len(value) > 500:
        return []
    details: list[dict[str, int]] = []
    for item in value:
        if not isinstance(item, dict) or set(item) != {"tg_id", "changed", "failed"}:
            return []
        tg_id = item["tg_id"]
        changed = item["changed"]
        failed = item["failed"]
        if (
            type(tg_id) is not int
            or not -(2**63) <= tg_id < 2**63
            or type(changed) is not int
            or type(failed) is not int
            or not 0 <= changed <= 1_000_000
            or not 0 <= failed <= 1_000_000
        ):
            return []
        details.append(
            {"tg_id": int(tg_id), "changed": int(changed), "failed": int(failed)}
        )
    return (
        details
        if len({item["tg_id"] for item in details}) == len(details)
        else []
    )


def _admin_guarded_action_response(
    *,
    action: str,
    target_id: str,
    result: dict[str, Any],
) -> dict[str, Any]:
    known_status = str(result.get("status") or "")
    if known_status not in {"completed", "failed"}:
        return result
    if known_status == "failed" and (
        action,
        str(result.get("result_code") or ""),
    ) not in {
        ("user.preset_run", "preset_partial"),
        ("user.bulk_key_action", "bulk_partial"),
        ("user.bulk_key_action", "force_required"),
        ("ticket.reply", "telegram_failed"),
        ("broadcast.send", "broadcast_partial"),
        ("node.sync_global", "global_sync_partial"),
    }:
        return result
    facts = result.get("result") if isinstance(result.get("result"), dict) else {}
    metadata = {
        "status": result.get("status"),
        "action_intent_id": result.get("action_intent_id"),
        "audit_id": result.get("audit_id"),
    }

    def merged(legacy: dict[str, Any]) -> dict[str, Any]:
        merged_result = {**result, **legacy, **metadata}
        merged_result["ok"] = bool(
            known_status == "completed" and legacy.get("ok", True)
        )
        return merged_result

    if action == "payment.reconcile":
        session = SessionLocal()
        try:
            order = session.query(ExternalOrder).filter(ExternalOrder.id == int(target_id)).first()
            if order is None:
                return result
            return merged(
                {
                    "ok": True,
                    "order": _admin_payment_order_payload(s=session, order=order),
                }
            )
        finally:
            session.close()

    if action == "user.manual_create":
        tg_id = int(facts["tg_id"])
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.tg_id == tg_id).first()
            if user is None:
                return result
            return merged(
                {
                    "ok": True,
                    "user": {
                        "tg_id": tg_id,
                        "display_name": str(user.display_name or ""),
                        "sub_type": str(user.sub_type or ""),
                        "is_active": bool(user.is_active),
                        "expiry_at": _safe_iso(user.expiry_at),
                        "subscription_url": build_subscription_url(str(user.sub_token or "")),
                    },
                    "sync_ok": bool(facts.get("sync_ok")),
                }
            )
        finally:
            session.close()

    if action == "user.block":
        return merged({"ok": True, "is_active": bool(facts.get("is_active"))})

    if action == "user.regenerate_token":
        tg_id = int(facts["tg_id"])
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.tg_id == tg_id).first()
            if user is None:
                return result
            return merged(
                {
                    "ok": True,
                    "subscription_url": build_subscription_url(str(user.sub_token or "")),
                    "sync_ok": bool(facts.get("sync_ok")),
                }
            )
        finally:
            session.close()

    if action in {"user.safe_delete", "user.delete_test"}:
        return merged(
            {
                "ok": True,
                "tg_id": int(facts["tg_id"]),
                "panel_deleted": bool(facts.get("panel_deleted")),
            }
        )

    if action == "user.key_toggle":
        return merged(
            {
                "ok": True,
                "tg_id": int(facts["tg_id"]),
                "node_code": str(facts["node_code"]),
                "enabled": bool(facts.get("enabled")),
            }
        )

    if action == "user.key_reset_traffic":
        return merged(
            {
                "ok": True,
                "tg_id": int(facts["tg_id"]),
                "node_code": str(facts["node_code"]),
            }
        )

    if action == "user.key_resync_subid":
        tg_id = int(facts["tg_id"])
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.tg_id == tg_id).first()
            if user is None:
                return result
            return merged(
                {
                    "ok": True,
                    "tg_id": tg_id,
                    "node_code": str(facts["node_code"]),
                    "expected_sub_id": str(user.sub_token or user.tg_id),
                }
            )
        finally:
            session.close()

    if action == "user.key_limits":
        tg_id = int(facts.get("tg_id") or target_id)
        node_code = str(facts.get("node_code") or "")
        session = SessionLocal()
        try:
            row = (
                session.query(UserKeyPolicy)
                .filter(
                    UserKeyPolicy.tg_id == tg_id,
                    func.lower(UserKeyPolicy.node_code) == node_code,
                )
                .first()
            )
            if row is None:
                return result
            return merged(
                {
                    "ok": True,
                    "policy": _serialize_key_policy(row),
                    "applied": facts.get("applied"),
                }
            )
        finally:
            session.close()

    if action == "user.loyalty_grant":
        tg_id = int(facts["tg_id"])
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.tg_id == tg_id).first()
            if user is None:
                return result
            return merged(
                {
                    "ok": True,
                    "tier_days": int(facts["tier_days"]),
                    "expiry_at": _safe_iso(user.expiry_at),
                    "sync_ok": bool(facts.get("sync_ok")),
                }
            )
        finally:
            session.close()

    if action == "user.preset_run" and facts:
        preset = str(facts["preset"])
        legacy: dict[str, Any] = {"ok": True, "preset": preset}
        if preset in {"reset_key", "rotate_link"}:
            tg_id = int(facts["tg_id"])
            session = SessionLocal()
            try:
                user = session.query(User).filter(User.tg_id == tg_id).first()
                if user is not None:
                    legacy["subscription_url"] = build_subscription_url(
                        str(user.sub_token or user.tg_id)
                    )
            finally:
                session.close()
            legacy["changed"] = int(facts.get("changed") or 0)
            legacy["failed"] = int(facts.get("failed") or 0)
        return merged(legacy)

    if action == "user.bulk_key_action":
        if facts:
            requires_force = bool(facts.get("requires_force"))
            return merged(
                {
                    "ok": not requires_force,
                    "requires_force": requires_force or None,
                    "action": str(facts.get("action") or ""),
                    "users": int(facts.get("users") or 0),
                    "changed": int(facts.get("changed") or 0),
                    "failed": int(facts.get("failed") or 0),
                    "details": _saved_bulk_details(facts.get("details")),
                    **(
                        {"message": "Для массового действия более чем над 50 пользователями нужен force=true"}
                        if requires_force
                        else {}
                    ),
                }
            )
        return merged(
            {
                "ok": True,
                "action": str(result.get("action") or ""),
                "dry_run": True,
                "users": int(result.get("users") or 0),
                "preview_tg_ids": _saved_bulk_preview_ids(
                    result.get("preview_tg_ids")
                ),
            }
        )

    if action == "user.message":
        return merged({"ok": True})

    if action == "broadcast.send":
        return merged(
            {
                "attempted": int(facts.get("attempted") or 0),
                "sent": int(facts.get("sent") or 0),
                "failed": int(facts.get("failed") or 0),
                "retryable_failed": int(facts.get("retryable_failed") or 0),
                "terminal_failed": int(facts.get("terminal_failed") or 0),
                "reason_counts": (
                    dict(facts.get("reason_counts") or {})
                    if isinstance(facts.get("reason_counts"), dict)
                    else {}
                ),
            }
        )

    if action == "node.sync_global":
        return merged(
            {
                "synced": int(facts.get("changed") or 0),
                "failed": int(facts.get("failed") or 0),
                "count": int(facts.get("count") or 0),
            }
        )

    if action in {"ticket.reply", "ticket.status", "ticket.note"}:
        ticket_id = int(facts.get("ticket_id") or result.get("ticket_id") or target_id)
        session = SessionLocal()
        try:
            ticket = get_ticket_by_id(session, ticket_id)
            if ticket is None:
                return result
            messages = list_ticket_messages(session, ticket_id, limit=100, include_internal=True)
            return merged({"ticket": _ticket_detail_row(ticket, messages)})
        finally:
            session.close()

    return result


async def _execute_admin_guarded_action(
    *,
    actor_tg_id: int,
    action: str,
    target_type: str,
    target_id: str,
    payload: dict[str, Any],
    request: Request,
) -> dict[str, Any]:
    intent_id = str(request.headers.get("X-Admin-Intent-Id") or "")
    idempotency_key = str(request.headers.get("X-Admin-Idempotency-Key") or "")
    confirmation = str(request.headers.get("X-Admin-Confirmation-SHA256") or "")
    if not intent_id.strip():
        raise HTTPException(
            status_code=428,
            detail={
                "code": "intent_required",
                "message": "Сначала создайте защищённое намерение через серверный предпросмотр.",
            },
        )
    if not idempotency_key.strip():
        _raise_action_intent_header_required(
            actor_tg_id=actor_tg_id,
            intent_id=intent_id,
            code="idempotency_required",
            message="Нужен клиентский ключ идемпотентности.",
        )
    if not confirmation.strip():
        _raise_action_intent_header_required(
            actor_tg_id=actor_tg_id,
            intent_id=intent_id,
            code="confirmation_required",
            message="Нужно подтверждение серверной проверочной фразы.",
        )
    try:
        execution_result = await _execute_action_intent(
            session_factory=SessionLocal,
            actor_tg_id=actor_tg_id,
            intent_id=intent_id,
            idempotency_key=idempotency_key,
            confirmation_sha256_header=confirmation,
            action=action,
            target={"type": target_type, "id": target_id},
            payload=payload,
            audit_writer=_add_admin_audit,
            db_executor=lambda session, state, normalized, runtime: (
                _execute_admin_client_action_db(
                    session,
                    state,
                    dict(normalized),
                    dict(runtime),
                    actor_tg_id=actor_tg_id,
                    action=action,
                )
            ),
            external_executor=_execute_admin_client_action_external,
            post_commit_executor=_execute_admin_post_commit,
            external_timeout_seconds=(
                300.0
                if action in {
                    "user.bulk_key_action",
                    "user.preset_run",
                    "emergency_catalog.stage",
                }
                else 30.0
            ),
            return_replay_state=True,
        )
    except ActionIntentError as error:
        if (
            action == "warp_material.replace"
            and error.code == "warp_material_rate_limited"
        ):
            event_session = SessionLocal()
            try:
                user = (
                    event_session.query(User)
                    .filter(User.tg_id == int(payload.get("tg_id") or 0))
                    .first()
                )
                if user is not None:
                    install_id = (
                        str(
                            payload.get("install_id")
                            or getattr(user, "app_install_id", "")
                            or ""
                        ).strip()
                        or None
                    )
                    policy = public_warp_policy_for_user(
                        event_session,
                        user=user,
                        install_id=install_id,
                        rollout_config=load_network_rollout_config(session=event_session),
                    )
                    record_warp_event(
                        event_session,
                        user=user,
                        install_id=install_id,
                        policy=policy,
                        event_name="material_provision_rate_limited",
                        state="rate_limited",
                        reason_code="provision_limit",
                        consented=False,
                        meta={"source": "admin", "actor_tg_id": int(actor_tg_id)},
                    )
                    event_session.commit()
            except Exception:
                event_session.rollback()
            finally:
                event_session.close()
        _raise_action_intent_http(error)
        raise AssertionError("unreachable")
    result, replayed = execution_result
    if replayed and action != "broadcast.send":
        return result
    return _admin_guarded_action_response(
        action=action,
        target_id=target_id,
        result=result,
    )


async def _execute_admin_node_action(
    *,
    actor_tg_id: int,
    action: str,
    node_code: str,
    payload: dict[str, Any],
    intent_id: str,
    idempotency_key: str,
    confirmation_sha256: str,
) -> dict[str, Any]:
    if not str(intent_id or "").strip():
        raise HTTPException(
            status_code=428,
            detail={
                "code": "intent_required",
                "message": "Сначала создайте защищённое намерение через серверный предпросмотр.",
            },
        )
    if not str(idempotency_key or "").strip():
        _raise_action_intent_header_required(
            actor_tg_id=actor_tg_id,
            intent_id=intent_id,
            code="idempotency_required",
            message="Нужен клиентский ключ идемпотентности.",
        )
    if not str(confirmation_sha256 or "").strip():
        _raise_action_intent_header_required(
            actor_tg_id=actor_tg_id,
            intent_id=intent_id,
            code="confirmation_required",
            message="Нужно подтверждение серверной проверочной фразы.",
        )
    try:
        return await _execute_action_intent(
            session_factory=SessionLocal,
            actor_tg_id=actor_tg_id,
            intent_id=intent_id,
            idempotency_key=idempotency_key,
            confirmation_sha256_header=confirmation_sha256,
            action=action,
            target={"type": "node", "id": node_code},
            payload=payload,
            audit_writer=_add_admin_audit,
            external_executor=(
                _execute_node_resync_external
                if action == "node.resync"
                else None
            ),
        )
    except ActionIntentError as error:
        _raise_action_intent_http(error)
        raise AssertionError("unreachable")


@app.post("/api/admin/action-intents")
async def admin_action_intent_prepare(
    payload: AdminActionIntentPrepareIn,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    session = SessionLocal()
    try:
        normalized_payload = _operator_action_payload_for_actor(
            session,
            actor_tg_id=actor,
            action=payload.action,
            payload=dict(payload.payload),
        )
        result = _prepare_action_intent(
            session=session,
            actor_tg_id=actor,
            action=payload.action,
            target={"type": payload.target.type, "id": payload.target.id},
            payload=normalized_payload,
        )
        session.commit()
        return result
    except ActionIntentError as error:
        session.rollback()
        _raise_action_intent_http(error)
        raise AssertionError("unreachable")
    except HTTPException:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail={
                "code": "intent_prepare_failed",
                "message": "Не удалось подготовить действие.",
            },
        ) from None
    finally:
        session.close()

@app.get("/api/admin/action-intents/{intent_id}")
async def admin_action_intent_status(
    intent_id: str,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    session = SessionLocal()
    try:
        return _get_action_intent_status(
            session=session,
            actor_tg_id=actor,
            intent_id=intent_id,
        )
    except ActionIntentError as error:
        _raise_action_intent_http(error)
        raise AssertionError("unreachable")
    finally:
        session.close()
