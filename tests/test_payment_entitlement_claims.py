from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
import sys
import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1] / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


import migrations  # noqa: E402
import models  # noqa: E402
from account_foundation_service import _move_account_owned_rows  # noqa: E402


NOW = datetime(2026, 7, 13, 10, 0, 0)


def _session(tmp_path: Path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'claims.db').as_posix()}")
    models.Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)()


def _account(session, account_id: str, email: str):
    account = models.Account(
        id=account_id,
        status="active",
        created_source="test",
        created_at=NOW,
        updated_at=NOW,
    )
    session.add(account)
    tg_id = 10_000 + int(session.query(models.Account).count())
    session.add(
        models.User(
            tg_id=tg_id,
            uuid=str(uuid.uuid4()),
            email=f"user_{tg_id}",
            account_id=account_id,
            sub_type="FREE",
            current_plan_code="free_monthly",
            expiry_at=NOW,
            is_active=True,
            created_at=NOW,
            tos_accepted=True,
        )
    )
    session.add(
        models.AccountIdentity(
            account_id=account_id,
            kind="email",
            provider="email",
            subject_norm=email,
            verified_at=NOW,
            created_at=NOW,
            updated_at=NOW,
        )
    )
    session.flush()
    return account


def _pending_claim(session, *, order_id: str = "order-1", email: str = "buyer@example.test"):
    from payment_entitlement_service import ensure_pending_claim

    return ensure_pending_claim(
        session,
        provider="lavatop",
        order_id=order_id,
        buyer_email=email,
        plan_code="1_month",
        duration_days=30,
        now=NOW,
    ).claim


def test_model_contract_and_unique_provider_order() -> None:
    table = models.Base.metadata.tables["payment_entitlement_claims"]
    assert {
        "provider",
        "order_id",
        "buyer_email_norm",
        "account_id",
        "status",
        "plan_code",
        "duration_days",
        "grant_id",
        "fallback_gift_card_id",
        "paid_at",
        "attached_at",
        "fulfilled_at",
        "reversed_at",
        "reversal_reason",
        "last_error",
        "last_error_at",
        "created_at",
        "updated_at",
    } <= set(table.c.keys())
    assert any(
        set(constraint.columns.keys()) == {"provider", "order_id"}
        for constraint in table.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    )


def test_external_order_attention_index_contract_and_migrations(tmp_path: Path) -> None:
    table = models.Base.metadata.tables["external_orders"]
    assert any(
        index.name == "ix_external_orders_status_created_at_id"
        and tuple(index.columns.keys()) == ("status", "created_at", "id")
        for index in table.indexes
    )

    engine = create_engine(f"sqlite:///{(tmp_path / 'external-order-index.db').as_posix()}")
    models.Base.metadata.create_all(engine)
    migrations.run_migrations(engine)
    migrations.run_migrations(engine)
    with engine.begin() as conn:
        indexes = {
            row[1]: tuple(
                item[2]
                for item in conn.execute(text(f"PRAGMA index_info('{row[1]}')"))
            )
            for row in conn.execute(text("PRAGMA index_list('external_orders')"))
        }
        query_plan = " ".join(
            str(item)
            for row in conn.execute(text(
                "EXPLAIN QUERY PLAN SELECT id FROM external_orders "
                "WHERE status IN ('refunded', 'chargeback') ORDER BY created_at DESC, id DESC"
            ))
            for item in row
        )
    assert indexes["ix_external_orders_status_created_at_id"] == ("status", "created_at", "id")
    assert "ix_external_orders_status_created_at_id" in query_plan

    class _Conn:
        def __init__(self):
            self.sql: list[str] = []

        def execute(self, statement, params=None):
            self.sql.append(str(statement))

    conn = _Conn()
    migrations._ensure_external_order_attention_index(conn)
    migrations._ensure_external_order_attention_index(conn)
    ddl = "\n".join(conn.sql)
    assert ddl.count("CREATE INDEX IF NOT EXISTS ix_external_orders_status_created_at_id") == 2
    assert "external_orders(status, created_at, id)" in ddl
    assert "DROP " not in ddl.upper()


def test_paid_before_attach_fulfills_once(tmp_path: Path) -> None:
    from payment_entitlement_service import attach_by_verified_email, fulfill_attached_paid_claim, mark_paid

    _engine, session = _session(tmp_path)
    _account(session, "account-a", "buyer@example.test")
    claim = _pending_claim(session)

    assert mark_paid(session, provider="lavatop", order_id="order-1", paid_at=NOW).claim.status == "paid_unclaimed"
    assert attach_by_verified_email(
        session,
        provider="lavatop",
        order_id="order-1",
        buyer_email=" BUYER@example.test ",
        account_id="account-a",
        now=NOW,
    ).claim.status == "paid_attached"
    first = fulfill_attached_paid_claim(session, provider="lavatop", order_id="order-1", now=NOW)
    second = fulfill_attached_paid_claim(session, provider="lavatop", order_id="order-1", now=NOW)

    assert first.claim.status == "fulfilled"
    assert second.code == "already_fulfilled"
    assert session.query(models.EntitlementGrant).filter_by(source="provider_payment").count() == 1
    assert claim.grant_id == first.claim.grant_id


