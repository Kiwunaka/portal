import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MARKETING_ROOT = REPO_ROOT / "marketing" / "src"
MARKETING_PUBLIC_ROOT = REPO_ROOT / "marketing" / "public"
WEBAPP_ROOT = REPO_ROOT / "webapp" / "src"
WEBAPP_PUBLIC_ROOT = REPO_ROOT / "webapp" / "public"
DOCS_ROOT = REPO_ROOT / "docs"
AUDIT_ROOT = DOCS_ROOT / "audit-artifacts"
COPY_ROOT = REPO_ROOT / "copy"


def _read(*parts: str) -> str:
    return (MARKETING_ROOT.joinpath(*parts)).read_text(encoding="utf-8")


def _read_webapp(*parts: str) -> str:
    return (WEBAPP_ROOT.joinpath(*parts)).read_text(encoding="utf-8")


def _read_doc(*parts: str) -> str:
    return (DOCS_ROOT.joinpath(*parts)).read_text(encoding="utf-8")


def _read_audit(*parts: str) -> str:
    return (AUDIT_ROOT.joinpath(*parts)).read_text(encoding="utf-8")


def _read_webapp_public_json(*parts: str) -> dict:
    return json.loads((WEBAPP_PUBLIC_ROOT.joinpath(*parts)).read_text(encoding="utf-8"))


def _read_copy_catalog() -> dict:
    return json.loads((COPY_ROOT / "catalog.ru.json").read_text(encoding="utf-8"))


def test_release_status_static_claims_mirror_current_launch_decision() -> None:
    launch_decision = json.loads(_read_audit("public-beta-launch-decision-2026-05-09.json"))
    release_status = _read_webapp_public_json("release-status.json")

    assert release_status["source_artifact"] == "public-beta-launch-decision-2026-05-09.json"
    assert release_status["safe_public_claims"] == launch_decision["safe_public_claims"]
    assert release_status["unsafe_public_claims"] == launch_decision["unsafe_public_claims"]
    assert "docs_url is missing" not in json.dumps(launch_decision, ensure_ascii=False)
    assert "docs_url is missing" not in json.dumps(release_status, ensure_ascii=False)


def test_cabinet_downloads_use_runtime_app_links_not_static_fallback() -> None:
    downloads = _read_webapp("components", "cabinet", "downloads-surface.tsx")

    assert "payload?.android?.apk_url || config.androidApkUrl" not in downloads
    assert "payload?.android?.mirror_url || config.androidMirrorUrl" not in downloads
    assert "payload?.windows?.exe_url || config.windowsExeUrl" not in downloads
    assert "payload?.windows?.mirror_url || config.windowsMirrorUrl" not in downloads
    assert 'const androidApk = payload?.android?.apk_url || "";' in downloads
    assert 'const windowsExe = payload?.windows?.exe_url || "";' in downloads


def test_public_install_page_does_not_use_static_app_artifact_flags() -> None:
    install = _read("app", "install", "page.tsx")

    assert "config.androidApkUrl" not in install
    assert "config.androidMirrorUrl" not in install
    assert "config.windowsExeUrl" not in install
    assert "config.windowsMirrorUrl" not in install
    assert "androidHasArtifact" not in install
    assert "windowsHasArtifact" not in install


