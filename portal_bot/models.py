from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base


Base = declarative_base()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _default_node_access_role(context) -> str:
    params = context.get_current_parameters() if context is not None else {}
    code = str((params or {}).get("code") or "").strip().lower()
    if "operator" in code or code.endswith("_lab") or code.endswith("-lab"):
        return "operator_lab"
    if "free" in code and "soft" in code:
        return "free_soft"
    if "free" in code:
        return "free_standard"
    return "paid"


class User(Base):
    __tablename__ = "users"

    tg_id = Column(BigInteger, primary_key=True)
    account_id = Column(String(36), index=True, nullable=True)
    username = Column(String(100), nullable=True)
    uuid = Column(String(36), unique=True)
    email = Column(String(100))
    sub_type = Column(String(50))
    current_plan_code = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
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
    is_app_user = Column(Boolean, default=False)
    created_by_admin = Column(BigInteger, nullable=True)
    display_name = Column(String(100), nullable=True)
    device_reset_last_at = Column(DateTime, nullable=True)
    free_cycle_anchor_at = Column(DateTime, nullable=True)
    free_cycle_last_reset_at = Column(DateTime, nullable=True)
    free_cycle_next_reset_at = Column(DateTime, nullable=True)
    free_profile_state = Column(String(32), default="standard", nullable=False)
    free_profile_active_role = Column(String(32), default="free_standard", nullable=False)
    free_profile_source = Column(String(64), default="legacy_backfill", nullable=False)
    free_profile_state_changed_at = Column(DateTime, nullable=True)
    free_profile_job_id = Column(Integer, index=True, nullable=True)
    free_profile_error_code = Column(String(64), nullable=True)
    free_profile_standard_node_code = Column(String(32), nullable=True)
    free_profile_soft_node_code = Column(String(32), nullable=True)
    free_profile_observed_bytes = Column(BigInteger, default=0, nullable=False)
    free_profile_observed_at = Column(DateTime, nullable=True)
    free_profile_observation_source = Column(String(64), nullable=True)
    app_install_id = Column(String(128), index=True, nullable=True)
    app_device_name = Column(String(120), nullable=True)
    app_platform = Column(String(32), nullable=True)
    app_os_version = Column(String(64), nullable=True)
    app_version = Column(String(32), nullable=True)
    app_locale = Column(String(32), nullable=True)
    app_timezone = Column(String(64), nullable=True)
    app_last_seen_at = Column(DateTime, nullable=True)
    app_last_ip = Column(String(64), nullable=True)
    route_mode = Column(String(32), nullable=True)
    route_selected_apps_json = Column(Text, nullable=True)
    route_requires_elevated_privileges = Column(Boolean, nullable=True)
    linked_telegram_id = Column(BigInteger, index=True, nullable=True)
    linked_telegram_username = Column(String(100), nullable=True)
    linked_telegram_linked_at = Column(DateTime, nullable=True)


class Account(Base):
    __tablename__ = "accounts"

    id = Column(String(36), primary_key=True)
    status = Column(String(24), default="active", index=True, nullable=False)
    created_source = Column(String(32), default="legacy_backfill", nullable=False)
    merged_into_account_id = Column(String(36), index=True, nullable=True)
    auth_epoch = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, nullable=False)


class AccountIdentity(Base):
    __tablename__ = "account_identities"
    __table_args__ = (
        UniqueConstraint(
            "kind",
            "provider",
            "subject_norm",
            name="uq_account_identity_subject",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String(36), index=True, nullable=False)
    kind = Column(String(32), index=True, nullable=False)
    provider = Column(String(32), nullable=False)
    subject_norm = Column(String(255), nullable=False)
    verified_at = Column(DateTime, nullable=True)
    disabled_at = Column(DateTime, nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, nullable=False)


class AccountDevice(Base):
    __tablename__ = "account_devices"

    id = Column(String(36), primary_key=True)
    account_id = Column(String(36), index=True, nullable=False)
    install_id = Column(String(128), unique=True, index=True, nullable=False)
    label = Column(String(120), nullable=True)
    platform = Column(String(32), nullable=True)
    os_version = Column(String(64), nullable=True)
    app_version = Column(String(32), nullable=True)
    locale = Column(String(32), nullable=True)
    time_zone = Column(String(64), nullable=True)
    route_mode = Column(String(32), nullable=True)
    selected_apps_json = Column(Text, nullable=True)
    requires_elevated_privileges = Column(Boolean, nullable=True)
    state = Column(String(24), default="active", index=True, nullable=False)
    credential_version = Column(Integer, default=1, nullable=False)
    first_seen_at = Column(DateTime, default=_utcnow, nullable=False)
    last_seen_at = Column(DateTime, default=_utcnow, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    revoke_reason = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, nullable=False)


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id = Column(String(36), primary_key=True)
    account_id = Column(String(36), index=True, nullable=False)
    device_id = Column(String(36), index=True, nullable=True)
    refresh_family_id = Column(String(36), index=True, nullable=False)
    refresh_token_hash = Column(String(64), unique=True, index=True, nullable=False)
    scope = Column(String(64), nullable=False)
    auth_origin = Column(String(32), index=True, nullable=False)
    access_expires_at = Column(DateTime, nullable=False)
    refresh_expires_at = Column(DateTime, nullable=False)
    fresh_auth_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    replaced_by_session_id = Column(String(36), index=True, nullable=True)
    reuse_detected_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    revoke_reason = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)


