import importlib
import os
import sys
import tempfile
import unittest
import uuid
from datetime import timedelta
from pathlib import Path


class ObserverServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.repo_root = repo_root
        portal_dir = str(repo_root / "portal_bot")
        if portal_dir not in sys.path:
            sys.path.insert(0, portal_dir)

        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = str((repo_root / f"portal_api_test_{uuid.uuid4().hex}.db").resolve())
        db_uri_path = Path(self.db_path).as_posix()
        self._saved_env = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = f"sqlite:///{db_uri_path}"

        for module_name in ("observer_service", "db", "models", "migrations", "config"):
            sys.modules.pop(module_name, None)

        self.db = importlib.import_module("db")
        self.models = importlib.import_module("models")
        self.observer_service = importlib.import_module("observer_service")
        self.db.init_db()

        session = self.db.SessionLocal()
        try:
            session.add_all(
                [
                    self.models.Node(
                        code="pl",
                        name="Poland",
                        host="pl.pokrov.space",
                        vless_port=443,
                        reality_sni="www.cloudflare.com",
                        reality_pbk="pbk-pl",
                        reality_sid="sid-pl",
                        panel_base_url="https://pl.pokrov.space:8444",
                        panel_path="/panel/",
                        panel_user="admin",
                        panel_pass="secret",
                        inbound_id=10,
                        enabled=True,
                    ),
                    self.models.Node(
                        code="de",
                        name="Germany",
                        host="de.pokrov.space",
                        vless_port=443,
                        reality_sni="www.cloudflare.com",
                        reality_pbk="pbk-de",
                        reality_sid="sid-de",
                        panel_base_url="https://de.pokrov.space:8444",
                        panel_path="/panel/",
                        panel_user="admin",
                        panel_pass="secret",
                        inbound_id=11,
                        enabled=True,
                    ),
                ]
            )
            session.flush()
            session.add(
                self.models.User(
                    tg_id=1001,
                    username="alice",
                    uuid=str(uuid.uuid4()),
                    email="alice@example.com",
                    sub_type="PAID",
                    is_active=True,
                    expiry_at=self.observer_service._utcnow() + timedelta(days=30),
                    tos_accepted=True,
                )
            )
            session.commit()
        finally:
            session.close()

    def tearDown(self) -> None:
        try:
            self.db.engine.dispose()
        except Exception:
            pass
        if self._saved_env is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = self._saved_env
        Path(self.db_path).unlink(missing_ok=True)
        self._tmp.cleanup()

    def test_normalize_source_ip_scores_ipv4_and_ipv6_but_excludes_private(self) -> None:
        ipv4 = self.observer_service.normalize_source_ip("8.8.8.8")
        self.assertEqual(ipv4["source_ip_raw"], "8.8.8.8")
        self.assertEqual(ipv4["score_ip_key"], "8.8.8.8")
        self.assertTrue(ipv4["counts_for_suspicion"])

        ipv6 = self.observer_service.normalize_source_ip("2001:4860:4860::8888")
        self.assertEqual(ipv6["score_ip_key"], "2001:4860:4860::/64")
        self.assertTrue(ipv6["counts_for_suspicion"])

        private = self.observer_service.normalize_source_ip("10.1.2.3")
        self.assertEqual(private["score_ip_key"], "10.1.2.3")
        self.assertFalse(private["counts_for_suspicion"])

    def test_different_batch_replay_counts_only_atomic_trial_activation(self) -> None:
        session = self.db.SessionLocal()
        try:
            now = self.observer_service._utcnow().replace(microsecond=0)
            user = session.query(self.models.User).filter_by(tg_id=1001).one()
            account = self.models.Account(
                id=str(uuid.uuid4()),
                status="active",
                created_source="test",
                created_at=now,
                updated_at=now,
            )
            device = self.models.AccountDevice(
                id=str(uuid.uuid4()),
                account_id=account.id,
                install_id="observer-replay-device",
                state="active",
                first_seen_at=now,
                last_seen_at=now,
                created_at=now,
                updated_at=now,
            )
            user.account_id = account.id
            user.app_install_id = device.install_id
            user.sub_type = "FREE"
            user.current_plan_code = "trial"
            session.add_all([account, device])
            session.flush()
            from economy_service import reserve_trial

            reserve_trial(session, account_id=account.id, device_id=device.id, now=now)
            node = session.query(self.models.Node).filter_by(code="pl").one()
            observation = {
                "occurred_at": (now + timedelta(hours=1)).isoformat(),
                "client_tg_id": user.tg_id,
                "source_ip": "8.8.8.8",
            }

            first = self.observer_service.ingest_observer_batch(
                session,
                node=node,
                batch_id="activation-first",
                cursor=None,
                observations=[observation],
                received_at=now + timedelta(hours=1),
            )
            target_account = self.models.Account(
                id=str(uuid.uuid4()),
                status="active",
                created_source="test_merge",
                created_at=now,
                updated_at=now,
            )
            session.add(target_account)
            session.flush()
            from account_foundation_service import _move_account_owned_rows

            _move_account_owned_rows(
                session,
                source_account_id=account.id,
                target_account_id=target_account.id,
                now=now + timedelta(hours=1, seconds=30),
            )
            user.account_id = target_account.id
            session.flush()
            second = self.observer_service.ingest_observer_batch(
                session,
                node=node,
                batch_id="activation-second",
                cursor=None,
                observations=[observation],
                received_at=now + timedelta(hours=1, minutes=1),
            )

            self.assertEqual(first["activated_trial_count"], 1)
            self.assertEqual(second["activated_trial_count"], 0)
            self.assertEqual(session.query(self.models.ConnectionEvidence).count(), 1)
            grant = session.query(self.models.EntitlementGrant).filter_by(source="premium_trial").one()
            self.assertEqual(grant.activated_at, now + timedelta(hours=1))
            self.assertEqual(grant.expires_at, now + timedelta(days=5, hours=1))
        finally:
            session.close()

    def test_recompute_user_observer_state_marks_overlap_as_suspicious(self) -> None:
        session = self.db.SessionLocal()
        try:
            now = self.observer_service._utcnow()
            pl = session.query(self.models.Node).filter(self.models.Node.code == "pl").first()
            de = session.query(self.models.Node).filter(self.models.Node.code == "de").first()
            assert pl is not None and de is not None

            session.add_all(
                [
                    self.models.ObserverDailyObservation(
                        tg_id=1001,
                        node_id=int(pl.id),
                        source_ip_raw="8.8.8.8",
                        score_ip_key="8.8.8.8",
                        day_bucket=now.date(),
                        first_seen_at=now - timedelta(minutes=5),
                        last_seen_at=now - timedelta(minutes=5),
                        hit_count=1,
                        identity_source="panel_email",
                        counts_for_suspicion=True,
                    ),
                    self.models.ObserverDailyObservation(
                        tg_id=1001,
                        node_id=int(de.id),
                        source_ip_raw="1.1.1.1",
                        score_ip_key="1.1.1.1",
                        day_bucket=now.date(),
                        first_seen_at=now - timedelta(minutes=4),
                        last_seen_at=now - timedelta(minutes=4),
                        hit_count=1,
                        identity_source="panel_email",
                        counts_for_suspicion=True,
                    ),
                    self.models.ObserverDailyObservation(
                        tg_id=1001,
                        node_id=int(pl.id),
                        source_ip_raw="9.9.9.9",
                        score_ip_key="9.9.9.9",
                        day_bucket=now.date(),
                        first_seen_at=now - timedelta(hours=1),
                        last_seen_at=now - timedelta(hours=1),
                        hit_count=1,
                        identity_source="panel_email",
                        counts_for_suspicion=True,
                    ),
                    self.models.ObserverDailyObservation(
                        tg_id=1001,
                        node_id=int(de.id),
                        source_ip_raw="4.4.4.4",
                        score_ip_key="4.4.4.4",
                        day_bucket=now.date(),
                        first_seen_at=now - timedelta(hours=2),
                        last_seen_at=now - timedelta(hours=2),
                        hit_count=1,
                        identity_source="panel_email",
                        counts_for_suspicion=True,
                    ),
                    self.models.ObserverDailyObservation(
                        tg_id=1001,
                        node_id=int(pl.id),
                        source_ip_raw="208.67.222.222",
                        score_ip_key="208.67.222.222",
                        day_bucket=now.date(),
                        first_seen_at=now - timedelta(hours=3),
                        last_seen_at=now - timedelta(hours=3),
                        hit_count=1,
                        identity_source="panel_email",
                        counts_for_suspicion=True,
                    ),
                    self.models.ObserverWindowObservation(
                        tg_id=1001,
                        node_id=int(pl.id),
                        source_ip_raw="8.8.8.8",
                        score_ip_key="8.8.8.8",
                        window_bucket_at=now.replace(minute=(now.minute // 10) * 10, second=0),
                        first_seen_at=now - timedelta(minutes=5),
                        last_seen_at=now - timedelta(minutes=5),
                        hit_count=1,
                        counts_for_suspicion=True,
                    ),
                    self.models.ObserverWindowObservation(
                        tg_id=1001,
                        node_id=int(de.id),
                        source_ip_raw="1.1.1.1",
                        score_ip_key="1.1.1.1",
                        window_bucket_at=now.replace(minute=(now.minute // 10) * 10, second=0),
                        first_seen_at=now - timedelta(minutes=4),
                        last_seen_at=now - timedelta(minutes=4),
                        hit_count=1,
                        counts_for_suspicion=True,
                    ),
                ]
            )
            session.commit()

            snapshot = self.observer_service.recompute_user_observer_state(session, tg_id=1001, now=now)
            session.commit()
        finally:
            session.close()

        self.assertEqual(snapshot["state"], "suspicious")
        self.assertGreaterEqual(int(snapshot["overlap_count_24h"]), 1)
        self.assertGreaterEqual(int(snapshot["observed_node_count_24h"]), 2)
        self.assertGreaterEqual(int(snapshot["observed_ip_count_24h"]), 5)

    def test_cleanup_observer_retention_prunes_old_rows_and_downgrades_state(self) -> None:
        session = self.db.SessionLocal()
        try:
            now = self.observer_service._utcnow()
            pl = session.query(self.models.Node).filter(self.models.Node.code == "pl").first()
            assert pl is not None
            old_dt = now - timedelta(days=45)
            old_day = old_dt.date()
            old_window = old_dt.replace(minute=(old_dt.minute // 10) * 10, second=0)
            session.add(
                self.models.ObserverDailyObservation(
                    tg_id=1001,
                    node_id=int(pl.id),
                    source_ip_raw="8.8.4.4",
                    score_ip_key="8.8.4.4",
                    day_bucket=old_day,
                    first_seen_at=old_dt,
                    last_seen_at=old_dt,
                    hit_count=1,
                    identity_source="panel_email",
                    counts_for_suspicion=True,
                )
            )
            session.add(
                self.models.ObserverWindowObservation(
                    tg_id=1001,
                    node_id=int(pl.id),
                    source_ip_raw="8.8.4.4",
                    score_ip_key="8.8.4.4",
                    window_bucket_at=old_window,
                    first_seen_at=old_dt,
                    last_seen_at=old_dt,
                    hit_count=1,
                    counts_for_suspicion=True,
                )
            )
            session.add(
                self.models.ObserverUserState(
                    tg_id=1001,
                    state="watch",
                    reasons_json='["many_ips"]',
                    observed_ip_count_24h=0,
                    observed_ip_count_7d=0,
                    observed_ip_count_30d=1,
                    observed_node_count_24h=0,
                    observed_node_count_7d=0,
                    observed_node_count_30d=1,
                    overlap_count_24h=0,
                    last_observed_at=old_dt,
                    updated_at=old_dt,
                )
            )
            session.commit()

            result = self.observer_service.cleanup_observer_retention(session, now=now)
            session.commit()

            state_row = session.query(self.models.ObserverUserState).filter(self.models.ObserverUserState.tg_id == 1001).first()
            daily_count = session.query(self.models.ObserverDailyObservation).filter(self.models.ObserverDailyObservation.tg_id == 1001).count()
            window_count = session.query(self.models.ObserverWindowObservation).filter(self.models.ObserverWindowObservation.tg_id == 1001).count()
        finally:
            session.close()

        self.assertGreaterEqual(int(result["daily_deleted"]), 1)
        self.assertGreaterEqual(int(result["window_deleted"]), 1)
        self.assertIsNotNone(state_row)
        self.assertEqual(state_row.state, "ok")
        self.assertEqual(daily_count, 0)
        self.assertEqual(window_count, 0)


if __name__ == "__main__":
    unittest.main()