def test_public_beta_docs_pin_current_brain_truth_and_unblock_packet() -> None:
    current_handoff_path = "docs/audit-artifacts/public-beta-handoff-2026-05-08.md"
    current_completion_audit_path = "docs/audit-artifacts/public-beta-completion-audit-2026-05-08.md"
    current_handoff = _read_audit("public-beta-handoff-2026-05-08.md")
    current_completion_audit = _read_audit("public-beta-completion-audit-2026-05-08.md")
    retained_handoff = _read_audit("public-beta-handoff-2026-05-07.md")
    retained_completion_audit = _read_audit("public-beta-completion-audit-2026-05-07.md")
    handoff = current_handoff + "\n" + retained_handoff
    completion_audit = current_completion_audit + "\n" + retained_completion_audit
    unblock_packet = _read_audit("public-beta-unblock-packet-2026-05-08.md")
    deployment = _read_doc("operations", "deployment-and-access.md")
    retained_reports = {
        "release_gate_report.md": _read_audit("release_gate_report.md"),
        "release_gate_quick_report.md": _read_audit("release_gate_quick_report.md"),
        "public_beta_release_gate_report.md": _read_audit("public_beta_release_gate_report.md"),
        "public_beta_release_gate_report_brain.md": _read_audit("public_beta_release_gate_report_brain.md"),
    }
    current_brain = "docs/audit-artifacts/release-gate-brain-2026-05-08.md"
    current_full = "docs/audit-artifacts/release-gate-full-local-2026-05-08.md"
    current_full_manual = "docs/audit-artifacts/release-gate-full-local-manual-refresh-2026-05-08.md"
    current_quick = "docs/audit-artifacts/release-gate-local-2026-05-08.md"
    unblock_path = "docs/audit-artifacts/public-beta-unblock-packet-2026-05-08.md"
    preflight_path = "docs/audit-artifacts/public-beta-external-access-preflight-2026-05-08.json"
    decision_path = "docs/audit-artifacts/public-beta-launch-decision-2026-05-08.json"
    email_status_path = "docs/audit-artifacts/live-email-auth-status-brain-2026-05-08.json"
    payment_readiness_path = "docs/audit-artifacts/payment-email-readiness-brain-2026-05-08.json"
    paid_evidence_path = "docs/audit-artifacts/paid-checkout-launch-evidence-brain-2026-05-08.json"
    ru_ssh22_path = "docs/audit-artifacts/ru-origin-mini-ssh22-access-2026-05-08.md"
    ru_skip_path = "docs/audit-artifacts/ru-origin-skip-accepted-2026-05-08.md"
    android_validation_path = "docs/audit-artifacts/android-physical-audit-evidence-validation-2026-05-08.json"
    payment_readiness_path_win = payment_readiness_path.replace("/", "\\")
    paid_evidence_path_win = paid_evidence_path.replace("/", "\\")
    android_validation_path_win = android_validation_path.replace("/", "\\")

    assert current_brain in handoff
    assert current_full in handoff
    assert current_full_manual in handoff
    assert current_quick in handoff
    assert current_brain in completion_audit
    assert current_full in completion_audit
    assert current_full_manual in completion_audit
    assert current_quick in completion_audit
    assert "## Concrete Success Criteria" in completion_audit
    assert "## Proxy Signal Limits" in completion_audit
    assert "full/default PASS proves the current-origin local gate set only" in completion_audit
    assert "dry-runs prove the planned asset names and safety guards only" in completion_audit
    assert current_brain in unblock_packet
    assert current_full in unblock_packet
    assert current_quick in unblock_packet
    assert decision_path in unblock_packet
    assert current_brain in deployment
    assert current_full in deployment
    assert current_full_manual in deployment
    assert current_quick in deployment
    assert "2026-05-08 11:45:24" in deployment
    assert "2026-05-08 00:41:20" in deployment
    assert "2026-05-08 11:59:43" in deployment
    assert "2026-05-08 10:52:15" in deployment
    assert "221 passed, 3 subtests passed" in deployment
    assert "green current-origin full/default gates" in completion_audit
    assert "221 passed tests and 3 passed subtests" in completion_audit
    assert "passed the latest integrated brain-origin quick gate" in deployment
    assert "Current handoff remains `NO-GO`" in deployment
    assert f"Operator unblock packet: `{unblock_path}`." in handoff
    assert f"External access preflight: `{preflight_path}`." in handoff
    assert f"| External unblock packet | `{unblock_path}` | PASS |" in completion_audit
    assert f"| External access preflight | `scripts/public_beta_external_access_preflight.py`, `tests/test_public_beta_external_access_preflight.py`, `{preflight_path}` | BLOCKED_BY_ACCESS_EXPECTED |" in completion_audit
    assert f"| Machine-readable launch decision | `scripts/public_beta_launch_decision.py`, `tests/test_public_beta_launch_decision.py`, `{decision_path}` | NO_GO_EXPECTED |" in completion_audit
    decision_payload = json.loads(_read_audit("public-beta-launch-decision-2026-05-08.json"))
    assert decision_payload["inputs"]["handoff"] == current_handoff_path.replace("/", "\\")
    assert decision_payload["inputs"]["completion_audit"] == current_completion_audit_path.replace("/", "\\")
    assert decision_payload["inputs"]["post_deploy_probe"] == "docs\\audit-artifacts\\public-beta-post-deploy-probe-2026-05-08.json"
    decision_checks = {check["name"]: check for check in decision_payload["checks"]}
    assert decision_checks["post_deploy_payment_email_probe"]["status"] == "BLOCKED_BY_ACCESS"
    assert "email live delivery proof" in decision_checks["post_deploy_payment_email_probe"]["missing"]
    assert email_status_path in handoff
    assert email_status_path in completion_audit
    assert payment_readiness_path in handoff
    assert payment_readiness_path in completion_audit
    assert payment_readiness_path in unblock_packet or payment_readiness_path_win in unblock_packet
    assert paid_evidence_path in handoff
    assert paid_evidence_path in completion_audit
    assert paid_evidence_path in unblock_packet or paid_evidence_path_win in unblock_packet
    assert ru_ssh22_path in handoff
    assert ru_ssh22_path in completion_audit
    assert ru_skip_path in handoff
    assert ru_skip_path in completion_audit
    assert ru_skip_path in unblock_packet
    assert "SKIPPED_BY_OPERATOR" in handoff
    assert "SKIPPED_BY_OPERATOR" in completion_audit
    assert "SKIPPED_BY_OPERATOR" in unblock_packet
    assert "RU-origin verification was skipped by operator" in handoff
    assert "Do not claim RU-origin readiness" in deployment
    assert android_validation_path in handoff
    assert android_validation_path in completion_audit
    assert android_validation_path in unblock_packet or android_validation_path_win in unblock_packet
    assert "ANDROID_AUDIT_EVIDENCE_JSON" in handoff
    assert "ANDROID_AUDIT_EVIDENCE_JSON" in unblock_packet
    assert "ANDROID_AUDIT_EVIDENCE_JSON" in deployment
    assert "public email mode is enabled" in handoff
    assert "public email mode is enabled" in completion_audit
    assert "delivery_secret_configured=true" in handoff
    assert "relay secret" in completion_audit
    assert "Public email mode is enabled on brain." in unblock_packet
    assert "brain-post-deploy-live-probe-2026-05-08.json" in handoff
    assert "brain-post-deploy-live-probe-2026-05-08.json" in completion_audit
    assert "--brain-live-probe-json" in handoff
    assert "--brain-live-probe-json" in completion_audit
    assert "--brain-live-probe-json" in deployment
    assert "--brain-live-probe-json" in unblock_packet
    assert 'brain_live_probe_json=""' not in handoff
    release_cockpit = _read_webapp("app", "(dashboard)", "admin", "release", "page.tsx")
    assert "brain-post-deploy-live-probe-<YYYY-MM-DD>.json" in release_cockpit
    assert "Последний retained brain-local probe" in release_cockpit
    assert "--post-deploy-live" in unblock_packet
    assert "email_public_runtime_config_passed=true" in handoff
    assert "safe_to_keep_email_public=true" in unblock_packet
    assert "email_live_delivery_probe_passed=true" in unblock_packet
    assert "post_deploy_probe_modes.email_public_runtime=PASS" in unblock_packet
    assert "email proof still requires `email_live_delivery_probe_passed=true`" in deployment
    assert "ready_to_run_email_post_deploy_probe" in completion_audit
    assert "access-key/QR/share/panic" in handoff
    assert "80 passed" in completion_audit
    canonical_email_text = "\n".join(
        [
            _read_doc("product", "portal-vpn-product.md"),
            _read_doc("architecture", "system-overview.md"),
            _read_doc("architecture", "app-first-and-bonus-flows.md"),
            _read_doc("user", "portal-vpn-user-guide-ru.md"),
            (REPO_ROOT / "webapp" / "README.md").read_text(encoding="utf-8"),
            _read_copy_catalog()["items"]["webapp.entry.card_body"]["ru"],
        ]
    )
    assert "Email browser continuation is planned `soon`" not in canonical_email_text
    assert "public email continuation marked `soon`" not in canonical_email_text
    assert "Email скоро подключим" not in canonical_email_text
    assert "/api/auth/email/status" in canonical_email_text
    assert "gh_cli_keyring" in handoff
    assert "gh_cli_keyring" in completion_audit
    assert "release_auth.ready=true" in handoff
    assert "release_auth.ready=true" in completion_audit
    assert "release not found" in handoff
    assert "release not found" in completion_audit
    assert "LOCAL_PASS_UNSIGNED_RISK_ACCEPTED" in completion_audit
    assert "UNSIGNED_BETA_RISK_ACCEPTED" in unblock_packet
    assert "Windows trusted signing is not required" in deployment
    for release_text in [handoff, completion_audit, unblock_packet, deployment]:
        assert "email public mode is off" not in release_text
        assert "public email mode is still `BLOCKED_BY_ACCESS`" not in release_text
        assert "Windows trusted signing: EXTERNAL_DEPENDENCY" not in release_text
        assert "`gh` is still missing" not in release_text
        assert "BLOCKED_TOOL_MISSING" not in release_text
    assert "staged client-app URL reachability" in completion_audit
    assert "staged URL-shape checks" in completion_audit
    assert "python scripts/public_beta_launch_decision.py --output docs/audit-artifacts/public-beta-launch-decision-2026-05-08.json" in deployment
    assert current_handoff_path in deployment
    assert "# Public Beta Handoff 2026-05-08" in current_handoff
    assert current_completion_audit_path in current_handoff
    assert current_handoff_path in unblock_packet
    assert current_completion_audit_path in unblock_packet
    assert "runtime-app-download-smoke-brain-2026-05-08-post-handoff.json" in unblock_packet
    assert "public-beta-handoff-2026-05-07.md" not in unblock_packet
    assert "public-beta-completion-audit-2026-05-07.md" not in unblock_packet
    assert "runtime-app-download-smoke-brain-2026-05-08.json" not in unblock_packet
    assert "Do not use older generic reports" in unblock_packet
    assert "Do not publish GitHub Releases for public distribution while the handoff says `NO-GO`." in unblock_packet
    assert "ARTIFACT STAGING GO FOR RUNTIME SMOKE" in unblock_packet
    assert "python scripts\\public_beta_external_access_preflight.py" in unblock_packet
    assert "ready_to_run_access_gated_smokes=true" in unblock_packet
    assert "--apps-json ..\\POKROV-app\\artifacts\\releases\\release-handoff.json" in unblock_packet
    assert "--policy-only" in unblock_packet
    assert "Stop and keep the release `NO-GO` if any of these happens:" in unblock_packet
    for release_text in [handoff, completion_audit, unblock_packet]:
        assert "VPN NODE SSH KEYS" not in release_text
        assert "PASSWORDS.txt" not in release_text

    for name, report in retained_reports.items():
        assert current_brain in report, name
        assert current_full in report, name
        assert current_quick in report, name
        assert "Superseded on 2026-05-0" in report, name

    for text in [handoff, completion_audit, deployment, *retained_reports.values()]:
        assert "Generated: 2026-05-07 21:02 MSK" not in text
        assert "2026-05-07 21:34:42" not in text
        assert "2026-05-07 21:40:30" not in text
        assert "brain-origin static hygiene" not in text
        assert "failed brain-origin runtime/static" not in text
        assert "14:31:57" not in text
        assert "16:34:04" not in text
        for line in text.splitlines():
            if "release-gate-brain-2026-05-08.md" in line:
                assert "FAIL" not in line


