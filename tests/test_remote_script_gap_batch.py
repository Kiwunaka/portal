from __future__ import annotations

import importlib.util
import base64
import io
import json
import shlex
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def _load_script(script_name: str) -> ModuleType:
    path = SCRIPTS_DIR / script_name
    spec = importlib.util.spec_from_file_location(script_name.replace(".py", ""), path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class _FakeChannel:
    def __init__(self, code: int = 0) -> None:
        self._code = code

    def recv_exit_status(self) -> int:
        return self._code


class _FakeStream:
    def __init__(self, text: str = "ok", code: int = 0) -> None:
        self.channel = _FakeChannel(code)
        self._text = text

    def read(self) -> bytes:
        return self._text.encode("utf-8")


class _FakeSSH:
    def __init__(
        self,
        files: dict[str, bytes] | None = None,
        command_outputs: dict[str, tuple[int, str, str]] | None = None,
    ) -> None:
        self.commands: list[str] = []
        self.connect_kwargs: dict[str, object] = {}
        self.files = files if files is not None else {}
        self.dirs: set[str] = {"/"}
        self.command_outputs = command_outputs or {}
        self.closed = False
        self.sftp_closed = False

    def load_system_host_keys(self) -> None:
        pass

    def load_host_keys(self, _path: str) -> None:
        pass

    def set_missing_host_key_policy(self, _policy) -> None:
        pass

    def connect(self, host: str | None = None, **kwargs) -> None:
        self.connect_kwargs = {"host": host or kwargs.get("hostname"), **kwargs}

    def exec_command(self, cmd: str, timeout: int):
        self.commands.append(cmd)
        code, out, err = self.command_outputs.get(cmd, (0, f"ok:{cmd}", ""))
        return None, _FakeStream(out, code), _FakeStream(err)

    def open_sftp(self):
        return _FakeSFTP(self)

    def close(self) -> None:
        self.closed = True


class _FakeSFTPFile:
    def __init__(self, ssh: _FakeSSH, path: str, mode: str) -> None:
        self._ssh = ssh
        self._path = path
        self._mode = mode
        initial = b"" if "w" in mode else ssh.files.get(path, b"")
        self._buffer = io.BytesIO(initial)

    def __enter__(self):
        return self

    def __exit__(self, *_exc) -> None:
        self.close()

    def read(self) -> bytes:
        return self._buffer.getvalue()

    def write(self, data) -> None:
        if isinstance(data, str):
            data = data.encode("utf-8")
        self._buffer = io.BytesIO(data)

    def close(self) -> None:
        if "w" in self._mode or "+" in self._mode:
            self._ssh.files[self._path] = self._buffer.getvalue()


class _FakeSFTP:
    def __init__(self, ssh: _FakeSSH) -> None:
        self._ssh = ssh

    def file(self, path: str, mode: str):
        if "r" in mode and path not in self._ssh.files:
            raise IOError(path)
        return _FakeSFTPFile(self._ssh, path, mode)

    def stat(self, path: str):
        if path in self._ssh.dirs or path in self._ssh.files:
            return object()
        raise IOError(path)

    def mkdir(self, path: str) -> None:
        self._ssh.dirs.add(path)

    def put(self, local_path: str, remote_path: str) -> None:
        self._ssh.files[remote_path] = Path(local_path).read_bytes()

    def chmod(self, _path: str, _mode: int) -> None:
        pass

    def close(self) -> None:
        self._ssh.sftp_closed = True


def _install_fake_ssh(
    module: ModuleType,
    monkeypatch,
    files: dict[str, bytes] | None = None,
    command_outputs: dict[str, tuple[int, str, str]] | None = None,
) -> _FakeSSH:
    fake = _FakeSSH(files, command_outputs)
    monkeypatch.setattr(module.paramiko, "SSHClient", lambda: fake)
    monkeypatch.setattr(module.paramiko, "AutoAddPolicy", lambda: object())
    monkeypatch.setenv("NODE_PASS_BRAIN", "brain-secret")
    return fake


@pytest.mark.parametrize(
    ("script_name", "expected_fragments"),
    [
        (
            "remote_brain_cat_default_xui.py",
            ["cat /etc/default/x-ui", "head -60 /usr/local/x-ui/x-ui.sh"],
        ),
        (
            "remote_grep_brain_xui_sh.py",
            ["grep -n '2096'", "grep -ni 'sub'", "subport\\|subPort\\|SUB"],
        ),
        (
            "remote_xui_help_brain.py",
            ["/usr/local/x-ui/x-ui -h", "/usr/local/x-ui/x-ui run -h", "setting -show true"],
        ),
        (
            "remote_xui_logs.py",
            ["systemctl status x-ui", "journalctl -u x-ui", "ss -tlnp"],
        ),
        (
            "remote_xui_db_tables_brain.py",
            ["sqlite_master where type='table'", "select key,value from settings", "pragma table_info(users)"],
        ),
        (
            "remote_xui_setting_show.py",
            ["/usr/local/x-ui/x-ui setting -show true"],
        ),
        (
            "remote_xui_settings_brain.py",
            ["select key,value from settings order by key"],
        ),
        (
            "remote_brain_inspect_xui_files.py",
            ["find /etc/x-ui", "systemctl cat x-ui", "grep -R --line-number"],
        ),
        (
            "remote_find_panel_service.py",
            ["systemctl list-unit-files", "ls -la /usr/local/x-ui", "ps aux", "ss -tlnp"],
        ),
    ],
)
def test_read_only_remote_xui_diagnostics_use_env_password_and_expected_commands(
    script_name: str, expected_fragments: list[str], monkeypatch
) -> None:
    module = _load_script(script_name)
    fake = _install_fake_ssh(module, monkeypatch)

    assert module.main() == 0

    assert fake.closed is True
    assert fake.connect_kwargs["host"] == "82.21.114.104"
    assert fake.connect_kwargs["port"] == 29374
    assert fake.connect_kwargs["username"] == "root"
    assert fake.connect_kwargs["password"] == "brain-secret"
    joined = "\n".join(fake.commands)
    for fragment in expected_fragments:
        assert fragment in joined
    assert "rm -rf" not in joined
    assert "reboot" not in joined
    assert "brain-secret" not in joined


def test_remote_check_brain_panel_fails_closed_when_facts_have_no_brain_entry(
    tmp_path: Path, monkeypatch
) -> None:
    module = _load_script("remote_check_brain_panel.py")
    facts = tmp_path / "node_facts.json"
    facts.write_text(json.dumps({"results": []}), encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["remote_check_brain_panel.py", "--facts", str(facts)],
    )

    with pytest.raises(SystemExit) as exc:
        module.main()

    assert "node_facts file has no brain entry:" in str(exc.value)


def test_remote_check_brain_panel_uses_explicit_facts_for_local_panel_probe(
    tmp_path: Path, monkeypatch
) -> None:
    module = _load_script("remote_check_brain_panel.py")
    facts = tmp_path / "node_facts.json"
    facts.write_text(
        json.dumps({"results": [{"code": "brain", "panel_port": 2096, "panel_path": "panel-path"}]}),
        encoding="utf-8",
    )
    fake = _install_fake_ssh(module, monkeypatch)
    monkeypatch.setattr(
        sys,
        "argv",
        ["remote_check_brain_panel.py", "--facts", str(facts)],
    )

    assert module.main() == 0

    joined = "\n".join(fake.commands)
    assert "systemctl is-active x-ui" in joined
    assert "grep -E ':2096\\b'" in joined
    assert "http://127.0.0.1:2096/" in joined
    assert "http://127.0.0.1:2096/panel-path/login" in joined
    assert fake.closed is True


def test_remote_brain_set_env_kv_updates_remote_env_and_restarts_without_printing_secret(
    monkeypatch, capsys
) -> None:
    module = _load_script("remote_brain_set_env_kv.py")
    files = {"/root/portal_bot/.env": b"EXISTING=1\nSECRET=old\n"}
    fake = _install_fake_ssh(module, monkeypatch, files)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "remote_brain_set_env_kv.py",
            "--brain-ip",
            "82.21.114.104",
            "--key",
            "SECRET",
            "--value",
            "new-secret",
            "--restart",
            "portal-api,portal-bot",
        ],
    )

    assert module.main() == 0

    assert fake.files["/root/portal_bot/.env"].decode("utf-8") == "EXISTING=1\nSECRET=new-secret\n"
    joined = "\n".join(fake.commands)
    assert "systemctl restart portal-api" in joined
    assert "systemctl is-active portal-bot" in joined
    output = capsys.readouterr().out
    assert "portal-api:" in output
    assert "new-secret" not in output
    assert "new-secret" not in joined
    assert fake.sftp_closed is True
    assert fake.closed is True