def test_attach_before_paid_and_same_account_retry_are_idempotent(tmp_path: Path) -> None:
    from payment_entitlement_service import attach_by_verified_email, fulfill_attached_paid_claim, mark_paid

    _engine, session = _session(tmp_path)
    _account(session, "account-a", "buyer@example.test")
    _pending_claim(session)

    first = attach_by_verified_email(
        session,
        provider="lavatop",
        order_id="order-1",
        buyer_email="buyer@example.test",
        account_id="account-a",
        now=NOW,
    )
    second = attach_by_verified_email(
        session,
        provider="lavatop",
        order_id="order-1",
        buyer_email="buyer@example.test",
        account_id="account-a",
        now=NOW,
    )

    assert first.claim.status == "attached_pending_payment"
    assert second.code == "already_attached"
    assert mark_paid(session, provider="lavatop", order_id="order-1", paid_at=NOW).claim.status == "paid_attached"
    assert fulfill_attached_paid_claim(session, provider="lavatop", order_id="order-1", now=NOW).claim.status == "fulfilled"


def test_cross_account_attach_never_transfers_access(tmp_path: Path) -> None:
    from payment_entitlement_service import attach_by_verified_email, fulfill_attached_paid_claim, mark_paid

    _engine, session = _session(tmp_path)
    _account(session, "account-a", "buyer@example.test")
    _account(session, "account-b", "other@example.test")
    _pending_claim(session)
    mark_paid(session, provider="lavatop", order_id="order-1", paid_at=NOW)
    attach_by_verified_email(
        session,
        provider="lavatop",
        order_id="order-1",
        buyer_email="buyer@example.test",
        account_id="account-a",
        now=NOW,
    )
    fulfill_attached_paid_claim(session, provider="lavatop", order_id="order-1", now=NOW)

    conflict = attach_by_verified_email(
        session,
        provider="lavatop",
        order_id="order-1",
        buyer_email="other@example.test",
        account_id="account-b",
        now=NOW,
    )

    assert conflict.code == "account_conflict"
    assert conflict.claim.status == "fulfilled"
    assert conflict.claim.account_id == "account-a"
    assert conflict.claim.last_error == "account_conflict"
    assert conflict.claim.last_error_at == NOW
    grant = session.get(models.EntitlementGrant, conflict.claim.grant_id)
    assert grant.account_id == "account-a"


def test_terminal_claim_definition_conflict_does_not_replace_state(tmp_path: Path) -> None:
    from payment_entitlement_service import (
        attach_by_verified_email,
        ensure_pending_claim,
        fulfill_attached_paid_claim,
        mark_paid,
        reverse_claim,
    )

    _engine, session = _session(tmp_path)
    _account(session, "account-a", "buyer@example.test")
    _pending_claim(session, order_id="fulfilled-order")
    mark_paid(session, provider="lavatop", order_id="fulfilled-order", paid_at=NOW)
    attach_by_verified_email(
        session,
        provider="lavatop",
        order_id="fulfilled-order",
        buyer_email="buyer@example.test",
        account_id="account-a",
        now=NOW,
    )
    fulfilled = fulfill_attached_paid_claim(
        session,
        provider="lavatop",
        order_id="fulfilled-order",
        now=NOW,
    )

    conflict = ensure_pending_claim(
        session,
        provider="lavatop",
        order_id="fulfilled-order",
        buyer_email="changed@example.test",
        plan_code="other_plan",
        duration_days=90,
        now=NOW,
    )
    assert conflict.code == "claim_definition_conflict"
    assert conflict.claim.status == "fulfilled"
    assert conflict.claim.grant_id == fulfilled.claim.grant_id

    reverse_claim(
        session,
        provider="lavatop",
        order_id="fulfilled-order",
        reason="refund",
        reversed_at=NOW,
    )
    reversed_conflict = ensure_pending_claim(
        session,
        provider="lavatop",
        order_id="fulfilled-order",
        buyer_email="changed@example.test",
        plan_code="other_plan",
        duration_days=90,
        now=NOW,
    )
    assert reversed_conflict.claim.status == "reversed"


