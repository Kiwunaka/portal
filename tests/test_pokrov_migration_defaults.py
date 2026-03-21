from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
LEGACY_PUBLIC_MARKERS = (
    "portal-privacy.online",
    "kiwunaka.space",
    "portal_service_bot",
    "portal_privacy_helpbot",
    "portalfeedbackbot",
    "PORTAL ENTRY",
)


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def _without_legacy_marker_catalog(text: str) -> str:
    return re.sub(r"export const LEGACY_PUBLIC_MARKERS = \[(?:.|\n)*?\] as const;\n?", "", text)


def _assert_no_legacy_markers(label: str, text: str) -> None:
    for marker in LEGACY_PUBLIC_MARKERS:
        assert marker not in text, f"{label} still contains legacy public marker: {marker}"


def test_backend_and_web_defaults_point_to_pokrov_surface() -> None:
    shared_portal_text = _read("shared/portal-config.ts")
    config_text = _read("portal_bot/config.py")
    web_portal_text = _read("webapp/src/lib/portal.ts")
    marketing_portal_text = _read("marketing/src/lib/portal.ts")
    client_portal_text = _read("external/client-fork/app/lib/features/portal/config/portal_public_config.dart")

    assert "pokrov.space" in config_text
    assert "api.pokrov.space" in config_text
    assert "app.pokrov.space" in config_text
    assert "connect.pokrov.space" in config_text
    assert "pay.pokrov.space" in config_text
    assert 'CLIENT_BRAND: str = (os.getenv("CLIENT_BRAND") or "POKROV VPN").strip()' in config_text
    assert 'MAIN_BOT_USERNAME: str = (os.getenv("MAIN_BOT_USERNAME") or os.getenv("BOT_USERNAME") or "pokrov_vpnbot").lstrip("@")' in config_text
    assert 'NEWS_CHANNEL_URL: str = (os.getenv("NEWS_CHANNEL_URL") or "https://t.me/pokrov_vpn").strip()' in config_text
    assert "pokrov_feedbackbot" in config_text
    assert 'export const CANONICAL_CLIENT_BRAND = "POKROV VPN";' in shared_portal_text
    assert 'export const CANONICAL_CHECKOUT_URL = `${CANONICAL_PAY_ORIGIN}/checkout`;' in shared_portal_text
    assert "connect.pokrov.space" in shared_portal_text
    assert "pokrov_feedbackbot" in shared_portal_text
    assert 'export const CANONICAL_CLIENT_BRAND = "POKROV VPN";' in web_portal_text
    assert 'export const CANONICAL_CHECKOUT_URL = `${CANONICAL_PAY_ORIGIN}/checkout`;' in web_portal_text
    assert "https://api.pokrov.space" in web_portal_text
    assert "https://app.pokrov.space" in web_portal_text
    assert "https://connect.pokrov.space" in web_portal_text
    assert "https://pay.pokrov.space" in web_portal_text
    assert "https://t.me/pokrov_vpnbot" in web_portal_text
    assert "https://t.me/pokrov_supportbot" in web_portal_text
    assert "https://t.me/pokrov_feedbackbot" in web_portal_text
    assert "Продолжить вход в POKROV VPN" in web_portal_text
    assert "Связаться с поддержкой" in web_portal_text
    assert 'export const CANONICAL_CLIENT_BRAND = "POKROV VPN";' in marketing_portal_text
    assert 'export const CANONICAL_CHECKOUT_URL = `${CANONICAL_PAY_ORIGIN}/checkout`;' in marketing_portal_text
    assert "https://api.pokrov.space" in marketing_portal_text
    assert "https://app.pokrov.space" in marketing_portal_text
    assert "https://connect.pokrov.space" in marketing_portal_text
    assert "https://pay.pokrov.space" in marketing_portal_text
    assert "https://t.me/pokrov_vpnbot" in marketing_portal_text
    assert "https://t.me/pokrov_supportbot" in marketing_portal_text
    assert "https://t.me/pokrov_feedbackbot" in marketing_portal_text
    assert "Свободный интернет без сложной настройки" in marketing_portal_text
    assert "POKROV VPN • Telegram-first • понятный старт" in marketing_portal_text
    assert "https://api.pokrov.space" in client_portal_text
    assert "https://app.pokrov.space" in client_portal_text
    assert "https://pay.pokrov.space" in client_portal_text
    assert "https://t.me/pokrov_vpnbot" in client_portal_text
    assert "https://t.me/pokrov_supportbot" in client_portal_text
    _assert_no_legacy_markers("shared/portal-config.ts", _without_legacy_marker_catalog(shared_portal_text))
    _assert_no_legacy_markers("webapp/src/lib/portal.ts", _without_legacy_marker_catalog(web_portal_text))
    _assert_no_legacy_markers("marketing/src/lib/portal.ts", _without_legacy_marker_catalog(marketing_portal_text))
    _assert_no_legacy_markers("portal_bot/config.py", config_text)