def test_remote_brain_copy_env_var_copies_existing_value_without_printing_it(monkeypatch, capsys) -> None:
    module = _load_script("remote_brain_copy_env_var.py")
    files = {"/root/portal_bot/.env": b"SRC_TOKEN=sensitive-token\nDST_TOKEN=old\n"}
    fake = _install_fake_ssh(module, monkeypatch, files)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "remote_brain_copy_env_var.py",
            "--brain-ip",
            "82.21.114.104",
            "--src",
            "SRC_TOKEN",
            "--dst",
            "DST_TOKEN",
            "--restart",
            "portal-api",
        ],
    )

    assert module.main() == 0

    updated = fake.files["/root/portal_bot/.env"].decode("utf-8")
    assert updated == "SRC_TOKEN=sensitive-token\nDST_TOKEN=sensitive-token\n"
    output = capsys.readouterr().out
    assert "portal-api:" in output
    assert "sensitive-token" not in output
    assert "sensitive-token" not in "\n".join(fake.commands)


def test_remote_brain_update_env_urls_rewrites_public_urls_and_keeps_secrets_off_stdout(
    monkeypatch, capsys
) -> None:
    module = _load_script("remote_brain_update_env_urls.py")
    files = {"/root/portal_bot/.env": b"PUBLIC_API_BASE_URL=http://old\nWEBAPP_URL=http://old\n"}
    fake = _install_fake_ssh(module, monkeypatch, files)
    monkeypatch.setenv("TELEGRAM_OAUTH_CLIENT_ID", "client-id")
    monkeypatch.setenv("TELEGRAM_OAUTH_REDIRECT_URI", "https://app.pokrov.space/oauth")
    monkeypatch.setenv("TELEGRAM_OAUTH_CLIENT_SECRET", "oauth-secret")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "remote_brain_update_env_urls.py",
            "--brain-ip",
            "82.21.114.104",
            "--api-domain",
            "api.pokrov.space",
            "--web-domain",
            "pokrov.space",
        ],
    )

    assert module.main() == 0

    updated = fake.files["/root/portal_bot/.env"].decode("utf-8")
    assert "PUBLIC_API_BASE_URL=https://api.pokrov.space" in updated
    assert "WEBAPP_URL=https://app.pokrov.space/" in updated
    assert "PUBLIC_API_DOMAIN=api.pokrov.space" in updated
    assert "PUBLIC_WEB_DOMAIN=pokrov.space" in updated
    assert "HOST_DOMAIN=api.pokrov.space" in updated
    assert "TELEGRAM_OAUTH_CLIENT_ID=client-id" in updated
    assert "TELEGRAM_OAUTH_REDIRECT_URI=https://app.pokrov.space/oauth" in updated
    assert "TELEGRAM_OAUTH_CLIENT_SECRET=oauth-secret" in updated
    joined = "\n".join(fake.commands)
    assert "systemctl restart portal-api" in joined
    assert "oauth-secret" not in joined
    assert "oauth-secret" not in capsys.readouterr().out


def test_remote_brain_patch_caddy_webapp_api_proxy_writes_expected_caddyfile(
    monkeypatch, capsys
) -> None:
    module = _load_script("remote_brain_patch_caddy_webapp_api_proxy.py")
    fake = _install_fake_ssh(module, monkeypatch, {})
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "remote_brain_patch_caddy_webapp_api_proxy.py",
            "--brain-ip",
            "82.21.114.104",
            "--domain",
            "pokrov.space",
            "--api-upstream",
            "127.0.0.1:8080",
        ],
    )

    assert module.main() == 0

    caddyfile = fake.files["/etc/caddy/Caddyfile"].decode("utf-8")
    assert "pokrov.space:8444" in caddyfile
    assert "handle /api/*" in caddyfile
    assert "reverse_proxy 127.0.0.1:8080" in caddyfile
    assert "handle_path /webapp/*" in caddyfile
    assert "pokrov.space:2096" in caddyfile
    joined = "\n".join(fake.commands)
    assert "systemctl restart caddy" in joined
    assert "--resolve pokrov.space:8444:127.0.0.1" in joined
    assert "https://pokrov.space:8444/api/health" in joined
    assert "ok:curl" in capsys.readouterr().out


def test_remote_deploy_brain_caddy_config_validates_backs_up_installs_and_reloads(monkeypatch, capsys) -> None:
    module = _load_script("remote_deploy_brain_caddy_config.py")
    fake = _FakeSSH()
    monkeypatch.setattr(module, "connect_node", lambda **_kwargs: (fake, "env"))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "remote_deploy_brain_caddy_config.py",
            "--brain-ip",
            "82.21.114.104",
        ],
    )

    assert module.main() == 0

    uploaded_paths = [path for path in fake.files if path.startswith("/tmp/pokrov-caddy-")]
    assert len(uploaded_paths) == 1
    assert b"auto_https disable_redirects" in fake.files[uploaded_paths[0]]
    joined = "\n".join(fake.commands)
    assert f"caddy validate --adapter caddyfile --config {shlex.quote(uploaded_paths[0])}" in joined
    assert "cp -a /etc/caddy/Caddyfile /etc/caddy/Caddyfile.bak-" in joined
    assert f"install -m 0644 {shlex.quote(uploaded_paths[0])} /etc/caddy/Caddyfile" in joined
    assert "caddy validate --adapter caddyfile --config /etc/caddy/Caddyfile" in joined
    assert "systemctl reload caddy || systemctl restart caddy" in joined
    assert "Caddyfile\\.bak\\-[0-9]{14}" in joined
    assert "head -n -5" in joined
    assert 'rm -f -- "$root/$name"' in joined
    assert "rm -f" in joined
    assert fake.closed is True
    assert "brain caddy config deployed:" in capsys.readouterr().out


