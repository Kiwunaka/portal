from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import shlex
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

import paramiko
from ssh_host_keys import configure_ssh_host_key_policy


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"
DEFAULT_BACKUP_DIRECTORY = "/root/backups/postgres-rehearsals"
DEFAULT_PASSPHRASE_ENV = "POKROV_POSTGRES_BACKUP_PASSPHRASE"
LIVE_ENV_PATH = "/root/portal_bot/.env"
LIVE_VENV_PYTHON = "/root/portal_bot/venv/bin/python"
MAX_SNAPSHOT_LIFETIME_SECONDS = 2 * 24 * 60 * 60 + 300

SQL_IDENTIFIER_RE = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")
SNAPSHOT_ID_RE = re.compile(r"^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{8}-[1-9][0-9]{0,19}$")
ENV_NAME_RE = re.compile(r"^[A-Z_][A-Z0-9_]{0,127}$")
BACKUP_COMPONENT_RE = re.compile(r"^[A-Za-z0-9_-][A-Za-z0-9._-]{0,127}$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
IDENTITY_NONCE_RE = re.compile(r"^[a-f0-9]{64}$")
SENSITIVE_KEY_RE = re.compile(
    r"(?i)(?:password|passwd|passphrase|token|secret|authorization|credential|"
    r"api[_-]?key|private[_-]?key|database[_-]?url|connection|dsn|uri|url)"
)
SENSITIVE_VALUE_RE = re.compile(
    r"(?i)(?:[a-z][a-z0-9+.-]{1,31}://|"
    r"(?:password|passwd|passphrase|token|secret|authorization|credential|api[_-]?key)\s*[:=]|"
    r"bearer\s+[a-z0-9._~+/=-]+|"
    r"(?:sk|pk|rk)[_-](?:live|test|prod)[_-][a-z0-9_-]{16,}|"
    r"gh[pousr]_[a-z0-9]{20,}|"
    r"eyJ[a-z0-9_-]{8,}\.[a-z0-9_-]{8,}\.[a-z0-9_-]{8,}|"
    r"[0-9]{6,12}:[a-z0-9_-]{20,}|"
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)"
)


class GateError(RuntimeError):
    pass


class RemoteGateError(GateError):
    def __init__(self, error_class: str) -> None:
        self.error_class = error_class
        super().__init__(f"remote_{error_class}_failed")

    def __repr__(self) -> str:
        return f"RemoteGateError({self.error_class!r})"


def remote_error(error_class: str, _cause: BaseException | None = None) -> RemoteGateError:
    safe_class = re.sub(r"[^a-z0-9_]+", "_", str(error_class).lower()).strip("_")
    return RemoteGateError(safe_class or "operation")


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, _message: str) -> None:
        self.print_usage(sys.stderr)
        raise SystemExit("Invalid command-line arguments")


def validate_database_selection(
    source: str,
    confirm_source: str,
    target: str,
    confirm_target: str,
) -> tuple[str, str]:
    if source != "portal":
        raise GateError("--source-db must be portal")
    if confirm_source != source:
        raise GateError("--confirm-source must exactly match --source-db")
    if not SQL_IDENTIFIER_RE.fullmatch(target):
        raise GateError("Invalid --target-db SQL identifier")
    if confirm_target != target:
        raise GateError("--confirm-target must exactly match --target-db")
    if not target.endswith("_rehearsal"):
        raise GateError("--target-db must end with _rehearsal")
    if target == source:
        raise GateError("Source and target databases must differ")
    return source, target


def validate_backup_directory(raw: str) -> str:
    value = str(raw or "").strip()
    path = PurePosixPath(value)
    parts = path.parts
    if len(parts) < 4 or parts[:3] != ("/", "root", "backups"):
        raise GateError("Backup directory must be below /root/backups/")
    if any(part in {"", ".", ".."} or not BACKUP_COMPONENT_RE.fullmatch(part) for part in parts[3:]):
        raise GateError("Invalid backup directory")
    normalized = str(path)
    if normalized != value:
        raise GateError("Backup directory must be normalized")
    return normalized


def make_backup_basename(
    source: str,
    *,
    timestamp: str | None = None,
    nonce: str | None = None,
) -> str:
    if not SQL_IDENTIFIER_RE.fullmatch(source):
        raise GateError("Invalid source database for backup basename")
    stamp = timestamp or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    unique = nonce or secrets.token_hex(6)
    if not re.fullmatch(r"[0-9]{8}T[0-9]{6}Z", stamp):
        raise GateError("Invalid backup timestamp")
    if not re.fullmatch(r"[a-f0-9]{8,32}", unique):
        raise GateError("Invalid backup nonce")
    return f"{source}-{stamp}-{unique}.dump.enc"


def _validated_backup_path(backup_path: str) -> tuple[str, str]:
    path = PurePosixPath(str(backup_path))
    directory = validate_backup_directory(str(path.parent))
    basename = path.name
    if not re.fullmatch(
        r"[a-z_][a-z0-9_]{0,62}-[0-9]{8}T[0-9]{6}Z-[a-f0-9]{8,32}\.dump\.enc",
        basename,
    ):
        raise GateError("Invalid backup filename")
    return directory, str(path)


def validate_snapshot_id(snapshot_id: str) -> str:
    value = str(snapshot_id or "").strip()
    if not SNAPSHOT_ID_RE.fullmatch(value):
        raise GateError("Invalid exported PostgreSQL snapshot id")
    return value


def _validated_server_timeout(value: int, operation: str) -> int:
    timeout_value = int(value)
    if not 60 <= timeout_value <= 24 * 60 * 60:
        raise GateError(f"Invalid {operation} server timeout")
    return timeout_value


def _encrypted_pipeline_supervisor(pipeline: str, *, server_timeout: int) -> str:
    return (
        "# gate_encrypted_pipeline_supervisor\n"
        "passphrase_fd=/proc/$$/fd/3\n"
        f"setsid --wait timeout --signal=TERM --kill-after=10s {server_timeout}s "
        f"sh -c {shlex.quote(pipeline)} pokrov-encrypted-pipeline \"$passphrase_fd\" 3<&-"
    )


def build_backup_command(
    source: str,
    backup_path: str,
    *,
    snapshot_id: str,
    server_timeout: int = 3600,
) -> str:
    if not SQL_IDENTIFIER_RE.fullmatch(source):
        raise GateError("Invalid source database")
    directory, final_path = _validated_backup_path(backup_path)
    directory_q = shlex.quote(directory)
    final_q = shlex.quote(final_path)
    source_q = shlex.quote(source)
    snapshot_q = shlex.quote(validate_snapshot_id(snapshot_id))
    timeout_value = _validated_server_timeout(server_timeout, "backup")
    pipeline = f"""nice -n 10 ionice -c 2 -n 7 \
  runuser -u postgres -- pg_dump --format=custom --compress=6 \
  --lock-wait-timeout=10s --snapshot={snapshot_q} --dbname={source_q} 3<&- </dev/null |
  openssl enc -aes-256-cbc -salt -pbkdf2 -iter 200000 -md sha256 \
  -pass file:\"$1\" -out {final_q}.partial"""
    supervised_pipeline = _encrypted_pipeline_supervisor(
        pipeline, server_timeout=timeout_value
    )
    return f"""# gate_encrypted_backup
set -Eeuo pipefail
umask 077
backup_dir={directory_q}
partial={final_q}.partial
final={final_q}
cleanup() {{ exec 3<&-; rm -f -- "$partial"; test ! -d "$backup_dir" || sync -f "$backup_dir"; }}
trap cleanup EXIT HUP INT TERM
install -d -m 0700 -- "$backup_dir"
test ! -e "$partial"
test ! -e "$final"
exec 3<&0 0</dev/null
{supervised_pipeline}
exec 3<&-
test -s "$partial"
chmod 0600 "$partial"
sync -f "$partial"
mv --no-clobber -- "$partial" "$final"
test ! -e "$partial"
sync -f "$final"
trap - EXIT HUP INT TERM
"""


def build_verify_command(backup_path: str, *, server_timeout: int = 1800) -> str:
    _, final_path = _validated_backup_path(backup_path)
    path_q = shlex.quote(final_path)
    timeout_value = _validated_server_timeout(server_timeout, "verify")
    pipeline = f"""openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -md sha256 \
  -pass file:\"$1\" -in {path_q} |
  nice -n 10 ionice -c 2 -n 7 runuser -u postgres -- \
  pg_restore --list 3<&- >/dev/null"""
    supervised_pipeline = _encrypted_pipeline_supervisor(
        pipeline, server_timeout=timeout_value
    )
    return f"""# gate_verify_archive
set -Eeuo pipefail
test -f {path_q}
test "$(stat -c %a -- {path_q})" = 600
exec 3<&0 0</dev/null
{supervised_pipeline}
exec 3<&-
"""