def test_runtime_and_edge_configs_use_pokrov_domains() -> None:
    haproxy_text = _read("infra/brain-haproxy-l4.cfg")
    caddy_text = _read("infra/Caddyfile.internal")
    deploy_text = _read("scripts/release_orchestrator.py")
    static_deploy_text = _read("scripts/remote_deploy_brain_static_sites.py")
    update_env_text = _read("scripts/remote_brain_update_env_urls.py")
    inspect_hosts_text = _read("scripts/inspect_public_subscription_hosts.py")
    inspect_names_text = _read("scripts/inspect_public_subscription_names.py")
    subscription_interval_text = _read("scripts/remote_check_subscription_interval.py")
    verify_text = _read("scripts/verify_brain_ready.py")
    web_next_config = _read("webapp/next.config.ts")

    assert "pokrov.space" in haproxy_text
    assert "app.pokrov.space" in haproxy_text
    assert "connect.pokrov.space" in haproxy_text
    assert "api.pokrov.space" in haproxy_text
    assert "pay.pokrov.space" in haproxy_text
    assert "pokrov.space" in caddy_text
    assert "app.pokrov.space" in caddy_text
    assert "connect.pokrov.space" in caddy_text
    assert "api.pokrov.space" in caddy_text
    assert "pay.pokrov.space" in caddy_text
    assert "pokrov.space:8444" in caddy_text
    assert "api.pokrov.space:8444" in caddy_text
    assert "pay.pokrov.space:8444" in caddy_text
    assert "\n:8444 {" not in caddy_text
    assert "tls internal" not in caddy_text
    assert "reverse_proxy 127.0.0.1:8080" in caddy_text
    pay_host_block = caddy_text.split("@pay_host host pay.pokrov.space", 1)[1].split("@legacy_web_hosts", 1)[0]
    assert "root * /var/www/portal/marketing" in pay_host_block
    assert 'default="pokrov.space"' in deploy_text
    assert 'default="api.pokrov.space"' in deploy_text
    assert 'default="pokrov.space"' in static_deploy_text
    assert 'default="api.pokrov.space"' in static_deploy_text
    assert 'default="api.pokrov.space"' in update_env_text
    assert 'default="pokrov.space"' in update_env_text
    assert 'default="https://api.pokrov.space"' in inspect_hosts_text
    assert 'default="https://api.pokrov.space"' in inspect_names_text
    assert 'default="api.pokrov.space"' in subscription_interval_text
    assert 'default="pokrov.space"' in verify_text
    assert 'default="api.pokrov.space"' in verify_text
    assert 'const BASE_PATH = ""' in web_next_config