def test_remote_install_feedbackbot_service_writes_expected_systemd_unit(monkeypatch, capsys) -> None:
    module = _load_script("remote_install_feedbackbot_service.py")
    fake = _install_fake_ssh(module, monkeypatch, {})
    monkeypatch.setattr(
        sys,
        "argv",
        ["remote_install_feedbackbot_service.py", "--brain-ip", "82.21.114.104"],
    )

    assert module.main() == 0

    service = fake.files["/etc/systemd/system/portal-feedbackbot.service"].decode("utf-8")
    assert "Description=Portal feedback bot (Telegram)" in service
    assert "WorkingDirectory=/root/portal_bot" in service
    assert "EnvironmentFile=-/root/portal_bot/.env" in service
    assert "ExecStart=/root/portal_bot/venv/bin/python /root/portal_bot/feedbackbot.py" in service
    joined = "\n".join(fake.commands)
    assert "test -e /root/portal_bot/feedbackbot.py" in joined
    assert "test -e /root/portal_bot/venv/bin/python" in joined
    assert "systemctl daemon-reload" in joined
    assert "systemctl enable portal-feedbackbot" in joined
    assert "systemctl restart portal-feedbackbot" in joined
    assert "portal-feedbackbot:" in capsys.readouterr().out
    assert fake.sftp_closed is True
    assert fake.closed is True


def test_remote_install_node_metrics_timer_writes_service_timer_and_optional_run_now(
    monkeypatch, capsys
) -> None:
    module = _load_script("remote_install_node_metrics_timer.py")
    fake = _install_fake_ssh(module, monkeypatch, {})
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "remote_install_node_metrics_timer.py",
            "--brain-ip",
            "82.21.114.104",
            "--workdir",
            "/opt/pokrov",
            "--collector-cmd",
            "/opt/pokrov/venv/bin/python /opt/pokrov/collect_node_metrics.py",
            "--run-now",
        ],
    )

    assert module.main() == 0

    service = fake.files["/etc/systemd/system/portal-node-metrics.service"].decode("utf-8")
    timer = fake.files["/etc/systemd/system/portal-node-metrics.timer"].decode("utf-8")
    assert "WorkingDirectory=/opt/pokrov" in service
    assert "ExecStart=/opt/pokrov/venv/bin/python /opt/pokrov/collect_node_metrics.py" in service
    assert "OnUnitActiveSec=60s" in timer
    joined = "\n".join(fake.commands)
    assert "systemctl enable portal-node-metrics.timer" in joined
    assert "systemctl restart portal-node-metrics.timer" in joined
    assert "systemctl start portal-node-metrics.service" in joined
    assert "node_health_samples" in joined
    assert "timer=" in capsys.readouterr().out


def test_remote_start_brain_bot_reloads_enables_restarts_and_reports_state(monkeypatch, capsys) -> None:
    module = _load_script("remote_start_brain_bot.py")
    fake = _install_fake_ssh(module, monkeypatch, {})
    monkeypatch.setattr(sys, "argv", ["remote_start_brain_bot.py", "--brain-ip", "82.21.114.104"])

    assert module.main() == 0

    assert fake.commands == [
        "systemctl daemon-reload",
        "systemctl enable portal-bot",
        "systemctl restart portal-bot",
        "systemctl is-active portal-bot || true",
    ]
    assert "ok:systemctl is-active portal-bot" in capsys.readouterr().out
    assert fake.closed is True


def test_remote_install_node_observer_render_helpers_keep_secret_scoped_to_env() -> None:
    module = _load_script("remote_install_node_observer.py")

    service = module._render_service(workdir="/opt/observer")
    env = module._render_env(
        api_url="https://api.pokrov.space/api/internal/observer/batches",
        node_code="PL",
        secret="observer-secret",
        log_path="/var/log/xray/access.log",
        cursor_path="/var/lib/observer/cursor.json",
    )
    logrotate = module._render_logrotate(log_path="/var/log/custom/access.log")

    assert "WorkingDirectory=/opt/observer" in service
    assert "EnvironmentFile=-/opt/observer/observer.env" in service
    assert "ExecStart=/usr/bin/env python3 /opt/observer/collect_xray_observer.py" in service
    assert "PORTAL_OBSERVER_NODE_CODE=pl" in env
    assert "PORTAL_OBSERVER_SECRET=observer-secret" in env
    assert "PORTAL_OBSERVER_LOG_PATH=/var/log/xray/access.log" in env
    assert "/var/log/custom/access.log" in logrotate
    assert "observer-secret" not in service
    assert "observer-secret" not in logrotate


def _write_inventory(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "| Code | Name | Role | Plan | IP |",
                "| --- | --- | --- | --- | --- |",
                "| `pl` | `PLnode` | Premium | `1 vCPU` | `203.0.113.10` |",
            ]
        ),
        encoding="utf-8",
    )


def test_inspect_nodes_inbounds_writes_sanitized_json_from_remote_sqlite(
    tmp_path: Path, monkeypatch
) -> None:
    module = _load_script("inspect_nodes_inbounds.py")
    inventory = tmp_path / "inventory.md"
    out_path = tmp_path / "inbounds.json"
    _write_inventory(inventory)
    fake = _FakeSSH(
        command_outputs={
            "test -f /etc/x-ui/x-ui.db && echo HAS_DB || echo NO_DB": (0, "HAS_DB\n", ""),
            'sqlite3 /etc/x-ui/x-ui.db "select id, port, protocol, enable from inbounds order by id;" 2>/dev/null || true': (
                0,
                "1|443|vless|1\n2|8443|trojan|0\n",
                "",
            ),
        }
    )
    monkeypatch.setattr(module, "connect_node", lambda **kwargs: (fake, "env"))
    monkeypatch.setattr(module.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "inspect_nodes_inbounds.py",
            "--inventory",
            str(inventory),
            "--only",
            "pl",
            "--out",
            str(out_path),
        ],
    )

    assert module.main() == 0

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["results"][0]["code"] == "pl"
    assert payload["results"][0]["ip"] == "203.0.113.10"
    assert payload["results"][0]["auth_method"] == "env"
    assert payload["results"][0]["xui_db"] == "HAS_DB"
    assert payload["results"][0]["inbounds"] == [
        {"id": 1, "port": 443, "protocol": "vless", "enable": 1},
        {"id": 2, "port": 8443, "protocol": "trojan", "enable": 0},
    ]
    assert fake.closed is True