def _application_role_shell(source: str, *, require_target_owner: str | None = None) -> str:
    if not SQL_IDENTIFIER_RE.fullmatch(source):
        raise GateError("Invalid source database for application role")
    if require_target_owner is not None and (
        not SQL_IDENTIFIER_RE.fullmatch(require_target_owner)
        or not require_target_owner.endswith("_rehearsal")
    ):
        raise GateError("Invalid target database for application role")
    resolver = "\n".join(
        (
            "import re, sys",
            "from dotenv import dotenv_values",
            "from sqlalchemy.engine import make_url",
            "try:",
            f"    raw = str(dotenv_values({LIVE_ENV_PATH!r}).get('DATABASE_URL') or '')",
            "    url = make_url(raw)",
            "    role = str(url.username or '')",
            f"    valid = url.get_backend_name() == 'postgresql' and url.database == {source!r}",
            "    valid = valid and re.fullmatch(r'[a-z_][a-z0-9_]{0,62}', role) is not None",
            "    if not valid:",
            "        raise ValueError('live_database_guard')",
            "except BaseException:",
            "    raise SystemExit(2)",
            "sys.stdout.write(role)",
        )
    )
    resolver = f"exec({resolver!r})"
    role_query = (
        "SELECT CASE WHEN EXISTS (SELECT 1 FROM pg_roles "
        "WHERE rolname = :'role_name' AND rolcanlogin AND NOT rolsuper "
        "AND NOT rolreplication AND NOT rolbypassrls) THEN 1 ELSE 0 END"
    )
    lines = [
        f"role=$({shlex.quote(LIVE_VENV_PYTHON)} -c {shlex.quote(resolver)})",
        'test -n "$role"',
        f"role_ok=$(printf '%s\\n' {shlex.quote(role_query)} | "
        "runuser -u postgres -- psql --no-psqlrc --quiet --tuples-only --no-align "
        "--set=ON_ERROR_STOP=1 --set=role_name=\"$role\" --dbname=postgres)",
        'test "$role_ok" = 1',
    ]
    if require_target_owner is not None:
        owner_query = (
            "SELECT CASE WHEN EXISTS (SELECT 1 FROM pg_database d JOIN pg_roles r ON r.oid = d.datdba "
            f"WHERE d.datname = '{require_target_owner}' AND r.rolname = :'role_name') "
            "THEN 1 ELSE 0 END"
        )
        lines.extend(
            (
                f"target_owner_ok=$(printf '%s\\n' {shlex.quote(owner_query)} | "
                "runuser -u postgres -- psql --no-psqlrc --quiet --tuples-only --no-align "
                "--set=ON_ERROR_STOP=1 --set=role_name=\"$role\" --dbname=postgres)",
                'test "$target_owner_ok" = 1',
            )
        )
    return "\n".join(lines)


def build_restore_command(
    target: str,
    backup_path: str,
    *,
    source: str = "portal",
    server_timeout: int = 5400,
) -> str:
    if not SQL_IDENTIFIER_RE.fullmatch(target) or not target.endswith("_rehearsal"):
        raise GateError("Invalid rehearsal target database")
    _, final_path = _validated_backup_path(backup_path)
    target_q = shlex.quote(target)
    path_q = shlex.quote(final_path)
    timeout_value = _validated_server_timeout(server_timeout, "restore")
    role_setup = _application_role_shell(source, require_target_owner=target)
    pipeline = f"""{role_setup}
openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -md sha256 \
  -pass file:\"$1\" -in {path_q} |
  nice -n 10 ionice -c 2 -n 7 runuser -u postgres -- \
  pg_restore --exit-on-error --no-owner --no-privileges --role=\"$role\" \
  --dbname={target_q} 3<&-"""
    supervised_pipeline = _encrypted_pipeline_supervisor(
        pipeline, server_timeout=timeout_value
    )
    return f"""# gate_restore_target
set -Eeuo pipefail
exec 3<&0 0</dev/null
{supervised_pipeline}
exec 3<&-
"""


def build_target_role_evidence_command(source: str, target: str) -> str:
    if not SQL_IDENTIFIER_RE.fullmatch(target) or not target.endswith("_rehearsal"):
        raise GateError("Invalid rehearsal target database")
    role_setup = _application_role_shell(source, require_target_owner=target)
    target_q = shlex.quote(target)
    sql = """
WITH app_role AS (
    SELECT oid FROM pg_roles WHERE rolname = :'role_name'
), public_objects AS (
    SELECT n.nspowner AS owner_oid
    FROM pg_namespace n
    WHERE n.nspname = 'public'
    UNION ALL
    SELECT c.relowner AS owner_oid
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
    UNION ALL
    SELECT p.proowner
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public'
    UNION ALL
    SELECT t.typowner
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE n.nspname = 'public'
    UNION ALL
    SELECT e.extowner
    FROM pg_extension e
    JOIN pg_namespace n ON n.oid = e.extnamespace
    WHERE n.nspname = 'public'
    UNION ALL
    SELECT c.collowner
    FROM pg_collation c
    JOIN pg_namespace n ON n.oid = c.collnamespace
    WHERE n.nspname = 'public'
    UNION ALL
    SELECT c.conowner
    FROM pg_conversion c
    JOIN pg_namespace n ON n.oid = c.connamespace
    WHERE n.nspname = 'public'
    UNION ALL
    SELECT o.oprowner
    FROM pg_operator o
    JOIN pg_namespace n ON n.oid = o.oprnamespace
    WHERE n.nspname = 'public'
    UNION ALL
    SELECT o.opcowner
    FROM pg_opclass o
    JOIN pg_namespace n ON n.oid = o.opcnamespace
    WHERE n.nspname = 'public'
    UNION ALL
    SELECT o.opfowner
    FROM pg_opfamily o
    JOIN pg_namespace n ON n.oid = o.opfnamespace
    WHERE n.nspname = 'public'
    UNION ALL
    SELECT d.dictowner
    FROM pg_ts_dict d
    JOIN pg_namespace n ON n.oid = d.dictnamespace
    WHERE n.nspname = 'public'
    UNION ALL
    SELECT c.cfgowner
    FROM pg_ts_config c
    JOIN pg_namespace n ON n.oid = c.cfgnamespace
    WHERE n.nspname = 'public'
    UNION ALL
    SELECT s.stxowner
    FROM pg_statistic_ext s
    JOIN pg_namespace n ON n.oid = s.stxnamespace
    WHERE n.nspname = 'public'
    UNION ALL
    SELECT d.defaclrole
    FROM pg_default_acl d
    JOIN pg_namespace n ON n.oid = d.defaclnamespace
    WHERE n.nspname = 'public'
)
SELECT json_build_object(
    'database_owner_is_app', (
        SELECT d.datdba = a.oid
        FROM pg_database d CROSS JOIN app_role a
        WHERE d.datname = current_database()
    ),
    'database_public_access_revoked', NOT EXISTS (
        SELECT 1
        FROM pg_database d
        CROSS JOIN LATERAL aclexplode(COALESCE(d.datacl, acldefault('d', d.datdba))) acl
        WHERE d.datname = current_database() AND acl.grantee = 0
    ),
    'public_schema_create', has_schema_privilege(:'role_name', 'public', 'CREATE'),
    'schema_public_access_revoked', NOT EXISTS (
        SELECT 1
        FROM pg_namespace n
        CROSS JOIN LATERAL aclexplode(COALESCE(n.nspacl, acldefault('n', n.nspowner))) acl
        WHERE n.nspname = 'public' AND acl.grantee = 0
    ),
    'public_objects_total', (SELECT count(*) FROM public_objects),
    'public_objects_owned', (
        SELECT count(*) FROM public_objects o CROSS JOIN app_role a WHERE o.owner_oid = a.oid
    )
);
""".strip()
    return f"""# gate_target_role_evidence
set -Eeuo pipefail
{role_setup}
printf '%s\n' {shlex.quote(sql)} | \
timeout --signal=TERM --kill-after=10s 60s runuser -u postgres -- \
  psql --no-psqlrc --quiet --tuples-only --no-align --set=ON_ERROR_STOP=1 \
  --set=role_name=\"$role\" --dbname={target_q}
"""