def test_client_metadata_uses_pokrov_brand_and_new_identities() -> None:
    constants_text = _read("external/client-fork/app/lib/core/model/constants.dart")
    pubspec_text = _read("external/client-fork/app/pubspec.yaml")
    android_gradle_text = _read("external/client-fork/app/android/app/build.gradle")
    android_manifest_text = _read("external/client-fork/app/android/app/src/main/AndroidManifest.xml")
    msix_text = _read("external/client-fork/app/windows/packaging/msix/make_config.yaml")
    windows_cmake_text = _read("external/client-fork/app/windows/CMakeLists.txt")
    windows_main_text = _read("external/client-fork/app/windows/runner/main.cpp")
    windows_rc_text = _read("external/client-fork/app/windows/runner/Runner.rc")
    windows_exe_packaging_text = _read("external/client-fork/app/windows/packaging/exe/make_config.yaml")
    windows_exe_script_text = _read("external/client-fork/app/windows/packaging/exe/inno_setup.sas")
    fork_branding_text = _read("external/client-fork/app/.github/scripts/apply_fork_branding.py")
    fork_release_workflow_text = _read("external/client-fork/app/.github/workflows/fork-android-windows-release.yml")
    fork_brand_env_text = _read("external/client-fork/branding/brand.env.example")
    fork_release_setup_text = _read("external/client-fork/app/.github/FORK_RELEASE_SETUP.md")
    fork_readme_text = _read("external/client-fork/README.md")
    package_windows_text = _read("external/client-fork/app/scripts/package_windows.ps1")

    assert 'static const appName = "POKROV VPN"' in constants_text
    assert "https://t.me/pokrov_vpn" in constants_text
    assert "https://pokrov.space/privacy" in constants_text
    assert "https://pokrov.space/terms" in constants_text
    assert "name: hiddify" in pubspec_text
    assert "namespace 'com.hiddify.hiddify'" in android_gradle_text
    assert 'testNamespace "test.com.hiddify.hiddify"' in android_gradle_text
    assert 'applicationId "space.pokrov.vpn"' in android_gradle_text
    assert 'android:label="POKROV VPN"' in android_manifest_text
    assert '<data android:scheme="pokrovvpn" />' in android_manifest_text
    assert "display_name: POKROV VPN" in msix_text
    assert "identity_name: Pokrov.Vpn" in msix_text
    assert "protocol_activation: pokrovvpn" in msix_text
    assert 'project(pokrovvpn LANGUAGES CXX)' in windows_cmake_text
    assert 'set(BINARY_NAME "POKROVVPN")' in windows_cmake_text
    assert 'L"POKROVVPNMutex"' in windows_main_text
    assert 'FindWindowA(NULL, "POKROV VPN")' in windows_main_text
    assert 'window.SendAppLinkToInstance(L"POKROV VPN")' in windows_main_text
    assert 'window.Create(L"POKROV VPN", origin, size)' in windows_main_text
    assert 'VALUE "FileDescription", "POKROV VPN"' in windows_rc_text
    assert 'VALUE "InternalName", "pokrovvpn"' in windows_rc_text
    assert 'VALUE "OriginalFilename", "POKROVVPN.exe"' in windows_rc_text
    assert 'VALUE "ProductName", "POKROV VPN"' in windows_rc_text
    assert "display_name: POKROV VPN" in windows_exe_packaging_text
    assert "executable_name: POKROVVPN.exe" in windows_exe_packaging_text
    assert "output_base_file_name: POKROVVPN-setup" in windows_exe_packaging_text
    assert 'install_dir_name: "{autopf64}\\\\POKROV VPN"' in windows_exe_packaging_text
    assert "Exec('taskkill', '/F /IM POKROVVPN.exe'" in windows_exe_script_text
    assert '_read_env("FORK_BRAND_NAME", "POKROV VPN")' in fork_branding_text
    assert '_read_env("FORK_ANDROID_APPLICATION_ID", "space.pokrov.vpn")' in fork_branding_text
    assert '_read_env("FORK_ANDROID_NAMESPACE", "com.hiddify.hiddify")' in fork_branding_text
    assert '"test.com.hiddify.hiddify"' in fork_branding_text
    assert '_read_env("FORK_URI_SCHEME", "pokrovvpn")' in fork_branding_text
    assert '_read_env("FORK_WINDOWS_IDENTITY_NAME", "Pokrov.Vpn")' in fork_branding_text
    assert '_read_env("FORK_WINDOWS_EXE_STEM", "POKROVVPN")' in fork_branding_text
    assert 'FindWindowA(NULL, "{brand_name}")' in fork_branding_text
    assert 'window.SendAppLinkToInstance(L"{brand_name}")' in fork_branding_text
    assert 'window.Create(L"{brand_name}", origin, size)' in fork_branding_text
    assert 'f"{exe_stem}-setup"' in fork_branding_text
    assert 'windows_exe_stem: POKROVVPN' not in fork_branding_text
    assert '"ProductName",' in fork_branding_text and "brand_name" in fork_branding_text
    assert 'APP_SLUG: "pokrov-vpn"' in fork_release_workflow_text
    assert "default: \"/var/www/downloads/pokrov-vpn\"" in fork_release_workflow_text
    assert "APP_ANDROID_PACKAGE: ${{ vars.ANDROID_PACKAGE_NAME || 'space.pokrov.vpn' }}" in fork_release_workflow_text
    assert 'FORK_BRAND_NAME=POKROV VPN' in fork_brand_env_text
    assert 'FORK_ANDROID_APPLICATION_ID=space.pokrov.vpn' in fork_brand_env_text
    assert 'FORK_ANDROID_NAMESPACE=com.hiddify.hiddify' in fork_brand_env_text
    assert 'FORK_ANDROID_TEST_NAMESPACE=test.com.hiddify.hiddify' in fork_brand_env_text
    assert 'FORK_URI_SCHEME=pokrovvpn' in fork_brand_env_text
    assert 'FORK_WINDOWS_IDENTITY_NAME=Pokrov.Vpn' in fork_brand_env_text
    assert 'FORK_WINDOWS_INSTALL_DIR=POKROV VPN' in fork_brand_env_text
    assert 'FORK_WINDOWS_EXE_STEM=POKROVVPN' in fork_brand_env_text
    assert '`pokrov-vpn`' in fork_release_setup_text
    assert '/var/www/downloads/pokrov-vpn' in fork_release_setup_text
    assert 'legacy `com.hiddify.hiddify` package' in fork_release_setup_text
    assert 'pokrov-vpn-android-universal.apk' in fork_readme_text
    assert 'pokrov-vpn-windows-setup-x64.exe' in fork_readme_text
    assert '$appSlug = if ($env:APP_SLUG)' in package_windows_text
    assert '"pokrov-vpn"' in package_windows_text
    assert '"*-setup.exe"' in package_windows_text
    assert '$appSlug-windows-setup-x64.exe' in package_windows_text
    assert '$appSlug-windows-portable-x64.zip' in package_windows_text


