"""Public, authentication and client-session bootstrap routes.

Loaded first by the API composition root. Managed client features and runtime
transport register in the immediately following api_client_routes slice.
Public symbols are re-exported for backwards compatibility.
"""

try:
    from .module_slices import bootstrap_slice
except ImportError:
    from module_slices import bootstrap_slice

bootstrap_slice(globals())

try:
    from .node_observability_sanitizer import sanitize_runtime_metric_meta
except ImportError:
    from node_observability_sanitizer import sanitize_runtime_metric_meta

try:
    from .emergency_catalog_crypto import (
        EmergencyCatalogCrypto,
        EmergencyCatalogCryptoError,
    )
    from .emergency_geoip_service import (
        lookup_country_code,
        observe_request_country,
        request_public_ip,
    )
    from .emergency_catalog_service import (
        EmergencyCatalogServiceError,
        read_serving_catalog,
        read_serving_endpoint_material,
    )
    from .emergency_eligibility_service import (
        resolve_emergency_eligibility,
        resolve_emergency_offline_bundle_eligibility,
    )
    from .emergency_profile_service import (
        EmergencyProfileError,
        build_emergency_singbox_config,
        build_profile_payload,
        build_safe_catalog_payload,
    )
    from .models import EmergencyCatalogEndpoint, EmergencyCatalogSnapshot
    from .commercial_order_service import (
        CommercialOrderBindingError,
        bind_commercial_offer_to_order,
        expire_failed_commercial_reservations,
    )
    from .payment_order_service import (
        PaymentOrderIntentError,
        build_payment_order_intent,
        lock_public_checkout_retry,
        recovered_checkout_fields,
        persist_local_order_intent,
        record_provider_checkout,
        record_provider_checkout_failure,
    )
except ImportError:
    from emergency_catalog_crypto import (
        EmergencyCatalogCrypto,
        EmergencyCatalogCryptoError,
    )
    from emergency_geoip_service import (
        lookup_country_code,
        observe_request_country,
        request_public_ip,
    )
    from emergency_catalog_service import (
        EmergencyCatalogServiceError,
        read_serving_catalog,
        read_serving_endpoint_material,
    )
    from emergency_eligibility_service import (
        resolve_emergency_eligibility,
        resolve_emergency_offline_bundle_eligibility,
    )
    from emergency_profile_service import (
        EmergencyProfileError,
        build_emergency_singbox_config,
        build_profile_payload,
        build_safe_catalog_payload,
    )
    from models import EmergencyCatalogEndpoint, EmergencyCatalogSnapshot
    from commercial_order_service import (
        CommercialOrderBindingError,
        bind_commercial_offer_to_order,
        expire_failed_commercial_reservations,
    )
    from payment_order_service import (
        PaymentOrderIntentError,
        build_payment_order_intent,
        lock_public_checkout_retry,
        recovered_checkout_fields,
        persist_local_order_intent,
        record_provider_checkout,
        record_provider_checkout_failure,
    )

EMERGENCY_PROBE_PAYLOAD_V1 = b"POKROV emergency probe payload v1\n"
EMERGENCY_PROBE_PAYLOAD_V1_SHA256 = hashlib.sha256(EMERGENCY_PROBE_PAYLOAD_V1).hexdigest()


@app.get("/api/health")
async def health() -> dict:
    return {
        "status": "ok",
        "ts": _utcnow().isoformat(),
        "commercial": commercial_health_snapshot(),
        "payment_db": payment_db_runtime_snapshot(),
    }


@app.get("/api/public/authenticated-egress-probe", status_code=204)
async def authenticated_egress_probe_marker() -> Response:
    return Response(
        status_code=204,
        headers={
            "X-Pokrov-Egress-Probe": "pokrov-authenticated-egress-v1",
            "Cache-Control": "no-store",
        },
    )


@app.get("/api/emergency-probe/payload-v1")
async def emergency_probe_payload_v1(request: Request) -> Response:
    """Owned deterministic payload used only by the controlled Core adapter."""

    headers = {
        "Cache-Control": "no-store",
        "X-Pokrov-Probe-Schema": "pokrov-emergency-probe-payload-v1",
        "X-Content-SHA256": EMERGENCY_PROBE_PAYLOAD_V1_SHA256,
    }
    public_ip = request_public_ip(request)
    country = lookup_country_code(public_ip) if public_ip else None
    if country:
        headers["X-Pokrov-Exit-Country"] = country
    return Response(
        content=EMERGENCY_PROBE_PAYLOAD_V1,
        media_type="application/octet-stream",
        headers=headers,
    )


def _emergency_eligibility_projection(eligibility: Any) -> dict[str, Any]:
    return {
        "eligible": bool(eligibility.eligible),
        "accessEligible": bool(eligibility.access_eligible),
        "networkEligible": bool(eligibility.network_eligible),
        "source": str(eligibility.source or ""),
        "countryCode": eligibility.country_code,
        "validUntil": _safe_iso(eligibility.valid_until),
    }


def _emergency_owned_hops(*, session: Any, user: Any) -> tuple[Any | None, Any | None, list[str]]:
    rollout_config = load_network_rollout_config(session=session)
    nodes_for_user = _nodes_for_user(user, enabled_nodes(session), session=session)
    effective_nodes = _effective_transport_nodes(
        nodes=nodes_for_user,
        transport_profile=LEGACY_REALITY_FALLBACK,
        rollout_config=rollout_config,
    )
    effective_nodes = rank_nodes_for_app(
        effective_nodes,
        policy_by_code=_node_capacity_policy_by_code(session),
        now=_utcnow(),
    )
    foreign = next(
        (
            node
            for node in effective_nodes
            if _node_code_base(str(getattr(node, "code", "") or "")) != "ru"
        ),
        None,
    )
    owned_ru = next(
        (
            node
            for node in effective_nodes
            if _node_code_base(str(getattr(node, "code", "") or "")) == "ru"
        ),
        None,
    )
    modes = ["reserve_direct"]
    if foreign is not None:
        modes.append("reserve_foreign")
    if foreign is not None and owned_ru is not None:
        modes.append("reserve_ru_foreign")
    return foreign, owned_ru, modes


def _emergency_owned_outbound(*, user: Any, node: Any, tag: str) -> dict[str, Any]:
    return _node_outbound_from_transport_profile(
        user_uuid=str(getattr(user, "uuid", "") or ""),
        node=node,
        tag=tag,
        transport_profile=LEGACY_REALITY_FALLBACK,
    )


def _observe_emergency_request_country(
    *,
    session: Any,
    user: Any,
    install_id: str,
    request: Request,
) -> None:
    country = observe_request_country(
        session,
        request=request,
        account_id=str(getattr(user, "account_id", "") or ""),
        install_id=install_id,
    )
    if country:
        session.commit()