def test_manual_review_blocks_payment_fallback_redemption(tmp_path: Path) -> None:
    from payment_entitlement_service import ensure_fallback_gift_card, mark_paid, redeem_payment_fallback

    _engine, session = _session(tmp_path)
    _account(session, "account-a", "buyer@example.test")
    claim = _pending_claim(session)
    mark_paid(session, provider="lavatop", order_id="order-1", paid_at=NOW)
    fallback = ensure_fallback_gift_card(
        session,
        provider="lavatop",
        order_id="order-1",
        gift_code="POKROV-MANUAL-REVIEW",
        now=NOW,
    )
    claim.status = "manual_review"
    claim.last_error = "verified_email_mismatch"
    claim.last_error_at = NOW
    session.flush()

    result = redeem_payment_fallback(
        session,
        gift_card_id=int(fallback.claim.fallback_gift_card_id),
        account_id="account-a",
        legacy_tg_id=10001,
        now=NOW,
    )

    assert result.code == "manual_review"
    assert result.claim.account_id is None
    assert session.query(models.EntitlementGrant).filter_by(source="provider_payment").count() == 0


def test_last_safe_error_evidence_survives_successful_retry(tmp_path: Path) -> None:
    from payment_entitlement_service import mark_paid, record_claim_error

    _engine, session = _session(tmp_path)
    claim = _pending_claim(session)
    record_claim_error(
        session,
        provider="lavatop",
        order_id="order-1",
        error_code="durable_fulfillment_failed",
        now=NOW,
    )
    error_at = claim.last_error_at

    mark_paid(
        session,
        provider="lavatop",
        order_id="order-1",
        paid_at=datetime(2026, 7, 13, 11, 0, 0),
    )

    assert claim.last_error == "durable_fulfillment_failed"
    assert claim.last_error_at == error_at == NOW


def test_missing_linked_fallback_is_not_durable_success(tmp_path: Path) -> None:
    from payment_entitlement_service import ensure_fallback_gift_card, mark_paid

    _engine, session = _session(tmp_path)
    claim = _pending_claim(session)
    mark_paid(session, provider="lavatop", order_id="order-1", paid_at=NOW)
    claim.fallback_gift_card_id = 999999
    session.flush()

    result = ensure_fallback_gift_card(
        session,
        provider="lavatop",
        order_id="order-1",
        gift_code="POKROV-NOT-CREATED",
        now=NOW,
    )

    assert result.code == "fallback_missing"
    assert result.claim.status == "manual_review"
    assert result.claim.last_error == "fallback_missing"
    assert result.claim.last_error_at == NOW
    assert session.query(models.GiftCard).count() == 0


def test_existing_unredeemed_legacy_fallback_is_linked_once(tmp_path: Path) -> None:
    from payment_entitlement_service import ensure_fallback_gift_card, mark_paid

    _engine, session = _session(tmp_path)
    claim = _pending_claim(session)
    mark_paid(session, provider="lavatop", order_id="order-1", paid_at=NOW)
    card = models.GiftCard(
        code="POKROV-LEGACY-PAID",
        card_type="1_month",
        created_by=0,
        created_at=NOW,
    )
    session.add(card)
    session.flush()

    first = ensure_fallback_gift_card(
        session,
        provider="lavatop",
        order_id="order-1",
        gift_code="POKROV-LEGACY-PAID",
        now=NOW,
    )
    second = ensure_fallback_gift_card(
        session,
        provider="lavatop",
        order_id="order-1",
        gift_code="POKROV-LEGACY-PAID",
        now=NOW,
    )

    assert first.code == "fallback_linked_existing"
    assert second.code == "fallback_already_exists"
    assert claim.fallback_gift_card_id == card.id
    assert session.query(models.GiftCard).count() == 1
    assert session.query(models.EntitlementGrant).filter_by(source="provider_payment").count() == 0


@pytest.mark.parametrize(
    ("card_type", "redeemed_by", "expected_code"),
    (
        ("other_plan", None, "fallback_type_conflict"),
        ("1_month", 777, "fallback_redeemed_conflict"),
    ),
)
def test_legacy_fallback_conflict_is_quarantined(
    tmp_path: Path,
    card_type: str,
    redeemed_by: int | None,
    expected_code: str,
) -> None:
    from payment_entitlement_service import ensure_fallback_gift_card, mark_paid

    _engine, session = _session(tmp_path)
    claim = _pending_claim(session)
    mark_paid(session, provider="lavatop", order_id="order-1", paid_at=NOW)
    session.add(
        models.GiftCard(
            code="POKROV-LEGACY-CONFLICT",
            card_type=card_type,
            created_by=0,
            created_at=NOW,
            redeemed_by=redeemed_by,
            redeemed_at=NOW if redeemed_by is not None else None,
        )
    )
    session.flush()

    result = ensure_fallback_gift_card(
        session,
        provider="lavatop",
        order_id="order-1",
        gift_code="POKROV-LEGACY-CONFLICT",
        now=NOW,
    )

    assert result.code == expected_code
    assert claim.status == "manual_review"
    assert claim.last_error == expected_code
    assert claim.last_error_at == NOW
    assert claim.fallback_gift_card_id is None
    assert session.query(models.GiftCard).count() == 1
    assert session.query(models.EntitlementGrant).filter_by(source="provider_payment").count() == 0


