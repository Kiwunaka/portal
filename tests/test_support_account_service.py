from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1] / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


from models import (
    Account,
    AccountIdentity,
    AccountMergeReview,
    AppSetting,
    Base,
    EntitlementGrant,
    PaymentEntitlementClaim,
    SupportAttachment,
    SupportTicket,
    SupportTicketMessage,
    User,
)
from support_account_service import (
    SUPPORT_ACCOUNT_OWNERSHIP_BACKFILL_KEY,
    backfill_support_account_ownership,
    run_support_account_ownership_backfill_once,
)


NOW = datetime(2026, 7, 14, 12, 0, 0)


def _session_factory(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'support-account.db').as_posix()}")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)


def _account(account_id: str, *, merged_into: str | None = None) -> Account:
    return Account(
        id=account_id,
        status="merged" if merged_into else "active",
        created_source="test",
        merged_into_account_id=merged_into,
        created_at=NOW,
        updated_at=NOW,
    )


def _ticket(legacy_id: int, *, subject: str = "subject") -> SupportTicket:
    return SupportTicket(
        user_tg_id=legacy_id,
        status="open",
        subject=subject,
        created_at=NOW,
        updated_at=NOW,
    )


def _attachment(legacy_id: int, *, name: str = "evidence.png") -> SupportAttachment:
    return SupportAttachment(
        stored_name=f"stored-{legacy_id}-{name}",
        owner_tg_id=legacy_id,
        original_name=name,
        content_type="image/png",
        size_bytes=4,
        media_type="image",
        created_at=NOW,
    )


def test_backfill_resolves_direct_linked_enabled_identity_and_merged_accounts(tmp_path) -> None:
    _engine, Session = _session_factory(tmp_path)
    with Session() as session:
        session.add_all(
            [
                _account("direct-account"),
                _account("linked-account"),
                _account("merged-source", merged_into="merged-target"),
                _account("merged-target"),
                User(tg_id=101, account_id="direct-account"),
                User(tg_id=999, account_id="linked-account", linked_telegram_id=202),
                AccountIdentity(
                    account_id="merged-source",
                    kind="telegram",
                    provider="telegram",
                    subject_norm="303",
                    created_at=NOW,
                    updated_at=NOW,
                ),
                AccountIdentity(
                    account_id="direct-account",
                    kind="telegram",
                    provider="telegram",
                    subject_norm="404",
                    disabled_at=NOW,
                    created_at=NOW,
                    updated_at=NOW,
                ),
                _ticket(101),
                _ticket(202),
                _ticket(303),
                _ticket(404),
                _attachment(202),
            ]
        )
        session.flush()

        report = backfill_support_account_ownership(session, now=NOW)
        session.flush()

        tickets = {row.user_tg_id: row.account_id for row in session.query(SupportTicket).all()}
        attachment = session.query(SupportAttachment).one()
        assert tickets == {
            101: "direct-account",
            202: "linked-account",
            303: "merged-target",
            404: None,
        }
        assert attachment.owner_account_id == "linked-account"
        assert report.ticket_assignments == 3
        assert report.attachment_assignments == 1


def test_backfill_keeps_unmatched_and_ambiguous_rows_null_with_safe_reviews(tmp_path) -> None:
    _engine, Session = _session_factory(tmp_path)
    with Session() as session:
        session.add_all(
            [
                _account("candidate-a"),
                _account("candidate-b"),
                User(tg_id=501, account_id="candidate-a"),
                User(tg_id=900, account_id="candidate-b", linked_telegram_id=501),
                _ticket(501, subject="do-not-copy-ticket-text"),
                _ticket(777, subject="do-not-copy-unmatched-text"),
                _attachment(501, name="do-not-copy-filename.png"),
                _attachment(778, name="do-not-copy-unmatched-filename.png"),
            ]
        )
        session.flush()

        report = backfill_support_account_ownership(session, now=NOW)
        session.flush()

        assert all(row.account_id is None for row in session.query(SupportTicket).all())
        assert all(row.owner_account_id is None for row in session.query(SupportAttachment).all())
        reviews = session.query(AccountMergeReview).order_by(AccountMergeReview.reason_code.asc()).all()
        assert {row.reason_code for row in reviews} == {
            "support_attachment_owner_conflict",
            "support_attachment_owner_unresolved",
            "support_ticket_account_conflict",
            "support_ticket_account_unresolved",
        }
        assert report.conflicts == 2
        assert report.unresolved == 2
        serialized = "\n".join(str(row.details_json or "") for row in reviews)
        assert "do-not-copy" not in serialized
        for row in reviews:
            details = json.loads(str(row.details_json))
            assert set(details) == {"candidate_ids", "candidate_sources", "entity_id", "entity_type", "legacy_id", "reason"}
            assert details["reason"] == row.reason_code


def test_backfill_review_is_idempotent_and_direct_function_repairs_later_match(tmp_path) -> None:
    _engine, Session = _session_factory(tmp_path)
    with Session() as session:
        ticket = _ticket(601)
        session.add(ticket)
        session.flush()

        backfill_support_account_ownership(session, now=NOW)
        backfill_support_account_ownership(session, now=NOW)
        assert session.query(AccountMergeReview).count() == 1
        assert ticket.account_id is None

        session.add_all([_account("repair-account"), User(tg_id=601, account_id="repair-account")])
        session.flush()
        repair = backfill_support_account_ownership(session, now=NOW)

        assert ticket.account_id == "repair-account"
        assert repair.ticket_assignments == 1
        assert session.query(AccountMergeReview).count() == 1