def test_inspect_reality_inbound_remote_derives_public_key_without_printing_private_key(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    module = _load_script("inspect_reality_inbound_remote.py")
    inventory = tmp_path / "inventory.md"
    _write_inventory(inventory)
    private_key = base64.urlsafe_b64encode(bytes(range(1, 33))).decode("ascii").rstrip("=")
    stream = {
        "network": "tcp",
        "security": "reality",
        "realitySettings": {
            "dest": "www.microsoft.com:443",
            "serverNames": ["www.microsoft.com"],
            "shortIds": ["abcd"],
            "privateKey": private_key,
        },
    }
    sql_out = f"1|443|vless|{json.dumps(stream)}|PL Reality|1\n"
    fake = _FakeSSH(
        command_outputs={
            'sqlite3 /etc/x-ui/x-ui.db "select id, port, protocol, stream_settings, remark, enable from inbounds where id=1;"': (
                0,
                sql_out,
                "",
            )
        }
    )
    monkeypatch.setattr(module, "connect_node", lambda **kwargs: (fake, "env"))
    monkeypatch.setattr(module.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        sys,
        "argv",
        ["inspect_reality_inbound_remote.py", "--inventory", str(inventory), "--only", "pl"],
    )

    assert module.main() == 0

    output = capsys.readouterr().out
    payload = json.loads(output)
    result = payload["results"][0]
    assert result["code"] == "pl"
    assert result["security"] == "reality"
    assert result["dest"] == "www.microsoft.com:443"
    assert result["server_names"] == ["www.microsoft.com"]
    assert result["public_key"]
    assert private_key not in output
    assert "privateKey" not in output
    assert fake.closed is True


def test_inspect_xui_schema_uses_node_password_env_and_read_only_schema_queries(
    monkeypatch, capsys
) -> None:
    module = _load_script("inspect_xui_schema.py")
    command_outputs = {
        'sqlite3 /etc/x-ui/x-ui.db "pragma table_info(inbounds);"': (0, "id|INTEGER\n", ""),
        'sqlite3 /etc/x-ui/x-ui.db "pragma table_info(settings);" 2>/dev/null || true': (0, "key|TEXT\n", ""),
        'sqlite3 /etc/x-ui/x-ui.db "select id, port, protocol, remark, enable from inbounds order by id;" 2>/dev/null || true': (
            0,
            "1|443|vless|main|1\n",
            "",
        ),
    }
    fake = _install_fake_ssh(module, monkeypatch, command_outputs=command_outputs)
    monkeypatch.setenv("NODE_PASS_PL", "node-secret")
    monkeypatch.setattr(
        sys,
        "argv",
        ["inspect_xui_schema.py", "--host", "203.0.113.10", "--code", "pl"],
    )

    assert module.main() == 0

    assert fake.connect_kwargs["host"] == "203.0.113.10"
    assert fake.connect_kwargs["password"] == "node-secret"
    assert fake.commands == list(command_outputs)
    output = capsys.readouterr().out
    assert "pragma table_info(inbounds)" in output
    assert "1|443|vless|main|1" in output
    assert "node-secret" not in output
    assert fake.closed is True


def test_remote_brain_nodes_sanity_queries_lengths_instead_of_panel_secrets(
    monkeypatch, capsys
) -> None:
    module = _load_script("remote_brain_nodes_sanity.py")
    fake = _install_fake_ssh(module, monkeypatch)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "remote_brain_nodes_sanity.py",
            "--brain-ip",
            "82.21.114.104",
            "--db",
            "/root/portal_bot/portal.db",
        ],
    )

    assert module.main() == 0

    joined = "\n".join(fake.commands)
    assert "apt-get install -y sqlite3" in joined
    assert "from nodes where code in ('pl','pl_free','free')" in joined
    assert "length(coalesce(panel_base_url,'')) as base_len" in joined
    assert "length(coalesce(panel_path,'')) as path_len" in joined
    assert "length(coalesce(panel_user,'')) as user_len" in joined
    assert "length(coalesce(panel_pass,'')) as pass_len" in joined
    assert " panel_pass," not in joined
    assert "brain-secret" not in joined
    assert "brain-secret" not in capsys.readouterr().out
    assert fake.closed is True


def test_remote_strings_brain_xui_runs_read_only_string_greps_without_secret_output(
    monkeypatch, capsys
) -> None:
    module = _load_script("remote_strings_brain_xui.py")
    fake = _install_fake_ssh(module, monkeypatch)

    assert module.main() == 0

    joined = "\n".join(fake.commands)
    assert "apt-get install -y binutils" in joined
    assert "strings /usr/local/x-ui/x-ui | grep -n '2096'" in joined
    assert "grep -E 'XUI_|SUB_PORT|SUBPORT|SUBPORT|SUB_.*PORT|subPort'" in joined
    assert "strings /usr/local/x-ui/x-ui | grep -E 'SUB|sub'" in joined
    output = capsys.readouterr().out
    assert "== strings grep 2096 ==" in output
    assert "brain-secret" not in joined
    assert "brain-secret" not in output
    assert fake.closed is True


def test_remote_manage_xui_restart_uses_connect_node_and_safe_status_output(
    monkeypatch, capsys
) -> None:
    module = _load_script("remote_manage_xui.py")
    fake = _FakeSSH(
        command_outputs={
            "systemctl enable x-ui >/dev/null 2>&1 || true": (0, "", ""),
            "systemctl restart x-ui || true": (0, "restarted\n", ""),
            "systemctl is-active x-ui || true": (0, "active\n", ""),
            "ss -tlnp | grep -E ':(\\d+)' | grep x-ui || true": (
                0,
                "tcp LISTEN 0 4096 0.0.0.0:2096 users:(('x-ui',pid=1))\n",
                "",
            ),
        }
    )
    connect_calls: list[dict[str, object]] = []

    def fake_connect_node(**kwargs):
        connect_calls.append(kwargs)
        return fake, "env"

    monkeypatch.setattr(module, "connect_node", fake_connect_node)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "remote_manage_xui.py",
            "--host",
            "203.0.113.10",
            "--code",
            "pl",
            "--action",
            "restart",
        ],
    )

    assert module.main() == 0

    assert connect_calls[0]["code"] == "pl"
    assert connect_calls[0]["host"] == "203.0.113.10"
    assert connect_calls[0]["port"] == 29374
    assert fake.commands == list(fake.command_outputs)
    output = capsys.readouterr().out
    assert "auth_method=env" in output
    assert "restarted" in output
    assert "active" in output
    assert "x-ui" in output
    assert fake.closed is True