def test_telegram_announcement_draft_stays_release_honest_and_readable() -> None:
    text = _read_doc("launch", "telegram-announcement.md")
    lower_text = text.lower()

    assert "Статус: только черновики. Не публиковать, пока финальный релизный пакет не говорит `GO`." in text
    assert "оплата пока закрыта" in lower_text
    assert "не используйте зеркала" in lower_text
    assert "@pokrov_supportbot" in text
    assert "https://app.pokrov.space/" in text
    assert "RU-origin в этой бета-волне не проверялся" in text
    assert "beta-" not in text
    assert "beta-сбор" not in text
    assert "релизный handoff" not in text
    assert "Публиковать, если финальный пакет остается `NO-GO`" not in text


def test_launch_pack_stays_ru_only_and_release_honest() -> None:
    launch_files = [
        "telegram-announcement.md",
        "open-beta-release-notes.md",
        "known-issues.md",
        "post-release-monitoring.md",
        "support-macros.md",
    ]
    forbidden_phrases = [
        "Open Beta Release Notes",
        "Known Issues",
        "Post-Release Monitoring",
        "Support Macros",
        "Last updated",
        "Status: draft",
        "broad public announcement",
        "broad public release",
        "Direct downloads",
        "Paid checkout",
        "best-effort",
        "release handoff",
        "public handoff",
        "activation key",
        "beta-",
    ]

    combined = "\n".join(_read_doc("launch", name) for name in launch_files)

    assert "Оплата может быть закрыта" in combined
    assert "Пожалуйста, не используйте неофициальные зеркала." in combined
    assert "Нельзя писать, что публичная бета уже запущена" in combined
    assert "Не повышайте статус до широкого публичного релиза" in combined
    assert "данные карты" in combined
    for phrase in forbidden_phrases:
        assert phrase not in combined


