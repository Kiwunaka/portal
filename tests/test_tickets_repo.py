import sys
import unittest
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


class TicketRepoTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        portal_dir = str(repo_root / "portal_bot")
        if portal_dir not in sys.path:
            sys.path.insert(0, portal_dir)

        from migrations import run_migrations
        from models import Base

        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        run_migrations(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def tearDown(self) -> None:
        self.engine.dispose()

    def test_ticket_tables_and_indexes_exist(self) -> None:
        with self.engine.connect() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table';")
                ).fetchall()
            }
            indexes = {
                row[0]
                for row in conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='index';")
                ).fetchall()
            }

        self.assertIn("support_tickets", tables)
        self.assertIn("support_ticket_messages", tables)
        self.assertIn("ix_support_tickets_status", indexes)
        self.assertIn("ix_support_ticket_messages_ticket_id", indexes)

    def test_ticket_lifecycle_and_messages(self) -> None:
        from tickets_repo import (
            STATUS_CLOSED,
            STATUS_IN_PROGRESS,
            STATUS_OPEN,
            add_ticket_message,
            create_ticket,
            get_user_active_ticket,
            list_ticket_messages,
            list_user_tickets,
            set_ticket_status,
        )

        s = self.Session()
        try:
            t = create_ticket(s, user_tg_id=1001)
            add_ticket_message(
                s,
                ticket_id=t.id,
                sender_tg_id=1001,
                sender_role="user",
                body="First issue details",
                media_type="photo",
                media_file_id="abc123",
                media_payload='{"w":1280,"h":720}',
            )
            set_ticket_status(s, ticket=t, status=STATUS_OPEN)
            s.commit()

            self.assertEqual(t.status, STATUS_OPEN)
            self.assertIsNotNone(get_user_active_ticket(s, 1001))
            self.assertEqual(len(list_user_tickets(s, 1001, limit=10)), 1)
            self.assertEqual(len(list_ticket_messages(s, t.id, limit=10)), 1)
            first = list_ticket_messages(s, t.id, limit=10)[0]
            self.assertEqual(first.media_type, "photo")
            self.assertEqual(first.media_file_id, "abc123")

            add_ticket_message(
                s,
                ticket_id=t.id,
                sender_tg_id=9999,
                sender_role="admin",
                body="Operator reply",
            )
            set_ticket_status(s, ticket=t, status=STATUS_IN_PROGRESS, assigned_admin_tg_id=9999)
            s.commit()
            self.assertEqual(t.status, STATUS_IN_PROGRESS)
            self.assertEqual(t.assigned_admin_tg_id, 9999)

            set_ticket_status(s, ticket=t, status=STATUS_CLOSED)
            s.commit()
            self.assertEqual(t.status, STATUS_CLOSED)
            self.assertIsNone(get_user_active_ticket(s, 1001))
        finally:
            s.close()

    def test_ticket_access_policy(self) -> None:
        from tickets_repo import can_access_ticket, create_ticket

        s = self.Session()
        try:
            t = create_ticket(s, user_tg_id=42)
            s.commit()
            self.assertTrue(can_access_ticket(t, 42, 999))
            self.assertTrue(can_access_ticket(t, 999, 999))
            self.assertFalse(can_access_ticket(t, 777, 999))
        finally:
            s.close()


if __name__ == "__main__":
    unittest.main()