def test_remote_inspect_brain_subscription_hosts_uses_local_token_without_leaking_it(
    monkeypatch, capsys
) -> None:
    module = _load_script("remote_inspect_brain_subscription_hosts.py")
    fake = _install_fake_ssh(module, monkeypatch)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "remote_inspect_brain_subscription_hosts.py",
            "--brain-ip",
            "82.21.114.104",
            "--domain",
            "connect.pokrov.space",
            "--db",
            "/root/portal_bot/portal.db",
        ],
    )

    assert module.main() == 0

    joined = "\n".join(fake.commands)
    assert "select sub_token from users where is_active=1" in joined
    assert "https://connect.pokrov.space:2096/s8Kx2mP7qR4wT/$TOK" in joined
    assert "TOKLEN=${#TOK}" in joined
    assert "RAWLEN=${#RAW}" in joined
    assert "awk -F'@'" in joined
    assert "brain-secret" not in joined
    assert "brain-secret" not in capsys.readouterr().out
    assert fake.closed is True


def test_remote_inspect_brain_subscription_hosts_fails_closed_on_remote_error(
    monkeypatch
) -> None:
    module = _load_script("remote_inspect_brain_subscription_hosts.py")
    fake = _install_fake_ssh(module, monkeypatch)
    monkeypatch.setattr(module, "_run", lambda *_args, **_kwargs: (7, "", "curl failed"))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "remote_inspect_brain_subscription_hosts.py",
            "--brain-ip",
            "82.21.114.104",
            "--domain",
            "connect.pokrov.space",
        ],
    )

    with pytest.raises(SystemExit) as exc:
        module.main()

    assert str(exc.value) == "curl failed"
    assert fake.closed is True


def test_configure_ssh_additional_port_keeps_port_22_and_adds_second_port(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    module = _load_script("configure_ssh_additional_port.py")
    inventory = tmp_path / "inventory.md"
    passwords = tmp_path / "PASSWORDS.txt"
    _write_inventory(inventory)
    passwords.write_text("", encoding="utf-8")
    fake = _FakeSSH()
    monkeypatch.setattr(module, "_ssh_connect", lambda *_args, **_kwargs: fake)
    monkeypatch.setattr(module, "parse_passwords", lambda *_args, **_kwargs: {"pl": "node-secret"})
    monkeypatch.setattr(module.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "configure_ssh_additional_port.py",
            "--inventory",
            str(inventory),
            "--passwords",
            str(passwords),
            "--only",
            "pl",
            "--ssh-port",
            "22",
            "--add-port",
            "29374",
        ],
    )

    assert module.main() == 0

    joined = "\n".join(fake.commands)
    assert "ufw allow 29374/tcp" in joined
    assert "grep -Eq \"^Port[[:space:]]+${PORT}$\"" in joined
    assert "added by configure_ssh_additional_port.py" in joined
    assert "systemctl restart ssh || systemctl restart sshd" in joined
    assert "ss -tlnp | grep -E ':(22|29374)\\b'" in joined
    assert "node-secret" not in joined
    assert "node-secret" not in capsys.readouterr().out
    assert fake.closed is True


def test_remote_install_xui_service_installs_unit_and_restarts_xui(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    module = _load_script("remote_install_xui_service.py")
    inventory = tmp_path / "inventory.md"
    passwords = tmp_path / "PASSWORDS.txt"
    inventory.write_text(
        "\n".join(
            [
                "| Code | Name | Role | IP |",
                "| --- | --- | --- | --- |",
                "| `pl` | `PLnode` | Premium | `203.0.113.10` |",
            ]
        ),
        encoding="utf-8",
    )
    passwords.write_text("", encoding="utf-8")
    fake = _FakeSSH()
    monkeypatch.setattr(module, "_ssh_connect", lambda *_args, **_kwargs: fake)
    monkeypatch.setattr(module, "_parse_passwords", lambda _path: {"pl": "node-secret"})
    monkeypatch.setattr(module.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "remote_install_xui_service.py",
            "--inventory",
            str(inventory),
            "--passwords",
            str(passwords),
            "--only",
            "pl",
        ],
    )

    assert module.main() == 0

    joined = "\n".join(fake.commands)
    assert "test -x /usr/local/x-ui/x-ui" in joined
    assert "cp /usr/local/x-ui/x-ui.service.debian /etc/systemd/system/x-ui.service" in joined
    assert "systemctl daemon-reload" in joined
    assert "systemctl enable x-ui" in joined
    assert "systemctl restart x-ui" in joined
    assert "ss -tlnp | grep -E ':([0-9]+)\\b' | grep x-ui" in joined
    assert "node-secret" not in joined
    assert "node-secret" not in capsys.readouterr().out
    assert fake.closed is True


def test_remote_brain_fix_xui_sub_server_backs_up_then_updates_subscription_settings(
    monkeypatch, capsys
) -> None:
    module = _load_script("remote_brain_fix_xui_sub_server.py")
    fake = _install_fake_ssh(module, monkeypatch)
    monkeypatch.setattr(module.time, "strftime", lambda _fmt: "20260627-120000")

    assert module.main() == 0

    joined = "\n".join(fake.commands)
    assert "apt-get install -y sqlite3" in joined
    assert "cp /etc/x-ui/x-ui.db /etc/x-ui/x-ui.db.bak-20260627-120000" in joined
    assert "DELETE FROM settings WHERE key IN ('subEnable','subPort');" in joined
    assert "INSERT INTO settings(key,value) VALUES('subEnable','false');" in joined
    assert "INSERT INTO settings(key,value) VALUES('subPort','2097');" in joined
    assert "systemctl restart x-ui" in joined
    assert "select key,value from settings where key in" in joined
    assert "brain-secret" not in joined
    assert "brain-secret" not in capsys.readouterr().out
    assert fake.closed is True


def test_remote_brain_set_node_hosts_dns_updates_hosts_after_backup(
    monkeypatch, capsys
) -> None:
    module = _load_script("remote_brain_set_node_hosts_dns.py")
    fake = _install_fake_ssh(module, monkeypatch)
    monkeypatch.setattr(module.time, "strftime", lambda _fmt: "20260627-120000")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "remote_brain_set_node_hosts_dns.py",
            "--brain-ip",
            "82.21.114.104",
            "--domain",
            "pokrov.space",
            "--include-brain",
        ],
    )

    assert module.main() == 0

    joined = "\n".join(fake.commands)
    assert "cp /root/portal_bot/portal.db /root/portal_bot/portal.db.bak-hosts-20260627-120000" in joined
    assert "update nodes set host='pl.pokrov.space' where code='pl';" in joined
    assert "update nodes set host='pl.pokrov.space' where code='pl_free';" in joined
    assert "update nodes set host='free.pokrov.space' where code='free';" in joined
    assert "update nodes set host='pokrov.space' where code='brain';" in joined
    assert "select code,host from nodes order by code;" in joined
    assert "systemctl restart portal-api" in joined
    assert "brain-secret" not in joined
    assert "brain-secret" not in capsys.readouterr().out
    assert fake.closed is True