def _build_emergency_profile_envelope(
    *,
    session: Any,
    user: Any,
    crypto: EmergencyCatalogCrypto,
    catalog_revision: str,
    reserve_id: str,
    chain_mode: str,
    access_state: str,
    access_expiry: datetime | None,
    eligibility: Any,
    foreign: Any | None,
    owned_ru: Any | None,
    supported_modes: list[str],
    install_id: str,
) -> dict[str, Any]:
    try:
        selected = read_serving_endpoint_material(
            session,
            stable_id=reserve_id,
            crypto=crypto,
        )
    except (EmergencyCatalogCryptoError, EmergencyCatalogServiceError):
        raise HTTPException(status_code=409, detail="Emergency catalog changed")
    if selected.catalog.get("catalog_version") != catalog_revision:
        raise HTTPException(status_code=409, detail="Emergency catalog changed")
    if chain_mode not in supported_modes:
        raise HTTPException(status_code=409, detail="Emergency route is unavailable")
    foreign_outbound = (
        _emergency_owned_outbound(user=user, node=foreign, tag="owned-foreign")
        if foreign is not None
        else None
    )
    ru_outbound = (
        _emergency_owned_outbound(user=user, node=owned_ru, tag="owned-ru")
        if owned_ru is not None
        else None
    )
    try:
        config = build_emergency_singbox_config(
            reserve_outbound=selected.record["outbound"],
            chain_mode=chain_mode,
            foreign_outbound=foreign_outbound,
            ru_outbound=ru_outbound,
            ruleset_base_url=_singbox_rule_set_base_url(),
        )
        catalog_expiry = datetime.fromisoformat(
            str(selected.catalog.get("expires_at") or "").replace("Z", "+00:00")
        )
        profile = build_profile_payload(
            catalog_revision=str(selected.catalog["catalog_version"]),
            reserve_id=reserve_id,
            chain_mode=chain_mode,
            install_id=install_id,
            access_state=access_state,
            access_expiry=access_expiry,
            eligibility=eligibility,
            catalog_expiry=catalog_expiry,
            config_payload=config,
        )
        return crypto.signed_envelope(profile)
    except (EmergencyCatalogCryptoError, EmergencyProfileError, ValueError):
        raise HTTPException(status_code=409, detail="Emergency profile is unavailable")