def test_marketing_has_real_seo_entrypoints() -> None:
    for relative_path in (
        ("app", "robots.ts"),
        ("app", "sitemap.ts"),
        ("app", "manifest.ts"),
    ):
        assert MARKETING_ROOT.joinpath(*relative_path).exists(), f"Missing SEO route: {'/'.join(relative_path)}"


def test_marketing_public_ctas_do_not_use_connect_host() -> None:
    marketing_landing = _read("components", "marketing-landing.tsx")

    assert 'href={config.connectUrl}' not in marketing_landing
    assert "config.webappUrl" in marketing_landing
    assert "/checkout/?plan=" not in marketing_landing
    assert "href={defaultCheckoutHref}" not in marketing_landing
    assert "href={buildCheckoutHref(plan.code)}" not in marketing_landing
    assert "href={paidBetaHref}" in marketing_landing


def test_marketing_public_home_does_not_promise_direct_downloads_before_runtime_go() -> None:
    public_home_copy = "\n".join(
        [
            _read("app", "layout.tsx"),
            _read("components", "home", "homepage.tsx"),
            _read("components", "marketing-landing.tsx"),
            _read("lib", "marketing-site.ts"),
        ]
    )

    assert "Скачайте приложение" not in public_home_copy
    assert "Скачайте POKROV" not in public_home_copy
    assert "Никакой регистрации — просто откройте и нажмите Подключить" not in public_home_copy
    assert "Откройте статус установки" in public_home_copy
    assert "если бета-файл доступен вашему аккаунту" in public_home_copy.lower()


