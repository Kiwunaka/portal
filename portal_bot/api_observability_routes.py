"""Privacy-bounded operational observability API routes."""

from __future__ import annotations

try:
    from .module_slices import bootstrap_slice
except ImportError:
    from module_slices import bootstrap_slice

bootstrap_slice(globals())

try:
    from . import observability_ingest as release_health_ingest_service
    from . import release_health_baseline_service
    from .models import ReleaseHealthEvent, ReleaseHealthIngestCounter
    from .request_correlation import request_correlation_from_request
except ImportError:
    import observability_ingest as release_health_ingest_service
    import release_health_baseline_service
    from models import ReleaseHealthEvent, ReleaseHealthIngestCounter
    from request_correlation import request_correlation_from_request


async def _read_release_health_body(request: Request, *, content_encoding: str) -> bytes:
    limit = release_health_ingest_service.encoded_body_limit(content_encoding)
    content_length = str(request.headers.get("content-length") or "").strip()
    if content_length:
        if re.fullmatch(r"[0-9]{1,12}", content_length) is None:
            raise release_health_ingest_service.ReleaseHealthIngestError(
                "invalid_content_length",
                status_code=400,
            )
        if int(content_length) > limit:
            raise release_health_ingest_service.ReleaseHealthIngestError(
                "encoded_body_too_large",
                status_code=413,
            )

    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > limit:
            raise release_health_ingest_service.ReleaseHealthIngestError(
                "encoded_body_too_large",
                status_code=413,
            )
    return bytes(body)


def _release_health_http_exception(
    error: release_health_ingest_service.ReleaseHealthIngestError,
) -> HTTPException:
    return HTTPException(
        status_code=error.status_code,
        detail={
            "code": error.catalog_code,
            "message": "Release-health batch rejected.",
            "reason": error.reason,
        },
    )


@app.post("/api/client/observability/release-health/batches", status_code=202)
async def ingest_client_release_health_batch(
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    session, user, _auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        _enforce_beta_rate_limit("release_health_ingest", request)
        content_type = str(request.headers.get("content-type") or "").split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            raise release_health_ingest_service.ReleaseHealthIngestError(
                "unsupported_content_type",
                status_code=415,
            )
        content_encoding = str(request.headers.get("content-encoding") or "identity").strip().lower()
        encoded_body = await _read_release_health_body(
            request,
            content_encoding=content_encoding,
        )
        decoded_body = release_health_ingest_service.decode_batch_body(
            encoded_body,
            content_encoding=content_encoding,
        )
        events = release_health_ingest_service.parse_release_health_batch(decoded_body)
        context = request_correlation_from_request(request)
        result = release_health_ingest_service.ingest_release_health_batch(
            session,
            events,
            request_context=context,
        )
        cohort_secret = str(os.getenv("RELEASE_HEALTH_COHORT_SECRET") or "")
        if cohort_secret and result.accepted_event_ids:
            accepted_ids = set(result.accepted_event_ids)
            release_health_baseline_service.record_cohort_contribution(
                session,
                (event for event in events if event.event_id in accepted_ids),
                contributor_key=(
                    str(getattr(user, "account_id", "") or "").strip()
                    or f"tg:{int(getattr(user, 'tg_id', 0) or 0)}"
                ),
                secret=cohort_secret,
            )
        session.commit()
        return {
            "ok": True,
            "accepted": result.accepted,
            "duplicates": result.duplicates,
            "request_id": context.request_id,
        }
    except release_health_ingest_service.ReleaseHealthIngestError as error:
        session.rollback()
        try:
            release_health_ingest_service.record_quarantine_counter(session, error.reason)
            session.commit()
        except Exception:
            session.rollback()
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "API-007",
                    "message": "Service temporarily unavailable.",
                },
            ) from None
        raise _release_health_http_exception(error) from None
    except HTTPException:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise HTTPException(
            status_code=503,
            detail={
                "code": "API-007",
                "message": "Service temporarily unavailable.",
            },
        ) from None
    finally:
        session.close()


@app.get("/api/client/observability/release-health/baseline")
async def client_release_health_baseline(
    request: Request,
    app_version: str,
    build_number: str,
    channel: str,
    candidate_label: str,
    git_revision: str,
    platform: str,
    architecture: str,
    core_abi: int | None = None,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    session, _user, _auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        _enforce_beta_rate_limit("release_health_baseline", request)
        identity = release_health_baseline_service.normalize_cohort_identity(
            {
                "app_version": app_version,
                "build_number": build_number,
                "channel": channel,
                "candidate_label": candidate_label,
                "git_revision": git_revision,
                "core_abi": core_abi,
                "platform": platform,
                "architecture": architecture,
            }
        )
        return release_health_baseline_service.client_baseline_snapshot(
            session,
            identity=identity,
            secret=os.getenv("RELEASE_HEALTH_COHORT_SECRET"),
        )
    except release_health_baseline_service.ReleaseHealthBaselineError as error:
        session.rollback()
        raise HTTPException(
            status_code=error.status_code,
            detail={
                "code": "API-007" if error.status_code >= 500 else "API-008",
                "message": "Release-health baseline unavailable.",
                "reason": error.reason,
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
                "code": "API-007",
                "message": "Service temporarily unavailable.",
            },
        ) from None
    finally:
        session.close()
