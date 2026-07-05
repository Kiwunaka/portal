from __future__ import annotations

import argparse
import os
import posixpath
import re
import secrets
import string
from pathlib import Path
from urllib.parse import quote_plus

import paramiko
from ssh_host_keys import configure_ssh_host_key_policy


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"
SQL_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


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


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 300) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return code, out, err


def _ensure_dir(sftp: paramiko.SFTPClient, remote_dir: str) -> None:
    parts: list[str] = []
    cur = remote_dir
    while cur not in {"", "/"}:
        parts.append(cur)
        cur = posixpath.dirname(cur)
    for d in reversed(parts):
        try:
            sftp.stat(d)
        except IOError:
            try:
                sftp.mkdir(d)
            except IOError:
                pass


def _put_file(sftp: paramiko.SFTPClient, local_path: Path, remote_path: str) -> None:
    _ensure_dir(sftp, posixpath.dirname(remote_path))
    sftp.put(str(local_path), remote_path)


def _random_password(length: int = 28) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(max(16, int(length))))


def _mask_url(url: str) -> str:
    if "@" not in url or "://" not in url:
        return url
    head, tail = url.split("://", 1)
    if "@" not in tail:
        return url
    auth, rest = tail.split("@", 1)
    if ":" in auth:
        user = auth.split(":", 1)[0]
        return f"{head}://{user}:***@{rest}"
    return f"{head}://***@{rest}"


def _sql_identifier(value: str, label: str) -> str:
    cleaned = str(value).strip()
    if not SQL_IDENTIFIER_RE.fullmatch(cleaned):
        raise SystemExit(f"Invalid {label}; expected a simple PostgreSQL identifier.")
    return cleaned


