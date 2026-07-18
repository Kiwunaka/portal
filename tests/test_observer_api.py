import hashlib
import hmac
import importlib
import json
import os
import sys
import tempfile
import time
import unittest
import uuid
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError


def _sign_telegram_init_data(*, bot_token: str, params: dict) -> str:
    items = sorted((k, v) for k, v in params.items())
    data_check_string = "\n".join([f"{k}={v}" for k, v in items])
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    check_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    params2 = dict(params)
    params2["hash"] = check_hash
    return urlencode(params2)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ObserverApiTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.repo_root = repo_root
        portal_dir = str(repo_root / "portal_bot")
        if portal_dir not in sys.path:
            sys.path.insert(0, portal_dir)

        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = str((repo_root / f"portal_api_test_{uuid.uuid4().hex}.db").resolve())
        db_uri_path = Path(self.db_path).as_posix()
        self.bot_token = "test_bot_token_123"
        self._saved_env: dict[str, str | None] = {}
        for key in (
            "DATABASE_URL",
            "BOT_TOKEN",
            "ADMIN_ID",
            "WEBAPP_SESSION_SECRET",
            "BOT_USERNAME",
            "SUPPORT_USERNAME",
            "PUBLIC_CHANNEL",
            "PUBLIC_API_BASE_URL",
        ):
            self._saved_env[key] = os.environ.get(key)

        os.environ["DATABASE_URL"] = f"sqlite:///{db_uri_path}"
        os.environ["BOT_TOKEN"] = self.bot_token
        os.environ["ADMIN_ID"] = "9999"
        os.environ["WEBAPP_SESSION_SECRET"] = "test_webapp_secret_123"
        os.environ["BOT_USERNAME"] = "pokrov_vpnbot"
        os.environ["SUPPORT_USERNAME"] = "pokrov_supportbot"
        os.environ["PUBLIC_CHANNEL"] = "pokrov_vpn"
        os.environ["PUBLIC_API_BASE_URL"] = "https://api.pokrov.test"

        for module_name in (
            "api",
            "observer_service",
            "events_service",
            "offers_service",
            "pay_attempts_service",
            "points_service",
            "db",
            "models",
            "migrations",
            "config",
        ):
            sys.modules.pop(module_name, None)

        importlib.import_module("config")
        self.db = importlib.import_module("db")
        self.models = importlib.import_module("models")
        self.api = importlib.import_module("api")
        importlib.reload(self.api)
        self.client = TestClient(self.api.app)

        session = self.db.SessionLocal()
        try:
            pl = self.models.Node(
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
                observer_push_secret="pl-secret",
            )
            de = self.models.Node(
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
                observer_push_secret="de-secret",
            )
            session.add_all([pl, de])
            session.flush()

            alice = self.models.User(
                tg_id=1001,
                username="alice",
                uuid=str(uuid.uuid4()),
                email="alice@example.com",
                sub_type="PAID",
                is_active=True,
                expiry_at=_utcnow() + timedelta(days=30),
                tos_accepted=True,
            )
            competitor = self.models.User(
                tg_id=1002,
                username="bob",
                uuid=str(uuid.uuid4()),
                email="panel-alice",
                sub_type="PAID",
                is_active=True,
                expiry_at=_utcnow() + timedelta(days=30),
                tos_accepted=True,
            )
            session.add_all([alice, competitor])
            session.flush()
            session.add_all(
                [
                    self.models.UserNode(
                        tg_id=1001,
                        node_id=int(pl.id),
                        client_uuid=str(alice.uuid),
                        panel_email="panel-alice",
                    ),
                    self.models.UserNode(
                        tg_id=1001,
                        node_id=int(de.id),
                        client_uuid=str(alice.uuid),
                        panel_email="panel-alice-de",
                    ),
                ]
            )
            session.commit()
        finally:
            session.close()

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
        Path(self.db_path).unlink(missing_ok=True)
        self._tmp.cleanup()

    def _init_data(self, tg_id: int, username: str) -> str:
        return _sign_telegram_init_data(
            bot_token=self.bot_token,
            params={
                "auth_date": str(int(time.time())),
                "query_id": "AAEAAAE",
                "user": f'{{"id":{tg_id},"first_name":"Test","username":"{username}"}}',
            },
        )

    def _observer_headers(self, *, node_code: str, secret: str, body: bytes, timestamp: int | None = None) -> dict[str, str]:
        ts = int(time.time() if timestamp is None else timestamp)
        canonical = f"{node_code}\n{ts}\n{body.decode('utf-8')}".encode("utf-8")
        sig = hmac.new(secret.encode("utf-8"), canonical, hashlib.sha256).hexdigest()
        return {
            "Content-Type": "application/json",
            "X-Portal-Node": node_code,
            "X-Portal-Timestamp": str(ts),
            "X-Portal-Signature": sig,
        }

    def test_internal_observer_batch_ingests_watch_state_and_exposes_admin_payloads(self) -> None:
        now = _utcnow().replace(microsecond=0)
        pl_body = json.dumps(
            {
                "batch_id": "pl-001",
                "cursor": {"inode": 12, "offset": 400},
                "observations": [
                    {"occurred_at": (now - timedelta(hours=4)).isoformat(), "client_email": "panel-alice", "source_ip": "8.8.8.8"},
                    {"occurred_at": (now - timedelta(hours=2)).isoformat(), "client_email": "panel-alice", "source_ip": "9.9.9.9"},
                ],
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        de_body = json.dumps(
            {
                "batch_id": "de-001",
                "cursor": {"inode": 20, "offset": 800},
                "observations": [
                    {"occurred_at": (now - timedelta(hours=3)).isoformat(), "client_email": "panel-alice-de", "source_ip": "1.1.1.1"},
                ],
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")

        pl_resp = self.client.post("/api/internal/observer/batches", content=pl_body, headers=self._observer_headers(node_code="pl", secret="pl-secret", body=pl_body))
        de_resp = self.client.post("/api/internal/observer/batches", content=de_body, headers=self._observer_headers(node_code="de", secret="de-secret", body=de_body))

        self.assertEqual(pl_resp.status_code, 200, pl_resp.text)
        self.assertEqual(de_resp.status_code, 200, de_resp.text)
        self.assertEqual(pl_resp.json()["accepted_count"], 2)
        self.assertEqual(de_resp.json()["accepted_count"], 1)
        self.assertEqual(sorted(de_resp.json()["updated_tg_ids"]), [1001])

        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}
        users_resp = self.client.get("/api/admin/users", headers=admin_hdrs, params={"observer_state": "watch", "page": 1, "page_size": 20})
        self.assertEqual(users_resp.status_code, 200, users_resp.text)
        users_body = users_resp.json()
        self.assertEqual(users_body["total"], 1)
        self.assertEqual(users_body["users"][0]["observer_state"], "watch")
        self.assertTrue(users_body["users"][0]["observer_updated_at"])

        card_resp = self.client.get("/api/admin/users/1001", headers=admin_hdrs)
        self.assertEqual(card_resp.status_code, 200, card_resp.text)
        card_body = card_resp.json()
        card_serialized = json.dumps(card_body, ensure_ascii=False)
        self.assertEqual(card_body["observer"]["state"], "watch")
        self.assertEqual(card_body["observer"]["observed_ip_count_24h"], 3)
        self.assertEqual(card_body["observer"]["observed_node_count_24h"], 2)
        self.assertNotIn("recent_ips", card_body["observer"])
        self.assertNotIn("source_ip_raw", card_resp.text)
        self.assertEqual(len(card_body["observer"]["recent_nodes"]), 2)
        for forbidden in (
            "subscription_token",
            "subscription_url",
            "vless_link",
            "expected_sub_id",
            "panel_email",
            "client_uuid",
            "node_host",
            "panel_error",
            '"meta"',
        ):
            self.assertNotIn(forbidden, card_serialized)

        investigation_resp = self.client.get("/api/admin/users/1001/investigation", headers=admin_hdrs)
        self.assertEqual(investigation_resp.status_code, 200, investigation_resp.text)
        investigation_body = investigation_resp.json()
        self.assertEqual(investigation_body["tg_id"], 1001)
        self.assertEqual(len(investigation_body["observer"]["recent_ips"]), 3)

        summary_resp = self.client.get("/api/admin/summary", headers=admin_hdrs)
        self.assertEqual(summary_resp.status_code, 200, summary_resp.text)
        summary_body = summary_resp.json()
        self.assertEqual(summary_body["observer"]["watch_users"], 1)
        self.assertEqual(summary_body["observer"]["suspicious_users"], 0)

        nodes_resp = self.client.get("/api/admin/nodes/health", headers=admin_hdrs)
        self.assertEqual(nodes_resp.status_code, 200, nodes_resp.text)
        pl_node = next(row for row in nodes_resp.json()["nodes"] if row["code"] == "pl")
        self.assertTrue(pl_node["observer_last_push_at"])
        self.assertEqual(pl_node["observer_unmatched_count"], 0)
        self.assertEqual(pl_node["observer_parse_error_count"], 0)
        self.assertFalse(pl_node["observer_is_stale"])

    def test_internal_observer_batch_is_idempotent_for_replayed_batch_ids(self) -> None:
        now = _utcnow().replace(microsecond=0)
        body = json.dumps(
            {
                "batch_id": "pl-replay",
                "cursor": {"inode": 12, "offset": 100},
                "observations": [
                    {"occurred_at": now.isoformat(), "client_email": "panel-alice", "source_ip": "8.8.8.8"},
                ],
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        headers = self._observer_headers(node_code="pl", secret="pl-secret", body=body)

        first = self.client.post("/api/internal/observer/batches", content=body, headers=headers)
        second = self.client.post("/api/internal/observer/batches", content=body, headers=headers)

        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(second.status_code, 200, second.text)
        self.assertEqual(first.json()["accepted_count"], 1)
        self.assertEqual(second.json()["accepted_count"], 0)
        self.assertEqual(second.json()["deduped_count"], 1)

    def test_internal_observer_batch_unique_race_converges_but_unrelated_integrity_error_fails(self) -> None:
        now = _utcnow().replace(microsecond=0)
        body = json.dumps(
            {
                "batch_id": "pl-race",
                "observations": [
                    {"occurred_at": now.isoformat(), "client_email": "panel-alice", "source_ip": "8.8.8.8"}
                ],
            },
            separators=(",", ":"),
        ).encode("utf-8")
        headers = self._observer_headers(node_code="pl", secret="pl-secret", body=body)

        def insert_winner_then_conflict(**_kwargs):
            winner = self.db.SessionLocal()
            try:
                node = winner.query(self.models.Node).filter_by(code="pl").one()
                winner.add(
                    self.models.ObserverBatch(
                        node_id=node.id,
                        batch_id="pl-race",
                        observation_count=1,
                        accepted_count=1,
                        deduped_count=0,
                        unmatched_count=0,
                        parse_error_count=0,
                        updated_tg_ids_json="[1001]",
                        created_at=now,
                    )
                )
                winner.commit()
            finally:
                winner.close()
            raise IntegrityError("INSERT observer_batches", {}, RuntimeError("unique"))

        with patch.object(self.api, "ingest_observer_batch", side_effect=insert_winner_then_conflict):
            response = self.client.post("/api/internal/observer/batches", content=body, headers=headers)

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["accepted_count"], 0)
        self.assertEqual(response.json()["deduped_count"], 1)
        self.assertEqual(response.json()["activated_trial_count"], 0)

        unrelated_body = body.replace(b"pl-race", b"pl-fail")
        unrelated_headers = self._observer_headers(node_code="pl", secret="pl-secret", body=unrelated_body)
        with patch.object(
            self.api,
            "ingest_observer_batch",
            side_effect=IntegrityError("INSERT other_table", {}, RuntimeError("unrelated")),
        ):
            unrelated = self.client.post(
                "/api/internal/observer/batches",
                content=unrelated_body,
                headers=unrelated_headers,
            )
        self.assertEqual(unrelated.status_code, 500)

    def test_internal_observer_batch_rejects_stale_push_and_tracks_unmatched_and_parse_errors(self) -> None:
        stale_body = json.dumps(
            {
                "batch_id": "pl-stale",
                "cursor": {"inode": 12, "offset": 100},
                "observations": [
                    {"occurred_at": _utcnow().replace(microsecond=0).isoformat(), "client_email": "panel-alice", "source_ip": "8.8.8.8"},
                ],
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        stale_headers = self._observer_headers(
            node_code="pl",
            secret="pl-secret",
            body=stale_body,
            timestamp=int(time.time()) - 5000,
        )
        stale_resp = self.client.post("/api/internal/observer/batches", content=stale_body, headers=stale_headers)
        self.assertEqual(stale_resp.status_code, 401, stale_resp.text)

        now = _utcnow().replace(microsecond=0)
        body = json.dumps(
            {
                "batch_id": "pl-errors",
                "cursor": {"inode": 14, "offset": 160},
                "parse_error_count": 2,
                "observations": [
                    {"occurred_at": now.isoformat(), "client_email": "unknown-client", "source_ip": "8.8.4.4"},
                    {"occurred_at": "not-a-date", "client_email": "panel-alice", "source_ip": "bad-ip"},
                ],
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        resp = self.client.post("/api/internal/observer/batches", content=body, headers=self._observer_headers(node_code="pl", secret="pl-secret", body=body))
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.json()["accepted_count"], 0)
        self.assertEqual(resp.json()["unmatched_count"], 1)

        admin_hdrs = {"X-Telegram-Init-Data": self._init_data(9999, "admin")}
        nodes_resp = self.client.get("/api/admin/nodes/health", headers=admin_hdrs)
        self.assertEqual(nodes_resp.status_code, 200, nodes_resp.text)
        pl_node = next(row for row in nodes_resp.json()["nodes"] if row["code"] == "pl")
        self.assertEqual(pl_node["observer_unmatched_count"], 1)
        self.assertEqual(pl_node["observer_parse_error_count"], 3)


if __name__ == "__main__":
    unittest.main()
