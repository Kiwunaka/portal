from __future__ import annotations

import importlib.util
import base64
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from types import ModuleType


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_script(script_name: str) -> ModuleType:
    path = REPO_ROOT / "scripts" / script_name
    spec = importlib.util.spec_from_file_location(script_name.replace(".py", ""), path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_ci_check_artifacts_reports_forbidden_generated_files(tmp_path: Path) -> None:
    module = _load_script("ci_check_artifacts.py")

    (tmp_path / ".pytest_cache").mkdir()
    (tmp_path / "pkg" / "__pycache__").mkdir(parents=True)
    (tmp_path / "pkg" / "__pycache__" / "module.pyc").write_bytes(b"cache")
    (tmp_path / "portal_api_test_sample.db").write_text("", encoding="utf-8")
    (tmp_path / "portal_api_test_sample.db-journal").write_text("", encoding="utf-8")
    (tmp_path / "node_modules" / "__pycache__").mkdir(parents=True)

    violations = module._collect_artifact_violations(tmp_path)

    assert "Forbidden artifact directory exists: .pytest_cache/" in violations
    assert "Forbidden artifact directory exists: pkg/__pycache__/" in violations
    assert "Forbidden artifact file exists: pkg/__pycache__/module.pyc" in violations
    assert "Forbidden artifact file exists: portal_api_test_sample.db" in violations
    assert "Forbidden artifact file exists: portal_api_test_sample.db-journal" in violations
    assert all("node_modules" not in item for item in violations)


def test_ci_check_artifacts_scans_catalog_and_bot_handler_slices(tmp_path: Path) -> None:
    module = _load_script("ci_check_artifacts.py")
    (tmp_path / "copy").mkdir()
    (tmp_path / "portal_bot").mkdir()
    catalog = tmp_path / "copy" / "catalog.ru.json"
    handler = tmp_path / "portal_bot" / "bot_user_handlers.py"
    catalog.write_text('{"ru":"гарантированный результат"}', encoding="utf-8")
    handler.write_text('MESSAGE = "интернет без ограничений"\n', encoding="utf-8")

    scanned = module._public_copy_files(tmp_path)
    violations = module._collect_copy_violations(tmp_path)

    assert catalog in scanned
    assert handler in scanned
    assert f"Forbidden absolute claim found: {catalog.relative_to(tmp_path).as_posix()}:1" in violations
    assert f"Forbidden absolute claim found: {handler.relative_to(tmp_path).as_posix()}:1" in violations


def test_export_release_gate_snapshot_writes_dated_history_file(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    module = _load_script("export_release_gate_snapshot.py")
    report = tmp_path / "release_gate_report.md"
    history_dir = tmp_path / "history"
    report.write_text("# Gate\n\n- PASS\n", encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "export_release_gate_snapshot.py",
            "--report",
            str(report),
            "--history-dir",
            str(history_dir),
            "--stamp",
            "20260627",
        ],
    )

    assert module.main() == 0

    snapshot = history_dir / "release_gate_report_20260627.md"
    body = snapshot.read_text(encoding="utf-8")
    assert "# Weekly Release Gate Snapshot (20260627)" in body
    assert f"- Source report: `{report.resolve()}`" in body
    assert "# Gate" in body
    assert "[snapshot]" in capsys.readouterr().out


def test_audit_node_dns_matrix_writes_report_with_mocked_resolvers(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    module = _load_script("audit_node_dns_matrix.py")
    inventory = tmp_path / "inventory.md"
    inventory.write_text(
        "\n".join(
            [
                "| `pl` | paid | `203.0.113.10` |",
                "| `it` | paid | `203.0.113.20` |",
                "| `us` | paid | `203.0.113.30` |",
                "| `nl` | paid | `203.0.113.40` |",
                "| `free` | free | `203.0.113.50` |",
                "| `brain` | api | `203.0.113.60` |",
            ]
        ),
        encoding="utf-8",
    )
    out = tmp_path / "dns-matrix.json"

    def fake_run(cmd, capture_output, text, encoding, errors, check):
        host = cmd[1]
        host_ip = {
            "pl.pokrov.space": "203.0.113.10",
            "it.pokrov.space": "203.0.113.20",
            "us.pokrov.space": "203.0.113.30",
            "nl.pokrov.space": "203.0.113.40",
            "free.pokrov.space": "203.0.113.50",
            "pokrov.space": "203.0.113.60",
        }[host]
        stdout = f"Name: {host}\nAddress: {host_ip}\nAddress: 2001:db8::1\n"
        return subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "audit_node_dns_matrix.py",
            "--domain",
            "pokrov.space",
            "--inventory",
            str(inventory),
            "--include-brain",
            "--resolvers",
            "system,1.1.1.1",
            "--out",
            str(out),
        ],
    )

    assert module.main() == 0

    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["domain"] == "pokrov.space"
    assert report["resolvers"] == ["system", "1.1.1.1"]
    assert set(report["matrix"]) == {"system", "1.1.1.1"}
    system_hosts = report["matrix"]["system"]["hosts"]
    assert [row["code"] for row in system_hosts] == ["pl", "it", "us", "nl", "free", "brain"]
    assert all(row["warnings"] == ["has_aaaa_records"] for row in system_hosts)
    assert "Report saved:" in capsys.readouterr().out


