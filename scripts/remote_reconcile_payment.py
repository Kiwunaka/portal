from __future__ import annotations

import argparse
import json
import os
import re
import shlex
from datetime import datetime, timezone
from pathlib import Path

import paramiko


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"
PLAN_CODE_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def _sql_literal(value: object) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _parse_password(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = [ln.strip() for ln in raw.splitlines()]
    for i, ln in enumerate(lines):
        if "BRAINnode" not in ln:
            continue
        for j in range(i + 1, min(i + 30, len(lines))):
            v = lines[j].strip()
            if v and not v.startswith("ssh-ed25519 "):
                return v
    return ""


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 120) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return code, out, err


def main() -> int:
    ap = argparse.ArgumentParser(description="Reconcile a missing paid purchase in PostgreSQL.")
    ap.add_argument("--brain-ip", required=True)
    ap.add_argument("--tg-id", type=int, required=True)
    ap.add_argument("--amount-stars", type=int, required=True)
    ap.add_argument("--plan-code", default="3_months")
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument("--db-name", default="portal")
    args = ap.parse_args()

    pw = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_password(Path(args.passwords))
    if not pw:
        raise SystemExit("Missing brain password.")

    tg_id = int(args.tg_id)
    amount = int(args.amount_stars)
    plan = str(args.plan_code).strip()
    if not PLAN_CODE_RE.fullmatch(plan):
        raise SystemExit("Invalid --plan-code value.")
    paid_at = datetime.now(timezone.utc).replace(tzinfo=None).isoformat(sep=" ", timespec="seconds")
    meta = json.dumps(
        {
            "flow": "manual_reconcile",
            "tg_id": tg_id,
            "plan_code": plan,
            "amount_stars": amount,
        },
        ensure_ascii=False,
    )
    db_arg = shlex.quote(str(args.db_name))

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        args.brain_ip,
        port=args.ssh_port,
        username=args.ssh_user,
        password=pw,
        timeout=30,
        banner_timeout=30,
        auth_timeout=30,
    )
    try:
        sql = f"""
BEGIN;

SELECT setval(pg_get_serial_sequence('achievements','id'), COALESCE((SELECT MAX(id) FROM achievements), 1), true);
SELECT setval(pg_get_serial_sequence('admin_audit','id'), COALESCE((SELECT MAX(id) FROM admin_audit), 1), true);
SELECT setval(pg_get_serial_sequence('campaign_sends','id'), COALESCE((SELECT MAX(id) FROM campaign_sends), 1), true);
SELECT setval(pg_get_serial_sequence('events','id'), COALESCE((SELECT MAX(id) FROM events), 1), true);
SELECT setval(pg_get_serial_sequence('family_slots','id'), COALESCE((SELECT MAX(id) FROM family_slots), 1), true);
SELECT setval(pg_get_serial_sequence('gift_cards','id'), COALESCE((SELECT MAX(id) FROM gift_cards), 1), true);
SELECT setval(pg_get_serial_sequence('node_health_samples','id'), COALESCE((SELECT MAX(id) FROM node_health_samples), 1), true);
SELECT setval(pg_get_serial_sequence('nodes','id'), COALESCE((SELECT MAX(id) FROM nodes), 1), true);
SELECT setval(pg_get_serial_sequence('offers','id'), COALESCE((SELECT MAX(id) FROM offers), 1), true);
SELECT setval(pg_get_serial_sequence('pay_attempts','id'), COALESCE((SELECT MAX(id) FROM pay_attempts), 1), true);
SELECT setval(pg_get_serial_sequence('points_ledger','id'), COALESCE((SELECT MAX(id) FROM points_ledger), 1), true);
SELECT setval(pg_get_serial_sequence('promo_codes','id'), COALESCE((SELECT MAX(id) FROM promo_codes), 1), true);
SELECT setval(pg_get_serial_sequence('promo_usage','id'), COALESCE((SELECT MAX(id) FROM promo_usage), 1), true);
SELECT setval(pg_get_serial_sequence('reviews','id'), COALESCE((SELECT MAX(id) FROM reviews), 1), true);
SELECT setval(pg_get_serial_sequence('support_ticket_messages','id'), COALESCE((SELECT MAX(id) FROM support_ticket_messages), 1), true);
SELECT setval(pg_get_serial_sequence('support_tickets','id'), COALESCE((SELECT MAX(id) FROM support_tickets), 1), true);
SELECT setval(pg_get_serial_sequence('templates','id'), COALESCE((SELECT MAX(id) FROM templates), 1), true);
SELECT setval(pg_get_serial_sequence('user_nodes','id'), COALESCE((SELECT MAX(id) FROM user_nodes), 1), true);

CREATE TEMP TABLE _reconciled_attempts(amount_stars INTEGER);

WITH target AS (
  SELECT id
  FROM pay_attempts
  WHERE tg_id = {tg_id}
    AND amount_stars = {amount}
    AND plan_code = {_sql_literal(plan)}
  ORDER BY id DESC
  LIMIT 1
), upd AS (
  UPDATE pay_attempts
  SET status='paid',
      paid_at={_sql_literal(paid_at)},
      updated_at={_sql_literal(paid_at)}
  WHERE id IN (SELECT id FROM target)
    AND status <> 'paid'
  RETURNING amount_stars
)
INSERT INTO _reconciled_attempts(amount_stars)
SELECT amount_stars FROM upd;

UPDATE users
SET stars_paid = COALESCE(stars_paid, 0) + COALESCE((SELECT SUM(amount_stars) FROM _reconciled_attempts), 0),
    first_purchase_done = CASE WHEN EXISTS (SELECT 1 FROM _reconciled_attempts) THEN TRUE ELSE first_purchase_done END
WHERE tg_id = {tg_id};

INSERT INTO events (tg_id, event_name, source, session_id, meta_json, created_at)
SELECT {tg_id}, 'paid', 'reconcile', NULL, {_sql_literal(meta)}, {_sql_literal(paid_at)}
WHERE EXISTS (SELECT 1 FROM _reconciled_attempts);

COMMIT;
"""
        code, out, err = _run(
            ssh,
            f"runuser -u postgres -- psql -d {db_arg} -v ON_ERROR_STOP=1 -c \"{sql}\"",
            timeout=120,
        )
        if code != 0:
            raise SystemExit(err.strip() or out.strip() or "failed to reconcile")

        verify_sql = f"""
select tg_id, username, sub_type, is_active, expiry_at, stars_paid, first_purchase_done
from users
where tg_id={tg_id};

select id, plan_code, amount_stars, status, paid_at
from pay_attempts
where tg_id={tg_id}
order by id desc
limit 5;
"""
        _, vout, verr = _run(
            ssh,
            f"runuser -u postgres -- psql -d {db_arg} -P pager=off -c \"{verify_sql}\"",
            timeout=120,
        )
        print((vout.strip() or verr.strip()).strip())
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