def test_legacy_fallback_linked_to_other_claim_is_quarantined(tmp_path: Path) -> None:
    from payment_entitlement_service import ensure_fallback_gift_card, mark_paid

    _engine, session = _session(tmp_path)
    first_claim = _pending_claim(session, order_id="order-1")
    second_claim = _pending_claim(session, order_id="order-2")
    mark_paid(session, provider="lavatop", order_id="order-1", paid_at=NOW)
    mark_paid(session, provider="lavatop", order_id="order-2", paid_at=NOW)
    card = models.GiftCard(
        code="POKROV-LEGACY-OWNED",
        card_type="1_month",
        created_by=0,
        created_at=NOW,
    )
    session.add(card)
    session.flush()
    first_claim.fallback_gift_card_id = card.id
    session.flush()

    result = ensure_fallback_gift_card(
        session,
        provider="lavatop",
        order_id="order-2",
        gift_code="POKROV-LEGACY-OWNED",
        now=NOW,
    )

    assert result.code == "fallback_ownership_conflict"
    assert second_claim.status == "manual_review"
    assert second_claim.fallback_gift_card_id is None
    assert first_claim.fallback_gift_card_id == card.id
    assert session.query(models.GiftCard).count() == 1


@pytest.mark.parametrize("created_by", [42, 9999])
def test_legacy_fallback_owned_by_user_or_admin_is_not_adopted(tmp_path: Path, created_by: int) -> None:
    from payment_entitlement_service import ensure_fallback_gift_card, mark_paid

    _engine, session = _session(tmp_path)
    claim = _pending_claim(session)
    mark_paid(session, provider="lavatop", order_id="order-1", paid_at=NOW)
    card = models.GiftCard(
        code="POKROV-OWNED-COLLISION",
        card_type="1_month",
        created_by=created_by,
        created_at=NOW,
    )
    session.add(card)
    session.flush()

    result = ensure_fallback_gift_card(
        session,
        provider="lavatop",
        order_id="order-1",
        gift_code=card.code,
        now=NOW,
    )

    assert result.code == "fallback_creator_conflict"
    assert result.claim.status == "manual_review"
    assert result.claim.last_error == "fallback_creator_conflict"
    assert result.claim.fallback_gift_card_id is None
    assert card.redeemed_by is None


def test_reversal_is_idempotent_and_blocks_fallback(tmp_path: Path) -> None:
    from payment_entitlement_service import (
        attach_by_verified_email,
        ensure_fallback_gift_card,
        fulfill_attached_paid_claim,
        mark_paid,
        redeem_payment_fallback,
        reverse_claim,
    )

    _engine, session = _session(tmp_path)
    _account(session, "account-a", "buyer@example.test")
    _pending_claim(session)
    mark_paid(session, provider="lavatop", order_id="order-1", paid_at=NOW)
    fallback = ensure_fallback_gift_card(
        session,
        provider="lavatop",
        order_id="order-1",
        gift_code="POKROV-TEST-CARD",
        now=NOW,
    )
    attach_by_verified_email(
        session,
        provider="lavatop",
        order_id="order-1",
        buyer_email="buyer@example.test",
        account_id="account-a",
        now=NOW,
    )
    fulfill_attached_paid_claim(session, provider="lavatop", order_id="order-1", now=NOW)

    first = reverse_claim(
        session,
        provider="lavatop",
        order_id="order-1",
        reason="chargeback",
        reversed_at=NOW,
    )
    second = reverse_claim(
        session,
        provider="lavatop",
        order_id="order-1",
        reason="chargeback",
        reversed_at=datetime(2026, 7, 13, 11, 0, 0),
    )

    assert first.claim.status == "reversed"
    assert second.code == "already_reversed"
    assert second.claim.reversed_at == NOW
    grant = session.get(models.EntitlementGrant, first.claim.grant_id)
    assert grant.status == "reversed"
    assert grant.reversed_at == NOW
    blocked = redeem_payment_fallback(
        session,
        gift_card_id=fallback.claim.fallback_gift_card_id,
        account_id="account-a",
        legacy_tg_id=None,
        now=NOW,
    )
    assert blocked.code == "claim_reversed"
    assert session.query(models.EntitlementGrant).filter_by(source="provider_payment").count() == 1


def test_dangling_grant_id_keeps_reversal_unreconciled(tmp_path: Path) -> None:
    from payment_entitlement_service import reverse_claim

    _engine, session = _session(tmp_path)
    claim = _pending_claim(session)
    claim.status = "fulfilled"
    claim.paid_at = NOW
    claim.fulfilled_at = NOW
    claim.grant_id = "missing-grant-id"
    session.flush()

    result = reverse_claim(
        session,
        provider="lavatop",
        order_id="order-1",
        reason="refund",
        reversed_at=NOW,
    )

    assert result.code == "grant_not_found"
    assert result.claim.status == "manual_review"
    assert result.claim.last_error == "grant_not_found"
    assert result.claim.last_error_at == NOW
    assert result.claim.reversed_at is None


