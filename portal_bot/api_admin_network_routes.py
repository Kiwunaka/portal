"""Guarded emergency-network and node lifecycle administrative routes.

Loaded after the guarded admin action slice. Public symbols are re-exported
through the legacy ``api`` composition root.
"""

try:
    from .module_slices import bootstrap_slice
except ImportError:
    from module_slices import bootstrap_slice

bootstrap_slice(globals())


@app.get("/api/admin/emergency-network/status")
async def admin_emergency_network_status(
    request: Request,
    limit: int = Query(default=20, ge=1, le=50),
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    _require_admin(x_telegram_init_data, request=request)
    session = SessionLocal()
    try:
        return build_emergency_catalog_admin_status(session, limit=limit)
    finally:
        session.close()


@app.post("/api/admin/emergency-network/stage")
async def admin_emergency_network_stage(
    payload: dict[str, Any],
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    actor = int(_require_admin(x_telegram_init_data, request=request).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="emergency_catalog.stage",
        target_type="emergency_catalog",
        target_id="global",
        payload=dict(payload),
        request=request,
    )


@app.post("/api/admin/emergency-network/snapshots/{snapshot_id}/promote")
async def admin_emergency_network_promote(
    snapshot_id: str,
    payload: dict[str, Any],
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    actor = int(_require_admin(x_telegram_init_data, request=request).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="emergency_catalog.promote",
        target_type="emergency_snapshot",
        target_id=str(snapshot_id),
        payload=dict(payload),
        request=request,
    )


@app.post("/api/admin/emergency-network/snapshots/{snapshot_id}/disable")
async def admin_emergency_network_disable(
    snapshot_id: str,
    payload: dict[str, Any],
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    actor = int(_require_admin(x_telegram_init_data, request=request).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="emergency_catalog.disable",
        target_type="emergency_snapshot",
        target_id=str(snapshot_id),
        payload=dict(payload),
        request=request,
    )


@app.post("/api/admin/emergency-network/snapshots/{snapshot_id}/rollback")
async def admin_emergency_network_rollback(
    snapshot_id: str,
    payload: dict[str, Any],
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    actor = int(_require_admin(x_telegram_init_data, request=request).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="emergency_catalog.rollback",
        target_type="emergency_snapshot",
        target_id=str(snapshot_id),
        payload=dict(payload),
        request=request,
    )


@app.post("/api/admin/nodes/{node_code}/disable")
async def admin_node_disable(
    node_code: str,
    payload: AdminNodeLifecycleIn,
    x_telegram_init_data: str = Header(default=""),
    x_admin_intent_id: str = Header(default="", alias="X-Admin-Intent-Id"),
    x_admin_idempotency_key: str = Header(
        default="",
        alias="X-Admin-Idempotency-Key",
    ),
    x_admin_confirmation_sha256: str = Header(
        default="",
        alias="X-Admin-Confirmation-SHA256",
    ),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    wanted = str(node_code or "").strip().lower()
    return await _execute_admin_node_action(
        actor_tg_id=actor,
        action="node.disable",
        node_code=wanted,
        payload={"force": bool(payload.force)},
        intent_id=x_admin_intent_id,
        idempotency_key=x_admin_idempotency_key,
        confirmation_sha256=x_admin_confirmation_sha256,
    )


@app.post("/api/admin/nodes/{node_code}/resync")
async def admin_node_resync(
    node_code: str,
    payload: AdminNodeResyncIn,
    x_telegram_init_data: str = Header(default=""),
    x_admin_intent_id: str = Header(default="", alias="X-Admin-Intent-Id"),
    x_admin_idempotency_key: str = Header(
        default="",
        alias="X-Admin-Idempotency-Key",
    ),
    x_admin_confirmation_sha256: str = Header(
        default="",
        alias="X-Admin-Confirmation-SHA256",
    ),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    wanted = str(node_code or "").strip().lower()
    return await _execute_admin_node_action(
        actor_tg_id=actor,
        action="node.resync",
        node_code=wanted,
        payload={"limit": int(payload.limit), "dry_run": bool(payload.dry_run)},
        intent_id=x_admin_intent_id,
        idempotency_key=x_admin_idempotency_key,
        confirmation_sha256=x_admin_confirmation_sha256,
    )
