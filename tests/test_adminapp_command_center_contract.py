import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADMINAPP = ROOT / "adminapp"


def test_status_mapper_has_the_seven_approved_russian_labels() -> None:
    text = (ROOT / "adminapp/src/lib/ops-status/presentation.ts").read_text(encoding="utf-8")
    for label in (
        "Норма",
        "Требует внимания",
        "Сбой",
        "Устарело",
        "Недоступно",
        "Нет данных",
        "Доступ заблокирован",
    ):
        assert label in text


def test_ru_read_reasons_have_russian_operator_copy() -> None:
    text = (ROOT / "adminapp/src/features/overview/triage-workspace.tsx").read_text(
        encoding="utf-8"
    )
    assert (
        'superseded_manifest: "Конфигурация RU-проверки изменилась: нужен новый запуск"'
        in text
    )
    assert (
        'current_target_missing: "В последнем запуске нет обязательной текущей цели"'
        in text
    )


def test_tooltip_contract_is_not_a_title_attribute() -> None:
    text = (ROOT / "adminapp/src/components/ui/tooltip.tsx").read_text(encoding="utf-8")
    assert "aria-describedby" in text
    assert 'role="tooltip"' in text
    assert 'event.key === "Escape"' in text
    assert " title=" not in text


def test_tooltip_escape_does_not_reopen_on_restored_focus() -> None:
    text = (ROOT / "adminapp/src/components/ui/tooltip.tsx").read_text(encoding="utf-8")
    assert "suppressFocusOpenRef.current = true" in text
    assert "if (!suppressFocusOpenRef.current)" in text


def test_source_row_suppresses_measurements_without_a_verdict() -> None:
    text = (ROOT / "adminapp/src/components/ui/source-row.tsx").read_text(encoding="utf-8")
    match = re.search(r"function sourceDetail\((.*?)\n}\n", text, re.DOTALL)
    assert match is not None
    contract = match.group(0)
    assert "status: OpsStatusCode" in contract
    assert 'status === "missing"' in contract
    assert 'status === "unavailable"' in contract
    assert 'return "Нет данных"' in contract
    assert 'return "Недоступно"' in contract
    assert contract.index('status === "missing"') < contract.index("return detail")
    assert contract.index('status === "unavailable"') < contract.index("return detail")
    assert "sourceDetail(status, detail)" in text


def test_empty_and_error_states_require_operator_guidance() -> None:
    text = (ROOT / "adminapp/src/components/ui/states.tsx").read_text(encoding="utf-8")
    for props_name in ("EmptyStateProps", "ErrorStateProps"):
        match = re.search(rf"export interface {props_name} {{(.*?)\n}}", text, re.DOTALL)
        assert match is not None
        assert "description: string;" in match.group(1)


def test_legacy_renderer_is_removed_and_dashboard_stays_thin() -> None:
    for relative in (
        "src/components/ui.tsx",
        "src/components/data-table.tsx",
        "src/features/legacy/legacy-section.tsx",
        "src/lib/api.ts",
        "e2e/adminapp-smoke.spec.ts",
    ):
        assert not (ADMINAPP / relative).exists(), relative

    dashboard = (ADMINAPP / "src/components/ops-dashboard.tsx").read_text(encoding="utf-8")
    assert "ActiveOpsRoute" in dashboard
    for forbidden in ("Promise.allSettled", "apiFetch", "fetch(", "@/lib/api", "features/legacy"):
        assert forbidden not in dashboard

    command_palette = (ADMINAPP / "src/components/ops/command-palette.tsx").read_text(encoding="utf-8")
    assert 'from "@/lib/admin-api/client"' in command_palette
    assert 'from "@/lib/api"' not in command_palette


def test_all_routes_and_primary_operator_copy_are_russian() -> None:
    sections = (ADMINAPP / "src/lib/sections.ts").read_text(encoding="utf-8")
    for label in (
        "Главная",
        "Ноды",
        "Трафик",
        "Алерты",
        "Лимиты провайдеров",
        "Экстренная сеть",
        "Бесплатный контур",
        "Пользователи",
        "Сейчас онлайн",
        "Тикеты",
        "Платежи",
        "Воронка",
        "Промо",
        "Рефералы",
        "Релиз",
        "Рассылка",
    ):
        assert f'label: "{label}"' in sections

    accessibility = (ADMINAPP / "e2e/accessibility.spec.ts").read_text(encoding="utf-8")
    for route in (
        "/",
        "/nodes",
        "/traffic",
        "/alerts",
        "/provider-caps",
        "/emergency-network",
        "/free-tier",
        "/users",
        "/online",
        "/tickets",
        "/payments",
        "/funnel",
        "/promos",
        "/referrals",
        "/release",
        "/broadcast",
    ):
        assert f'["{route}",' in accessibility

    visible_sources = [
        *ADMINAPP.glob("src/**/*.ts"),
        *ADMINAPP.glob("src/**/*.tsx"),
    ]
    visible_text = "\n".join(path.read_text(encoding="utf-8") for path in visible_sources)
    assert "Ops admin" not in visible_text
    assert "Free tier" not in visible_text


def test_accessibility_mobile_and_feature_boundaries_remain_explicit() -> None:
    dialog = (ADMINAPP / "src/components/ui/dialog.tsx").read_text(encoding="utf-8")
    for contract in (
        'role="dialog"',
        'aria-modal="true"',
        'event.key === "Escape"',
        "querySelectorAll<HTMLElement>(FOCUSABLE)",
        "restoreFocusRef.current?.focus()",
    ):
        assert contract in dialog

    globals_css = (ADMINAPP / "src/app/globals.css").read_text(encoding="utf-8")
    assert "100dvh" in globals_css
    assert "prefers-reduced-motion: reduce" in globals_css
    assert "font-variant-numeric: tabular-nums" in globals_css
    assert "100vh" not in "\n".join(
        path.read_text(encoding="utf-8")
        for path in [*ADMINAPP.glob("src/**/*.ts"), *ADMINAPP.glob("src/**/*.tsx"), *ADMINAPP.glob("src/**/*.css")]
    )

    feature_root = ADMINAPP / "src/features"
    sibling_import = re.compile(r'from\s+["\']@/features/([^/]+)/')
    for path in [*feature_root.glob("**/*.ts"), *feature_root.glob("**/*.tsx")]:
        if path.name == "registry.tsx":
            continue
        own_domain = path.relative_to(feature_root).parts[0]
        for imported_domain in sibling_import.findall(path.read_text(encoding="utf-8")):
            assert imported_domain == own_domain, f"{path}: imports sibling feature {imported_domain}"

    boundary = (ADMINAPP / "src/components/ops/route-boundary.tsx").read_text(encoding="utf-8")
    assert "Технический код:" in boundary
    assert "ID обращения:" in boundary