def test_unchanged_idempotent_review_preserves_updated_at(tmp_path) -> None:
    _engine, Session = _session_factory(tmp_path)
    with Session() as session:
        session.add(_ticket(602))
        session.flush()

        backfill_support_account_ownership(session, now=NOW)
        session.flush()
        review = session.query(AccountMergeReview).one()
        original_updated_at = review.updated_at

        backfill_support_account_ownership(session, now=NOW + timedelta(hours=1))
        session.flush()

        assert session.query(AccountMergeReview).count() == 1
        assert review.updated_at == original_updated_at


def test_startup_marker_is_distinct_gated_and_direct_repair_remains_callable(tmp_path) -> None:
    from account_foundation_service import ACCOUNT_FOUNDATION_BACKFILL_KEY

    _engine, Session = _session_factory(tmp_path)
    with Session() as session:
        session.add_all([_account("account-701"), User(tg_id=701, account_id="account-701"), _ticket(701)])
        session.flush()

        first = run_support_account_ownership_backfill_once(session, now=NOW)
        session.commit()
        assert first.ticket_assignments == 1
        marker = session.query(AppSetting).filter_by(key=SUPPORT_ACCOUNT_OWNERSHIP_BACKFILL_KEY).one()
        assert SUPPORT_ACCOUNT_OWNERSHIP_BACKFILL_KEY != ACCOUNT_FOUNDATION_BACKFILL_KEY
        assert json.loads(str(marker.value_json))["status"] == "complete"

        late = _ticket(701)
        session.add(late)
        session.commit()
        second = run_support_account_ownership_backfill_once(session, now=NOW)
        assert second.ticket_assignments == 0
        assert late.account_id is None

        repaired = backfill_support_account_ownership(session, now=NOW)
        assert repaired.ticket_assignments == 1
        assert late.account_id == "account-701"


def test_startup_marker_ownership_and_reviews_rollback_together_on_commit_failure(tmp_path) -> None:
    _engine, Session = _session_factory(tmp_path)
    with Session() as session:
        session.add_all([_account("account-801"), User(tg_id=801, account_id="account-801"), _ticket(801), _ticket(802)])
        session.commit()

        run_support_account_ownership_backfill_once(session, now=NOW)

        def _fail_commit(_session) -> None:
            raise RuntimeError("forced commit failure")

        event.listen(session, "before_commit", _fail_commit, once=True)
        with pytest.raises(RuntimeError, match="forced commit failure"):
            session.commit()
        session.rollback()

    with Session() as verification:
        assert verification.query(SupportTicket).filter(SupportTicket.account_id.isnot(None)).count() == 0
        assert verification.query(AccountMergeReview).count() == 0
        assert verification.query(AppSetting).filter_by(key=SUPPORT_ACCOUNT_OWNERSHIP_BACKFILL_KEY).count() == 0


def test_account_merge_moves_support_owners_without_rewriting_history_or_other_authority(tmp_path) -> None:
    from account_foundation_service import _move_account_owned_rows

    _engine, Session = _session_factory(tmp_path)
    with Session() as session:
        session.add_all([_account("merge-source"), _account("merge-target"), _account("unrelated-account")])
        ticket = _ticket(901, subject="preserve subject")
        ticket.account_id = "merge-source"
        attachment = _attachment(901, name="preserve-name.png")
        attachment.owner_account_id = "merge-source"
        unrelated_grant = EntitlementGrant(
            id="unrelated-grant",
            account_id="unrelated-account",
            idempotency_key="unrelated-grant-key",
            source="manual",
            status="active",
            grant_kind="paid_access",
            plan_code="month",
            created_at=NOW,
            updated_at=NOW,
        )
        unrelated_payment = PaymentEntitlementClaim(
            provider="test-provider",
            order_id="unrelated-order",
            buyer_email_norm="redacted@example.invalid",
            account_id="unrelated-account",
            status="fulfilled",
            plan_code="month",
            duration_days=30,
            created_at=NOW,
            updated_at=NOW,
        )
        session.add_all([ticket, attachment, unrelated_grant, unrelated_payment])
        session.flush()
        message = SupportTicketMessage(
            ticket_id=ticket.id,
            sender_tg_id=901,
            sender_role="user",
            body="preserve body",
            media_type="photo",
            media_file_id="preserve-file-id",
            media_payload='{"preserve":true}',
            created_at=NOW,
        )
        session.add(message)
        session.flush()
        original_ids = (ticket.id, attachment.id, message.id)

        _move_account_owned_rows(
            session,
            source_account_id="merge-source",
            target_account_id="merge-target",
            now=NOW,
        )
        session.flush()

        assert (ticket.id, attachment.id, message.id) == original_ids
        assert ticket.account_id == "merge-target"
        assert attachment.owner_account_id == "merge-target"
        assert (ticket.user_tg_id, ticket.subject) == (901, "preserve subject")
        assert (attachment.owner_tg_id, attachment.original_name) == (901, "preserve-name.png")
        assert (message.body, message.media_file_id, message.media_payload) == (
            "preserve body",
            "preserve-file-id",
            '{"preserve":true}',
        )
        assert unrelated_grant.account_id == "unrelated-account"
        assert unrelated_payment.account_id == "unrelated-account"
        assert unrelated_payment.status == "fulfilled"


def test_database_startup_runs_support_backfill_after_account_foundation_in_one_commit_scope() -> None:
    source = (Path(__file__).resolve().parents[1] / "portal_bot" / "db.py").read_text(encoding="utf-8")

    account_call = "run_account_foundation_backfill_once(session)"
    support_call = "run_support_account_ownership_backfill_once(session)"
    commit_call = "session.commit()"
    assert support_call in source
    assert source.index(account_call) < source.index(support_call) < source.index(commit_call)