def test_dangling_fallback_id_keeps_reversal_unreconciled(tmp_path: Path) -> None:
    from payment_entitlement_service import mark_paid, reverse_claim

    _engine, session = _session(tmp_path)
    claim = _pending_claim(session, order_id="dangling-reversal-fallback")
    mark_paid(session, provider="lavatop", order_id=claim.order_id, paid_at=NOW)
    claim.fallback_gift_card_id = 999999
    session.flush()

    result = reverse_claim(
        session,
        provider="lavatop",
        order_id=claim.order_id,
        reason="refunded",
        reversed_at=NOW,
    )

    assert result.code == "fallback_missing"
    assert claim.status == "manual_review"
    assert claim.reversed_at is None
    assert claim.reversal_reason is None
    assert claim.last_error == "fallback_missing"
    assert claim.last_error_at == NOW


def test_attached_paid_fulfillment_locks_account_before_claim(tmp_path: Path, monkeypatch) -> None:
    import payment_entitlement_service as service

    _engine, session = _session(tmp_path)
    _account(session, "account-a", "buyer@example.test")
    claim = _pending_claim(session)
    claim.account_id = "account-a"
    claim.attached_at = NOW
    claim.status = "attached_pending_payment"
    session.flush()

    operations: list[str] = []
    original_accounts = service._lock_canonical_accounts
    original_claim = service._claim

    def _accounts(*args, **kwargs):
        operations.append("account")
        return original_accounts(*args, **kwargs)

    def _claim(*args, **kwargs):
        operations.append("claim")
        return original_claim(*args, **kwargs)

    monkeypatch.setattr(service, "_lock_canonical_accounts", _accounts)
    monkeypatch.setattr(service, "_claim", _claim)

    result = service.mark_paid_and_fulfill_attached_claim(
        session,
        provider="lavatop",
        order_id="order-1",
        buyer_email="buyer@example.test",
        plan_code="1_month",
        duration_days=30,
        paid_at=NOW,
    )

    assert result.code == "fulfilled"
    assert operations[:2] == ["account", "claim"]


def test_fallback_after_auto_claim_is_same_account_idempotent(tmp_path: Path) -> None:
    from payment_entitlement_service import (
        attach_by_verified_email,
        ensure_fallback_gift_card,
        fulfill_attached_paid_claim,
        mark_paid,
        redeem_payment_fallback,
    )

    _engine, session = _session(tmp_path)
    _account(session, "account-a", "buyer@example.test")
    _pending_claim(session)
    mark_paid(session, provider="lavatop", order_id="order-1", paid_at=NOW)
    fallback = ensure_fallback_gift_card(
        session,
        provider="lavatop",
        order_id="order-1",
        gift_code="POKROV-TEST-CARD",
        now=NOW,
    )
    attach_by_verified_email(
        session,
        provider="lavatop",
        order_id="order-1",
        buyer_email="buyer@example.test",
        account_id="account-a",
        now=NOW,
    )
    fulfill_attached_paid_claim(session, provider="lavatop", order_id="order-1", now=NOW)

    result = redeem_payment_fallback(
        session,
        gift_card_id=fallback.claim.fallback_gift_card_id,
        account_id="account-a",
        legacy_tg_id=1001,
        now=NOW,
    )

    assert result.code == "already_fulfilled"
    assert session.query(models.EntitlementGrant).filter_by(source="provider_payment").count() == 1


def test_gift_card_service_redeems_payment_fallback_once(tmp_path: Path, monkeypatch) -> None:
    import control_panel
    import gift_cards_service
    from payment_entitlement_service import ensure_fallback_gift_card, mark_paid

    engine, session = _session(tmp_path)
    _account(session, "account-a", "buyer@example.test")
    user = session.query(models.User).filter_by(account_id="account-a").one()
    _pending_claim(session)
    mark_paid(session, provider="lavatop", order_id="order-1", paid_at=NOW)
    fallback = ensure_fallback_gift_card(
        session,
        provider="lavatop",
        order_id="order-1",
        gift_code="POKROV-TEST-CARD",
        now=NOW,
    )
    session.commit()

    class _Panel:
        async def login(self):
            return None

        async def get_existing_client(self, _tg_id):
            return True

        async def update_client_traffic(self, _tg_id, _traffic):
            return True

        async def close(self):
            return None

    monkeypatch.setattr(gift_cards_service.db, "SessionLocal", sessionmaker(bind=engine))
    monkeypatch.setattr(control_panel, "ControlPanel", _Panel)

    first = asyncio.run(
        gift_cards_service.redeem_gift_card(
            code="POKROV-TEST-CARD",
            recipient_tg_id=int(user.tg_id),
            require_tos=True,
        )
    )
    with sessionmaker(bind=engine)() as check:
        first_expiry = check.query(models.User).filter_by(tg_id=int(user.tg_id)).one().expiry_at
    second = asyncio.run(
        gift_cards_service.redeem_gift_card(
            code="POKROV-TEST-CARD",
            recipient_tg_id=int(user.tg_id),
            require_tos=True,
        )
    )

    assert first["ok"] is True
    assert second["ok"] is True
    assert first["plan_code"] == "1_month"
    assert first["days"] == 30
    assert first["card_type"] == "1_month"
    with sessionmaker(bind=engine)() as check:
        claim = check.get(models.PaymentEntitlementClaim, fallback.claim.id)
        assert claim.status == "fulfilled"
        assert check.query(models.EntitlementGrant).filter_by(source="provider_payment").count() == 1
        assert check.query(models.User).filter_by(tg_id=int(user.tg_id)).one().expiry_at == first_expiry