@app.get("/api/client/emergency-network/catalog")
async def client_emergency_network_catalog(
    request: Request,
    manual_limited_network: bool = Query(default=False),
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    s, user, auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        install_id = _client_authenticated_install_id(s, user=user, auth_user=auth_user)
        _observe_emergency_request_country(
            session=s,
            user=user,
            install_id=install_id,
            request=request,
        )
        access_policy = _build_reconciled_access_policy(
            session=s,
            user=user,
            used_bytes=0,
            source="emergency_catalog",
        )
        eligibility = resolve_emergency_eligibility(
            s,
            account_id=str(getattr(user, "account_id", "") or ""),
            install_id=install_id,
            access_state=str(access_policy.get("access_state") or ""),
            manual_limited_network=bool(manual_limited_network),
        )
        base: dict[str, Any] = {
            "schemaVersion": "pokrov-emergency-catalog-response-v1",
            "available": False,
            "reason": "not_eligible",
            "eligibility": _emergency_eligibility_projection(eligibility),
            "disclosure": {
                "title": "Экстренная сеть POKROV",
                "body": "В прямом аварийном режиме первая точка может быть из согласованного внешнего пула и не управляется POKROV.",
                "warpSupported": False,
            },
            "envelope": None,
        }
        if not eligibility.eligible:
            return base
        try:
            crypto = EmergencyCatalogCrypto.from_environment()
            payload = read_serving_catalog(s, crypto=crypto)
        except (EmergencyCatalogCryptoError, EmergencyCatalogServiceError):
            base["reason"] = "catalog_unavailable"
            return base

        snapshot = (
            s.query(EmergencyCatalogSnapshot)
            .filter(EmergencyCatalogSnapshot.catalog_version == str(payload["catalog_version"]))
            .first()
        )
        if snapshot is None:
            return base
        rows = (
            s.query(EmergencyCatalogEndpoint)
            .filter(
                EmergencyCatalogEndpoint.snapshot_id == snapshot.id,
                EmergencyCatalogEndpoint.stable_id.in_(
                    [
                        str(item.get("stable_id") or "")
                        for item in payload.get("endpoints", [])
                        if isinstance(item, dict)
                    ]
                ),
            )
            .all()
        )
        row_by_id = {row.stable_id: row for row in rows}
        _foreign, _owned_ru, modes = _emergency_owned_hops(session=s, user=user)
        try:
            signed_payload = build_safe_catalog_payload(
                catalog=payload,
                endpoint_rows=row_by_id,
                install_id=install_id,
                access_state=str(access_policy.get("access_state") or ""),
                access_expiry=getattr(user, "expiry_at", None),
                eligibility=eligibility,
                supported_modes=modes,
            )
            usable_count = sum(
                1
                for item in signed_payload["items"]
                if item.get("status") in {"working", "stale"}
            )
            if usable_count < 4:
                base["reason"] = "insufficient_working_reserves"
                return base
            base["available"] = True
            base["reason"] = "ready"
            base["envelope"] = crypto.signed_envelope(signed_payload)
        except (EmergencyCatalogCryptoError, EmergencyProfileError):
            base["reason"] = "catalog_invalid"
        return base
    finally:
        s.close()


@app.post("/api/client/emergency-network/offline-bundle")
async def client_emergency_network_offline_bundle(
    request: Request,
    response: Response,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    raw_body = await request.body()
    if len(raw_body) > 1024:
        raise HTTPException(status_code=413, detail="Emergency bundle request is too large")
    try:
        body = json.loads(raw_body.decode("utf-8"))
    except (UnicodeError, ValueError):
        raise HTTPException(status_code=422, detail="Emergency bundle request is invalid")
    if (
        not isinstance(body, dict)
        or not set(body).issubset({"manual_limited_network", "precache_only"})
        or "manual_limited_network" not in body
        or not isinstance(body.get("manual_limited_network"), bool)
        or ("precache_only" in body and not isinstance(body.get("precache_only"), bool))
    ):
        raise HTTPException(status_code=422, detail="Emergency bundle request is invalid")

    response.headers["Cache-Control"] = "no-store"
    s, user, auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        install_id = _client_authenticated_install_id(s, user=user, auth_user=auth_user)
        _observe_emergency_request_country(
            session=s,
            user=user,
            install_id=install_id,
            request=request,
        )
        access_policy = _build_reconciled_access_policy(
            session=s,
            user=user,
            used_bytes=0,
            source="emergency_offline_bundle",
        )
        access_state = str(access_policy.get("access_state") or "")
        access_expiry = getattr(user, "expiry_at", None)
        eligibility = resolve_emergency_offline_bundle_eligibility(
            s,
            account_id=str(getattr(user, "account_id", "") or ""),
            install_id=install_id,
            access_state=access_state,
            manual_limited_network=body["manual_limited_network"],
            precache_only=bool(body.get("precache_only", False)),
        )
        if not eligibility.eligible:
            raise HTTPException(status_code=403, detail="Emergency network is not available")
        try:
            crypto = EmergencyCatalogCrypto.from_environment()
            catalog = read_serving_catalog(s, crypto=crypto)
        except (EmergencyCatalogCryptoError, EmergencyCatalogServiceError):
            raise HTTPException(status_code=409, detail="Emergency catalog is unavailable")

        snapshot = (
            s.query(EmergencyCatalogSnapshot)
            .filter(EmergencyCatalogSnapshot.catalog_version == str(catalog["catalog_version"]))
            .first()
        )
        if snapshot is None:
            raise HTTPException(status_code=409, detail="Emergency catalog is unavailable")
        raw_endpoints = [
            item for item in catalog.get("endpoints", []) if isinstance(item, dict)
        ]
        rows = (
            s.query(EmergencyCatalogEndpoint)
            .filter(
                EmergencyCatalogEndpoint.snapshot_id == snapshot.id,
                EmergencyCatalogEndpoint.stable_id.in_(
                    [str(item.get("stable_id") or "") for item in raw_endpoints]
                ),
            )
            .all()
        )
        row_by_id = {row.stable_id: row for row in rows}
        foreign, owned_ru, supported_modes = _emergency_owned_hops(session=s, user=user)
        try:
            catalog_payload = build_safe_catalog_payload(
                catalog=catalog,
                endpoint_rows=row_by_id,
                install_id=install_id,
                access_state=access_state,
                access_expiry=access_expiry,
                eligibility=eligibility,
                supported_modes=supported_modes,
            )
            usable_items = [
                item
                for item in catalog_payload["items"]
                if item.get("status") in {"working", "stale"}
            ]
            if len(usable_items) < 4:
                raise HTTPException(
                    status_code=409,
                    detail="Emergency catalog has insufficient working reserves",
                )
            catalog_envelope = crypto.signed_envelope(catalog_payload)
        except (EmergencyCatalogCryptoError, EmergencyProfileError):
            raise HTTPException(status_code=409, detail="Emergency catalog is unavailable")

        profile_envelopes: list[dict[str, Any]] = []
        for item in usable_items:
            reserve_id = str(item["id"])
            for chain_mode in item["modes"]:
                profile_envelopes.append(
                    {
                        "reserveId": reserve_id,
                        "chainMode": chain_mode,
                        "envelope": _build_emergency_profile_envelope(
                            session=s,
                            user=user,
                            crypto=crypto,
                            catalog_revision=str(catalog_payload["catalog_revision"]),
                            reserve_id=reserve_id,
                            chain_mode=str(chain_mode),
                            access_state=access_state,
                            access_expiry=access_expiry,
                            eligibility=eligibility,
                            foreign=foreign,
                            owned_ru=owned_ru,
                            supported_modes=supported_modes,
                            install_id=install_id,
                        ),
                    }
                )
        return {
            "schemaVersion": "pokrov-emergency-offline-bundle-v1",
            "catalogEnvelope": catalog_envelope,
            "profileEnvelopes": profile_envelopes,
        }
    finally:
        s.close()


@app.post("/api/client/emergency-network/profile")
async def client_emergency_network_profile(
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    raw_body = await request.body()
    if len(raw_body) > 4096:
        raise HTTPException(status_code=413, detail="Emergency profile request is too large")
    try:
        body = json.loads(raw_body.decode("utf-8"))
    except (UnicodeError, ValueError):
        raise HTTPException(status_code=422, detail="Emergency profile request is invalid")
    allowed_keys = {"catalog_revision", "reserve_id", "chain_mode", "manual_limited_network"}
    if not isinstance(body, dict) or set(body) != allowed_keys:
        raise HTTPException(status_code=422, detail="Emergency profile request is invalid")
    if not isinstance(body.get("manual_limited_network"), bool):
        raise HTTPException(status_code=422, detail="Emergency profile request is invalid")

    s, user, auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        install_id = _client_authenticated_install_id(s, user=user, auth_user=auth_user)
        _observe_emergency_request_country(
            session=s,
            user=user,
            install_id=install_id,
            request=request,
        )
        access_policy = _build_reconciled_access_policy(
            session=s,
            user=user,
            used_bytes=0,
            source="emergency_profile",
        )
        eligibility = resolve_emergency_eligibility(
            s,
            account_id=str(getattr(user, "account_id", "") or ""),
            install_id=install_id,
            access_state=str(access_policy.get("access_state") or ""),
            manual_limited_network=body["manual_limited_network"],
        )
        if not eligibility.eligible:
            raise HTTPException(status_code=403, detail="Emergency network is not available")
        try:
            crypto = EmergencyCatalogCrypto.from_environment()
        except EmergencyCatalogCryptoError:
            raise HTTPException(status_code=409, detail="Emergency profile is unavailable")
        foreign, owned_ru, supported_modes = _emergency_owned_hops(session=s, user=user)
        chain_mode = str(body.get("chain_mode") or "").strip().lower()
        envelope = _build_emergency_profile_envelope(
            session=s,
            user=user,
            crypto=crypto,
            catalog_revision=str(body.get("catalog_revision") or ""),
            reserve_id=str(body.get("reserve_id") or ""),
            chain_mode=chain_mode,
            access_state=str(access_policy.get("access_state") or ""),
            access_expiry=getattr(user, "expiry_at", None),
            eligibility=eligibility,
            foreign=foreign,
            owned_ru=owned_ru,
            supported_modes=supported_modes,
            install_id=install_id,
        )
        return {
            "schemaVersion": "pokrov-emergency-profile-response-v1",
            "envelope": envelope,
        }
    finally:
        s.close()


@app.post("/api/internal/observer/batches")
async def api_internal_observer_batches(
    request: Request,
    x_portal_node: str = Header(default=""),
    x_portal_timestamp: str = Header(default=""),
    x_portal_signature: str = Header(default=""),
) -> dict:
    raw_body = await request.body()
    try:
        raw_payload = json.loads(raw_body.decode("utf-8", errors="replace"))
        payload = ObserverBatchIn.model_validate(raw_payload if isinstance(raw_payload, dict) else {})
    except Exception:
        raise HTTPException(status_code=400, detail="Observer batch payload is invalid")

    try:
        timestamp = int(str(x_portal_timestamp or "").strip())
    except Exception:
        raise HTTPException(status_code=401, detail="Observer push timestamp is invalid")

    s = SessionLocal()
    node_id: int | None = None
    try:
        node = _verify_observer_push(
            s=s,
            node_code=x_portal_node,
            timestamp=timestamp,
            signature=x_portal_signature,
            raw_body=raw_body,
        )
        node_id = int(node.id)
        result = ingest_observer_batch(
            s=s,
            node=node,
            batch_id=payload.batch_id,
            cursor=payload.cursor,
            observations=[item.model_dump() for item in payload.observations],
            collector_parse_error_count=int(payload.parse_error_count or 0),
            received_at=_utcnow(),
        )
        s.commit()
        return result
    except HTTPException:
        s.rollback()
        raise
    except IntegrityError as exc:
        s.rollback()
        if node_id is not None and is_observer_batch_unique_conflict(exc):
            existing = (
                s.query(ObserverBatch)
                .filter(ObserverBatch.node_id == node_id, ObserverBatch.batch_id == payload.batch_id)
                .first()
            )
            if existing is not None:
                return observer_batch_replay_response(existing)
        logger.exception("observer batch integrity failure node=%s", str(x_portal_node or "").strip().lower())
        raise HTTPException(status_code=500, detail="Observer batch ingest failed")
    except Exception:
        s.rollback()
        logger.exception("observer batch ingest failed node=%s", str(x_portal_node or "").strip().lower())
        raise HTTPException(status_code=500, detail="Observer batch ingest failed")
    finally:
        s.close()


@app.get("/api/public/plans")
async def public_plans(response: Response) -> dict:
    s = SessionLocal()
    try:
        plans = _plan_catalog_payload(s=s, only_active=True)
        try:
            assert_plan_projection_matches_contract(plans)
        except CommercialContractError as exc:
            logger.error("commercial_plan_contract_mismatch code=%s", str(exc))
            raise HTTPException(
                status_code=503, detail="Commercial plans unavailable"
            ) from exc
        response.headers["Cache-Control"] = "public, max-age=120"
        return {
            "commercial_revision": commercial_revision(),
            "commercial_contract_sha256": commercial_contract_sha256(),
            "plans": plans,
            "widget_enabled": bool(CHECKOUT_WIDGET_ENABLED),
        }
    finally:
        s.close()


@app.get("/api/public/catalog")
async def public_catalog(response: Response) -> dict:
    s = SessionLocal()
    try:
        response.headers["Cache-Control"] = "public, max-age=120"
        try:
            return _public_catalog_payload(s=s)
        except CommercialContractError as exc:
            logger.error("commercial_catalog_contract_mismatch code=%s", str(exc))
            raise HTTPException(
                status_code=503, detail="Commercial catalog unavailable"
            ) from exc
    finally:
        s.close()


@app.get("/api/public/trust-catalog")
async def public_trust_catalog(response: Response) -> dict[str, Any]:
    path = Path(__file__).resolve().parents[1] / "shared" / "trust-and-guides.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        logger.exception("public trust catalog unavailable")
        raise HTTPException(status_code=503, detail="Trust catalog unavailable")
    response.headers["Cache-Control"] = "public, max-age=300"
    return payload


@app.get("/api/public/live-updates")
async def public_live_updates(response: Response, limit: int = Query(default=3, ge=1, le=10)) -> dict:
    s = SessionLocal()
    try:
        rows = (
            s.query(LiveUpdate)
            .filter(LiveUpdate.is_active == True)
            .order_by(LiveUpdate.sort_order.asc(), LiveUpdate.id.desc())
            .limit(int(limit))
            .all()
        )
        if not rows:
            response.headers["Cache-Control"] = "public, max-age=120"
            return {"updates": _default_live_updates()[: int(limit)]}
        out = []
        for row in rows:
            tg_link = _build_tg_post_link(
                channel_username=getattr(row, "channel_username", None),
                post_id=getattr(row, "post_id", None),
                fallback_link=str(row.link or "").strip(),
            )
            channel_raw = str(getattr(row, "channel_username", "") or "").strip().lstrip("@")
            out.append(
                {
                    "id": int(row.id),
                    "title": str(row.title or "").strip(),
                    "summary": str(row.summary or "").strip(),
                    "date": (row.published_at or row.created_at or _utcnow()).date().isoformat(),
                    "link": tg_link,
                    "tg_link": tg_link,
                    "channel_username": channel_raw or None,
                    "post_id": int(getattr(row, "post_id", 0) or 0) or None,
                    "is_active": bool(row.is_active),
                    "sort_order": int(row.sort_order or 0),
                }
            )
        response.headers["Cache-Control"] = "public, max-age=120"
        return {"updates": out}
    finally:
        s.close()


@app.get("/api/public/service-status")
async def public_service_status(response: Response) -> dict[str, Any]:
    s = SessionLocal()
    try:
        current = (
            s.query(ServiceIncident)
            .filter(ServiceIncident.status == "confirmed")
            .order_by(ServiceIncident.started_at.desc())
            .limit(10)
            .all()
        )
        recent = (
            s.query(ServiceIncident)
            .filter(ServiceIncident.status == "resolved")
            .order_by(ServiceIncident.ended_at.desc(), ServiceIncident.started_at.desc())
            .limit(10)
            .all()
        )
        response.headers["Cache-Control"] = "public, max-age=30"
        return {
            "status": "degraded" if current else "operational",
            "checkedAt": _safe_iso(_utcnow()),
            "current": [incident_service.incident_payload(row) for row in current],
            "recent": [incident_service.incident_payload(row) for row in recent],
        }
    finally:
        s.close()


def _public_program_capabilities() -> list[dict[str, Any]]:
    return [
            {
                "kind": "competitor_switch",
                "title": "Переход от другого VPN",
                "enabled": True,
                "review": "manual",
                "reward": "Предложение определяется после проверки; автоматического бонуса нет.",
            },
            {
                "kind": "research",
                "title": "Исследования и качественные баг-репорты",
                "enabled": True,
                "review": "manual",
                "reward": "За подтверждённый вклад оператор может начислить 1, 3 или 7 дней.",
            },
            {
                "kind": "team_pack",
                "title": "Набор для команды",
                "enabled": True,
                "review": "manual",
                "reward": "Персональное предложение для 2–50 устройств без автосписаний.",
            },
            {
                "kind": "affiliate",
                "title": "Партнёрская программа",
                "enabled": False,
                "review": "not_accepting",
                "reward": "Фундамент заложен, заявки и начисления пока выключены.",
            },
        ]


@app.get("/api/public/programs")
async def public_programs(response: Response) -> dict[str, Any]:
    response.headers["Cache-Control"] = "public, max-age=300"
    return {
        "ok": True,
        "programs": _public_program_capabilities(),
        "review_policy": "Заявки не меняют срок доступа до явного решения оператора.",
    }


def _set_web_session_cookie(response: Response, token: str) -> None:
    value = str(token or "").strip()
    if not value:
        return
    response.set_cookie(
        key=WEB_SESSION_COOKIE_NAME,
        value=value,
        max_age=int(SESSION_TTL_SECONDS),
        expires=int(SESSION_TTL_SECONDS),
        path="/",
        domain=WEB_SESSION_COOKIE_DOMAIN or None,
        secure=True,
        httponly=True,
        samesite=WEB_SESSION_COOKIE_SAMESITE if WEB_SESSION_COOKIE_SAMESITE in {"lax", "strict", "none"} else "lax",
    )


@app.post("/api/auth/telegram/web-login")
async def auth_telegram_web_login(payload: TelegramWebLoginIn, request: Request, response: Response) -> dict:
    _enforce_beta_rate_limit("telegram_auth", request)
    verified = verify_telegram_login_payload(
        payload=payload.model_dump(),
        bot_token=_current_bot_token(),
        max_age_seconds=TELEGRAM_WEB_LOGIN_MAX_AGE_SECONDS,
    )
    if not verified:
        try:
            auth_age = int(time.time()) - int(payload.auth_date or 0)
        except Exception:
            auth_age = 0
        if auth_age > int(TELEGRAM_WEB_LOGIN_MAX_AGE_SECONDS):
            raise _auth_http_exception(
                detail="Сессия Telegram устарела. Нажмите вход через Telegram еще раз, и мы сразу вернем вас в кабинет.",
                code="telegram_login_expired",
            )
        raise _auth_http_exception(
            detail="Telegram не подтвердил вход. Повторите вход через кнопку Telegram.",
            code="telegram_login_invalid",
        )

    tg_id = int(verified.get("id") or 0)
    if tg_id <= 0:
        raise _auth_http_exception(
            detail="Telegram не подтвердил пользователя. Повторите вход через кнопку Telegram.",
            code="telegram_login_invalid_user",
        )
    username = (verified.get("username") or "").strip() or None
    _ensure_user_row_for_login(tg_id=tg_id, username=username)
    token = create_web_session_token(
        tg_id=tg_id,
        username=username,
        auth_type="telegram",
        auth_origin="telegram",
    )
    if not token:
        raise HTTPException(status_code=500, detail="Web session is not configured")
    _set_web_session_cookie(response, token)
    return {
        "ok": True,
        "token": token,
        "token_transport": "cookie_and_legacy_bearer",
        "user": {"id": tg_id, "username": username},
        "expires_in": int(SESSION_TTL_SECONDS),
    }


@app.get("/api/auth/telegram/oidc/start")
async def auth_telegram_oidc_start() -> dict:
    try:
        payload = build_telegram_oidc_authorize_url()
    except RuntimeError as exc:
        # Configuration exceptions can include the configured redirect URL or
        # other deployment detail. Keep the public auth contract fixed.
        logger.warning("telegram_oidc_start_failed code=telegram_oidc_unavailable")
        raise _auth_http_exception(
            detail="Telegram sign-in is temporarily unavailable. Try again later.",
            code="telegram_oidc_unavailable",
            status_code=503,
        ) from exc
    return {
        "ok": True,
        "mode": "oidc",
        "auth_url": payload["auth_url"],
        "redirect_uri": payload["redirect_uri"],
    }


@app.post("/api/auth/telegram/oidc/finish")
async def auth_telegram_oidc_finish(payload: TelegramOidcFinishIn, response: Response) -> dict:
    if not verify_telegram_oidc_state_token(payload.state):
        raise _auth_http_exception(
            detail="Telegram sign-in expired. Start sign-in again.",
            code="telegram_oidc_state_expired",
        )
    try:
        verified = await exchange_telegram_oidc_code(
            code=payload.code,
            state_token=payload.state,
        )
    except ValueError as exc:
        logger.warning("telegram_oidc_finish_failed code=telegram_oidc_invalid")
        raise _auth_http_exception(
            detail="Telegram sign-in could not be verified. Start sign-in again.",
            code="telegram_oidc_invalid",
        ) from exc
    except RuntimeError as exc:
        # Provider and transport errors may contain response bodies, URLs,
        # addresses, ports or credentials. Log only the stable classification.
        logger.warning("telegram_oidc_finish_failed code=telegram_oidc_unavailable")
        raise _auth_http_exception(
            detail="Telegram sign-in is temporarily unavailable. Try again later.",
            code="telegram_oidc_unavailable",
            status_code=502,
        ) from exc

    tg_id = int(verified.get("id") or 0)
    if tg_id <= 0:
        raise HTTPException(status_code=401, detail="Invalid Telegram user")
    username = (verified.get("preferred_username") or verified.get("username") or "").strip() or None
    _ensure_user_row_for_login(tg_id=tg_id, username=username)
    token = create_web_session_token(
        tg_id=tg_id,
        username=username,
        auth_type="telegram",
        auth_origin="telegram",
    )
    if not token:
        raise HTTPException(status_code=500, detail="Web session is not configured")
    _set_web_session_cookie(response, token)
    return {
        "ok": True,
        "token": token,
        "token_transport": "cookie_and_legacy_bearer",
        "user": {"id": tg_id, "username": username},
        "expires_in": int(SESSION_TTL_SECONDS),
    }


@app.get("/api/auth/email/status")
async def auth_email_status() -> dict[str, Any]:
    status = dict(email_delivery_runtime_status())
    otp_configured = email_login_otp_configured()
    status["otp_configured"] = bool(otp_configured)
    if not otp_configured:
        blocked = list(status.get("blocked_reasons") or [])
        if "otp_secret_missing" not in blocked:
            blocked.append("otp_secret_missing")
        status["blocked_reasons"] = blocked
        status["enabled"] = False
    return status


@app.post("/api/auth/email/register")
async def auth_email_register(
    payload: EmailRegisterIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    _require_email_public_ready()
    _enforce_beta_rate_limit("email_auth", request, identity=str(payload.email or "").strip().lower())
    auth_user = _optional_auth_user(x_telegram_init_data, request=request)
    linked_tg_id = int((auth_user or {}).get("id") or 0) or None
    s = SessionLocal()
    try:
        try:
            identity, verify_token = register_email_identity(
                s,
                email=payload.email,
                password=payload.password,
                linked_tg_id=linked_tg_id,
                display_name=payload.display_name,
            )
        except DuplicateEmailIdentityError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except InvalidEmailInputError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        s.commit()
        s.refresh(identity)
        delivery = await deliver_auth_message(
            kind="verify",
            email=str(identity.email),
            token=verify_token,
            linked_tg_id=int(identity.linked_tg_id or 0),
        )
        debug = build_email_auth_debug_payload(verify_token=verify_token)
        return {
            "ok": True,
            "verification_required": True,
            "delivery": delivery,
            "identity": _email_identity_payload(identity),
            "debug": debug,
        }
    except HTTPException:
        s.rollback()
        raise
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


@app.post("/api/auth/email/verify")
async def auth_email_verify(payload: EmailVerifyIn, request: Request, response: Response) -> dict:
    _enforce_beta_rate_limit("email_auth", request)
    s = SessionLocal()
    try:
        try:
            identity = verify_email_identity(s, token=payload.token)
        except InvalidEmailTokenError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        user = s.query(User).filter(User.tg_id == int(identity.linked_tg_id)).first()
        if not user:
            raise HTTPException(status_code=409, detail="Linked account is missing")
        token = create_web_session_token(
            tg_id=int(user.tg_id),
            username=str(user.username or "").strip() or None,
            auth_type="email",
            auth_origin="email",
            email=str(identity.email),
        )
        if not token:
            raise HTTPException(status_code=500, detail="Web session is not configured")
        s.commit()
        _set_web_session_cookie(response, token)
        return {
            "ok": True,
            "token": token,
            "token_transport": "cookie_and_legacy_bearer",
            "expires_in": int(SESSION_TTL_SECONDS),
            "user": {
                "id": int(user.tg_id),
                "username": str(user.username or "").strip() or None,
                "email": str(identity.email),
            },
        }
    except HTTPException:
        s.rollback()
        raise
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


@app.post("/api/auth/email/login")
async def auth_email_login(payload: EmailLoginIn, request: Request, response: Response) -> dict:
    _enforce_beta_rate_limit("email_auth", request, identity=str(payload.email or "").strip().lower())
    s = SessionLocal()
    try:
        try:
            identity = authenticate_email_identity(
                s,
                email=payload.email,
                password=payload.password,
            )
        except (InvalidEmailInputError, InvalidEmailCredentialsError) as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        user = s.query(User).filter(User.tg_id == int(identity.linked_tg_id)).first()
        if not user:
            raise HTTPException(status_code=409, detail="Linked account is missing")
        token = create_web_session_token(
            tg_id=int(user.tg_id),
            username=str(user.username or "").strip() or None,
            auth_type="email",
            auth_origin="email",
            email=str(identity.email),
        )
        if not token:
            raise HTTPException(status_code=500, detail="Web session is not configured")
        s.commit()
        _set_web_session_cookie(response, token)
        return {
            "ok": True,
            "token": token,
            "auth_method": "password_compatibility",
            "token_transport": "cookie_and_legacy_bearer",
            "expires_in": int(SESSION_TTL_SECONDS),
            "user": {
                "id": int(user.tg_id),
                "username": str(user.username or "").strip() or None,
                "email": str(identity.email),
            },
        }
    except HTTPException:
        s.rollback()
        raise
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


async def _deliver_login_otp_background(
    *,
    email: str,
    code: str,
    linked_tg_id: int,
) -> None:
    try:
        await deliver_auth_message(
            kind="login_otp",
            email=email,
            token=code,
            linked_tg_id=linked_tg_id,
        )
    except Exception:
        logger.exception("email OTP background delivery failed")


@app.post("/api/auth/email/otp/start")
async def auth_email_otp_start(
    payload: EmailOtpStartIn,
    request: Request,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    _require_email_public_ready()
    if not email_login_otp_configured():
        raise _account_recovery_http_exception(EmailOtpError("email_otp_not_configured"))
    try:
        email_norm = validate_email_input(payload.email)
    except InvalidEmailInputError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    email_fingerprint = hashlib.sha256(email_norm.encode("utf-8")).hexdigest()[:32]
    _enforce_beta_rate_limit("email_otp_start_ip", request)
    _enforce_beta_rate_limit("email_otp_start", request, identity=f"email_sha256:{email_fingerprint}")

    s = SessionLocal()
    try:
        identity, code = issue_login_otp(s, email=email_norm, now=_utcnow())
        s.commit()
        if identity is not None and code is not None:
            background_tasks.add_task(
                _deliver_login_otp_background,
                email=str(identity.email),
                code=code,
                linked_tg_id=int(identity.linked_tg_id or 0),
            )
        return {
            "ok": True,
            "otp_requested": True,
            "expires_in": 300,
            "delivery": {"status": "accepted", "kind": "login_otp"},
        }
    except (InvalidEmailInputError, EmailOtpError) as exc:
        s.rollback()
        if isinstance(exc, EmailOtpError):
            raise _account_recovery_http_exception(exc) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


@app.post("/api/auth/email/otp/finish")
async def auth_email_otp_finish(
    payload: EmailOtpFinishIn,
    request: Request,
    response: Response,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    if not email_login_otp_configured():
        raise _account_recovery_http_exception(EmailOtpError("email_otp_not_configured"))
    email_fingerprint = hashlib.sha256(str(payload.email or "").strip().lower().encode("utf-8")).hexdigest()[:32]
    _enforce_beta_rate_limit("email_otp_finish_ip", request)
    _enforce_beta_rate_limit("email_otp_finish", request, identity=f"email_sha256:{email_fingerprint}")
    if payload.install_id:
        install_fingerprint = hashlib.sha256(str(payload.install_id).strip().encode("utf-8")).hexdigest()[:32]
        _enforce_beta_rate_limit(
            "email_otp_finish_install",
            request,
            identity=f"install_sha256:{install_fingerprint}",
        )
    try:
        current_auth = _optional_auth_user(x_telegram_init_data, request=request)
    except HTTPException:
        current_auth = None

    now = _utcnow()
    s = SessionLocal()
    try:
        try:
            identity = consume_login_otp(
                s,
                email=payload.email,
                code=payload.code,
                now=now,
            )
        except (InvalidEmailInputError, EmailOtpError) as exc:
            raise _account_recovery_http_exception(
                exc if isinstance(exc, EmailOtpError) else EmailOtpError("email_otp_invalid")
            ) from exc
        user = s.query(User).filter(User.tg_id == int(identity.linked_tg_id)).first()
        if user is None:
            raise HTTPException(status_code=409, detail="Linked account is missing")
        account_id = str(getattr(user, "account_id", "") or "").strip()
        if not account_id:
            raise HTTPException(status_code=409, detail="Canonical account is missing")

        issued_session = None
        fresh_auth_until = None
        install_id = str(payload.install_id or "").strip()
        if install_id:
            existing_device = s.query(AccountDevice).filter(AccountDevice.install_id == install_id).first()
            active_devices = (
                s.query(func.count(AccountDevice.id))
                .filter(
                    AccountDevice.account_id == account_id,
                    AccountDevice.state == "active",
                    AccountDevice.revoked_at.is_(None),
                )
                .scalar()
                or 0
            )
            if existing_device is None and int(active_devices) >= int(_plan_device_limit(user)):
                raise _account_recovery_http_exception(AccountRecoveryError("device_limit_reached"))
            try:
                issued_session = auth_session_service.issue_authenticated_device_session(
                    s,
                    account_id=account_id,
                    install_id=install_id,
                    device_name=str(payload.device_name or "Authenticated device"),
                    platform=str(payload.platform or "device"),
                    os_version=payload.os_version,
                    app_version=payload.app_version,
                    locale=payload.locale,
                    time_zone=payload.time_zone,
                    scope="client",
                    auth_origin="email_otp",
                    now=now,
                )
            except auth_session_service.AuthSessionError as exc:
                raise _auth_session_http_exception(exc) from exc
            fresh_auth_until = now + timedelta(seconds=auth_session_service.APP_FRESH_AUTH_MAX_AGE_SECONDS)
        else:
            current_session_id = str((current_auth or {}).get("session_id") or "").strip()
            current_account_id = str((current_auth or {}).get("account_id") or "").strip()
            if current_session_id and current_account_id == account_id:
                try:
                    auth_session_service.mark_session_fresh(
                        s,
                        account_id=account_id,
                        session_id=current_session_id,
                        now=now,
                    )
                except auth_session_service.AuthSessionError as exc:
                    raise _auth_session_http_exception(exc) from exc
                fresh_auth_until = now + timedelta(seconds=auth_session_service.APP_FRESH_AUTH_MAX_AGE_SECONDS)

        if issued_session is not None:
            session_payload = issued_session.response_payload(now=now)
            session_payload["scope"] = "client"
            s.commit()
            return {
                "ok": True,
                "auth_method": "email_otp",
                "token": issued_session.access_token,
                "access_token": issued_session.access_token,
                "refresh_token": issued_session.refresh_token,
                "token_transport": "bearer",
                "fresh_auth_until": _safe_iso(fresh_auth_until),
                "session": session_payload,
                "user": {
                    "id": int(user.tg_id),
                    "account_id": account_id,
                    "email": str(identity.email),
                },
            }

        token = create_web_session_token(
            tg_id=int(user.tg_id),
            username=str(user.username or "").strip() or None,
            auth_type="email",
            auth_origin="email_otp",
            email=str(identity.email),
        )
        if not token:
            raise HTTPException(status_code=500, detail="Web session is not configured")
        s.commit()
        _set_web_session_cookie(response, token)
        return {
            "ok": True,
            "auth_method": "email_otp",
            "token": token,
            "token_transport": "cookie_and_legacy_bearer",
            "expires_in": int(SESSION_TTL_SECONDS),
            "fresh_auth_until": _safe_iso(fresh_auth_until),
            "user": {
                "id": int(user.tg_id),
                "account_id": account_id,
                "email": str(identity.email),
            },
        }
    except HTTPException:
        s.rollback()
        raise
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


@app.post("/api/auth/email/recovery/start")
async def auth_email_recovery_start(payload: EmailRecoveryStartIn, request: Request) -> dict:
    _require_email_public_ready()
    _enforce_beta_rate_limit("email_auth", request, identity=str(payload.email or "").strip().lower())
    s = SessionLocal()
    try:
        try:
            identity, reset_token = start_password_reset(s, email=payload.email)
        except InvalidEmailInputError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        s.commit()
        delivery = {"status": "suppressed", "kind": "reset", "email": str(payload.email).strip().lower()}
        if identity and reset_token:
            delivery = await deliver_auth_message(
                kind="reset",
                email=str(identity.email),
                token=reset_token,
                linked_tg_id=int(identity.linked_tg_id or 0),
            )
        debug = build_email_auth_debug_payload(reset_token=reset_token)
        return {
            "ok": True,
            "recovery_requested": True,
            "delivery": delivery,
            "debug": debug,
        }
    except HTTPException:
        s.rollback()
        raise
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


@app.post("/api/auth/email/recovery/finish")
async def auth_email_recovery_finish(payload: EmailRecoveryFinishIn, request: Request, response: Response) -> dict:
    _enforce_beta_rate_limit("email_auth", request)
    s = SessionLocal()
    try:
        try:
            identity = finish_password_reset(
                s,
                token=payload.token,
                password=payload.password,
            )
        except InvalidEmailInputError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except InvalidEmailTokenError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        user = s.query(User).filter(User.tg_id == int(identity.linked_tg_id)).first()
        if not user:
            raise HTTPException(status_code=409, detail="Linked account is missing")
        token = create_web_session_token(
            tg_id=int(user.tg_id),
            username=str(user.username or "").strip() or None,
            auth_type="email",
            auth_origin="email",
            email=str(identity.email),
        )
        if not token:
            raise HTTPException(status_code=500, detail="Web session is not configured")
        s.commit()
        _set_web_session_cookie(response, token)
        return {
            "ok": True,
            "token": token,
            "token_transport": "cookie_and_legacy_bearer",
            "expires_in": int(SESSION_TTL_SECONDS),
            "user": {
                "id": int(user.tg_id),
                "username": str(user.username or "").strip() or None,
                "email": str(identity.email),
            },
        }
    except HTTPException:
        s.rollback()
        raise
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


@app.get("/api/auth/session")
async def auth_session(request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == tg_id).first()
        email_identity = _verified_email_identity_for_account_family(s, user=user)
    finally:
        s.close()
    device_name = app_first_service.normalize_app_device_name(
        (getattr(user, "app_device_name", None) if user else None)
        or (getattr(user, "display_name", None) if user else None),
    )
    token_auth_type = str(auth_user.get("auth_type") or "").strip()
    linked_email = _email_identity_payload(email_identity)
    session_email = str(auth_user.get("email") or "") or ((linked_email or {}).get("email") if linked_email else None)
    auth_type = token_auth_type or ("app" if bool(getattr(user, "is_app_user", False)) else "telegram")
    auth_origin = str(auth_user.get("auth_origin") or "").strip() or auth_type
    telegram_identity_id = _linked_telegram_id(user) or (tg_id if auth_type == "telegram" else 0)
    telegram_identity_username = (
        str(getattr(user, "linked_telegram_username", "") or "").strip() if user else ""
    ) or (
        str(auth_user.get("username") or "").strip() if auth_type == "telegram" else ""
    )
    return {
        "ok": True,
        "user": {
            "id": tg_id,
            "account_id": str(tg_id),
            "username": (auth_user.get("username") or (getattr(user, "username", None) if user else None)),
            "display_name": (str(getattr(user, "display_name", "") or "").strip() if user else None) or None,
            "email": session_email or None,
            "device_name": device_name,
            "linked_telegram_id": _linked_telegram_id(user),
            "linked_telegram_username": (
                str(getattr(user, "linked_telegram_username", "") or "").strip() if user else ""
            )
            or None,
            "is_authorized": True,
            "auth_type": auth_type,
            "auth_origin": auth_origin,
            "linked_identities": {
                "telegram": {
                    "id": telegram_identity_id or None,
                    "username": telegram_identity_username or None,
                }
                if telegram_identity_id
                else None,
                "email": linked_email,
            },
        },
    }


@app.post("/api/admin/auth/session")
async def admin_auth_session(request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = _require_admin(x_telegram_init_data, request=request)
    actor_id = int(actor.get("id") or 0)
    token = create_web_session_token(
        tg_id=actor_id,
        username=str(actor.get("username") or "").strip() or None,
        auth_type="admin",
        auth_origin="adminapp",
        ttl_seconds=int(ADMIN_WEB_SESSION_TTL_SECONDS),
        purpose="admin",
    )
    if not token:
        raise HTTPException(status_code=500, detail="Admin session is not configured")
    return {
        "ok": True,
        "token": token,
        "token_transport": "bearer",
        "expires_in": int(ADMIN_WEB_SESSION_TTL_SECONDS),
        "user": {
            "id": actor_id,
            "username": str(actor.get("username") or "").strip() or None,
            "role": "superadmin",
        },
    }


@app.post("/api/client/session/start-trial")
async def client_start_trial(payload: AppStartTrialIn, request: Request) -> dict:
    client_policy: dict[str, Any] | None = None
    session_now = _utcnow()
    client_ip = _request_client_ip(request)
    trial_event_id = ""
    trial_projection: dict[str, Any] | None = None
    s = SessionLocal()
    try:
        install_id = str(payload.install_id or "").strip()[:128]
        existing_device = (
            s.query(AccountDevice.id)
            .filter(AccountDevice.install_id == install_id)
            .first()
        )
        if existing_device is not None:
            session_history = (
                s.query(AuthSession.id)
                .filter(AuthSession.device_id == str(existing_device.id))
                .first()
            )
            if session_history is not None:
                raise _auth_session_http_exception(
                    auth_session_service.AuthSessionError("device_recovery_required")
                )
        existing_app_account = (
            s.query(User.tg_id).filter(User.app_install_id == install_id).first()
        )
        if not existing_app_account:
            _enforce_beta_rate_limit("start_trial", request)
        user, created = app_first_service.upsert_app_trial_user(
            s=s,
            payload=payload,
            now=session_now,
            trial_days=APP_TRIAL_DEFAULT_DAYS,
            request_client_ip=client_ip,
        )
        account_device = (
            s.query(AccountDevice).filter(AccountDevice.install_id == install_id).one()
        )
        trial_event = record_antiabuse_event(
            s,
            event_kind="trial_reserved" if created else "trial_session_issued",
            source="client_api",
            occurred_at=session_now,
            account_id=str(getattr(user, "account_id", "") or "") or None,
            device_id=str(account_device.id),
            install_id=install_id,
            raw_ip=client_ip,
            reasons=["first_install"] if created else ["legacy_install_session"],
            metadata={
                "platform": payload.platform,
                "app_version": payload.app_version,
                "os_major": str(payload.os_version or "").split(".", 1)[0],
                "device_label": payload.device_name,
            },
        )
        trial_event_id = str(trial_event.id)
        s.commit()
        s.refresh(user)
        client_policy = app_first_service.build_client_policy(
            session=s,
            user=user,
            install_id=str(getattr(user, "app_install_id", "") or "").strip() or None,
            carrier=_request_carrier_header(request.headers.get("X-Portal-Carrier")),
        )
        trial_projection = read_trial_projection(
            s, account_id=str(user.account_id), now=session_now
        )
    except HTTPException:
        s.rollback()
        raise
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()

    session_token = create_web_session_token(
        tg_id=int(user.tg_id),
        username=str(user.username or "").strip() or None,
        auth_type="app",
        auth_origin="app",
    )
    if not session_token:
        raise HTTPException(status_code=500, detail="App session is not configured")

    sync_ok = await _sync_control_panel_access(user=user)
    if not sync_ok:
        logger.warning(
            "app start-trial panel sync returned false tg_id=%s plan=%s sub_type=%s",
            int(user.tg_id),
            str(getattr(user, "current_plan_code", "") or ""),
            str(getattr(user, "sub_type", "") or ""),
        )

    start_trial_parts = app_first_service.build_start_trial_response_parts(
        user=user,
        session_token="",
        now=_utcnow(),
        sync_ok=bool(sync_ok),
        build_access_policy=_build_access_policy,
        trial_days=APP_TRIAL_DEFAULT_DAYS,
        channel_bonus_days=CHANNEL_PREMIUM_DAYS,
        client_policy=client_policy,
        trial_projection=trial_projection,
    )
    payload_s = SessionLocal()
    try:
        payload_user = (
            payload_s.query(User).filter(User.tg_id == int(user.tg_id)).first() or user
        )
        payload_nodes = _nodes_for_user(
            payload_user, enabled_nodes(payload_s), session=payload_s
        )
        promo_slots = _promo_slots_payload_for_surface(
            s=payload_s,
            surface="app",
            access_state=str(start_trial_parts["access"].get("access_state") or ""),
            user=payload_user,
        )
        linked_identities = _linked_identities_payload(s=payload_s, user=payload_user)
    finally:
        payload_s.close()

    credential_now = _utcnow()
    session_s = SessionLocal()
    try:
        session_user = (
            session_s.query(User).filter(User.tg_id == int(user.tg_id)).first()
        )
        if session_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        issued_session = auth_session_service.issue_device_session(
            session_s,
            user=session_user,
            install_id=install_id,
            now=credential_now,
        )
        trial_event = (
            session_s.query(AntiAbuseEvent)
            .filter(AntiAbuseEvent.id == trial_event_id)
            .with_for_update()
            .one()
        )
        trial_event.account_id = issued_session.account_id
        trial_event.device_id = issued_session.device_id
        trial_event.session_id = issued_session.session_id
        session_contract = issued_session.response_payload(now=credential_now)
        start_trial_parts["session"].update(session_contract)
        response_payload = {
            "ok": True,
            "created": bool(created),
            "session_token": issued_session.access_token,
            "access_token": issued_session.access_token,
            "refresh_token": issued_session.refresh_token,
            "token_type": "Bearer",
            "expires_in": session_contract["expires_in"],
            "refresh_expires_in": session_contract["refresh_expires_in"],
            "canonical_account_id": issued_session.account_id,
            "account_id": str(int(user.tg_id)),
            "subscription_url": start_trial_parts["subscription_url"],
            "sync_ok": bool(sync_ok),
            "session": start_trial_parts["session"],
            "client_policy": start_trial_parts["client_policy"],
            "access": start_trial_parts["access"],
            "linked_identities": linked_identities,
            "free_caps": _free_caps_payload(
                user=user, access_policy=start_trial_parts["access"]
            ),
            "redeem_eligibility": _redeem_eligibility_payload(
                user=user,
                access_policy=start_trial_parts["access"],
            ),
            "promo_slots": promo_slots,
            "hidden_transport_matrix": _hidden_transport_matrix_payload(
                nodes=payload_nodes,
                client_policy=client_policy,
            ),
            "location_matrix": _location_matrix_payload(
                user=user,
                nodes=payload_nodes,
                client_policy=client_policy,
            ),
            "provisioning": start_trial_parts["provisioning"],
        }
        session_s.commit()
    except HTTPException:
        session_s.rollback()
        raise
    except auth_session_service.AuthSessionError as exc:
        session_s.rollback()
        raise _auth_session_http_exception(exc) from exc
    except Exception:
        session_s.rollback()
        raise
    finally:
        session_s.close()
    return response_payload


@app.post("/api/client/session/refresh")
async def client_session_refresh(payload: AppSessionRefreshIn, request: Request) -> dict[str, Any]:
    refresh_fingerprint = hashlib.sha256(payload.refresh_token.encode("utf-8")).hexdigest()[:32]
    _enforce_beta_rate_limit("session_refresh_ip", request)
    _enforce_beta_rate_limit(
        "session_refresh",
        request,
        identity=f"refresh_sha256:{refresh_fingerprint}",
    )
    now = _utcnow()
    s = SessionLocal()
    try:
        issued = auth_session_service.rotate_device_session(
            s,
            refresh_token=payload.refresh_token,
            now=now,
        )
        s.commit()
    except auth_session_service.AuthSessionError as exc:
        if exc.security_state_changed:
            s.commit()
        else:
            s.rollback()
        raise _auth_session_http_exception(exc) from exc
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()

    session_payload = issued.response_payload(now=now)
    return {
        "ok": True,
        **session_payload,
        "session": dict(session_payload),
    }


@app.post("/api/client/session/revoke")
async def client_session_revoke(
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    account_id = str(auth_user.get("account_id") or "").strip()
    session_id = str(auth_user.get("session_id") or "").strip()
    if not account_id or not session_id:
        raise _auth_http_exception(
            detail="Эта совместимая сессия не поддерживает серверный отзыв.",
            code="session_not_persisted",
            status_code=409,
        )

    s = SessionLocal()
    try:
        auth_session_service.revoke_session(
            s,
            account_id=account_id,
            session_id=session_id,
            now=_utcnow(),
        )
        s.commit()
    except auth_session_service.AuthSessionError as exc:
        s.rollback()
        raise _auth_session_http_exception(exc) from exc
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()
    return {"ok": True, "session_id": session_id, "revoked": True}


@app.post("/api/client/recovery-code/rotate")
async def client_recovery_code_rotate(
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    account_id = str(auth_user.get("account_id") or "").strip()
    session_id = str(auth_user.get("session_id") or "").strip()
    if not account_id or not session_id:
        raise _auth_http_exception(
            detail="Эта совместимая сессия не поддерживает recovery-коды.",
            code="session_not_persisted",
            status_code=409,
        )
    session_fingerprint = hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:32]
    _enforce_beta_rate_limit(
        "recovery_rotate",
        request,
        identity=f"session_sha256:{session_fingerprint}",
    )
    now = _utcnow()
    s = SessionLocal()
    try:
        issued = rotate_recovery_code(
            s,
            account_id=account_id,
            actor_session_id=session_id,
            now=now,
        )
        s.commit()
        return {
            "ok": True,
            "recovery_code": issued.code,
            "code_hint": issued.code_hint,
            "version": int(issued.version),
            "shown_once": True,
        }
    except AccountRecoveryError as exc:
        s.rollback()
        raise _account_recovery_http_exception(exc) from exc
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


@app.post("/api/client/recovery/exchange")
async def client_recovery_exchange(
    payload: RecoveryCodeExchangeIn,
    request: Request,
) -> dict[str, Any]:
    code_fingerprint = hashlib.sha256(str(payload.code or "").strip().upper().encode("utf-8")).hexdigest()[:32]
    _enforce_beta_rate_limit("recovery_exchange_ip", request)
    _enforce_beta_rate_limit(
        "recovery_exchange",
        request,
        identity=f"code_sha256:{code_fingerprint}",
    )
    install_fingerprint = hashlib.sha256(str(payload.install_id).strip().encode("utf-8")).hexdigest()[:32]
    _enforce_beta_rate_limit(
        "recovery_exchange_install",
        request,
        identity=f"install_sha256:{install_fingerprint}",
    )
    now = _utcnow()
    s = SessionLocal()
    try:
        exchange = exchange_recovery_code(
            s,
            code=payload.code,
            install_id=payload.install_id,
            device_name=payload.device_name,
            platform=payload.platform,
            os_version=payload.os_version,
            app_version=payload.app_version,
            locale=payload.locale,
            time_zone=payload.time_zone,
            now=now,
        )
        session_payload = exchange.session.response_payload(now=now)
        session_payload["scope"] = "recovery"
        response_payload = {
            "ok": True,
            "access_token": exchange.session.access_token,
            "refresh_token": exchange.session.refresh_token,
            "token_type": "Bearer",
            "expires_in": session_payload["expires_in"],
            "refresh_expires_in": session_payload["refresh_expires_in"],
            "session": session_payload,
            "allowed_actions": ["status", "support", "reissue", "device_revoke"],
        }
        s.commit()
        return response_payload
    except AccountRecoveryError as exc:
        s.rollback()
        raise _account_recovery_http_exception(exc) from exc
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


@app.post("/api/client/access/reissue")
async def client_access_reissue(
    payload: AccessReissueIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    account_id = str(auth_user.get("account_id") or "").strip()
    session_id = str(auth_user.get("session_id") or "").strip()
    if not account_id or not session_id:
        raise _auth_http_exception(
            detail="Нужна ограниченная recovery-сессия.",
            code="recovery_session_invalid",
            status_code=401,
        )
    session_fingerprint = hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:32]
    _enforce_beta_rate_limit(
        "access_reissue",
        request,
        identity=f"session_sha256:{session_fingerprint}",
    )
    now = _utcnow()
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == int(auth_user.get("id") or 0)).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        result = complete_access_reissue(
            s,
            account_id=account_id,
            recovery_session_id=session_id,
            mode=payload.mode,
            device_limit=_plan_device_limit(user),
            now=now,
        )
        session_payload = result.session.response_payload(now=now)
        session_payload["scope"] = "client"
        response_payload = {
            "ok": True,
            "mode": result.mode,
            "access_token": result.session.access_token,
            "refresh_token": result.session.refresh_token,
            "token_type": "Bearer",
            "expires_in": session_payload["expires_in"],
            "refresh_expires_in": session_payload["refresh_expires_in"],
            "session": session_payload,
            "provisioning_status": result.provisioning_status,
            "queued_key_rotations": len(result.provisioning_job_ids),
            "revoked_devices": int(result.revoked_devices),
        }
        s.commit()
        return response_payload
    except AccountRecoveryError as exc:
        s.rollback()
        raise _account_recovery_http_exception(exc) from exc
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def _route_policy_payload(user: User | None) -> dict[str, Any]:
    return {
        "ok": True,
        **app_first_service.resolve_route_policy(user),
    }


@app.get("/api/client/route-policy")
async def client_route_policy(
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return _route_policy_payload(user)
    finally:
        s.close()


@app.post("/api/client/route-policy")
async def client_update_route_policy(
    payload: ClientRoutePolicyIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        try:
            app_first_service.persist_route_policy(
                user,
                route_mode=payload.route_mode,
                selected_apps=list(payload.selected_apps or []),
                requires_elevated_privileges=payload.requires_elevated_privileges,
            )
        except app_first_service.RoutePolicyValidationError as exc:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": exc.code,
                    "message": "Select at least one app before using selected-apps routing.",
                },
            ) from exc
        s.commit()
        s.refresh(user)
        return _route_policy_payload(user)
    except HTTPException:
        s.rollback()
        raise
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


# Managed client feature/runtime routes register next through the ordered
# api_client_routes slice.