class RecoveryCode(Base):
    __tablename__ = "recovery_codes"

    id = Column(String(36), primary_key=True)
    account_id = Column(String(36), index=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    code_hmac = Column(String(64), unique=True, index=True, nullable=False)
    code_hint = Column(String(24), nullable=False)
    status = Column(String(24), default="active", index=True, nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    used_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    replaced_by_code_id = Column(String(36), nullable=True)


class EntitlementGrant(Base):
    __tablename__ = "entitlement_grants"

    id = Column(String(36), primary_key=True)
    account_id = Column(String(36), index=True, nullable=False)
    legacy_tg_id = Column(BigInteger, index=True, nullable=True)
    idempotency_key = Column(String(160), unique=True, index=True, nullable=False)
    source = Column(String(40), index=True, nullable=False)
    status = Column(String(24), index=True, nullable=False)
    grant_kind = Column(String(32), nullable=False)
    plan_code = Column(String(32), nullable=True)
    starts_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, index=True, nullable=True)
    reserved_at = Column(DateTime, nullable=True)
    reservation_expires_at = Column(DateTime, index=True, nullable=True)
    activated_at = Column(DateTime, nullable=True)
    duration_days = Column(Integer, nullable=True)
    activation_evidence_id = Column(String(36), index=True, nullable=True)
    provider = Column(String(32), nullable=True)
    external_order_id = Column(String(160), nullable=True)
    metadata_json = Column(Text, nullable=True)
    reversed_at = Column(DateTime, nullable=True)
    reversal_reason = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, nullable=False)


class PaymentEntitlementClaim(Base):
    __tablename__ = "payment_entitlement_claims"
    __table_args__ = (
        UniqueConstraint("provider", "order_id", name="uq_payment_entitlement_claim_provider_order"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(32), nullable=False, index=True)
    order_id = Column(String(128), nullable=False, index=True)
    buyer_email_norm = Column(String(255), nullable=False, index=True)
    account_id = Column(String(36), nullable=True, index=True)
    status = Column(String(32), default="pending_payment", nullable=False, index=True)
    plan_code = Column(String(32), nullable=False)
    duration_days = Column(Integer, nullable=False)
    grant_id = Column(String(36), nullable=True, index=True)
    fallback_gift_card_id = Column(Integer, unique=True, nullable=True, index=True)
    paid_at = Column(DateTime, nullable=True)
    attached_at = Column(DateTime, nullable=True)
    fulfilled_at = Column(DateTime, nullable=True)
    reversed_at = Column(DateTime, nullable=True)
    reversal_reason = Column(String(64), nullable=True)
    last_error = Column(String(120), nullable=True)
    last_error_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, nullable=False)


class ConnectionEvidence(Base):
    __tablename__ = "connection_evidence"

    id = Column(String(36), primary_key=True)
    account_id = Column(String(36), index=True, nullable=False)
    device_id = Column(String(36), index=True, nullable=True)
    node_id = Column(Integer, index=True, nullable=False)
    evidence_kind = Column(String(40), index=True, nullable=False)
    observed_at = Column(DateTime, index=True, nullable=False)
    evidence_key = Column(String(160), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)


class ReferralRelationship(Base):
    __tablename__ = "referral_relationships"

    id = Column(String(36), primary_key=True)
    referred_account_id = Column(String(36), unique=True, index=True, nullable=False)
    referrer_account_id = Column(String(36), index=True, nullable=False)
    source = Column(String(32), nullable=False)
    status = Column(String(24), default="linked", index=True, nullable=False)
    review_status = Column(String(24), default="clear", index=True, nullable=False)
    friend_evidence_id = Column(String(36), index=True, nullable=True)
    friend_grant_id = Column(String(36), nullable=True)
    friend_granted_at = Column(DateTime, nullable=True)
    first_payment_key = Column(String(160), unique=True, index=True, nullable=True)
    first_payment_at = Column(DateTime, nullable=True)
    hold_until = Column(DateTime, index=True, nullable=True)
    referrer_grant_id = Column(String(36), nullable=True)
    referrer_granted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, nullable=False)


class ReferralTransition(Base):
    __tablename__ = "referral_transitions"

    id = Column(String(36), primary_key=True)
    relationship_id = Column(String(36), index=True, nullable=False)
    referred_account_id = Column(String(36), index=True, nullable=False)
    referrer_account_id = Column(String(36), index=True, nullable=False)
    transition_key = Column(String(160), unique=True, index=True, nullable=False)
    transition_kind = Column(String(40), index=True, nullable=False)
    status = Column(String(24), nullable=False)
    occurred_at = Column(DateTime, index=True, nullable=False)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)


class AntiAbuseEvent(Base):
    __tablename__ = "antiabuse_events"

    id = Column(String(36), primary_key=True)
    account_id = Column(String(36), index=True, nullable=True)
    device_id = Column(String(36), index=True, nullable=True)
    session_id = Column(String(36), index=True, nullable=True)
    event_kind = Column(String(40), index=True, nullable=False)
    source = Column(String(32), index=True, nullable=False)
    occurred_at = Column(DateTime, default=_utcnow, index=True, nullable=False)
    install_hmac = Column(String(64), nullable=True)
    raw_ip = Column(String(64), nullable=True)
    raw_ip_expires_at = Column(DateTime, index=True, nullable=True)
    ip_full_hmac = Column(String(64), index=True, nullable=True)
    ip_prefix_hmac = Column(String(64), index=True, nullable=True)
    hmac_version = Column(Integer, nullable=True)
    risk_score = Column(Float, default=0.0, nullable=False)
    reasons_json = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)


