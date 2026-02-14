import os
import sys
import unittest
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class NodesRepoLoadAwareTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        portal_dir = str(repo_root / "portal_bot")
        if portal_dir not in sys.path:
            sys.path.insert(0, portal_dir)

        from models import Base

        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

        self._saved = {}
        for k in ("DATABASE_URL", "BOT_TOKEN"):
            self._saved[k] = os.environ.get(k)
            os.environ[k] = "sqlite:///:memory:" if k == "DATABASE_URL" else "test_bot_token_123"

    def tearDown(self) -> None:
        self.engine.dispose()
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_enabled_nodes_prefers_healthy_by_score(self) -> None:
        from models import Node
        from nodes_repo import enabled_nodes

        s = self.Session()
        try:
            s.add_all(
                [
                    Node(
                        code="pl",
                        name="Poland A",
                        host="pl-a.test",
                        vless_port=443,
                        reality_sni="a.test",
                        reality_pbk="pbk",
                        reality_sid="sid",
                        panel_base_url="http://pl-a",
                        panel_path="xui",
                        panel_user="u",
                        panel_pass="p",
                        inbound_id=1,
                        enabled=True,
                        weight=100,
                        health_score=25.0,
                        is_healthy=True,
                    ),
                    Node(
                        code="pl_b",
                        name="Poland B",
                        host="pl-b.test",
                        vless_port=443,
                        reality_sni="b.test",
                        reality_pbk="pbk",
                        reality_sid="sid",
                        panel_base_url="http://pl-b",
                        panel_path="xui",
                        panel_user="u",
                        panel_pass="p",
                        inbound_id=1,
                        enabled=True,
                        weight=80,
                        health_score=80.0,
                        is_healthy=True,
                    ),
                    Node(
                        code="it",
                        name="Italy",
                        host="it.test",
                        vless_port=443,
                        reality_sni="it.test",
                        reality_pbk="pbk",
                        reality_sid="sid",
                        panel_base_url="http://it",
                        panel_path="xui",
                        panel_user="u",
                        panel_pass="p",
                        inbound_id=1,
                        enabled=True,
                        weight=100,
                        health_score=99.0,
                        is_healthy=False,
                    ),
                ]
            )
            s.commit()
            rows = enabled_nodes(s)
            self.assertEqual(rows[0].code, "pl_b")
            self.assertNotIn("it", [n.code for n in rows])
        finally:
            s.close()

    def test_enabled_nodes_falls_back_when_all_unhealthy(self) -> None:
        from models import Node
        from nodes_repo import enabled_nodes

        s = self.Session()
        try:
            s.add_all(
                [
                    Node(
                        code="us_a",
                        name="US A",
                        host="us-a.test",
                        vless_port=443,
                        reality_sni="us.test",
                        reality_pbk="pbk",
                        reality_sid="sid",
                        panel_base_url="http://us-a",
                        panel_path="xui",
                        panel_user="u",
                        panel_pass="p",
                        inbound_id=1,
                        enabled=True,
                        weight=20,
                        health_score=10.0,
                        is_healthy=False,
                    ),
                    Node(
                        code="us_b",
                        name="US B",
                        host="us-b.test",
                        vless_port=443,
                        reality_sni="us.test",
                        reality_pbk="pbk",
                        reality_sid="sid",
                        panel_base_url="http://us-b",
                        panel_path="xui",
                        panel_user="u",
                        panel_pass="p",
                        inbound_id=1,
                        enabled=True,
                        weight=10,
                        health_score=50.0,
                        is_healthy=False,
                    ),
                ]
            )
            s.commit()
            rows = enabled_nodes(s)
            self.assertEqual(rows[0].code, "us_b")
            self.assertEqual(len(rows), 2)
        finally:
            s.close()

    def test_enabled_nodes_includes_nl_premium_and_nl_free_codes(self) -> None:
        from models import Node
        from nodes_repo import enabled_nodes

        s = self.Session()
        try:
            s.add_all(
                [
                    Node(
                        code="nl",
                        name="Netherlands Premium",
                        host="nl.test",
                        vless_port=443,
                        reality_sni="nl.test",
                        reality_pbk="pbk",
                        reality_sid="sid",
                        panel_base_url="http://nl",
                        panel_path="xui",
                        panel_user="u",
                        panel_pass="p",
                        inbound_id=1,
                        enabled=True,
                        weight=100,
                        health_score=75.0,
                        is_healthy=True,
                    ),
                    Node(
                        code="pl_free",
                        name="NL Free",
                        host="free.test",
                        vless_port=443,
                        reality_sni="free.test",
                        reality_pbk="pbk",
                        reality_sid="sid",
                        panel_base_url="http://free",
                        panel_path="xui",
                        panel_user="u",
                        panel_pass="p",
                        inbound_id=1,
                        enabled=True,
                        weight=90,
                        health_score=55.0,
                        is_healthy=True,
                    ),
                ]
            )
            s.commit()
            rows = enabled_nodes(s)
            codes = [n.code for n in rows]
            self.assertIn("nl", codes)
            self.assertIn("pl_free", codes)
            self.assertEqual(codes[0], "nl")
        finally:
            s.close()


if __name__ == "__main__":
    unittest.main()
