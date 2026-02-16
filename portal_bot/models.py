from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    tg_id = Column(BigInteger, primary_key=True)
    username = Column(String(100), nullable=True)
    uuid = Column(String(36), unique=True)
    email = Column(String(100))
    sub_type = Column(String(50))
    current_plan_code = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expiry_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    stars_paid = Column(Integer, default=0)
    total_gb = Column(Integer, default=0)
    trial_used = Column(Boolean, default=False)

    # Referral system
    referrer_id = Column(BigInteger, nullable=True)
    referral_count = Column(Integer, default=0)
    referral_code = Column(String(10), unique=True, nullable=True)
    first_purchase_done = Column(Boolean, default=False)

    # Terms
    tos_accepted = Column(Boolean, default=False)

    # Secure subscription token (replaces tg_id in subscription URL)
    sub_token = Column(String(64), unique=True, nullable=True)

    # Wheel / streak
    last_wheel_spin = Column(DateTime, nullable=True)
    streak_months = Column(Integer, default=0)
    streak_last_check = Column(DateTime, nullable=True)
    channel_bonus_claimed_at = Column(DateTime, nullable=True)
    channel_bonus_active = Column(Boolean, default=False)
    channel_bonus_expires_at = Column(DateTime, nullable=True)
    channel_bonus_revoked_at = Column(DateTime, nullable=True)
    pending_discount_pct = Column(Integer, nullable=True)
    pending_discount_code = Column(String(20), nullable=True)
    pending_discount_set_at = Column(DateTime, nullable=True)
    is_manual = Column(Boolean, default=False)
    created_by_admin = Column(BigInteger, nullable=True)
    display_name = Column(String(100), nullable=True)
    device_reset_last_at = Column(DateTime, nullable=True)
    free_cycle_anchor_at = Column(DateTime, nullable=True)
    free_cycle_last_reset_at = Column(DateTime, nullable=True)
    free_cycle_next_reset_at = Column(DateTime, nullable=True)


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, index=True)
    achievement_id = Column(String(50))
    unlocked_at = Column(DateTime, default=datetime.utcnow)


class GiftCard(Base):
    __tablename__ = "gift_cards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, index=True)
    card_type = Column(String(20))
    created_by = Column(BigInteger)
    created_at = Column(DateTime, default=datetime.utcnow)
    redeemed_by = Column(BigInteger, nullable=True)
    redeemed_at = Column(DateTime, nullable=True)


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, index=True)
    username = Column(String(100), nullable=True)
    rating = Column(Integer)
    text = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_featured = Column(Boolean, default=False)


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, index=True)
    promo_type = Column(String(10))
    value = Column(Integer)
    uses_left = Column(Integer)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PromoUsage(Base):
    __tablename__ = "promo_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, index=True)
    promo_code = Column(String(20))
    used_at = Column(DateTime, default=datetime.utcnow)


class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(50), unique=True, index=True)
    text = Column(String(2000))
    created_at = Column(DateTime, default=datetime.utcnow)


class Node(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, index=True)  # us/de/nl/...
    name = Column(String(100))
    host = Column(String(255))  # e.g. us.<your-domain>
    vless_port = Column(Integer, default=443)
    reality_sni = Column(String(255))
    reality_pbk = Column(String(255))
    reality_sid = Column(String(64))
    fingerprint = Column(String(64), default="firefox")
    flow = Column(String(64), default="xtls-rprx-vision")

    # Panel access from control-plane
    panel_base_url = Column(String(255))  # e.g. https://us.<your-domain>:8444
    panel_path = Column(String(255))      # 3x-ui random path prefix
    panel_user = Column(String(128))
    panel_pass = Column(String(255))
    inbound_id = Column(Integer)

    enabled = Column(Boolean, default=True)
    weight = Column(Integer, default=100)
    health_score = Column(Float, default=0.0)
    last_health_at = Column(DateTime, nullable=True)
    is_healthy = Column(Boolean, default=True)
    panel_latency_ms = Column(Integer, nullable=True)
    panel_error_rate = Column(Float, default=0.0)
    active_clients = Column(Integer, default=0)
    last_ok_at = Column(DateTime, nullable=True)


class UserNode(Base):
    __tablename__ = "user_nodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, index=True, nullable=False)
    node_id = Column(Integer, index=True, nullable=False)
    client_uuid = Column(String(36), nullable=False)
    panel_email = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("tg_id", "node_id", name="uq_user_nodes_tg_node"),)


