from __future__ import annotations

import argparse
import json
import os
import shlex
from pathlib import Path

import paramiko
from ssh_host_keys import configure_ssh_host_key_policy


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"


def _parse_password(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = [ln.strip() for ln in raw.splitlines()]
    for i, line in enumerate(lines):
        if "BRAINnode" not in line:
            continue
        for value in lines[i + 1 : i + 30]:
            if value and not value.startswith("ssh-ed25519 "):
                return value
    return ""


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 120) -> tuple[int, str, str]:
    _stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return code, out, err


def _sql(retention_days: int, sample_limit: int) -> str:
    days = int(retention_days)
    limit = int(sample_limit)
    return f"""
WITH base AS MATERIALIZED (
    SELECT
        u.*,
        CASE
            WHEN coalesce(u.is_manual, false)
                 OR u.tg_id < 0
                 OR upper(coalesce(u.sub_type, '')) = 'MANUAL'
                 OR u.created_by_admin IS NOT NULL
                THEN 'manual_test'
            WHEN (coalesce(u.is_app_user, false) OR nullif(u.app_install_id, '') IS NOT NULL)
                 AND u.linked_telegram_id IS NULL
                 AND u.username IS NULL
                THEN 'app_unlinked'
            WHEN coalesce(u.is_app_user, false) OR nullif(u.app_install_id, '') IS NOT NULL
                THEN 'app_or_hybrid'
            ELSE 'telegram'
        END AS origin,
        CASE
            WHEN coalesce(u.is_active, false) = true
                 AND u.expiry_at IS NOT NULL
                 AND u.expiry_at > now()
                THEN 'active'
            WHEN coalesce(u.is_active, false) = false
                 AND u.expiry_at IS NOT NULL
                 AND u.expiry_at > now()
                THEN 'blocked'
            ELSE 'expired'
        END AS effective_status,
        greatest(
            coalesce(u.app_last_seen_at, timestamp '1970-01-01'),
            coalesce(u.created_at, timestamp '1970-01-01'),
            coalesce(u.expiry_at, timestamp '1970-01-01')
        ) AS last_activity_at
    FROM users u
),
candidates AS MATERIALIZED (
    SELECT *
    FROM base
    WHERE effective_status IN ('blocked', 'expired')
      AND last_activity_at < (now() - make_interval(days => {days}))
),
candidate_paid_attempts AS MATERIALIZED (
    SELECT DISTINCT pa.tg_id
    FROM pay_attempts pa
    JOIN candidates c ON c.tg_id = pa.tg_id
    WHERE pa.status IN ('paid', 'succeeded', 'success', 'completed')
),
candidate_paid_orders AS MATERIALIZED (
    SELECT DISTINCT eo.tg_id
    FROM external_orders eo
    JOIN candidates c ON c.tg_id = eo.tg_id
    WHERE eo.status IN ('paid', 'succeeded', 'success', 'completed', 'fulfilled')
),
candidate_support AS MATERIALIZED (
    SELECT DISTINCT st.user_tg_id AS tg_id
    FROM support_tickets st
    JOIN candidates c ON c.tg_id = st.user_tg_id
),
safe_garbage AS MATERIALIZED (
    SELECT c.*
    FROM candidates c
    WHERE c.origin IN ('manual_test', 'app_unlinked')
      AND coalesce(c.stars_paid, 0) = 0
      AND coalesce(c.first_purchase_done, false) = false
      AND NOT EXISTS (SELECT 1 FROM candidate_paid_attempts p WHERE p.tg_id = c.tg_id)
      AND NOT EXISTS (SELECT 1 FROM candidate_paid_orders o WHERE o.tg_id = c.tg_id)
      AND NOT EXISTS (SELECT 1 FROM candidate_support s WHERE s.tg_id = c.tg_id)
),
table_counts AS (
    SELECT *
    FROM (VALUES
        ('users', (SELECT count(*)::bigint FROM candidates)),
        ('safe_garbage_users', (SELECT count(*)::bigint FROM safe_garbage)),
        ('user_nodes', (SELECT count(*)::bigint FROM user_nodes WHERE tg_id IN (SELECT tg_id FROM candidates))),
        ('web_email_identities', (SELECT count(*)::bigint FROM web_email_identities WHERE linked_tg_id IN (SELECT tg_id FROM candidates))),
        ('web_email_tokens', (
            SELECT count(*)::bigint
            FROM web_email_tokens
            WHERE identity_id IN (
                SELECT id FROM web_email_identities WHERE linked_tg_id IN (SELECT tg_id FROM candidates)
            )
        )),
        ('web_cabinet_handoff_tokens', (SELECT count(*)::bigint FROM web_cabinet_handoff_tokens WHERE tg_id IN (SELECT tg_id FROM candidates))),
        ('achievements', (SELECT count(*)::bigint FROM achievements WHERE tg_id IN (SELECT tg_id FROM candidates))),
        ('reviews', (SELECT count(*)::bigint FROM reviews WHERE tg_id IN (SELECT tg_id FROM candidates))),
        ('feedback_entries', (SELECT count(*)::bigint FROM feedback_entries WHERE tg_id IN (SELECT tg_id FROM candidates))),
        ('promo_usage', (SELECT count(*)::bigint FROM promo_usage WHERE tg_id IN (SELECT tg_id FROM candidates))),
        ('key_action_history', (SELECT count(*)::bigint FROM key_action_history WHERE tg_id IN (SELECT tg_id FROM candidates) OR actor_tg_id IN (SELECT tg_id FROM candidates))),
        ('user_key_policy', (SELECT count(*)::bigint FROM user_key_policy WHERE tg_id IN (SELECT tg_id FROM candidates) OR updated_by IN (SELECT tg_id FROM candidates))),
        ('referral_bonus_queue', (SELECT count(*)::bigint FROM referral_bonus_queue WHERE referrer_tg_id IN (SELECT tg_id FROM candidates) OR referred_tg_id IN (SELECT tg_id FROM candidates))),
        ('reward_claims', (SELECT count(*)::bigint FROM reward_claims WHERE tg_id IN (SELECT tg_id FROM candidates))),
        ('support_tickets', (SELECT count(*)::bigint FROM support_tickets WHERE user_tg_id IN (SELECT tg_id FROM candidates))),
        ('support_ticket_messages', (
            SELECT count(*)::bigint
            FROM support_ticket_messages
            WHERE sender_tg_id IN (SELECT tg_id FROM candidates)
               OR ticket_id IN (SELECT id FROM support_tickets WHERE user_tg_id IN (SELECT tg_id FROM candidates))
        )),
        ('events', (SELECT count(*)::bigint FROM events WHERE tg_id IN (SELECT tg_id FROM candidates))),
        ('warp_events', (SELECT count(*)::bigint FROM warp_events WHERE tg_id IN (SELECT tg_id FROM candidates))),
        ('warp_materials', (SELECT count(*)::bigint FROM warp_materials WHERE tg_id IN (SELECT tg_id FROM candidates))),
        ('funnel_events', (SELECT count(*)::bigint FROM funnel_events WHERE tg_id IN (SELECT tg_id FROM candidates))),
        ('observer_daily_observations', (SELECT count(*)::bigint FROM observer_daily_observations WHERE tg_id IN (SELECT tg_id FROM candidates))),
        ('observer_window_observations', (SELECT count(*)::bigint FROM observer_window_observations WHERE tg_id IN (SELECT tg_id FROM candidates))),
        ('observer_user_state', (SELECT count(*)::bigint FROM observer_user_state WHERE tg_id IN (SELECT tg_id FROM candidates))),
        ('offers', (SELECT count(*)::bigint FROM offers WHERE tg_id IN (SELECT tg_id FROM candidates))),
        ('pay_attempts', (SELECT count(*)::bigint FROM pay_attempts WHERE tg_id IN (SELECT tg_id FROM candidates))),
        ('external_orders', (SELECT count(*)::bigint FROM external_orders WHERE tg_id IN (SELECT tg_id FROM candidates))),
        ('external_payment_events', (
            SELECT count(*)::bigint
            FROM external_payment_events epe
            WHERE EXISTS (
                SELECT 1
                FROM external_orders eo
                JOIN candidates c ON c.tg_id = eo.tg_id
                WHERE eo.provider = epe.provider
                  AND eo.order_id = epe.order_id
            )
        )),
        ('points_ledger', (SELECT count(*)::bigint FROM points_ledger WHERE tg_id IN (SELECT tg_id FROM candidates) OR ref_tg_id IN (SELECT tg_id FROM candidates))),
        ('campaign_sends', (SELECT count(*)::bigint FROM campaign_sends WHERE tg_id IN (SELECT tg_id FROM candidates))),
        ('family_slots', (SELECT count(*)::bigint FROM family_slots WHERE tg_id IN (SELECT tg_id FROM candidates))),
        ('gift_cards_created_by', (SELECT count(*)::bigint FROM gift_cards WHERE created_by IN (SELECT tg_id FROM candidates))),
        ('gift_cards_redeemed_by', (SELECT count(*)::bigint FROM gift_cards WHERE redeemed_by IN (SELECT tg_id FROM candidates))),
        ('admin_audit_actor', (SELECT count(*)::bigint FROM admin_audit WHERE actor_tg_id IN (SELECT tg_id FROM candidates))),
        ('admin_audit_target', (SELECT count(*)::bigint FROM admin_audit WHERE target_tg_id IN (SELECT tg_id FROM candidates))),
        ('incentive_campaigns_created_by', (SELECT count(*)::bigint FROM incentive_campaigns WHERE created_by IN (SELECT tg_id FROM candidates)))
    ) AS v(table_name, row_count)
)
SELECT jsonb_build_object(
    'generated_at_utc', to_char(now() AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
    'retention_days', {days},
    'cutoff_at_utc', to_char((now() - make_interval(days => {days})) AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
    'users_total', (SELECT count(*) FROM users),
    'users_by_status_origin', coalesce((
        SELECT jsonb_agg(to_jsonb(x) ORDER BY x.effective_status, x.origin)
        FROM (
            SELECT effective_status, origin, count(*) AS users
            FROM base
            GROUP BY effective_status, origin
        ) x
    ), '[]'::jsonb),
    'candidates_total', (SELECT count(*) FROM candidates),
    'candidates_by_status_origin', coalesce((
        SELECT jsonb_agg(to_jsonb(x) ORDER BY x.effective_status, x.origin)
        FROM (
            SELECT effective_status, origin, count(*) AS users
            FROM candidates
            GROUP BY effective_status, origin
        ) x
    ), '[]'::jsonb),
    'safe_garbage_total', (SELECT count(*) FROM safe_garbage),
    'risk_flags', jsonb_build_object(
        'stars_paid_positive_users', (SELECT count(*) FROM candidates WHERE coalesce(stars_paid, 0) > 0),
        'first_purchase_done_users', (SELECT count(*) FROM candidates WHERE coalesce(first_purchase_done, false) = true),
        'paid_pay_attempt_users', (SELECT count(*) FROM candidate_paid_attempts),
        'paid_external_order_users', (SELECT count(*) FROM candidate_paid_orders),
        'support_ticket_users', (SELECT count(*) FROM candidate_support)
    ),
    'candidate_table_counts', (
        SELECT jsonb_object_agg(table_name, row_count ORDER BY table_name)
        FROM table_counts
    ),
    'candidate_samples', coalesce((
        SELECT jsonb_agg(to_jsonb(x) ORDER BY x.last_activity_at_utc ASC)
        FROM (
            SELECT
                tg_id,
                username,
                origin,
                effective_status,
                sub_type,
                current_plan_code,
                is_active,
                stars_paid,
                first_purchase_done,
                to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS created_at_utc,
                to_char(expiry_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS expiry_at_utc,
                to_char(app_last_seen_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS app_last_seen_at_utc,
                to_char(last_activity_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS last_activity_at_utc
            FROM candidates
            ORDER BY last_activity_at ASC
            LIMIT {limit}
        ) x
    ), '[]'::jsonb),
    'safe_garbage_samples', coalesce((
        SELECT jsonb_agg(to_jsonb(x) ORDER BY x.last_activity_at_utc ASC)
        FROM (
            SELECT
                tg_id,
                username,
                origin,
                effective_status,
                sub_type,
                current_plan_code,
                is_active,
                to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS created_at_utc,
                to_char(expiry_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS expiry_at_utc,
                to_char(app_last_seen_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS app_last_seen_at_utc,
                to_char(last_activity_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS last_activity_at_utc
            FROM safe_garbage
            ORDER BY last_activity_at ASC
            LIMIT {limit}
        ) x
    ), '[]'::jsonb)
)::text;
""".strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only audit of inactive production users on brain Postgres.")
    parser.add_argument("--brain-ip", required=True)
    parser.add_argument("--ssh-user", default="root")
    parser.add_argument("--ssh-port", type=int, default=29374)
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--db-name", default="portal")
    parser.add_argument("--retention-days", type=int, default=14)
    parser.add_argument("--sample-limit", type=int, default=30)
    args = parser.parse_args()

    if args.retention_days < 1:
        raise SystemExit("--retention-days must be positive")
    if args.sample_limit < 0:
        raise SystemExit("--sample-limit must be non-negative")

    password = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_password(Path(args.passwords))
    if not password:
        raise SystemExit("Missing brain password.")

    sql = _sql(args.retention_days, args.sample_limit)
    remote_sql = f"/tmp/pokrov_inactive_audit_{os.getpid()}.sql"
    ssh = paramiko.SSHClient()
    configure_ssh_host_key_policy(ssh)
    ssh.connect(
        args.brain_ip,
        port=int(args.ssh_port),
        username=args.ssh_user,
        password=password,
        timeout=30,
        banner_timeout=30,
        auth_timeout=30,
    )
    try:
        sftp = ssh.open_sftp()
        try:
            with sftp.file(remote_sql, "w") as handle:
                handle.write(sql)
        finally:
            sftp.close()

        cmd = (
            "runuser -u postgres -- psql "
            f"-d {shlex.quote(str(args.db_name))} "
            "-v ON_ERROR_STOP=1 -P pager=off -At "
            f"-f {shlex.quote(remote_sql)}"
        )
        code, out, err = _run(ssh, cmd, timeout=180)
        if code != 0:
            raise SystemExit((err or out).strip() or f"psql failed with exit={code}")

        raw = out.strip()
        if not raw:
            raise SystemExit((err or "psql returned no JSON output").strip())
        payload = json.loads(raw)
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    finally:
        _run(ssh, f"rm -f {shlex.quote(remote_sql)}", timeout=30)
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