def build_integrity_evidence_command(
    database: str,
    *,
    snapshot_id: str | None = None,
    server_timeout: int = 3600,
) -> str:
    if not SQL_IDENTIFIER_RE.fullmatch(database):
        raise GateError("Invalid evidence database")
    timeout_value = _validated_server_timeout(server_timeout, "evidence")
    database_q = shlex.quote(database)
    snapshot_sql = ""
    if snapshot_id is not None:
        snapshot_sql = f"SET TRANSACTION SNAPSHOT '{validate_snapshot_id(snapshot_id)}';\n"
    statement_timeout = timeout_value - 5
    return f"""# gate_integrity_evidence
set -Eeuo pipefail
nice -n 10 ionice -c 2 -n 7 timeout --signal=TERM --kill-after=10s {timeout_value}s \
  runuser -u postgres -- psql --no-psqlrc --quiet --tuples-only --no-align \
  --set=ON_ERROR_STOP=1 --dbname={database_q} <<'POKROV_GATE_SQL'
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
{snapshot_sql}SET LOCAL statement_timeout = '{statement_timeout}s';
SET LOCAL lock_timeout = '10s';
SELECT json_build_object(
  'record_type', 'database',
  'database_bytes', pg_database_size(current_database()),
  'public_table_count', (
    SELECT count(*)
    FROM pg_catalog.pg_class c
    JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p')
  )
);

SELECT format(
  $pokrov_count$SELECT json_build_object(
    'record_type', 'table',
    'name', %L,
    'row_count', count(*)
  ) FROM public.%I;$pokrov_count$,
  c.relname,
  c.relname
)
FROM pg_catalog.pg_class c
JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p')
ORDER BY c.relname
\\gexec

SELECT CASE
  WHEN to_regclass('public.support_attachments') IS NULL THEN
    $pokrov_absent$SELECT json_build_object(
      'record_type', 'support',
      'schema_status', 'absent',
      'total', 0
    );$pokrov_absent$
  WHEN to_regclass('public.support_tickets') IS NOT NULL
       AND to_regclass('public.support_ticket_messages') IS NOT NULL
       AND NOT EXISTS (
         SELECT 1
         FROM (VALUES ('support_attachments', 'ticket_id'),
                      ('support_attachments', 'message_id'),
                      ('support_tickets', 'id'),
                      ('support_ticket_messages', 'id'),
                      ('support_ticket_messages', 'ticket_id')) required(table_name, column_name)
         WHERE NOT EXISTS (
           SELECT 1 FROM information_schema.columns actual
           WHERE actual.table_schema = 'public'
             AND actual.table_name = required.table_name
             AND actual.column_name = required.column_name
         )
       ) THEN
    $pokrov_available$SELECT json_build_object(
      'record_type', 'support',
      'schema_status', 'available',
      'total', count(*),
      'bound', count(*) FILTER (
        WHERE a.ticket_id IS NOT NULL AND a.message_id IS NOT NULL
          AND t.id IS NOT NULL AND m.id IS NOT NULL
          AND m.ticket_id = a.ticket_id
      ),
      'unbound', count(*) FILTER (WHERE a.ticket_id IS NULL AND a.message_id IS NULL),
      'dangling', count(*) FILTER (
        WHERE (a.ticket_id IS NULL) <> (a.message_id IS NULL)
           OR (a.ticket_id IS NOT NULL AND t.id IS NULL)
           OR (a.message_id IS NOT NULL AND m.id IS NULL)
           OR (m.id IS NOT NULL AND m.ticket_id IS DISTINCT FROM a.ticket_id)
      )
    )
    FROM public.support_attachments a
    LEFT JOIN public.support_tickets t ON t.id = a.ticket_id
    LEFT JOIN public.support_ticket_messages m ON m.id = a.message_id;$pokrov_available$
  ELSE
    $pokrov_legacy$SELECT json_build_object(
      'record_type', 'support',
      'schema_status', 'legacy',
      'total', count(*)
    ) FROM public.support_attachments;$pokrov_legacy$
END
\\gexec
COMMIT;
POKROV_GATE_SQL
"""


def assert_report_safe(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if SENSITIVE_KEY_RE.search(str(key)):
                raise GateError("Report contains a sensitive field name")
            assert_report_safe(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_report_safe(item)
        return
    if isinstance(value, str) and SENSITIVE_VALUE_RE.search(value):
        raise GateError("Report contains a sensitive value")


def validate_report_path(path: Path | str) -> Path:
    target = Path(path).expanduser().resolve()
    if target.suffix.lower() != ".json":
        raise GateError("--report must use a .json filename")
    if target.exists():
        raise GateError("Report path already exists")
    parent = target.parent
    for candidate in (parent, *parent.parents):
        if (candidate / ".git").exists():
            raise GateError("Refusing to write operational evidence inside a git worktree")
    return target


def write_report_atomic(path: Path | str, report: Mapping[str, Any]) -> None:
    target = validate_report_path(path)
    assert_report_safe(report)
    payload = json.dumps(dict(report), ensure_ascii=True, sort_keys=True, indent=2) + "\n"
    assert_report_safe(payload)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
    descriptor: int | None = None
    try:
        descriptor = _open_private_report_temp(temporary)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            descriptor = None
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, target)
        except FileExistsError:
            raise GateError("Report path already exists") from None
        except OSError:
            raise GateError("Unable to publish report atomically") from None
        _fsync_parent_directory(target.parent)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        temporary.unlink(missing_ok=True)
        _fsync_parent_directory(target.parent)


def _open_private_report_temp(path: Path) -> int:
    if os.name != "nt":
        return os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)

    import ctypes
    import msvcrt
    from ctypes import wintypes

    security_descriptor = ctypes.c_void_p()
    sddl = f"D:P(A;;GA;;;{_windows_current_user_sid()})"
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    convert = advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW
    convert.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(wintypes.ULONG),
    )
    convert.restype = wintypes.BOOL
    if not convert(sddl, 1, ctypes.byref(security_descriptor), None):
        raise GateError("Unable to secure report temp file")

    class SecurityAttributes(ctypes.Structure):
        _fields_ = (
            ("nLength", wintypes.DWORD),
            ("lpSecurityDescriptor", ctypes.c_void_p),
            ("bInheritHandle", wintypes.BOOL),
        )

    attributes = SecurityAttributes(
        ctypes.sizeof(SecurityAttributes), security_descriptor, False
    )
    create_file = kernel32.CreateFileW
    create_file.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(SecurityAttributes),
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    create_file.restype = wintypes.HANDLE
    invalid_handle = ctypes.c_void_p(-1).value
    handle = create_file(
        str(path),
        0x40000000,
        0,
        ctypes.byref(attributes),
        1,
        0x80,
        None,
    )
    kernel32.LocalFree.argtypes = (ctypes.c_void_p,)
    kernel32.LocalFree.restype = ctypes.c_void_p
    kernel32.LocalFree(security_descriptor)
    if handle == invalid_handle:
        error = ctypes.get_last_error()
        if error in {80, 183}:
            raise FileExistsError(str(path))
        raise GateError("Unable to create private report temp file")
    try:
        return msvcrt.open_osfhandle(int(handle), os.O_WRONLY | os.O_BINARY)
    except Exception:
        kernel32.CloseHandle(handle)
        raise GateError("Unable to open private report temp file") from None


def _windows_current_user_sid() -> str:
    if os.name != "nt":
        raise GateError("Windows SID is unavailable")

    import ctypes
    from ctypes import wintypes

    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    token = wintypes.HANDLE()
    advapi32.OpenProcessToken.argtypes = (
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.HANDLE),
    )
    advapi32.OpenProcessToken.restype = wintypes.BOOL
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    advapi32.GetTokenInformation.argtypes = (
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    )
    advapi32.GetTokenInformation.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.LocalFree.argtypes = (ctypes.c_void_p,)
    kernel32.LocalFree.restype = ctypes.c_void_p
    if not advapi32.OpenProcessToken(kernel32.GetCurrentProcess(), 0x0008, ctypes.byref(token)):
        raise GateError("Unable to identify report owner")
    try:
        required = wintypes.DWORD()
        advapi32.GetTokenInformation(token, 1, None, 0, ctypes.byref(required))
        if required.value == 0:
            raise GateError("Unable to identify report owner")
        buffer = ctypes.create_string_buffer(required.value)
        if not advapi32.GetTokenInformation(
            token, 1, buffer, required, ctypes.byref(required)
        ):
            raise GateError("Unable to identify report owner")
        sid_pointer = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_void_p))[0]
        sid_string = wintypes.LPWSTR()
        advapi32.ConvertSidToStringSidW.argtypes = (
            ctypes.c_void_p,
            ctypes.POINTER(wintypes.LPWSTR),
        )
        advapi32.ConvertSidToStringSidW.restype = wintypes.BOOL
        if not advapi32.ConvertSidToStringSidW(sid_pointer, ctypes.byref(sid_string)):
            raise GateError("Unable to identify report owner")
        try:
            return sid_string.value
        finally:
            kernel32.LocalFree(sid_string)
    finally:
        kernel32.CloseHandle(token)


def _windows_file_dacl_sddl(path: Path | str) -> str:
    if os.name != "nt":
        raise GateError("Windows DACL is unavailable")

    import ctypes
    from ctypes import wintypes

    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    security_descriptor = ctypes.c_void_p()
    advapi32.GetNamedSecurityInfoW.argtypes = (
        wintypes.LPWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p),
    )
    advapi32.GetNamedSecurityInfoW.restype = wintypes.DWORD
    advapi32.ConvertSecurityDescriptorToStringSecurityDescriptorW.argtypes = (
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.LPWSTR),
        ctypes.POINTER(wintypes.ULONG),
    )
    advapi32.ConvertSecurityDescriptorToStringSecurityDescriptorW.restype = wintypes.BOOL
    kernel32.LocalFree.argtypes = (ctypes.c_void_p,)
    kernel32.LocalFree.restype = ctypes.c_void_p
    result = advapi32.GetNamedSecurityInfoW(
        str(path), 1, 0x00000004, None, None, None, None, ctypes.byref(security_descriptor)
    )
    if result != 0:
        raise GateError("Unable to inspect report DACL")
    sddl = wintypes.LPWSTR()
    try:
        if not advapi32.ConvertSecurityDescriptorToStringSecurityDescriptorW(
            security_descriptor, 1, 0x00000004, ctypes.byref(sddl), None
        ):
            raise GateError("Unable to inspect report DACL")
        try:
            return sddl.value
        finally:
            kernel32.LocalFree(sddl)
    finally:
        kernel32.LocalFree(security_descriptor)