def test_remote_brain_set_node_hosts_dns_fails_closed_when_backup_fails(
    monkeypatch
) -> None:
    module = _load_script("remote_brain_set_node_hosts_dns.py")
    backup_cmd = "cp /root/portal_bot/portal.db /root/portal_bot/portal.db.bak-hosts-20260627-120000"
    fake = _install_fake_ssh(
        module,
        monkeypatch,
        command_outputs={backup_cmd: (1, "", "backup denied")},
    )
    monkeypatch.setattr(module.time, "strftime", lambda _fmt: "20260627-120000")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "remote_brain_set_node_hosts_dns.py",
            "--brain-ip",
            "82.21.114.104",
            "--domain",
            "pokrov.space",
        ],
    )

    with pytest.raises(SystemExit) as exc:
        module.main()

    assert str(exc.value) == "backup denied"
    assert not any("BEGIN;" in cmd for cmd in fake.commands)
    assert fake.closed is True


def test_remote_grant_all_users_days_requires_env_and_runs_bounded_sql(
    monkeypatch, capsys
) -> None:
    module = _load_script("remote_grant_all_users_days.py")
    fake = _install_fake_ssh(module, monkeypatch)
    monkeypatch.setenv("SSH_HOST", "82.21.114.104")
    monkeypatch.setenv("SSH_PASS", "ssh-secret")
    monkeypatch.setenv("SSH_PORT", "29374")
    monkeypatch.setenv("REMOTE_PORTAL_DB", "/root/portal_bot/portal.db")
    monkeypatch.setattr(sys, "argv", ["remote_grant_all_users_days.py", "--days", "3"])

    assert module.main() == 0

    assert fake.connect_kwargs["host"] == "82.21.114.104"
    assert fake.connect_kwargs["password"] == "ssh-secret"
    joined = "\n".join(fake.commands)
    assert "command -v sqlite3" in joined
    assert "update users set is_active=1, expiry_at='" in joined
    assert "select 'users_total=' || count(*) from users;" in joined
    assert "ssh-secret" not in joined
    assert "ssh-secret" not in capsys.readouterr().out
    assert fake.closed is True


def test_remote_brain_promo_grant_premium_days_backs_up_excludes_manuals_and_restarts_units(
    monkeypatch, capsys
) -> None:
    module = _load_script("remote_brain_promo_grant_premium_days.py")
    fake = _install_fake_ssh(module, monkeypatch)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "remote_brain_promo_grant_premium_days.py",
            "--brain-ip",
            "82.21.114.104",
            "--days",
            "7",
            "--restart",
            "portal-api,portal-bot",
        ],
    )

    assert module.main() == 0

    joined = "\n".join(fake.commands)
    assert "mkdir -p /root/backups" in joined
    assert 'sqlite3 /root/portal_bot/portal.db ".backup /root/backups/portal.db.promo-' in joined
    assert "where lower(coalesce(sub_type,''))!='manual'" in joined
    assert "coalesce(is_manual,0)=0 and created_by_admin is null" in joined
    assert "upper(coalesce(sub_type,'')) in ('','FREE','PENDING')" in joined
    assert "then 'admin_grant' else current_plan_code end" in joined
    assert "select 'users_manual=' || count(*)" in joined
    assert "systemctl restart portal-api" in joined
    assert "systemctl is-active portal-bot" in joined
    assert "brain-secret" not in joined
    assert "brain-secret" not in capsys.readouterr().out
    assert fake.closed is True


def test_remote_install_free_per_ip_limiter_uploads_infra_scripts_and_runs_rate_command(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    module = _load_script("remote_install_free_per_ip_limiter.py")
    inventory = tmp_path / "inventory.md"
    inventory.write_text(
        "\n".join(
            [
                "| Code | Name | Role | IP |",
                "| --- | --- | --- | --- |",
                "| `pl` | `PLnode` | Premium | `203.0.113.10` |",
            ]
        ),
        encoding="utf-8",
    )
    fake = _install_fake_ssh(module, monkeypatch)
    monkeypatch.setenv("NODE_PASS_PL", "node-secret")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "remote_install_free_per_ip_limiter.py",
            "--inventory",
            str(inventory),
            "--code",
            "pl",
            "--port",
            "8443",
            "--rate-kbps",
            "6250",
            "--burst-kb",
            "512",
        ],
    )

    assert module.main() == 0

    assert fake.connect_kwargs["host"] == "203.0.113.10"
    assert fake.connect_kwargs["password"] == "node-secret"
    assert "/root/setup_free_per_ip_limiter.sh" in fake.files
    assert "/root/install_free_per_ip_limiter.sh" in fake.files
    joined = "\n".join(fake.commands)
    assert "command -v nft" in joined
    assert "PORT=8443 RATE_KBPS=6250 BURST_KB=512" in joined
    assert "/root/install_free_per_ip_limiter.sh" in joined
    assert "node-secret" not in joined
    assert "node-secret" not in capsys.readouterr().out
    assert fake.sftp_closed is True
    assert fake.closed is True


def test_remote_brain_sync_users_to_nodes_uploads_free_paid_partitioning_snippet(
    monkeypatch, capsys
) -> None:
    module = _load_script("remote_brain_sync_users_to_nodes.py")
    fake = _install_fake_ssh(module, monkeypatch)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "remote_brain_sync_users_to_nodes.py",
            "--brain-ip",
            "82.21.114.104",
            "--concurrency",
            "8",
            "--passes",
            "3",
            "--tg-id",
            "9000000000000",
        ],
    )

    assert module.main() == 0

    uploaded = fake.files["/root/portal_bot/portal_sync_users_to_nodes.py"].decode("utf-8")
    assert "load_service_env" in uploaded
    assert "Dedicated FREE pools receive only FREE users." in uploaded
    assert "Other countries are PAID-only." in uploaded
    joined = "\n".join(fake.commands)
    assert "test -x /root/portal_bot/venv/bin/python" in joined
    assert "SYNC_CONCURRENCY=8 SYNC_PASSES=3 SYNC_TG_ID=9000000000000" in joined
    assert "requested_tg_id" in uploaded
    assert "DATABASE_URL=sqlite" not in joined
    assert "python /root/portal_bot/portal_sync_users_to_nodes.py" in joined
    assert "brain-secret" not in joined
    assert "brain-secret" not in capsys.readouterr().out
    assert fake.sftp_closed is True
    assert fake.closed is True


