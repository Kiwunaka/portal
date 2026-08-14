"""Public, authentication, client-session, runtime and payment routes.

Loaded by the api composition root in source order. Public symbols are
re-exported for backwards compatibility.
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

@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "ts": _utcnow().isoformat()}


@app.get("/api/public/authenticated-egress-probe", status_code=204)
async def authenticated_egress_probe_marker() -> Response:
    return Response(
        status_code=204,
        headers={
            "X-Pokrov-Egress-Probe": "pokrov-authenticated-egress-v1",
            "Cache-Control": "no-store",
        },
    )


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
        response.headers["Cache-Control"] = "public, max-age=120"
        return {"plans": plans, "widget_enabled": bool(CHECKOUT_WIDGET_ENABLED)}
    finally:
        s.close()


@app.get("/api/public/catalog")
async def public_catalog(response: Response) -> dict:
    s = SessionLocal()
    try:
        response.headers["Cache-Control"] = "public, max-age=120"
        return _public_catalog_payload(s=s)
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
        existing_device = s.query(AccountDevice.id).filter(AccountDevice.install_id == install_id).first()
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
        existing_app_account = s.query(User.tg_id).filter(User.app_install_id == install_id).first()
        if not existing_app_account:
            _enforce_beta_rate_limit("start_trial", request)
        user, created = app_first_service.upsert_app_trial_user(
            s=s,
            payload=payload,
            now=session_now,
            trial_days=APP_TRIAL_DEFAULT_DAYS,
            request_client_ip=client_ip,
        )
        account_device = s.query(AccountDevice).filter(AccountDevice.install_id == install_id).one()
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
        trial_projection = read_trial_projection(s, account_id=str(user.account_id), now=session_now)
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

    sync_ok = False
    panel = ControlPanel()
    try:
        sync_ok = bool(
            await panel.add_client(
                user_uuid=str(user.uuid),
                email=str(user.email),
                sub_type=str(user.sub_type or "FREE"),
                total_gb=int(user.total_gb or 0),
                tg_id=int(user.tg_id),
                sub_token=str(user.sub_token or ""),
            )
        )
        if not sync_ok:
            logger.warning(
                "app start-trial panel sync returned false tg_id=%s plan=%s sub_type=%s",
                int(user.tg_id),
                str(getattr(user, "current_plan_code", "") or ""),
                str(getattr(user, "sub_type", "") or ""),
            )
    except Exception as exc:
        logger.exception(
            "app start-trial panel sync failed tg_id=%s plan=%s sub_type=%s err=%s",
            int(user.tg_id),
            str(getattr(user, "current_plan_code", "") or ""),
            str(getattr(user, "sub_type", "") or ""),
            exc,
        )
        sync_ok = False
    finally:
        await panel.close()

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
        payload_user = payload_s.query(User).filter(User.tg_id == int(user.tg_id)).first() or user
        payload_nodes = _nodes_for_user(payload_user, enabled_nodes(payload_s), session=payload_s)
        promo_slots = _promo_slots_payload_for_surface(
            s=payload_s,
            surface="app",
            access_state=str(start_trial_parts["access"].get("access_state") or ""),
        )
        linked_identities = _linked_identities_payload(s=payload_s, user=payload_user)
    finally:
        payload_s.close()

    credential_now = _utcnow()
    session_s = SessionLocal()
    try:
        session_user = session_s.query(User).filter(User.tg_id == int(user.tg_id)).first()
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
            "free_caps": _free_caps_payload(user=user, access_policy=start_trial_parts["access"]),
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


SMART_CONNECT_LATENCY_EVENT_NAME = "smart_connect_latency_sample"


class NodeLatencyPointIn(BaseModel):
    node_code: str = Field(min_length=2, max_length=32)
    rtt_ms: int = Field(ge=1, le=60_000)


class NodeLatencySamplesIn(BaseModel):
    profile_revision: str | None = Field(default=None, max_length=128)
    transport_profile: str | None = Field(default=None, max_length=64)
    selected_node_code: str | None = Field(default=None, max_length=32)
    previous_node_code: str | None = Field(default=None, max_length=32)
    stickiness_applied: bool = False
    samples: list[NodeLatencyPointIn] = Field(default_factory=list, max_length=10)


class NodeSelectIn(BaseModel):
    mode: str = Field(default="auto", max_length=16)
    profile_revision: str | None = Field(default=None, max_length=128)
    transport_profile: str | None = Field(default=None, max_length=64)
    selected_node_code: str | None = Field(default=None, max_length=32)
    previous_node_code: str | None = Field(default=None, max_length=32)
    samples: list[NodeLatencyPointIn] = Field(default_factory=list, max_length=16)


class ClientRuntimeStatsIn(BaseModel):
    profile_revision: str | None = Field(default=None, max_length=128)
    selected_node_code: str | None = Field(default=None, max_length=32)
    runtime_phase: str | None = Field(default=None, max_length=32)
    connected: bool | None = None
    uptime_seconds: int | None = Field(default=None, ge=0, le=31_536_000)
    rtt_ms: int | None = Field(default=None, ge=0, le=60_000)
    rx_mbps: float | None = Field(default=None, ge=0)
    tx_mbps: float | None = Field(default=None, ge=0)
    error_code: str | None = Field(default=None, max_length=64)


class AccountOnboardingStatusIn(BaseModel):
    status: str = Field(min_length=7, max_length=9)


class InternalNodeMetricsIn(BaseModel):
    sampled_at: datetime | None = None
    source: str = Field(default="node_agent", max_length=64)
    batch_id: str | None = Field(default=None, max_length=128)
    provisioned_clients_count: int | None = Field(default=None, ge=0)
    online_connections_hint: int | None = Field(default=None, ge=0)
    network_rx_mbps_1m: float | None = Field(default=None, ge=0)
    network_tx_mbps_1m: float | None = Field(default=None, ge=0)
    network_rx_mbps_5m: float | None = Field(default=None, ge=0)
    network_tx_mbps_5m: float | None = Field(default=None, ge=0)
    network_total_mbps: float | None = Field(default=None, ge=0)
    cpu_percent: float | None = Field(default=None, ge=0, le=100)
    memory_used_mb: int | None = Field(default=None, ge=0)
    memory_total_mb: int | None = Field(default=None, ge=0)
    tcp_retrans_percent: float | None = Field(default=None, ge=0)
    packet_loss_percent: float | None = Field(default=None, ge=0)
    dataplane_ok: bool | None = None
    dataplane_rtt_ms: int | None = Field(default=None, ge=0, le=60_000)
    meta: dict[str, Any] | None = None


def _node_capacity_policy_by_code(session) -> dict[str, Any]:
    try:
        rows = session.query(NodeCapacityPolicy).filter(NodeCapacityPolicy.is_enabled == True).all()
    except Exception:
        return {}
    return {
        str(getattr(row, "node_code", "") or "").strip().lower(): row
        for row in rows
        if str(getattr(row, "node_code", "") or "").strip()
    }


def _nodes_by_code(nodes: list[Any]) -> dict[str, Any]:
    return {
        str(getattr(node, "code", "") or "").strip().lower(): node
        for node in nodes
        if str(getattr(node, "code", "") or "").strip()
    }


def _smart_connect_latest_sample(session, *, user: User, install_id: str) -> dict[str, Any]:
    query = session.query(Event).filter(Event.tg_id == int(user.tg_id), Event.event_name == SMART_CONNECT_LATENCY_EVENT_NAME)
    if install_id:
        query = query.filter(Event.session_id == install_id)
    row = query.order_by(Event.created_at.desc(), Event.id.desc()).first()
    if not row:
        return {}
    try:
        payload = json.loads(str(getattr(row, "meta_json", "") or "{}"))
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    payload.setdefault("created_at", _safe_iso(getattr(row, "created_at", None)))
    return payload


def _smart_connect_rejection_reason(
    node: Any,
    *,
    transport_profile: str,
    rollout_config: dict[str, Any],
    now: datetime,
    capacity_policy: Any | None = None,
) -> str | None:
    if CAPACITY_AWARE_NODE_SELECTION:
        capacity_reason = node_hard_reject_reason(
            node,
            policy=capacity_policy,
            now=now,
            stale_after_seconds=SMART_CONNECT_STALE_AFTER_SECONDS,
        )
        if capacity_reason:
            return capacity_reason
    if not bool(getattr(node, "enabled", True)):
        return "disabled"
    if not bool(getattr(node, "accepting_new_clients", True)):
        return "not_accepting_new_clients"
    if bool(getattr(node, "is_draining", False)):
        return "draining"
    if not bool(getattr(node, "is_healthy", True)):
        return "unhealthy"
    if node_is_stale(node, now=now, stale_after_seconds=SMART_CONNECT_STALE_AFTER_SECONDS):
        return "stale"
    if AUTHENTICATED_EGRESS_ENFORCEMENT_ENABLED:
        if getattr(node, "authenticated_egress_ok", None) is not True:
            return (
                "authenticated_egress_failed"
                if getattr(node, "authenticated_egress_ok", None) is False
                else "authenticated_egress_unavailable"
            )
        authenticated_at = getattr(node, "last_authenticated_egress_at", None)
        if not isinstance(authenticated_at, datetime):
            return "authenticated_egress_unavailable"
        if authenticated_at.tzinfo is not None and authenticated_at.utcoffset() is not None:
            authenticated_at = authenticated_at.astimezone(timezone.utc).replace(tzinfo=None)
        if (now - authenticated_at).total_seconds() > SMART_CONNECT_STALE_AFTER_SECONDS:
            return "authenticated_egress_stale"
    if node_cpu_penalty(node) is None:
        return "cpu_hot"
    is_ru_bridge_relay = str(transport_profile or "").strip() == RU_BRIDGE_RELAY
    required_transport = LEGACY_REALITY_FALLBACK if is_ru_bridge_relay else transport_profile
    if not _node_supports_transport_profile(node, required_transport):
        return "transport_mismatch"
    filtered = _filter_nodes_for_transport_profile(
        nodes=[node],
        rollout_config=rollout_config,
        transport_profile=transport_profile,
        apply_exclusions=not is_ru_bridge_relay,
    )
    if not filtered:
        return "transport_allowlist_mismatch"
    return None


def _smart_connect_shortlist(
    *,
    session,
    user: User,
    nodes: list[Any],
    transport_profile: str,
    rollout_config: dict[str, Any],
    profile_revision: str,
    preferred_node_code: str = "",
) -> dict[str, Any]:
    now = _utcnow()
    policy_by_code = _node_capacity_policy_by_code(session)
    rejected_counts: dict[str, int] = {}
    eligible: list[Any] = []
    for node in nodes:
        code = str(getattr(node, "code", "") or "").strip().lower()
        reason = _smart_connect_rejection_reason(
            node,
            transport_profile=transport_profile,
            rollout_config=rollout_config,
            now=now,
            capacity_policy=policy_by_code.get(code),
        )
        if reason:
            rejected_counts[reason] = int(rejected_counts.get(reason, 0) or 0) + 1
            continue
        eligible.append(node)

    eligible = rank_nodes_for_app(eligible, policy_by_code=policy_by_code, now=now)
    requested_preferred_code = str(preferred_node_code or "").strip().lower()
    if requested_preferred_code:
        eligible = sorted(
            eligible,
            key=lambda node: (
                0
                if str(getattr(node, "code", "") or "").strip().lower()
                == requested_preferred_code
                else 1
            ),
        )
    shortlist_limit = 1 if user_uses_free_pool(user) else SMART_CONNECT_SHORTLIST_LIMIT
    shortlist_nodes = eligible[:shortlist_limit]
    shortlist_codes = [str(getattr(node, "code", "") or "").strip().lower() for node in shortlist_nodes]
    install_id = str(getattr(user, "app_install_id", "") or "").strip()
    latest_sample = _smart_connect_latest_sample(session, user=user, install_id=install_id)
    preferred_node_code = str(latest_sample.get("selected_node_code") or "").strip().lower() or None
    if preferred_node_code and preferred_node_code not in shortlist_codes:
        preferred_node_code = None

    shortlist_payload = []
    for index, node in enumerate(shortlist_nodes, start=1):
        code = str(getattr(node, "code", "") or "").strip().lower()
        transport = _node_transport_profile(node, transport_profile)
        capacity = node_capacity_status(node, policy=policy_by_code.get(code), now=now)
        probe_host = str(transport.get("host") or getattr(node, "host", "") or "").strip()
        probe_port = int(transport.get("port") or getattr(node, "vless_port", 443) or 443)
        probe_payload = {"host": probe_host, "port": probe_port} if probe_host and probe_port > 0 else None
        shortlist_payload.append(
            {
                "code": code,
                "country": _node_country_name(code),
                "outbound_tag": _node_label_ru(code, str(getattr(node, "name", "") or "")),
                "rank": index,
                "probe": probe_payload,
                "rank_hint": {
                    "health_score": float(getattr(node, "health_score", 0.0) or 0.0),
                    "cpu_percent": float(getattr(node, "cpu_percent", 0.0) or 0.0),
                    "panel_latency_ms": _safe_ping(node),
                    "backend_penalty": int(node_backend_penalty(node) or 0),
                    "cpu_penalty": int(node_cpu_penalty(node) or 0),
                    "capacity_state": str(capacity.get("state") or "unknown"),
                    "capacity_score": float(capacity.get("score") or 0.0),
                    "tx_ratio": capacity.get("tx_ratio"),
                    "tx_mbps": capacity.get("tx_mbps"),
                    "provisioned_clients_count": int(capacity.get("provisioned_clients_count") or 0),
                    "online_connections_hint": int(capacity.get("online_connections_hint") or 0),
                    "sticky_preferred": bool(preferred_node_code and preferred_node_code == code),
                },
            }
        )

    revision_seed = "|".join(
        [
            str(profile_revision or "").strip(),
            str(transport_profile or "").strip(),
            *(item["code"] for item in shortlist_payload),
        ]
    )
    shortlist_revision = hashlib.sha256(revision_seed.encode("utf-8")).hexdigest()[:12] if revision_seed else ""
    return {
        "eligible": bool(shortlist_payload),
        "fallback_required": not bool(shortlist_payload),
        "shortlist_reason": "eligible" if shortlist_payload else "no_eligible_nodes",
        "shortlist_limit": int(shortlist_limit),
        "shortlist_revision": shortlist_revision,
        "transport_profile": str(transport_profile or ""),
        "profile_revision": str(profile_revision or ""),
        "fallback_order": _managed_manifest_fallback_order(transport_profile),
        "shortlist": shortlist_payload,
        "stickiness": {
            "preferred_node_code": preferred_node_code,
            "threshold_percent": int(SMART_CONNECT_STICKINESS_THRESHOLD_PERCENT),
            "latest_sample_at": latest_sample.get("created_at"),
            "stickiness_applied": bool(latest_sample.get("stickiness_applied", False)),
        },
        "scoring": {
            "formula": "effective_score = rtt_ms + dataplane_rtt + cpu_penalty + backend_penalty + network_pressure",
            "cpu_penalty_buckets": [
                {"range": "<60", "penalty": 0},
                {"range": "60-74", "penalty": 20},
                {"range": "75-84", "penalty": 60},
                {"range": "85-89", "penalty": 120},
                {"range": ">=90", "penalty": "reject"},
            ],
            "backend_penalty_buckets": [
                {"range": ">=90", "penalty": 0},
                {"range": "75-89", "penalty": 30},
                {"range": "60-74", "penalty": 80},
                {"range": "<60", "penalty": 160},
            ],
            "stickiness_threshold_percent": int(SMART_CONNECT_STICKINESS_THRESHOLD_PERCENT),
        },
        "rejected_counts": rejected_counts,
    }


def _client_user_session(request: Request, x_telegram_init_data: str) -> tuple[Any, User, dict[str, Any]]:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        _maybe_downgrade_expired_to_free(s, user)
        _ensure_free_cycle_state_persisted(s, user)
        return s, user, auth_user
    except Exception:
        s.close()
        raise


def _client_event_meta(value: dict[str, Any] | None) -> str:
    return json.dumps(dict(value or {}), ensure_ascii=False, separators=(",", ":"))[:4000]


def _record_client_event(
    s,
    *,
    user: User,
    event_name: str,
    source: str = "app",
    session_id: str | None = None,
    meta: dict[str, Any] | None = None,
) -> None:
    s.add(
        Event(
            tg_id=int(user.tg_id),
            event_name=str(event_name or "").strip()[:64],
            source=str(source or "app").strip()[:32] or "app",
            session_id=(str(session_id or getattr(user, "app_install_id", "") or "").strip()[:64] or None),
            meta_json=_client_event_meta(meta),
            created_at=_utcnow(),
        )
    )


def _node_country_code(code: str) -> str:
    base = _node_code_base(code)
    if base == "brain":
        return "de"
    return base or "xx"


def _node_city_name(code: str, fallback_name: str = "") -> str:
    raw = str(code or "").strip().lower()
    parts = [part for part in re.split(r"[-_.]+", raw) if part]
    city_key = parts[1] if len(parts) > 1 and parts[1] != "free" else parts[0] if parts else ""
    cities = {
        "ams": "Amsterdam",
        "nl": "Amsterdam",
        "fra": "Frankfurt",
        "de": "Frankfurt",
        "hel": "Helsinki",
        "fi": "Helsinki",
        "waw": "Warsaw",
        "pl": "Warsaw",
        "lon": "London",
        "gb": "London",
        "uk": "London",
        "nyc": "New York",
        "us": "New York",
        "mil": "Milan",
        "it": "Milan",
        "par": "Paris",
        "fr": "Paris",
        "ru": "Moscow",
    }
    if "free" in raw:
        return cities.get(_node_country_code(raw), "Free node")
    if city_key in cities:
        return cities[city_key]
    cleaned = str(fallback_name or raw or "Node").strip()
    return cleaned[:1].upper() + cleaned[1:] if cleaned else "Node"


def _node_health_ratio(node: Any) -> float:
    try:
        raw = float(getattr(node, "health_score", 0.0) or 0.0)
    except Exception:
        raw = 0.0
    if raw > 1:
        raw = raw / 100.0
    return round(max(0.0, min(raw, 1.0)), 3)


def _node_load_ratio(node: Any) -> float:
    try:
        raw = float(getattr(node, "cpu_percent", 0.0) or 0.0) / 100.0
    except Exception:
        raw = 0.0
    return round(max(0.0, min(raw, 1.0)), 3)


def _node_client_latency_ms(node: Any) -> int | None:
    """Prefer dataplane RTT; panel login latency is only a fallback."""
    for attribute in ("dataplane_rtt_ms", "panel_latency_ms"):
        raw = getattr(node, attribute, None)
        try:
            value = int(raw) if raw is not None else None
        except (TypeError, ValueError):
            value = None
        if value is not None and value >= 0:
            return value
    return None


def _node_matches_query(*, node: Any, country: str, city: str, query: str) -> bool:
    q = str(query or "").strip().lower()
    if not q:
        return True
    haystack = " ".join(
        [
            str(getattr(node, "code", "") or ""),
            str(getattr(node, "name", "") or ""),
            country,
            city,
        ]
    ).lower()
    return q in haystack


def _client_subscription_lane(access_state: str) -> str:
    mapping = {
        "trial_premium": "trialPremium",
        "bonus_premium": "bonusPremium",
        "paid_unlimited": "paidUnlimited",
        "free_monthly": "freeMonthly",
        "free_soft_mode": "freeSoftMode",
    }
    return mapping.get(str(access_state or "").strip().lower(), "expiredOrBlocked")


def _client_days_left(expiry: datetime | None, *, now: datetime | None = None) -> int:
    if not expiry:
        return 0
    current = now or _utcnow()
    seconds = (expiry - current).total_seconds()
    if seconds <= 0:
        return 0
    return int((seconds + 86399) // 86400)


def _client_subscription_plans(s) -> list[dict[str, Any]]:
    plans: list[dict[str, Any]] = []
    for plan in _plan_catalog_payload(s=s, only_active=True):
        code = str(plan.get("code") or "").strip().lower()
        if not code or code == "trial":
            continue
        amount_rub = int(plan.get("amount_rub") or 0)
        days = max(1, int(plan.get("days") or 30))
        title = str(plan.get("label") or "").strip() or (f"{days} days" if days != 30 else "1 month")
        price = f"{amount_rub} ₽" if amount_rub > 0 else ""
        plans.append(
            {
                "id": code,
                "title": title,
                "price": price,
                "days": days,
                "deviceLimit": max(1, int(plan.get("device_limit") or 1)),
                "badge": str(plan.get("badge") or "").strip() or None,
            }
        )
    return plans


def _client_notification_read_ids(s, *, user: User) -> set[str]:
    rows = (
        s.query(Event)
        .filter(Event.tg_id == int(user.tg_id))
        .filter(Event.event_name == "client_notification_read")
        .order_by(Event.created_at.desc(), Event.id.desc())
        .limit(200)
        .all()
    )
    out: set[str] = set()
    for row in rows:
        try:
            payload = json.loads(str(row.meta_json or "{}"))
        except Exception:
            payload = {}
        for item in list((payload or {}).get("ids") or []):
            value = str(item or "").strip()
            if value:
                out.add(value)
    return out


def _client_notification_items(
    *,
    user: User,
    access_policy: dict[str, Any],
    read_ids: set[str],
    incidents: list[ServiceIncident] | None = None,
    live_updates: list[LiveUpdate] | None = None,
    compensation_grants: list[EntitlementGrant] | None = None,
    program_applications: list[ProgramApplication] | None = None,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    current_now = now or _utcnow()
    items: list[dict[str, Any]] = []
    for incident in list(incidents or [])[:10]:
        notification_id = f"incident.{incident.id}"
        items.append(
            {
                "id": notification_id,
                "kind": "incident",
                "title": str(incident.title or "Инцидент сервиса").strip(),
                "body": str(incident.summary or "Проверяем состояние сервиса.").strip(),
                "createdAt": _safe_iso(incident.started_at or incident.created_at or _utcnow()),
                "ctaLabel": "Статус защиты",
                "ctaHref": f"{_public_webapp_url().rstrip('/')}/protection/",
                "read": notification_id in read_ids,
            }
        )
    for grant in list(compensation_grants or [])[:10]:
        try:
            metadata = json.loads(str(grant.metadata_json or "{}"))
        except Exception:
            metadata = {}
        notification_id = f"compensation.{grant.id}"
        title = str((metadata or {}).get("incident_title") or "Компенсация за инцидент").strip()
        days = max(0, int(grant.duration_days or 0))
        items.append(
            {
                "id": notification_id,
                "kind": "compensation",
                "title": title,
                "body": f"Начислили {days} дн. после подтверждённого инцидента.",
                "createdAt": _safe_iso(grant.created_at or _utcnow()),
                "ctaLabel": "Открыть кабинет",
                "ctaHref": _public_webapp_url(),
                "read": notification_id in read_ids,
            }
        )
    for update in list(live_updates or [])[:10]:
        notification_id = f"release.{update.id}"
        update_href = _build_tg_post_link(
            channel_username=getattr(update, "channel_username", None),
            post_id=getattr(update, "post_id", None),
            fallback_link=str(update.link or "").strip(),
        )
        items.append(
            {
                "id": notification_id,
                "kind": "release",
                "title": str(update.title or "Обновление POKROV").strip(),
                "body": str(update.summary or "Доступно новое обновление.").strip(),
                "createdAt": _safe_iso(update.published_at or update.created_at or _utcnow()),
                "ctaLabel": "Подробнее",
                "ctaHref": update_href or None,
                "read": notification_id in read_ids,
            }
        )
    access_state = str(access_policy.get("access_state") or "").strip().lower()
    expiry_at = getattr(user, "expiry_at", None)
    access_kind = {
        "trial_premium": "trial",
        "bonus_premium": "bonus",
        "paid_unlimited": "paid",
    }.get(access_state)
    if not access_kind:
        plan_code = str(getattr(user, "current_plan_code", "") or "").strip().lower()
        sub_type = str(getattr(user, "sub_type", "") or "").strip().upper()
        if plan_code == "trial" or sub_type.startswith("TRIAL"):
            access_kind = "trial"
        elif plan_code in {"channel_bonus", "bonus"} or sub_type.startswith("BONUS"):
            access_kind = "bonus"
        elif expiry_at is not None:
            access_kind = "paid"
    access_stage = ""
    if expiry_at is not None and access_kind:
        delta = expiry_at - current_now
        if access_kind == "paid" and timedelta(days=2) < delta <= timedelta(days=3):
            access_stage = "t3"
        elif timedelta(hours=20) < delta <= timedelta(hours=28):
            access_stage = "t1"
        elif timedelta(hours=-1) <= delta <= timedelta(hours=1):
            access_stage = "t0"
    if access_stage and access_kind and expiry_at is not None:
        notification_id = f"access.{access_kind}.{access_stage}.{expiry_at.date().isoformat()}"
        if access_stage == "t3":
            title = "Доступ закончится через 3 дня"
            body = "Продлите заранее, если хотите сохранить подключение без паузы."
        elif access_stage == "t1":
            title = "Пробный период закончится завтра" if access_kind == "trial" else "До окончания доступа 1 день"
            body = "Выберите подходящий срок — автосписаний нет."
        elif expiry_at > current_now:
            title = "Доступ заканчивается сегодня"
            body = "Продлить можно в кабинете. Автосписаний нет."
        else:
            title = "Доступ закончился"
            body = "Выберите срок, чтобы снова подключить POKROV."
        items.append(
            {
                "id": notification_id,
                "kind": "access",
                "title": title,
                "body": body,
                "createdAt": _safe_iso(expiry_at),
                "ctaLabel": "Выбрать срок",
                "ctaHref": _public_webapp_url(),
                "read": notification_id in read_ids,
            }
        )
    program_titles = {
        "competitor_switch": "Переход от другого VPN",
        "research": "Исследование POKROV",
        "team_pack": "Набор для команды",
    }
    status_bodies = {
        "submitted": "Заявка принята и ждёт проверки.",
        "under_review": "Оператор проверяет заявку.",
        "approved": "Заявка одобрена. Детали доступны в кабинете.",
        "rejected": "Проверка завершена без начисления.",
        "rewarded": "Проверка завершена, подтверждённая награда начислена.",
        "cancelled": "Заявка отменена.",
    }
    for application in list(program_applications or [])[:10]:
        status = str(application.status or "submitted").strip().lower()
        notification_id = f"program.{application.id}.{status}"
        days = max(0, int(application.reward_days or 0))
        body = status_bodies.get(status, "Статус заявки изменился.")
        if status == "rewarded" and days:
            body = f"Проверка завершена: начислено {days} дн."
        items.append(
            {
                "id": notification_id,
                "kind": "program",
                "title": program_titles.get(str(application.kind or ""), "Заявка POKROV"),
                "body": body,
                "createdAt": _safe_iso(application.updated_at or application.created_at or _utcnow()),
                "ctaLabel": "Открыть заявки",
                "ctaHref": f"{_public_webapp_url().rstrip('/')}/programs/",
                "read": notification_id in read_ids,
            }
        )
    return sorted(
        items,
        key=lambda item: str(item.get("createdAt") or ""),
        reverse=True,
    )[:30]


ASSISTANT_DIAGNOSTIC_KEYS = frozenset(
    {
        "account_access_state",
        "account_days_left",
        "account_device_count",
        "account_plan",
        "account_telegram_linked",
        "app_version",
        "panel_active_connections",
        "panel_last_online_age_seconds",
        "panel_runtime_state",
        "platform",
        "route_mode",
        "connection_status",
        "enhanced_protection_state",
        "enhanced_protection_consent",
        "enhanced_protection_available",
        "telegram_bonus_state",
    }
)


def _admit_support_assistant_diagnostics(raw_value: Any) -> dict[str, str | int | bool | None]:
    if not isinstance(raw_value, dict) or len(raw_value) > 20:
        raise HTTPException(status_code=422, detail="Invalid safe diagnostics")
    admitted: dict[str, str | int | bool | None] = {}
    for key in ASSISTANT_DIAGNOSTIC_KEYS:
        if key not in raw_value:
            continue
        value = raw_value[key]
        if isinstance(value, str):
            if len(value) > 512 or any(ord(char) < 32 and char not in "\t\n\r" for char in value):
                raise HTTPException(status_code=422, detail="Invalid safe diagnostics")
            admitted[key] = value
        elif type(value) in {int, bool} or value is None:
            admitted[key] = value
        else:
            raise HTTPException(status_code=422, detail="Invalid safe diagnostics")
    serialized = json.dumps(admitted, ensure_ascii=False, separators=(",", ":"))
    if len(serialized) > 4096:
        raise HTTPException(status_code=422, detail="Invalid safe diagnostics")
    return admitted


async def _support_assistant_account_diagnostics(*, s, user: User) -> dict[str, str | int | bool | None]:
    """Return a same-account, identifier-free snapshot for the support agent."""
    runtime: dict[str, Any]
    try:
        nodes = enabled_nodes(s)
        nodes_for_user = _nodes_for_user(user, nodes, session=s)
        runtime = await _get_user_runtime_summary(s=s, user=user, nodes=nodes_for_user)
    except Exception:
        logger.warning("support assistant account snapshot panel lookup failed")
        runtime = {"panel_state": "error", "status": "unknown", "traffic_total_bytes": 0}

    access_policy = _build_reconciled_access_policy(
        session=s,
        user=user,
        used_bytes=int(runtime.get("traffic_total_bytes", 0) or 0),
        source="support_assistant_runtime",
    )
    access_state = str(access_policy.get("access_state") or "expired_or_blocked").strip().lower()
    days_left = _client_days_left(getattr(user, "expiry_at", None))
    if access_state == "trial_premium":
        days_left = min(days_left, int(APP_TRIAL_DEFAULT_DAYS))

    plan_code = re.sub(
        r"[^a-z0-9_.:-]+",
        "_",
        str(getattr(user, "current_plan_code", "") or "").strip().lower(),
    )[:64]
    account_id = str(getattr(user, "account_id", "") or "").strip()
    device_count = 0
    if account_id:
        device_count = int(
            s.query(func.count(AccountDevice.id))
            .filter(
                AccountDevice.account_id == account_id,
                AccountDevice.state == "active",
                AccountDevice.revoked_at.is_(None),
            )
            .scalar()
            or 0
        )

    linked_telegram_id = _linked_telegram_id(user)
    telegram_linked = bool(
        linked_telegram_id
        or (not _is_app_or_email_account(user) and int(getattr(user, "tg_id", 0) or 0) > 0)
    )
    channel_status = channel_bonus_service.channel_bonus_status(s, user=user)
    if bool(channel_status.get("claimed")):
        telegram_bonus_state = "claimed"
    elif not bool(getattr(user, "tos_accepted", False)):
        telegram_bonus_state = "tos_required"
    elif str(getattr(user, "sub_type", "") or "").strip().upper() == "MANUAL":
        telegram_bonus_state = "unavailable"
    else:
        telegram_bonus_state = "available"

    panel_state = str(runtime.get("panel_state") or "error").strip().lower()
    panel_runtime_state = (
        str(runtime.get("status") or "unknown").strip().lower()
        if panel_state == "ok"
        else "unavailable"
    )
    last_online_age = runtime.get("last_online_age_seconds")
    return {
        "account_access_state": access_state,
        "account_days_left": max(0, int(days_left)),
        "account_device_count": max(0, device_count),
        "account_plan": plan_code or None,
        "account_telegram_linked": telegram_linked,
        "panel_active_connections": max(0, int(runtime.get("active_connections", 0) or 0)),
        "panel_last_online_age_seconds": (
            max(0, int(last_online_age)) if last_online_age is not None else None
        ),
        "panel_runtime_state": panel_runtime_state,
        "telegram_bonus_state": telegram_bonus_state,
    }


def _client_location_variants(
    *,
    node: Any,
    rollout_config: dict[str, Any],
    transport_profile: str,
) -> list[dict[str, str]]:
    variants = [
        {
            "id": "direct",
            "label": "Обычный",
            "description": "Прямое подключение",
        }
    ]
    seen_ids = {"direct"}
    for endpoint in _ru_bridge_endpoints_for_node(
        node=node,
        rollout_config=rollout_config,
        transport_profile=transport_profile,
    ):
        endpoint_id = str(endpoint.get("id") or "").strip().lower()
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,63}", endpoint_id) or endpoint_id in seen_ids:
            continue
        label = " ".join(str(endpoint.get("label") or "Белые списки").split())[:48].strip()
        if not label:
            label = "Белые списки"
        variants.append(
            {
                "id": endpoint_id,
                "label": label,
                "description": "Для ограниченных сетей",
            }
        )
        seen_ids.add(endpoint_id)
    return variants


@app.get("/api/client/locations")
async def client_locations_catalog(
    request: Request,
    platform: str = Query(default="", max_length=32),
    q: str = Query(default="", max_length=80),
    x_telegram_init_data: str = Header(default=""),
    x_portal_carrier: str = Header(default=""),
) -> dict[str, Any]:
    del platform
    s, user, _auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        rollout_config = load_network_rollout_config(session=s)
        install_id = str(getattr(user, "app_install_id", "") or "").strip() or None
        client_policy = app_first_service.build_client_policy(
            session=s,
            user=user,
            install_id=install_id,
            carrier=_request_carrier_header(x_portal_carrier),
            rollout_config=rollout_config,
        )
        transport_profile = str(client_policy.get("transport_profile") or LEGACY_REALITY_FALLBACK).strip() or LEGACY_REALITY_FALLBACK
        all_nodes = enabled_nodes(s)
        free_pool_code = canonical_free_node_code(all_nodes, access_role=user_free_access_role(user))
        nodes_for_user = _nodes_for_user(user, all_nodes, session=s)
        smart_connect = _smart_connect_shortlist(
            session=s,
            user=user,
            nodes=nodes_for_user,
            transport_profile=transport_profile,
            rollout_config=rollout_config,
            profile_revision=str(client_policy.get("profile_revision") or ""),
        )

        grouped: dict[str, dict[str, Any]] = {}
        now = _utcnow()
        query = str(q or "").strip().lower()
        for node in nodes_for_user:
            reason = _smart_connect_rejection_reason(
                node,
                transport_profile=transport_profile,
                rollout_config=rollout_config,
                now=now,
            )
            if reason:
                continue
            code = str(getattr(node, "code", "") or "").strip().lower()
            if not code:
                continue
            country_code = _node_country_code(code)
            country = _node_country_name(code)
            city = _node_city_name(code, str(getattr(node, "name", "") or ""))
            if not _node_matches_query(node=node, country=country, city=city, query=query):
                continue
            transport = _node_transport_profile(node, transport_profile)
            probe_host = str(transport.get("host") or getattr(node, "host", "") or "").strip()
            probe_port = int(transport.get("port") or getattr(node, "vless_port", 443) or 443)
            city_row = {
                "code": code,
                "city": city,
                "country": country,
                "countryCode": country_code,
                "healthScore": _node_health_ratio(node),
                "latencyMs": _node_client_latency_ms(node),
                "latencySource": "brain",
                "premium": not node_is_free(node),
                "load": _node_load_ratio(node),
                "measuredAt": _safe_iso(getattr(node, "last_health_at", None)),
                "variants": _client_location_variants(
                    node=node,
                    rollout_config=rollout_config,
                    transport_profile=transport_profile,
                ),
                "probe": (
                    {"host": probe_host, "port": probe_port}
                    if probe_host and 0 < probe_port <= 65535
                    else None
                ),
            }
            bucket = grouped.setdefault(
                country_code,
                {"code": country_code, "country": country, "cities": []},
            )
            bucket["cities"].append(city_row)

        countries = list(grouped.values())
        for country in countries:
            country["cities"].sort(key=lambda item: (item.get("premium") is False, item.get("latencyMs") or 999999, item.get("city") or ""))
        countries.sort(key=lambda item: str(item.get("country") or ""))
        all_codes = [city["code"] for country in countries for city in country["cities"]]
        preferred_code = str((smart_connect.get("stickiness") or {}).get("preferred_node_code") or "").strip().lower()
        current_code = preferred_code if preferred_code in all_codes else (all_codes[0] if all_codes else None)
        return {
            "auto": {
                "enabled": bool(smart_connect.get("eligible")),
                "currentCode": current_code,
            },
            "countries": countries,
            "freePoolCode": str(free_pool_code or "").strip().lower() or None,
            "query": query,
            "search": {
                "matched": len(all_codes),
                "source": "nodes",
                "interactive": True,
            },
            "profileRevision": str(client_policy.get("profile_revision") or ""),
            "transportProfile": transport_profile,
        }
    finally:
        s.close()


@app.get("/api/client/subscription")
async def client_subscription(request: Request, x_telegram_init_data: str = Header(default="")) -> dict[str, Any]:
    s, user, _auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        nodes = enabled_nodes(s)
        nodes_for_user = _nodes_for_user(user, nodes, session=s)
        runtime = await _get_user_runtime_summary(s=s, user=user, nodes=nodes_for_user)
        access_policy = _build_reconciled_access_policy(
            session=s,
            user=user,
            used_bytes=int(runtime.get("traffic_total_bytes", 0) or 0),
            source="client_subscription_runtime",
        )
        access_state = str(access_policy.get("access_state") or "")
        expiry = getattr(user, "expiry_at", None)
        days_left = _client_days_left(expiry)
        if access_state == "trial_premium":
            days_left = min(days_left, int(APP_TRIAL_DEFAULT_DAYS))
        return {
            "lane": _client_subscription_lane(access_state),
            "accessState": access_state,
            "expiresAt": _safe_iso(expiry),
            "daysLeft": days_left,
            "autoRenew": False,
            "renewUrl": _checkout_url_for_user(tg_id=int(user.tg_id), source="app"),
            "plans": _client_subscription_plans(s),
            "trafficPolicy": dict(access_policy.get("traffic_policy") or {}),
            "usage": {
                "trafficUsedBytes": int(runtime.get("traffic_total_bytes", 0) or 0),
                "activeConnections": int(runtime.get("active_connections", 0) or 0),
                "lastOnlineAt": runtime.get("last_online_at"),
                "source": (
                    "panel_runtime"
                    if runtime.get("panel_state") == "ok"
                    else "unavailable"
                ),
            },
            "currentPlanCode": str(getattr(user, "current_plan_code", "") or "").strip() or None,
        }
    finally:
        s.close()


def _device_pairing_http_error(exc: device_pairing_service.DevicePairingError) -> HTTPException:
    status_by_code = {
        "pairing_not_configured": 503,
        "pairing_not_found": 404,
        "pairing_code_invalid": 400,
        "pairing_code_expired": 410,
        "pairing_code_used": 409,
        "device_invalid": 400,
        "device_already_registered": 409,
        "device_identity_conflict": 409,
        "device_limit_reached": 409,
        "account_not_found": 409,
    }
    message_by_code = {
        "pairing_not_configured": "Привязка устройств пока не настроена.",
        "pairing_not_found": "Код привязки не найден.",
        "pairing_code_invalid": "Код не подошёл. Проверьте восемь символов.",
        "pairing_code_expired": "Код истёк. Создайте новый на уже связанном устройстве.",
        "pairing_code_used": "Этот код уже использован или отменён.",
        "device_invalid": "Не удалось определить новое устройство.",
        "device_already_registered": "Это устройство уже связано. Используйте восстановление доступа.",
        "device_identity_conflict": "Это устройство связано с другим аккаунтом.",
        "device_limit_reached": "Лимит устройств исчерпан. Сначала отвяжите старое устройство.",
        "account_not_found": "Аккаунт для привязки недоступен.",
    }
    code = str(exc.code or "pairing_failed")
    return HTTPException(
        status_code=int(status_by_code.get(code, 400)),
        detail={"code": code, "message": message_by_code.get(code, "Не удалось привязать устройство.")},
    )


@app.post("/api/client/device-pairing/codes")
async def client_device_pairing_issue(
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    s, user, auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        _enforce_beta_rate_limit("device_pairing_issue", request, identity=f"account:{user.account_id}")
        now = _utcnow()
        issued = device_pairing_service.issue_pairing_code(
            s,
            account_id=str(user.account_id or ""),
            issued_by_session_id=str(auth_user.get("session_id") or "") or None,
            now=now,
        )
        _record_client_event(
            s,
            user=user,
            event_name="device_pairing_code_issued",
            meta={"pairing_id": str(issued.row.id), "expires_at": _safe_iso(issued.row.expires_at)},
        )
        s.commit()
        manual_code = str(issued.code)
        return {
            "ok": True,
            "pairing": {
                **device_pairing_service.pairing_code_public_payload(issued.row),
                "code": manual_code,
                "pairing_uri": f"pokrov://pair?code={urlencode({'code': manual_code}).split('=', 1)[-1]}",
                "ttl_seconds": int((issued.row.expires_at - now).total_seconds()),
            },
        }
    except device_pairing_service.DevicePairingError as exc:
        s.rollback()
        raise _device_pairing_http_error(exc) from exc
    finally:
        s.close()


@app.get("/api/client/device-pairing/codes")
async def client_device_pairing_codes(
    request: Request,
    x_telegram_init_data: str = Header(default=""),
    limit: int = Query(default=10, ge=1, le=25),
) -> dict[str, Any]:
    s, user, _auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        rows = device_pairing_service.list_pairing_codes(
            s,
            account_id=str(user.account_id or ""),
            now=_utcnow(),
            limit=limit,
        )
        s.commit()
        return {"ok": True, "items": [device_pairing_service.pairing_code_public_payload(row) for row in rows]}
    except device_pairing_service.DevicePairingError as exc:
        s.rollback()
        raise _device_pairing_http_error(exc) from exc
    finally:
        s.close()


@app.delete("/api/client/device-pairing/codes/{pairing_id}")
async def client_device_pairing_cancel(
    pairing_id: str,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    s, user, _auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        row = device_pairing_service.cancel_pairing_code(
            s,
            account_id=str(user.account_id or ""),
            pairing_id=pairing_id,
            now=_utcnow(),
        )
        s.commit()
        return {"ok": True, "pairing": device_pairing_service.pairing_code_public_payload(row)}
    except device_pairing_service.DevicePairingError as exc:
        s.rollback()
        raise _device_pairing_http_error(exc) from exc
    finally:
        s.close()


@app.post("/api/client/device-pairing/claim")
async def client_device_pairing_claim(payload: ClientDevicePairingClaimIn, request: Request) -> dict[str, Any]:
    code_fp = hashlib.sha256(str(payload.code or "").strip().upper().encode("utf-8")).hexdigest()[:24]
    install_fp = hashlib.sha256(str(payload.install_id or "").strip().encode("utf-8")).hexdigest()[:24]
    _enforce_beta_rate_limit("device_pairing_claim_ip", request)
    _enforce_beta_rate_limit("device_pairing_claim", request, identity=f"{code_fp}:{install_fp}")
    now = _utcnow()
    s = SessionLocal()
    try:
        claimed = device_pairing_service.claim_pairing_code(
            s,
            code=payload.code,
            install_id=payload.install_id,
            device_name=payload.device_name,
            platform=payload.platform,
            os_version=payload.os_version,
            app_version=payload.app_version,
            locale=payload.locale,
            time_zone=payload.time_zone,
            device_limit_resolver=_plan_device_limit,
            now=now,
        )
        owner = (
            s.query(User)
            .filter(User.account_id == str(claimed.row.account_id))
            .order_by(User.tg_id.asc())
            .first()
        )
        if owner is not None:
            _record_client_event(
                s,
                user=owner,
                event_name="device_pairing_claimed",
                session_id=str(payload.install_id),
                meta={"pairing_id": str(claimed.row.id), "platform": str(payload.platform)},
            )
        session_payload = claimed.session.response_payload(now=now)
        session_payload["scope"] = "client"
        s.commit()
        return {
            "ok": True,
            "token": claimed.session.access_token,
            "session_token": claimed.session.access_token,
            "access_token": claimed.session.access_token,
            "refresh_token": claimed.session.refresh_token,
            "token_type": "Bearer",
            "expires_in": session_payload["expires_in"],
            "refresh_expires_in": session_payload["refresh_expires_in"],
            "canonical_account_id": claimed.session.account_id,
            "session": session_payload,
        }
    except device_pairing_service.DevicePairingError as exc:
        s.rollback()
        raise _device_pairing_http_error(exc) from exc
    finally:
        s.close()


@app.get("/api/client/programs")
async def client_programs(request: Request, x_telegram_init_data: str = Header(default="")) -> dict[str, Any]:
    s, user, _auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        rows = program_application_service.list_account_applications(
            s,
            account_id=str(user.account_id or ""),
        )
        return {
            "ok": True,
            "capabilities": _public_program_capabilities(),
            "applications": [program_application_service.application_payload(row) for row in rows],
        }
    finally:
        s.close()


@app.post("/api/client/programs/applications")
async def client_program_application_create(
    payload: ProgramApplicationCreateIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    s, user, _auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        _enforce_beta_rate_limit("program_application", request, identity=f"account:{user.account_id}")
        row = program_application_service.submit_application(
            s,
            user=user,
            kind=payload.kind,
            source_name=payload.source_name,
            seats=payload.seats,
            summary=payload.summary,
            contact=payload.contact,
            now=_utcnow(),
        )
        _record_client_event(
            s,
            user=user,
            event_name="program_application_submitted",
            meta={"application_id": str(row.id), "kind": str(row.kind)},
        )
        s.commit()
        return {"ok": True, "application": program_application_service.application_payload(row)}
    except program_application_service.ProgramApplicationError as exc:
        s.rollback()
        status = 409 if exc.code == "program_application_pending" else 400
        raise HTTPException(status_code=status, detail={"code": exc.code, "message": exc.message}) from exc
    finally:
        s.close()


@app.delete("/api/client/programs/applications/{application_id}")
async def client_program_application_cancel(
    application_id: str,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    s, user, _auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        row = program_application_service.cancel_application(
            s,
            account_id=str(user.account_id or ""),
            application_id=application_id,
            now=_utcnow(),
        )
        s.commit()
        return {"ok": True, "application": program_application_service.application_payload(row)}
    except program_application_service.ProgramApplicationError as exc:
        s.rollback()
        raise HTTPException(status_code=404, detail={"code": exc.code, "message": exc.message}) from exc
    finally:
        s.close()


@app.patch("/api/client/devices/current")
async def client_device_metadata_update(
    payload: AppDeviceMetadataIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    s, user, auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        now = _utcnow()
        account_id = str(auth_user.get("account_id") or getattr(user, "account_id", "") or "").strip()
        current_registry_id = str(auth_user.get("device_id") or "").strip()
        current_install_id = str(getattr(user, "app_install_id", "") or "").strip()
        device = None
        if account_id and current_registry_id:
            device = (
                s.query(AccountDevice)
                .filter(
                    AccountDevice.account_id == account_id,
                    AccountDevice.id == current_registry_id,
                )
                .first()
            )
        if device is None and account_id and current_install_id:
            device = (
                s.query(AccountDevice)
                .filter(
                    AccountDevice.account_id == account_id,
                    AccountDevice.install_id == current_install_id,
                )
                .first()
            )

        label = app_first_service.normalize_app_device_name(payload.device_name)
        platform = str(payload.platform or "device").strip().lower()[:32] or "device"
        os_version = str(payload.os_version or "").strip()[:64] or None
        app_version = str(payload.app_version or "").strip()[:32] or None
        user.app_device_name = label
        user.app_platform = platform
        user.app_os_version = os_version
        user.app_version = app_version
        user.app_last_seen_at = now
        if device is not None:
            device.label = label
            device.platform = platform
            device.os_version = os_version
            device.app_version = app_version
            device.last_seen_at = now
        s.commit()
        return {"ok": True}
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


@app.get("/api/client/devices")
async def client_devices(request: Request, x_telegram_init_data: str = Header(default="")) -> dict[str, Any]:
    s, user, auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        rows = []
        account_id = str(getattr(user, "account_id", "") or "").strip()
        current_registry_id = str(auth_user.get("device_id") or "").strip()
        devices = (
            s.query(AccountDevice)
            .filter(AccountDevice.account_id == account_id)
            .order_by(AccountDevice.created_at.asc(), AccountDevice.id.asc())
            .all()
            if account_id
            else []
        )
        for device in devices:
            active = str(device.state or "").strip().lower() == "active" and device.revoked_at is None
            rows.append(
                {
                    "id": str(device.install_id),
                    "registryId": str(device.id),
                    "label": _normalize_app_device_name(device.label),
                    "platform": str(device.platform or "device"),
                    "osVersion": str(device.os_version or "").strip() or None,
                    "appVersion": str(device.app_version or "").strip() or None,
                    "lastSeen": _safe_iso(device.last_seen_at),
                    "current": bool(
                        str(device.id) == current_registry_id
                        if current_registry_id
                        else str(device.install_id) == str(getattr(user, "app_install_id", "") or "")
                    ),
                    "active": active,
                    "state": str(device.state or "active"),
                    "revokedAt": _safe_iso(device.revoked_at),
                }
            )
        if not rows:
            for item in _build_app_device_rows(user):
                rows.append(
                    {
                        "id": str(item.get("id") or ""),
                        "registryId": None,
                        "label": str(item.get("name") or "Current device"),
                        "platform": str(item.get("platform") or "device"),
                        "osVersion": item.get("os_version"),
                        "appVersion": item.get("app_version"),
                        "lastSeen": item.get("last_seen_at"),
                        "current": bool(item.get("is_current")),
                        "active": bool(item.get("is_active")),
                        "state": "legacy",
                        "revokedAt": None,
                    }
                )
        return {"items": rows, "limit": _plan_device_limit(user)}
    finally:
        s.close()


@app.delete("/api/client/devices/{device_id}")
async def client_device_revoke(device_id: str, request: Request, x_telegram_init_data: str = Header(default="")) -> dict[str, Any]:
    s, user, auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        target = str(device_id or "").strip()
        if not target:
            raise HTTPException(status_code=404, detail="Device not found")
        account_id = str(auth_user.get("account_id") or getattr(user, "account_id", "") or "").strip()
        actor_session_id = str(auth_user.get("session_id") or "").strip()
        device = (
            s.query(AccountDevice)
            .filter(
                AccountDevice.account_id == account_id,
                or_(AccountDevice.id == target, AccountDevice.install_id == target),
            )
            .first()
            if account_id
            else None
        )
        if device is None:
            raise HTTPException(status_code=404, detail="Device not found")
        if not actor_session_id:
            raise HTTPException(
                status_code=409,
                detail={"code": "cannot_revoke_current_device", "message": "Current device cannot revoke itself."},
            )
        try:
            revoked = auth_session_service.revoke_device(
                s,
                account_id=account_id,
                device_id=str(device.id),
                actor_session_id=actor_session_id,
                now=_utcnow(),
            )
            s.commit()
        except auth_session_service.AuthSessionError as exc:
            s.rollback()
            raise _auth_session_http_exception(exc) from exc
        return {
            "ok": True,
            "device": {
                "id": str(revoked.install_id),
                "registryId": str(revoked.id),
                "active": False,
                "state": str(revoked.state or "revoked"),
                "revokedAt": _safe_iso(revoked.revoked_at),
            },
        }
    finally:
        s.close()


@app.get("/api/client/notifications")
async def client_notifications(
    request: Request,
    after: str = Query(default="", max_length=128),
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    del after
    s, user, _auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        nodes = enabled_nodes(s)
        nodes_for_user = _nodes_for_user(user, nodes, session=s)
        runtime = await _get_user_runtime_summary(s=s, user=user, nodes=nodes_for_user)
        access_policy = _build_reconciled_access_policy(
            session=s,
            user=user,
            used_bytes=int(runtime.get("traffic_total_bytes", 0) or 0),
            source="client_notifications_runtime",
        )
        read_ids = _client_notification_read_ids(s, user=user)
        incidents = (
            s.query(ServiceIncident)
            .filter(ServiceIncident.status == "confirmed")
            .order_by(ServiceIncident.started_at.desc())
            .limit(10)
            .all()
        )
        live_updates = (
            s.query(LiveUpdate)
            .filter(LiveUpdate.is_active == True)
            .order_by(LiveUpdate.sort_order.asc(), LiveUpdate.id.desc())
            .limit(10)
            .all()
        )
        account_id = str(getattr(user, "account_id", "") or "").strip()
        compensation_grants = (
            s.query(EntitlementGrant)
            .filter(
                EntitlementGrant.account_id == account_id,
                EntitlementGrant.source == "incident_compensation",
                EntitlementGrant.status == "active",
            )
            .order_by(EntitlementGrant.created_at.desc())
            .limit(10)
            .all()
            if account_id
            else []
        )
        program_applications = (
            s.query(ProgramApplication)
            .filter(ProgramApplication.account_id == account_id)
            .order_by(ProgramApplication.updated_at.desc(), ProgramApplication.created_at.desc())
            .limit(10)
            .all()
            if account_id
            else []
        )
        items = _client_notification_items(
            user=user,
            access_policy=access_policy,
            read_ids=read_ids,
            incidents=incidents,
            live_updates=live_updates,
            compensation_grants=compensation_grants,
            program_applications=program_applications,
        )
        return {
            "items": items,
            "nextCursor": None,
            "unreadCount": sum(1 for item in items if not bool(item.get("read"))),
        }
    finally:
        s.close()


@app.post("/api/client/notifications/read")
async def client_notifications_read(
    payload: ClientNotificationsReadIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    s, user, _auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        ids = []
        for item in list(payload.ids or [])[:100]:
            value = str(item or "").strip()
            if value and value not in ids:
                ids.append(value[:128])
        _record_client_event(
            s,
            user=user,
            event_name="client_notification_read",
            meta={"ids": ids},
        )
        s.commit()
        return {"ok": True, "accepted": len(ids), "ignored": []}
    finally:
        s.close()


@app.post("/api/client/push/register")
async def client_push_register(
    payload: ClientPushRegisterIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    s, user, _auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        platform = re.sub(r"[^a-z0-9_.:-]+", "_", str(payload.platform or "").strip().lower())[:32]
        provider = re.sub(r"[^a-z0-9_.:-]+", "_", str(payload.provider or "").strip().lower())[:32]
        token = str(payload.token or "").strip()
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        _record_client_event(
            s,
            user=user,
            event_name="client_push_register",
            session_id=str(getattr(user, "app_install_id", "") or ""),
            meta={
                "platform": platform,
                "provider": provider,
                "token_hash": token_hash,
                "token_last4": token[-4:],
            },
        )
        s.commit()
        return {"ok": True, "platform": platform, "provider": provider, "tokenHash": token_hash}
    finally:
        s.close()


@app.post("/api/client/support/assistant")
async def client_support_assistant(
    payload: ClientSupportAssistantIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    s, user, _auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        if str(payload.scope or "").strip().casefold() != "support":
            raise HTTPException(status_code=422, detail="Invalid assistant scope")
        ticket_id = int(payload.ticket_id or payload.ticketId or 0)
        if ticket_id:
            ticket = get_ticket_by_id(s, ticket_id)
            if not ticket:
                raise HTTPException(status_code=404, detail="Ticket not found")
            if int(ticket.user_tg_id) != int(user.tg_id):
                raise HTTPException(status_code=403, detail="Access denied")
        diagnostics = _admit_support_assistant_diagnostics(payload.safeDiagnostics)
        diagnostics.update(await _support_assistant_account_diagnostics(s=s, user=user))
        message = str(payload.message or "").strip()
        supplied_session_id = payload.assistant_session_id or payload.assistantSessionId
        owner_id = str(getattr(user, "account_id", "") or "").strip() or f"tg:{int(user.tg_id)}"
        result = await SUPPORT_AGENT_SERVICE.generate(
            surface="app",
            authenticated_owner_id=owner_id,
            message=message,
            assistant_session_id=supplied_session_id,
            ticket_id=ticket_id or None,
            safe_diagnostics=diagnostics,
        )
        reply = str(result.reply or "").strip() or support_fallback_reply(message)

        if ticket_id and reply:
            add_ticket_message(
                s,
                ticket_id=ticket_id,
                sender_tg_id=0,
                sender_role="assistant",
                body=reply[:2000],
            )

        _record_client_event(
            s,
            user=user,
            event_name="client_support_assistant",
            source="app",
            meta={
                "scope": "support",
                "source": result.source,
                "ticket_id": ticket_id or None,
                "should_escalate": bool(result.should_escalate),
                "diagnostics_keys": sorted(diagnostics),
            },
        )
        s.commit()
        return {
            "reply": reply,
            "assistantSessionId": result.assistant_session_id,
            "suggestedActions": list(result.suggested_actions),
            "shouldEscalate": bool(result.should_escalate),
            "source": result.source,
        }
    finally:
        s.close()


@app.get("/api/client/profile/managed")
async def client_managed_profile(
    request: Request,
    selected_node_code: str = Query(default="", max_length=32),
    x_telegram_init_data: str = Header(default=""),
    x_portal_carrier: str = Header(default=""),
) -> dict[str, Any]:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        _maybe_downgrade_expired_to_free(s, user)
        _ensure_free_cycle_state_persisted(s, user)
        rollout_config = load_network_rollout_config(session=s)
        install_id = str(getattr(user, "app_install_id", "") or "").strip() or None
        client_policy = app_first_service.build_client_policy(
            session=s,
            user=user,
            install_id=install_id,
            carrier=_request_carrier_header(x_portal_carrier),
            rollout_config=rollout_config,
        )
        transport_profile = str(client_policy.get("transport_profile") or LEGACY_REALITY_FALLBACK).strip() or LEGACY_REALITY_FALLBACK
        nodes = enabled_nodes(s)
        nodes_for_user = _nodes_for_user(user, nodes, session=s)
        requested_node_code = str(selected_node_code or "").strip().lower()
        smart_connect = _smart_connect_shortlist(
            session=s,
            user=user,
            nodes=nodes_for_user,
            transport_profile=transport_profile,
            rollout_config=rollout_config,
            profile_revision=str(client_policy.get("profile_revision") or ""),
            preferred_node_code=requested_node_code,
        )
        sync_ok = await _sync_control_panel_access(user=user)
        if not sync_ok:
            logger.warning(
                "managed profile panel sync returned false tg_id=%s plan=%s sub_type=%s",
                int(user.tg_id),
                str(getattr(user, "current_plan_code", "") or ""),
                str(getattr(user, "sub_type", "") or ""),
            )
        runtime = await _get_user_runtime_summary(s=s, user=user, nodes=nodes_for_user)
        access_policy = _build_reconciled_access_policy(
            session=s,
            user=user,
            used_bytes=int(runtime.get("traffic_total_bytes", 0) or 0),
            source="managed_profile_runtime",
        )
        effective_nodes = _effective_transport_nodes(
            nodes=nodes_for_user,
            rollout_config=rollout_config,
            transport_profile=transport_profile,
        )
        effective_by_code = _nodes_by_code(effective_nodes)
        shortlist_codes = [
            str(item.get("code") or "").strip().lower()
            for item in smart_connect.get("shortlist") or []
            if str(item.get("code") or "").strip()
        ]
        effective_nodes = [effective_by_code[code] for code in shortlist_codes if code in effective_by_code]
        if not effective_nodes:
            raise HTTPException(status_code=503, detail="No eligible nodes")
        if requested_node_code not in set(shortlist_codes):
            requested_node_code = ""
        ranked_effective_nodes = rank_nodes_for_app(
            effective_nodes,
            policy_by_code=_node_capacity_policy_by_code(s),
            now=_utcnow(),
        )
        effective_nodes = _prefer_smart_connect_node_order(
            nodes=ranked_effective_nodes,
            preferred_node_code=requested_node_code
            or str((smart_connect.get("stickiness") or {}).get("preferred_node_code") or ""),
        )
        if requested_node_code:
            smart_connect["selected_node_code"] = requested_node_code
        config_format, config_payload = _managed_manifest_payload(
            user=user,
            nodes=effective_nodes,
            title="POKROV",
            transport_profile=transport_profile,
            rollout_config=rollout_config,
        )
        return {
            "version": str(rollout_config.get("version") or ""),
            "profile_revision": str(client_policy.get("profile_revision") or ""),
            "transport_profile": transport_profile,
            "transport_kind": str(client_policy.get("transport_kind") or ""),
            "engine_hint": str(client_policy.get("engine_hint") or ""),
            "config_format": config_format,
            "config_payload": config_payload,
            "fallback_order": _managed_manifest_fallback_order(transport_profile),
            "support_context": dict(client_policy.get("support_context") or {}),
            "subscription_url": build_subscription_url(str(getattr(user, "sub_token", "") or "")),
            "smart_connect": smart_connect,
            "warp_policy": managed_warp_policy_for_user(
                s,
                user=user,
                install_id=install_id,
                rollout_config=rollout_config,
            ),
            "linked_identities": _linked_identities_payload(s=s, user=user, auth_user=auth_user),
            "access": {
                **access_policy,
                "sub_type": str(getattr(user, "sub_type", "") or ""),
                "current_plan_code": str(getattr(user, "current_plan_code", "") or ""),
                "expiry_at": _safe_iso(getattr(user, "expiry_at", None)),
            },
            "free_caps": _free_caps_payload(user=user, access_policy=access_policy),
            "redeem_eligibility": _redeem_eligibility_payload(user=user, access_policy=access_policy),
            "promo_slots": _promo_slots_payload_for_surface(
                s=s,
                surface="app",
                access_state=str(access_policy.get("access_state") or ""),
            ),
            "hidden_transport_matrix": _hidden_transport_matrix_payload(nodes=nodes_for_user, client_policy=client_policy),
            "location_matrix": _location_matrix_payload(user=user, nodes=nodes_for_user, client_policy=client_policy),
            "provisioning": {
                "status": "ready" if sync_ok else "pending_sync",
                "sync_ok": bool(sync_ok),
                "managed_profile_path": "/api/client/profile/managed",
            },
        }
    finally:
        s.close()


@app.get("/api/client/promo-slots")
async def client_promo_slots(
    request: Request,
    surface: str = Query(default="app", min_length=2, max_length=32),
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        _maybe_downgrade_expired_to_free(s, user)
        _ensure_free_cycle_state_persisted(s, user)
        nodes = enabled_nodes(s)
        nodes_for_user = _nodes_for_user(user, nodes, session=s)
        runtime = await _get_user_runtime_summary(s=s, user=user, nodes=nodes_for_user)
        access_policy = _build_reconciled_access_policy(
            session=s,
            user=user,
            used_bytes=int(runtime.get("traffic_total_bytes", 0) or 0),
            source="promo_runtime",
        )
        return _promo_slots_payload_for_surface(
            s=s,
            surface=str(surface or "app").strip().lower(),
            access_state=str(access_policy.get("access_state") or ""),
        )
    finally:
        s.close()


def _best_rtt_by_code(samples: list[NodeLatencyPointIn], *, allowed_codes: set[str]) -> dict[str, int]:
    out: dict[str, int] = {}
    for sample in list(samples or [])[:16]:
        code = str(sample.node_code or "").strip().lower()
        if not code or (allowed_codes and code not in allowed_codes):
            continue
        value = int(sample.rtt_ms)
        current = out.get(code)
        if current is None or value < current:
            out[code] = value
    return out


@app.get("/api/client/nodes/candidates")
async def client_nodes_candidates(
    request: Request,
    profile_revision: str = Query(default="", max_length=128),
    transport_profile: str = Query(default="", max_length=64),
    x_telegram_init_data: str = Header(default=""),
    x_portal_carrier: str = Header(default=""),
) -> dict[str, Any]:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        _maybe_downgrade_expired_to_free(s, user)
        _ensure_free_cycle_state_persisted(s, user)
        rollout_config = load_network_rollout_config(session=s)
        client_policy = app_first_service.build_client_policy(
            session=s,
            user=user,
            install_id=str(getattr(user, "app_install_id", "") or "").strip() or None,
            carrier=_request_carrier_header(x_portal_carrier),
            rollout_config=rollout_config,
        )
        resolved_profile = str(transport_profile or client_policy.get("transport_profile") or LEGACY_REALITY_FALLBACK).strip()
        resolved_profile = resolved_profile or LEGACY_REALITY_FALLBACK
        nodes = enabled_nodes(s)
        nodes_for_user = _nodes_for_user(user, nodes, session=s)
        smart_connect = _smart_connect_shortlist(
            session=s,
            user=user,
            nodes=nodes_for_user,
            transport_profile=resolved_profile,
            rollout_config=rollout_config,
            profile_revision=str(profile_revision or client_policy.get("profile_revision") or ""),
        )
        return {
            "ok": True,
            "strategy": "capacity_rtt_sticky",
            "ttl_seconds": int(os.getenv("SMART_CONNECT_CANDIDATE_TTL_SECONDS", "120")),
            "probe_timeout_ms": int(os.getenv("SMART_CONNECT_PROBE_TIMEOUT_MS", "1500")),
            "profile_revision": str(profile_revision or client_policy.get("profile_revision") or ""),
            "transport_profile": resolved_profile,
            "shortlist": list(smart_connect.get("shortlist") or []),
            "stickiness": dict(smart_connect.get("stickiness") or {}),
            "fallback_order": list(smart_connect.get("fallback_order") or []),
            "rejected_counts": dict(smart_connect.get("rejected_counts") or {}),
        }
    finally:
        s.close()


@app.post("/api/client/nodes/select")
async def client_nodes_select(
    payload: NodeSelectIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
    x_portal_carrier: str = Header(default=""),
) -> dict[str, Any]:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        install_id = str(getattr(user, "app_install_id", "") or "").strip()
        if not install_id:
            raise HTTPException(status_code=400, detail="install_id is required")
        if str(os.getenv("APP_NODES_SELECT_ENDPOINT", "true")).strip().lower() in {"0", "false", "no", "off"}:
            return {
                "ok": True,
                "enabled": False,
                "selected_node_code": None,
                "reason": "feature_disabled",
                "stickiness_applied": False,
                "accepted_samples": [],
            }

        rollout_config = load_network_rollout_config(session=s)
        client_policy = app_first_service.build_client_policy(
            session=s,
            user=user,
            install_id=install_id,
            carrier=_request_carrier_header(x_portal_carrier),
            rollout_config=rollout_config,
        )
        resolved_profile = str(payload.transport_profile or client_policy.get("transport_profile") or LEGACY_REALITY_FALLBACK).strip()
        resolved_profile = resolved_profile or LEGACY_REALITY_FALLBACK
        nodes = enabled_nodes(s)
        nodes_for_user = _nodes_for_user(user, nodes, session=s)
        effective_nodes = _effective_transport_nodes(
            nodes=nodes_for_user,
            rollout_config=rollout_config,
            transport_profile=resolved_profile,
        )
        mode = str(payload.mode or "auto").strip().lower()
        selected_node_code = str(payload.selected_node_code or "").strip().lower()
        smart_connect = _smart_connect_shortlist(
            session=s,
            user=user,
            nodes=nodes_for_user,
            transport_profile=resolved_profile,
            rollout_config=rollout_config,
            profile_revision=str(payload.profile_revision or client_policy.get("profile_revision") or ""),
            preferred_node_code=selected_node_code if mode == "manual" else "",
        )
        shortlist_codes = {
            str(item.get("code") or "").strip().lower()
            for item in smart_connect.get("shortlist") or []
            if str(item.get("code") or "").strip()
        }
        effective_by_code = _nodes_by_code(effective_nodes)
        if not shortlist_codes:
            raise HTTPException(status_code=503, detail="No eligible nodes")
        previous_node_code = str(payload.previous_node_code or "").strip().lower()
        policy_by_code = _node_capacity_policy_by_code(s)
        rtt_by_code = _best_rtt_by_code(payload.samples, allowed_codes=shortlist_codes)
        accepted_samples = [
            {"node_code": code, "rtt_ms": int(value)}
            for code, value in sorted(rtt_by_code.items())
        ]

        candidate_codes = shortlist_codes
        if mode == "manual":
            if selected_node_code not in candidate_codes:
                raise HTTPException(status_code=400, detail="selected node is not eligible")
            winner = selected_node_code
            stickiness_applied = False
            reason = "manual_preference"
        else:
            candidate_nodes = [effective_by_code[code] for code in candidate_codes if code in effective_by_code]
            ranked = rank_nodes_for_app(
                candidate_nodes,
                client_rtt_by_code=rtt_by_code,
                policy_by_code=policy_by_code,
                now=_utcnow(),
            )
            if not ranked:
                raise HTTPException(status_code=503, detail="No eligible nodes")
            winner = str(getattr(ranked[0], "code", "") or "").strip().lower()
            stickiness_applied = False
            reason = "best_capacity_rtt"
            if previous_node_code and previous_node_code in candidate_codes and previous_node_code in effective_by_code:
                previous_node = effective_by_code[previous_node_code]
                winner_node = effective_by_code.get(winner)
                prev_reject = node_hard_reject_reason(previous_node, policy=policy_by_code.get(previous_node_code), now=_utcnow())
                if not prev_reject and winner_node is not None:
                    prev_score = node_selection_score(
                        previous_node,
                        policy=policy_by_code.get(previous_node_code),
                        client_rtt_ms=rtt_by_code.get(previous_node_code),
                    )
                    winner_score = node_selection_score(
                        winner_node,
                        policy=policy_by_code.get(winner),
                        client_rtt_ms=rtt_by_code.get(winner),
                    )
                    if prev_score > 0:
                        improvement_percent = max(0.0, (prev_score - winner_score) / prev_score * 100.0)
                        if improvement_percent < float(SMART_CONNECT_STICKINESS_THRESHOLD_PERCENT):
                            winner = previous_node_code
                            stickiness_applied = True
                            reason = "sticky_previous"

        event_meta = {
            "install_id": install_id,
            "mode": mode,
            "profile_revision": str(payload.profile_revision or client_policy.get("profile_revision") or ""),
            "transport_profile": resolved_profile,
            "selected_node_code": winner,
            "requested_node_code": selected_node_code or None,
            "previous_node_code": previous_node_code or None,
            "stickiness_applied": bool(stickiness_applied),
            "reason": reason,
            "samples": accepted_samples,
            "carrier": _request_carrier_header(x_portal_carrier) or None,
            "platform": str(getattr(user, "app_platform", "") or "").strip() or None,
        }
        _record_client_event(
            s,
            user=user,
            event_name="smart_connect_node_select",
            source="app",
            session_id=install_id,
            meta=event_meta,
        )
        s.commit()
        managed_profile_url = "/api/client/profile/managed"
        if winner:
            managed_profile_url = f"{managed_profile_url}?{urlencode({'selected_node_code': winner})}"
        return {
            "ok": True,
            "selected_node_code": winner,
            "previous_node_code": previous_node_code or None,
            "stickiness_applied": bool(stickiness_applied),
            "reason": reason,
            "requires_profile_refresh": bool(winner and winner != previous_node_code),
            "managed_profile_url": managed_profile_url,
            "profile_revision": str(payload.profile_revision or client_policy.get("profile_revision") or ""),
            "transport_profile": resolved_profile,
            "accepted_samples": len(accepted_samples),
        }
    finally:
        s.close()


@app.post("/api/client/runtime/stats")
async def client_runtime_stats(
    payload: ClientRuntimeStatsIn,
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
        _record_client_event(
            s,
            user=user,
            event_name="client_runtime_stats",
            source="app",
            session_id=str(getattr(user, "app_install_id", "") or "").strip() or None,
            meta={
                "profile_revision": str(payload.profile_revision or "") or None,
                "selected_node_code": str(payload.selected_node_code or "").strip().lower() or None,
                "runtime_phase": str(payload.runtime_phase or "").strip().lower() or None,
                "connected": payload.connected,
                "uptime_seconds": payload.uptime_seconds,
                "rtt_ms": payload.rtt_ms,
                "rx_mbps": payload.rx_mbps,
                "tx_mbps": payload.tx_mbps,
                "error_code": str(payload.error_code or "").strip() or None,
            },
        )
        if bool(payload.connected):
            account_id = str(auth_user.get("account_id") or getattr(user, "account_id", "") or "").strip()
            if account_id:
                account_experience_service.record_first_connection_reported(
                    s,
                    account_id=account_id,
                )
        s.commit()
        return {"ok": True}
    finally:
        s.close()


@app.post("/api/account/experience/onboarding")
async def account_onboarding_status(
    payload: AccountOnboardingStatusIn,
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
        account_id = str(auth_user.get("account_id") or getattr(user, "account_id", "") or "").strip()
        if not account_id:
            raise HTTPException(status_code=409, detail="Account foundation is not ready")
        try:
            account_experience_service.set_onboarding_status(
                s,
                account_id=account_id,
                status=payload.status,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        experience = account_experience_service.build_experience_snapshot(
            s,
            account_id=account_id,
            app_identity_known=bool(str(getattr(user, "app_install_id", "") or "").strip()),
        )
        s.commit()
        return {"ok": True, "experience": experience}
    finally:
        s.close()


def _node_metrics_secret(node: Node | None = None) -> str:
    return (
        str(os.getenv("NODE_AGENT_METRICS_SECRET") or "").strip()
        or str(getattr(node, "observer_push_secret", "") or "").strip()
    )


async def _require_node_metrics_signature(request: Request, *, node: Node | None) -> None:
    secret = _node_metrics_secret(node)
    if not secret:
        raise HTTPException(status_code=503, detail="node metrics secret is not configured")
    timestamp = str(request.headers.get("X-POKROV-Timestamp") or "").strip()
    signature = str(request.headers.get("X-POKROV-Signature") or "").strip().lower()
    if not timestamp or not signature:
        raise HTTPException(status_code=401, detail="missing node metrics signature")
    try:
        ts_value = int(timestamp)
    except Exception:
        raise HTTPException(status_code=401, detail="invalid node metrics timestamp")
    if abs(int(time.time()) - ts_value) > int(os.getenv("NODE_AGENT_METRICS_MAX_SKEW_SECONDS", "120")):
        raise HTTPException(status_code=401, detail="stale node metrics signature")
    body = await request.body()
    messages = [
        timestamp.encode("utf-8") + b"." + body,
        body + b"." + timestamp.encode("utf-8"),
        body,
    ]
    valid = any(
        hmac.compare_digest(
            hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest().lower(),
            signature,
        )
        for message in messages
    )
    if not valid:
        raise HTTPException(status_code=401, detail="invalid node metrics signature")


def _apply_node_metric_payload(node: Node, payload: InternalNodeMetricsIn, *, policy: Any | None = None) -> dict[str, Any]:
    sampled_at = payload.sampled_at or _utcnow()
    provisioned = int(payload.provisioned_clients_count if payload.provisioned_clients_count is not None else getattr(node, "provisioned_clients_count", 0) or 0)
    online_hint = int(payload.online_connections_hint if payload.online_connections_hint is not None else getattr(node, "online_connections_hint", 0) or 0)
    tx_1m = payload.network_tx_mbps_1m
    tx_5m = payload.network_tx_mbps_5m
    rx_1m = payload.network_rx_mbps_1m
    rx_5m = payload.network_rx_mbps_5m
    total_mbps = payload.network_total_mbps
    if total_mbps is None:
        total_mbps = float((tx_1m or tx_5m or 0.0) + (rx_1m or rx_5m or 0.0))

    node.provisioned_clients_count = provisioned
    node.active_clients = provisioned
    node.online_connections_hint = online_hint
    node.network_tx_mbps_1m = tx_1m
    node.network_tx_mbps_5m = tx_5m
    node.network_rx_mbps_1m = rx_1m
    node.network_rx_mbps_5m = rx_5m
    node.network_total_mbps = total_mbps
    if tx_1m is not None:
        node.network_tx_mbps = tx_1m
    if rx_1m is not None:
        node.network_rx_mbps = rx_1m
    if payload.cpu_percent is not None:
        node.cpu_percent = payload.cpu_percent
    if payload.memory_used_mb is not None:
        node.memory_used_mb = payload.memory_used_mb
    if payload.memory_total_mb is not None:
        node.memory_total_mb = payload.memory_total_mb
    node.tcp_retrans_percent = payload.tcp_retrans_percent
    node.packet_loss_percent = payload.packet_loss_percent
    node.dataplane_ok = payload.dataplane_ok
    node.dataplane_rtt_ms = payload.dataplane_rtt_ms
    node.last_health_at = sampled_at
    node.last_ok_at = sampled_at if payload.dataplane_ok is not False else getattr(node, "last_ok_at", None)
    node.is_healthy = payload.dataplane_ok is not False
    capacity = node_capacity_status(node, policy=policy, now=sampled_at)
    node.capacity_score = float(capacity.get("score") or 0.0)
    node.capacity_state = str(capacity.get("state") or "unknown")
    node.capacity_reject_reason = str(capacity.get("reject_reason") or "") or None
    return capacity


def _int_metric(value: Any, default: int = 0) -> int:
    try:
        return max(0, int(value))
    except Exception:
        return int(default)


def _float_metric(value: Any, default: float = 0.0) -> float:
    try:
        return max(0.0, float(value))
    except Exception:
        return float(default)


def _key_pressure_state(
    *,
    traffic_gb_24h: float,
    peak_tx_mbps: float,
    distinct_source_ips_24h: int,
    distinct_asns_24h: int,
    distinct_countries_24h: int,
    node_count_24h: int,
) -> tuple[str, float, list[str], bool]:
    score = 0.0
    reasons: list[str] = []

    if peak_tx_mbps >= 120.0:
        score += 45.0
        reasons.append("peak_tx_mbps>=120")
    elif peak_tx_mbps >= 60.0:
        score += 25.0
        reasons.append("peak_tx_mbps>=60")

    if traffic_gb_24h >= 300.0:
        score += 45.0
        reasons.append("traffic_gb_24h>=300")
    elif traffic_gb_24h >= 100.0:
        score += 28.0
        reasons.append("traffic_gb_24h>=100")
    elif traffic_gb_24h >= 30.0:
        score += 12.0
        reasons.append("traffic_gb_24h>=30")

    if distinct_source_ips_24h >= 20:
        score += 30.0
        reasons.append("distinct_source_ips_24h>=20")
    elif distinct_source_ips_24h >= 8:
        score += 15.0
        reasons.append("distinct_source_ips_24h>=8")

    if distinct_asns_24h >= 5:
        score += 25.0
        reasons.append("distinct_asns_24h>=5")
    elif distinct_asns_24h >= 3:
        score += 12.0
        reasons.append("distinct_asns_24h>=3")

    if distinct_countries_24h >= 4:
        score += 25.0
        reasons.append("distinct_countries_24h>=4")
    elif distinct_countries_24h >= 2:
        score += 10.0
        reasons.append("distinct_countries_24h>=2")

    if node_count_24h >= 4:
        score += 20.0
        reasons.append("node_count_24h>=4")
    elif node_count_24h >= 2:
        score += 8.0
        reasons.append("node_count_24h>=2")

    traffic_pressure = peak_tx_mbps >= 20.0 or traffic_gb_24h >= 20.0
    if not traffic_pressure and score > 35.0:
        score = 35.0
        reasons.append("churn_without_traffic_pressure_capped")

    if score >= 100.0:
        state = "fair_use" if KEY_PRESSURE_FAIR_USE_ROUTING else "suspected_shared"
    elif score >= 75.0:
        state = "suspected_shared"
    elif score >= 45.0:
        state = "heavy"
    elif score >= 20.0:
        state = "warm"
    else:
        state = "ok"
    return state, round(score, 3), reasons, state in {"heavy", "suspected_shared", "fair_use"}


def _upsert_key_pressure_state(
    s,
    *,
    key_id: int | None,
    tg_id: int | None,
    node_code: str,
    panel_email: str,
    item: dict[str, Any],
    total_bytes: int,
    source_ip_hashes: list[Any],
) -> None:
    if not KEY_PRESSURE_SCORING or not key_id:
        return
    ips_24h = _int_metric(item.get("distinct_source_ips_24h"), len(source_ip_hashes))
    ips_1h = _int_metric(item.get("distinct_source_ips_1h"), min(ips_24h, len(source_ip_hashes)))
    asns_raw = item.get("source_asns") if isinstance(item.get("source_asns"), list) else []
    countries_raw = item.get("source_countries") if isinstance(item.get("source_countries"), list) else []
    asns_24h = _int_metric(item.get("distinct_asns_24h"), len({str(v) for v in asns_raw if str(v).strip()}))
    countries_24h = _int_metric(
        item.get("distinct_countries_24h"),
        len({str(v).upper() for v in countries_raw if str(v).strip()}),
    )
    node_count_24h = _int_metric(item.get("node_count_24h"), 1)
    traffic_gb_24h = _float_metric(item.get("traffic_gb_24h"), float(total_bytes) / 1024.0 / 1024.0 / 1024.0)
    peak_tx_mbps = _float_metric(item.get("peak_tx_mbps"), 0.0)
    state, score, reasons, manual_review = _key_pressure_state(
        traffic_gb_24h=traffic_gb_24h,
        peak_tx_mbps=peak_tx_mbps,
        distinct_source_ips_24h=ips_24h,
        distinct_asns_24h=asns_24h,
        distinct_countries_24h=countries_24h,
        node_count_24h=node_count_24h,
    )
    row = s.get(KeyPressureState, int(key_id))
    if row is None:
        row = KeyPressureState(key_id=int(key_id))
        s.add(row)
    row.tg_id = tg_id or None
    row.node_code = str(node_code or "")[:32] or None
    row.panel_email = str(panel_email or "")[:100] or None
    row.state = state
    row.pressure_score = float(score)
    row.reasons_json = json.dumps(reasons, ensure_ascii=False, separators=(",", ":"))[:2000]
    row.distinct_source_ips_1h = int(ips_1h)
    row.distinct_source_ips_24h = int(ips_24h)
    row.node_count_24h = int(node_count_24h)
    row.traffic_gb_24h = float(round(traffic_gb_24h, 6))
    row.manual_review_required = bool(manual_review)
    row.updated_at = _utcnow()


@app.post("/api/internal/nodes/{node_code}/metrics")
async def internal_node_metrics(
    node_code: str,
    payload: InternalNodeMetricsIn,
    request: Request,
) -> dict[str, Any]:
    wanted = str(node_code or "").strip().lower()
    if not wanted:
        raise HTTPException(status_code=400, detail="node_code is required")
    s = SessionLocal()
    try:
        node = s.query(Node).filter(func.lower(Node.code) == wanted).first()
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")
        await _require_node_metrics_signature(request, node=node)
        policy = s.query(NodeCapacityPolicy).filter(func.lower(NodeCapacityPolicy.node_code) == wanted).first()
        capacity = _apply_node_metric_payload(node, payload, policy=policy)
        safe_meta = sanitize_runtime_metric_meta(payload.meta)
        sampled_at = payload.sampled_at or _utcnow()
        metric = NodeRuntimeMetric(
            node_code=wanted,
            sampled_at=sampled_at,
            source=str(payload.source or "node_agent").strip()[:64] or "node_agent",
            batch_id=str(payload.batch_id or "").strip()[:128] or None,
            provisioned_clients_count=int(getattr(node, "provisioned_clients_count", 0) or 0),
            online_connections_hint=int(getattr(node, "online_connections_hint", 0) or 0),
            network_rx_mbps_1m=payload.network_rx_mbps_1m,
            network_tx_mbps_1m=payload.network_tx_mbps_1m,
            network_rx_mbps_5m=payload.network_rx_mbps_5m,
            network_tx_mbps_5m=payload.network_tx_mbps_5m,
            network_total_mbps=getattr(node, "network_total_mbps", None),
            cpu_percent=getattr(node, "cpu_percent", None),
            memory_used_mb=getattr(node, "memory_used_mb", None),
            memory_total_mb=getattr(node, "memory_total_mb", None),
            tcp_retrans_percent=payload.tcp_retrans_percent,
            packet_loss_percent=payload.packet_loss_percent,
            dataplane_ok=payload.dataplane_ok,
            dataplane_rtt_ms=payload.dataplane_rtt_ms,
            capacity_score=float(capacity.get("score") or 0.0),
            capacity_state=str(capacity.get("state") or "unknown"),
            reject_reason=str(capacity.get("reject_reason") or "") or None,
            meta_json=json.dumps(safe_meta, ensure_ascii=False, separators=(",", ":")),
        )
        s.add(metric)
        s.commit()
        return {"ok": True, "node_code": wanted, "capacity": capacity}
    finally:
        s.close()


@app.post("/api/internal/nodes/{node_code}/xray-stats")
async def internal_node_xray_stats(node_code: str, request: Request) -> dict[str, Any]:
    wanted = str(node_code or "").strip().lower()
    if not wanted:
        raise HTTPException(status_code=400, detail="node_code is required")
    s = SessionLocal()
    try:
        node = s.query(Node).filter(func.lower(Node.code) == wanted).first()
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")
        await _require_node_metrics_signature(request, node=node)
        try:
            payload = await request.json()
        except Exception:
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        rows = list(payload.get("keys") or payload.get("clients") or [])
        if not isinstance(rows, list):
            rows = []
        bucket_at = _utcnow().replace(second=0, microsecond=0)
        accepted = 0
        for item in rows[:500]:
            if not isinstance(item, dict):
                continue
            panel_email = str(item.get("panel_email") or item.get("email") or "").strip()
            key_uuid = str(item.get("key_uuid") or item.get("uuid") or "").strip()
            key_row = None
            if panel_email:
                key_row = (
                    s.query(AccessKey)
                    .filter(func.lower(AccessKey.node_code) == wanted)
                    .filter(func.lower(AccessKey.panel_email) == panel_email.lower())
                    .first()
                )
            if not key_row and key_uuid:
                key_row = s.query(AccessKey).filter(AccessKey.key_uuid == key_uuid).first()
            tg_id = int(getattr(key_row, "tg_id", 0) or int(item.get("tg_id") or 0))
            upload_bytes = int(item.get("upload_bytes") or item.get("up") or 0)
            download_bytes = int(item.get("download_bytes") or item.get("down") or 0)
            total_bytes = int(item.get("total_bytes") or upload_bytes + download_bytes)
            key_id = int(getattr(key_row, "id", 0) or 0) or None
            window_seconds = int(item.get("window_seconds") or payload.get("window_seconds") or 300)
            rollup = None
            if key_id:
                rollup = (
                    s.query(KeyUsageRollup)
                    .filter(KeyUsageRollup.key_id == key_id)
                    .filter(KeyUsageRollup.node_code == wanted)
                    .filter(KeyUsageRollup.window_bucket_at == bucket_at)
                    .filter(KeyUsageRollup.window_seconds == window_seconds)
                    .first()
                )
            if rollup is None:
                rollup = KeyUsageRollup(
                    key_id=key_id,
                    node_code=wanted,
                    window_bucket_at=bucket_at,
                    window_seconds=window_seconds,
                )
                s.add(rollup)
            rollup.tg_id = tg_id or None
            rollup.panel_email = panel_email or None
            rollup.upload_bytes = max(0, upload_bytes)
            rollup.download_bytes = max(0, download_bytes)
            rollup.total_bytes = max(0, total_bytes)
            rollup.peak_tx_mbps = float(item.get("peak_tx_mbps")) if item.get("peak_tx_mbps") is not None else None
            rollup.observations = int(item.get("observations") or 1)
            rollup.source = str(payload.get("source") or "xray_stats").strip()[:64] or "xray_stats"
            source_ip_hashes = item.get("source_ip_hashes") or item.get("source_ips") or []
            if isinstance(source_ip_hashes, list):
                for raw_hash in source_ip_hashes[:50]:
                    source_hash = hashlib.sha256(str(raw_hash).encode("utf-8")).hexdigest() if len(str(raw_hash)) != 64 else str(raw_hash)
                    observation = None
                    if key_id:
                        observation = (
                            s.query(KeySourceObservation)
                            .filter(KeySourceObservation.key_id == key_id)
                            .filter(KeySourceObservation.node_code == wanted)
                            .filter(KeySourceObservation.source_ip_hash == source_hash[:64])
                            .filter(KeySourceObservation.window_bucket_at == bucket_at)
                            .first()
                        )
                    if observation is None:
                        observation = KeySourceObservation(
                            key_id=key_id,
                            node_code=wanted,
                            source_ip_hash=source_hash[:64],
                            window_bucket_at=bucket_at,
                            first_seen_at=bucket_at,
                            hit_count=0,
                        )
                        s.add(observation)
                    observation.tg_id = tg_id or None
                    observation.panel_email = panel_email or None
                    observation.source_asn = str(item.get("source_asn") or "")[:32] or None
                    observation.source_country = str(item.get("source_country") or "")[:8] or None
                    observation.last_seen_at = _utcnow()
                    observation.hit_count = int(observation.hit_count or 0) + 1
            _upsert_key_pressure_state(
                s,
                key_id=key_id,
                tg_id=tg_id or None,
                node_code=wanted,
                panel_email=panel_email,
                item=item,
                total_bytes=max(0, total_bytes),
                source_ip_hashes=source_ip_hashes if isinstance(source_ip_hashes, list) else [],
            )
            if tg_id:
                observed_user = s.query(User).filter(User.tg_id == int(tg_id)).first()
                if observed_user is not None:
                    reconcile_free_profile_usage(
                        s,
                        user=observed_user,
                        used_bytes=max(0, total_bytes),
                        source="node_xray_stats",
                        now=_utcnow(),
                    )
            accepted += 1
        s.commit()
        return {"ok": True, "node_code": wanted, "accepted": accepted}
    finally:
        s.close()


@app.post("/api/client/nodes/latency-samples")
async def client_nodes_latency_samples(
    payload: NodeLatencySamplesIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
    x_portal_carrier: str = Header(default=""),
) -> dict[str, Any]:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        install_id = str(getattr(user, "app_install_id", "") or "").strip()
        if not install_id:
            raise HTTPException(status_code=400, detail="install_id is required")

        rollout_config = load_network_rollout_config(session=s)
        client_policy = app_first_service.build_client_policy(
            session=s,
            user=user,
            install_id=install_id or None,
            carrier=_request_carrier_header(x_portal_carrier),
            rollout_config=rollout_config,
        )
        transport_profile = (
            str(payload.transport_profile or client_policy.get("transport_profile") or LEGACY_REALITY_FALLBACK).strip()
            or LEGACY_REALITY_FALLBACK
        )
        nodes = enabled_nodes(s)
        nodes_for_user = _nodes_for_user(user, nodes, session=s)
        smart_connect = _smart_connect_shortlist(
            session=s,
            user=user,
            nodes=nodes_for_user,
            transport_profile=transport_profile,
            rollout_config=rollout_config,
            profile_revision=str(payload.profile_revision or client_policy.get("profile_revision") or ""),
        )
        allowed_codes = {
            str(item.get("code") or "").strip().lower()
            for item in smart_connect.get("shortlist") or []
            if str(item.get("code") or "").strip()
        }
        accepted_samples: list[dict[str, int | str]] = []
        for sample in list(payload.samples or [])[:10]:
            code = str(sample.node_code or "").strip().lower()
            if not code or (allowed_codes and code not in allowed_codes):
                continue
            accepted_samples.append({"node_code": code, "rtt_ms": int(sample.rtt_ms)})

        selected_node_code = str(payload.selected_node_code or "").strip().lower()
        if selected_node_code and allowed_codes and selected_node_code not in allowed_codes:
            selected_node_code = ""
        previous_node_code = str(payload.previous_node_code or "").strip().lower()
        if previous_node_code and allowed_codes and previous_node_code not in allowed_codes:
            previous_node_code = ""

        event_meta = {
            "install_id": install_id,
            "profile_revision": str(payload.profile_revision or client_policy.get("profile_revision") or ""),
            "transport_profile": transport_profile,
            "selected_node_code": selected_node_code or None,
            "previous_node_code": previous_node_code or None,
            "stickiness_applied": bool(payload.stickiness_applied),
            "carrier": _request_carrier_header(x_portal_carrier) or None,
            "platform": str(getattr(user, "app_platform", "") or "").strip() or None,
            "samples": accepted_samples,
        }
        s.add(
            Event(
                tg_id=int(user.tg_id),
                event_name=SMART_CONNECT_LATENCY_EVENT_NAME,
                source="app",
                session_id=install_id,
                meta_json=json.dumps(event_meta, ensure_ascii=False),
                created_at=_utcnow(),
            )
        )
        s.commit()
        return {
            "ok": True,
            "accepted_samples": len(accepted_samples),
            "preferred_node_code": selected_node_code or None,
        }
    finally:
        s.close()


def _client_warp_context(request: Request, x_telegram_init_data: str) -> tuple[Any, User, str, dict[str, Any]]:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    user = s.query(User).filter(User.tg_id == tg_id).first()
    if not user:
        s.close()
        raise HTTPException(status_code=404, detail="User not found")
    install_id = str(getattr(user, "app_install_id", "") or "").strip()
    rollout_config = load_network_rollout_config(session=s)
    policy = public_warp_policy_for_user(
        s,
        user=user,
        install_id=install_id,
        rollout_config=rollout_config,
    )
    return s, user, install_id, policy


def _warp_env_int(
    name: str,
    *,
    default: int,
    minimum: int = 0,
    maximum: int = 1_000_000,
) -> int:
    try:
        value = int(str(os.getenv(name) or "").strip() or default)
    except Exception:
        value = default
    return max(minimum, min(maximum, value))


def _warp_event_count(
    session,
    *,
    user: User,
    install_id: str | None,
    event_name: str,
    window_seconds: int,
) -> int:
    since = _utcnow() - timedelta(seconds=max(1, int(window_seconds)))
    query = (
        session.query(func.count(WarpEvent.id))
        .filter(WarpEvent.tg_id == int(user.tg_id))
        .filter(WarpEvent.event_name == str(event_name))
        .filter(WarpEvent.created_at >= since)
    )
    clean_install = str(install_id or "").strip()
    if clean_install:
        query = query.filter(WarpEvent.install_id == clean_install)
    return int(query.scalar() or 0)


def _warp_rate_limit_detail(*, code: str, limit: int, window_seconds: int) -> dict[str, Any]:
    return {
        "code": code,
        "limit": int(limit),
        "window_seconds": int(window_seconds),
        "retry_after_seconds": int(window_seconds),
        "message": "WARP action is rate limited. Try again later.",
    }


def _warp_material_provision_limit() -> tuple[int, int]:
    return (
        _warp_env_int(
            "WARP_MATERIAL_PROVISION_LIMIT_PER_HOUR",
            default=6,
            minimum=0,
            maximum=1000,
        ),
        3600,
    )


def _warp_rotation_limit() -> tuple[int, int]:
    return (
        _warp_env_int(
            "WARP_ROTATION_LIMIT_PER_HOUR",
            default=3,
            minimum=0,
            maximum=1000,
        ),
        3600,
    )


def _warp_not_ready_detail(status: dict[str, Any]) -> dict[str, Any]:
    return {
        "code": "warp_not_runtime_ready",
        "state": str(status.get("state") or "not_ready"),
        "policy_state": str(status.get("policy_state") or ""),
        "message": "Extended protection is not ready for this device yet.",
    }


@app.get("/api/client/warp/status")
async def client_warp_status(request: Request, x_telegram_init_data: str = Header(default="")) -> dict[str, Any]:
    s, user, install_id, policy = _client_warp_context(request, x_telegram_init_data)
    try:
        return build_warp_status(s, user=user, install_id=install_id, policy=policy)
    finally:
        s.close()


@app.post("/api/client/warp/consent")
async def client_warp_consent(
    payload: ClientWarpConsentIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    s, user, install_id, policy = _client_warp_context(request, x_telegram_init_data)
    try:
        status = build_warp_status(s, user=user, install_id=install_id, policy=policy)
        if not bool(status.get("runtime_ready")):
            raise HTTPException(status_code=409, detail=_warp_not_ready_detail(status))
        if not payload.consent:
            record_warp_event(
                s,
                user=user,
                install_id=install_id,
                policy=policy,
                event_name="revoke",
                state="revoked",
                reason_code=payload.reason_code or "consent_declined",
                consented=False,
                meta={"source": "app_consent", "action": "decline"},
            )
        else:
            record_warp_event(
                s,
                user=user,
                install_id=install_id,
                policy=policy,
                event_name="consent",
                state="consented",
                reason_code=payload.reason_code or "user_consented",
                consented=True,
                meta={"source": "app_consent", "action": "accept"},
            )
        s.commit()
        return build_warp_status(s, user=user, install_id=install_id, policy=policy)
    finally:
        s.close()


@app.post("/api/client/warp/revoke")
async def client_warp_revoke(
    payload: ClientWarpActionIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    s, user, install_id, policy = _client_warp_context(request, x_telegram_init_data)
    try:
        status = build_warp_status(s, user=user, install_id=install_id, policy=policy)
        record_warp_event(
            s,
            user=user,
            install_id=install_id,
            policy=policy,
            event_name="revoke",
            state="revoked",
            reason_code=payload.reason_code or "user_disabled",
            consented=False,
            meta={"source": "app_action", "previous_state": status.get("state")},
        )
        revoke_warp_material(s, user=user, install_id=install_id)
        s.commit()
        return build_warp_status(s, user=user, install_id=install_id, policy=policy)
    finally:
        s.close()


@app.post("/api/client/warp/rotate")
async def client_warp_rotate(
    payload: ClientWarpActionIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    s, user, install_id, policy = _client_warp_context(request, x_telegram_init_data)
    try:
        status = build_warp_status(s, user=user, install_id=install_id, policy=policy)
        if not bool(status.get("runtime_ready")):
            raise HTTPException(status_code=409, detail=_warp_not_ready_detail(status))
        limit, window_seconds = _warp_rotation_limit()
        if limit and _warp_event_count(
            s,
            user=user,
            install_id=install_id,
            event_name="rotate_requested",
            window_seconds=window_seconds,
        ) >= limit:
            record_warp_event(
                s,
                user=user,
                install_id=install_id,
                policy=policy,
                event_name="rotate_rate_limited",
                state="rate_limited",
                reason_code=payload.reason_code or "rotation_limit",
                consented=bool(status.get("consented")),
                meta={"source": "app_action", "previous_state": status.get("state")},
            )
            s.commit()
            raise HTTPException(
                status_code=429,
                detail=_warp_rate_limit_detail(
                    code="warp_rotation_rate_limited",
                    limit=limit,
                    window_seconds=window_seconds,
                ),
            )
        record_warp_event(
            s,
            user=user,
            install_id=install_id,
            policy=policy,
            event_name="rotate_requested",
            state="rotation_requested",
            reason_code=payload.reason_code or "user_requested",
            consented=bool(status.get("consented")),
            meta={"source": "app_action", "previous_state": status.get("state")},
        )
        mark_warp_material_rotation_requested(s, user=user, install_id=install_id)
        s.commit()
        return build_warp_status(s, user=user, install_id=install_id, policy=policy)
    finally:
        s.close()


@app.post("/api/client/warp/events")
async def client_warp_events(
    payload: ClientWarpRuntimeEventIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    s, user, install_id, policy = _client_warp_context(request, x_telegram_init_data)
    try:
        status = build_warp_status(s, user=user, install_id=install_id, policy=policy)
        event_meta = dict(payload.meta or {})
        if payload.message:
            event_meta["message"] = payload.message
        record_warp_event(
            s,
            user=user,
            install_id=install_id,
            policy=policy,
            event_name=payload.event_name,
            state=payload.state or str(status.get("state") or "not_ready"),
            reason_code=payload.reason_code,
            consented=bool(status.get("consented")),
            meta=event_meta,
        )
        s.commit()
        return {"ok": True, **build_warp_status(s, user=user, install_id=install_id, policy=policy)}
    finally:
        s.close()


@app.post("/api/client/telegram/link")
async def client_telegram_link_start(request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        linked_id = _linked_telegram_id(user)
        linked_username = str(getattr(user, "linked_telegram_username", "") or "").strip()
        start_code = ""
        if not linked_id:
            start_code = app_first_service.create_app_telegram_start_code(
                s,
                account_tg_id=int(user.tg_id),
                now=_utcnow(),
            )
        s.commit()
        bot_username = (BOT_USERNAME or "pokrov_vpnbot").lstrip("@")
        channel_username = (PUBLIC_CHANNEL or "").lstrip("@").strip()
        return {
            "ok": True,
            "linked": bool(linked_id),
            "linked_telegram_id": linked_id or None,
            "linked_telegram_username": linked_username or None,
            "start_code": start_code,
            "bot_url": f"https://t.me/{bot_username}?start={start_code}" if start_code else f"https://t.me/{bot_username}",
            "channel_url": f"https://t.me/{channel_username}" if channel_username else None,
        }
    finally:
        s.close()


@app.api_route("/pay/success", methods=["GET", "POST"])
async def pay_success(request: Request):
    if request.method == "POST":
        return {"ok": True, "status": "success"}
    action = _public_webapp_url()
    return HTMLResponse(
        content=_payment_page_html(
            title="Оплата подтверждена",
            message="Платеж получен. Доступ обновится автоматически, а статус появится в личном кабинете.",
            action_url=action,
            action_label="Открыть кабинет",
        )
    )


@app.api_route("/pay/fail", methods=["GET", "POST"])
async def pay_fail(request: Request):
    if request.method == "POST":
        return {"ok": False, "status": "failed"}
    action = _public_checkout_url() or (f"https://t.me/{BOT_USERNAME}" if BOT_USERNAME else "/")
    return HTMLResponse(
        content=_payment_page_html(
            title="Платеж не завершен",
            message="Платеж не прошел. Можно повторить попытку или обратиться в службу заботы через Telegram.",
            action_url=action,
            action_label="Повторить оплату",
        )
    )


@app.api_route("/api/payments/result/{provider}", methods=["POST", "GET"])
async def payment_result(provider: str, request: Request) -> dict:
    return await _handle_payment_callback(provider=provider, event_type="result", request=request)


@app.api_route("/api/payments/refund/{provider}", methods=["POST", "GET"])
async def payment_refund(provider: str, request: Request) -> dict:
    return await _handle_payment_callback(provider=provider, event_type="refund", request=request)


@app.api_route("/api/payments/chargeback/{provider}", methods=["POST", "GET"])
async def payment_chargeback(provider: str, request: Request) -> dict:
    return await _handle_payment_callback(provider=provider, event_type="chargeback", request=request)


@app.api_route("/api/payments/freekassa/notify", methods=["POST", "GET"])
async def payment_freekassa_notify(request: Request):
    result = await _handle_payment_callback(provider="freekassa", event_type="result", request=request)
    if request.method == "POST" and bool(result.get("ok")):
        # Freekassa SCI expects a plain "YES" acknowledgment.
        return PlainTextResponse("YES")
    return result


def _normalize_lavatop_payment_method(raw: str | None) -> tuple[str, str, str]:
    method = str(raw or "").strip().lower()
    if not method:
        return "", "", ""
    aliases = {
        "sbp": "sbp",
        "сбп": "sbp",
        "pay2me_sbp": "sbp",
        "card": "card",
        "cards": "card",
        "bank_card": "card",
        "bankcard": "card",
        "mir": "card",
        "карта": "card",
        "карты": "card",
    }
    method = aliases.get(method, method)
    if method == "sbp":
        return "sbp", "PAY2ME", "SBP"
    if method == "card":
        return "card", "SMART_GLOCAL", "CARD"
    raise HTTPException(status_code=400, detail="Unsupported payment method")


async def _rub_create_order_internal(
    *,
    request: Request,
    provider: str,
    tg_id: int | None,
    source: str,
    plan_code: str,
    campaign: str = "",
    promo_code: str = "",
    currency: str = "RUB",
    buyer_email: str | None = None,
    payment_method: str | None = None,
    consume_pending_discount: bool = False,
    acquisition_handle: str | None = None,
) -> RubOrderActionOut:
    _ensure_checkout_runtime_ready()
    provider = _normalize_provider(provider)
    if not provider:
        enabled_codes = [str(row.get("code") or "") for row in enabled_public_provider_catalog()]
        provider = str(enabled_codes[0] if enabled_codes else "").strip().lower()
    if not provider:
        raise HTTPException(status_code=503, detail="No RUB payment providers are enabled")
    if provider not in PAYMENT_PROVIDER_WHITELIST:
        raise HTTPException(status_code=400, detail="Unsupported payment provider")
    _ensure_checkout_provider_enabled(provider)
    if provider != "freekassa" and not provider_is_configured(provider):
        raise HTTPException(status_code=503, detail=f"{provider} is not configured")
    payment_method_choice, lavatop_payment_provider, lavatop_payment_method = ("", "", "")
    if provider == "lavatop":
        payment_method_choice, lavatop_payment_provider, lavatop_payment_method = _normalize_lavatop_payment_method(payment_method)
    normalized_tg_id = int(tg_id or 0)
    buyer_email_norm = ""
    if normalized_tg_id <= 0:
        try:
            buyer_email_norm = validate_email_input(str(buyer_email or ""))
        except InvalidEmailInputError as exc:
            raise HTTPException(status_code=400, detail="Valid buyer_email is required") from exc
    s = SessionLocal()
    try:
        plan = _resolve_plan_config(s=s, code=plan_code)
        if not plan:
            raise HTTPException(status_code=400, detail="Unknown plan for RUB checkout")
        user = None
        if normalized_tg_id > 0:
            user = s.query(User).filter(User.tg_id == int(normalized_tg_id)).first()
        if normalized_tg_id > 0 and not user:
            raise HTTPException(status_code=404, detail="User not found")
        acquisition_handoff = None
        acquisition_row = None
        attribution_snapshot = None
        if acquisition_handle:
            try:
                acquisition_handoff, acquisition_row, attribution_snapshot = consume_acquisition_handoff(
                    s,
                    raw_handle=acquisition_handle,
                    expected_purpose="checkout",
                    bound_tg_id=(int(normalized_tg_id) if normalized_tg_id > 0 else None),
                    bound_account_id=(str(getattr(user, "account_id", "") or "") or None) if user else None,
                    now=_utcnow(),
                )
            except AcquisitionError as exc:
                raise HTTPException(status_code=exc.status_code, detail=exc.code) from exc
            source = str(attribution_snapshot["last"].get("source") or source or "unknown")[:32]
            campaign = str(attribution_snapshot["last"].get("campaign") or "")[:64]
        normalized_plan_code = str(plan.get("code") or plan_code).strip().lower()
        if not public_provider_is_configured_for_plan(provider, normalized_plan_code):
            raise HTTPException(status_code=503, detail=f"{provider} plan is not configured for public RUB checkout")
        _ensure_start99_available_for_order(
            s=s,
            user=user,
            buyer_email_norm=buyer_email_norm,
            plan_code=normalized_plan_code,
        )
        base_amount = max(0, int(plan.get("amount_rub") or 0))
        final_amount = base_amount
        discount_pct = 0
        discount_applied = False
        discount_allowed = normalized_plan_code != "start_99"
        requested_promo = (promo_code or "").strip().upper()[:32]
        effective_promo = ""
        pending_code = (getattr(user, "pending_discount_code", "") or "").strip().upper()[:20] if user else ""
        pending_pct = int(getattr(user, "pending_discount_pct", 0) or 0) if user else 0
        direct_discount_pct = 0
        direct_discount_code = ""
        direct_discount_source = ""
        referral_discount_eligible = bool(
            discount_allowed
            and user
            and getattr(user, "referrer_id", None)
            and not _has_successful_provider_payment(s=s, user=user)
        )
        working_amount = int(base_amount)
        if referral_discount_eligible and working_amount > 0:
            working_amount = max(1, int(round(working_amount * 0.8)))
        if discount_allowed and pending_pct > 0:
            working_amount, _ = _price_with_pending_discount(amount_rub=working_amount, pending_pct=pending_pct)
            if pending_code:
                effective_promo = pending_code[:32]
        elif discount_allowed and requested_promo:
            direct_discount_pct, direct_discount_code, direct_discount_source = _checkout_discount_code_preview_pct(
                s=s,
                promo_code=requested_promo,
            )
            if direct_discount_pct > 0:
                working_amount, _ = _price_with_pending_discount(amount_rub=working_amount, pending_pct=direct_discount_pct)
                effective_promo = direct_discount_code[:32]
        final_amount = max(1, int(working_amount)) if base_amount > 0 else 0
        discount_applied = bool(base_amount > 0 and final_amount < base_amount)
        discount_pct = int(round((1.0 - (float(final_amount) / float(base_amount))) * 100)) if discount_applied else 0
        amount_rub = float(final_amount)
        duration_days = max(1, int(plan.get("duration_days") or plan.get("days") or 30))
        entitlement_snapshot = {
            "plan_code": normalized_plan_code,
            "duration_days": duration_days,
            "amount_rub": f"{Decimal(str(amount_rub)):.2f}",
            "currency": (currency or "RUB").strip().upper()[:16] or "RUB",
            "source": str(source or "").strip().lower(),
        }
        order_prefix = "fk" if provider == "freekassa" else provider[:12]
        order_subject = str(normalized_tg_id if normalized_tg_id > 0 else "public")
        order_id = f"{order_prefix}_{source}_{order_subject}_{int(time.time())}_{secrets.token_hex(4)}"
        if acquisition_handoff is not None:
            acquisition_handoff.bound_order_id = order_id
        plan_label = str(plan.get("label") or RUB_PLAN_LABELS.get(plan_code) or plan_code).strip()
        fulfillment_mode = "account_extend" if normalized_tg_id > 0 else "access_key_email"
        ext = ExternalOrder(
            order_id=order_id,
            tg_id=int(normalized_tg_id) if normalized_tg_id > 0 else None,
            provider=provider,
            plan_code=normalized_plan_code,
            source=source,
            campaign=(campaign or "").strip()[:64] or None,
            acquisition_session_id=(str(acquisition_row.id) if acquisition_row is not None else None),
            promo_code=effective_promo or None,
            amount=float(amount_rub),
            currency=(currency or "RUB").strip().upper()[:16] or "RUB",
            status="created",
            meta_json=_serialize_external_order_meta(
                {
                    "source": source,
                    "campaign": campaign,
                    "attribution_snapshot": attribution_snapshot,
                    "requested_promo_code": requested_promo or None,
                    "promo_code": effective_promo,
                    "tg_id": int(normalized_tg_id) if normalized_tg_id > 0 else None,
                    "buyer_email": buyer_email_norm or None,
                    "plan_code": normalized_plan_code,
                    "provider": provider,
                    "payment_method": payment_method_choice or None,
                    "lavatop_payment_provider": lavatop_payment_provider or None,
                    "lavatop_payment_method": lavatop_payment_method or None,
                    "plan_label": plan_label,
                    "entitlement_snapshot": entitlement_snapshot,
                    "fulfillment": {
                        "mode": fulfillment_mode,
                        "status": "pending_payment",
                    },
                    "pricing": {
                        "base_amount_rub": int(base_amount),
                        "final_amount_rub": int(final_amount),
                        "discount_pct": int(discount_pct),
                        "discount_applied": bool(discount_applied),
                        "pending_discount_code": pending_code or None,
                        "direct_discount_pct": int(direct_discount_pct),
                        "direct_discount_code": direct_discount_code or None,
                        "direct_discount_source": direct_discount_source or None,
                        "referral_discount_eligible": bool(referral_discount_eligible),
                    },
                },
            ),
            created_at=_utcnow(),
        )
        s.add(ext)
        if normalized_tg_id <= 0:
            ensure_pending_claim(
                s,
                provider=provider,
                order_id=order_id,
                buyer_email=buyer_email_norm,
                plan_code=normalized_plan_code,
                duration_days=max(1, int(plan.get("duration_days") or plan.get("days") or 30)),
                now=ext.created_at,
            )
        if user and consume_pending_discount and discount_applied:
            user.pending_discount_pct = None
            user.pending_discount_code = None
            user.pending_discount_set_at = None
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()

    req_data = {
        "provider": provider,
        "amount": float(amount_rub),
        "currency": "RUB",
        "tg_id": int(normalized_tg_id) if normalized_tg_id > 0 else None,
        "buyer_email": buyer_email_norm or None,
        "plan_code": normalized_plan_code,
        "plan_label": plan_label,
        "campaign": campaign or "",
        "requested_promo_code": requested_promo or "",
        "promo_code": effective_promo or "",
        "source": source,
        "payment_method": payment_method_choice or "",
        "lavatop_payment_provider": lavatop_payment_provider or "",
        "lavatop_payment_method": lavatop_payment_method or "",
        "discount_pct": int(discount_pct),
        "base_amount_rub": int(base_amount),
        "final_amount_rub": int(final_amount),
        "referral_discount_eligible": bool(referral_discount_eligible),
        "client_ip": _fk_client_ip(request),
    }
    if provider == "freekassa":
        payment_url = _build_freekassa_payment_url(
            source=source,
            order_id=order_id,
            amount_rub=amount_rub,
            currency="RUB",
            tg_id=int(normalized_tg_id),
            plan_code=normalized_plan_code,
            campaign=campaign or "",
            promo_code=effective_promo or "",
        )
        remote_response: dict[str, Any] = {"payment_url": payment_url}
    else:
        payment = await create_rub_payment(
            provider=provider,
            order_id=order_id,
            amount_rub=amount_rub,
            currency="RUB",
            description=f"POKROV {plan_label}",
            success_url=_pay_success_url(provider),
            fail_url=_pay_fail_url(provider),
            result_url=_provider_result_url(provider),
            refund_url=_provider_refund_url(provider),
            chargeback_url=_provider_chargeback_url(provider),
            logo_url=(os.getenv("PAYMENT_LOGO_URL") or "").strip(),
            custom={
                **({"tg_id": int(normalized_tg_id)} if normalized_tg_id > 0 else {}),
                **({"email": buyer_email_norm} if buyer_email_norm else {}),
                "plan_code": normalized_plan_code,
                "provider": provider,
                "source": source,
                "campaign": campaign or "",
                "promo_code": effective_promo or "",
                "payment_method": payment_method_choice or "",
                "lavatop_payment_provider": lavatop_payment_provider or "",
                "lavatop_payment_method": lavatop_payment_method or "",
            },
        )
        payment_url = str(payment.get("payment_url") or "").strip()
        remote_response = dict(payment.get("remote") or {})

    s = SessionLocal()
    try:
        row = s.query(ExternalOrder).filter(ExternalOrder.provider == provider, ExternalOrder.order_id == order_id).first()
        if row:
            row.status = "pending"
            meta = _external_order_meta(row)
            meta.update(
                {
                    "request": req_data,
                    "response": {"payment_url": payment_url, "remote": remote_response},
                    "entitlement_snapshot": entitlement_snapshot,
                    "pricing": {
                        "base_amount_rub": int(base_amount),
                        "final_amount_rub": int(final_amount),
                        "discount_pct": int(discount_pct),
                        "discount_applied": bool(discount_applied),
                        "requested_promo_code": requested_promo or None,
                        "promo_code": effective_promo or None,
                        "pending_discount_code": pending_code or None,
                        "direct_discount_pct": int(direct_discount_pct),
                        "direct_discount_code": direct_discount_code or None,
                        "direct_discount_source": direct_discount_source or None,
                    },
                    "fulfillment": {
                        "mode": fulfillment_mode,
                        "status": "pending_payment",
                        "buyer_email": buyer_email_norm or None,
                    },
                    "payment_method": {
                        "choice": payment_method_choice or None,
                        "lavatop_payment_provider": lavatop_payment_provider or None,
                        "lavatop_payment_method": lavatop_payment_method or None,
                    },
                }
            )
            _set_external_order_meta(row, meta)
            s.commit()
    finally:
        s.close()

    return RubOrderActionOut(
        ok=True,
        provider=provider,
        provider_label=(PROVIDER_META.get(provider).label if provider in PROVIDER_META else provider.title()),
        order_id=order_id,
        payment_url=payment_url or None,
        amount_rub=float(amount_rub),
        currency="RUB",
        status="pending",
        widget_enabled=bool(CHECKOUT_WIDGET_ENABLED),
        discount_applied=bool(discount_applied),
        base_amount_rub=float(base_amount),
        discount_pct=int(discount_pct),
    )


@app.get("/api/payments/providers", response_model=RubProvidersOut)
async def rub_payment_providers() -> RubProvidersOut:
    return _public_checkout_provider_state()


@app.post("/api/payments/orders/create", response_model=RubOrderActionOut)
async def rub_order_create(
    payload: RubOrderCreateIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> RubOrderActionOut:
    _ensure_checkout_runtime_ready()
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    actor_tg_id = int(auth_user.get("id", 0))
    source = (payload.source or "site").strip().lower()
    if source not in {"site", "bot"}:
        source = "site"

    tg_id = int(payload.tg_id or actor_tg_id)
    if tg_id != actor_tg_id and not _is_admin_tg(actor_tg_id):
        raise HTTPException(status_code=403, detail="Access denied")
    return await _rub_create_order_internal(
        request=request,
        provider=_normalize_provider(payload.provider),
        tg_id=int(tg_id),
        source=source,
        plan_code=(payload.plan_code or "").strip().lower(),
        campaign=_sanitize_deeplink_token(payload.campaign, max_len=64, uppercase=False),
        promo_code=_sanitize_deeplink_token(payload.promo_code, max_len=20, uppercase=True),
        currency=(payload.currency or "RUB").strip().upper(),
        payment_method=payload.payment_method,
        consume_pending_discount=False,
        acquisition_handle=payload.acquisition_handle,
    )


@app.post("/api/payments/orders/create-public", response_model=RubOrderActionOut)
async def rub_order_create_public(
    payload: RubPublicOrderCreateIn,
    request: Request,
) -> RubOrderActionOut:
    _ensure_checkout_runtime_ready()
    ticket_raw = str(payload.checkout_ticket or "").strip()
    public_subject = ticket_raw or str(payload.buyer_email or payload.source or "").strip()[:96]
    public_identity = hashlib.sha256(public_subject.encode("utf-8")).hexdigest()[:32] if public_subject else ""
    _enforce_beta_rate_limit("public_order_create", request, identity=public_identity)
    ticket_payload = _parse_checkout_ticket(ticket_raw) if ticket_raw else None
    request_plan_code = (payload.plan_code or "").strip().lower()
    if ticket_raw and not ticket_payload:
        raise HTTPException(status_code=401, detail="Invalid or expired checkout ticket")

    if ticket_payload:
        tg_id = int(ticket_payload.get("tg_id") or 0)
        if tg_id <= 0:
            raise HTTPException(status_code=400, detail="Checkout ticket has no user binding")
        source = str(ticket_payload.get("source") or "bot").strip().lower()
        if source not in {"site", "bot"}:
            source = "bot"
        ticket_plan_code = str(ticket_payload.get("plan_code") or "").strip().lower()
        if ticket_plan_code and request_plan_code and request_plan_code != ticket_plan_code:
            raise HTTPException(status_code=400, detail="Plan code does not match checkout ticket")
        plan_code = (ticket_plan_code or request_plan_code or "").strip().lower()
        campaign = _sanitize_deeplink_token(str(ticket_payload.get("campaign_key") or ""), max_len=64, uppercase=False)
        promo_code = _sanitize_deeplink_token(str(ticket_payload.get("promo_code") or ""), max_len=20, uppercase=True)
        buyer_email = None
    else:
        tg_id = None
        source = str(payload.source or "site").strip().lower()
        if source not in {"site"}:
            source = "site"
        plan_code = request_plan_code
        campaign = _sanitize_deeplink_token(payload.campaign, max_len=64, uppercase=False)
        promo_code = _sanitize_deeplink_token(payload.promo_code, max_len=20, uppercase=True)
        buyer_email = str(payload.buyer_email or "").strip()

    return await _rub_create_order_internal(
        request=request,
        provider=_normalize_provider(payload.provider),
        tg_id=tg_id,
        source=source,
        plan_code=plan_code,
        campaign=campaign,
        promo_code=promo_code,
        currency=(payload.currency or "RUB").strip().upper(),
        buyer_email=buyer_email,
        payment_method=payload.payment_method,
        consume_pending_discount=False,
        acquisition_handle=payload.acquisition_handle,
    )


@app.post("/api/payments/start-99-eligibility")
async def start99_eligibility(
    payload: Start99EligibilityIn,
    request: Request,
) -> dict[str, Any]:
    ticket_raw = str(payload.checkout_ticket or "").strip()
    identity = hashlib.sha256(ticket_raw.encode("utf-8")).hexdigest()[:32]
    _enforce_beta_rate_limit("start99_eligibility", request, identity=identity)
    ticket_payload = _parse_checkout_ticket(ticket_raw)
    if not ticket_payload:
        raise HTTPException(status_code=401, detail="Invalid or expired checkout ticket")
    tg_id = int(ticket_payload.get("tg_id") or 0)
    if tg_id <= 0:
        raise HTTPException(status_code=400, detail="Checkout ticket has no user binding")
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == tg_id).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        eligible = not _has_successful_provider_payment(s=s, user=user)
        replacement_ticket = None
        if not eligible:
            replacement_ticket = _create_checkout_ticket(
                tg_id=tg_id,
                plan_code="1_month",
                promo_code=_sanitize_deeplink_token(
                    str(ticket_payload.get("promo_code") or ""),
                    max_len=20,
                    uppercase=True,
                ),
                campaign_key=_sanitize_deeplink_token(
                    str(ticket_payload.get("campaign_key") or ""),
                    max_len=64,
                    uppercase=False,
                ),
                source=str(ticket_payload.get("source") or "bot").strip().lower(),
            )
        return {
            "known": True,
            "eligible": eligible,
            "reason": None if eligible else "start_99_already_used",
            "replacement_plan": "1_month",
            "replacement_checkout_ticket": replacement_ticket,
        }
    finally:
        s.close()


@app.post("/api/payments/freekassa/orders/create", response_model=RubOrderActionOut)
async def freekassa_order_create(
    payload: FreekassaOrderCreateIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> RubOrderActionOut:
    generic = RubOrderCreateIn(
        provider="freekassa",
        plan_code=payload.plan_code,
        source=payload.source,
        tg_id=payload.tg_id,
        campaign=payload.campaign,
        promo_code=payload.promo_code,
        currency=payload.currency,
        payment_method=payload.payment_method,
        acquisition_handle=payload.acquisition_handle,
    )
    return await rub_order_create(generic, request=request, x_telegram_init_data=x_telegram_init_data)


@app.post("/api/payments/freekassa/orders/create-public", response_model=RubOrderActionOut)
async def freekassa_order_create_public(
    payload: FreekassaPublicOrderCreateIn,
    request: Request,
) -> RubOrderActionOut:
    generic = RubPublicOrderCreateIn(
        provider="freekassa",
        plan_code=payload.plan_code,
        checkout_ticket=payload.checkout_ticket,
        currency=payload.currency,
        payment_method=payload.payment_method,
        acquisition_handle=payload.acquisition_handle,
    )
    return await rub_order_create_public(generic, request=request)


@app.get("/api/payments/freekassa/orders/{order_id}")
async def freekassa_order_get(
    order_id: str,
    request: Request,
    source: str = "site",
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    actor_tg_id = int(auth_user.get("id", 0))
    local_status = ""
    request_source = (source or "").strip().lower() or "site"
    s = SessionLocal()
    try:
        row = s.query(ExternalOrder).filter(ExternalOrder.provider == "freekassa", ExternalOrder.order_id == str(order_id)).first()
        if not row:
            raise HTTPException(status_code=404, detail="Order not found")
        if int(row.tg_id or 0) != actor_tg_id and not _is_admin_tg(actor_tg_id):
            raise HTTPException(status_code=403, detail="Access denied")
        local_status = str(row.status or "")
        if str(row.source or "").strip():
            request_source = str(row.source).strip().lower()
    finally:
        s.close()
    remote = await _freekassa_api_request(source=request_source, method="orders", data={"orderId": order_id})
    return {"ok": True, "provider": "freekassa", "order_id": order_id, "status_local": local_status, "remote": remote}


@app.post("/api/payments/freekassa/orders/{order_id}/refund")
async def freekassa_order_refund(
    order_id: str,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    _require_admin(x_telegram_init_data, request=request)
    s = SessionLocal()
    try:
        row = s.query(ExternalOrder).filter(ExternalOrder.provider == "freekassa", ExternalOrder.order_id == str(order_id)).first()
        if not row:
            raise HTTPException(status_code=404, detail="Order not found")
        amount = float(row.amount or 0.0)
        source = str(row.source or "site")
    finally:
        s.close()
    remote = await _freekassa_api_request(
        source=source,
        method="orders/refund",
        data={"orderId": order_id, "amount": amount},
    )
    return {"ok": True, "provider": "freekassa", "order_id": order_id, "remote": remote}


@app.get("/api/payments/freekassa/currencies")
async def freekassa_currencies(
    request: Request,
    source: str = "site",
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    _require_auth_user(x_telegram_init_data, request=request)
    remote = await _freekassa_api_request(source=source, method="currencies", data={})
    return {"ok": True, "provider": "freekassa", "remote": remote}


@app.get("/api/payments/freekassa/currencies/{currency}/status")
async def freekassa_currency_status(
    currency: str,
    request: Request,
    source: str = "site",
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    _require_auth_user(x_telegram_init_data, request=request)
    remote = await _freekassa_api_request(
        source=source,
        method="currencies/status",
        data={"currency": str(currency or "").strip().upper()},
    )
    return {"ok": True, "provider": "freekassa", "currency": str(currency or "").upper(), "remote": remote}