def test_marketing_metadata_declares_canonical_and_share_metadata() -> None:
    layout = _read("app", "layout.tsx")
    landing = _read("components", "marketing-landing.tsx")

    assert "metadataBase" in layout
    assert "alternates" in landing
    assert "canonical" in landing
    assert "twitter" in landing
    assert "images" in landing


def test_frontend_release_builds_do_not_depend_on_google_font_fetch() -> None:
    webapp_layout = _read_webapp("app", "layout.tsx")
    webapp_globals = _read_webapp("app", "globals.css")
    marketing_layout = _read("app", "layout.tsx")
    marketing_globals = _read("app", "globals.css")

    for layout in (webapp_layout, marketing_layout):
        assert "next/font/google" not in layout
        assert "Manrope(" not in layout
        assert "JetBrains_Mono(" not in layout

    for globals_css in (webapp_globals, marketing_globals):
        assert "--font-body:" in globals_css
        assert "--font-display:" in globals_css
        assert "--font-mono:" in globals_css


def test_software_application_jsonld_does_not_claim_paid_checkout_is_in_stock() -> None:
    marketing_site = _read("lib", "marketing-site.ts")
    jsonld_block = marketing_site.split("export function buildSoftwareApplicationJsonLd", 1)[1].split(
        "export function buildBreadcrumbJsonLd",
        1,
    )[0]

    assert "https://schema.org/InStock" not in jsonld_block
    assert "offers:" not in jsonld_block


def test_marketing_landing_has_quiet_luxury_structure() -> None:
    landing = _read("components", "marketing-landing.tsx")

    assert "lp-hero-stage" in landing
    assert "lp-trust-grid" in landing
    assert "lp-pricing-shell" in landing
    assert "lp-footer-cta" in landing
    assert '<details className="lp-faq-item">' in landing


def test_marketing_sitemap_includes_checkout_route() -> None:
    marketing_site = _read("lib", "marketing-site.ts")
    sitemap_block = marketing_site.split(
        "export const MARKETING_SITEMAP_ROUTES: MarketingRouteConfig[] = [",
        1,
    )[1].split("];", 1)[0]

    assert "MARKETING_CANONICAL_PATHS.checkout" in sitemap_block


def test_homepage_free_trial_ctas_start_with_install_not_checkout() -> None:
    homepage = _read("components", "home", "homepage.tsx")
    hero = homepage.split("function Hero", 1)[1].split("function ProofStrip", 1)[0]
    free_plan = homepage.split("<div className={styles.pricingIntro}>", 1)[1].split("<div className={styles.planGrid}>", 1)[0]
    final_cta = homepage.split("function FinalCta", 1)[1].split("export default", 1)[0]

    assert "href={links.installHref}" in hero
    assert "href={links.checkoutHref}" not in hero
    assert "href={links.installHref}" in free_plan
    assert "href={links.checkoutHref}" not in free_plan
    assert 'href={links.installHref} className={`${styles.btnPrimary} ${styles.btnPill}`}' in final_cta


