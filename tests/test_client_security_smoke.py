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

        failures = self.module._security_default_failures(config_text, "")

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

        failures = self.module._security_default_failures(config_text, "")

        self.assertIn("allow-connection-from-lan must default to false", failures)

    def test_security_defaults_fail_when_release_sanitizer_and_libcore_safe_defaults_are_missing(self) -> None:
        config_text = """
static final enableClashApi = PreferencesNotifier.create<bool, bool>(
  "enable-clash-api",
  false,
);
static final allowConnectionFromLan = PreferencesNotifier.create<bool, bool>(
  "allow-connection-from-lan",
  false,
);
static final mixedPort = PreferencesNotifier.create<int, int>(
  "mixed-port",
  12334,
);
static final tproxyPort = PreferencesNotifier.create<int, int>(
  "tproxy-port",
  12335,
);
static final localDnsPort = PreferencesNotifier.create<int, int>(
  "local-dns-port",
  16450,
);
"""

        failures = self.module._security_default_failures(config_text, "")

        self.assertIn("Android release config must apply local surface sanitization before startup", failures)
        self.assertIn("MixedPort must default to a release-safe value in libcore", failures)
        self.assertIn("TProxyPort must default to a release-safe value in libcore", failures)
        self.assertIn("LocalDnsPort must default to a release-safe value in libcore", failures)

    def test_security_defaults_accept_release_sanitizer_and_safe_libcore_defaults(self) -> None:
        config_text = """
static final enableClashApi = PreferencesNotifier.create<bool, bool>(
  "enable-clash-api",
  false,
);
static final allowConnectionFromLan = PreferencesNotifier.create<bool, bool>(
  "allow-connection-from-lan",
  false,
);
return applyReleaseLocalSurfacePolicy(config, isAndroid: true, isReleaseMode: true);
"""
        go_defaults_text = """
EnableClashApi: false,
MixedPort:      0,
TProxyPort:     0,
LocalDnsPort:   0,
"""

        failures = self.module._security_default_failures(config_text, go_defaults_text)

        self.assertEqual(failures, [])

    def test_analytics_defaults_fail_when_opt_in_is_not_explicit(self) -> None:
        analytics_text = """
return _preferences.getBool(enableAnalyticsPrefKey) ?? true;
"""

        failures = self.module._analytics_default_failures(analytics_text)

        self.assertIn(
            "analytics must default to disabled until the user explicitly opts in",
            failures,
        )

    def test_analytics_defaults_accept_explicit_opt_in_policy(self) -> None:
        analytics_text = """
return _preferences.getBool(enableAnalyticsPrefKey) ?? false;
"""

        failures = self.module._analytics_default_failures(analytics_text)

        self.assertEqual(failures, [])

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
        self.assertIn("RoutingMode must include blockedOnly", failures)
        self.assertIn("buildRoutingRules must handle RoutingMode.allExceptRu", failures)
        self.assertIn("buildRoutingRules must handle RoutingMode.blockedOnly", failures)

    def test_routing_preset_accepts_release_routing_modes(self) -> None:
        enum_text = """
enum RoutingMode {
  global,
  allExceptRu,
  blockedOnly,
}
"""
        config_text = """
const kBlockedOnlyRuleSetUrl =
    'https://github.com/savely-krasovsky/antizapret-sing-box/releases/latest/download/antizapret.srs';

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
    RoutingMode.blockedOnly => const <SingboxRule>[
      SingboxRule(
        ruleSetUrl: kBlockedOnlyRuleSetUrl,
        outbound: RuleOutbound.proxy,
      ),
    ],
  };
}
"""

        failures = self.module._routing_preset_failures(enum_text, config_text)

        self.assertEqual(failures, [])

    def test_public_routing_surface_fails_when_picker_exposes_blocked_only(self) -> None:
        page_text = """
ChoicePreferenceWidget(
  selected: ref.watch(ConfigOptions.routingMode),
  preferences: ref.watch(ConfigOptions.routingMode.notifier),
  choices: RoutingMode.values,
  title: 'Routing preset',
)
"""

        failures = self.module._public_routing_surface_failures(page_text)

        self.assertIn(
            "public routing picker must use RoutingMode.visibleChoices to keep blockedOnly internal by default",
            failures,
        )

    def test_public_routing_surface_accepts_visible_choice_filter(self) -> None:
        page_text = """
ChoicePreferenceWidget(
  selected: ref.watch(ConfigOptions.routingMode),
  preferences: ref.watch(ConfigOptions.routingMode.notifier),
  choices: ref.watch(ConfigOptions.routingMode).visibleChoices(
    selected: ref.watch(ConfigOptions.routingMode),
  ),
  title: 'Routing preset',
)
"""

        failures = self.module._public_routing_surface_failures(page_text)

        self.assertEqual(failures, [])

    def test_routing_defaults_fail_when_consumer_path_starts_global_and_plain_udp_dns(self) -> None:
        config_text = """
static final routingMode = PreferencesNotifier.create<RoutingMode, String>(
  "routing-mode",
  RoutingMode.global,
);
static final remoteDnsAddress = PreferencesNotifier.create<String, String>(
  "remote-dns-address",
  "udp://1.1.1.1",
);
static final directDnsAddress = PreferencesNotifier.create<String, String>(
  "direct-dns-address",
  "udp://1.1.1.1",
);
"""

        failures = self.module._routing_default_failures(config_text)

        self.assertIn(
            "routing-mode must default to RoutingMode.allExceptRu for the consumer path",
            failures,
        )
        self.assertIn(
            "remote-dns-address must default to a tunneled DoH endpoint instead of udp://1.1.1.1",
            failures,
        )
        self.assertIn(
            "direct-dns-address must default to local for split-direct routing",
            failures,
        )

    def test_routing_defaults_accept_consumer_routing_and_split_direct_dns_defaults(self) -> None:
        config_text = """
static final routingMode = PreferencesNotifier.create<RoutingMode, String>(
  "routing-mode",
  RoutingMode.allExceptRu,
);
static final remoteDnsAddress = PreferencesNotifier.create<String, String>(
  "remote-dns-address",
  "https://sky.rethinkdns.com/dns-query",
);
static final directDnsAddress = PreferencesNotifier.create<String, String>(
  "direct-dns-address",
  "udp://1.1.1.1",
  defaultValueFunction: (ref) {
    return switch (ref.read(routingMode)) {
      RoutingMode.global => "udp://1.1.1.1",
      RoutingMode.allExceptRu => "local",
      RoutingMode.blockedOnly => "local",
    };
  },
);
"""

        failures = self.module._routing_default_failures(config_text)

        self.assertEqual(failures, [])

    def test_identity_defaults_fail_when_client_impersonates_legacy_tools(self) -> None:
        app_info_text = """
String get userAgent =>
    "POKROVVPN/$version ($operatingSystem) like ClashMeta v2ray sing-box";
"""
        profile_text = """
userAgent: configs.useXrayCoreWhenPossible ? "v2rayNG/1.8.23" : null,
"""

        failures = self.module._identity_failures(app_info_text, profile_text)

        self.assertIn("app user agent must not mention clash/v2ray/sing-box", failures)
        self.assertIn("compatibility profile downloads must use a first-party user agent", failures)

    def test_identity_defaults_accept_neutral_first_party_identifiers(self) -> None:
        app_info_text = """
String get userAgent =>
    "POKROVVPN/$version ($operatingSystem)";
"""
        profile_text = """
userAgent: configs.useXrayCoreWhenPossible ? "POKROVVPN/XrayCompat" : null,
"""

        failures = self.module._identity_failures(app_info_text, profile_text)

        self.assertEqual(failures, [])

    def test_control_surface_observations_ignore_release_guarded_command_server(self) -> None:
        box_service_text = """
private fun startCommandServer() {
    if (!BuildConfig.DEBUG) {
        return
    }
    val commandServer = CommandServer(this, 300)
    commandServer.start()
    this.commandServer = commandServer
}
"""
        method_handler_text = """
if (BuildConfig.DEBUG) {
  Libbox.newStandaloneCommandClient().serviceReload()
}
"""
        observations = self.module._control_surface_observations(
            box_service_text=box_service_text,
            method_handler_text=method_handler_text,
        )

        self.assertEqual(observations, [])

    def test_control_surface_observations_detect_unprotected_command_server(self) -> None:
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
        observations = self.module._control_surface_observations(
            box_service_text=box_service_text,
            method_handler_text=method_handler_text,
        )

        self.assertIn("android libbox CommandServer is present and requires release-build localhost audit", observations)
        self.assertIn("android/libbox standalone command client calls are present", observations)

    def test_packaging_branding_failures_detects_legacy_user_facing_vpn_branding(self) -> None:
        manifest_text = '<application android:label="POKROV VPN"></application>'
        exe_config_text = """
publisher: POKROV VPN
display_name: POKROV VPN
output_base_file_name: pokrov-vpn-windows-setup-x64
install_dir_name: "{autopf64}\\POKROV VPN"
"""
        msix_text = """
display_name: POKROV VPN
publisher_display_name: POKROV VPN
protocol_activation: pokrovvpn
"""
        runner_rc_text = """
VALUE "CompanyName", "POKROV VPN" "\\0"
VALUE "FileDescription", "POKROV VPN" "\\0"
VALUE "ProductName", "POKROV VPN" "\\0"
"""
        main_cpp_text = 'if (!window.Create(L"POKROV VPN", origin, size)) { return EXIT_FAILURE; }'

        failures = self.module._packaging_branding_failures(
            manifest_text=manifest_text,
            exe_config_text=exe_config_text,
            msix_text=msix_text,
            runner_rc_text=runner_rc_text,
            main_cpp_text=main_cpp_text,
        )

        self.assertIn("Android launcher label must be POKROV", failures)
        self.assertIn("Android manifest must register pokrov:// as the canonical app link scheme", failures)
        self.assertIn("Windows exe package display_name must be POKROV", failures)
        self.assertIn("Windows exe package output filename must drop vpn wording", failures)
        self.assertIn("Windows msix display_name must be POKROV", failures)
        self.assertIn("Windows msix protocol activation must use pokrov", failures)
        self.assertIn("Windows runner resources must use POKROV for CompanyName/FileDescription/ProductName", failures)
        self.assertIn("Windows main window title must be POKROV", failures)

    def test_packaging_branding_failures_accepts_pokrov_user_facing_labels_with_hidden_compatibility(self) -> None:
        manifest_text = """
<application android:label="POKROV">
  <activity>
    <intent-filter>
      <data android:scheme="pokrov" />
      <data android:scheme="pokrovvpn" />
    </intent-filter>
  </activity>
</application>
"""
        exe_config_text = """
publisher: POKROV
display_name: POKROV
output_base_file_name: pokrov-windows-setup-x64
install_dir_name: "{autopf64}\\POKROV"
"""
        msix_text = """
display_name: POKROV
publisher_display_name: POKROV
protocol_activation: pokrov
"""
        runner_rc_text = """
VALUE "CompanyName", "POKROV" "\\0"
VALUE "FileDescription", "POKROV" "\\0"
VALUE "ProductName", "POKROV" "\\0"
"""
        main_cpp_text = 'if (!window.Create(L"POKROV", origin, size)) { return EXIT_FAILURE; }'

        failures = self.module._packaging_branding_failures(
            manifest_text=manifest_text,
            exe_config_text=exe_config_text,
            msix_text=msix_text,
            runner_rc_text=runner_rc_text,
            main_cpp_text=main_cpp_text,
        )

        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