def _fsync_parent_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor: int | None = None
    try:
        descriptor = os.open(path, flags)
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _parse_password(path: Path) -> str:
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    lines = [line.strip() for line in raw.splitlines()]
    for index, line in enumerate(lines):
        if "BRAINnode" not in line:
            continue
        in_key_block = False
        for candidate in lines[index + 1 : index + 30]:
            if candidate.startswith("-----BEGIN ") and candidate.endswith(" KEY-----"):
                in_key_block = True
                continue
            if in_key_block:
                if candidate.startswith("-----END ") and candidate.endswith(" KEY-----"):
                    in_key_block = False
                continue
            if re.search(r"(?:^|\s)(?:ssh-(?:ed25519|rsa|dss)|ecdsa-sha2-|sk-ssh-)", candidate):
                continue
            if candidate:
                return candidate
    return ""


def _require_passphrase(env: Mapping[str, str], name: str) -> str:
    if not ENV_NAME_RE.fullmatch(name):
        raise GateError("Invalid --passphrase-env name")
    value = str(env.get(name, ""))
    if not value:
        raise GateError(f"Missing passphrase environment variable: {name}")
    if "\n" in value or "\r" in value:
        raise GateError("Passphrase environment variable must be a single line")
    return value


def _remote_run(
    ssh: paramiko.SSHClient,
    command: str,
    *,
    error_class: str,
    timeout: float,
    secret_input: str | None = None,
    max_output_bytes: int = 2 * 1024 * 1024,
) -> str:
    try:
        stdin, stdout, _stderr = ssh.exec_command(command, timeout=timeout)
        if secret_input is not None:
            stdin.write(secret_input + "\n")
            stdin.flush()
        stdin.close()
        code, output = _drain_channel_to_exit(
            stdout.channel,
            error_class=error_class,
            timeout=timeout,
            max_output_bytes=max_output_bytes,
        )
    except RemoteGateError:
        raise
    except Exception as exc:
        raise remote_error(error_class, exc) from None
    if code != 0:
        raise remote_error(error_class)
    return output.decode("utf-8", errors="replace")


def _drain_channel_once(
    channel: Any,
    stdout_buffer: bytearray,
    *,
    stderr_bytes: int,
    max_output_bytes: int,
    error_class: str,
) -> tuple[bool, int]:
    drained = False
    if channel.recv_ready():
        chunk = channel.recv(32768)
        if chunk:
            drained = True
            stdout_buffer.extend(chunk)
            if len(stdout_buffer) + stderr_bytes > max_output_bytes:
                channel.close()
                raise remote_error(f"{error_class}_output")
    if channel.recv_stderr_ready():
        chunk = channel.recv_stderr(32768)
        if chunk:
            drained = True
            stderr_bytes += len(chunk)
            if len(stdout_buffer) + stderr_bytes > max_output_bytes:
                channel.close()
                raise remote_error(f"{error_class}_output")
    return drained, stderr_bytes


def _drain_channel_to_exit(
    channel: Any,
    *,
    error_class: str,
    timeout: float,
    max_output_bytes: int,
) -> tuple[int, bytes]:
    deadline = time.monotonic() + float(timeout)
    stdout_buffer = bytearray()
    stderr_bytes = 0
    while True:
        drained, stderr_bytes = _drain_channel_once(
            channel,
            stdout_buffer,
            stderr_bytes=stderr_bytes,
            max_output_bytes=max_output_bytes,
            error_class=error_class,
        )
        if channel.exit_status_ready():
            drained_after_exit, stderr_bytes = _drain_channel_once(
                channel,
                stdout_buffer,
                stderr_bytes=stderr_bytes,
                max_output_bytes=max_output_bytes,
                error_class=error_class,
            )
            if not drained_after_exit and not channel.recv_ready() and not channel.recv_stderr_ready():
                return channel.recv_exit_status(), bytes(stdout_buffer)
        if time.monotonic() >= deadline:
            channel.close()
            raise remote_error(f"{error_class}_timeout")
        if not drained:
            time.sleep(0.01)


@dataclass(frozen=True)
class ExporterIdentity:
    identity_nonce: str
    process_id: int
    process_group_id: int
    session_id: int
    start_time: int


@dataclass(frozen=True)
class ObservedProcessIdentity:
    process_id: int
    process_group_id: int
    session_id: int
    start_time: int
    command_arguments: tuple[str, ...]


def _validate_identity_nonce(value: str) -> str:
    nonce = str(value or "")
    if not IDENTITY_NONCE_RE.fullmatch(nonce):
        raise GateError("Invalid exporter identity nonce")
    return nonce


def _exporter_identity_matches(
    expected: ExporterIdentity,
    observed: ObservedProcessIdentity,
) -> bool:
    marker = f"pokrov-exporter-{expected.identity_nonce}"
    return (
        observed.process_id == expected.process_id
        and observed.process_group_id == expected.process_group_id
        and observed.session_id == expected.session_id
        and observed.start_time == expected.start_time
        and marker in observed.command_arguments
    )


def _cleanup_signal_plan(
    expected: ExporterIdentity,
    observed: ObservedProcessIdentity,
) -> tuple[str, ...]:
    return ("TERM", "KILL") if _exporter_identity_matches(expected, observed) else ()


@dataclass
class SnapshotExporter:
    snapshot_id: str
    identity_nonce: str
    process_id: int
    process_group_id: int
    session_id: int
    start_time: int
    ssh: paramiko.SSHClient
    stdin: Any
    channel: Any
    active: bool = True

    @property
    def identity(self) -> ExporterIdentity:
        return ExporterIdentity(
            identity_nonce=self.identity_nonce,
            process_id=self.process_id,
            process_group_id=self.process_group_id,
            session_id=self.session_id,
            start_time=self.start_time,
        )


def _snapshot_exporter_command(
    database: str,
    *,
    server_timeout: int,
    identity_nonce: str,
) -> str:
    if not SQL_IDENTIFIER_RE.fullmatch(database):
        raise GateError("Invalid snapshot database")
    nonce = _validate_identity_nonce(identity_nonce)
    timeout_value = max(60, min(int(server_timeout), MAX_SNAPSHOT_LIFETIME_SECONDS))
    marker = f"pokrov-exporter-{nonce}"
    postgres_command = (
        f"exec runuser -u postgres -- env POKROV_EXPORTER_NONCE={nonce} "
        "psql --no-psqlrc --quiet --tuples-only --no-align "
        f"--set=ON_ERROR_STOP=1 --dbname={shlex.quote(database)}"
    )
    child = f"""export POKROV_EXPORTER_NONCE={nonce}
read -r proc_stat < /proc/$$/stat
proc_fields=${{proc_stat#*) }}
set -- $proc_fields
process_group_id=$3
session_id=$4
start_time=${{20}}
test "$process_group_id" = "$$"
test "$session_id" = "$$"
printf 'POKROV_EXPORTER_NONCE=%s\n' {nonce}
printf 'POKROV_EXPORTER_PID=%s\n' "$$"
printf 'POKROV_EXPORTER_PGID=%s\n' "$process_group_id"
printf 'POKROV_EXPORTER_SESSION=%s\n' "$session_id"
printf 'POKROV_EXPORTER_STARTTIME=%s\n' "$start_time"
exec nice -n 10 ionice -c 2 -n 7 timeout --signal=TERM --kill-after=10s {timeout_value}s \
  sh -c {shlex.quote(postgres_command)} {shlex.quote(marker)}"""
    return (
        "# gate_snapshot_exporter\nset -Eeuo pipefail\n"
        "exec setsid --wait sh -c " + shlex.quote(child)
    )