def test_homepage_public_beta_copy_stays_gated_until_release_go() -> None:
    homepage = _read("components", "home", "homepage.tsx")
    hero = homepage.split("function Hero", 1)[1].split("function ProofStrip", 1)[0]
    final_cta = homepage.split("function FinalCta", 1)[1].split("export default", 1)[0]

    assert "Статус беты" in hero
    assert "Запросить доступ" in hero
    assert "Открыть статус установки" in final_cta
    assert "Попробуйте 5 дней бесплатно" not in final_cta
    assert "href={buildCheckoutHref(plan.code)}" not in homepage
    assert "href={links.checkoutHref}" not in final_cta


def test_user_guide_keeps_telegram_payment_fallback_single_and_gated() -> None:
    guide = _read_doc("user", "portal-vpn-user-guide-ru.md")
    telegram_section = guide.split("## Роль Telegram", 1)[1].split("Официальные Telegram-поверхности", 1)[0]

    assert guide.count("продолжить персональный маршрут оплаты") == 1
    assert "рублёвая оплата остаётся Lava.top-only" in telegram_section
    assert "может быть недоступна" in telegram_section


def test_canonical_checkout_docs_and_catalog_stay_release_gated() -> None:
    product = _read_doc("product", "portal-vpn-product.md")
    system = _read_doc("architecture", "system-overview.md")
    app_first = _read_doc("architecture", "app-first-and-bonus-flows.md")
    checkout_page = _read("app", "checkout", "page.tsx")
    checkout_client = _read("app", "checkout", "checkout-client.tsx")
    funnel = product.split("Public funnel rule:", 1)[1].split("## Unified Public Copy Direction", 1)[0]
    system_checkout = system.split("### Checkout Continuation Flow", 1)[1].split("### Public Web Journey", 1)[0]
    system_public_web = system.split("### Public Web Journey", 1)[1].split("Public web rule:", 1)[0]
    app_first_checkout = app_first.split("## Checkout Continuation", 1)[1].split("## Subscription Delivery Semantics", 1)[0]
    catalog_items = (_read_copy_catalog().get("items") or {}).values()
    catalog_text = "\n".join(str((item or {}).get("ru") or "") for item in catalog_items)

    assert "sells activation keys through the hosted checkout flow" not in funnel
    assert "hosted checkout sells an activation key" not in system_checkout
    assert "hosted checkout sells an activation key" not in app_first_checkout
    assert "marketing CTA defaults into `pokrov.space/checkout/`" not in system_public_web
    assert "public checkout sells an activation key" not in system_public_web
    assert "paid checkout must remain unavailable or degraded" in funnel
    assert "paid checkout must remain unavailable or degraded" in system_checkout
    assert "paid checkout must remain unavailable or degraded" in app_first_checkout
    assert "Lava.top" in funnel
    assert "email" in funnel.lower()
    assert "activation key" not in catalog_text
    assert "Страница checkout" not in catalog_text
    assert "Оплата бета-доступа" not in catalog_text
    assert "Оплата бета-доступа" not in checkout_page
    assert "Спокойная оплата" not in checkout_client
    assert "Маршрут оплаты" not in checkout_client
    assert "Потом оплатить" not in checkout_client
    assert "Email-вход на сайте пока готовится" not in checkout_client
    assert "Статус продления | POKROV" in checkout_page
    assert "Проверка продления без технических ссылок" in checkout_client
    assert "перейти к оплате" not in catalog_text
    for forbidden_live_payment_copy in [
        "понятную оплату",
        "оплата открываются",
        "продолжить оплату",
        "переходите к оплате",
        "оплатите его",
    ]:
        assert forbidden_live_payment_copy not in catalog_text
    assert "ключ доступа" in catalog_text


def test_marketing_checkout_errors_do_not_render_raw_backend_payloads() -> None:
    checkout_client = _read("app", "checkout", "checkout-client.tsx")

    assert "publicCheckoutErrorMessage" in checkout_client
    assert "readPublicCheckoutError(response" in checkout_client
    assert "(await response.text()) || `HTTP" not in checkout_client
    assert "publicCheckoutExceptionMessage" in checkout_client
    assert "String((error as { message?: string })?.message || error ||" not in checkout_client


