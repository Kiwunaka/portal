from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
import time
from pathlib import Path

import paramiko

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from ssh_host_keys import configure_ssh_host_key_policy
from node_access import connect_node


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"
BACKUP_ROOT = "/root/portal_bot/backups"
CONFIRM_PHRASE = "RETIRE_FREE_TIER"


def _parse_password(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = [line.strip() for line in raw.splitlines()]
    for index, line in enumerate(lines):
        if "BRAINnode" not in line:
            continue
        for value in lines[index + 1 : index + 30]:
            if value and not value.startswith("ssh-ed25519 "):
                return value
    return ""


def _run(ssh: paramiko.SSHClient, command: str, *, timeout: int = 120) -> tuple[int, str, str]:
    _stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    return (
        code,
        stdout.read().decode(errors="replace"),
        stderr.read().decode(errors="replace"),
    )


def _target_ctes() -> str:
    return """
free_nodes AS MATERIALIZED (
    SELECT id, code
    FROM nodes
    WHERE lower(coalesce(access_role, '')) IN ('free_standard', 'free_soft')
       OR lower(coalesce(code, '')) LIKE '%free%'
),
bounded_trials AS MATERIALIZED (
    SELECT tg_id
    FROM users
    WHERE upper(coalesce(sub_type, '')) = 'FREE'
      AND lower(coalesce(current_plan_code, '')) = 'trial'
      AND coalesce(is_active, false) = true
      AND expiry_at > now()
      AND expiry_at <= now() + interval '7 days 5 minutes'
),
target_users AS MATERIALIZED (
    SELECT tg_id
    FROM users
    WHERE upper(coalesce(sub_type, '')) = 'FREE'
      AND tg_id NOT IN (SELECT tg_id FROM bounded_trials)
)
""".strip()


def _plan_sql() -> str:
    return f"""
WITH {_target_ctes()}
SELECT jsonb_build_object(
    'generated_at_utc', to_char(now() AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
    'free_nodes_total', (SELECT count(*) FROM free_nodes),
    'enabled_free_nodes', (
        SELECT count(*) FROM nodes WHERE id IN (SELECT id FROM free_nodes) AND coalesce(enabled, false) = true
    ),
    'target_users_total', (SELECT count(*) FROM target_users),
    'bounded_trials_excluded', (SELECT count(*) FROM bounded_trials),
    'free_node_mappings_total', (
        SELECT count(*) FROM user_nodes WHERE node_id IN (SELECT id FROM free_nodes)
    ),
    'active_free_keys_total', (
        SELECT count(*)
        FROM access_keys
        WHERE state = 'active'
          AND (
              tg_id IN (SELECT tg_id FROM target_users)
              OR lower(coalesce(pool_code, '')) = 'free_pool'
              OR lower(coalesce(node_code, '')) IN (SELECT lower(code) FROM free_nodes)
          )
    ),
    'queued_free_jobs_total', (
        SELECT count(*)
        FROM node_provisioning_jobs
        WHERE job_type IN ('free_to_soft', 'free_to_standard')
          AND status IN ('queued', 'running')
    ),
    'enabled_free_pool_memberships', (
        SELECT count(*)
        FROM node_pool_membership
        WHERE lower(coalesce(pool_code, '')) = 'free_pool'
          AND coalesce(is_enabled, false) = true
    )
)::text;
""".strip()


def _apply_sql() -> str:
    return f"""
BEGIN;
WITH {_target_ctes()},
retired_users AS (
    UPDATE users
    SET current_plan_code = 'free_retired',
        expiry_at = least(coalesce(expiry_at, now()), now()),
        is_active = true,
        free_cycle_next_reset_at = NULL,
        free_profile_state = 'retired',
        free_profile_source = 'owner_retired_free_tier',
        free_profile_state_changed_at = now(),
        free_profile_job_id = NULL,
        free_profile_error_code = NULL
    WHERE tg_id IN (SELECT tg_id FROM target_users)
    RETURNING 1
),
revoked_keys AS (
    UPDATE access_keys
    SET state = 'revoked',
        revoked_at = coalesce(revoked_at, now()),
        updated_at = now()
    WHERE state = 'active'
      AND (
          tg_id IN (SELECT tg_id FROM target_users)
          OR lower(coalesce(pool_code, '')) = 'free_pool'
          OR lower(coalesce(node_code, '')) IN (SELECT lower(code) FROM free_nodes)
      )
    RETURNING 1
),
removed_mappings AS (
    DELETE FROM user_nodes
    WHERE node_id IN (SELECT id FROM free_nodes)
    RETURNING 1
),
disabled_memberships AS (
    UPDATE node_pool_membership
    SET is_enabled = false,
        updated_at = now(),
        source = 'owner_retired_free_tier'
    WHERE lower(coalesce(pool_code, '')) = 'free_pool'
       OR lower(coalesce(node_code, '')) IN (SELECT lower(code) FROM free_nodes)
    RETURNING 1
),
disabled_nodes AS (
    UPDATE nodes
    SET enabled = false,
        accepting_new_clients = false,
        is_draining = true
    WHERE id IN (SELECT id FROM free_nodes)
    RETURNING 1
),
cancelled_jobs AS (
    UPDATE node_provisioning_jobs
    SET status = 'cancelled',
        completed_at = now(),
        updated_at = now(),
        next_run_at = NULL,
        locked_at = NULL,
        lock_token = NULL,
        last_error_code = 'free_tier_disabled',
        result_json = '{{"code":"free_tier_disabled","outcome":"cancelled"}}'
    WHERE job_type IN ('free_to_soft', 'free_to_standard')
      AND status IN ('queued', 'running')
    RETURNING 1
)
SELECT jsonb_build_object(
    'retired_users', (SELECT count(*) FROM retired_users),
    'revoked_keys', (SELECT count(*) FROM revoked_keys),
    'removed_mappings', (SELECT count(*) FROM removed_mappings),
    'disabled_memberships', (SELECT count(*) FROM disabled_memberships),
    'disabled_nodes', (SELECT count(*) FROM disabled_nodes),
    'cancelled_jobs', (SELECT count(*) FROM cancelled_jobs)
)::text;
COMMIT;
""".strip()


def _postcheck_sql() -> str:
    return f"""
WITH {_target_ctes()}
SELECT jsonb_build_object(
    'enabled_free_nodes', (
        SELECT count(*) FROM nodes WHERE id IN (SELECT id FROM free_nodes) AND coalesce(enabled, false) = true
    ),
    'accepting_free_nodes', (
        SELECT count(*) FROM nodes WHERE id IN (SELECT id FROM free_nodes) AND coalesce(accepting_new_clients, false) = true
    ),
    'active_target_users', (
        SELECT count(*)
        FROM users
        WHERE tg_id IN (SELECT tg_id FROM target_users)
          AND expiry_at > now()
    ),
    'free_node_mappings', (
        SELECT count(*) FROM user_nodes WHERE node_id IN (SELECT id FROM free_nodes)
    ),
    'active_free_keys', (
        SELECT count(*)
        FROM access_keys
        WHERE state = 'active'
          AND (
              tg_id IN (SELECT tg_id FROM target_users)
              OR lower(coalesce(pool_code, '')) = 'free_pool'
              OR lower(coalesce(node_code, '')) IN (SELECT lower(code) FROM free_nodes)
          )
    ),
    'queued_free_jobs', (
        SELECT count(*)
        FROM node_provisioning_jobs
        WHERE job_type IN ('free_to_soft', 'free_to_standard')
          AND status IN ('queued', 'running')
    ),
    'enabled_free_pool_memberships', (
        SELECT count(*)
        FROM node_pool_membership
        WHERE lower(coalesce(pool_code, '')) = 'free_pool'
          AND coalesce(is_enabled, false) = true
    )
)::text;
""".strip()


def _node_targets_sql() -> str:
    return f"""
WITH {_target_ctes()}
SELECT jsonb_build_object(
    'targets', coalesce((
        SELECT jsonb_agg(jsonb_build_object('code', code, 'host', host) ORDER BY code)
        FROM nodes
        WHERE id IN (SELECT id FROM free_nodes)
    ), '[]'::jsonb)
)::text;
""".strip()


def _psql_json(
    ssh: paramiko.SSHClient,
    *,
    db_name: str,
    sql: str,
    label: str,
    timeout: int = 180,
) -> dict:
    remote_sql = f"/tmp/pokrov_{label}_{os.getpid()}.sql"
    sftp = ssh.open_sftp()
    try:
        with sftp.file(remote_sql, "w") as handle:
            handle.write(sql)
    finally:
        sftp.close()
    try:
        command = (
            "runuser -u postgres -- psql "
            f"-d {shlex.quote(str(db_name))} "
            "-v ON_ERROR_STOP=1 -P pager=off -At "
            f"-f {shlex.quote(remote_sql)}"
        )
        code, out, err = _run(ssh, command, timeout=timeout)
        if code != 0:
            raise RuntimeError((err or out).strip() or f"{label} failed with exit={code}")
        lines = [line for line in out.splitlines() if line.strip() and line.strip() not in {"BEGIN", "COMMIT"}]
        if not lines:
            raise RuntimeError(f"{label} returned no JSON")
        return json.loads(lines[-1])
    finally:
        _run(ssh, f"rm -f {shlex.quote(remote_sql)}", timeout=30)


def _backup_postgres(ssh: paramiko.SSHClient, *, db_name: str) -> str:
    stamp = time.strftime("%Y%m%d_%H%M%S")
    backup_path = f"{BACKUP_ROOT}/portal_pre_free_tier_retirement_{stamp}.dump"
    command = (
        f"mkdir -p {shlex.quote(BACKUP_ROOT)} && "
        f"runuser -u postgres -- pg_dump -Fc -d {shlex.quote(str(db_name))} > {shlex.quote(backup_path)} && "
        f"test -s {shlex.quote(backup_path)}"
    )
    code, out, err = _run(ssh, command, timeout=600)
    if code != 0:
        raise RuntimeError((err or out).strip() or "pg_dump backup failed")
    return backup_path


def _panel_cleanup_script() -> str:
    return r'''
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
from models import Node
from nodes_repo import NodeRuntime
from panel_client import PanelClient


def runtime_from_node(node: Node) -> NodeRuntime:
    return NodeRuntime(
        id=node.id,
        code=node.code,
        name=node.name,
        host=node.host,
        vless_port=int(node.vless_port or 443),
        reality_sni=node.reality_sni or "",
        reality_pbk=node.reality_pbk or "",
        reality_sid=node.reality_sid or "",
        fingerprint=node.fingerprint or "firefox",
        flow=node.flow or "xtls-rprx-vision",
        panel_base_url=node.panel_base_url or "",
        panel_path=node.panel_path or "",
        panel_user=node.panel_user or "",
        panel_pass=node.panel_pass or "",
        inbound_id=int(node.inbound_id or 0),
        accepting_new_clients=bool(getattr(node, "accepting_new_clients", True)),
        is_draining=bool(getattr(node, "is_draining", False)),
        weight=int(getattr(node, "weight", 0) or 0),
        health_score=float(getattr(node, "health_score", 0.0) or 0.0),
        last_health_at=getattr(node, "last_health_at", None),
        is_healthy=bool(getattr(node, "is_healthy", True)),
        panel_latency_ms=getattr(node, "panel_latency_ms", None),
        panel_error_rate=float(getattr(node, "panel_error_rate", 0.0) or 0.0),
        active_clients=int(getattr(node, "active_clients", 0) or 0),
        cpu_percent=float(getattr(node, "cpu_percent", 0.0) or 0.0),
        last_ok_at=getattr(node, "last_ok_at", None),
        last_probe_at=getattr(node, "last_probe_at", None),
        transport_profiles_json=getattr(node, "transport_profiles_json", None),
    )


async def panel_clients(client: PanelClient) -> list[tuple[str, str]]:
    rows: set[tuple[str, str]] = set()
    inbounds = await client._get_inbounds()
    for inbound in client._selected_inbounds(inbounds, include_disabled=True):
        settings = client._decode_settings(inbound.get("settings", "{}"))
        for raw in settings.get("clients", []) or []:
            item = dict(raw or {})
            identity = (str(item.get("id") or "").strip(), str(item.get("email") or "").strip())
            if identity != ("", ""):
                rows.add(identity)
    return sorted(rows)


async def main() -> None:
    session = SessionLocal()
    try:
        nodes = (
            session.query(Node)
            .filter(
                (Node.access_role.in_(["free_standard", "free_soft"]))
                | (Node.code.ilike("%free%"))
            )
            .order_by(Node.code.asc())
            .all()
        )
        runtimes = [runtime_from_node(node) for node in nodes]
    finally:
        session.close()

    reachable = 0
    clients_before = 0
    delete_confirmed = 0
    clients_after = 0
    for runtime in runtimes:
        client = PanelClient(runtime)
        try:
            if not await client.login():
                continue
            reachable += 1
            before = await panel_clients(client)
            clients_before += len(before)
            for client_uuid, email in before:
                removed = await client.delete_client_uuid(client_uuid) if client_uuid else False
                if not removed and email:
                    removed = await client.delete_client_email(email)
                if removed:
                    delete_confirmed += 1
            clients_after += len(await panel_clients(client))
        finally:
            await client.close()

    print(json.dumps({
        "free_nodes": len(runtimes),
        "reachable_nodes": reachable,
        "clients_before": clients_before,
        "delete_confirmed": delete_confirmed,
        "clients_after": clients_after,
    }, separators=(",", ":")))


asyncio.run(main())
'''.strip()


def _run_panel_cleanup(ssh: paramiko.SSHClient) -> dict:
    remote_py = f"/tmp/pokrov_retire_free_panel_{os.getpid()}.py"
    sftp = ssh.open_sftp()
    try:
        with sftp.file(remote_py, "w") as handle:
            handle.write(_panel_cleanup_script())
    finally:
        sftp.close()
    try:
        command = f"cd /root/portal_bot && /root/portal_bot/venv/bin/python {shlex.quote(remote_py)}"
        code, out, err = _run(ssh, command, timeout=900)
        if code != 0:
            raise RuntimeError((err or out).strip() or "panel cleanup failed")
        lines = [line for line in out.splitlines() if line.strip()]
        if not lines:
            raise RuntimeError("panel cleanup returned no JSON")
        return json.loads(lines[-1])
    finally:
        _run(ssh, f"rm -f {shlex.quote(remote_py)}", timeout=30)


def _stop_free_delivery_via_ssh(*, targets: list[dict], passwords_path: Path) -> dict:
    connected = 0
    stopped = 0
    active_after = 0
    for raw in targets:
        code = str((raw or {}).get("code") or "").strip()
        host = str((raw or {}).get("host") or "").strip()
        if not code or not host:
            continue
        node_ssh, _auth_method = connect_node(
            code=code,
            host=host,
            user="root",
            port=29374,
            passwords_path=passwords_path,
        )
        try:
            connected += 1
            command = (
                "systemctl disable --now x-ui >/dev/null 2>&1 || true; "
                "systemctl disable --now xray >/dev/null 2>&1 || true; "
                "xui_state=$(systemctl is-active x-ui 2>/dev/null || true); "
                "xray_state=$(systemctl is-active xray 2>/dev/null || true); "
                "xray_processes=$(pgrep -x xray 2>/dev/null | wc -l); "
                "printf '%s|%s|%s\\n' \"$xui_state\" \"$xray_state\" \"$xray_processes\""
            )
            status, out, err = _run(node_ssh, command, timeout=120)
            if status != 0:
                raise RuntimeError((err or out).strip() or "free-node delivery stop failed")
            parts = (out.strip().splitlines()[-1] if out.strip() else "||1").split("|")
            xui_active = len(parts) > 0 and parts[0].strip() == "active"
            xray_active = len(parts) > 1 and parts[1].strip() == "active"
            try:
                xray_processes = int(parts[2]) if len(parts) > 2 else 1
            except ValueError:
                xray_processes = 1
            if xui_active or xray_active or xray_processes > 0:
                active_after += 1
            else:
                stopped += 1
        finally:
            node_ssh.close()
    return {
        "free_nodes": len(targets),
        "reachable_nodes": connected,
        "delivery_stopped_nodes": stopped,
        "active_delivery_nodes": active_after,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Retire the production consumer free tier without deleting accounts or the server."
    )
    parser.add_argument("--brain-ip", required=True)
    parser.add_argument("--ssh-user", default="root")
    parser.add_argument("--ssh-port", type=int, default=29374)
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--db-name", default="portal")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm", default="")
    parser.add_argument(
        "--allow-ssh-delivery-stop",
        action="store_true",
        help="If the free panel is unreachable, disable only x-ui/xray on the dedicated free node over SSH.",
    )
    parser.add_argument(
        "--force-db-retire-with-unreachable-node",
        action="store_true",
        help="Retire database access even when the external free-node dataplane cannot be reached; reports BLOCKED_BY_ACCESS.",
    )
    args = parser.parse_args()

    if args.apply and args.confirm != CONFIRM_PHRASE:
        raise SystemExit(f"Apply requires --confirm {CONFIRM_PHRASE}")

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
        plan = _psql_json(ssh, db_name=args.db_name, sql=_plan_sql(), label="free_tier_plan")
        print(json.dumps({"mode": "apply" if args.apply else "plan", "plan": plan}, ensure_ascii=False))
        if not args.apply:
            return 0

        backup_path = _backup_postgres(ssh, db_name=args.db_name)
        print(json.dumps({"backup": backup_path}, ensure_ascii=False))
        panel = _run_panel_cleanup(ssh)
        print(json.dumps({"panel": panel}, ensure_ascii=False))
        panel_complete = (
            int(panel.get("reachable_nodes", 0)) == int(panel.get("free_nodes", 0))
            and int(panel.get("clients_after", 0)) == 0
        )
        if not panel_complete:
            if not args.allow_ssh_delivery_stop and not args.force_db_retire_with_unreachable_node:
                raise RuntimeError("free-node panel cleanup was incomplete; database retirement was not applied")
            if args.allow_ssh_delivery_stop:
                target_payload = _psql_json(
                    ssh,
                    db_name=args.db_name,
                    sql=_node_targets_sql(),
                    label="free_tier_node_targets",
                )
                targets = [dict(item or {}) for item in target_payload.get("targets", [])]
                fallback = _stop_free_delivery_via_ssh(
                    targets=targets,
                    passwords_path=Path(args.passwords),
                )
                print(json.dumps({"ssh_delivery_stop": fallback}, ensure_ascii=False))
                fallback_complete = (
                    int(fallback.get("reachable_nodes", 0)) == int(fallback.get("free_nodes", 0))
                    and int(fallback.get("delivery_stopped_nodes", 0)) == int(fallback.get("free_nodes", 0))
                    and int(fallback.get("active_delivery_nodes", 0)) == 0
                )
                if not fallback_complete and not args.force_db_retire_with_unreachable_node:
                    raise RuntimeError("free-node delivery is still active; database retirement was not applied")
                if not fallback_complete:
                    print(json.dumps({"external_delivery_shutdown": "BLOCKED_BY_ACCESS"}))
            else:
                print(json.dumps({"external_delivery_shutdown": "BLOCKED_BY_ACCESS"}))

        applied = _psql_json(ssh, db_name=args.db_name, sql=_apply_sql(), label="free_tier_apply")
        postcheck = _psql_json(ssh, db_name=args.db_name, sql=_postcheck_sql(), label="free_tier_postcheck")
        print(json.dumps({"applied": applied, "postcheck": postcheck}, ensure_ascii=False))
        if any(int(value or 0) != 0 for value in postcheck.values()):
            raise RuntimeError("free-tier retirement postcheck failed")
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