def _open_snapshot_exporter(
    ssh: paramiko.SSHClient,
    database: str,
    *,
    timeout: float,
    server_timeout: int | None = None,
    identity_nonce: str | None = None,
    state: "RunState | None" = None,
) -> SnapshotExporter:
    channel: Any | None = None
    stdin: Any | None = None
    partial_identity: ExporterIdentity | None = None
    nonce = _validate_identity_nonce(identity_nonce or secrets.token_hex(32))
    try:
        lifetime_timeout = server_timeout if server_timeout is not None else max(60, int(float(timeout)) + 30)
        lifetime_timeout = max(60, min(int(lifetime_timeout), MAX_SNAPSHOT_LIFETIME_SECONDS))
        stdin, stdout, _stderr = ssh.exec_command(
            _snapshot_exporter_command(
                database,
                server_timeout=lifetime_timeout,
                identity_nonce=nonce,
            ),
            timeout=timeout,
        )
        channel = stdout.channel
        stdin.write(
            "BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;\n"
            f"SET LOCAL statement_timeout = '{lifetime_timeout - 5}s';\n"
            "SET LOCAL lock_timeout = '10s';\n"
            "SELECT 'POKROV_SNAPSHOT=' || pg_export_snapshot();\n"
        )
        stdin.flush()
        deadline = time.monotonic() + float(timeout)
        stdout_buffer = bytearray()
        stderr_bytes = 0
        while True:
            drained, stderr_bytes = _drain_channel_once(
                channel,
                stdout_buffer,
                stderr_bytes=stderr_bytes,
                max_output_bytes=64 * 1024,
                error_class="snapshot_export",
            )
            output = bytes(stdout_buffer)
            snapshot_match = re.search(rb"(?:^|\n)POKROV_SNAPSHOT=([^\r\n]+)", output)
            nonce_match = re.search(rb"(?:^|\n)POKROV_EXPORTER_NONCE=([a-f0-9]{64})", output)
            pid_match = re.search(rb"(?:^|\n)POKROV_EXPORTER_PID=([0-9]+)", output)
            pgid_match = re.search(rb"(?:^|\n)POKROV_EXPORTER_PGID=([0-9]+)", output)
            session_match = re.search(rb"(?:^|\n)POKROV_EXPORTER_SESSION=([0-9]+)", output)
            start_match = re.search(rb"(?:^|\n)POKROV_EXPORTER_STARTTIME=([0-9]+)", output)
            identity_matches = (
                nonce_match,
                pid_match,
                pgid_match,
                session_match,
                start_match,
            )
            if all(identity_matches) and partial_identity is None:
                received_nonce = nonce_match.group(1).decode("ascii")  # type: ignore[union-attr]
                process_id = int(pid_match.group(1))  # type: ignore[union-attr]
                process_group_id = int(pgid_match.group(1))  # type: ignore[union-attr]
                session_id = int(session_match.group(1))  # type: ignore[union-attr]
                start_time = int(start_match.group(1))  # type: ignore[union-attr]
                if (
                    received_nonce != nonce
                    or process_id <= 1
                    or process_id != process_group_id
                    or process_id != session_id
                    or start_time <= 0
                ):
                    raise remote_error("snapshot_export_identity")
                partial_identity = ExporterIdentity(
                    identity_nonce=nonce,
                    process_id=process_id,
                    process_group_id=process_group_id,
                    session_id=session_id,
                    start_time=start_time,
                )
            if snapshot_match and partial_identity is not None:
                snapshot_id = validate_snapshot_id(
                    snapshot_match.group(1).decode("ascii", errors="strict")
                )
                if channel.exit_status_ready():
                    raise remote_error("snapshot_export_liveness")
                return SnapshotExporter(
                    snapshot_id=snapshot_id,
                    identity_nonce=partial_identity.identity_nonce,
                    process_id=partial_identity.process_id,
                    process_group_id=partial_identity.process_group_id,
                    session_id=partial_identity.session_id,
                    start_time=partial_identity.start_time,
                    ssh=ssh,
                    stdin=stdin,
                    channel=channel,
                )
            if channel.exit_status_ready():
                _drain_channel_to_exit(
                    channel,
                    error_class="snapshot_export",
                    timeout=max(0.01, deadline - time.monotonic()),
                    max_output_bytes=64 * 1024,
                )
                raise remote_error("snapshot_export")
            if time.monotonic() >= deadline:
                channel.close()
                raise remote_error("snapshot_export_timeout")
            if not drained:
                time.sleep(0.01)
    except RemoteGateError:
        if channel is not None:
            channel.close()
        if stdin is not None:
            try:
                stdin.close()
            except Exception:
                pass
        _cleanup_failed_snapshot_open(ssh, partial_identity, state=state)
        raise
    except Exception as exc:
        if channel is not None:
            channel.close()
        _cleanup_failed_snapshot_open(ssh, partial_identity, state=state)
        raise remote_error("snapshot_export", exc) from None


def _close_snapshot_exporter(
    exporter: SnapshotExporter,
    *,
    commit: bool,
    timeout: float,
) -> None:
    if not exporter.active:
        return
    try:
        exporter.stdin.write(("COMMIT;" if commit else "ROLLBACK;") + "\n\\q\n")
        exporter.stdin.flush()
        exporter.stdin.close()
        code, _output = _drain_channel_to_exit(
            exporter.channel,
            error_class="snapshot_close",
            timeout=timeout,
            max_output_bytes=64 * 1024,
        )
        if code != 0:
            raise remote_error("snapshot_close")
    except RemoteGateError:
        exporter.channel.close()
        raise
    except Exception as exc:
        exporter.channel.close()
        raise remote_error("snapshot_close", exc) from None
    finally:
        exporter.active = False


def _snapshot_force_cleanup_command(
    identity: ExporterIdentity,
    *,
    server_timeout: int = 15,
) -> str:
    nonce = _validate_identity_nonce(identity.identity_nonce)
    if (
        identity.process_id <= 1
        or identity.process_id != identity.process_group_id
        or identity.process_id != identity.session_id
        or identity.start_time <= 0
    ):
        raise GateError("Invalid snapshot process identity")
    timeout_value = max(5, min(int(server_timeout), 30))
    marker = f"pokrov-exporter-{nonce}"
    helper = f"""import os
import select
import signal
import time

EXPECTED_PID = {identity.process_id}
EXPECTED_PGID = {identity.process_group_id}
EXPECTED_SESSION = {identity.session_id}
EXPECTED_STARTTIME = {identity.start_time}
EXPECTED_NONCE = {nonce!r}
EXPECTED_MARKER = {marker!r}

def read_identity(pid):
    with open(f"/proc/{{pid}}/stat", "r", encoding="ascii") as handle:
        stat_text = handle.read()
    close_paren = stat_text.rfind(") ")
    if close_paren < 0:
        raise RuntimeError("identity")
    process_id = int(stat_text[:stat_text.find(" (")])
    fields = stat_text[close_paren + 2:].split()
    with open(f"/proc/{{pid}}/cmdline", "rb") as handle:
        command_arguments = tuple(
            item.decode("utf-8", errors="surrogateescape")
            for item in handle.read().split(b"\\0") if item
        )
    return process_id, int(fields[2]), int(fields[3]), int(fields[19]), command_arguments

def has_nonce(pid):
    with open(f"/proc/{{pid}}/environ", "rb") as handle:
        return ("POKROV_EXPORTER_NONCE=" + EXPECTED_NONCE).encode() in handle.read().split(b"\\0")

def verify_identity():
    leader = read_identity(EXPECTED_PID)
    if leader[:4] != (EXPECTED_PID, EXPECTED_PGID, EXPECTED_SESSION, EXPECTED_STARTTIME):
        raise RuntimeError("identity")
    if EXPECTED_MARKER not in leader[4] or not has_nonce(EXPECTED_PID):
        raise RuntimeError("identity")
    members = []
    try:
        for entry in os.scandir("/proc"):
            if not entry.name.isdigit():
                continue
            pid = int(entry.name)
            try:
                observed = read_identity(pid)
                if observed[2] != EXPECTED_SESSION or not has_nonce(pid):
                    continue
                pidfd = os.pidfd_open(pid)
                repeated = read_identity(pid)
                if repeated[:4] != observed[:4] or not has_nonce(pid):
                    os.close(pidfd)
                    raise RuntimeError("identity")
                members.append((pid, pidfd, repeated))
            except (FileNotFoundError, ProcessLookupError, PermissionError):
                continue
        if not any(pid == EXPECTED_PID for pid, _pidfd, _observed in members):
            raise RuntimeError("identity")
        return members
    except Exception:
        for _pid, pidfd, _observed in members:
            os.close(pidfd)
        raise

def pidfd_exited(pidfd):
    poller = select.poll()
    poller.register(pidfd, select.POLLIN)
    return bool(poller.poll(0))

def signal_pinned(members, signal_number):
    for pid, pidfd, observed in sorted(members, reverse=True):
        if pidfd_exited(pidfd):
            continue
        repeated = read_identity(pid)
        if repeated[:4] != observed[:4] or not has_nonce(pid):
            raise RuntimeError("identity")
        signal.pidfd_send_signal(pidfd, signal_number)

def signal_verified(signal_number):
    members = verify_identity()
    try:
        signal_pinned(members, signal_number)
        return members
    except Exception:
        for _pid, pidfd, _observed in members:
            os.close(pidfd)
        raise

def wait_for_exit(members, seconds):
    poller = select.poll()
    for _pid, pidfd, _observed in members:
        poller.register(pidfd, select.POLLIN)
    deadline = time.monotonic() + seconds
    exited = set()
    while len(exited) < len(members):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False
        for fd, _event in poller.poll(max(1, int(remaining * 1000))):
            exited.add(fd)
            poller.unregister(fd)
    return True

term_members = signal_verified(signal.SIGTERM)
if wait_for_exit(term_members, 8):
    for _pid, pidfd, _observed in term_members:
        os.close(pidfd)
    raise SystemExit(0)
signal_pinned(term_members, signal.SIGKILL)
clean = wait_for_exit(term_members, 2)
for _pid, pidfd, _observed in term_members:
    os.close(pidfd)
raise SystemExit(0 if clean else 1)
"""
    return f"""# gate_snapshot_force_cleanup
set -Eeuo pipefail
timeout --signal=TERM --kill-after=2s {timeout_value}s python3 - <<'POKROV_SNAPSHOT_CLEANUP'
{helper}POKROV_SNAPSHOT_CLEANUP
"""