def test_marketing_checkout_normalizes_access_keys_like_cabinet_redeem() -> None:
    checkout_client = _read("app", "checkout", "checkout-client.tsx")

    assert "function normalizeAccessKey" in checkout_client
    assert r"[\u2010\u2011\u2012\u2013\u2014\u2212_]+" in checkout_client
    assert 'normalizeAccessKey(searchParams.get("key") || "")' in checkout_client
    assert "const normalized = normalizeAccessKey(keyInput);" in checkout_client
    assert "fetchAccessKeyStatus(normalized)" in checkout_client
    assert "setKeyInput(normalizeAccessKey(event.target.value))" in checkout_client
    assert "keyInput.trim().toUpperCase()" not in checkout_client


def test_marketing_checkout_does_not_probe_same_origin_api_by_default() -> None:
    checkout_client = _read("app", "checkout", "checkout-client.tsx")

    assert "sameOriginApiFallback" in checkout_client
    assert "NEXT_PUBLIC_ENABLE_SAME_ORIGIN_API_FALLBACK" in checkout_client
    assert 'typeof window !== "undefined" ? window.location.origin.replace(/\\/+$/, "") : ""' not in checkout_client


def test_public_homepage_metadata_stays_install_first_until_payment_go() -> None:
    homepage_page = _read("app", "page.tsx")
    marketing_site = _read("lib", "marketing-site.ts")

    assert "понятная оплата" not in homepage_page
    assert "перейти к оплате" not in homepage_page
    assert "переходите к оплате" not in marketing_site
    assert "статус платежного маршрута" in marketing_site
    assert "установ" in homepage_page.lower()
    assert "статус" in homepage_page.lower()


def test_cabinet_upstream_payment_copy_stays_status_first_until_payment_go() -> None:
    dashboard = _read_webapp("app", "(dashboard)", "dashboard", "page.tsx")
    subscription = _read_webapp("app", "(dashboard)", "subscription", "page.tsx")
    redeem = _read_webapp("app", "(dashboard)", "redeem", "page.tsx")
    settings = _read_webapp("app", "(dashboard)", "settings", "page.tsx")
    upstream_copy = "\n".join([dashboard, subscription, redeem, settings])

    assert "Открыть оплату" not in upstream_copy
    assert "Показываем только рабочие варианты" not in subscription
    assert "Купить ключ" not in upstream_copy
    assert "Продлить доступ" not in dashboard
    assert "Продлить подписку" not in dashboard
    assert "Продлите сейчас" not in dashboard
    assert "вернуть защиту" not in dashboard
    assert "Проверьте статус доступа" in dashboard
    assert "Проверить статус продления" in dashboard
    assert "Проверить статус продления" in subscription
    assert "Проверить статус продления" in settings
    assert "Проверить статус ключа" in redeem


def test_cabinet_recovery_surfaces_hide_raw_technical_errors() -> None:
    subscription = _read_webapp("app", "(dashboard)", "subscription", "page.tsx")
    checkout = _read_webapp("app", "(dashboard)", "subscription", "checkout", "page.tsx")
    support = _read_webapp("app", "(dashboard)", "support", "page.tsx")
    support_thread = _read_webapp("app", "(dashboard)", "support", "thread", "page.tsx")
    settings = _read_webapp("app", "(dashboard)", "settings", "page.tsx")
    dashboard = _read_webapp("app", "(dashboard)", "dashboard", "page.tsx")
    downloads_surface = _read_webapp("components", "cabinet", "downloads-surface.tsx")
    email_entry = _read_webapp("components", "cabinet-entry-auth.tsx")
    qr_card = _read_webapp("components", "subscription-qr-card.tsx")
    helper = _read_webapp("lib", "public-error-messages.ts")

    assert "function userFacingErrorMessage" in helper
    for source in [subscription, checkout, support, support_thread, settings, dashboard, downloads_surface, email_entry, qr_card]:
        assert "userFacingErrorMessage" in source
        assert "String((nextError as { message?: string })?.message || nextError || \"\")" not in source
        assert "String((error as { message?: string })?.message || error ||" not in source
        assert "String((err as { message?: string })?.message || err ||" not in source
    assert ": {error}" not in subscription
    assert ": {catalogError}" not in checkout
    assert "MAX_TICKET_ATTACHMENT_BYTES" in support
    assert "attachmentFile.size > MAX_TICKET_ATTACHMENT_BYTES" in support
    settings_email_block = settings.split('key: "email"', 1)[1].split('key: "access"', 1)[0]
    assert 'href="/"' not in settings_email_block