class AntiAbuseCase(Base):
    __tablename__ = "antiabuse_cases"

    id = Column(String(36), primary_key=True)
    account_id = Column(String(36), index=True, nullable=True)
    status = Column(String(24), default="open", index=True, nullable=False)
    severity = Column(String(16), default="watch", index=True, nullable=False)
    reason_code = Column(String(64), index=True, nullable=False)
    risk_score = Column(Float, default=0.0, nullable=False)
    hard_lock = Column(Boolean, default=False, nullable=False)
    opened_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    assigned_operator_tg_id = Column(BigInteger, nullable=True)
    details_json = Column(Text, nullable=True)


class AntiAbuseAction(Base):
    __tablename__ = "antiabuse_actions"

    id = Column(String(36), primary_key=True)
    case_id = Column(String(36), index=True, nullable=False)
    account_id = Column(String(36), index=True, nullable=True)
    action_kind = Column(String(40), index=True, nullable=False)
    actor_kind = Column(String(24), nullable=False)
    actor_tg_id = Column(BigInteger, nullable=True)
    reason = Column(String(255), nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)


class AccountMergeReview(Base):
    __tablename__ = "account_merge_reviews"

    id = Column(String(36), primary_key=True)
    fingerprint = Column(String(64), unique=True, index=True, nullable=False)
    account_id = Column(String(36), index=True, nullable=True)
    conflicting_account_id = Column(String(36), index=True, nullable=True)
    reason_code = Column(String(64), index=True, nullable=False)
    status = Column(String(24), default="open", index=True, nullable=False)
    subject_hint = Column(String(255), nullable=True)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)


class WebEmailIdentity(Base):
    __tablename__ = "web_email_identities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(200), nullable=False)
    email_norm = Column(String(200), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    linked_tg_id = Column(BigInteger, index=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, nullable=False)


class WebEmailToken(Base):
    __tablename__ = "web_email_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    identity_id = Column(Integer, index=True, nullable=False)
    token_kind = Column(String(32), index=True, nullable=False)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)


class WebCabinetHandoffToken(Base):
    __tablename__ = "web_cabinet_handoff_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, index=True, nullable=False)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    target_path = Column(String(512), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, index=True)
    achievement_id = Column(String(50))
    unlocked_at = Column(DateTime, default=_utcnow)


class GiftCard(Base):
    __tablename__ = "gift_cards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, index=True)
    card_type = Column(String(20))
    created_by = Column(BigInteger)
    created_at = Column(DateTime, default=_utcnow)
    redeemed_by = Column(BigInteger, nullable=True)
    redeemed_at = Column(DateTime, nullable=True)


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, index=True)
    username = Column(String(100), nullable=True)
    rating = Column(Integer)
    text = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    is_featured = Column(Boolean, default=False)


class FeedbackEntry(Base):
    __tablename__ = "feedback_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, index=True, nullable=False)
    username = Column(String(100), nullable=True)
    category = Column(String(32), default="general", nullable=False)
    text = Column(String(1000), nullable=False)
    status = Column(String(20), default="new", nullable=False)
    source = Column(String(32), default="webapp", nullable=False)
    review_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    reviewed_at = Column(DateTime, nullable=True)


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, index=True)
    promo_type = Column(String(10))
    value = Column(Integer)
    uses_left = Column(Integer)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class PromoUsage(Base):
    __tablename__ = "promo_usage"
    __table_args__ = (UniqueConstraint("tg_id", "promo_code", name="uq_promo_usage_tg_code"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, index=True)
    promo_code = Column(String(20))
    used_at = Column(DateTime, default=_utcnow)


class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(50), unique=True, index=True)
    text = Column(String(2000))
    created_at = Column(DateTime, default=_utcnow)


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
    access_role = Column(String(32), default=_default_node_access_role, nullable=False, index=True)
    access_role_legacy = Column(String(32), nullable=True)

    enabled = Column(Boolean, default=True)
    accepting_new_clients = Column(Boolean, default=True)
    is_draining = Column(Boolean, default=False)
    weight = Column(Integer, default=100)
    health_score = Column(Float, default=0.0)
    last_health_at = Column(DateTime, nullable=True)
    is_healthy = Column(Boolean, default=True)
    panel_latency_ms = Column(Integer, nullable=True)
    panel_error_rate = Column(Float, default=0.0)
    active_clients = Column(Integer, default=0)
    provisioned_clients_count = Column(Integer, default=0)
    online_connections_hint = Column(Integer, default=0)
    cpu_percent = Column(Float, default=0.0)
    memory_used_mb = Column(Integer, nullable=True)
    memory_total_mb = Column(Integer, nullable=True)
    disk_used_gb = Column(Float, nullable=True)
    disk_total_gb = Column(Float, nullable=True)
    disk_free_gb = Column(Float, nullable=True)
    network_rx_bytes_total = Column(BigInteger, nullable=True)
    network_tx_bytes_total = Column(BigInteger, nullable=True)
    network_rx_mbps = Column(Float, nullable=True)
    network_tx_mbps = Column(Float, nullable=True)
    network_total_mbps = Column(Float, nullable=True)
    network_rx_mbps_1m = Column(Float, nullable=True)
    network_tx_mbps_1m = Column(Float, nullable=True)
    network_rx_mbps_5m = Column(Float, nullable=True)
    network_tx_mbps_5m = Column(Float, nullable=True)
    tcp_retrans_percent = Column(Float, nullable=True)
    packet_loss_percent = Column(Float, nullable=True)
    dataplane_ok = Column(Boolean, nullable=True)
    dataplane_rtt_ms = Column(Integer, nullable=True)
    capacity_score = Column(Float, nullable=True)
    capacity_state = Column(String(32), default="unknown")
    capacity_reject_reason = Column(String(64), nullable=True)
    last_ok_at = Column(DateTime, nullable=True)
    last_probe_at = Column(DateTime, nullable=True)
    last_probe_stage = Column(String(64), nullable=True)
    last_probe_error_kind = Column(String(64), nullable=True)
    last_probe_error_message = Column(String(500), nullable=True)
    hoster_family = Column(String(64), nullable=True)
    hoster_asn = Column(String(32), nullable=True)
    hoster_subnet = Column(String(64), nullable=True)
    ipv4_health = Column(String(32), nullable=True)
    ipv6_health = Column(String(32), nullable=True)
    last_probe_classification = Column(String(64), nullable=True)
    transport_health_json = Column(Text, nullable=True)
    transport_profiles_json = Column(Text, nullable=True)
    observer_push_secret = Column(String(128), nullable=True)
    observer_last_push_at = Column(DateTime, nullable=True)
    observer_last_batch_id = Column(String(128), nullable=True)
    observer_unmatched_count = Column(Integer, default=0)
    observer_parse_error_count = Column(Integer, default=0)