def _force_cleanup_exporter_identity(
    ssh: paramiko.SSHClient,
    identity: ExporterIdentity,
    *,
    timeout: float = 15,
) -> None:
    _remote_run(
        ssh,
        _snapshot_force_cleanup_command(identity, server_timeout=int(timeout)),
        error_class="snapshot_force_cleanup",
        timeout=float(timeout) + 3,
        max_output_bytes=64 * 1024,
    )


def _force_cleanup_snapshot_exporter(exporter: SnapshotExporter, *, timeout: float = 15) -> None:
    exporter.channel.close()
    _force_cleanup_exporter_identity(exporter.ssh, exporter.identity, timeout=timeout)


def _cleanup_failed_snapshot_open(
    ssh: paramiko.SSHClient,
    identity: ExporterIdentity | None,
    *,
    state: "RunState | None",
) -> None:
    if identity is None:
        if state is not None:
            state.snapshot_cleanup_outcome = "open_failed_identity_unavailable"
        return
    try:
        _force_cleanup_exporter_identity(ssh, identity, timeout=15)
    except GateError:
        if state is not None:
            state.snapshot_cleanup_outcome = "open_failed_force_cleanup_failed"
    else:
        if state is not None:
            state.snapshot_cleanup_outcome = "open_failed_force_killed"


def _settle_snapshot_exporter(
    exporter: SnapshotExporter,
    *,
    commit: bool,
    state: "RunState",
) -> GateError | None:
    action = "commit" if commit else "rollback"
    try:
        _close_snapshot_exporter(exporter, commit=commit, timeout=15)
    except GateError as close_error:
        try:
            _force_cleanup_snapshot_exporter(exporter, timeout=15)
            state.snapshot_cleanup_outcome = f"{action}_failed_force_killed"
        except GateError:
            state.snapshot_cleanup_outcome = f"{action}_failed_force_cleanup_failed"
        return close_error
    state.snapshot_cleanup_outcome = "committed" if commit else "rolled_back"
    return None


def _database_exists_command(database: str, *, marker: str) -> str:
    if not SQL_IDENTIFIER_RE.fullmatch(database):
        raise GateError("Invalid database existence check")
    return (
        f"# {marker}\nset -Eeuo pipefail\n"
        "runuser -u postgres -- psql --no-psqlrc --tuples-only --no-align "
        "--set=ON_ERROR_STOP=1 --dbname=postgres --command="
        + shlex.quote(f"SELECT 1 FROM pg_database WHERE datname = '{database}'")
    )


def _tools_preflight_command() -> str:
    tools = (
        "pg_dump pg_restore psql createdb dropdb openssl runuser nice ionice timeout "
        "stat sha256sum sync cut install mv rm setsid sleep sh python3 env"
    )
    return f"""# gate_tools_preflight
set -Eeuo pipefail
for tool in {tools}; do command -v "$tool" >/dev/null; done
test -x {shlex.quote(LIVE_VENV_PYTHON)}
test -r {shlex.quote(LIVE_ENV_PATH)}
setsid --wait sh -c 'exit 0'
python3 - <<'POKROV_PIDFD_PREFLIGHT'
import os
import signal
assert hasattr(os, "pidfd_open")
assert hasattr(signal, "pidfd_send_signal")
POKROV_PIDFD_PREFLIGHT"""


def _backup_metadata_command(backup_path: str) -> str:
    _, path = _validated_backup_path(backup_path)
    path_q = shlex.quote(path)
    return f"""# gate_backup_metadata
set -Eeuo pipefail
bytes=$(stat -c %s -- {path_q})
mode=$(stat -c %a -- {path_q})
digest=$(sha256sum -- {path_q} | cut -d ' ' -f 1)
printf '{{"bytes":%s,"sha256":"%s","mode":"%s"}}\n' "$bytes" "$digest" "$mode"
"""


def _reset_target_command(target: str) -> str:
    if not SQL_IDENTIFIER_RE.fullmatch(target) or not target.endswith("_rehearsal"):
        raise GateError("Invalid reset target")
    terminate = (
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
        f"WHERE datname = '{target}' AND pid <> pg_backend_pid()"
    )
    return (
        "# gate_reset_target\nset -Eeuo pipefail\n"
        "runuser -u postgres -- psql --no-psqlrc --set=ON_ERROR_STOP=1 --dbname=postgres --command="
        + shlex.quote(terminate)
        + " >/dev/null\n"
        + f"runuser -u postgres -- dropdb --if-exists -- {shlex.quote(target)}"
    )


def _create_target_command(target: str, *, source: str = "portal") -> str:
    if not SQL_IDENTIFIER_RE.fullmatch(target) or not target.endswith("_rehearsal"):
        raise GateError("Invalid create target")
    role_setup = _application_role_shell(source)
    acl_sql = (
        f"REVOKE ALL ON DATABASE {target} FROM PUBLIC;\n"
        'ALTER SCHEMA public OWNER TO :"role_name";\n'
        "REVOKE ALL ON SCHEMA public FROM PUBLIC;\n"
        'GRANT USAGE, CREATE ON SCHEMA public TO :"role_name";'
    )
    return (
        "# gate_create_target\nset -Eeuo pipefail\n"
        + role_setup
        + "\n"
        + f"runuser -u postgres -- createdb --owner=\"$role\" -- {shlex.quote(target)}\n"
        + f"printf '%s\\n' {shlex.quote(acl_sql)} | "
        + "runuser -u postgres -- psql --no-psqlrc --quiet --set=ON_ERROR_STOP=1 "
        + f"--set=role_name=\"$role\" --dbname={shlex.quote(target)}"
    )


def _partial_cleanup_command(backup_path: str) -> str:
    directory, path = _validated_backup_path(backup_path)
    partial_q = shlex.quote(path + ".partial")
    directory_q = shlex.quote(directory)
    return (
        f"# gate_partial_cleanup\nset -Eeuo pipefail\nrm -f -- {partial_q}\n"
        f"if test -d {directory_q}; then sync -f {directory_q}; fi\n"
        f"test ! -e {partial_q}"
    )


def _parse_json_object(raw: str, error_class: str) -> dict[str, Any]:
    try:
        value = json.loads(raw.strip())
    except (TypeError, ValueError):
        raise remote_error(f"{error_class}_json") from None
    if not isinstance(value, dict):
        raise remote_error(f"{error_class}_shape")
    assert_report_safe(value)
    return value


def _parse_integrity_evidence_stream(raw: str, error_class: str) -> dict[str, Any]:
    database_record: dict[str, Any] | None = None
    support_record: dict[str, Any] | None = None
    tables: list[dict[str, Any]] = []
    for line in str(raw or "").splitlines():
        candidate = line.strip()
        if not candidate:
            continue
        try:
            record = json.loads(candidate)
        except (TypeError, ValueError):
            raise remote_error(f"{error_class}_json") from None
        if not isinstance(record, dict):
            raise remote_error(f"{error_class}_shape")
        assert_report_safe(record)
        record_type = record.get("record_type")
        if record_type == "database":
            if database_record is not None or set(record) != {
                "record_type",
                "database_bytes",
                "public_table_count",
            }:
                raise remote_error(f"{error_class}_shape")
            database_record = {
                "database_bytes": record.get("database_bytes"),
                "public_table_count": record.get("public_table_count"),
            }
        elif record_type == "table":
            if set(record) != {"record_type", "name", "row_count"}:
                raise remote_error(f"{error_class}_shape")
            tables.append({"name": record.get("name"), "row_count": record.get("row_count")})
        elif record_type == "support":
            if support_record is not None:
                raise remote_error(f"{error_class}_shape")
            support_record = {key: value for key, value in record.items() if key != "record_type"}
        else:
            raise remote_error(f"{error_class}_shape")
    if database_record is None or support_record is None:
        raise remote_error(f"{error_class}_shape")
    return {
        **database_record,
        "tables": tables,
        "support_attachments": support_record,
    }


def _validate_backup_metadata(value: Mapping[str, Any]) -> dict[str, Any]:
    size = value.get("bytes")
    digest = value.get("sha256")
    mode = value.get("mode")
    if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
        raise remote_error("backup_metadata")
    if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
        raise remote_error("backup_metadata")
    if str(mode) != "600":
        raise remote_error("backup_permissions")
    return {"bytes": size, "sha256": digest, "mode": "0600"}


def _validate_target_role_evidence(value: Mapping[str, Any]) -> dict[str, Any]:
    expected = {
        "database_owner_is_app",
        "database_public_access_revoked",
        "public_schema_create",
        "schema_public_access_revoked",
        "public_objects_total",
        "public_objects_owned",
    }
    if set(value) != expected:
        raise remote_error("target_role_shape")
    if any(
        value.get(key) is not True
        for key in (
            "database_owner_is_app",
            "database_public_access_revoked",
            "public_schema_create",
            "schema_public_access_revoked",
        )
    ):
        raise remote_error("target_role_privileges")
    total = value.get("public_objects_total")
    owned = value.get("public_objects_owned")
    if (
        not isinstance(total, int)
        or isinstance(total, bool)
        or total <= 0
        or not isinstance(owned, int)
        or isinstance(owned, bool)
        or owned != total
    ):
        raise remote_error("target_role_ownership")
    return {
        "database_owner_is_app": True,
        "database_public_access_revoked": True,
        "public_schema_create": True,
        "schema_public_access_revoked": True,
        "public_objects_total": total,
        "public_objects_owned": owned,
    }