def test_remote_sync_users_to_nodes_uploads_portal_code_db_and_runs_sync(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    module = _load_script("remote_sync_users_to_nodes.py")
    db_path = tmp_path / "portal.db.cluster.db"
    db_path.write_bytes(b"sqlite-db")
    fake = _install_fake_ssh(module, monkeypatch)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "remote_sync_users_to_nodes.py",
            "--brain-ip",
            "82.21.114.104",
            "--db",
            str(db_path),
            "--concurrency",
            "5",
        ],
    )

    assert module.main() == 0

    assert fake.files["/root/portal_bot/portal.db"] == b"sqlite-db"
    assert "/root/portal_bot/requirements.txt" in fake.files
    assert "/root/portal_bot/sync_users_to_nodes.py" in fake.files
    uploaded = fake.files["/root/portal_bot/sync_users_to_nodes.py"].decode("utf-8")
    assert "if user_uses_free_pool(user):" in uploaded
    assert "return {_node_code(node) for node in paid_pool_nodes(nodes)" in uploaded
    assert "skip_bases" not in uploaded
    joined = "\n".join(fake.commands)
    assert "apt-get install -y python3 python3-venv python3-pip ca-certificates" in joined
    assert "pip install -r requirements.txt" in joined
    assert "DATABASE_URL=sqlite:////root/portal_bot/portal.db SYNC_CONCURRENCY=5" in joined
    assert "python3 sync_users_to_nodes.py" in joined
    assert "brain-secret" not in joined
    assert "brain-secret" not in capsys.readouterr().out
    assert fake.sftp_closed is True
    assert fake.closed is True


def test_remote_sync_users_to_nodes_desired_codes_cover_all_paid_nodes(monkeypatch) -> None:
    module = _load_script("remote_sync_users_to_nodes.py")

    db_stub = ModuleType("db")
    db_stub.SessionLocal = object
    db_stub.init_db = lambda: None
    models_stub = ModuleType("models")
    models_stub.User = SimpleNamespace
    node_policy_stub = ModuleType("node_policy")
    node_policy_stub.canonical_free_node_code = lambda nodes: next(
        (node.code for node in nodes if "free" in str(node.code).lower()),
        "",
    )
    node_policy_stub.paid_pool_nodes = lambda nodes: [
        node for node in nodes if "free" not in str(node.code).lower()
    ]
    node_policy_stub.user_uses_free_pool = lambda user: (
        str(getattr(user, "sub_type", "") or "").upper() == "FREE"
        or str(getattr(user, "current_plan_code", "") or "").lower() == "free"
    )
    nodes_repo_stub = ModuleType("nodes_repo")
    nodes_repo_stub.enabled_nodes = lambda _session: []
    panel_client_stub = ModuleType("panel_client")
    panel_client_stub.PanelClient = object

    monkeypatch.setitem(sys.modules, "db", db_stub)
    monkeypatch.setitem(sys.modules, "models", models_stub)
    monkeypatch.setitem(sys.modules, "node_policy", node_policy_stub)
    monkeypatch.setitem(sys.modules, "nodes_repo", nodes_repo_stub)
    monkeypatch.setitem(sys.modules, "panel_client", panel_client_stub)

    namespace: dict[str, object] = {}
    exec(module.SYNC_SCRIPT, namespace)
    desired_codes = namespace["_desired_codes_for_user"]
    nodes = [
        SimpleNamespace(code="brain"),
        SimpleNamespace(code="de"),
        SimpleNamespace(code="pl"),
        SimpleNamespace(code="free"),
    ]

    paid = SimpleNamespace(is_active=True, sub_type="PAID", current_plan_code="1_month")
    trial = SimpleNamespace(is_active=True, sub_type="TRIAL", current_plan_code="trial")
    free = SimpleNamespace(is_active=True, sub_type="FREE", current_plan_code="free")
    inactive = SimpleNamespace(is_active=False, sub_type="PAID", current_plan_code="1_month")

    assert desired_codes(paid, nodes) == {"brain", "de", "pl"}
    assert desired_codes(trial, nodes) == {"brain", "de", "pl"}
    assert desired_codes(free, nodes) == {"free"}
    assert desired_codes(inactive, nodes) == set()


def test_migrate_to_nodes_syncs_only_active_users_for_selected_node(
    monkeypatch, capsys
) -> None:
    module = _load_script("migrate_to_nodes.py")
    calls: list[object] = []

    class FakeColumn:
        def asc(self):
            return self

    class FakeUserModel:
        created_at = FakeColumn()

    class FakeUser:
        def __init__(self, tg_id: int, is_active: bool) -> None:
            self.tg_id = tg_id
            self.uuid = f"uuid-{tg_id}"
            self.email = f"user-{tg_id}@example.test"
            self.sub_token = f"token-{tg_id}"
            self.is_active = is_active

    class FakeNode:
        def __init__(self, code: str) -> None:
            self.code = code

    users = [FakeUser(1, True), FakeUser(2, False)]
    nodes = [FakeNode("pl"), FakeNode("it")]

    class FakeQuery:
        def __init__(self) -> None:
            self.active_only = False

        def filter_by(self, **kwargs):
            self.active_only = kwargs.get("is_active") is True
            return self

        def order_by(self, *_args):
            return self

        def all(self):
            return [u for u in users if u.is_active] if self.active_only else list(users)

    class FakeSession:
        def query(self, model):
            assert model is FakeUserModel
            return FakeQuery()

        def close(self) -> None:
            calls.append("session_closed")

    class FakePanelClient:
        def __init__(self, node) -> None:
            self.node = node

        async def login(self) -> bool:
            calls.append(("login", self.node.code))
            return True

        async def ensure_client(self, **kwargs) -> bool:
            calls.append(("ensure", self.node.code, kwargs["tg_id"], kwargs["enable"], kwargs["sub_id"]))
            return True

        async def close(self) -> None:
            calls.append(("close", self.node.code))

    db_mod = ModuleType("db")
    db_mod.init_db = lambda: calls.append("init_db")
    db_mod.SessionLocal = lambda: FakeSession()
    models_mod = ModuleType("models")
    models_mod.User = FakeUserModel
    nodes_repo_mod = ModuleType("nodes_repo")
    nodes_repo_mod.enabled_nodes = lambda _session: nodes
    panel_client_mod = ModuleType("panel_client")
    panel_client_mod.PanelClient = FakePanelClient

    monkeypatch.setitem(sys.modules, "db", db_mod)
    monkeypatch.setitem(sys.modules, "models", models_mod)
    monkeypatch.setitem(sys.modules, "nodes_repo", nodes_repo_mod)
    monkeypatch.setitem(sys.modules, "panel_client", panel_client_mod)
    monkeypatch.setattr(
        sys,
        "argv",
        ["migrate_to_nodes.py", "--node", "pl", "--only-active", "--concurrency", "2"],
    )

    assert module.main() == 0

    output = capsys.readouterr().out
    assert "node=pl: ok=1 fail=0" in output
    assert "DONE: ok=1 fail=0" in output
    assert ("ensure", "pl", 1, True, "token-1") in calls
    assert not any(call for call in calls if isinstance(call, tuple) and call[0] == "ensure" and call[2] == 2)
    assert ("close", "pl") in calls


