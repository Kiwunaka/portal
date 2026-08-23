# ruff: noqa: F821
"""Authenticated opaque support-bundle upload routes.

These handlers accept bounded metadata and encrypted bytes only. Decryption,
archive handling and diagnostic payload parsing are worker-only concerns.
"""

from __future__ import annotations

import json

try:
    from .module_slices import bootstrap_slice
except ImportError:
    from module_slices import bootstrap_slice

bootstrap_slice(globals())

try:
    from . import support_bundle_upload_service as support_bundle_uploads
    from . import support_mode_service
except ImportError:
    import support_bundle_upload_service as support_bundle_uploads
    import support_mode_service


SUPPORT_BUNDLE_QUARANTINE_DIR = Path(
    os.getenv("POKROV_SUPPORT_BUNDLE_QUARANTINE_DIR")
    or (Path(__file__).resolve().parent / "private" / "support-bundle-quarantine")
).resolve()
_UPLOAD_TICKET_INPUT_FIELDS = frozenset(
    {
        "anonymous_nonce",
        "bundle_id",
        "case_subject",
        "case_summary",
        "content_type",
        "idempotency_key",
        "sha256",
        "size_bytes",
        "ticket_id",
    }
)
_UPLOAD_TICKET_REQUIRED_FIELDS = frozenset(
    {
        "bundle_id",
        "case_summary",
        "content_type",
        "idempotency_key",
        "sha256",
        "size_bytes",
    }
)
_SUPPORT_MODE_REDEEM_FIELDS = frozenset(
    {"app_version", "build_number", "code", "platform"}
)


def _support_bundle_http_exception(
    error: support_bundle_uploads.SupportBundleUploadError,
) -> HTTPException:
    return HTTPException(
        status_code=error.status_code,
        detail={
            "code": error.code,
            "message": "Support bundle request rejected.",
        },
    )


def _reject_support_recovery_scope(auth_user: Mapping[str, Any]) -> None:
    if _auth_user_is_recovery_scope(dict(auth_user)):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "recovery_scope_forbidden",
                "message": "Recovery session cannot upload diagnostic bundles.",
            },
        )


def _support_owner_context(
    session,
    *,
    user: User,
    auth_user: Mapping[str, Any],
    anonymous_nonce: object,
) -> tuple[int, str | None, str]:
    _reject_support_recovery_scope(auth_user)
    tg_id = int(auth_user.get("id") or getattr(user, "tg_id", 0) or 0)
    account_id = resolve_support_account_id(
        session,
        account_id=str(
            auth_user.get("account_id") or getattr(user, "account_id", "") or ""
        ).strip()
        or None,
        user_tg_id=tg_id,
    )
    binding = support_bundle_uploads.owner_binding_hash(
        owner_tg_id=tg_id,
        owner_account_id=account_id,
        anonymous_nonce=anonymous_nonce,
    )
    return tg_id, account_id, binding


def _support_upload_signing_secret() -> str:
    return str(os.getenv("POKROV_SUPPORT_UPLOAD_TICKET_SECRET") or "")


def _support_ticket_response(
    result: support_bundle_uploads.SupportBundleTicketResult,
) -> dict[str, Any]:
    return {
        "ok": True,
        "upload_id": result.upload_id,
        "ticket_id": result.ticket_id,
        "upload_ticket": result.upload_ticket,
        "expires_at": result.expires_at.replace(tzinfo=timezone.utc).isoformat(),
        "next_offset": result.next_offset,
        "status": result.status,
        "object_name": result.object_name,
        "failure_code": result.failure_code,
        "chunk_size_bytes": support_bundle_uploads.MAX_CHUNK_BYTES,
    }


async def _read_support_ticket_input(request: Request) -> dict[str, Any]:
    raw = await _read_limited_request_body(
        request,
        max_bytes=4096,
        scope="Support bundle ticket",
    )
    try:
        value = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=support_bundle_uploads._reject_duplicate_keys,
        )
    except (UnicodeError, ValueError):
        raise support_bundle_uploads.SupportBundleUploadError(
            "invalid_ticket_request"
        ) from None
    if (
        not isinstance(value, dict)
        or not _UPLOAD_TICKET_REQUIRED_FIELDS.issubset(value)
        or not set(value).issubset(_UPLOAD_TICKET_INPUT_FIELDS)
    ):
        raise support_bundle_uploads.SupportBundleUploadError("invalid_ticket_request")
    return value


async def _read_support_mode_redeem_input(request: Request) -> dict[str, Any]:
    raw = await _read_limited_request_body(
        request,
        max_bytes=1024,
        scope="Support mode redeem",
    )
    try:
        value = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=support_bundle_uploads._reject_duplicate_keys,
        )
    except (UnicodeError, ValueError):
        raise support_mode_service.SupportModeError(
            "support_mode_redeem_shape_invalid"
        ) from None
    if not isinstance(value, dict) or set(value) != _SUPPORT_MODE_REDEEM_FIELDS:
        raise support_mode_service.SupportModeError(
            "support_mode_redeem_shape_invalid"
        )
    return value