def _validate_integrity_evidence(value: Mapping[str, Any]) -> dict[str, Any]:
    database_bytes = value.get("database_bytes")
    table_count = value.get("public_table_count")
    tables = value.get("tables")
    support = value.get("support_attachments")
    if not isinstance(database_bytes, int) or isinstance(database_bytes, bool) or database_bytes < 0:
        raise remote_error("integrity_shape")
    if not isinstance(table_count, int) or isinstance(table_count, bool) or table_count < 0:
        raise remote_error("integrity_shape")
    if not isinstance(tables, list) or len(tables) != table_count:
        raise remote_error("integrity_shape")
    normalized_tables: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in tables:
        if not isinstance(item, dict) or set(item) != {"name", "row_count"}:
            raise remote_error("integrity_shape")
        name = item.get("name")
        count = item.get("row_count")
        if not isinstance(name, str) or not SQL_IDENTIFIER_RE.fullmatch(name) or name in seen:
            raise remote_error("integrity_shape")
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise remote_error("integrity_shape")
        seen.add(name)
        normalized_tables.append({"name": name, "row_count": count})
    normalized_tables.sort(key=lambda item: item["name"])
    if not isinstance(support, dict):
        raise GateError("support_evidence_unavailable")
    schema_status = support.get("schema_status")
    if schema_status == "available":
        if set(support) != {"schema_status", "total", "bound", "unbound", "dangling"}:
            raise GateError("support_evidence_invalid")
        normalized_support: dict[str, Any] = {"schema_status": "available"}
        for key in ("total", "bound", "unbound", "dangling"):
            count = support.get(key)
            if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                raise GateError("support_evidence_invalid")
            normalized_support[key] = count
        if normalized_support["total"] != (
            normalized_support["bound"] + normalized_support["unbound"] + normalized_support["dangling"]
        ):
            raise GateError("support_evidence_invalid")
    elif schema_status in {"legacy", "absent"}:
        if set(support) != {"schema_status", "total"}:
            raise GateError("support_evidence_invalid")
        total = support.get("total")
        if not isinstance(total, int) or isinstance(total, bool) or total < 0:
            raise GateError("support_evidence_invalid")
        if schema_status == "absent" and total != 0:
            raise GateError("support_evidence_invalid")
        normalized_support = {"schema_status": schema_status, "total": total}
    else:
        raise GateError("support_evidence_invalid")
    result = {
        "database_bytes": database_bytes,
        "public_table_count": table_count,
        "tables": normalized_tables,
        "support_attachments": normalized_support,
    }
    assert_report_safe(result)
    return result


def _support_ownership_status(evidence: Mapping[str, Any]) -> str:
    support = evidence.get("support_attachments")
    if not isinstance(support, Mapping):
        raise GateError("support_evidence_unavailable")
    schema_status = support.get("schema_status")
    if schema_status == "available":
        return "PASS" if support.get("dangling") == 0 else "FAIL_DANGLING_ATTACHMENTS"
    if schema_status == "legacy":
        return "LEGACY_SCHEMA_NOT_GATED"
    if schema_status == "absent":
        return "NOT_APPLICABLE_ABSENT"
    raise GateError("support_evidence_invalid")


def _assert_integrity_matches(source: Mapping[str, Any], target: Mapping[str, Any]) -> None:
    comparable = ("public_table_count", "tables", "support_attachments")
    if any(source.get(key) != target.get(key) for key in comparable):
        raise GateError("integrity_evidence_mismatch")


def _plan_report(source: str, target: str, backup_path: str, *, reset_target: bool) -> dict[str, Any]:
    report = {
        "status": "PLAN_ONLY",
        "mode": "plan",
        "backup_restore_status": "NOT_RUN",
        "support_ownership_status": "NOT_EVALUATED",
        "target_role_status": "NOT_RUN",
        "origin": "brain",
        "source_database": source,
        "target_database": target,
        "backup_path": backup_path,
        "reset_target": bool(reset_target),
        "operations": [
            "strict SSH host-key preflight",
            "encrypted custom-format backup with no plaintext dump",
            "encrypted archive list verification",
            "rehearsal target create and restore as the guarded live application role",
            "redacted target ownership evidence",
            "redacted exact-count integrity evidence",
        ],
        "mutation_performed": False,
    }
    assert_report_safe(report)
    return report


@dataclass
class RunState:
    backup_path: str
    phase: str = "local_preflight"
    backup_metadata: dict[str, Any] | None = None
    backup_retained: bool | str = False
    target_state: str = "not_checked"
    partial_cleanup_outcome: str = "not_attempted"
    snapshot_cleanup_outcome: str = "not_opened"
    support_ownership_status: str = "NOT_EVALUATED"
    target_role_status: str = "NOT_EVALUATED"