def test_create_reality_inbounds_generates_keypair_and_uploads_redacted_remote_script(
    monkeypatch
) -> None:
    module = _load_script("create_reality_inbounds.py")
    private_key, public_key = module._gen_reality_keypair()
    assert module._derive_public_from_private(private_key) == public_key

    fake = _FakeSSH()
    commands: list[str] = []

    def fake_run(_ssh, cmd: str, *, timeout: int):
        commands.append(cmd)
        if cmd.startswith("python3 /tmp/ensure_inbound.py "):
            return 0, json.dumps({"ok": True, "action": "exists", "inbound": {"id": 7}}), ""
        if cmd == "rm -f /tmp/ensure_inbound.py":
            return 0, "", ""
        return 1, "", "unexpected command"

    monkeypatch.setattr(module, "_run", fake_run)
    response = module._upload_and_run(
        fake,
        payload={
            "panel_port": 2096,
            "panel_path": "secret-panel",
            "panel_user": "admin",
            "panel_pass": "panel-secret",
            "desired": {"port": 443, "protocol": "vless"},
        },
    )

    assert response == {"ok": True, "action": "exists", "inbound": {"id": 7}}
    remote_script = fake.files["/tmp/ensure_inbound.py"].decode("utf-8")
    assert "panel_pass" in remote_script
    assert "panel-secret" not in remote_script
    assert commands[-1] == "rm -f /tmp/ensure_inbound.py"
    assert fake.sftp_closed is True


def test_remote_configure_brain_for_vless_443_writes_caddy_without_printing_panel_path(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    module = _load_script("remote_configure_brain_for_vless_443.py")
    facts = tmp_path / "node_facts.json"
    facts.write_text(
        json.dumps(
            {
                "results": [
                    {
                        "code": "brain",
                        "panel_port": 2096,
                        "panel_path": "secret-panel-path",
                        "panel_user": "admin",
                        "panel_pass": "panel-secret",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    fake = _install_fake_ssh(module, monkeypatch)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "remote_configure_brain_for_vless_443.py",
            "--brain-ip",
            "82.21.114.104",
            "--domain",
            "pokrov.space",
            "--node-facts",
            str(facts),
        ],
    )

    assert module.main() == 0

    caddyfile = fake.files["/etc/caddy/Caddyfile"].decode("utf-8")
    assert "pokrov.space:8444" in caddyfile
    assert "pokrov.space:2096" in caddyfile
    assert "pokrov.space:443" not in caddyfile
    assert "reverse_proxy 127.0.0.1:8080" in caddyfile
    assert "systemctl restart caddy" in "\n".join(fake.commands)
    output = capsys.readouterr().out
    assert "path_len=17" in output
    assert "secret-panel-path" not in output
    assert "panel-secret" not in output
    assert "panel-secret" not in caddyfile
    assert fake.sftp_closed is True
    assert fake.closed is True


def test_remote_setup_pl_free_8443_helper_uploads_sanitizing_inbound_script(
    monkeypatch
) -> None:
    module = _load_script("remote_setup_pl_free_8443.py")
    fake = _FakeSSH()
    commands: list[str] = []

    def fake_run(_ssh, cmd: str, *, timeout: int):
        commands.append(cmd)
        if cmd.startswith("python3 /tmp/ensure_pl_free_8443.py "):
            return 0, json.dumps({"ok": True, "action": "created", "inbound": {"id": 44}}), ""
        return 0, "", ""

    monkeypatch.setattr(module, "_ssh_connect", lambda *_args, **_kwargs: fake)
    monkeypatch.setattr(module, "_run", fake_run)

    inbound_id = module._ensure_pl_inbound_8443(
        pl_ip="203.0.113.10",
        ssh_user="root",
        ssh_port=29374,
        ssh_pass="node-secret",
        panel_facts={
            "panel_port": 2096,
            "panel_path": "secret-panel",
            "panel_user": "admin",
            "panel_pass": "panel-secret",
        },
    )

    assert inbound_id == 44
    remote_script = fake.files["/tmp/ensure_pl_free_8443.py"].decode("utf-8")
    assert "Do not return streamSettings/settings" in remote_script
    assert "streamSettings" in remote_script
    assert "panel-secret" not in remote_script
    assert commands[0].startswith("python3 /tmp/ensure_pl_free_8443.py ")
    assert fake.sftp_closed is True
    assert fake.closed is True


def test_remote_audit_paid_node_coverage_embeds_bounded_payload_and_writes_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    module = _load_script("remote_audit_paid_node_coverage.py")
    out_path = tmp_path / "paid-coverage.json"
    fake = _install_fake_ssh(
        module,
        monkeypatch,
        command_outputs={},
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "remote_audit_paid_node_coverage.py",
            "--brain-ip",
            "82.21.114.104",
            "--repair",
            "--cleanup-disallowed",
            "--limit",
            "3",
            "--tg-id",
            "123",
            "--out",
            str(out_path),
        ],
    )

    assert module.main() == 0

    command = fake.commands[0]
    marker = "PAYLOAD = base64.b64decode('"
    start = command.index(marker) + len(marker)
    end = command.index("').decode('utf-8')", start)
    payload = json.loads(base64.b64decode(command[start:end]).decode("utf-8"))
    assert payload == {
        "repair": True,
        "cleanup_disallowed": True,
        "limit": 3,
        "only_tg_id": 123,
    }
    assert "ensure_user_on_all_nodes" in command
    assert "cleanup_disallowed" in command
    assert out_path.read_text(encoding="utf-8").startswith("ok:cd /root/portal_bot")
    assert str(out_path) in capsys.readouterr().out
    assert "brain-secret" not in command
    assert fake.closed is True


def test_remote_prepare_brain_public_splits_pem_and_rewrites_public_env_without_dropping_secrets() -> None:
    module = _load_script("remote_prepare_brain_public.py")
    pem = "\n".join(
        [
            "-----BEGIN PRIVATE KEY-----",
            "secret-key",
            "-----END PRIVATE KEY-----",
            "-----BEGIN CERTIFICATE-----",
            "cert-one",
            "-----END CERTIFICATE-----",
            "-----BEGIN CERTIFICATE-----",
            "cert-two",
            "-----END CERTIFICATE-----",
        ]
    )

    priv, fullchain = module._split_pem_bundle(pem)
    rewritten = module._rewrite_env(
        "BOT_TOKEN=keep-secret\nPUBLIC_API_BASE_URL=http://old\nWEBAPP_URL=http://old\n",
        public_api_base="https://pokrov.space:2096",
        webapp_url="https://pokrov.space/webapp/",
    )

    assert priv == "-----BEGIN PRIVATE KEY-----\nsecret-key\n-----END PRIVATE KEY-----\n"
    assert "cert-one" in fullchain
    assert "cert-two" in fullchain
    assert "BOT_TOKEN=keep-secret" in rewritten
    assert "DATABASE_URL=sqlite:////root/portal_bot/portal.db" in rewritten
    assert "PUBLIC_API_BASE_URL=https://pokrov.space:2096" in rewritten
    assert "WEBAPP_URL=https://pokrov.space/webapp/" in rewritten