def test_admin_release_cockpit_hides_raw_loading_errors() -> None:
    release_cockpit = _read_webapp("app", "(dashboard)", "admin", "release", "page.tsx")

    assert "userFacingErrorMessage" in release_cockpit
    assert "String((nextError as { message?: string })?.message || nextError ||" not in release_cockpit
    assert "Не удалось загрузить релизный экран." in release_cockpit


def test_public_release_copy_avoids_internal_operator_terms() -> None:
    catalog_items = (_read_copy_catalog().get("items") or {}).values()
    catalog_text = "\n".join(str((item or {}).get("ru") or "") for item in catalog_items)
    marketing_public = "\n".join(
        [
            _read("lib", "marketing-site.ts"),
            _read("components", "marketing-landing.tsx"),
            _read("components", "home", "homepage.tsx"),
            _read("app", "install", "page.tsx"),
        ]
    )
    downloads_surface = _read_webapp("components", "cabinet", "downloads-surface.tsx")
    dashboard = _read_webapp("app", "(dashboard)", "dashboard", "page.tsx")
    admin_release = _read_webapp("app", "(dashboard)", "admin", "release", "page.tsx")

    public_copy = "\n".join([catalog_text, marketing_public, downloads_surface])
    for forbidden in [
        "best-effort",
        "декоративного SLA",
        "production signing",
        "release-build audit",
        "спокойной оплате",
    ]:
        assert forbidden not in public_copy
    assert "backend" not in downloads_surface
    assert "Google Play" not in downloads_surface
    assert "play.google.com" not in downloads_surface
    assert "androidPlay" not in downloads_surface
    assert "Android через Play" not in downloads_surface
    assert "APK и Google Play" not in dashboard
    assert "APK из кабинета" in dashboard
    assert "firstUrl(apps?.android?.apk_url, apps?.android?.mirror_url, apps?.android?.play_url)" not in admin_release
    assert "firstUrl(apps?.android?.apk_url, apps?.android?.mirror_url)" in admin_release
    assert "function isGithubReleaseArtifactUrl" in admin_release
    assert 'url.hostname.toLowerCase() === "github.com"' in admin_release
    assert 'path.includes("/releases/download/")' in admin_release
    assert "function isInstallDocsUrl" in admin_release
    assert 'url.hostname.toLowerCase() === "pokrov.space"' in admin_release
    assert 'firstUrl(apps?.android?.play_url)' in admin_release
    assert "!androidPlayUrl" in admin_release
    assert "доверенной подписи" not in public_copy
    assert "физической проверки сборки" not in downloads_surface
    assert "финальной проверки ссылок" in public_copy
    assert "runtime-синхронизации ссылки" in downloads_surface


def test_homepage_hash_navigation_targets_exist() -> None:
    homepage = _read("components", "home", "homepage.tsx")
    targets = sorted(set(re.findall(r'href="#([^"]+)"', homepage)))

    assert targets
    for target in targets:
        assert f'id="{target}"' in homepage


def test_marketing_public_static_artifacts_do_not_expose_legacy_payment_provider() -> None:
    legacy_provider_files = sorted(path.name for path in MARKETING_PUBLIC_ROOT.glob("fk-*"))

    assert legacy_provider_files == []


def test_cabinet_dashboard_download_ctas_point_to_install_route() -> None:
    dashboard = _read_webapp("app", "(dashboard)", "dashboard", "page.tsx")

    assert "https://pokrov.space/#download" not in dashboard
    assert "https://pokrov.space/install/" in dashboard


def test_email_auth_enabled_ui_stays_ru_only() -> None:
    entry = _read_webapp("components", "cabinet-entry-auth.tsx")

    forbidden = [
        "Verification email sent.",
        "Account created.",
        "Email session token is missing.",
        "Email action failed.",
        'placeholder="Password"',
        ">Sign in<",
        ">Create account<",
        'placeholder="Verification token"',
        'placeholder="Reset token"',
        'placeholder="New password"',
        '"Reset and sign in"',
        '"Send reset email"',
    ]
    for text in forbidden:
        assert text not in entry
    assert "Войти" in entry
    assert "Создать аккаунт" in entry
    assert "Восстановить доступ" in entry