def test_payment_fallback_redemption_uses_saved_claim_after_plan_removal(tmp_path: Path, monkeypatch) -> None:
    import control_panel
    import gift_cards_service
    from payment_entitlement_service import ensure_fallback_gift_card, mark_paid

    engine, session = _session(tmp_path)
    _account(session, "account-a", "buyer@example.test")
    user = session.query(models.User).filter_by(account_id="account-a").one()
    _pending_claim(session)
    mark_paid(session, provider="lavatop", order_id="order-1", paid_at=NOW)
    fallback = ensure_fallback_gift_card(
        session,
        provider="lavatop",
        order_id="order-1",
        gift_code="POKROV-REMOVED-PLAN",
        now=NOW,
    )
    session.commit()

    class _Panel:
        async def login(self):
            return None

        async def get_existing_client(self, _tg_id):
            return True

        async def update_client_traffic(self, _tg_id, _traffic):
            return True

        async def close(self):
            return None

    monkeypatch.setattr(gift_cards_service.db, "SessionLocal", sessionmaker(bind=engine))
    monkeypatch.setattr(gift_cards_service, "_card_type_info", lambda _card_type: None)
    monkeypatch.setattr(control_panel, "ControlPanel", _Panel)

    first = asyncio.run(
        gift_cards_service.redeem_gift_card(
            code="POKROV-REMOVED-PLAN",
            recipient_tg_id=int(user.tg_id),
            require_tos=True,
        )
    )
    second = asyncio.run(
        gift_cards_service.redeem_gift_card(
            code="POKROV-REMOVED-PLAN",
            recipient_tg_id=int(user.tg_id),
            require_tos=True,
        )
    )

    assert first["ok"] is True
    assert second["ok"] is True
    with sessionmaker(bind=engine)() as check:
        claim = check.get(models.PaymentEntitlementClaim, fallback.claim.id)
        grant = check.query(models.EntitlementGrant).filter_by(source="provider_payment").one()
        assert claim.status == "fulfilled"
        assert grant.plan_code == "1_month"
        assert grant.duration_days == 30
        assert check.query(models.EntitlementGrant).filter_by(source="provider_payment").count() == 1


def test_wrong_fallback_redeemer_does_not_poison_rightful_owner(tmp_path: Path) -> None:
    from payment_entitlement_service import (
        attach_by_verified_email,
        ensure_fallback_gift_card,
        mark_paid,
        redeem_payment_fallback,
    )

    _engine, session = _session(tmp_path)
    _account(session, "account-a", "buyer@example.test")
    _account(session, "account-b", "other@example.test")
    _pending_claim(session)
    mark_paid(session, provider="lavatop", order_id="order-1", paid_at=NOW)
    fallback = ensure_fallback_gift_card(
        session,
        provider="lavatop",
        order_id="order-1",
        gift_code="POKROV-OWNER-SAFE",
        now=NOW,
    )
    attach_by_verified_email(
        session,
        provider="lavatop",
        order_id="order-1",
        buyer_email="buyer@example.test",
        account_id="account-a",
        now=NOW,
    )

    wrong = redeem_payment_fallback(
        session,
        gift_card_id=int(fallback.claim.fallback_gift_card_id),
        account_id="account-b",
        legacy_tg_id=2002,
        now=NOW,
    )
    assert wrong.code == "account_conflict"
    assert wrong.changed is False
    assert wrong.claim.status == "paid_attached"
    assert wrong.claim.last_error is None

    rightful = redeem_payment_fallback(
        session,
        gift_card_id=int(fallback.claim.fallback_gift_card_id),
        account_id="account-a",
        legacy_tg_id=2001,
        now=NOW,
    )
    assert rightful.code == "fulfilled"
    assert rightful.claim.status == "fulfilled"
    assert session.query(models.EntitlementGrant).filter_by(source="provider_payment").count() == 1