class AdminAudit(Base):
    __tablename__ = "admin_audit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    actor_tg_id = Column(BigInteger, index=True, nullable=False)
    action = Column(String(64), nullable=False)
    target_tg_id = Column(BigInteger, index=True, nullable=True)
    meta = Column(String(2000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_tg_id = Column(BigInteger, index=True, nullable=False)
    status = Column(String(20), default="open", nullable=False)  # open / in_progress / closed
    subject = Column(String(200), nullable=True)
    assigned_admin_tg_id = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    closed_at = Column(DateTime, nullable=True)


class SupportTicketMessage(Base):
    __tablename__ = "support_ticket_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, index=True, nullable=False)
    sender_tg_id = Column(BigInteger, index=True, nullable=False)
    sender_role = Column(String(20), nullable=False)  # user / admin
    body = Column(String(2000), nullable=False)
    media_type = Column(String(32), nullable=True)
    media_file_id = Column(String(256), nullable=True)
    media_payload = Column(String(2000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class NodeHealthSample(Base):
    __tablename__ = "node_health_samples"

    id = Column(Integer, primary_key=True, autoincrement=True)
    node_code = Column(String(20), index=True, nullable=False)
    sampled_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    panel_latency_ms = Column(Integer, nullable=True)
    panel_error_rate = Column(Float, default=0.0)
    active_clients = Column(Integer, default=0)
    is_healthy = Column(Boolean, default=True)
    score = Column(Float, default=0.0)
    source = Column(String(64), default="collector")


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, index=True, nullable=False)
    event_name = Column(String(64), index=True, nullable=False)
    source = Column(String(32), default="unknown", nullable=False)
    session_id = Column(String(64), nullable=True)
    meta_json = Column(String(4000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Offer(Base):
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, index=True, nullable=False)
    offer_type = Column(String(32), nullable=False)
    plan_code = Column(String(32), nullable=False)
    price_stars = Column(Integer, default=0, nullable=False)
    status = Column(String(20), default="active", nullable=False)
    trigger_reason = Column(String(64), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PayAttempt(Base):
    __tablename__ = "pay_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, index=True, nullable=False)
    source = Column(String(32), default="bot", nullable=False)
    plan_code = Column(String(32), nullable=False)
    amount_stars = Column(Integer, default=0, nullable=False)
    currency = Column(String(12), default="XTR", nullable=False)
    status = Column(String(20), default="started", nullable=False)
    invoice_payload = Column(String(255), unique=True, nullable=True)
    offer_id = Column(Integer, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    paid_at = Column(DateTime, nullable=True)
    abandoned_notified_at = Column(DateTime, nullable=True)


class ExternalOrder(Base):
    __tablename__ = "external_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(128), nullable=False, index=True)
    tg_id = Column(BigInteger, nullable=True, index=True)
    provider = Column(String(32), nullable=False, index=True)
    plan_code = Column(String(32), nullable=True)
    source = Column(String(32), nullable=True)
    campaign = Column(String(64), nullable=True)
    promo_code = Column(String(32), nullable=True)
    meta_json = Column(Text, nullable=True)
    amount = Column(Float, default=0.0, nullable=False)
    currency = Column(String(16), default="RUB", nullable=False)
    status = Column(String(24), default="created", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    paid_at = Column(DateTime, nullable=True)

    __table_args__ = (UniqueConstraint("provider", "order_id", name="uq_external_orders_provider_order"),)


class ExternalPaymentEvent(Base):
    __tablename__ = "external_payment_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(32), nullable=False, index=True)
    event_type = Column(String(24), nullable=False, index=True)
    external_id = Column(String(128), nullable=False, index=True)
    order_id = Column(String(128), nullable=True, index=True)
    payload_json = Column(Text, nullable=False)
    signature_ok = Column(Boolean, default=False, nullable=False)
    processed_ok = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "provider",
            "event_type",
            "external_id",
            name="uq_external_payment_events_provider_type_extid",
        ),
    )


class PointsLedger(Base):
    __tablename__ = "points_ledger"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, index=True, nullable=False)
    delta_points = Column(Integer, default=0, nullable=False)
    reason = Column(String(64), nullable=False)
    ref_tg_id = Column(BigInteger, nullable=True)
    pay_attempt_id = Column(Integer, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class CampaignSend(Base):
    __tablename__ = "campaign_sends"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, index=True, nullable=False)
    campaign_key = Column(String(64), nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class FamilySlot(Base):
    __tablename__ = "family_slots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, index=True, nullable=False)
    slots = Column(Integer, default=1, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PlanCatalog(Base):
    __tablename__ = "plan_catalog"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, index=True, nullable=False)
    label = Column(String(120), nullable=False)
    amount_rub = Column(Integer, default=0, nullable=False)
    amount_stars = Column(Integer, default=0, nullable=False)
    days = Column(Integer, default=30, nullable=False)
    device_limit = Column(Integer, default=1, nullable=False)
    node_policy = Column(String(32), nullable=True)
    badge = Column(String(32), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=100, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class LiveUpdate(Base):
    __tablename__ = "live_updates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(160), nullable=False)
    summary = Column(String(600), nullable=False)
    link = Column(String(600), nullable=False)
    channel_username = Column(String(64), nullable=True)
    post_id = Column(Integer, nullable=True)
    published_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=100, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class StartLink(Base):
    __tablename__ = "start_links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(64), unique=True, index=True, nullable=False)
    description = Column(String(240), nullable=True)
    target_action = Column(String(64), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AppSetting(Base):
    __tablename__ = "app_settings"

    key = Column(String(64), primary_key=True)
    value_json = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
