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
        for key in ("DATABASE_URL", "BOT_TOKEN", "PUBLIC_CHANNEL"):
            self._saved_env[key] = os.environ.get(key)

        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = (repo_root / f"portal_api_test_{uuid.uuid4().hex}.db").resolve()
        os.environ["DATABASE_URL"] = f"sqlite:///{self.db_path.as_posix()}"
        os.environ["BOT_TOKEN"] = "test_bot_token_123"
        os.environ["PUBLIC_CHANNEL"] = "pokrov_vpn"

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


if __name__ == "__main__":
    unittest.main()