def test_runtime_bot_defaults_use_new_pokrov_identities() -> None:
    api_text = _read("portal_bot/api.py")
    bot_text = _read("portal_bot/bot.py")
    helpbot_text = _read("portal_bot/helpbot.py")
    worker_text = _read("portal_bot/worker.py")
    redirect_text = _read("portal_bot/legacy_redirect_bot.py")
    webapp_e2e_text = _read("webapp/e2e/admin-gate.spec.ts")
    config_text = _read("portal_bot/config.py")

    assert 'or "pokrov_supportbot"' in api_text
    assert 'or "pokrov_vpnbot"' in api_text
    assert "api.pokrov.space" in api_text
    assert "pay.pokrov.space" in api_text
    assert 'or "pokrov_vpnbot"' in bot_text
    assert 'or "pokrov_supportbot"' in bot_text
    assert 'or "api.pokrov.space"' in bot_text
    assert 'or "pokrov_vpnbot"' in helpbot_text
    assert 'or "pokrov_vpnbot"' in worker_text
    assert 'or "pokrov_supportbot"' in worker_text
    assert 'or "pokrov_feedbackbot"' in config_text
    assert "connect.pokrov.space" in config_text
    assert "https://t.me/pokrov_vpnbot" in redirect_text
    assert "https://api.pokrov.space/s8Kx2mP7qR4wT/mock_token" in webapp_e2e_text
    assert "https://t.me/pokrov_supportbot" in webapp_e2e_text
    assert "https://t.me/pokrov_vpnbot?start=ref_mock" in webapp_e2e_text
    assert 'or "pokrov_vpnbot"' in config_text
    assert 'https://t.me/pokrov_vpn' in config_text