def test_backup_portal_db_fails_closed_without_required_ssh_env(monkeypatch) -> None:
    module = _load_script("backup_portal_db.py")
    monkeypatch.delenv("SSH_HOST", raising=False)
    monkeypatch.delenv("SSH_PASS", raising=False)
    monkeypatch.setattr(sys, "argv", ["backup_portal_db.py", "--out", "ignored.db"])

    try:
        module.main()
    except SystemExit as exc:
        assert str(exc) == "Missing required env var: SSH_HOST"
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("backup_portal_db.py should fail before opening SSH without SSH_HOST")


def test_inspect_local_xui_db_prints_public_inbound_shape_without_private_key(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    module = _load_script("inspect_local_xui_db.py")
    db_path = tmp_path / "x-ui.db"
    private_key = base64.urlsafe_b64encode(bytes(range(1, 33))).decode("ascii").rstrip("=")
    stream_settings = {
        "network": "tcp",
        "security": "reality",
        "realitySettings": {
            "dest": "www.microsoft.com:443",
            "serverNames": ["www.microsoft.com"],
            "shortIds": ["abcd"],
            "privateKey": private_key,
        },
    }
    con = sqlite3.connect(db_path)
    try:
        con.execute(
            "create table inbounds (id integer, port integer, protocol text, remark text, enable integer, stream_settings text)"
        )
        con.execute(
            "insert into inbounds values (?, ?, ?, ?, ?, ?)",
            (7, 443, "vless", "main", 1, json.dumps(stream_settings)),
        )
        con.commit()
    finally:
        con.close()

    monkeypatch.setattr(sys, "argv", ["inspect_local_xui_db.py", "--db", str(db_path)])

    assert module.main() == 0

    output = capsys.readouterr().out
    parsed = json.loads(output)
    inbound = parsed["inbounds"][0]
    assert inbound["id"] == 7
    assert inbound["port"] == 443
    assert inbound["security"] == "reality"
    assert inbound["server_names"] == ["www.microsoft.com"]
    assert inbound["public_key"]
    assert private_key not in output
    assert "privateKey" not in output


def test_list_nodes_fails_closed_for_missing_explicit_db() -> None:
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "list_nodes.py"), "--db", "missing-portal.db"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    assert proc.returncode != 0
    assert "DB not found: missing-portal.db" in (proc.stdout + proc.stderr)


