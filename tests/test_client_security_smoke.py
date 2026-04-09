import importlib.util
import sys
import unittest
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "client_security_smoke.py"
    spec = importlib.util.spec_from_file_location("client_security_smoke", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ClientSecuritySmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_security_defaults_fail_when_clash_api_is_enabled(self) -> None:
        config_text = """
static final enableClashApi = PreferencesNotifier.create<bool, bool>(
  "enable-clash-api",
  true,
);
static final allowConnectionFromLan = PreferencesNotifier.create<bool, bool>(
  "allow-connection-from-lan",
  false,
);
"""

        failures = self.module._security_default_failures(config_text)

        self.assertIn("enable-clash-api must default to false", failures)

    def test_security_defaults_fail_when_lan_access_is_enabled(self) -> None:
        config_text = """
static final enableClashApi = PreferencesNotifier.create<bool, bool>(
  "enable-clash-api",
  false,
);
static final allowConnectionFromLan = PreferencesNotifier.create<bool, bool>(
  "allow-connection-from-lan",
  true,
);
"""

        failures = self.module._security_default_failures(config_text)

        self.assertIn("allow-connection-from-lan must default to false", failures)

    def test_routing_preset_requires_all_except_ru_groundwork(self) -> None:
        enum_text = """
enum RoutingMode {
  global,
}
"""
        config_text = """
List<SingboxRule> buildRoutingRules({
  required RoutingMode routingMode,
  required Region? region,
}) {
  return switch (routingMode) {
    RoutingMode.global => const <SingboxRule>[],
  };
}
"""

        failures = self.module._routing_preset_failures(enum_text, config_text)

        self.assertIn("RoutingMode must include allExceptRu", failures)
        self.assertIn("buildRoutingRules must handle RoutingMode.allExceptRu", failures)

    def test_routing_preset_accepts_all_except_ru_rules(self) -> None:
        enum_text = """
enum RoutingMode {
  global,
  allExceptRu,
}
"""
        config_text = """
List<SingboxRule> buildRoutingRules({
  required RoutingMode routingMode,
  required Region? region,
}) {
  return switch (routingMode) {
    RoutingMode.global => const <SingboxRule>[],
    RoutingMode.allExceptRu => const <SingboxRule>[
      SingboxRule(
        ip: "geoip:private",
        outbound: RuleOutbound.bypass,
      ),
      SingboxRule(
        domains: "domain:.ru",
        ip: "geoip:ru",
        outbound: RuleOutbound.bypass,
      ),
    ],
  };
}
"""

        failures = self.module._routing_preset_failures(enum_text, config_text)

        self.assertEqual(failures, [])

    def test_control_surface_observations_detect_command_server(self) -> None:
        box_service_text = """
private fun startCommandServer() {
    val commandServer = CommandServer(this, 300)
    commandServer.start()
    this.commandServer = commandServer
}
"""
        method_handler_text = """
Libbox.newStandaloneCommandClient().serviceReload()
"""
        core_service_text = """
ClientChannel(
  'localhost',
  port: 7078,
)
"""

        observations = self.module._control_surface_observations(
            box_service_text=box_service_text,
            method_handler_text=method_handler_text,
            core_service_text=core_service_text,
        )

        self.assertIn("android libbox CommandServer is present and requires release-build localhost audit", observations)
        self.assertIn("android/libbox standalone command client calls are present", observations)
        self.assertIn("localhost gRPC channel is present in core sing-box service", observations)


if __name__ == "__main__":
    unittest.main()
