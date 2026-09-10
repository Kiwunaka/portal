import importlib
import hashlib
import os
import sys
import tempfile
import time
import unittest
import uuid
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlencode
from unittest.mock import patch

from fastapi.testclient import TestClient


def _sign_telegram_init_data(*, bot_token: str, params: dict) -> str:
    import hashlib
    import hmac

    items = sorted((k, v) for k, v in params.items())
    data_check_string = "\n".join([f"{k}={v}" for k, v in items])
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    check_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    payload = dict(params)
    payload["hash"] = check_hash
    return urlencode(payload)


class BackendRouteGapCoverageTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        portal_dir = str(repo_root / "portal_bot")
        if portal_dir not in sys.path:
            sys.path.insert(0, portal_dir)

        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = str((repo_root / f"portal_api_gap_test_{uuid.uuid4().hex}.db").resolve())
        self.bot_token = "test_bot_token_123"
        self._saved_env = {
            key: os.environ.get(key)
            for key in (
                "DATABASE_URL",
                "BOT_TOKEN",
                "ADMIN_ID",
                "WEBAPP_SESSION_SECRET",
                "BOT_USERNAME",
                "SUPPORT_USERNAME",
                "PUBLIC_CHANNEL",
            )
        }
        os.environ["DATABASE_URL"] = f"sqlite:///{Path(self.db_path).as_posix()}"
        os.environ["BOT_TOKEN"] = self.bot_token
        os.environ["ADMIN_ID"] = "9999"
        os.environ["WEBAPP_SESSION_SECRET"] = "test_webapp_secret_123"
        os.environ["BOT_USERNAME"] = "pokrov_vpnbot"
        os.environ["SUPPORT_USERNAME"] = "pokrov_supportbot"
        os.environ["PUBLIC_CHANNEL"] = "pokrov_vpn"

        for module_name in ("config", "db", "api"):
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
        self.api = importlib.import_module("api")
        importlib.reload(self.api)
        self.client = TestClient(self.api.app)

        from db import SessionLocal
        from models import User

        session = SessionLocal()
        try:
            session.add(
                User(
                    tg_id=1001,
                    username="alice",
                    uuid=str(uuid.uuid4()),
                    email="user_1001",
                    sub_type="FREE",
                    is_active=True,
                    tos_accepted=True,
                )
            )
            session.add(
                User(
                    tg_id=9999,
                    username="admin",
                    uuid=str(uuid.uuid4()),
                    email="user_9999",
                    sub_type="PAID",
                    is_active=True,
                    tos_accepted=True,
                )
            )
            session.commit()
        finally:
            session.close()

    def tearDown(self) -> None:
        try:
            from db import engine

            engine.dispose()
        except Exception:
            pass
        for key, value in self._saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        try:
            Path(self.db_path).unlink(missing_ok=True)
        except Exception:
            pass
        self._tmp.cleanup()

    def _init_data(self, tg_id: int, username: str) -> str:
        return _sign_telegram_init_data(
            bot_token=self.bot_token,
            params={
                "auth_date": str(int(time.time())),
                "query_id": f"query-{tg_id}",
                "user": f'{{"id":{tg_id},"first_name":"Test","username":"{username}"}}',
            },
        )

    @property
    def admin_headers(self) -> dict[str, str]:
        return {"X-Telegram-Init-Data": self._init_data(9999, "admin")}

    @property
    def user_headers(self) -> dict[str, str]:
        return {"X-Telegram-Init-Data": self._init_data(1001, "alice")}

    def _prepare_admin_action(
        self,
        *,
        action: str,
        target_type: str,
        target_id: str,
        payload: dict[str, object],
    ) -> dict[str, str]:
        prepared = self.client.post(
            "/api/admin/action-intents",
            headers=self.admin_headers,
            json={
                "action": action,
                "target": {"type": target_type, "id": target_id},
                "payload": payload,
            },
        )
        self.assertEqual(prepared.status_code, 200, prepared.text)
        confirmation = str(prepared.json()["confirmation_challenge"])
        return {
            **self.admin_headers,
            "X-Admin-Intent-Id": str(prepared.json()["intent_id"]),
            "X-Admin-Idempotency-Key": str(uuid.uuid4()),
            "X-Admin-Confirmation-SHA256": hashlib.sha256(
                confirmation.encode("utf-8")
            ).hexdigest(),
        }

    def test_public_catalog_and_funnel_gap_routes(self) -> None:
        catalog = self.client.get("/api/public/catalog")
        self.assertEqual(catalog.status_code, 200, catalog.text)
        self.assertIn("Cache-Control", catalog.headers)
        catalog_body = catalog.json()
        self.assertEqual(catalog.headers.get("X-Pokrov-Commercial-Revision"), self.api.COMMERCIAL_REVISION)
        self.assertEqual(catalog_body.get("commercial_revision"), self.api.COMMERCIAL_REVISION)
        self.assertEqual(catalog_body.get("price_authority"), "server_commercial_contract")
        self.assertEqual(catalog_body.get("promo_authority"), "server_offer_preview_only")
        self.assertFalse(catalog_body.get("legal_launch_ready"))

        plans = self.client.get("/api/public/plans")
        self.assertEqual(plans.status_code, 200, plans.text)
        self.assertEqual(plans.headers.get("X-Pokrov-Commercial-Revision"), self.api.COMMERCIAL_REVISION)
        self.assertEqual(plans.json().get("commercial_revision"), self.api.COMMERCIAL_REVISION)

        health = self.client.get("/api/health")
        self.assertEqual(health.status_code, 200, health.text)
        self.assertEqual(health.headers.get("X-Pokrov-Commercial-Revision"), self.api.COMMERCIAL_REVISION)
        self.assertEqual(health.json()["commercial"]["source_consistency"], "consistent")

        funnel = self.client.post(
            "/api/funnel/events",
            json={
                "event_name": "page_view",
                "stage": "site_visit",
                "channel": "marketing",
                "source": "home",
                "session_id": "session-gap-001",
                "path": "/",
                "meta": {"surface": "gap-test"},
            },
        )
        self.assertEqual(funnel.status_code, 200, funnel.text)
        self.assertTrue(funnel.json().get("ok"))

        bad_funnel = self.client.post(
            "/api/funnel/events",
            json={
                "event_name": "unknown_event",
                "stage": "site_visit",
                "channel": "marketing",
                "source": "home",
                "session_id": "session-gap-002",
            },
        )
        self.assertEqual(bad_funnel.status_code, 400, bad_funnel.text)

        connect = self.client.post("/api/connect/confirm", headers=self.user_headers)
        self.assertEqual(connect.status_code, 200, connect.text)
        self.assertTrue(connect.json().get("ok"))

        summary = self.client.get("/api/admin/funnel/summary", headers=self.admin_headers)
        self.assertEqual(summary.status_code, 200, summary.text)
        body = summary.json()
        self.assertIn("acquisition", body)
        self.assertIn("product", body)
        self.assertIn("period", body)

    def test_admin_funnel_separates_exact_acquisition_from_product_users(self) -> None:
        from db import SessionLocal
        from models import (
            AccountExperienceState,
            AcquisitionHandoff,
            AcquisitionSession,
            ConnectionEvidence,
            Event,
            ExternalOrder,
            FunnelEvent,
            PayAttempt,
            User,
        )

        now = self.api._utcnow()
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.tg_id == 1001).one()
            user.account_id = "account-funnel-1001"
            user.app_last_seen_at = now
            acquisition = AcquisitionSession(
                id="acquisition-funnel-1",
                session_key_hash="a" * 64,
                first_source="telegram_ads",
                first_channel="marketing",
                first_campaign="august",
                first_entry_route="/install",
                last_source="telegram_ads",
                last_channel="checkout",
                last_campaign="august",
                last_entry_route="/checkout",
                bound_tg_id=1001,
                bound_account_id=user.account_id,
                created_at=now - timedelta(minutes=5),
                first_touch_at=now - timedelta(minutes=5),
                last_touch_at=now,
                expires_at=now + timedelta(days=180),
            )
            session.add(acquisition)
            session.flush()
            session.add(
                FunnelEvent(
                    session_id=acquisition.session_key_hash,
                    channel="marketing",
                    event_name="download_click",
                    stage="download",
                    source="telegram_ads",
                    path="/install",
                    created_at=now,
                )
            )
            session.add_all(
                [
                    AcquisitionHandoff(
                        id="handoff-install-1",
                        token_hash="b" * 64,
                        acquisition_session_id=acquisition.id,
                        purpose="android_install",
                        created_at=now,
                        expires_at=now + timedelta(hours=72),
                        consumed_at=now,
                        bound_tg_id=1001,
                        bound_account_id=user.account_id,
                    ),
                    AcquisitionHandoff(
                        id="handoff-checkout-1",
                        token_hash="c" * 64,
                        acquisition_session_id=acquisition.id,
                        purpose="checkout",
                        created_at=now,
                        expires_at=now + timedelta(hours=72),
                        consumed_at=now,
                        bound_tg_id=1001,
                        bound_account_id=user.account_id,
                        bound_order_id="order-funnel-1",
                    ),
                ]
            )
            session.add(
                ExternalOrder(
                    order_id="order-funnel-1",
                    tg_id=1001,
                    provider="lavatop",
                    plan_code="start_99",
                    source="telegram_ads",
                    campaign="august",
                    acquisition_session_id=acquisition.id,
                    amount=99,
                    currency="RUB",
                    status="paid",
                    created_at=now,
                    paid_at=now,
                )
            )
            session.add(
                PayAttempt(
                    tg_id=1001,
                    source="bot",
                    plan_code="start_99",
                    amount_stars=99,
                    status="paid",
                    acquisition_session_id=acquisition.id,
                    started_at=now,
                    updated_at=now,
                    paid_at=now,
                )
            )
            session.add(
                AccountExperienceState(
                    account_id=user.account_id,
                    first_connection_reported_at=now,
                    created_at=now,
                    updated_at=now,
                )
            )
            session.add_all(
                [
                    Event(tg_id=1001, event_name="opened_webapp", source="webapp", created_at=now),
                    Event(tg_id=1001, event_name="clicked_pay", source="webapp", created_at=now),
                    Event(tg_id=1001, event_name="paid", source="webapp", created_at=now),
                    Event(tg_id=1001, event_name="connected_ok", source="webapp", created_at=now),
                ]
            )
            session.commit()
        finally:
            session.close()

        summary = self.client.get(
            "/api/admin/funnel/summary",
            headers=self.admin_headers,
            params={"from": (now - timedelta(days=1)).isoformat(), "to": (now + timedelta(days=1)).isoformat()},
        )
        self.assertEqual(summary.status_code, 200, summary.text)
        body = summary.json()
        self.assertEqual(
            body["acquisition"]["totals"],
            {"sessions": 1, "entry_intents": 1, "resolved_entries": 1, "checkouts": 1, "paid": 1, "connected": 0},
        )
        self.assertEqual(
            body["product"]["totals"],
            {"opened": 1, "checkouts": 1, "paid": 1, "connected": 0},
        )
        observability = body["product"]["observability"]
        self.assertGreaterEqual(int(observability["summary"]["events"]), 4)
        self.assertEqual(int(observability["summary"]["active_users_7d"]), 1)
        self.assertIn("versions", observability)
        self.assertIn("errors", observability)
        self.assertEqual(body["acquisition"]["by_source"][0]["source"], "telegram_ads")
        self.assertNotIn("recent", body)
        serialized = summary.text
        self.assertNotIn("acquisition-funnel-1", serialized)
        self.assertNotIn("account-funnel-1001", serialized)
        self.assertNotIn("order-funnel-1", serialized)

        # Only an observer connection after the server-owned payment is a
        # paid-to-connected outcome; self-report and an earlier trial are not.
        for evidence_id, observed_at, kind, expected in (
            ("earlier", now - timedelta(seconds=1), "observer_connection", 0),
            ("untrusted", now + timedelta(seconds=1), "client_report", 0),
            ("verified", now + timedelta(seconds=2), "observer_connection", 1),
        ):
            session = SessionLocal()
            try:
                session.add(ConnectionEvidence(
                    id=evidence_id,
                    account_id="account-funnel-1001",
                    node_id=1,
                    evidence_kind=kind,
                    observed_at=observed_at,
                    evidence_key=f"funnel-{evidence_id}",
                    created_at=observed_at,
                ))
                session.commit()
            finally:
                session.close()
            response = self.client.get(
                "/api/admin/funnel/summary",
                headers=self.admin_headers,
                params={"from": (now - timedelta(days=1)).isoformat(), "to": (now + timedelta(days=1)).isoformat()},
            )
            self.assertEqual(response.status_code, 200, response.text)
            for funnel_name in ("acquisition", "product"):
                self.assertEqual(response.json()[funnel_name]["totals"]["connected"], expected)

    def test_admin_funnel_client_paid_event_is_not_payment_authority(self) -> None:
        for event_name in ("opened_webapp", "clicked_pay", "paid", "connected_ok"):
            response = self.client.post(
                "/api/events", headers=self.user_headers, json={"event_name": event_name}
            )
            self.assertEqual(response.status_code, 200, response.text)
        response = self.client.get("/api/admin/funnel/summary", headers=self.admin_headers)
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["product"]["totals"], {
            "opened": 1, "checkouts": 1, "paid": 0, "connected": 0,
        })
        self.assertEqual(body["acquisition"]["totals"]["sessions"], 0)

        # A later server payment and observer fact belong to the product
        # cohort without fabricating an anonymous browser handoff.
        from db import SessionLocal
        from models import ConnectionEvidence, PayAttempt, User

        now = self.api._utcnow()
        session = SessionLocal()
        try:
            user = session.query(User).filter_by(tg_id=1001).one()
            user.account_id = "account-product-only-1001"
            session.add(PayAttempt(
                tg_id=1001, source="bot", plan_code="start_99", amount_stars=99,
                status="paid", started_at=now, updated_at=now, paid_at=now,
            ))
            session.add(ConnectionEvidence(
                id="product-only-evidence", account_id=user.account_id, node_id=1,
                evidence_kind="observer_connection", observed_at=now,
                evidence_key="product-only-funnel", created_at=now,
            ))
            session.commit()
        finally:
            session.close()
        response = self.client.get("/api/admin/funnel/summary", headers=self.admin_headers)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["product"]["totals"], {
            "opened": 1, "checkouts": 1, "paid": 1, "connected": 1,
        })
        self.assertEqual(response.json()["acquisition"]["totals"]["sessions"], 0)

    def test_admin_broadcast_and_referral_gap_routes(self) -> None:
        sent_to: list[int] = []
        broadcast_payload = {
            "text": "POKROV test broadcast",
            "segment": "custom",
            "tg_ids": [1001],
            "limit": 5,
        }
        broadcast_headers = self._prepare_admin_action(
            action="broadcast.send",
            target_type="broadcast",
            target_id="broadcast",
            payload=broadcast_payload,
        )

        from telegram_delivery_service import TelegramDeliveryResult

        async def fake_send_message(
            tg_id: int,
            _text: str,
            **_kwargs,
        ) -> TelegramDeliveryResult:
            sent_to.append(int(tg_id))
            return TelegramDeliveryResult(
                sent=True,
                reason_code="sent",
                retryable=False,
                duration_ms=1,
                http_status=200,
                message_id=123,
            )

        with patch.object(self.api, "_telegram_send_message_detailed", new=fake_send_message):
            broadcast = self.client.post(
                "/api/admin/broadcast",
                headers=broadcast_headers,
                json=broadcast_payload,
            )
        self.assertEqual(broadcast.status_code, 200, broadcast.text)
        self.assertEqual(broadcast.json().get("sent"), 1)
        self.assertEqual(sent_to, [1001])

        from db import SessionLocal
        from models import ReferralBonusQueue

        session = SessionLocal()
        try:
            session.add(
                ReferralBonusQueue(
                    referrer_tg_id=9999,
                    referred_tg_id=1001,
                    order_id="gap-order-1",
                    ready_at=self.api._utcnow() - timedelta(minutes=1),
                    status="pending",
                    meta="{}",
                )
            )
            session.commit()
        finally:
            session.close()

        pending = self.client.get("/api/admin/referrals/pending", headers=self.admin_headers)
        self.assertEqual(pending.status_code, 200, pending.text)
        self.assertEqual(pending.json()["rows"][0]["order_id"], "gap-order-1")

        referral_payload = {"limit": 10, "force_without_activity": False}
        referral_headers = self._prepare_admin_action(
            action="referral.process",
            target_type="referral_queue",
            target_id="ready",
            payload=referral_payload,
        )
        processed = self.client.post(
            "/api/admin/referrals/process",
            headers=referral_headers,
            json=referral_payload,
        )
        self.assertEqual(processed.status_code, 200, processed.text)
        self.assertTrue(processed.json().get("ok"))
        self.assertEqual(processed.json().get("processed"), 1)
        self.assertEqual(processed.json().get("waiting"), 1)

    def test_admin_campaign_crud_gap_routes(self) -> None:
        create_payload = self.api.AdminCampaignCreateIn(
            name="Gap campaign",
            campaign_type="promo",
            target_value="GAP10",
            segment="all_active",
            max_activations=5,
            auto_disable=True,
            metadata={"source": "test"},
        ).model_dump()
        created = self.client.post(
            "/api/admin/campaigns",
            headers=self._prepare_admin_action(
                action="campaign.create",
                target_type="campaign",
                target_id="new",
                payload=create_payload,
            ),
            json=create_payload,
        )
        self.assertEqual(created.status_code, 200, created.text)
        campaign_id = int(created.json()["id"])

        listed = self.client.get("/api/admin/campaigns", headers=self.admin_headers)
        self.assertEqual(listed.status_code, 200, listed.text)
        capacity_automation = listed.json()["capacity_automation"]
        self.assertEqual(
            capacity_automation["schema"],
            "pokrov-commercial-capacity-automation-v1",
        )
        self.assertEqual(
            capacity_automation["commercial_revision"], self.api.COMMERCIAL_REVISION
        )
        self.assertEqual(
            capacity_automation["forecast"]["pause_threshold_units"], 210
        )
        self.assertEqual(
            capacity_automation["forecast"]["resume_below_units"], 194
        )
        listed_campaign = next(
            row for row in listed.json()["campaigns"] if int(row["id"]) == campaign_id
        )
        self.assertTrue(str(listed_campaign["public_id"]).startswith("cmp_"))
        self.assertEqual(listed_campaign["lifecycle_status"], "draft")
        self.assertFalse(listed_campaign["policy"]["activation_allowed"])
        self.assertIn("seller_unpublished", listed_campaign["policy"]["blocking_reasons"])

        update_payload = {
            "expected_revision": int(listed_campaign["revision"]),
            "name": "Gap campaign patched",
            "lifecycle_status": "paused",
            "state_reason": "owner_paused",
        }
        update_headers = self._prepare_admin_action(
            action="campaign.update",
            target_type="campaign",
            target_id=str(campaign_id),
            payload=update_payload,
        )
        from models import Node

        with self.api.SessionLocal() as session:
            session.add(Node(
                code="quality-test", access_role="paid", last_health_at=self.api._utcnow(),
                cpu_percent=20, network_tx_mbps_1m=10, packet_loss_percent=0,
            ))
            session.commit()
        changed_quality = self.client.patch(
            f"/api/admin/campaigns/{campaign_id}", headers=update_headers, json=update_payload
        )
        self.assertEqual(changed_quality.status_code, 409, changed_quality.text)
        self.assertEqual(changed_quality.json()["detail"]["code"], "stale_intent")
        update_headers = self._prepare_admin_action(
            action="campaign.update", target_type="campaign",
            target_id=str(campaign_id), payload=update_payload,
        )
        with self.api.SessionLocal() as session:
            node = session.query(Node).filter(Node.code == "quality-test").one()
            node.cpu_percent = 21
            node.last_health_at = self.api._utcnow()
            session.commit()
        patched = self.client.patch(
            f"/api/admin/campaigns/{campaign_id}", headers=update_headers, json=update_payload
        )
        self.assertEqual(patched.status_code, 200, patched.text)
        replayed_update = self.client.patch(
            f"/api/admin/campaigns/{campaign_id}", headers=update_headers, json=update_payload
        )
        self.assertEqual(replayed_update.status_code, 200, replayed_update.text)
        self.assertEqual(replayed_update.json()["revision"], patched.json()["revision"])

        stale_prepare = self.client.post(
            "/api/admin/action-intents",
            headers=self.admin_headers,
            json={
                "action": "campaign.update",
                "target": {"type": "campaign", "id": str(campaign_id)},
                "payload": {
                    "expected_revision": int(listed_campaign["revision"]),
                    "name": "stale campaign update",
                },
            },
        )
        self.assertEqual(stale_prepare.status_code, 409, stale_prepare.text)
        self.assertEqual(stale_prepare.json()["detail"]["code"], "stale_campaign_revision")

        delete_headers = self._prepare_admin_action(
            action="campaign.delete",
            target_type="campaign",
            target_id=str(campaign_id),
            payload={},
        )
        deleted = self.client.delete(
            f"/api/admin/campaigns/{campaign_id}", headers=delete_headers
        )
        self.assertEqual(deleted.status_code, 200, deleted.text)
        self.assertTrue(deleted.json().get("ok"))
        replayed_delete = self.client.delete(
            f"/api/admin/campaigns/{campaign_id}", headers=delete_headers
        )
        self.assertEqual(replayed_delete.status_code, 200, replayed_delete.text)
        self.assertEqual(replayed_delete.json()["revision"], deleted.json()["revision"])

    def test_admin_winback_pilot_decision_fails_closed_without_live_evidence(self) -> None:
        from db import SessionLocal
        from models import IncentiveCampaign

        session = SessionLocal()
        try:
            row = IncentiveCampaign(
                name="Release 1.2 winback decision",
                campaign_type="promo",
                target_value="WIN10",
                objective="winback",
                lifecycle_status="draft",
                segment="expired_paid_7_30d",
                paid_cap=20,
                starts_at=self.api._utcnow() - timedelta(hours=1),
                ends_at=self.api._utcnow() + timedelta(hours=71),
            )
            session.add(row)
            session.commit()
            campaign_id = int(row.id)
        finally:
            session.close()

        response = self.client.get(
            f"/api/admin/campaigns/{campaign_id}/pilot-decision",
            headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["decision"]["recommendation"], "stop")
        self.assertEqual(body["decision"]["primary_metric"]["state"], "insufficient_data")
        self.assertFalse(body["decision"]["scale_automatic"])
        self.assertEqual(body["postmortem"]["winner_state"], "insufficient_data")
        self.assertIsNone(body["postmortem"]["winner"])

    def test_admin_campaign_live_activation_fails_closed_on_legal_contract(self) -> None:
        create_payload = self.api.AdminCampaignCreateIn(
            name="Blocked live campaign",
            campaign_type="promo",
            target_value="BLOCK10",
            objective="acquisition",
            lifecycle_status="draft",
            legal_profile_status="owner_approved",
            channels=["owned_web"],
            seller_profile_id="seller-owner-approved-v1",
            terms_revision=self.api.get_commercial_contract()["terms_revision"],
            paid_cap=10,
        ).model_dump()
        create_headers = self._prepare_admin_action(
            action="campaign.create",
            target_type="campaign",
            target_id="new",
            payload=create_payload,
        )
        created = self.client.post(
            "/api/admin/campaigns", headers=create_headers, json=create_payload
        )
        self.assertEqual(created.status_code, 200, created.text)
        campaign_id = int(created.json()["id"])
        replayed_create = self.client.post(
            "/api/admin/campaigns", headers=create_headers, json=create_payload
        )
        self.assertEqual(replayed_create.status_code, 200, replayed_create.text)
        self.assertEqual(int(replayed_create.json()["id"]), campaign_id)

        listed = self.client.get("/api/admin/campaigns", headers=self.admin_headers)
        row = next(
            item for item in listed.json()["campaigns"] if int(item["id"]) == campaign_id
        )
        update_payload = {
            "expected_revision": int(row["revision"]),
            "lifecycle_status": "live",
        }
        prepared = self.client.post(
            "/api/admin/action-intents",
            headers=self.admin_headers,
            json={
                "action": "campaign.update",
                "target": {"type": "campaign", "id": str(campaign_id)},
                "payload": update_payload,
            },
        )
        self.assertEqual(prepared.status_code, 200, prepared.text)
        preview = prepared.json()["preview"]
        self.assertIn("seller_unpublished", preview["after"]["policy"]["blocking_reasons"])
        confirmation = str(prepared.json()["confirmation_challenge"])
        blocked = self.client.patch(
            f"/api/admin/campaigns/{campaign_id}",
            headers={
                **self.admin_headers,
                "X-Admin-Intent-Id": str(prepared.json()["intent_id"]),
                "X-Admin-Idempotency-Key": str(uuid.uuid4()),
                "X-Admin-Confirmation-SHA256": hashlib.sha256(
                    confirmation.encode("utf-8")
                ).hexdigest(),
            },
            json=update_payload,
        )
        self.assertEqual(blocked.status_code, 409, blocked.text)
        self.assertEqual(blocked.json()["detail"]["code"], "campaign_policy_blocked")

        readback = self.client.get("/api/admin/campaigns", headers=self.admin_headers)
        current = next(
            item for item in readback.json()["campaigns"] if int(item["id"]) == campaign_id
        )
        self.assertEqual(current["lifecycle_status"], "draft")
        self.assertFalse(current["is_active"])

    def test_public_offer_preview_returns_server_base_for_unknown_promo(self) -> None:
        response = self.client.post(
            "/api/public/offers/preview",
            json={"plan_code": "3_months", "promo_code": "UNKNOWN10"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertFalse(body["valid"])
        self.assertEqual(body["reason_code"], "promo_unknown")
        self.assertEqual(body["base_price_rub"], 669)
        self.assertEqual(body["final_price_rub"], 669)
        self.assertEqual(body["benefit_rub"], 0)
        self.assertIsNone(body["offer_token"])
        self.assertEqual(
            response.headers["X-Pokrov-Commercial-Revision"],
            self.api.COMMERCIAL_REVISION,
        )
        self.assertEqual(response.headers["Cache-Control"], "no-store, private")

    def test_admin_node_runtime_and_sync_gap_routes(self) -> None:
        class FakePanel:
            async def login(self):
                return True

            async def get_node_runtime_snapshots(self, node_codes=None):
                codes = node_codes or ["nl-free"]
                return {
                    code: {
                        "node_code": code,
                        "panel": {"ok": True},
                        "dataplane": {"ok": True},
                        "transport": {"ok": True},
                    }
                    for code in codes
                }

            async def enable_client(self, _uuid, _enable):
                return True

            async def close(self):
                return None

        with patch.object(self.api, "ControlPanel", FakePanel):
            runtime = self.client.get("/api/admin/nodes/runtime?only=nl-free", headers=self.admin_headers)
            self.assertEqual(runtime.status_code, 200, runtime.text)
            self.assertEqual(runtime.json()["nodes"][0]["node_code"], "nl-free")

            sync_payload = {"tg_id": 1001, "segment": "active", "limit": 10}
            synced = self.client.post(
                "/api/admin/nodes/sync",
                headers=self._prepare_admin_action(
                    action="node.sync_global",
                    target_type="node_sync",
                    target_id="global",
                    payload=sync_payload,
                ),
                json=sync_payload,
            )
        self.assertEqual(synced.status_code, 200, synced.text)
        self.assertEqual(synced.json().get("synced"), 1)
