import sys
import unittest
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
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
            add_ticket_message(
                s,
                ticket_id=t.id,
                sender_tg_id=0,
                sender_role="assistant",
                body="Automated support hint",
            )
            set_ticket_status(s, ticket=t, status=STATUS_IN_PROGRESS, assigned_admin_tg_id=9999)
            s.commit()
            self.assertEqual(t.status, STATUS_IN_PROGRESS)
            self.assertEqual(t.assigned_admin_tg_id, 9999)
            self.assertEqual(
                [message.sender_role for message in list_ticket_messages(s, t.id, limit=10)],
                ["user", "admin", "assistant"],
            )

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

    def test_support_models_declare_nullable_indexed_account_ownership(self) -> None:
        from models import SupportAttachment, SupportTicket

        ticket_column = SupportTicket.__table__.c.account_id
        attachment_column = SupportAttachment.__table__.c.owner_account_id

        self.assertTrue(ticket_column.nullable)
        self.assertEqual(ticket_column.type.length, 36)
        self.assertTrue(ticket_column.index)
        self.assertTrue(attachment_column.nullable)
        self.assertEqual(attachment_column.type.length, 36)
        self.assertTrue(attachment_column.index)

    def test_sqlite_support_ownership_migration_is_rerunnable_and_preserves_legacy_rows(self) -> None:
        from migrations import run_migrations
        from models import Base

        engine = create_engine("sqlite:///:memory:")
        try:
            Base.metadata.create_all(engine)
            with engine.begin() as conn:
                conn.execute(text("DROP TABLE support_ticket_messages"))
                conn.execute(text("DROP TABLE support_tickets"))
                conn.execute(text("DROP TABLE support_attachments"))
                conn.execute(
                    text(
                        "CREATE TABLE support_tickets ("
                        "id INTEGER PRIMARY KEY, user_tg_id BIGINT NOT NULL, status VARCHAR(20), "
                        "subject VARCHAR(200), assigned_admin_tg_id BIGINT, created_at DATETIME NOT NULL, "
                        "updated_at DATETIME, closed_at DATETIME)"
                    )
                )
                conn.execute(
                    text(
                        "CREATE TABLE support_ticket_messages ("
                        "id INTEGER PRIMARY KEY, ticket_id INTEGER NOT NULL, sender_tg_id BIGINT NOT NULL, "
                        "sender_role VARCHAR(20) NOT NULL, body VARCHAR(2000) NOT NULL, "
                        "media_type VARCHAR(32), media_file_id VARCHAR(256), media_payload VARCHAR(2000), "
                        "created_at DATETIME NOT NULL)"
                    )
                )
                conn.execute(
                    text(
                        "CREATE TABLE support_attachments ("
                        "id INTEGER PRIMARY KEY, stored_name VARCHAR(160) NOT NULL, owner_tg_id BIGINT NOT NULL, "
                        "original_name VARCHAR(160) NOT NULL, content_type VARCHAR(80) NOT NULL, "
                        "size_bytes INTEGER NOT NULL, media_type VARCHAR(32) NOT NULL, created_at DATETIME NOT NULL)"
                    )
                )
                conn.execute(
                    text(
                        "INSERT INTO support_tickets "
                        "(id,user_tg_id,status,subject,created_at,updated_at) "
                        "VALUES (7,1001,'open','legacy subject','2026-07-14','2026-07-14')"
                    )
                )
                conn.execute(
                    text(
                        "INSERT INTO support_ticket_messages "
                        "(id,ticket_id,sender_tg_id,sender_role,body,media_type,media_file_id,media_payload,created_at) "
                        "VALUES (9,7,1001,'user','legacy body','photo','telegram-file',:payload,'2026-07-14')"
                    ),
                    {"payload": '{"safe":true}'},
                )
                conn.execute(
                    text(
                        "INSERT INTO support_attachments "
                        "(id,stored_name,owner_tg_id,original_name,content_type,size_bytes,media_type,created_at) "
                        "VALUES (11,'stored.png',1001,'legacy.png','image/png',4,'image','2026-07-14')"
                    )
                )

            run_migrations(engine)
            run_migrations(engine)

            columns = {
                table: {column["name"] for column in inspect(engine).get_columns(table)}
                for table in ("support_tickets", "support_attachments")
            }
            indexes = {
                row["name"]
                for table in ("support_tickets", "support_attachments")
                for row in inspect(engine).get_indexes(table)
            }
            with engine.connect() as conn:
                ticket = conn.execute(text("SELECT user_tg_id, subject, account_id FROM support_tickets WHERE id=7")).one()
                message = conn.execute(
                    text("SELECT body, media_type, media_file_id, media_payload FROM support_ticket_messages WHERE id=9")
                ).one()
                attachment = conn.execute(
                    text("SELECT owner_tg_id, original_name, owner_account_id FROM support_attachments WHERE id=11")
                ).one()

            self.assertIn("account_id", columns["support_tickets"])
            self.assertIn("owner_account_id", columns["support_attachments"])
            self.assertIn("ix_support_tickets_account_id", indexes)
            self.assertIn("ix_support_attachments_owner_account_id", indexes)
            self.assertEqual(tuple(ticket), (1001, "legacy subject", None))
            self.assertEqual(tuple(message), ("legacy body", "photo", "telegram-file", '{"safe":true}'))
            self.assertEqual(tuple(attachment), (1001, "legacy.png", None))
        finally:
            engine.dispose()

    def test_account_owned_history_is_shared_across_tg_ids_without_wrong_owner_fallback(self) -> None:
        from models import Account, SupportTicket, User
        from tickets_repo import can_access_ticket, create_ticket, list_user_tickets

        s = self.Session()
        try:
            s.add_all(
                [
                    Account(id="shared-account", status="active", created_source="test"),
                    Account(id="other-account", status="active", created_source="test"),
                    User(tg_id=1001, account_id="shared-account"),
                    User(tg_id=2002, account_id="shared-account"),
                    User(tg_id=3003, account_id="other-account"),
                ]
            )
            s.flush()
            shared = create_ticket(s, user_tg_id=1001, account_id="shared-account")
            tempting = SupportTicket(
                user_tg_id=2002,
                account_id="other-account",
                status="open",
                created_at=shared.created_at,
                updated_at=shared.updated_at,
            )
            legacy = SupportTicket(
                user_tg_id=2002,
                account_id=None,
                status="open",
                created_at=shared.created_at,
                updated_at=shared.updated_at,
            )
            s.add_all([tempting, legacy])
            s.flush()

            visible = list_user_tickets(s, 2002, account_id="shared-account", limit=10)

            self.assertIn(shared.id, [row.id for row in visible])
            self.assertIn(legacy.id, [row.id for row in visible])
            self.assertNotIn(tempting.id, [row.id for row in visible])
            self.assertTrue(can_access_ticket(shared, 2002, 9999, account_id="shared-account"))
            self.assertTrue(can_access_ticket(legacy, 2002, 9999, account_id="shared-account"))
            self.assertFalse(can_access_ticket(tempting, 2002, 9999, account_id="shared-account"))
            self.assertTrue(can_access_ticket(tempting, 9999, 9999, account_id=None))
            self.assertIsNone(legacy.account_id)
            self.assertEqual(s.query(SupportTicket).count(), 3)
        finally:
            s.close()

    def test_active_selection_uses_account_or_null_legacy_and_claims_only_eligible_write(self) -> None:
        from datetime import datetime, timedelta

        from models import Account, SupportTicket, User
        from tickets_repo import claim_legacy_ticket, get_user_active_ticket

        s = self.Session()
        try:
            s.add_all(
                [
                    Account(id="claim-account", status="active", created_source="test"),
                    User(tg_id=4100, account_id="claim-account"),
                ]
            )
            base = datetime(2026, 7, 14, 10, 0, 0)
            older = SupportTicket(user_tg_id=4100, account_id="claim-account", status="open", created_at=base, updated_at=base)
            newer_null = SupportTicket(
                user_tg_id=4100,
                account_id=None,
                status="in_progress",
                created_at=base,
                updated_at=base + timedelta(minutes=1),
            )
            duplicate_time = SupportTicket(
                user_tg_id=4100,
                account_id=None,
                status="open",
                created_at=base,
                updated_at=base + timedelta(minutes=1),
            )
            s.add_all([older, newer_null, duplicate_time])
            s.flush()

            active = get_user_active_ticket(s, 4100, account_id="claim-account")

            self.assertEqual(active.id, duplicate_time.id)
            self.assertTrue(claim_legacy_ticket(active, actor_tg_id=4100, account_id="claim-account"))
            self.assertEqual(active.account_id, "claim-account")
            self.assertFalse(claim_legacy_ticket(newer_null, actor_tg_id=999, account_id="claim-account"))
            self.assertIsNone(newer_null.account_id)
            self.assertEqual(s.query(SupportTicket).count(), 3)
        finally:
            s.close()

    def test_repository_resolver_and_notification_prefer_explicit_linked_telegram(self) -> None:
        from models import Account, User
        from tickets_repo import (
            create_ticket,
            resolve_support_account_id,
            resolve_ticket_notification_tg_id,
        )

        s = self.Session()
        try:
            s.add_all(
                [
                    Account(id="source-account", status="merged", created_source="test", merged_into_account_id="target-account"),
                    Account(id="target-account", status="active", created_source="test"),
                    User(tg_id=8_000_000_000_101, account_id="source-account", linked_telegram_id=5101),
                ]
            )
            s.flush()

            resolved = resolve_support_account_id(s, account_id="source-account", user_tg_id=8_000_000_000_101)
            ticket = create_ticket(s, user_tg_id=8_000_000_000_101, account_id=resolved)

            self.assertEqual(resolved, "target-account")
            self.assertEqual(ticket.account_id, "target-account")
            self.assertEqual(resolve_ticket_notification_tg_id(s, ticket), 5101)
        finally:
            s.close()

    def test_notification_target_uses_enabled_telegram_identity_without_linked_user(self) -> None:
        from models import Account, AccountIdentity
        from tickets_repo import create_ticket, resolve_ticket_notification_tg_id

        s = self.Session()
        try:
            s.add_all(
                [
                    Account(id="identity-target-account", status="active", created_source="test"),
                    AccountIdentity(
                        account_id="identity-target-account",
                        kind="telegram",
                        provider="telegram",
                        subject_norm="5202",
                    ),
                ]
            )
            s.flush()
            ticket = create_ticket(
                s,
                user_tg_id=8_000_000_000_202,
                account_id="identity-target-account",
            )

            self.assertEqual(resolve_ticket_notification_tg_id(s, ticket), 5202)
        finally:
            s.close()

    def test_notification_target_returns_none_for_synthetic_owner_without_link(self) -> None:
        from models import Account
        from tickets_repo import create_ticket, resolve_ticket_notification_tg_id

        s = self.Session()
        try:
            s.add(Account(id="synthetic-only-account", status="active", created_source="test"))
            s.flush()
            ticket = create_ticket(
                s,
                user_tg_id=8_000_000_000_303,
                account_id="synthetic-only-account",
            )

            self.assertIsNone(resolve_ticket_notification_tg_id(s, ticket))
        finally:
            s.close()


if __name__ == "__main__":
    unittest.main()