def test_fallback_redemption_canonicalizes_merged_owner(tmp_path: Path) -> None:
    from payment_entitlement_service import ensure_fallback_gift_card, mark_paid, redeem_payment_fallback

    _engine, session = _session(tmp_path)
    source = _account(session, "source", "buyer@example.test")
    _account(session, "target", "target@example.test")
    source.status = "merged"
    source.merged_into_account_id = "target"
    claim = _pending_claim(session)
    mark_paid(session, provider="lavatop", order_id="order-1", paid_at=NOW)
    fallback = ensure_fallback_gift_card(
        session,
        provider="lavatop",
        order_id="order-1",
        gift_code="POKROV-MERGED-OWNER",
        now=NOW,
    )
    claim.account_id = "source"
    claim.status = "paid_attached"
    session.flush()

    result = redeem_payment_fallback(
        session,
        gift_card_id=int(fallback.claim.fallback_gift_card_id),
        account_id="source",
        legacy_tg_id=2001,
        now=NOW,
    )

    assert result.code == "fulfilled"
    assert result.claim.account_id == "target"
    assert session.query(models.EntitlementGrant).filter_by(account_id="target").count() == 1


def test_attach_locks_account_before_claim(monkeypatch, tmp_path: Path) -> None:
    import payment_entitlement_service as service

    _engine, session = _session(tmp_path)
    _account(session, "account-a", "buyer@example.test")
    _pending_claim(session)
    calls: list[str] = []
    original_canonical = service.canonical_account_id
    original_claim = service._claim

    def _canonical(*args, **kwargs):
        calls.append("account")
        return original_canonical(*args, **kwargs)

    def _claim(*args, **kwargs):
        calls.append("claim")
        return original_claim(*args, **kwargs)

    monkeypatch.setattr(service, "canonical_account_id", _canonical)
    monkeypatch.setattr(service, "_claim", _claim)
    service.attach_by_verified_email(
        session,
        provider="lavatop",
        order_id="order-1",
        buyer_email="buyer@example.test",
        account_id="account-a",
        now=NOW,
    )

    assert calls.index("account") < calls.index("claim")


def test_account_merge_moves_claim_to_canonical_account(tmp_path: Path) -> None:
    _engine, session = _session(tmp_path)
    _account(session, "target", "target@example.test")
    _account(session, "source", "buyer@example.test")
    claim = _pending_claim(session)
    claim.account_id = "source"
    claim.status = "attached_pending_payment"
    claim.attached_at = NOW
    session.flush()

    _move_account_owned_rows(
        session,
        source_account_id="source",
        target_account_id="target",
        now=NOW,
    )

    session.expire(claim)
    assert claim.account_id == "target"


def test_sqlite_migration_is_repeatable_and_retains_existing_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "migration.db"
    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    models.Base.metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE payment_entitlement_claims"))
        conn.execute(
            text(
                "CREATE TABLE payment_entitlement_claims ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, provider VARCHAR(32) NOT NULL, "
                "order_id VARCHAR(128) NOT NULL, buyer_email_norm VARCHAR(255) NOT NULL)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO payment_entitlement_claims (provider, order_id, buyer_email_norm) "
                "VALUES ('legacy', 'legacy-claim', 'legacy@example.test')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO external_orders "
                "(order_id, provider, amount, currency, status, created_at) "
                "VALUES ('legacy-order', 'legacy', 1, 'RUB', 'paid', :now)"
            ),
            {"now": NOW},
        )

    migrations.run_migrations(engine)
    migrations.run_migrations(engine)

    with engine.begin() as conn:
        assert conn.execute(text("SELECT count(*) FROM external_orders WHERE order_id='legacy-order'")) .scalar() == 1
        assert conn.execute(
            text("SELECT count(*) FROM payment_entitlement_claims WHERE order_id='legacy-claim'")
        ).scalar() == 1
        table_info = {
            row[1]: row for row in conn.execute(text("PRAGMA table_info(payment_entitlement_claims)"))
        }
        columns = set(table_info)
        assert {"provider", "order_id", "buyer_email_norm", "fallback_gift_card_id", "last_error_at"} <= columns
        assert all(
            table_info[column][3] == 1
            for column in ("status", "plan_code", "duration_days", "created_at", "updated_at")
        )

    with sessionmaker(bind=engine)() as session:
        quarantined = session.query(models.PaymentEntitlementClaim).filter_by(order_id="legacy-claim").one()
        assert quarantined.status == "manual_review"
        assert quarantined.buyer_email_norm == "legacy@example.test"
        assert quarantined.plan_code == "unknown"
        assert quarantined.duration_days == 0
        assert quarantined.last_error == "migration_incomplete_claim"
        assert quarantined.last_error_at is not None
        assert quarantined.created_at is not None
        assert quarantined.updated_at is not None