@app.get("/api/client/support/bundles/key-set")
async def get_support_bundle_key_set(
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    session, _user, auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        _reject_support_recovery_scope(auth_user)
        _enforce_beta_rate_limit(
            "support_bundle_key_set",
            request,
            identity=f"tg:{int(auth_user.get('id') or 0)}",
        )
        return support_bundle_uploads.load_configured_signed_key_set(
            str(os.getenv("POKROV_SUPPORT_SIGNED_KEY_SET_JSON") or "")
        )
    except support_bundle_uploads.SupportBundleUploadError as error:
        raise _support_bundle_http_exception(error) from None
    finally:
        session.close()


@app.post("/api/client/support/mode/redeem")
async def redeem_support_mode_policy(
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    session, user, auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        _enforce_beta_rate_limit(
            "support_mode_redeem",
            request,
            identity=f"tg:{int(auth_user.get('id') or 0)}",
        )
        payload = await _read_support_mode_redeem_input(request)
        tg_id, account_id, _binding = _support_owner_context(
            session,
            user=user,
            auth_user=auth_user,
            anonymous_nonce=None,
        )
        redeemed = support_mode_service.redeem_support_mode(
            session,
            activation_code=payload["code"],
            owner_tg_id=tg_id,
            owner_account_id=account_id,
            platform=payload["platform"],
            app_version=payload["app_version"],
            build_number=payload["build_number"],
        )
        session.commit()
        return {
            "ok": True,
            "policy": redeemed.signed_policy,
            "expires_at": redeemed.row.expires_at.replace(
                tzinfo=timezone.utc
            ).isoformat(),
        }
    except support_mode_service.SupportModeError as error:
        session.rollback()
        raise HTTPException(
            status_code=error.status_code,
            detail={
                "code": error.code,
                "message": "Support mode request rejected.",
            },
        ) from None
    except HTTPException:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise HTTPException(
            status_code=503,
            detail={
                "code": "support_mode_unavailable",
                "message": "Service unavailable.",
            },
        ) from None
    finally:
        session.close()


@app.post("/api/client/support/bundles/upload-tickets")
async def issue_support_bundle_upload_ticket(
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    session, user, auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        _enforce_beta_rate_limit(
            "support_bundle_ticket",
            request,
            identity=f"tg:{int(auth_user.get('id') or 0)}",
        )
        payload = await _read_support_ticket_input(request)
        tg_id, account_id, owner_binding = _support_owner_context(
            session,
            user=user,
            auth_user=auth_user,
            anonymous_nonce=payload.get("anonymous_nonce"),
        )
        selected_ticket_id = payload.get("ticket_id")
        if selected_ticket_id is not None:
            try:
                selected_ticket_id = int(selected_ticket_id)
            except (TypeError, ValueError):
                raise support_bundle_uploads.SupportBundleUploadError(
                    "ticket_required"
                ) from None
            ticket = get_ticket_by_id(session, selected_ticket_id)
            if ticket is None:
                raise support_bundle_uploads.SupportBundleUploadError(
                    "ticket_not_found",
                    status_code=404,
                )
            if not can_access_ticket(
                ticket,
                tg_id,
                int(Settings.ADMIN_ID or 0),
                account_id=account_id,
            ):
                raise support_bundle_uploads.SupportBundleUploadError(
                    "ticket_access_denied",
                    status_code=403,
                )
        spec = support_bundle_uploads.normalize_upload_spec(
            idempotency_key=payload.get("idempotency_key"),
            bundle_id=payload.get("bundle_id"),
            size_bytes=payload.get("size_bytes"),
            sha256=payload.get("sha256"),
            content_type=payload.get("content_type"),
            case_summary=payload.get("case_summary"),
            case_subject=payload.get("case_subject", "Диагностика POKROV"),
        )
        result = support_bundle_uploads.issue_upload_ticket(
            session,
            owner_tg_id=tg_id,
            owner_account_id=account_id,
            owner_binding=owner_binding,
            spec=spec,
            signing_secret=_support_upload_signing_secret(),
            ticket_id=selected_ticket_id,
        )
        session.commit()
        return _support_ticket_response(result)
    except support_bundle_uploads.SupportBundleUploadError as error:
        session.rollback()
        raise _support_bundle_http_exception(error) from None
    except HTTPException:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise HTTPException(
            status_code=503,
            detail={
                "code": "support_bundle_unavailable",
                "message": "Service unavailable.",
            },
        ) from None
    finally:
        session.close()


@app.put("/api/client/support/bundles/uploads/{upload_id}/chunks", status_code=202)
async def upload_support_bundle_chunk(
    upload_id: str,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
    x_pokrov_upload_ticket: str = Header(default=""),
    x_pokrov_chunk_offset: str = Header(default=""),
    x_pokrov_chunk_sha256: str = Header(default=""),
    x_pokrov_anonymous_nonce: str = Header(default=""),
) -> dict[str, Any]:
    session, user, auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        _enforce_beta_rate_limit(
            "support_bundle_chunk",
            request,
            identity=f"tg:{int(auth_user.get('id') or 0)}",
        )
        _tg_id, _account_id, owner_binding = _support_owner_context(
            session,
            user=user,
            auth_user=auth_user,
            anonymous_nonce=x_pokrov_anonymous_nonce,
        )
        content_type = (
            str(request.headers.get("content-type") or "").split(";", 1)[0].lower()
        )
        if content_type != "application/octet-stream":
            raise support_bundle_uploads.SupportBundleUploadError(
                "unsupported_chunk_content_type",
                status_code=415,
            )
        chunk = await _read_limited_request_body(
            request,
            max_bytes=support_bundle_uploads.MAX_CHUNK_BYTES,
            scope="Support bundle chunk",
        )
        result = support_bundle_uploads.accept_upload_chunk(
            session,
            upload_id=upload_id,
            upload_ticket=x_pokrov_upload_ticket,
            owner_binding=owner_binding,
            offset_bytes=x_pokrov_chunk_offset,
            chunk_sha256=x_pokrov_chunk_sha256,
            chunk=chunk,
            signing_secret=_support_upload_signing_secret(),
            quarantine_root=SUPPORT_BUNDLE_QUARANTINE_DIR,
        )
        session.commit()
        return {
            "ok": True,
            "upload_id": result.upload_id,
            "next_offset": result.next_offset,
            "complete": result.complete,
            "repeated": result.repeated,
        }
    except support_bundle_uploads.SupportBundleUploadError as error:
        session.rollback()
        raise _support_bundle_http_exception(error) from None
    except HTTPException:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise HTTPException(
            status_code=503,
            detail={
                "code": "support_bundle_unavailable",
                "message": "Service unavailable.",
            },
        ) from None
    finally:
        session.close()


def _support_upload_owner_and_ticket(
    session,
    *,
    user: User,
    auth_user: Mapping[str, Any],
    anonymous_nonce: object,
    upload_id: str,
    upload_ticket: str,
):
    _tg_id, _account_id, owner_binding = _support_owner_context(
        session,
        user=user,
        auth_user=auth_user,
        anonymous_nonce=anonymous_nonce,
    )
    return support_bundle_uploads.get_upload_status(
        session,
        upload_id=upload_id,
        upload_ticket=upload_ticket,
        owner_binding=owner_binding,
        signing_secret=_support_upload_signing_secret(),
    )


@app.get("/api/client/support/bundles/uploads/{upload_id}")
async def get_support_bundle_upload_status(
    upload_id: str,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
    x_pokrov_upload_ticket: str = Header(default=""),
    x_pokrov_anonymous_nonce: str = Header(default=""),
) -> dict[str, Any]:
    session, user, auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        _enforce_beta_rate_limit(
            "support_bundle_status",
            request,
            identity=f"tg:{int(auth_user.get('id') or 0)}",
        )
        result = _support_upload_owner_and_ticket(
            session,
            user=user,
            auth_user=auth_user,
            anonymous_nonce=x_pokrov_anonymous_nonce,
            upload_id=upload_id,
            upload_ticket=x_pokrov_upload_ticket,
        )
        return _support_ticket_response(result)
    except support_bundle_uploads.SupportBundleUploadError as error:
        raise _support_bundle_http_exception(error) from None
    finally:
        session.close()


@app.post("/api/client/support/bundles/uploads/{upload_id}/complete", status_code=202)
async def complete_support_bundle_upload(
    upload_id: str,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
    x_pokrov_upload_ticket: str = Header(default=""),
    x_pokrov_anonymous_nonce: str = Header(default=""),
) -> dict[str, Any]:
    session, user, auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        _enforce_beta_rate_limit(
            "support_bundle_complete",
            request,
            identity=f"tg:{int(auth_user.get('id') or 0)}",
        )
        _tg_id, _account_id, owner_binding = _support_owner_context(
            session,
            user=user,
            auth_user=auth_user,
            anonymous_nonce=x_pokrov_anonymous_nonce,
        )
        row = support_bundle_uploads.complete_upload(
            session,
            upload_id=upload_id,
            upload_ticket=x_pokrov_upload_ticket,
            owner_binding=owner_binding,
            signing_secret=_support_upload_signing_secret(),
        )
        session.commit()
        return {
            "ok": True,
            "upload_id": row.upload_id,
            "ticket_id": int(row.ticket_id),
            "status": row.status,
            "next_offset": int(row.received_size_bytes),
        }
    except support_bundle_uploads.SupportBundleUploadError as error:
        session.rollback()
        raise _support_bundle_http_exception(error) from None
    except HTTPException:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise HTTPException(
            status_code=503,
            detail={
                "code": "support_bundle_unavailable",
                "message": "Service unavailable.",
            },
        ) from None
    finally:
        session.close()
