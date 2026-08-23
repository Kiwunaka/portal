# ruff: noqa: F821
"""Least-privilege operator views for release health and support evidence."""

from __future__ import annotations

import json

try:
    from .module_slices import bootstrap_slice
except ImportError:
    from module_slices import bootstrap_slice

bootstrap_slice(globals())

try:
    from . import operator_observability_service as operator_observability
except ImportError:
    import operator_observability_service as operator_observability


SUPPORT_BUNDLE_ACCEPTED_DIR = Path(
    os.getenv("POKROV_SUPPORT_BUNDLE_ACCEPTED_DIR")
    or (Path(__file__).resolve().parent / "private" / "support-bundle-accepted")
).resolve()


def _operator_error(
    error: operator_observability.OperatorObservabilityError,
) -> HTTPException:
    return HTTPException(
        status_code=error.status_code,
        detail={"code": error.code, "message": "Operator request rejected."},
    )


def _operator_actor(x_telegram_init_data: str) -> int:
    return int(_require_admin(x_telegram_init_data).get("id") or 0)


def _privileged_operator_ids() -> frozenset[int]:
    return operator_observability.parse_privileged_actor_ids(
        os.getenv("POKROV_SUPPORT_BUNDLE_L2_TG_IDS")
    )


async def _read_operator_json(
    request: Request, *, maximum_bytes: int = 8192
) -> dict[str, Any]:
    raw = await _read_limited_request_body(
        request,
        max_bytes=maximum_bytes,
        scope="Operator observability",
    )

    def reject_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result

    try:
        payload = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=reject_duplicates,
        )
    except (UnicodeError, ValueError):
        raise operator_observability.OperatorObservabilityError(
            "operator_payload_invalid"
        ) from None
    if not isinstance(payload, dict):
        raise operator_observability.OperatorObservabilityError(
            "operator_payload_invalid"
        )
    return payload


@app.get("/api/admin/observability/release-health")
async def admin_release_health_snapshot(
    hours: int = Query(default=24, ge=1, le=168),
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    _operator_actor(x_telegram_init_data)
    session = SessionLocal()
    try:
        return operator_observability.release_health_snapshot(session, hours=hours)
    finally:
        session.close()


@app.get("/api/admin/observability/known-issues")
async def admin_known_issues(
    candidate_label: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    _operator_actor(x_telegram_init_data)
    session = SessionLocal()
    try:
        issues = operator_observability.known_issues(
            session,
            candidate_label=candidate_label,
            status=status,
            limit=limit,
        )
        return {"issues": issues}
    except operator_observability.OperatorObservabilityError as error:
        raise _operator_error(error) from None
    finally:
        session.close()


@app.post("/api/admin/observability/known-issues")
async def admin_upsert_known_issue(
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    actor = _operator_actor(x_telegram_init_data)
    session = SessionLocal()
    try:
        payload = await _read_operator_json(request)
        issue = operator_observability.upsert_known_issue(
            session,
            actor_tg_id=actor,
            payload=payload,
        )
        session.commit()
        return {"ok": True, "issue": issue}
    except operator_observability.OperatorObservabilityError as error:
        session.rollback()
        raise _operator_error(error) from None
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@app.get("/api/admin/support/bundles/{upload_id}/summary")
async def admin_support_bundle_summary(
    upload_id: str,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    actor = _operator_actor(x_telegram_init_data)
    session = SessionLocal()
    try:
        privileged = _privileged_operator_ids()
        summary = operator_observability.support_bundle_summary(
            session,
            upload_id=upload_id,
        )
        return {
            "operator_role": operator_observability.operator_role(actor, privileged),
            "bundle": summary,
        }
    except operator_observability.OperatorObservabilityError as error:
        raise _operator_error(error) from None
    finally:
        session.close()


@app.post("/api/admin/support/bundles/{upload_id}/access-grants")
async def admin_issue_support_bundle_access_grant(
    upload_id: str,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    actor = _operator_actor(x_telegram_init_data)
    session = SessionLocal()
    try:
        payload = await _read_operator_json(request, maximum_bytes=1024)
        if set(payload) != {"reason_code"}:
            raise operator_observability.OperatorObservabilityError(
                "operator_payload_invalid"
            )
        grant = operator_observability.issue_bundle_access_grant(
            session,
            upload_id=upload_id,
            actor_tg_id=actor,
            privileged_ids=_privileged_operator_ids(),
            reason_code=payload["reason_code"],
        )
        session.commit()
        return {
            "ok": True,
            "upload_id": grant.upload_id,
            "ticket_id": grant.ticket_id,
            "access_grant": grant.token,
            "expires_at": grant.expires_at.replace(tzinfo=timezone.utc).isoformat(),
        }
    except operator_observability.OperatorObservabilityError as error:
        session.rollback()
        raise _operator_error(error) from None
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@app.get("/api/admin/support/bundles/{upload_id}/content")
async def admin_download_support_bundle_ciphertext(
    upload_id: str,
    x_pokrov_support_grant: str = Header(default=""),
    x_telegram_init_data: str = Header(default=""),
) -> FileResponse:
    actor = _operator_actor(x_telegram_init_data)
    session = SessionLocal()
    try:
        item = operator_observability.consume_bundle_access_grant(
            session,
            upload_id=upload_id,
            token=x_pokrov_support_grant,
            actor_tg_id=actor,
            privileged_ids=_privileged_operator_ids(),
            accepted_root=SUPPORT_BUNDLE_ACCEPTED_DIR,
        )
        session.commit()
        return FileResponse(
            path=item.path,
            media_type="application/octet-stream",
            filename=f"pokrov-support-{item.upload_id}.bin",
            headers={
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
            },
        )
    except operator_observability.OperatorObservabilityError as error:
        session.rollback()
        raise _operator_error(error) from None
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@app.post("/api/admin/support/bundles/{upload_id}/retention-hold")
async def admin_set_support_bundle_retention_hold(
    upload_id: str,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    actor = _operator_actor(x_telegram_init_data)
    session = SessionLocal()
    try:
        payload = await _read_operator_json(request, maximum_bytes=1024)
        if set(payload) != {"hold", "reason_code"} or type(payload["hold"]) is not bool:
            raise operator_observability.OperatorObservabilityError(
                "operator_payload_invalid"
            )
        summary = operator_observability.set_bundle_retention_hold(
            session,
            upload_id=upload_id,
            actor_tg_id=actor,
            privileged_ids=_privileged_operator_ids(),
            hold=payload["hold"],
            reason_code=payload["reason_code"],
        )
        session.commit()
        return {"ok": True, "bundle": summary}
    except operator_observability.OperatorObservabilityError as error:
        session.rollback()
        raise _operator_error(error) from None
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
