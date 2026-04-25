import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def _load_module():
    path = SCRIPTS_DIR / "remote_install_mtproto_proxy.py"
    spec = importlib.util.spec_from_file_location("remote_install_mtproto_proxy", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class RemoteInstallMtprotoProxyTests(unittest.TestCase):
    def test_defaults_point_to_free_node_endpoint(self) -> None:
        module = _load_module()

        self.assertEqual(module.DEFAULT_HOST, "151.245.217.23")

    def test_mtproto_links_default_to_random_padding_https_share_link(self) -> None:
        module = _load_module()

        tg_link, https_link = module.mtproto_links(
            host="176.123.166.119",
            port=443,
            secret="0123456789abcdef0123456789abcdef",
        )

        self.assertEqual(
            tg_link,
            "tg://proxy?server=176.123.166.119&port=443&secret=dd0123456789abcdef0123456789abcdef",
        )
        self.assertEqual(
            https_link,
            "https://t.me/proxy?server=176.123.166.119&port=443&secret=dd0123456789abcdef0123456789abcdef",
        )

    def test_render_service_unit_uses_env_file_and_local_config_paths(self) -> None:
        module = _load_module()

        rendered = module.render_service_unit(unit_name="portal-mtproto", install_root="/opt/portal-mtproto")

        self.assertIn("EnvironmentFile=/etc/portal-mtproto.env", rendered)
        self.assertIn("ExecStart=/usr/bin/unshare --fork --pid --mount-proc /opt/portal-mtproto/start.sh", rendered)

    def test_render_install_script_disables_nginx_before_starting_unit(self) -> None:
        module = _load_module()

        rendered = module.render_install_script(
            repo_url="https://github.com/TelegramMessenger/MTProxy",
            install_root="/opt/portal-mtproto",
            unit_name="portal-mtproto",
            env_body=module.render_env(
                advertised_host="176.123.166.119",
                listen_port=443,
                stats_port=8888,
                workers=1,
                secret="0123456789abcdef0123456789abcdef",
                tg_link="tg://proxy?server=176.123.166.119&port=443&secret=dd0123456789abcdef0123456789abcdef",
                https_link="https://t.me/proxy?server=176.123.166.119&port=443&secret=dd0123456789abcdef0123456789abcdef",
            ),
            service_body=module.render_service_unit(),
            refresh_service_body=module.render_refresh_service(),
            refresh_timer_body=module.render_refresh_timer(),
            stop_services=["nginx"],
            allow_ufw=True,
            enable_refresh_timer=False,
        )

        self.assertIn('git clone --depth 1 "$repo_url" "$repo_dir"', rendered)
        self.assertIn('cat >"$install_root/start.sh"', rendered)
        self.assertIn('--aes-pwd __INSTALL_ROOT__/proxy-secret', rendered)
        self.assertIn('for svc in nginx; do', rendered)
        self.assertIn('systemctl disable --now "$svc.service"', rendered)
        self.assertIn('systemctl restart "$unit_name.service"', rendered)
        self.assertIn('systemctl is-active --quiet "$unit_name.service"', rendered)

    def test_render_install_script_can_leave_existing_services_alone(self) -> None:
        module = _load_module()

        rendered = module.render_install_script(
            repo_url="https://github.com/TelegramMessenger/MTProxy",
            install_root="/opt/portal-mtproto",
            unit_name="portal-mtproto",
            env_body=module.render_env(
                advertised_host="151.245.217.23",
                listen_port=9443,
                stats_port=8888,
                workers=1,
                secret="0123456789abcdef0123456789abcdef",
                tg_link="tg://proxy?server=151.245.217.23&port=9443&secret=dd0123456789abcdef0123456789abcdef",
                https_link="https://t.me/proxy?server=151.245.217.23&port=9443&secret=dd0123456789abcdef0123456789abcdef",
            ),
            service_body=module.render_service_unit(),
            refresh_service_body=module.render_refresh_service(),
            refresh_timer_body=module.render_refresh_timer(),
            stop_services=[],
            allow_ufw=True,
            enable_refresh_timer=True,
        )

        self.assertNotIn("for svc in ; do", rendered)
        self.assertIn('systemctl restart "$unit_name.service"', rendered)
        self.assertIn('systemctl restart "$unit_name-config-refresh.timer"', rendered)


if __name__ == "__main__":
    unittest.main()