class UserNode(Base):
    __tablename__ = "user_nodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, index=True, nullable=False)
    node_id = Column(Integer, index=True, nullable=False)
    client_uuid = Column(String(36), nullable=False)
    panel_email = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=_utcnow)

    __table_args__ = (UniqueConstraint("tg_id", "node_id", name="uq_user_nodes_tg_node"),)


class AccessKey(Base):
    __tablename__ = "access_keys"
    __table_args__ = (
        UniqueConstraint("tg_id", "key_uuid", name="uq_access_keys_tg_uuid"),
        UniqueConstraint("node_code", "panel_email", name="uq_access_keys_node_email"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, index=True, nullable=False)
    key_uuid = Column(String(36), index=True, nullable=False)
    panel_email = Column(String(100), nullable=False)
    node_code = Column(String(32), index=True, nullable=True)
    pool_code = Column(String(32), index=True, nullable=False, default="premium_pool")
    state = Column(String(32), index=True, nullable=False, default="active")
    source = Column(String(32), nullable=False, default="legacy_user")
    is_primary = Column(Boolean, default=True, nullable=False)
    provisioned_at = Column(DateTime, nullable=True)
    last_seen_at = Column(DateTime, nullable=True)
    rotated_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    meta_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, nullable=False)


class NodeCapacityPolicy(Base):
    __tablename__ = "node_capacity_policy"
    __table_args__ = (UniqueConstraint("node_code", name="uq_node_capacity_policy_code"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    node_code = Column(String(32), index=True, nullable=False)
    max_tx_mbps = Column(Float, nullable=True)
    soft_tx_ratio = Column(Float, default=0.70, nullable=False)
    drain_tx_ratio = Column(Float, default=0.82, nullable=False)
    hard_tx_ratio = Column(Float, default=0.92, nullable=False)
    soft_cpu_percent = Column(Float, default=75.0, nullable=False)
    hard_cpu_percent = Column(Float, default=90.0, nullable=False)
    stale_after_seconds = Column(Integer, default=180, nullable=False)
    max_packet_loss_percent = Column(Float, default=2.0, nullable=False)
    max_tcp_retrans_percent = Column(Float, default=5.0, nullable=False)
    rank_weight = Column(Integer, default=100, nullable=False)
    allow_free_pool = Column(Boolean, default=False, nullable=False)
    allow_premium_pool = Column(Boolean, default=True, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    updated_by = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, nullable=False)


class NodeRuntimeMetric(Base):
    __tablename__ = "node_runtime_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    node_code = Column(String(32), index=True, nullable=False)
    sampled_at = Column(DateTime, default=_utcnow, index=True, nullable=False)
    source = Column(String(64), default="collector", nullable=False)
    batch_id = Column(String(128), nullable=True)
    provisioned_clients_count = Column(Integer, default=0, nullable=False)
    online_connections_hint = Column(Integer, default=0, nullable=False)
    network_rx_mbps_1m = Column(Float, nullable=True)
    network_tx_mbps_1m = Column(Float, nullable=True)
    network_rx_mbps_5m = Column(Float, nullable=True)
    network_tx_mbps_5m = Column(Float, nullable=True)
    network_total_mbps = Column(Float, nullable=True)
    cpu_percent = Column(Float, nullable=True)
    memory_used_mb = Column(Integer, nullable=True)
    memory_total_mb = Column(Integer, nullable=True)
    tcp_retrans_percent = Column(Float, nullable=True)
    packet_loss_percent = Column(Float, nullable=True)
    dataplane_ok = Column(Boolean, nullable=True)
    dataplane_rtt_ms = Column(Integer, nullable=True)
    capacity_score = Column(Float, nullable=True)
    capacity_state = Column(String(32), default="unknown", nullable=False)
    reject_reason = Column(String(64), nullable=True)
    meta_json = Column(Text, nullable=True)


class KeyUsageRollup(Base):
    __tablename__ = "key_usage_rollups"
    __table_args__ = (
        UniqueConstraint("key_id", "node_code", "window_bucket_at", "window_seconds", name="uq_key_usage_rollup_window"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    key_id = Column(Integer, index=True, nullable=True)
    tg_id = Column(BigInteger, index=True, nullable=True)
    node_code = Column(String(32), index=True, nullable=False)
    panel_email = Column(String(100), index=True, nullable=True)
    window_bucket_at = Column(DateTime, index=True, nullable=False)
    window_seconds = Column(Integer, default=300, nullable=False)
    upload_bytes = Column(BigInteger, default=0, nullable=False)
    download_bytes = Column(BigInteger, default=0, nullable=False)
    total_bytes = Column(BigInteger, default=0, nullable=False)
    peak_tx_mbps = Column(Float, nullable=True)
    observations = Column(Integer, default=0, nullable=False)
    source = Column(String(64), default="observer", nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)


class KeySourceObservation(Base):
    __tablename__ = "key_source_observations"
    __table_args__ = (
        UniqueConstraint("key_id", "node_code", "source_ip_hash", "window_bucket_at", name="uq_key_source_window"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    key_id = Column(Integer, index=True, nullable=True)
    tg_id = Column(BigInteger, index=True, nullable=True)
    node_code = Column(String(32), index=True, nullable=False)
    panel_email = Column(String(100), index=True, nullable=True)
    source_ip_hash = Column(String(64), index=True, nullable=False)
    source_asn = Column(String(32), nullable=True)
    source_country = Column(String(8), nullable=True)
    window_bucket_at = Column(DateTime, index=True, nullable=False)
    first_seen_at = Column(DateTime, nullable=False)
    last_seen_at = Column(DateTime, nullable=False)
    hit_count = Column(Integer, default=0, nullable=False)
    meta_json = Column(Text, nullable=True)


class KeyPressureState(Base):
    __tablename__ = "key_pressure_state"

    key_id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, index=True, nullable=True)
    node_code = Column(String(32), index=True, nullable=True)
    panel_email = Column(String(100), index=True, nullable=True)
    state = Column(String(32), index=True, default="ok", nullable=False)
    pressure_score = Column(Float, default=0.0, nullable=False)
    reasons_json = Column(Text, nullable=True)
    distinct_source_ips_1h = Column(Integer, default=0, nullable=False)
    distinct_source_ips_24h = Column(Integer, default=0, nullable=False)
    node_count_24h = Column(Integer, default=0, nullable=False)
    traffic_gb_24h = Column(Float, default=0.0, nullable=False)
    manual_review_required = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, index=True, nullable=False)


class SubscriptionFetchEvent(Base):
    __tablename__ = "subscription_fetch_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, index=True, nullable=False)
    token_fp = Column(String(32), index=True, nullable=False)
    lookup_mode = Column(String(32), nullable=False)
    client_format = Column(String(32), index=True, nullable=False)
    user_agent_hash = Column(String(64), nullable=True)
    request_host = Column(String(255), nullable=True)
    selected_nodes_json = Column(Text, nullable=True)
    excluded_nodes_json = Column(Text, nullable=True)
    response_status = Column(Integer, default=200, nullable=False)
    created_at = Column(DateTime, default=_utcnow, index=True, nullable=False)


class RenderedSubscriptionSnapshot(Base):
    __tablename__ = "rendered_subscription_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fetch_event_id = Column(Integer, index=True, nullable=True)
    tg_id = Column(BigInteger, index=True, nullable=False)
    profile_revision = Column(String(128), nullable=True)
    client_format = Column(String(32), index=True, nullable=False)
    node_order_json = Column(Text, nullable=False)
    excluded_nodes_json = Column(Text, nullable=True)
    content_sha256 = Column(String(64), index=True, nullable=False)
    created_at = Column(DateTime, default=_utcnow, index=True, nullable=False)


class NodePoolMembership(Base):
    __tablename__ = "node_pool_membership"
    __table_args__ = (UniqueConstraint("node_code", "pool_code", name="uq_node_pool_membership_code_pool"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    node_code = Column(String(32), index=True, nullable=False)
    pool_code = Column(String(32), index=True, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    source = Column(String(32), default="migration", nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, nullable=False)


class NodeProvisioningJob(Base):
    __tablename__ = "node_provisioning_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, index=True, nullable=True)
    key_id = Column(Integer, index=True, nullable=True)
    node_code = Column(String(32), index=True, nullable=True)
    job_type = Column(String(32), index=True, nullable=False)
    status = Column(String(32), index=True, default="queued", nullable=False)
    desired_state_json = Column(Text, nullable=True)
    result_json = Column(Text, nullable=True)
    idempotency_key = Column(String(160), unique=True, index=True, nullable=True)
    attempts = Column(Integer, default=0, nullable=False)
    next_run_at = Column(DateTime, nullable=True)
    locked_at = Column(DateTime, nullable=True)
    lock_token = Column(String(64), index=True, nullable=True)
    last_error_code = Column(String(64), nullable=True)
    replacement_key_uuid = Column(String(36), nullable=True)
    completed_at = Column(DateTime, nullable=True)
    manual_review_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, nullable=False)


class ProviderTrafficQuota(Base):
    __tablename__ = "provider_traffic_quotas"
    __table_args__ = (UniqueConstraint("node_code", name="uq_provider_traffic_quotas_node_code"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    node_code = Column(String(32), index=True, nullable=False)
    included_bytes = Column(BigInteger, default=0, nullable=False)
    reset_day = Column(Integer, default=1, nullable=False)
    timezone = Column(String(64), default="UTC", nullable=False)
    warning_ratio = Column(Float, default=0.80, nullable=False)
    critical_ratio = Column(Float, default=0.95, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)
    updated_by = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, nullable=False)


class ProviderTrafficQuotaAudit(Base):
    __tablename__ = "provider_traffic_quota_audit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    quota_id = Column(Integer, index=True, nullable=True)
    node_code = Column(String(32), index=True, nullable=False)
    actor_tg_id = Column(BigInteger, index=True, nullable=True)
    action = Column(String(32), nullable=False)
    before_json = Column(Text, nullable=True)
    after_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)


class OpsAlert(Base):
    __tablename__ = "ops_alerts"
    __table_args__ = (UniqueConstraint("fingerprint", name="uq_ops_alerts_fingerprint"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    fingerprint = Column(String(160), index=True, nullable=False)
    source = Column(String(64), index=True, nullable=False)
    severity = Column(String(16), index=True, nullable=False)
    status = Column(String(24), index=True, default="active", nullable=False)
    title = Column(String(180), nullable=False)
    body = Column(String(1000), nullable=True)
    node_code = Column(String(32), index=True, nullable=True)
    tg_id = Column(BigInteger, index=True, nullable=True)
    key_id = Column(Integer, index=True, nullable=True)
    first_seen_at = Column(DateTime, default=_utcnow, nullable=False)
    last_seen_at = Column(DateTime, default=_utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(BigInteger, nullable=True)
    silence_until = Column(DateTime, nullable=True)
    last_delivery_at = Column(DateTime, nullable=True)
    last_delivery_status = Column(String(64), nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, nullable=False)


class AdminAudit(Base):
    __tablename__ = "admin_audit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    actor_tg_id = Column(BigInteger, index=True, nullable=False)
    action = Column(String(64), nullable=False)
    target_tg_id = Column(BigInteger, index=True, nullable=True)
    meta = Column(String(2000), nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class SecurityRateLimitBucket(Base):
    __tablename__ = "security_rate_limit_buckets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bucket_key = Column(String(160), unique=True, index=True, nullable=False)
    scope = Column(String(64), index=True, nullable=False)
    fingerprint = Column(String(64), index=True, nullable=False)
    window_start = Column(DateTime, index=True, nullable=False)
    expires_at = Column(DateTime, index=True, nullable=False)
    hits = Column(Integer, default=0, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, nullable=False)


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(64), index=True, nullable=False)
    scope = Column(String(64), index=True, nullable=True)
    fingerprint = Column(String(64), index=True, nullable=True)
    client_ip = Column(String(64), index=True, nullable=True)
    subject = Column(String(160), nullable=True)
    reason = Column(String(160), nullable=True)
    meta_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, index=True, nullable=False)


class KeyActionHistory(Base):
    __tablename__ = "key_action_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, index=True, nullable=False)
    node_code = Column(String(32), index=True, nullable=True)
    action = Column(String(64), nullable=False)
    actor_tg_id = Column(BigInteger, nullable=True)
    source = Column(String(32), default="admin", nullable=False)
    meta = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)


class UserKeyPolicy(Base):
    __tablename__ = "user_key_policy"
    __table_args__ = (UniqueConstraint("tg_id", "node_code", name="uq_user_key_policy_tg_node"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, index=True, nullable=False)
    node_code = Column(String(32), index=True, nullable=False)
    burst_mbps = Column(Integer, nullable=True)
    soft_cap_gb = Column(Integer, nullable=True)
    hard_cap_gb = Column(Integer, nullable=True)
    notify_soft = Column(Boolean, default=True, nullable=False)
    notify_hard = Column(Boolean, default=True, nullable=False)
    auto_disable_on_hard = Column(Boolean, default=True, nullable=False)
    updated_by = Column(BigInteger, nullable=True)
    updated_at = Column(DateTime, default=_utcnow, nullable=False)


class ReferralBonusQueue(Base):
    __tablename__ = "referral_bonus_queue"
    __table_args__ = (
        UniqueConstraint(
            "order_id",
            "referrer_tg_id",
            "referred_tg_id",
            name="uq_referral_bonus_queue_order_pair",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    referrer_tg_id = Column(BigInteger, index=True, nullable=False)
    referred_tg_id = Column(BigInteger, index=True, nullable=False)
    order_id = Column(String(128), index=True, nullable=False)
    queued_at = Column(DateTime, default=_utcnow, nullable=False)
    ready_at = Column(DateTime, nullable=False)
    status = Column(String(24), default="pending", nullable=False)
    processed_at = Column(DateTime, nullable=True)
    meta = Column(Text, nullable=True)


class IncentiveCampaign(Base):
    __tablename__ = "incentive_campaigns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    campaign_type = Column(String(16), nullable=False)  # promo | gift
    target_value = Column(String(64), nullable=False)   # promo code or gift card type
    segment = Column(String(32), default="all_active", nullable=False)
    starts_at = Column(DateTime, nullable=True)
    ends_at = Column(DateTime, nullable=True)
    max_activations = Column(Integer, default=-1, nullable=False)
    activations_count = Column(Integer, default=0, nullable=False)
    auto_disable = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(BigInteger, nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, nullable=False)


class RewardClaim(Base):
    __tablename__ = "reward_claims"
    __table_args__ = (UniqueConstraint("tg_id", "reward_key", name="uq_reward_claim_tg_key"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, index=True, nullable=False)
    reward_key = Column(String(64), nullable=False)
    meta = Column(Text, nullable=True)
    claimed_at = Column(DateTime, default=_utcnow, nullable=False)


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_tg_id = Column(BigInteger, index=True, nullable=False)
    account_id = Column(String(36), index=True, nullable=True)
    status = Column(String(20), default="open", nullable=False)  # open / in_progress / closed
    subject = Column(String(200), nullable=True)
    assigned_admin_tg_id = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, nullable=False)
    closed_at = Column(DateTime, nullable=True)


class SupportAttachment(Base):
    __tablename__ = "support_attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stored_name = Column(String(160), unique=True, index=True, nullable=False)
    owner_tg_id = Column(BigInteger, index=True, nullable=False)
    owner_account_id = Column(String(36), index=True, nullable=True)
    original_name = Column(String(160), nullable=False)
    content_type = Column(String(80), nullable=False)
    size_bytes = Column(Integer, default=0, nullable=False)
    media_type = Column(String(32), nullable=False)
    ticket_id = Column(Integer, index=True, nullable=True)
    message_id = Column(Integer, unique=True, index=True, nullable=True)
    attached_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, index=True, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)


class SupportTicketMessage(Base):
    __tablename__ = "support_ticket_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, index=True, nullable=False)
    sender_tg_id = Column(BigInteger, index=True, nullable=False)
    sender_role = Column(String(20), nullable=False)  # user / admin / assistant
    body = Column(String(2000), nullable=False)
    media_type = Column(String(32), nullable=True)
    media_file_id = Column(String(256), nullable=True)
    media_payload = Column(String(2000), nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)


class NodeHealthSample(Base):
    __tablename__ = "node_health_samples"

    id = Column(Integer, primary_key=True, autoincrement=True)
    node_code = Column(String(20), index=True, nullable=False)
    sampled_at = Column(DateTime, default=_utcnow, nullable=False)
    panel_latency_ms = Column(Integer, nullable=True)
    panel_error_rate = Column(Float, default=0.0)
    active_clients = Column(Integer, default=0)
    cpu_percent = Column(Float, default=0.0)
    memory_used_mb = Column(Integer, nullable=True)
    memory_total_mb = Column(Integer, nullable=True)
    disk_used_gb = Column(Float, nullable=True)
    disk_total_gb = Column(Float, nullable=True)
    disk_free_gb = Column(Float, nullable=True)
    network_rx_bytes_total = Column(BigInteger, nullable=True)
    network_tx_bytes_total = Column(BigInteger, nullable=True)
    network_rx_mbps = Column(Float, nullable=True)
    network_tx_mbps = Column(Float, nullable=True)
    network_total_mbps = Column(Float, nullable=True)
    total_up_bytes = Column(BigInteger, default=0)
    total_down_bytes = Column(BigInteger, default=0)
    total_traffic_bytes = Column(BigInteger, default=0)
    is_healthy = Column(Boolean, default=True)
    score = Column(Float, default=0.0)
    source = Column(String(64), default="collector")
    probe_at = Column(DateTime, nullable=True)
    probe_stage = Column(String(64), nullable=True)
    probe_error_kind = Column(String(64), nullable=True)
    probe_error_message = Column(String(500), nullable=True)
    probe_classification = Column(String(64), nullable=True)
    ipv4_health = Column(String(32), nullable=True)
    ipv6_health = Column(String(32), nullable=True)
    transport_health_json = Column(Text, nullable=True)


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, index=True, nullable=False)
    event_name = Column(String(64), index=True, nullable=False)
    source = Column(String(32), default="unknown", nullable=False)
    session_id = Column(String(64), nullable=True)
    meta_json = Column(String(4000), nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)


class WarpEvent(Base):
    __tablename__ = "warp_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, index=True, nullable=False)
    install_id = Column(String(128), index=True, nullable=True)
    event_name = Column(String(64), index=True, nullable=False)
    state = Column(String(32), index=True, nullable=False)
    reason_code = Column(String(64), nullable=True)
    runtime_ready = Column(Boolean, default=False, nullable=False)
    consented = Column(Boolean, default=False, nullable=False)
    meta_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, index=True, nullable=False)


class WarpMaterial(Base):
    __tablename__ = "warp_materials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, index=True, nullable=False)
    install_id = Column(String(128), index=True, nullable=True)
    source = Column(String(64), default="operator_provisioned", nullable=False)
    mode = Column(String(32), default="proxy_over_warp", nullable=False)
    state = Column(String(32), default="ready", index=True, nullable=False)
    wireguard_ciphertext = Column(Text, nullable=False)
    account_ciphertext = Column(Text, nullable=True)
    material_hash = Column(String(64), index=True, nullable=True)
    is_active = Column(Boolean, default=True, index=True, nullable=False)
    provisioned_at = Column(DateTime, default=_utcnow, index=True, nullable=False)
    rotation_requested_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=_utcnow, nullable=False)


class FunnelEvent(Base):
    __tablename__ = "funnel_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(96), index=True, nullable=False)
    tg_id = Column(BigInteger, index=True, nullable=True)
    channel = Column(String(32), index=True, default="site", nullable=False)
    event_name = Column(String(64), index=True, nullable=False)
    stage = Column(String(64), index=True, nullable=False)
    source = Column(String(64), index=True, default="unknown", nullable=False)
    path = Column(String(512), nullable=True)
    referrer = Column(String(600), nullable=True)
    campaign = Column(String(64), nullable=True)
    meta_json = Column(String(4000), nullable=True)
    created_at = Column(DateTime, default=_utcnow, index=True, nullable=False)


class ObserverBatch(Base):
    __tablename__ = "observer_batches"
    __table_args__ = (UniqueConstraint("node_id", "batch_id", name="uq_observer_batches_node_batch"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(Integer, index=True, nullable=False)
    batch_id = Column(String(128), nullable=False)
    cursor_json = Column(Text, nullable=True)
    observation_count = Column(Integer, default=0, nullable=False)
    accepted_count = Column(Integer, default=0, nullable=False)
    deduped_count = Column(Integer, default=0, nullable=False)
    unmatched_count = Column(Integer, default=0, nullable=False)
    parse_error_count = Column(Integer, default=0, nullable=False)
    updated_tg_ids_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)


class ObserverDailyObservation(Base):
    __tablename__ = "observer_daily_observations"
    __table_args__ = (
        UniqueConstraint(
            "tg_id",
            "node_id",
            "source_ip_raw",
            "day_bucket",
            name="uq_observer_daily_tg_node_ip_day",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, index=True, nullable=False)
    node_id = Column(Integer, index=True, nullable=False)
    source_ip_raw = Column(String(64), nullable=False)
    score_ip_key = Column(String(64), index=True, nullable=False)
    day_bucket = Column(Date, index=True, nullable=False)
    first_seen_at = Column(DateTime, nullable=False)
    last_seen_at = Column(DateTime, nullable=False)
    hit_count = Column(Integer, default=0, nullable=False)
    identity_source = Column(String(32), nullable=False)
    counts_for_suspicion = Column(Boolean, default=True, nullable=False)


class ObserverWindowObservation(Base):
    __tablename__ = "observer_window_observations"
    __table_args__ = (
        UniqueConstraint(
            "tg_id",
            "node_id",
            "score_ip_key",
            "window_bucket_at",
            name="uq_observer_window_tg_node_score_bucket",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, index=True, nullable=False)
    node_id = Column(Integer, index=True, nullable=False)
    source_ip_raw = Column(String(64), nullable=False)
    score_ip_key = Column(String(64), index=True, nullable=False)
    window_bucket_at = Column(DateTime, index=True, nullable=False)
    first_seen_at = Column(DateTime, nullable=False)
    last_seen_at = Column(DateTime, nullable=False)
    hit_count = Column(Integer, default=0, nullable=False)
    counts_for_suspicion = Column(Boolean, default=True, nullable=False)


class ObserverUserState(Base):
    __tablename__ = "observer_user_state"

    tg_id = Column(BigInteger, primary_key=True)
    state = Column(String(20), default="ok", nullable=False)
    reasons_json = Column(Text, nullable=True)
    observed_ip_count_24h = Column(Integer, default=0, nullable=False)
    observed_ip_count_7d = Column(Integer, default=0, nullable=False)
    observed_ip_count_30d = Column(Integer, default=0, nullable=False)
    observed_node_count_24h = Column(Integer, default=0, nullable=False)
    observed_node_count_7d = Column(Integer, default=0, nullable=False)
    observed_node_count_30d = Column(Integer, default=0, nullable=False)
    overlap_count_24h = Column(Integer, default=0, nullable=False)
    last_observed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=_utcnow, nullable=False)


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
    created_at = Column(DateTime, default=_utcnow, nullable=False)


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
    started_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, nullable=False)
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
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    paid_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("provider", "order_id", name="uq_external_orders_provider_order"),
        Index("ix_external_orders_status_created_at_id", "status", "created_at", "id"),
    )


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
    created_at = Column(DateTime, default=_utcnow, nullable=False)

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
    created_at = Column(DateTime, default=_utcnow, nullable=False)


class CampaignSend(Base):
    __tablename__ = "campaign_sends"
    __table_args__ = (UniqueConstraint("tg_id", "campaign_key", name="uq_campaign_sends_tg_campaign"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, index=True, nullable=False)
    campaign_key = Column(String(64), nullable=False)
    sent_at = Column(DateTime, default=_utcnow, nullable=False)


class FamilySlot(Base):
    __tablename__ = "family_slots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, index=True, nullable=False)
    slots = Column(Integer, default=1, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)


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
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, nullable=False)


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
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, nullable=False)


class StartLink(Base):
    __tablename__ = "start_links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(64), unique=True, index=True, nullable=False)
    description = Column(String(240), nullable=True)
    target_action = Column(String(64), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, nullable=False)


class AppSetting(Base):
    __tablename__ = "app_settings"

    key = Column(String(64), primary_key=True)
    value_json = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=_utcnow, nullable=False)