def test_seed_nodes_from_facts_seeds_without_storing_panel_credentials(tmp_path: Path) -> None:
    db_path = tmp_path / "portal.db"
    facts_path = tmp_path / "node_facts.json"
    reality_path = tmp_path / "node_reality.json"
    facts_path.write_text(
        json.dumps(
            {
                "results": [
                    {
                        "code": "pl",
                        "ip": "203.0.113.10",
                        "panel_port": 2053,
                        "panel_path": "panel",
                        "panel_user": "operator",
                        "panel_pass": "secret",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    reality_path.write_text(
        json.dumps(
            {
                "results": [
                    {
                        "code": "pl",
                        "vless_port": 443,
                        "reality_sni": "www.microsoft.com",
                        "reality_pbk": "public",
                        "reality_sid": "abcd",
                        "inbound_id": 3,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"

    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "seed_nodes_from_facts.py"),
            "--node-facts",
            str(facts_path),
            "--node-reality",
            str(reality_path),
            "--only",
            "pl",
            "--host-mode",
            "dns",
            "--host-suffix",
            ".pokrov.space",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "OK: seeded nodes: pl" in proc.stdout
    assert "panel credentials were NOT stored" in proc.stdout

    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "select code, name, host, panel_base_url, panel_user, panel_pass, inbound_id, enabled from nodes"
        ).fetchone()
    finally:
        con.close()

    assert row == ("pl", "Poland", "pl.pokrov.space", "http://203.0.113.10:2053", "", "", 3, 1)


def _create_minimal_users_table(db_path: Path) -> None:
    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            create table users (
              tg_id integer primary key,
              uuid text unique,
              email text,
              sub_type text,
              created_at text,
              expiry_at text,
              is_active integer,
              stars_paid integer,
              total_gb integer,
              trial_used integer,
              username text,
              referrer_id integer,
              referral_count integer,
              tos_accepted integer,
              first_purchase_done integer,
              referral_code text,
              sub_token text
            )
            """.strip()
        )
        con.commit()
    finally:
        con.close()


def test_add_manual_users_inserts_negative_id_users_with_tokens(
    tmp_path: Path, monkeypatch
) -> None:
    module = _load_script("add_manual_users.py")
    db_path = tmp_path / "portal.db"
    _create_minimal_users_table(db_path)
    monkeypatch.setattr(sys, "argv", ["add_manual_users.py", "--db", str(db_path), "--days", "21"])

    assert module.main() == 0

    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "select tg_id, email, uuid, sub_type, is_active, tos_accepted, first_purchase_done, sub_token from users order by tg_id"
        ).fetchall()
    finally:
        con.close()

    assert [row[0] for row in rows] == [-10004, -10003, -10002, -10001]
    assert {row[1] for row in rows} == {"Admin", "RODITELI", "User_1808391444", "User_5187992322"}
    assert all(row[3] == "manual" for row in rows)
    assert all(row[4] == 1 for row in rows)
    assert all(row[5] == 1 for row in rows)
    assert all(row[6] == 1 for row in rows)
    assert all(row[7] for row in rows)
    assert len({row[7] for row in rows}) == 4


def test_export_manual_user_links_writes_only_token_backed_secret_urls(
    tmp_path: Path, monkeypatch
) -> None:
    module = _load_script("export_manual_user_links.py")
    db_path = tmp_path / "portal.db"
    out_path = tmp_path / "manual-users.txt"
    _create_minimal_users_table(db_path)
    con = sqlite3.connect(db_path)
    try:
        con.executemany(
            "insert into users (tg_id, uuid, email, sub_token) values (?, ?, ?, ?)",
            [
                (-2, "uuid-2", "Needs Space", "tok-space"),
                (-1, "uuid-1", "NoToken", ""),
                (100, "uuid-real", "Real", "tok-real"),
            ],
        )
        con.commit()
    finally:
        con.close()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "export_manual_user_links.py",
            "--db",
            str(db_path),
            "--domain",
            "connect.pokrov.space",
            "--port",
            "443",
            "--out",
            str(out_path),
        ],
    )

    assert module.main() == 0

    body = out_path.read_text(encoding="utf-8")
    assert "# Manual users subscription URLs for connect.pokrov.space:443" in body
    assert "Treat as secrets" in body
    assert "Needs Space (tg_id=-2)" in body
    assert "https://connect.pokrov.space:443/s8Kx2mP7qR4wT/tok-space#Needs%20Space" in body
    assert "NoToken" not in body
    assert "tok-real" not in body


def test_grant_all_users_days_activates_every_user_without_changing_identity_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    module = _load_script("grant_all_users_days.py")
    db_path = tmp_path / "portal.db"
    _create_minimal_users_table(db_path)
    con = sqlite3.connect(db_path)
    try:
        con.executemany(
            "insert into users (tg_id, uuid, email, sub_type, expiry_at, is_active, sub_token) values (?, ?, ?, ?, ?, ?, ?)",
            [
                (1, "uuid-1", "one@example.test", "trial_premium", "2020-01-01 00:00:00", 0, "tok-1"),
                (2, "uuid-2", "two@example.test", "paid_unlimited", "2020-01-01 00:00:00", 1, "tok-2"),
            ],
        )
        con.commit()
    finally:
        con.close()
    monkeypatch.setattr(sys, "argv", ["grant_all_users_days.py", "--db", str(db_path), "--days", "5"])

    assert module.main() == 0

    assert "OK: users_total=2 users_active=2 expiry_at_utc=" in capsys.readouterr().out
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "select tg_id, uuid, sub_type, is_active, sub_token, expiry_at from users order by tg_id"
        ).fetchall()
    finally:
        con.close()

    assert rows[0][:5] == (1, "uuid-1", "trial_premium", 1, "tok-1")
    assert rows[1][:5] == (2, "uuid-2", "paid_unlimited", 1, "tok-2")
    assert all(row[5] != "2020-01-01 00:00:00" for row in rows)


class _FakeUrlResponse:
    def __init__(self, body: str) -> None:
        self._body = body.encode("utf-8")

    def read(self) -> bytes:
        return self._body


def _create_subscription_user_db(db_path: Path, token: str | None = "secret-token") -> None:
    con = sqlite3.connect(db_path)
    try:
        con.execute("create table users (sub_token text, is_active integer, created_at text)")
        con.execute(
            "insert into users (sub_token, is_active, created_at) values (?, 1, '2026-01-01 00:00:00')",
            (token,),
        )
        con.commit()
    finally:
        con.close()


def test_inspect_public_subscription_hosts_extracts_hosts_without_printing_token(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    module = _load_script("inspect_public_subscription_hosts.py")
    db_path = tmp_path / "portal.db"
    _create_subscription_user_db(db_path)
    subscription = "\n".join(
        [
            "vless://uuid@pl.pokrov.space:443?type=tcp#PL",
            "vless://uuid@it.pokrov.space:443?type=tcp#IT",
            "vless://uuid@pl.pokrov.space:443?type=tcp#PL-dup",
        ]
    )
    encoded = base64.b64encode(subscription.encode("utf-8")).decode("ascii")

    def fake_urlopen(url, context, timeout):
        assert url == "https://api.pokrov.space/s8Kx2mP7qR4wT/secret-token"
        return _FakeUrlResponse(encoded)

    monkeypatch.setattr(module.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(
        sys,
        "argv",
        ["inspect_public_subscription_hosts.py", "--db", str(db_path)],
    )

    assert module.main() == 0

    output = capsys.readouterr().out
    assert output.splitlines() == ["it.pokrov.space", "pl.pokrov.space"]
    assert "secret-token" not in output


def test_inspect_public_subscription_names_extracts_decoded_fragments_and_fails_closed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    module = _load_script("inspect_public_subscription_names.py")
    db_path = tmp_path / "portal.db"
    _create_subscription_user_db(db_path)
    subscription = "\n".join(
        [
            "vless://uuid@pl.pokrov.space:443?type=tcp#Poland%20Premium",
            "vless://uuid@it.pokrov.space:443?type=tcp#Italy",
        ]
    )
    encoded = base64.b64encode(subscription.encode("utf-8")).decode("ascii")
    monkeypatch.setattr(module.urllib.request, "urlopen", lambda *args, **kwargs: _FakeUrlResponse(encoded))
    monkeypatch.setattr(
        sys,
        "argv",
        ["inspect_public_subscription_names.py", "--db", str(db_path)],
    )

    assert module.main() == 0
    assert capsys.readouterr().out.splitlines() == ["Poland Premium", "Italy"]

    empty_db = tmp_path / "empty.db"
    _create_subscription_user_db(empty_db, token=None)
    monkeypatch.setattr(sys, "argv", ["inspect_public_subscription_names.py", "--db", str(empty_db)])
    try:
        module.main()
    except SystemExit as exc:
        assert str(exc) == "No active user with sub_token found in DB."
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("expected inspect_public_subscription_names.py to fail without a token")


def test_api_lifecycle_smoke_runs_default_unittest_target_and_relays_output(
    monkeypatch, capsys
) -> None:
    module = _load_script("api_lifecycle_smoke.py")
    calls: list[dict[str, object]] = []

    def fake_run(**kwargs):
        calls.append(kwargs)
        return subprocess.CompletedProcess(kwargs["args"], 0, stdout="lifecycle ok\n", stderr="")

    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda args, **kwargs: fake_run(args=args, **kwargs),
    )
    monkeypatch.setattr(sys, "argv", ["api_lifecycle_smoke.py"])

    assert module.main() == 0

    assert calls[0]["args"] == [
        sys.executable,
        "-m",
        "unittest",
        module.DEFAULT_TARGET,
    ]
    assert calls[0]["cwd"] == str(module.REPO_ROOT)
    assert "lifecycle ok" in capsys.readouterr().out


def test_lavatop_webhook_replay_smoke_dry_run_and_live_key_guard(
    monkeypatch, capsys
) -> None:
    module = _load_script("lavatop_webhook_replay_smoke.py")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lavatop_webhook_replay_smoke.py",
            "--order-id",
            "order-123",
            "--plan-code",
            "start_99",
            "--amount",
            "150",
            "--currency",
            "rub",
        ],
    )

    assert module.main() == 0

    dry_run = json.loads(capsys.readouterr().out)
    assert dry_run["dry_run"] is True
    assert dry_run["url"] == "http://127.0.0.1:8080/api/payments/result/lavatop"
    assert dry_run["payload"]["eventType"] == "payment.success"
    assert dry_run["payload"]["amount"] == 150.0
    assert dry_run["payload"]["currency"] == "RUB"
    assert dry_run["payload"]["clientUtm"]["utm_content"] == "order-123"

    monkeypatch.delenv("LAVATOP_WEBHOOK_API_KEY", raising=False)
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavatop_webhook_replay_smoke.py", "--order-id", "order-123", "--live"],
    )

    assert module.main() == 2
    assert "LAVATOP_WEBHOOK_API_KEY is required for replay" in capsys.readouterr().err
