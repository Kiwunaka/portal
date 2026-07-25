import importlib
import asyncio
import inspect
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
        cleanup_env_keys = (
            "SUPPORT_ATTACHMENT_CLEANUP_INTERVAL_SECONDS",
            "SUPPORT_ATTACHMENT_CLEANUP_GRACE_SECONDS",
            "SUPPORT_ATTACHMENT_CLEANUP_BATCH_SIZE",
            "SUPPORT_ATTACHMENT_CLEANUP_SCAN_LIMIT",
        )
        for key in (
            "DATABASE_URL",
            "BOT_TOKEN",
            "PUBLIC_CHANNEL",
            *cleanup_env_keys,
            "RU_PROBE_RETENTION_DAYS",
            "RU_PROBE_HEARTBEAT_RETENTION_DAYS",
        ):
            self._saved_env[key] = os.environ.get(key)
        for key in cleanup_env_keys:
            os.environ.pop(key, None)

        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db_path = (Path(self._tmp.name) / f"portal_api_test_{uuid.uuid4().hex}.db").resolve()
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

    def test_channel_guard_uses_linked_identity_grace_and_rejoin_cancellation(self) -> None:
        from economy_service import grant_channel_bonus
        from models import Account, EntitlementGrant, User

        now = self.worker._utcnow()
        s = self.db.SessionLocal()
        try:
            account = Account(
                id=str(uuid.uuid4()),
                status="active",
                created_source="app_first",
                created_at=now,
                updated_at=now,
            )
            user = User(
                tg_id=9_000_000_007_001,
                account_id=account.id,
                username="guard-app-user",
                uuid=str(uuid.uuid4()),
                email="guard-app@example.test",
                sub_type="FREE",
                current_plan_code="trial",
                expiry_at=now + timedelta(days=5),
                is_active=True,
                tos_accepted=True,
                is_app_user=True,
                linked_telegram_id=7001,
                created_at=now,
            )
            s.add_all([account, user])
            s.flush()
            grant_channel_bonus(
                s,
                account_id=account.id,
                legacy_tg_id=user.tg_id,
                telegram_id=7001,
                now=now,
            )
            s.commit()
        finally:
            s.close()

        checked: list[int] = []

        async def not_member(_channel: str, telegram_id: int):
            checked.append(telegram_id)
            return False, "left"

        async def member(_channel: str, telegram_id: int):
            checked.append(telegram_id)
            return True, "member"

        first = asyncio.run(self.worker.channel_bonus_guard_once(is_channel_member=not_member, now=now))
        second = asyncio.run(
            self.worker.channel_bonus_guard_once(
                is_channel_member=member,
                now=now + timedelta(hours=23),
            )
        )

        self.assertEqual(first["grace_started"], 1)
        self.assertEqual(first["reversed"], 0)
        self.assertEqual(second["grace_cancelled"], 1)
        self.assertEqual(checked, [7001, 7001])
        s = self.db.SessionLocal()
        try:
            grant = s.query(EntitlementGrant).filter_by(source="telegram_channel").one()
            self.assertEqual(grant.status, "active")
        finally:
            s.close()

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
        from models import Event, ReferralBonusQueue, ReferralRelationship, User

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
        self.assertEqual(int(out.get("rewarded") or 0), 0)
        self.assertEqual(int(out.get("migrated") or 0), 1)

        s = self.db.SessionLocal()
        try:
            referrer = s.query(User).filter_by(tg_id=2001).first()
            referred = s.query(User).filter_by(tg_id=2002).one()
            legacy = s.query(ReferralBonusQueue).filter_by(order_id="order-2002").one()
            relationship = (
                s.query(ReferralRelationship)
                .filter_by(referred_account_id=str(referred.account_id))
                .one()
            )
            self.assertIsNotNone(referrer)
            self.assertEqual(int(referrer.referral_count or 0), 1)
            self.assertEqual(legacy.status, "superseded_account")
            self.assertEqual(relationship.referrer_account_id, referrer.account_id)
            self.assertEqual(relationship.first_payment_at, legacy.queued_at)
            self.assertEqual(relationship.hold_until, legacy.queued_at + timedelta(hours=72))
            self.assertEqual(relationship.status, "holding")
        finally:
            s.close()

    def test_referral_queue_keeps_missing_identity_row_pending_for_retry(self) -> None:
        from models import ReferralBonusQueue

        now = self.worker._utcnow()
        s = self.db.SessionLocal()
        try:
            s.add(
                ReferralBonusQueue(
                    order_id="missing-user-order",
                    referrer_tg_id=2991,
                    referred_tg_id=2992,
                    queued_at=now - timedelta(hours=10),
                    ready_at=now - timedelta(hours=1),
                    status="pending",
                    meta='{"source":"legacy_payment_callback"}',
                )
            )
            s.commit()
        finally:
            s.close()

        first = self.worker._process_referral_bonus_queue(limit=10)
        second = self.worker._process_referral_bonus_queue(limit=10)

        self.assertEqual(int(first.get("retryable") or 0), 1)
        self.assertEqual(int(second.get("retryable") or 0), 0)
        s = self.db.SessionLocal()
        try:
            row = s.query(ReferralBonusQueue).filter_by(order_id="missing-user-order").one()
            self.assertEqual(row.status, "pending")
            self.assertIsNone(row.processed_at)
            self.assertGreater(row.ready_at, now)
            self.assertIn('"account_migration_retry"', str(row.meta))
        finally:
            s.close()

    def test_referral_queue_retry_rows_do_not_starve_newer_valid_payment(self) -> None:
        from models import ReferralBonusQueue, User

        now = self.worker._utcnow()
        s = self.db.SessionLocal()
        try:
            s.add_all(
                [
                    ReferralBonusQueue(
                        order_id=f"conflict-{index}",
                        referrer_tg_id=3100 + index,
                        referred_tg_id=3200 + index,
                        queued_at=now - timedelta(hours=80),
                        ready_at=now - timedelta(hours=1),
                        status="pending",
                        meta=(
                            '{"account_migration_retry":{"attempts":"broken"}}'
                            if index == 0
                            else None
                        ),
                    )
                    for index in range(2)
                ]
            )
            s.add_all(
                [
                    User(
                        tg_id=tg_id,
                        username=f"valid_{tg_id}",
                        uuid=str(uuid.uuid4()),
                        email=f"valid_{tg_id}",
                        sub_type="PAID",
                        is_active=True,
                        expiry_at=now + timedelta(days=30),
                        tos_accepted=True,
                    )
                    for tg_id in (3301, 3302)
                ]
            )
            s.add(
                ReferralBonusQueue(
                    order_id="valid-after-conflicts",
                    referrer_tg_id=3301,
                    referred_tg_id=3302,
                    queued_at=now - timedelta(hours=80),
                    ready_at=now - timedelta(hours=1),
                    status="pending",
                )
            )
            s.commit()
        finally:
            s.close()

        first = self.worker._process_referral_bonus_queue(limit=2)
        second = self.worker._process_referral_bonus_queue(limit=2)

        self.assertEqual(first["retryable"], 2)
        self.assertEqual(second["migrated"], 1)
        s = self.db.SessionLocal()
        try:
            valid = s.query(ReferralBonusQueue).filter_by(order_id="valid-after-conflicts").one()
            conflicts = s.query(ReferralBonusQueue).filter(ReferralBonusQueue.order_id.like("conflict-%")).all()
            self.assertEqual(valid.status, "superseded_account")
            self.assertTrue(all(row.status == "pending" for row in conflicts))
        finally:
            s.close()

    def test_referral_worker_uses_normalized_hold_and_ignores_ux_activity_authority(self) -> None:
        from economy_service import create_referral_relationship, queue_first_payment_referrer_reward
        from models import Account, EntitlementGrant, Event, ReferralBonusQueue, ReferralRelationship, User

        now = self.worker._utcnow()
        s = self.db.SessionLocal()
        try:
            referrer_account = Account(
                id=str(uuid.uuid4()),
                status="active",
                created_source="test",
                created_at=now,
                updated_at=now,
            )
            referred_account = Account(
                id=str(uuid.uuid4()),
                status="active",
                created_source="test",
                created_at=now,
                updated_at=now,
            )
            referrer = User(
                tg_id=2101,
                account_id=referrer_account.id,
                username="normalized-referrer",
                uuid=str(uuid.uuid4()),
                email="normalized-referrer@example.test",
                sub_type="PAID",
                current_plan_code="1_month",
                is_active=True,
                expiry_at=now + timedelta(days=20),
                tos_accepted=True,
            )
            referred = User(
                tg_id=2102,
                account_id=referred_account.id,
                username="normalized-referred",
                uuid=str(uuid.uuid4()),
                email="normalized-referred@example.test",
                sub_type="PAID",
                current_plan_code="1_month",
                is_active=True,
                expiry_at=now + timedelta(days=30),
                tos_accepted=True,
                first_purchase_done=True,
            )
            s.add_all([referrer_account, referred_account, referrer, referred])
            s.flush()
            relationship = create_referral_relationship(
                s,
                referred_account_id=referred_account.id,
                referrer_account_id=referrer_account.id,
                source="test",
                now=now - timedelta(hours=80),
            )
            queue_first_payment_referrer_reward(
                s,
                referred_account_id=referred_account.id,
                payment_key="payment:normalized-2102",
                paid_at=now - timedelta(hours=73),
            )
            s.add(Event(tg_id=2102, event_name="clicked_connect", source="client", created_at=now))
            s.add(
                ReferralBonusQueue(
                    order_id="legacy-normalized-2102",
                    referrer_tg_id=2101,
                    referred_tg_id=2102,
                    queued_at=now - timedelta(hours=80),
                    ready_at=now - timedelta(hours=1),
                    status="pending",
                    meta='{"source":"legacy"}',
                )
            )
            s.commit()
            relationship_id = str(relationship.id)
        finally:
            s.close()

        first = self.worker._process_referral_bonus_queue(limit=10)
        replay = self.worker._process_referral_bonus_queue(limit=10)

        self.assertEqual(first["rewarded"], 1)
        self.assertEqual(replay["rewarded"], 0)
        s = self.db.SessionLocal()
        try:
            legacy = s.query(ReferralBonusQueue).filter_by(order_id="legacy-normalized-2102").one()
            relationship = s.query(ReferralRelationship).filter_by(id=relationship_id).one()
            self.assertEqual(legacy.status, "superseded_account")
            self.assertEqual(relationship.status, "rewarded")
            self.assertEqual(relationship.first_payment_at, legacy.queued_at)
            self.assertEqual(relationship.hold_until, legacy.queued_at + timedelta(hours=72))
            self.assertTrue(str(relationship.first_payment_key).startswith("payment:legacy-referral:"))
            self.assertEqual(s.query(EntitlementGrant).filter_by(source="referral_referrer").count(), 1)
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

    def test_referral_worker_rebuilds_paid_to_bonus_then_free_policy(self) -> None:
        from models import AccessKey, Account, EntitlementGrant, User

        now = self.worker._utcnow()
        s = self.db.SessionLocal()
        try:
            account = Account(
                id=str(uuid.uuid4()),
                status="active",
                created_source="test",
                created_at=now - timedelta(days=30),
                updated_at=now,
            )
            user = User(
                tg_id=2199,
                account_id=account.id,
                username="worker-projection",
                uuid=str(uuid.uuid4()),
                email="worker-projection@example.test",
                sub_type="PAID",
                current_plan_code="1_month",
                is_active=True,
                expiry_at=now + timedelta(days=4),
                first_purchase_done=True,
            )
            paid = EntitlementGrant(
                id=str(uuid.uuid4()),
                account_id=account.id,
                legacy_tg_id=user.tg_id,
                idempotency_key="worker-paid-boundary",
                source="provider_payment",
                status="active",
                grant_kind="paid_access",
                plan_code="1_month",
                starts_at=now - timedelta(days=30),
                expires_at=now - timedelta(seconds=1),
                activated_at=now - timedelta(days=30),
                duration_days=30,
                provider="lavatop",
                external_order_id="worker-paid-boundary",
                created_at=now - timedelta(days=30),
                updated_at=now,
            )
            bonus = EntitlementGrant(
                id=str(uuid.uuid4()),
                account_id=account.id,
                legacy_tg_id=user.tg_id,
                idempotency_key="worker-bonus-boundary",
                source="referral_friend",
                status="active",
                grant_kind="premium_bonus",
                plan_code="referral_friend",
                starts_at=now - timedelta(seconds=1),
                expires_at=now + timedelta(days=4),
                activated_at=now - timedelta(seconds=1),
                duration_days=5,
                provider="internal_economy",
                created_at=now - timedelta(seconds=1),
                updated_at=now,
            )
            key = AccessKey(
                tg_id=user.tg_id,
                key_uuid=str(uuid.uuid4()),
                panel_email="worker-projection@example.test",
                node_code="NL-free",
                pool_code="premium_pool",
                state="active",
                source="test",
                is_primary=True,
                created_at=now,
                updated_at=now,
            )
            s.add_all([account, user, paid, bonus, key])
            s.commit()
        finally:
            s.close()

        self.worker._process_referral_bonus_queue(limit=1)
        s = self.db.SessionLocal()
        try:
            user = s.query(User).filter_by(tg_id=2199).one()
            key = s.query(AccessKey).filter_by(tg_id=2199).one()
            bonus = s.query(EntitlementGrant).filter_by(idempotency_key="worker-bonus-boundary").one()
            self.assertEqual(user.sub_type, "BONUS")
            self.assertEqual(user.current_plan_code, "referral_friend")
            self.assertEqual(key.pool_code, "premium_pool")
            bonus.expires_at = self.worker._utcnow() - timedelta(seconds=1)
            s.commit()
        finally:
            s.close()

        self.worker._process_referral_bonus_queue(limit=1)
        s = self.db.SessionLocal()
        try:
            user = s.query(User).filter_by(tg_id=2199).one()
            key = s.query(AccessKey).filter_by(tg_id=2199).one()
            self.assertEqual(user.sub_type, "FREE")
            self.assertEqual(user.current_plan_code, "free_monthly")
            self.assertEqual(key.pool_code, "free_pool")
        finally:
            s.close()

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

    def test_support_attachment_cleanup_job_uses_bounded_defaults_and_is_supervised(self) -> None:
        cleanup_calls: list[tuple[object, dict]] = []
        sleep_calls: list[float] = []

        def _cleanup(session_factory, **kwargs):
            cleanup_calls.append((session_factory, kwargs))
            return {
                "expired_rows_removed": 0,
                "expired_files_removed": 0,
                "expired_files_missing": 0,
                "expired_files_preserved": 0,
                "temp_files_removed": 0,
                "orphan_files_removed": 0,
                "rows_missing_files": 0,
                "rows_scanned": 0,
                "malformed_rows_skipped": 0,
                "file_errors": 0,
                "file_candidates_selected": 0,
                "filesystem_entries_enumerated": 0,
                "file_window_wrapped": 0,
                "row_window_wrapped": 0,
            }

        async def _to_thread(func, *args, **kwargs):
            return func(*args, **kwargs)

        async def _stop_after_first_sleep(seconds: float) -> None:
            sleep_calls.append(seconds)
            raise asyncio.CancelledError()

        with mock.patch.object(self.worker, "reconcile_support_attachments", side_effect=_cleanup), \
             mock.patch.object(self.worker.asyncio, "to_thread", side_effect=_to_thread), \
             mock.patch.object(self.worker.asyncio, "sleep", side_effect=_stop_after_first_sleep):
            with self.assertRaises(asyncio.CancelledError):
                self.worker.asyncio.run(self.worker.support_attachment_cleanup_job())

        self.assertEqual(len(cleanup_calls), 1)
        self.assertIs(cleanup_calls[0][0], self.worker.SessionLocal)
        self.assertEqual(cleanup_calls[0][1]["grace_seconds"], 3600)
        self.assertEqual(cleanup_calls[0][1]["batch_size"], 100)
        self.assertEqual(cleanup_calls[0][1]["scan_limit"], 500)
        self.assertIs(cleanup_calls[0][1]["cursor"], self.worker._SUPPORT_ATTACHMENT_CLEANUP_CURSOR)
        self.assertEqual(sleep_calls, [900])
        main_source = inspect.getsource(self.worker.main)
        self.assertIn('"support_attachment_cleanup"', main_source)
        self.assertIn("support_attachment_cleanup_job", main_source)

    def test_antiabuse_retention_job_drains_before_sleep(self) -> None:
        drain_calls: list[object] = []
        to_thread_calls: list[object] = []

        async def _stop_after_first_sleep(_seconds: float) -> None:
            raise asyncio.CancelledError()

        def _drain(session_factory, *, now=None, batch_limit=1000, max_batches=0):
            drain_calls.append((session_factory, now, batch_limit, max_batches))
            return {"status": "drained", "changed_batches": 2, "cleared": {}, "remaining": {}}

        async def _to_thread(func, *args, **kwargs):
            to_thread_calls.append((func, args, kwargs))
            return func(*args, **kwargs)

        with mock.patch.object(self.worker, "drain_antiabuse_retention", side_effect=_drain), \
             mock.patch.object(self.worker.asyncio, "to_thread", side_effect=_to_thread), \
             mock.patch.object(self.worker.asyncio, "sleep", side_effect=_stop_after_first_sleep):
            with self.assertRaises(asyncio.CancelledError):
                self.worker.asyncio.run(self.worker.antiabuse_retention_job())

        self.assertEqual(len(drain_calls), 1)
        self.assertIs(drain_calls[0][0], self.worker.SessionLocal)
        self.assertIsNotNone(drain_calls[0][1])
        self.assertEqual(drain_calls[0][2], self.worker.ANTIABUSE_RETENTION_BATCH_LIMIT)
        self.assertEqual(drain_calls[0][3], self.worker.ANTIABUSE_RETENTION_MAX_BATCHES_PER_RUN)
        self.assertEqual(len(to_thread_calls), 1)

    def test_antiabuse_retention_job_retries_backlog_without_full_interval_sleep(self) -> None:
        sleep_calls: list[float] = []

        async def _to_thread(func, *args, **kwargs):
            return func(*args, **kwargs)

        def _drain(*_args, **_kwargs):
            return {
                "status": "backlog_remaining",
                "changed_batches": 1,
                "cleared": {"antiabuse_raw_ip": 1},
                "remaining": {"antiabuse_raw_ip": 1},
            }

        async def _record_sleep(seconds: float) -> None:
            sleep_calls.append(seconds)
            raise asyncio.CancelledError()

        with mock.patch.object(self.worker, "drain_antiabuse_retention", side_effect=_drain), \
             mock.patch.object(self.worker.asyncio, "to_thread", side_effect=_to_thread), \
             mock.patch.object(self.worker.asyncio, "sleep", side_effect=_record_sleep):
            with self.assertRaises(asyncio.CancelledError):
                self.worker.asyncio.run(self.worker.antiabuse_retention_job())

        self.assertEqual(sleep_calls, [1])

    def test_telemetry_retention_cleans_ru_tables_and_preserves_holds(self) -> None:
        from models import (
            InternalIngestNonce,
            ReleaseCandidate,
            ReleaseOriginEvidence,
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
            candidate_id = "f" * 64
            session.add(
                ReleaseCandidate(
                    candidate_id=candidate_id,
                    component="adminapp",
                    version="2026.07.15.1",
                    revision="9da042c9da042c9da042c9da042c9da042c9da0",
                    artifact_sha256="e" * 64,
                    canonical_descriptor_json='{"artifact_sha256":"' + "e" * 64 + '"}',
                    descriptor_sha256=candidate_id,
                    ingest_key_id="release-test",
                    imported_at=now - timedelta(days=180),
                )
            )
            session.flush()
            session.add(
                ReleaseOriginEvidence(
                    candidate_id=candidate_id,
                    origin="ru",
                    check_name="ru_origin_reachability",
                    status="PASS",
                    evidence_sha256="9" * 64,
                    observed_at=old_held.finished_at,
                    detail_json='{"source":"retained-run"}',
                    ru_probe_run_id=old_held.id,
                    imported_at=now - timedelta(days=180),
                )
            )
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
            self.assertEqual(session.query(ReleaseCandidate).count(), 1)
            self.assertEqual(session.query(ReleaseOriginEvidence).count(), 1)
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