def _sql_literal(value: object) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _upsert_env(raw: str, updates: dict[str, str]) -> str:
    lines = raw.splitlines()
    idx: dict[str, int] = {}
    for i, ln in enumerate(lines):
        if "=" not in ln or ln.lstrip().startswith("#"):
            continue
        idx[ln.split("=", 1)[0].strip()] = i
    for k, v in updates.items():
        row = f"{k}={v}"
        if k in idx:
            lines[idx[k]] = row
        else:
            lines.append(row)
    return "\n".join(lines).rstrip("\n") + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Install PostgreSQL on brain and migrate data from SQLite.")
    ap.add_argument("--brain-ip", required=True)
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument("--db-name", default="portal")
    ap.add_argument("--db-user", default="portal_app")
    ap.add_argument("--db-password", default="")
    ap.add_argument("--sqlite-path", default="/root/portal_bot/portal.db")
    ap.add_argument("--venv-python", default="/root/portal_bot/venv/bin/python")
    args = ap.parse_args()

    pw = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_password(Path(args.passwords))
    if not pw:
        raise SystemExit("Missing brain password.")

    db_password = (args.db_password or "").strip() or _random_password()
    db_user = _sql_identifier(str(args.db_user), "--db-user")
    db_name = _sql_identifier(str(args.db_name), "--db-name")
    sqlite_url = f"sqlite:///{args.sqlite_path}"
    pg_url = f"postgresql+psycopg2://{quote_plus(db_user)}:{quote_plus(db_password)}@127.0.0.1:5432/{quote_plus(db_name)}"

    ssh = paramiko.SSHClient()
    configure_ssh_host_key_policy(ssh)
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
        print("Installing PostgreSQL packages...")
        for cmd in [
            "DEBIAN_FRONTEND=noninteractive apt-get update -y",
            "DEBIAN_FRONTEND=noninteractive apt-get install -y postgresql postgresql-contrib",
            "systemctl enable --now postgresql",
        ]:
            code, out, err = _run(ssh, cmd, timeout=1800)
            if code != 0:
                raise SystemExit(f"Remote command failed: {cmd}\n{err.strip() or out.strip()}")

        print("Provisioning PostgreSQL role/database...")
        code, out, err = _run(
            ssh,
            f"sudo -u postgres psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='{db_user}'\"",
            timeout=120,
        )
        if code != 0:
            raise SystemExit(f"Failed to query postgres roles:\n{err.strip() or out.strip()}")
        role_exists = "1" in (out or "").strip().splitlines()
        role_sql = (
            f"ALTER ROLE {db_user} WITH LOGIN PASSWORD {_sql_literal(db_password)}"
            if role_exists
            else f"CREATE ROLE {db_user} LOGIN PASSWORD {_sql_literal(db_password)}"
        )
        code, out, err = _run(ssh, f"sudo -u postgres psql -v ON_ERROR_STOP=1 -c \"{role_sql}\"", timeout=120)
        if code != 0:
            raise SystemExit(f"Failed to create/alter role:\n{err.strip() or out.strip()}")

        code, out, err = _run(
            ssh,
            f"sudo -u postgres psql -tAc \"SELECT 1 FROM pg_database WHERE datname='{db_name}'\"",
            timeout=120,
        )
        if code != 0:
            raise SystemExit(f"Failed to query postgres databases:\n{err.strip() or out.strip()}")
        db_exists = "1" in (out or "").strip().splitlines()
        if not db_exists:
            code, out, err = _run(
                ssh,
                f"sudo -u postgres psql -v ON_ERROR_STOP=1 -c \"CREATE DATABASE {db_name} OWNER {db_user}\"",
                timeout=120,
            )
            if code != 0:
                raise SystemExit(f"Failed to create database:\n{err.strip() or out.strip()}")

        print("Installing psycopg2 in app venv...")
        code, out, err = _run(ssh, f"{args.venv_python} -m pip install --quiet psycopg2-binary", timeout=600)
        if code != 0:
            raise SystemExit(f"Failed to install psycopg2-binary:\n{err.strip() or out.strip()}")

        print("Uploading migration script...")
        sftp = ssh.open_sftp()
        try:
            _put_file(sftp, REPO_ROOT / "scripts" / "migrate_sqlite_to_postgres.py", "/root/portal_bot/migrate_sqlite_to_postgres.py")
        finally:
            sftp.close()

        print("Backing up current sqlite and .env...")
        _run(ssh, "cp -f /root/portal_bot/.env /root/portal_bot/.env.pre_postgres.bak", timeout=60)
        _run(ssh, f"cp -f {args.sqlite_path} {args.sqlite_path}.pre_postgres.bak", timeout=120)

        print("Running data migration...")
        code, out, err = _run(
            ssh,
            (
                f"{args.venv_python} /root/portal_bot/migrate_sqlite_to_postgres.py "
                f"--sqlite-url '{sqlite_url}' --postgres-url '{pg_url}' --truncate-target"
            ),
            timeout=1800,
        )
        if code != 0:
            raise SystemExit(f"SQLite -> Postgres migration failed:\n{err.strip() or out.strip()}")
        print(out.strip())

        print("Updating /root/portal_bot/.env DATABASE_URL...")
        sftp = ssh.open_sftp()
        try:
            with sftp.file("/root/portal_bot/.env", "r") as f:
                env_raw = f.read().decode("utf-8", errors="replace")
            env_new = _upsert_env(
                env_raw,
                {
                    "DATABASE_URL": pg_url,
                    "POSTGRES_DATABASE_URL": pg_url,
                    "SQLITE_DATABASE_URL": sqlite_url,
                    "WORKER_EMBEDDED": "false",
                },
            )
            with sftp.file("/root/portal_bot/.env", "w") as f:
                f.write(env_new)
        finally:
            sftp.close()

        print("Restarting services...")
        code, out, err = _run(
            ssh,
            "systemctl restart portal-api portal-bot portal-helpbot portal-worker && systemctl is-active portal-api portal-bot portal-helpbot portal-worker",
            timeout=180,
        )
        if code != 0:
            raise SystemExit(f"Service restart failed:\n{err.strip() or out.strip()}")
        print(out.strip())

        print("Postgres cutover complete.")
        print(f"DATABASE_URL={_mask_url(pg_url)}")
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