def _apply_gate(
    args: argparse.Namespace,
    *,
    source: str,
    target: str,
    backup_path: str,
    password: str,
    passphrase: str,
    state: RunState,
) -> dict[str, Any]:
    ssh: paramiko.SSHClient | None = None
    target_role_evidence: dict[str, Any] | None = None
    try:
        state.phase = "ssh_setup"
        try:
            ssh = paramiko.SSHClient()
            configure_ssh_host_key_policy(ssh, allow_trust_on_first_use=False)
        except Exception as exc:
            raise remote_error("ssh_setup", exc) from None
        state.phase = "ssh_connect"
        try:
            ssh.connect(
                args.brain_ip,
                port=args.ssh_port,
                username=args.ssh_user,
                password=password,
                timeout=30,
                banner_timeout=30,
                auth_timeout=30,
            )
        except Exception as exc:
            raise remote_error("ssh_connect", exc) from None

        try:
            state.phase = "remote_preflight"
            _remote_run(ssh, _tools_preflight_command(), error_class="preflight", timeout=60)
            state.phase = "source_check"
            source_exists = _remote_run(
                ssh,
                _database_exists_command(source, marker="gate_source_exists"),
                error_class="source_check",
                timeout=60,
            ).strip()
            if source_exists != "1":
                raise GateError("Source database does not exist")
            state.phase = "target_check"
            target_exists = _remote_run(
                ssh,
                _database_exists_command(target, marker="gate_target_exists"),
                error_class="target_check",
                timeout=60,
            ).strip()
            if target_exists not in {"", "1", "0"}:
                raise remote_error("target_check_shape")
            target_is_present = target_exists == "1"
            state.target_state = "preexisting_rehearsal" if target_is_present else "absent_not_created"
            if target_is_present and not args.reset_target:
                state.target_state = "preexisting_retained"
                raise GateError("Target database exists; explicit --reset-target is required")

            state.phase = "snapshot_export"
            snapshot_lifetime = min(
                MAX_SNAPSHOT_LIFETIME_SECONDS,
                int(args.evidence_timeout) + int(args.backup_timeout) + 120,
            )
            snapshot = _open_snapshot_exporter(
                ssh,
                source,
                timeout=60,
                server_timeout=snapshot_lifetime,
                state=state,
            )
            state.snapshot_cleanup_outcome = "active"
            snapshot_can_commit = False
            try:
                state.phase = "source_evidence"
                source_evidence = _validate_integrity_evidence(
                    _parse_integrity_evidence_stream(
                        _remote_run(
                            ssh,
                            build_integrity_evidence_command(
                                source,
                                snapshot_id=snapshot.snapshot_id,
                                server_timeout=args.evidence_timeout,
                            ),
                            error_class="source_integrity",
                            timeout=args.evidence_timeout + 15,
                        ),
                        "source_integrity",
                    )
                )
                state.support_ownership_status = _support_ownership_status(source_evidence)
                state.phase = "backup"
                state.backup_retained = "unknown"
                _remote_run(
                    ssh,
                    build_backup_command(
                        source,
                        backup_path,
                        snapshot_id=snapshot.snapshot_id,
                        server_timeout=args.backup_timeout,
                    ),
                    error_class="backup",
                    timeout=args.backup_timeout + 15,
                    secret_input=passphrase,
                )
                state.backup_retained = True
                snapshot_can_commit = True
            finally:
                if snapshot_can_commit:
                    state.phase = "snapshot_close"
                    close_error = _settle_snapshot_exporter(snapshot, commit=True, state=state)
                    if close_error is not None:
                        raise close_error
                else:
                    _settle_snapshot_exporter(snapshot, commit=False, state=state)

            state.phase = "backup_metadata"
            backup_metadata = _validate_backup_metadata(
                _parse_json_object(
                    _remote_run(
                        ssh,
                        _backup_metadata_command(backup_path),
                        error_class="backup_metadata",
                        timeout=60,
                    ),
                    "backup_metadata",
                )
            )
            state.backup_metadata = backup_metadata
            state.backup_retained = True
            state.phase = "backup_verify"
            _remote_run(
                ssh,
                build_verify_command(backup_path, server_timeout=args.verify_timeout),
                error_class="backup_verify",
                timeout=args.verify_timeout + 15,
                secret_input=passphrase,
            )

            if target_is_present:
                state.phase = "target_reset"
                state.target_state = "reset_in_progress"
                try:
                    _remote_run(
                        ssh,
                        _reset_target_command(target),
                        error_class="target_reset",
                        timeout=120,
                    )
                except Exception:
                    state.target_state = "reset_failed_unknown"
                    raise
                state.target_state = "absent_after_reset"
            state.phase = "target_create"
            try:
                _remote_run(
                    ssh,
                    _create_target_command(target, source=source),
                    error_class="target_create",
                    timeout=120,
                )
            except Exception:
                state.target_state = "create_failed_unknown"
                raise
            state.target_state = "created_empty_retained"
            state.phase = "target_restore"
            try:
                _remote_run(
                    ssh,
                    build_restore_command(
                        target,
                        backup_path,
                        source=source,
                        server_timeout=args.restore_timeout,
                    ),
                    error_class="target_restore",
                    timeout=args.restore_timeout + 15,
                    secret_input=passphrase,
                )
            except Exception:
                state.target_state = "restore_failed_retained"
                raise
            state.target_state = "restored_unverified_retained"
            state.phase = "target_role_evidence"
            try:
                target_role_evidence = _validate_target_role_evidence(
                    _parse_json_object(
                        _remote_run(
                            ssh,
                            build_target_role_evidence_command(source, target),
                            error_class="target_role_evidence",
                            timeout=75,
                        ),
                        "target_role_evidence",
                    )
                )
            except Exception:
                state.target_role_status = "FAIL"
                state.target_state = "restored_role_invalid_retained"
                raise
            state.target_role_status = "PASS"
            state.phase = "target_evidence"
            target_evidence = _validate_integrity_evidence(
                _parse_integrity_evidence_stream(
                    _remote_run(
                        ssh,
                        build_integrity_evidence_command(
                            target,
                            server_timeout=args.evidence_timeout,
                        ),
                        error_class="target_integrity",
                        timeout=args.evidence_timeout + 15,
                    ),
                    "target_integrity",
                )
            )
            state.phase = "integrity_compare"
            try:
                _assert_integrity_matches(source_evidence, target_evidence)
            except Exception:
                state.target_state = "integrity_mismatch_retained"
                raise
            state.target_state = "restored_retained"
            state.phase = "complete"
        except Exception:
            if state.backup_metadata is None and state.backup_retained == "unknown" and state.phase not in {
                "ssh_setup",
                "ssh_connect",
                "remote_preflight",
            }:
                try:
                    state.backup_metadata = _validate_backup_metadata(
                        _parse_json_object(
                            _remote_run(
                                ssh,
                                _backup_metadata_command(backup_path),
                                error_class="backup_probe",
                                timeout=30,
                            ),
                            "backup_probe",
                        )
                    )
                    state.backup_retained = True
                except GateError:
                    state.backup_retained = "unknown"
            try:
                _remote_run(
                    ssh,
                    _partial_cleanup_command(backup_path),
                    error_class="partial_cleanup",
                    timeout=30,
                )
                state.partial_cleanup_outcome = "removed_or_absent"
            except GateError:
                state.partial_cleanup_outcome = "failed"
            raise
    finally:
        if ssh is not None:
            try:
                ssh.close()
            except Exception:
                pass

    report = {
        "status": "PASS",
        "mode": "apply",
        "backup_restore_status": "PASS",
        "support_ownership_status": _support_ownership_status(source_evidence),
        "target_role_status": state.target_role_status,
        "origin": "brain",
        "source_database": source,
        "target_database": target,
        "backup": {"path": backup_path, **backup_metadata},
        "source_integrity": source_evidence,
        "target_integrity": target_evidence,
        "target_role_evidence": target_role_evidence,
        "target_was_reset": bool(target_is_present),
        "backup_retained": True,
        "target_retained": True,
        "mutation_performed": True,
        "target_state": state.target_state,
        "snapshot_cleanup_outcome": state.snapshot_cleanup_outcome,
    }
    assert_report_safe(report)
    return report


def _build_parser() -> argparse.ArgumentParser:
    parser = SafeArgumentParser(
        description="Fail-closed encrypted PostgreSQL backup and restore rehearsal gate on brain.",
        allow_abbrev=False,
    )
    parser.add_argument("--brain-ip", required=True)
    parser.add_argument("--ssh-user", default="root")
    parser.add_argument("--ssh-port", type=int, default=29374)
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--source-db", required=True)
    parser.add_argument("--confirm-source", required=True)
    parser.add_argument("--target-db", required=True)
    parser.add_argument("--confirm-target", required=True)
    parser.add_argument("--backup-dir", default=DEFAULT_BACKUP_DIRECTORY)
    parser.add_argument("--passphrase-env", default=DEFAULT_PASSPHRASE_ENV)
    parser.add_argument("--report", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--reset-target", action="store_true")
    parser.add_argument("--backup-timeout", type=int, default=3600)
    parser.add_argument("--verify-timeout", type=int, default=1800)
    parser.add_argument("--restore-timeout", type=int, default=5400)
    parser.add_argument("--evidence-timeout", type=int, default=3600)
    return parser


def _failure_code(exc: BaseException) -> str:
    if isinstance(exc, RemoteGateError):
        return str(exc)
    words = re.findall(r"[a-z0-9]+", str(exc).lower())
    return "_".join(words[:12])[:160] or "gate_refused"


def _write_failure_report(
    report_path: Path | None,
    *,
    source: str | None,
    target: str | None,
    exc: BaseException,
    state: RunState | None,
) -> None:
    try:
        if report_path is None or source is None or target is None or report_path.exists():
            return
        encrypted_backup: dict[str, Any] = {
            "path": state.backup_path if state is not None else "unallocated"
        }
        if state is not None and state.backup_metadata is not None:
            encrypted_backup.update(state.backup_metadata)
        report = {
            "status": "FAIL",
            "mode": "apply",
            "backup_restore_status": "FAIL",
            "support_ownership_status": (
                state.support_ownership_status if state is not None else "NOT_EVALUATED"
            ),
            "target_role_status": (
                state.target_role_status if state is not None else "NOT_EVALUATED"
            ),
            "origin": "brain",
            "source_database": source,
            "target_database": target,
            "error_class": _failure_code(exc),
            "phase": state.phase if state is not None else "local_preflight",
            "encrypted_backup": encrypted_backup,
            "backup_retained": state.backup_retained if state is not None else "unknown",
            "target_state": state.target_state if state is not None else "not_checked",
            "partial_cleanup_outcome": (
                state.partial_cleanup_outcome if state is not None else "not_attempted"
            ),
            "snapshot_cleanup_outcome": (
                state.snapshot_cleanup_outcome if state is not None else "not_opened"
            ),
        }
        write_report_atomic(report_path, report)
    except Exception:
        pass


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    source: str | None = None
    target: str | None = None
    report_path: Path | None = None
    state: RunState | None = None
    try:
        source, target = validate_database_selection(
            args.source_db,
            args.confirm_source,
            args.target_db,
            args.confirm_target,
        )
        backup_directory = validate_backup_directory(args.backup_dir)
        report_path = validate_report_path(args.report)
        if not ENV_NAME_RE.fullmatch(args.passphrase_env):
            raise GateError("Invalid --passphrase-env name")
        if not (1 <= args.ssh_port <= 65535):
            raise GateError("Invalid --ssh-port")
        for name in ("backup_timeout", "verify_timeout", "restore_timeout", "evidence_timeout"):
            if not 60 <= int(getattr(args, name)) <= 24 * 60 * 60:
                raise GateError(f"Invalid --{name.replace('_', '-')}")
        backup_path = f"{backup_directory}/{make_backup_basename(source)}"
        state = RunState(backup_path=backup_path)

        if not args.apply:
            report = _plan_report(source, target, backup_path, reset_target=args.reset_target)
            write_report_atomic(report_path, report)
            print(json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2))
            return 0

        passphrase = _require_passphrase(os.environ, args.passphrase_env)
        password = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_password(Path(args.passwords))
        if not password:
            raise GateError("Missing brain SSH credential")
        report = _apply_gate(
            args,
            source=source,
            target=target,
            backup_path=backup_path,
            password=password,
            passphrase=passphrase,
            state=state,
        )
        write_report_atomic(report_path, report)
        print(json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2))
        return 0
    except GateError as exc:
        if args.apply:
            _write_failure_report(report_path, source=source, target=target, exc=exc, state=state)
        raise SystemExit(str(exc)) from None
    except Exception as exc:
        generic = GateError(f"local_gate_failed_{type(exc).__name__.lower()}")
        if args.apply:
            _write_failure_report(report_path, source=source, target=target, exc=generic, state=state)
        raise SystemExit(str(generic)) from None


if __name__ == "__main__":
    raise SystemExit(main())