def test_sqlite_preexisting_nullable_claim_is_quarantined_not_claimable(tmp_path: Path) -> None:
    from payment_entitlement_service import ensure_fallback_gift_card, mark_paid

    db_path = tmp_path / "nullable-claim.db"
    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    models.Base.metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE payment_entitlement_claims"))
        conn.execute(
            text(
                "CREATE TABLE payment_entitlement_claims ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, provider VARCHAR(32) NOT NULL, "
                "order_id VARCHAR(128) NOT NULL, buyer_email_norm VARCHAR(255), "
                "status VARCHAR(32), plan_code VARCHAR(32), duration_days INTEGER, "
                "created_at DATETIME, updated_at DATETIME)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO payment_entitlement_claims "
                "(provider, order_id, buyer_email_norm, status, plan_code, duration_days) "
                "VALUES ('legacy', 'nullable-claim', NULL, NULL, NULL, NULL)"
            )
        )

    migrations.run_migrations(engine)

    with sessionmaker(bind=engine)() as session:
        claim = session.query(models.PaymentEntitlementClaim).filter_by(order_id="nullable-claim").one()
        assert claim.status == "manual_review"
        assert claim.last_error == "migration_incomplete_claim"
        assert claim.last_error_at is not None
        assert mark_paid(
            session,
            provider="legacy",
            order_id="nullable-claim",
            paid_at=NOW,
        ).code == "manual_review"
        assert ensure_fallback_gift_card(
            session,
            provider="legacy",
            order_id="nullable-claim",
            gift_code="POKROV-QUARANTINED",
            now=NOW,
        ).code == "manual_review"
        assert session.query(models.GiftCard).count() == 0
        assert session.query(models.EntitlementGrant).count() == 0

    with engine.begin() as conn:
        info = {row[1]: row for row in conn.execute(text("PRAGMA table_info(payment_entitlement_claims)"))}
        assert info["status"][3] == 0


def test_postgres_claim_ddl_is_additive_and_compatible() -> None:
    class _Result:
        def scalar(self):
            return False

    class _Conn:
        def __init__(self):
            self.sql: list[str] = []

        def execute(self, statement, params=None):
            self.sql.append(str(statement))
            return _Result()

    conn = _Conn()
    migrations._ensure_payment_entitlement_claims_postgres(conn)
    ddl = "\n".join(conn.sql)

    assert "CREATE TABLE IF NOT EXISTS payment_entitlement_claims" in ddl
    assert "UNIQUE(provider, order_id)" in ddl
    assert "fallback_gift_card_id INTEGER" in ddl
    assert "last_error_at TIMESTAMP" in ddl
    assert "UPDATE payment_entitlement_claims" in ddl
    assert "migration_incomplete_claim" in ddl
    assert "ALTER COLUMN buyer_email_norm SET NOT NULL" in ddl
    assert "ALTER COLUMN status SET NOT NULL" in ddl
    assert "ALTER COLUMN plan_code SET NOT NULL" in ddl
    assert "ALTER COLUMN duration_days SET NOT NULL" in ddl
    assert "ALTER COLUMN created_at SET NOT NULL" in ddl
    assert "ALTER COLUMN updated_at SET NOT NULL" in ddl
    assert "DROP TABLE" not in ddl.upper()
    assert "DROP COLUMN" not in ddl.upper()


def test_postgres_claim_not_null_alters_are_metadata_guarded() -> None:
    class _Result:
        def __init__(self, value=False):
            self.value = value

        def scalar(self):
            return self.value

    class _Conn:
        def __init__(self):
            self.sql: list[str] = []
            self.columns = {
                "buyer_email_norm",
                "account_id",
                "status",
                "plan_code",
                "duration_days",
                "grant_id",
                "fallback_gift_card_id",
                "paid_at",
                "attached_at",
                "fulfilled_at",
                "reversed_at",
                "reversal_reason",
                "last_error",
                "last_error_at",
                "created_at",
                "updated_at",
            }
            self.not_null: set[str] = set()

        def execute(self, statement, params=None):
            sql = str(statement)
            self.sql.append(sql)
            if "information_schema.columns" in sql and "is_nullable" in sql:
                return _Result(str((params or {}).get("column_name")) in self.not_null)
            if "information_schema.columns" in sql:
                return _Result(str((params or {}).get("column_name")) in self.columns)
            if " SET NOT NULL" in sql:
                column = sql.split("ALTER COLUMN ", 1)[1].split(" SET NOT NULL", 1)[0].strip()
                self.not_null.add(column)
            return _Result(False)

    conn = _Conn()
    migrations._ensure_payment_entitlement_claims_postgres(conn)
    first_alters = sum(" SET NOT NULL" in sql for sql in conn.sql)
    migrations._ensure_payment_entitlement_claims_postgres(conn)
    second_alters = sum(" SET NOT NULL" in sql for sql in conn.sql)

    assert first_alters == 6
    assert second_alters == first_alters
