import importlib
import asyncio
import os
import sys
import tempfile
import unittest
import uuid
from datetime import timedelta
from pathlib import Path
from unittest import mock

from sqlalchemy.exc import IntegrityError


class WorkerRetentionTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        portal_dir = str(repo_root / "portal_bot")
        if portal_dir not in sys.path:
            sys.path.insert(0, portal_dir)

        self._saved_env: dict[str, str | None] = {}
        for key in (
            "DATABASE_URL",
            "BOT_TOKEN",
            "PUBLIC_CHANNEL",
            "RU_PROBE_RETENTION_DAYS",
            "RU_PROBE_HEARTBEAT_RETENTION_DAYS",
        ):
            self._saved_env[key] = os.environ.get(key)

        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = (repo_root / f"portal_api_test_{uuid.uuid4().hex}.db").resolve()
        os.environ["DATABASE_URL"] = f"sqlite:///{self.db_path.as_posix()}"
        os.environ["BOT_TOKEN"] = "test_bot_token_123"
        os.environ["PUBLIC_CHANNEL"] = "pokrov_vpn"
        os.environ["RU_PROBE_RETENTION_DAYS"] = "180"
        os.environ["RU_PROBE_HEARTBEAT_RETENTION_DAYS"] = "30"

        for mod_name in ("config", "db", "worker"):
            if mod_name in sys.modules:
                importlib.reload(sys.modules[mod_name])

        self.db = importlib.import_module("db")
        importlib.reload(self.db)
        self.db.init_db()

        self.worker = importlib.import_module("worker")
        importlib.reload(self.worker)
        self.worker._TEMPLATE_CACHE.clear()

    def tearDown(self) -> None:
        try:
            self.db.engine.dispose()
        except Exception:
            pass
        for key, value in self._saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        try:
            self.db_path.unlink(missing_ok=True)
        except Exception:
            pass
        self._tmp.cleanup()

    def test_expiry_stage_windows(self) -> None:
        self.assertEqual(self.worker._expiry_stage(timedelta(days=2, hours=12)), "t3")
        self.assertEqual(self.worker._expiry_stage(timedelta(hours=23)), "t1")
        self.assertEqual(self.worker._expiry_stage(timedelta(minutes=30)), "t0")
        self.assertEqual(self.worker._expiry_stage(timedelta(days=5)), "")

    def test_ab_variant_is_stable(self) -> None:
        v1 = self.worker._ab_variant_for_user(tg_id=1001, flow_key="expiry_t3")
        v2 = self.worker._ab_variant_for_user(tg_id=1001, flow_key="expiry_t3")
        self.assertEqual(v1, v2)
        self.assertIn(v1, {"a", "b"})

    def test_retention_text_uses_template_override(self) -> None:
        from models import Template

        s = self.db.SessionLocal()
        try:
            row = s.query(Template).filter(Template.key == "retention_t1_a").first()
            if row is None:
                row = Template(key="retention_t1_a", text="Custom T-1 message until {expiry_date}")
                s.add(row)
            else:
                row.text = "Custom T-1 message until {expiry_date}"
            s.commit()
        finally:
            s.close()

        self.worker._TEMPLATE_CACHE.clear()
        text = self.worker._retention_text(flow="t1", variant="a", context={"expiry_date": "2026-02-20"})
        self.assertIn("Custom T-1 message", text)
        self.assertIn("2026-02-20", text)

    def test_retention_buttons_include_channel_for_welcome(self) -> None:
        buttons = self.worker._retention_buttons(flow="welcome", variant="a")
        self.assertGreaterEqual(len(buttons), 2)
        self.assertIn("t.me/pokrov_vpn", str(buttons[1][0].get("url") or ""))

    def test_channel_membership_reason_normalization(self) -> None:
        self.assertEqual(self.worker._normalize_channel_membership_reason("left"), "not_member")
        self.assertEqual(self.worker._normalize_channel_membership_reason("kicked"), "not_member")
        self.assertEqual(self.worker._normalize_channel_membership_reason("not_member"), "not_member")
        self.assertEqual(self.worker._normalize_channel_membership_reason("telegram_http_error"), "telegram_http_error")

    def test_get_chat_member_maps_chat_not_found_from_non_200_response(self) -> None:
        class _FakeResponse:
            status = 400

            async def json(self, content_type=None):
                return {
                    "ok": False,
                    "error_code": 400,
                    "description": "Bad Request: chat not found",
                }

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

        class _FakeSession:
            def post(self, *args, **kwargs):
                return _FakeResponse()

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

        with mock.patch.object(self.worker.aiohttp, "ClientSession", return_value=_FakeSession()):
            is_member, reason = self.worker.asyncio.run(
                self.worker._telegram_get_chat_member("pokrov_vpn", 123456789)
            )

        self.assertFalse(is_member)
        self.assertEqual(reason, "channel_not_found")

    def test_get_chat_member_classifies_timeout_without_revocation_reason(self) -> None:
        class _FakeSession:
            def post(self, *args, **kwargs):
                raise self_module.worker.asyncio.TimeoutError()

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

        self_module = self
        with mock.patch.object(self.worker.aiohttp, "ClientSession", return_value=_FakeSession()):
            is_member, reason = self.worker.asyncio.run(
                self.worker._telegram_get_chat_member("pokrov_vpn", 123456789)
            )

        self.assertFalse(is_member)
        self.assertEqual(reason, "telegram_timeout")

    def test_referral_queue_does_not_double_increment_already_counted_referral(self) -> None:
        from models import Event, ReferralBonusQueue, User

        now = self.worker._utcnow()
        s = self.db.SessionLocal()
        try:
            s.add(
                User(
                    tg_id=2001,
                    username="referrer",
                    uuid=str(uuid.uuid4()),
                    email="ref_2001",
                    sub_type="PAID",
                    is_active=True,
                    referral_count=1,
                    expiry_at=now + timedelta(days=30),
                    tos_accepted=True,
                )
            )
            s.add(
                User(
                    tg_id=2002,
                    username="referred",
                    uuid=str(uuid.uuid4()),
                    email="ref_2002",
                    sub_type="PAID",
                    is_active=True,
                    expiry_at=now + timedelta(days=30),
                    tos_accepted=True,
                )
            )
            s.add(Event(tg_id=2002, event_name="connected_ok", source="test", created_at=now))
            s.add(
                ReferralBonusQueue(
                    order_id="order-2002",
                    referrer_tg_id=2001,
                    referred_tg_id=2002,
                    queued_at=now - timedelta(hours=30),
                    ready_at=now - timedelta(hours=1),
                    status="pending",
                    meta='{"source":"payment_callback","counted":true}',
                )
            )
            s.commit()
        finally:
            s.close()

        out = self.worker._process_referral_bonus_queue(limit=10)
        self.assertEqual(int(out.get("rewarded") or 0), 1)

        s = self.db.SessionLocal()
        try:
            referrer = s.query(User).filter_by(tg_id=2001).first()
            self.assertIsNotNone(referrer)
            self.assertEqual(int(referrer.referral_count or 0), 1)
        finally:
            s.close()

    def test_mark_campaign_sent_once_returns_false_on_duplicate_insert_race(self) -> None:
        class _FakeSession:
            def __init__(self) -> None:
                self.rollback_called = False
                self.closed = False

            def add(self, _row) -> None:
                return None

            def commit(self) -> None:
                raise IntegrityError("insert", {}, Exception("duplicate"))

            def rollback(self) -> None:
                self.rollback_called = True

            def close(self) -> None:
                self.closed = True

        fake = _FakeSession()
        old_session_factory = self.worker.SessionLocal
        self.worker.SessionLocal = lambda: fake
        try:
            out = self.worker._mark_campaign_sent_once(tg_id=1001, campaign_key="welcome_chain_v1")
        finally:
            self.worker.SessionLocal = old_session_factory

        self.assertFalse(out)
        self.assertTrue(fake.rollback_called)
        self.assertTrue(fake.closed)

    def test_observer_retention_job_runs_cleanup_and_commits(self) -> None:
        cleanup_calls: list[int] = []

        class _FakeSession:
            def __init__(self) -> None:
                self.committed = False
                self.closed = False

            def commit(self) -> None:
                self.committed = True

            def rollback(self) -> None:
                return None

            def close(self) -> None:
                self.closed = True

        fake_session = _FakeSession()

        async def _stop_after_first_sleep(_seconds: float) -> None:
            raise asyncio.CancelledError()

        def _cleanup(*, s, now=None):
            cleanup_calls.append(1)
            self.assertIs(s, fake_session)
            return {"deleted_daily": 0}

        with mock.patch.object(self.worker, "SessionLocal", return_value=fake_session), \
             mock.patch.object(self.worker, "cleanup_observer_retention", side_effect=_cleanup), \
             mock.patch.object(self.worker.asyncio, "sleep", side_effect=_stop_after_first_sleep):
            with self.assertRaises(asyncio.CancelledError):
                self.worker.asyncio.run(self.worker.observer_retention_job())

        self.assertEqual(cleanup_calls, [1])
        self.assertTrue(fake_session.committed)
        self.assertTrue(fake_session.closed)

    def test_telemetry_retention_cleans_ru_tables_and_preserves_holds(self) -> None:
        from models import (
            InternalIngestNonce,
            RuProbeRun,
            RuProbeTargetResult,
            RuProbeUploaderHeartbeat,
        )

        now = self.worker._utcnow()
        session = self.db.SessionLocal()
        try:
            old_unheld = RuProbeRun(
                run_id=str(uuid.uuid4()),
                schema_version=2,
                origin="ru",
                probe_host_id="mini",
                probe_host_label="Мини",
                runner_version="2.0.0",
                started_at=now - timedelta(days=181, minutes=2),
                finished_at=now - timedelta(days=181),
                received_at=now - timedelta(days=181),
                manifest_revision="a" * 64,
                execution_status="completed",
                environment_verdict="available",
                release_verdict="pass",
                current_eligible=True,
                google_reachable=True,
                xhttp_alive=False,
                hysteria_alive=False,
                artifact_sha256="b" * 64,
                ingest_key_id="ru-test",
                retention_hold=False,
            )
            old_held = RuProbeRun(
                run_id=str(uuid.uuid4()),
                schema_version=2,
                origin="ru",
                probe_host_id="mini",
                probe_host_label="Мини",
                runner_version="2.0.0",
                started_at=now - timedelta(days=181, minutes=2),
                finished_at=now - timedelta(days=181),
                received_at=now - timedelta(days=181),
                manifest_revision="c" * 64,
                execution_status="completed",
                environment_verdict="available",
                release_verdict="pass",
                current_eligible=True,
                google_reachable=True,
                xhttp_alive=False,
                hysteria_alive=False,
                artifact_sha256="d" * 64,
                ingest_key_id="ru-test",
                retention_hold=True,
                retention_hold_reason="release_evidence:candidate-1",
                retention_held_at=now - timedelta(days=180),
            )
            session.add_all([old_unheld, old_held])
            session.flush()
            for run in (old_unheld, old_held):
                session.add(
                    RuProbeTargetResult(
                        run_db_id=run.id,
                        target_id="node:nl",
                        target_kind="delivery_node",
                        scope="release_required",
                        node_code="nl",
                        endpoint_fingerprint="e" * 64,
                        endpoint_host="nl.example.test",
                        endpoint_port=443,
                        requested_address_families_json=["ipv4"],
                        transport_metadata_json={},
                        transport_profile="legacy_reality_fallback",
                        probe_mode="delivery_tls",
                        observed_at=run.finished_at,
                        overall_status="pass",
                        current_eligible=True,
                        dns_status="pass",
                        tcp_status="pass",
                        tls_status="pass",
                        http_large_body_status="not_applicable",
                        transport_handshake_status="not_applicable",
                        ipv4_status="pass",
                        ipv6_status="not_applicable",
                        reported_transport_handshake_status="not_applicable",
                        reported_transport_classification="ok",
                    )
                )
            session.add_all(
                [
                    InternalIngestNonce(
                        key_scope="ru_probe:ingest",
                        key_id="ru-test",
                        nonce_hash="1" * 64,
                        request_path="/api/internal/probes/ru-origin/runs",
                        request_timestamp=now - timedelta(days=2),
                        body_sha256="2" * 64,
                        expires_at=now - timedelta(minutes=1),
                        created_at=now - timedelta(days=2),
                    ),
                    RuProbeUploaderHeartbeat(
                        probe_host_id="mini",
                        observed_at=now - timedelta(days=31),
                        received_at=now - timedelta(days=31),
                        service_version="2.0.0",
                        pending_count=0,
                        blocked_count=0,
                        quarantine_count=0,
                        archive_write_ok=True,
                        disk_free_bytes=1_000_000,
                        disk_state="ok",
                        ingest_key_id="ru-test",
                    ),
                    RuProbeUploaderHeartbeat(
                        probe_host_id="mini",
                        observed_at=now - timedelta(days=29),
                        received_at=now - timedelta(days=29),
                        service_version="2.0.0",
                        pending_count=0,
                        blocked_count=0,
                        quarantine_count=0,
                        archive_write_ok=True,
                        disk_free_bytes=1_000_000,
                        disk_state="ok",
                        ingest_key_id="ru-test",
                    ),
                ]
            )
            session.commit()

            deleted = self.worker.run_telemetry_retention_once(
                session=session,
                now=now,
            )
            session.commit()

            self.assertEqual(deleted["ru_probe_runs"], 1)
            self.assertEqual(deleted["internal_ingest_nonces"], 1)
            self.assertEqual(deleted["ru_probe_uploader_heartbeats"], 1)
            remaining_runs = session.query(RuProbeRun).all()
            self.assertEqual([row.id for row in remaining_runs], [old_held.id])
            remaining_targets = session.query(RuProbeTargetResult).all()
            self.assertEqual([row.run_db_id for row in remaining_targets], [old_held.id])
            self.assertEqual(session.query(InternalIngestNonce).count(), 0)
            self.assertEqual(session.query(RuProbeUploaderHeartbeat).count(), 1)
        finally:
            session.close()

    def test_admin_action_intent_retention_only_deletes_old_unaudited_prepared_rows(self) -> None:
        from models import AdminActionIntent, AdminAudit

        now = self.worker._utcnow()
        session = self.db.SessionLocal()
        try:
            audit = AdminAudit(
                actor_tg_id=9999,
                action="admin_node_disable",
                meta='{"outcome":"completed"}',
                created_at=now - timedelta(days=20),
            )
            session.add(audit)
            session.flush()

            def make_intent(
                status: str,
                *,
                age_days: int,
                audit_id: int | None = None,
            ) -> AdminActionIntent:
                intent_id = str(uuid.uuid4())
                terminal = status in {"completed", "failed", "uncertain"}
                result = (
                    f'{{"action_intent_id":"{intent_id}","status":"{status}"}}'
                    if terminal
                    else None
                )
                return AdminActionIntent(
                    id=intent_id,
                    actor_tg_id=9999,
                    action="node.disable",
                    target_type="node",
                    target_id="nl",
                    risk_level="L3",
                    executor_kind="db",
                    canonical_payload_json='{"force":false}',
                    payload_hash="a" * 64,
                    preview_snapshot_json='{"summary":"safe"}',
                    snapshot_hash="b" * 64,
                    confirmation_challenge_kind="exact_node_code",
                    confirmation_challenge_hash="c" * 64,
                    entity_version_hash="d" * 64,
                    status=status,
                    expires_at=now - timedelta(days=age_days),
                    consumed_at=now - timedelta(days=age_days) if terminal else None,
                    client_idempotency_key=str(uuid.uuid4()) if terminal else None,
                    result_code=status if terminal else None,
                    result_summary_json=result,
                    result_hash="e" * 64 if terminal else None,
                    admin_audit_id=audit_id,
                    created_at=now - timedelta(days=age_days, minutes=10),
                    updated_at=now - timedelta(days=age_days),
                )

            old_prepared = make_intent("prepared", age_days=8)
            old_expired = make_intent("expired", age_days=8)
            recent_prepared = make_intent("prepared", age_days=6)
            audited_expired = make_intent(
                "expired",
                age_days=20,
                audit_id=int(audit.id),
            )
            completed = make_intent(
                "completed",
                age_days=20,
                audit_id=int(audit.id),
            )
            failed = make_intent(
                "failed",
                age_days=20,
                audit_id=int(audit.id),
            )
            uncertain = make_intent(
                "uncertain",
                age_days=20,
                audit_id=int(audit.id),
            )
            expected_ids = {
                "old_prepared": str(old_prepared.id),
                "old_expired": str(old_expired.id),
                "recent_prepared": str(recent_prepared.id),
                "audited_expired": str(audited_expired.id),
                "completed": str(completed.id),
                "failed": str(failed.id),
                "uncertain": str(uncertain.id),
            }
            audit_id = int(audit.id)
            session.add_all(
                [
                    old_prepared,
                    old_expired,
                    recent_prepared,
                    audited_expired,
                    completed,
                    failed,
                    uncertain,
                ]
            )
            session.commit()

            deleted = self.worker.run_telemetry_retention_once(
                session=session,
                now=now,
            )
            session.commit()

            self.assertEqual(deleted["admin_action_intents"], 2)
            remaining_ids = {
                row.id for row in session.query(AdminActionIntent).all()
            }
            self.assertNotIn(expected_ids["old_prepared"], remaining_ids)
            self.assertNotIn(expected_ids["old_expired"], remaining_ids)
            self.assertEqual(
                remaining_ids,
                {
                    expected_ids["recent_prepared"],
                    expected_ids["audited_expired"],
                    expected_ids["completed"],
                    expected_ids["failed"],
                    expected_ids["uncertain"],
                },
            )
            self.assertEqual(session.query(AdminAudit).filter_by(id=audit_id).count(), 1)
        finally:
            session.close()


if __name__ == "__main__":
    unittest.main()
