from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import time
from pathlib import Path

import paramiko
from ssh_host_keys import configure_ssh_host_key_policy


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"
INACTIVE_BACKUP_ROOT = "/root/portal_bot/backups"
DEFAULT_BACKUP_RETENTION_COUNT = 2
CONFIRM_PHRASE = "PURGE_INACTIVE_14D"


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


def _candidate_sql(retention_days: int, sample_limit: int) -> str:
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
paid_attempt_users AS MATERIALIZED (
    SELECT DISTINCT pa.tg_id
    FROM pay_attempts pa
    JOIN candidates c ON c.tg_id = pa.tg_id
    WHERE pa.status IN ('paid', 'succeeded', 'success', 'completed')
),
paid_order_users AS MATERIALIZED (
    SELECT DISTINCT eo.tg_id
    FROM external_orders eo
    JOIN candidates c ON c.tg_id = eo.tg_id
    WHERE eo.status IN ('paid', 'succeeded', 'success', 'completed', 'fulfilled')
),
support_users AS MATERIALIZED (
    SELECT DISTINCT st.user_tg_id AS tg_id
    FROM support_tickets st
    JOIN candidates c ON c.tg_id = st.user_tg_id
)
SELECT jsonb_build_object(
    'generated_at_utc', to_char(now() AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
    'retention_days', {days},
    'cutoff_at_utc', to_char((now() - make_interval(days => {days})) AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
    'candidates_total', (SELECT count(*) FROM candidates),
    'candidate_ids', coalesce((SELECT jsonb_agg(tg_id ORDER BY tg_id) FROM candidates), '[]'::jsonb),
    'risk_flags', jsonb_build_object(
        'stars_paid_positive_users', (SELECT count(*) FROM candidates WHERE coalesce(stars_paid, 0) > 0),
        'first_purchase_done_users', (SELECT count(*) FROM candidates WHERE coalesce(first_purchase_done, false) = true),
        'paid_pay_attempt_users', (SELECT count(*) FROM paid_attempt_users),
        'paid_external_order_users', (SELECT count(*) FROM paid_order_users),
        'support_ticket_users', (SELECT count(*) FROM support_users)
    ),
    'candidate_samples', coalesce((
        SELECT jsonb_agg(to_jsonb(x) ORDER BY x.last_activity_at_utc)
        FROM (
            SELECT
                tg_id,
                username,
                origin,
                effective_status,
                sub_type,
                current_plan_code,
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
    ), '[]'::jsonb)
)::text;
""".strip()


def _purge_sql(tg_ids: list[int]) -> str:
    if not tg_ids:
        return "SELECT '{}'::jsonb::text;"
    values = ", ".join(f"({int(tg_id)})" for tg_id in sorted(set(tg_ids)))
    return f"""
BEGIN;
WITH ids(tg_id) AS (VALUES {values}),
identity_ids AS (
    SELECT id FROM web_email_identities WHERE linked_tg_id IN (SELECT tg_id FROM ids)
),
ticket_ids AS (
    SELECT id FROM support_tickets WHERE user_tg_id IN (SELECT tg_id FROM ids)
),
order_keys AS (
    SELECT provider, order_id
    FROM external_orders
    WHERE tg_id IN (SELECT tg_id FROM ids)
),
del_support_messages AS (
    DELETE FROM support_ticket_messages
    WHERE ticket_id IN (SELECT id FROM ticket_ids)
       OR sender_tg_id IN (SELECT tg_id FROM ids)
    RETURNING 1
),
del_support_tickets AS (
    DELETE FROM support_tickets
    WHERE id IN (SELECT id FROM ticket_ids)
    RETURNING 1
),
del_web_email_tokens AS (
    DELETE FROM web_email_tokens
    WHERE identity_id IN (SELECT id FROM identity_ids)
    RETURNING 1
),
del_web_email_identities AS (
    DELETE FROM web_email_identities
    WHERE id IN (SELECT id FROM identity_ids)
    RETURNING 1
),
del_web_cabinet_handoff_tokens AS (
    DELETE FROM web_cabinet_handoff_tokens WHERE tg_id IN (SELECT tg_id FROM ids) RETURNING 1
),
del_achievements AS (
    DELETE FROM achievements WHERE tg_id IN (SELECT tg_id FROM ids) RETURNING 1
),
del_reviews AS (
    DELETE FROM reviews WHERE tg_id IN (SELECT tg_id FROM ids) RETURNING 1
),
del_feedback_entries AS (
    DELETE FROM feedback_entries WHERE tg_id IN (SELECT tg_id FROM ids) RETURNING 1
),
del_promo_usage AS (
    DELETE FROM promo_usage WHERE tg_id IN (SELECT tg_id FROM ids) RETURNING 1
),
del_key_action_history AS (
    DELETE FROM key_action_history
    WHERE tg_id IN (SELECT tg_id FROM ids)
       OR actor_tg_id IN (SELECT tg_id FROM ids)
    RETURNING 1
),
del_user_key_policy AS (
    DELETE FROM user_key_policy
    WHERE tg_id IN (SELECT tg_id FROM ids)
       OR updated_by IN (SELECT tg_id FROM ids)
    RETURNING 1
),
del_referral_bonus_queue AS (
    DELETE FROM referral_bonus_queue
    WHERE referrer_tg_id IN (SELECT tg_id FROM ids)
       OR referred_tg_id IN (SELECT tg_id FROM ids)
    RETURNING 1
),
del_reward_claims AS (
    DELETE FROM reward_claims WHERE tg_id IN (SELECT tg_id FROM ids) RETURNING 1
),
del_events AS (
    DELETE FROM events WHERE tg_id IN (SELECT tg_id FROM ids) RETURNING 1
),
del_warp_events AS (
    DELETE FROM warp_events WHERE tg_id IN (SELECT tg_id FROM ids) RETURNING 1
),
del_warp_materials AS (
    DELETE FROM warp_materials WHERE tg_id IN (SELECT tg_id FROM ids) RETURNING 1
),
del_funnel_events AS (
    DELETE FROM funnel_events WHERE tg_id IN (SELECT tg_id FROM ids) RETURNING 1
),
del_observer_daily AS (
    DELETE FROM observer_daily_observations WHERE tg_id IN (SELECT tg_id FROM ids) RETURNING 1
),
del_observer_window AS (
    DELETE FROM observer_window_observations WHERE tg_id IN (SELECT tg_id FROM ids) RETURNING 1
),
del_observer_state AS (
    DELETE FROM observer_user_state WHERE tg_id IN (SELECT tg_id FROM ids) RETURNING 1
),
del_offers AS (
    DELETE FROM offers WHERE tg_id IN (SELECT tg_id FROM ids) RETURNING 1
),
del_external_payment_events AS (
    DELETE FROM external_payment_events epe
    WHERE EXISTS (
        SELECT 1
        FROM order_keys ok
        WHERE ok.provider = epe.provider
          AND ok.order_id = epe.order_id
    )
    RETURNING 1
),
del_external_orders AS (
    DELETE FROM external_orders WHERE tg_id IN (SELECT tg_id FROM ids) RETURNING 1
),
del_pay_attempts AS (
    DELETE FROM pay_attempts WHERE tg_id IN (SELECT tg_id FROM ids) RETURNING 1
),
del_points_ledger AS (
    DELETE FROM points_ledger
    WHERE tg_id IN (SELECT tg_id FROM ids)
       OR ref_tg_id IN (SELECT tg_id FROM ids)
    RETURNING 1
),
del_campaign_sends AS (
    DELETE FROM campaign_sends WHERE tg_id IN (SELECT tg_id FROM ids) RETURNING 1
),
del_family_slots AS (
    DELETE FROM family_slots WHERE tg_id IN (SELECT tg_id FROM ids) RETURNING 1
),
del_gift_cards AS (
    DELETE FROM gift_cards
    WHERE created_by IN (SELECT tg_id FROM ids)
       OR redeemed_by IN (SELECT tg_id FROM ids)
    RETURNING 1
),
del_admin_audit AS (
    DELETE FROM admin_audit
    WHERE actor_tg_id IN (SELECT tg_id FROM ids)
       OR target_tg_id IN (SELECT tg_id FROM ids)
    RETURNING 1
),
del_incentive_campaigns AS (
    DELETE FROM incentive_campaigns WHERE created_by IN (SELECT tg_id FROM ids) RETURNING 1
),
del_access_keys AS (
    DELETE FROM access_keys WHERE tg_id IN (SELECT tg_id FROM ids) RETURNING 1
),
del_user_nodes AS (
    DELETE FROM user_nodes WHERE tg_id IN (SELECT tg_id FROM ids) RETURNING 1
),
del_users AS (
    DELETE FROM users WHERE tg_id IN (SELECT tg_id FROM ids) RETURNING 1
)
SELECT jsonb_build_object(
    'support_ticket_messages', (SELECT count(*) FROM del_support_messages),
    'support_tickets', (SELECT count(*) FROM del_support_tickets),
    'web_email_tokens', (SELECT count(*) FROM del_web_email_tokens),
    'web_email_identities', (SELECT count(*) FROM del_web_email_identities),
    'web_cabinet_handoff_tokens', (SELECT count(*) FROM del_web_cabinet_handoff_tokens),
    'achievements', (SELECT count(*) FROM del_achievements),
    'reviews', (SELECT count(*) FROM del_reviews),
    'feedback_entries', (SELECT count(*) FROM del_feedback_entries),
    'promo_usage', (SELECT count(*) FROM del_promo_usage),
    'key_action_history', (SELECT count(*) FROM del_key_action_history),
    'user_key_policy', (SELECT count(*) FROM del_user_key_policy),
    'referral_bonus_queue', (SELECT count(*) FROM del_referral_bonus_queue),
    'reward_claims', (SELECT count(*) FROM del_reward_claims),
    'events', (SELECT count(*) FROM del_events),
    'warp_events', (SELECT count(*) FROM del_warp_events),
    'warp_materials', (SELECT count(*) FROM del_warp_materials),
    'funnel_events', (SELECT count(*) FROM del_funnel_events),
    'observer_daily_observations', (SELECT count(*) FROM del_observer_daily),
    'observer_window_observations', (SELECT count(*) FROM del_observer_window),
    'observer_user_state', (SELECT count(*) FROM del_observer_state),
    'offers', (SELECT count(*) FROM del_offers),
    'external_payment_events', (SELECT count(*) FROM del_external_payment_events),
    'external_orders', (SELECT count(*) FROM del_external_orders),
    'pay_attempts', (SELECT count(*) FROM del_pay_attempts),
    'points_ledger', (SELECT count(*) FROM del_points_ledger),
    'campaign_sends', (SELECT count(*) FROM del_campaign_sends),
    'family_slots', (SELECT count(*) FROM del_family_slots),
    'gift_cards', (SELECT count(*) FROM del_gift_cards),
    'admin_audit', (SELECT count(*) FROM del_admin_audit),
    'incentive_campaigns', (SELECT count(*) FROM del_incentive_campaigns),
    'access_keys', (SELECT count(*) FROM del_access_keys),
    'user_nodes', (SELECT count(*) FROM del_user_nodes),
    'users', (SELECT count(*) FROM del_users)
)::text;
COMMIT;
""".strip()


def _panel_cleanup_script(tg_ids: list[int]) -> str:
    ids_json = json.dumps(sorted(set(int(x) for x in tg_ids)))
    return f"""
from __future__ import annotations

import asyncio
import json
import os
import sys

sys.path.insert(0, "/root/portal_bot")


def load_env(path: str) -> None:
    try:
        lines = open(path, "r", encoding="utf-8", errors="replace").read().splitlines()
    except FileNotFoundError:
        return
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_env("/root/portal_bot/.env")

from db import SessionLocal
from models import Node, UserNode
from nodes_repo import NodeRuntime
from panel_client import PanelClient


TG_IDS = set({ids_json})


def runtime_from_node(n: Node) -> NodeRuntime:
    return NodeRuntime(
        id=n.id,
        code=n.code,
        name=n.name,
        host=n.host,
        vless_port=int(n.vless_port or 443),
        reality_sni=n.reality_sni or "",
        reality_pbk=n.reality_pbk or "",
        reality_sid=n.reality_sid or "",
        fingerprint=n.fingerprint or "firefox",
        flow=n.flow or "xtls-rprx-vision",
        panel_base_url=n.panel_base_url or "",
        panel_path=n.panel_path or "",
        panel_user=n.panel_user or "",
        panel_pass=n.panel_pass or "",
        inbound_id=int(n.inbound_id or 0),
        accepting_new_clients=bool(getattr(n, "accepting_new_clients", True)),
        is_draining=bool(getattr(n, "is_draining", False)),
        weight=int(getattr(n, "weight", 0) or 0),
        health_score=float(getattr(n, "health_score", 0.0) or 0.0),
        last_health_at=getattr(n, "last_health_at", None),
        is_healthy=bool(getattr(n, "is_healthy", True)),
        panel_latency_ms=getattr(n, "panel_latency_ms", None),
        panel_error_rate=float(getattr(n, "panel_error_rate", 0.0) or 0.0),
        active_clients=int(getattr(n, "active_clients", 0) or 0),
        cpu_percent=float(getattr(n, "cpu_percent", 0.0) or 0.0),
        last_ok_at=getattr(n, "last_ok_at", None),
        last_probe_at=getattr(n, "last_probe_at", None),
        transport_profiles_json=getattr(n, "transport_profiles_json", None),
    )


async def main() -> None:
    session = SessionLocal()
    try:
        mappings = (
            session.query(UserNode)
            .filter(UserNode.tg_id.in_(TG_IDS))
            .order_by(UserNode.tg_id.asc(), UserNode.node_id.asc())
            .all()
        )
        node_ids = sorted({{int(m.node_id) for m in mappings if m.node_id is not None}})
        nodes = session.query(Node).filter(Node.id.in_(node_ids)).all() if node_ids else []
        node_by_id = {{int(n.id): runtime_from_node(n) for n in nodes if n.id is not None}}
    finally:
        session.close()

    clients: dict[int, PanelClient] = {{}}
    results = []
    try:
        for mapping in mappings:
            runtime = node_by_id.get(int(mapping.node_id or 0))
            if runtime is None:
                results.append({{
                    "tg_id": int(mapping.tg_id),
                    "node_id": int(mapping.node_id or 0),
                    "ok": False,
                    "reason": "node_missing",
                }})
                continue
            client = clients.get(int(runtime.id or 0))
            if client is None:
                client = PanelClient(runtime)
                clients[int(runtime.id or 0)] = client
            uuid = str(mapping.client_uuid or "").strip()
            email = str(mapping.panel_email or "").strip()
            ok_uuid = await client.delete_client_uuid(uuid) if uuid else False
            ok_email = False if ok_uuid else (await client.delete_client_email(email) if email else False)
            results.append({{
                "tg_id": int(mapping.tg_id),
                "node_code": runtime.code,
                "uuid": uuid,
                "email": email,
                "ok": bool(ok_uuid or ok_email),
                "method": "uuid" if ok_uuid else ("email" if ok_email else "not_found_or_failed"),
            }})
    finally:
        for client in clients.values():
            await client.close()

    print(json.dumps({{
        "mappings": len(mappings),
        "ok": sum(1 for row in results if row.get("ok")),
        "failed_or_absent": sum(1 for row in results if not row.get("ok")),
        "results": results,
    }}, ensure_ascii=False))


asyncio.run(main())
""".strip()


def _psql_json(ssh: paramiko.SSHClient, *, db_name: str, sql: str, label: str, timeout: int = 180) -> dict:
    remote_sql = f"/tmp/pokrov_{label}_{os.getpid()}.sql"
    sftp = ssh.open_sftp()
    try:
        with sftp.file(remote_sql, "w") as handle:
            handle.write(sql)
    finally:
        sftp.close()
    try:
        cmd = (
            "runuser -u postgres -- psql "
            f"-d {shlex.quote(str(db_name))} "
            "-v ON_ERROR_STOP=1 -P pager=off -At "
            f"-f {shlex.quote(remote_sql)}"
        )
        code, out, err = _run(ssh, cmd, timeout=timeout)
        if code != 0:
            raise RuntimeError((err or out).strip() or f"{label} psql failed with exit={code}")
        lines = [line for line in out.splitlines() if line.strip() and not line.startswith(("BEGIN", "COMMIT"))]
        if not lines:
            raise RuntimeError((err or f"{label} returned no JSON").strip())
        return json.loads(lines[-1])
    finally:
        _run(ssh, f"rm -f {shlex.quote(remote_sql)}", timeout=30)


def _backup_postgres(ssh: paramiko.SSHClient, *, db_name: str) -> str:
    stamp = time.strftime("%Y%m%d_%H%M%S")
    backup_path = f"{INACTIVE_BACKUP_ROOT}/portal_pre_inactive_user_purge_{stamp}.dump"
    cmd = (
        "mkdir -p /root/portal_bot/backups && "
        f"runuser -u postgres -- pg_dump -Fc -d {shlex.quote(str(db_name))} > {shlex.quote(backup_path)} && "
        f"test -s {shlex.quote(backup_path)} && "
        f"ls -lh {shlex.quote(backup_path)}"
    )
    code, out, err = _run(ssh, cmd, timeout=600)
    if code != 0:
        raise RuntimeError((err or out).strip() or "pg_dump backup failed")
    return backup_path


def _build_backup_retention_command(backup_path: str, *, retain_count: int = DEFAULT_BACKUP_RETENTION_COUNT) -> str:
    keep = int(retain_count)
    if not 1 <= keep <= 30:
        raise ValueError("retain_count must be between 1 and 30")
    expected = re.compile(
        rf"^{re.escape(INACTIVE_BACKUP_ROOT)}/portal_pre_inactive_user_purge_[0-9]{{8}}_[0-9]{{6}}\.dump$"
    )
    if not expected.fullmatch(str(backup_path or "")):
        raise ValueError("unsafe inactive-user backup path")
    root_q = shlex.quote(INACTIVE_BACKUP_ROOT)
    current_q = shlex.quote(backup_path)
    return "\n".join(
        [
            "set -e",
            f"root={root_q}",
            f"current={current_q}",
            f'test "$root" = {root_q}',
            'test -f "$current"',
            'find "$root" -mindepth 1 -maxdepth 1 -type f -printf \'%f\\n\' |',
            "  grep -E '^portal_pre_inactive_user_purge_[0-9]{8}_[0-9]{6}\\.dump$' |",
            "  LC_ALL=C sort |",
            f"  head -n -{keep} |",
            "  while IFS= read -r name; do",
            '    test -n "$name" || continue',
            '    candidate="$root/$name"',
            '    test "$candidate" = "$current" && continue',
            '    rm -f -- "$candidate"',
            "  done",
        ]
    )


def _prune_postgres_backups(ssh: paramiko.SSHClient, backup_path: str) -> str:
    code, _out, _err = _run(
        ssh,
        _build_backup_retention_command(backup_path),
        timeout=120,
    )
    return "PASS" if code == 0 else "FAILED"


def _run_panel_cleanup(ssh: paramiko.SSHClient, *, tg_ids: list[int]) -> dict:
    remote_py = f"/tmp/pokrov_panel_cleanup_{os.getpid()}.py"
    script = _panel_cleanup_script(tg_ids)
    sftp = ssh.open_sftp()
    try:
        with sftp.file(remote_py, "w") as handle:
            handle.write(script)
    finally:
        sftp.close()
    try:
        cmd = f"cd /root/portal_bot && /root/portal_bot/venv/bin/python {shlex.quote(remote_py)}"
        code, out, err = _run(ssh, cmd, timeout=900)
        if code != 0:
            raise RuntimeError((err or out).strip() or "panel cleanup failed")
        raw = out.strip().splitlines()[-1] if out.strip() else ""
        if not raw:
            raise RuntimeError((err or "panel cleanup returned no JSON").strip())
        return json.loads(raw)
    finally:
        _run(ssh, f"rm -f {shlex.quote(remote_py)}", timeout=30)


def main() -> int:
    parser = argparse.ArgumentParser(description="Purge inactive production users on brain after backup.")
    parser.add_argument("--brain-ip", required=True)
    parser.add_argument("--ssh-user", default="root")
    parser.add_argument("--ssh-port", type=int, default=29374)
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--db-name", default="portal")
    parser.add_argument("--retention-days", type=int, default=14)
    parser.add_argument("--sample-limit", type=int, default=30)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm", default="")
    parser.add_argument("--include-support-roots", action="store_true")
    parser.add_argument("--include-money-roots", action="store_true")
    args = parser.parse_args()

    if args.retention_days < 1:
        raise SystemExit("--retention-days must be positive")

    password = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_password(Path(args.passwords))
    if not password:
        raise SystemExit("Missing brain password.")

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
        candidates = _psql_json(
            ssh,
            db_name=args.db_name,
            sql=_candidate_sql(args.retention_days, args.sample_limit),
            label="inactive_candidates",
            timeout=180,
        )
        tg_ids = [int(x) for x in candidates.get("candidate_ids", [])]
        flags = candidates.get("risk_flags") or {}
        money_risk = any(
            int(flags.get(key, 0) or 0) > 0
            for key in (
                "stars_paid_positive_users",
                "first_purchase_done_users",
                "paid_pay_attempt_users",
                "paid_external_order_users",
            )
        )
        support_risk = int(flags.get("support_ticket_users", 0) or 0) > 0

        if not args.apply:
            print(json.dumps({"mode": "dry_run", "candidates": candidates}, ensure_ascii=False, indent=2, sort_keys=True))
            return 0

        if args.confirm != CONFIRM_PHRASE:
            raise SystemExit(f"Refusing apply without --confirm {CONFIRM_PHRASE}")
        if money_risk and not args.include_money_roots:
            raise SystemExit("Refusing apply: candidate set has payment/revenue flags; pass --include-money-roots if intentional.")
        if support_risk and not args.include_support_roots:
            raise SystemExit("Refusing apply: candidate set has support tickets; pass --include-support-roots if intentional.")
        if not tg_ids:
            print(json.dumps({"mode": "apply", "candidates": candidates, "result": "nothing_to_purge"}, ensure_ascii=False, indent=2))
            return 0

        backup_path = _backup_postgres(ssh, db_name=args.db_name)
        panel_result = _run_panel_cleanup(ssh, tg_ids=tg_ids)
        purge_result = _psql_json(
            ssh,
            db_name=args.db_name,
            sql=_purge_sql(tg_ids),
            label="inactive_purge",
            timeout=300,
        )
        backup_retention_status = _prune_postgres_backups(ssh, backup_path)
        print(
            json.dumps(
                {
                    "mode": "apply",
                    "backup_path": backup_path,
                    "backup_retention_status": backup_retention_status,
                    "backup_retain_count": DEFAULT_BACKUP_RETENTION_COUNT,
                    "candidates": candidates,
                    "panel_cleanup": panel_result,
                    "db_purge": purge_result,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
