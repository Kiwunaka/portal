import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PUBLIC_COPY_FILES = [
    ROOT / "docs/product/portal-vpn-product.md",
    ROOT / "docs/architecture/system-overview.md",
    ROOT / "docs/architecture/app-first-and-bonus-flows.md",
    ROOT / "docs/operations/deployment-and-access.md",
    ROOT / "docs/developer/developer-guide.md",
    ROOT / "docs/developer/repository-map.md",
    ROOT / "docs/user/portal-vpn-user-guide-ru.md",
]
FRONTEND_COPY_FILES = [
    ROOT / "shared/portal-config.ts",
    ROOT / "shared/public-urls.json",
    ROOT / "shared/product-facts.json",
    ROOT / "copy/catalog.ru.json",
    ROOT / "shared/redesign-spine.json",
]
SHARED_MANIFEST_FILES = [
    ROOT / "shared/redesign-spine.json",
    ROOT / "shared/redesign-assets.json",
]

WEBAPP_PUBLIC_COPY_FILES = [
    ROOT / "webapp/src/app/page.tsx",
    ROOT / "webapp/src/app/(dashboard)/dashboard/page.tsx",
    ROOT / "webapp/src/app/(dashboard)/subscription/page.tsx",
    ROOT / "webapp/src/app/(dashboard)/devices/page.tsx",
    ROOT / "webapp/src/app/(dashboard)/downloads/page.tsx",
    ROOT / "webapp/src/app/(dashboard)/support/page.tsx",
    ROOT / "webapp/src/app/(dashboard)/profile/page.tsx",
]

WEBAPP_ADMIN_COPY_FILES = [
    ROOT / "webapp/src/app/(dashboard)/admin/page.tsx",
    ROOT / "webapp/src/app/(dashboard)/admin/users/page.tsx",
    ROOT / "webapp/src/components/admin/users/admin-user-side-panel.tsx",
]

WORKER3_MARKETING_COPY_FILES = [
    ROOT / "marketing/src/app/checkout/page.tsx",
    ROOT / "marketing/src/app/checkout/checkout-client.tsx",
    ROOT / "marketing/src/app/install/page.tsx",
    ROOT / "marketing/src/app/mobile/page.tsx",
    ROOT / "marketing/src/app/tiktok/page.tsx",
    ROOT / "marketing/src/app/youtube/page.tsx",
    ROOT / "marketing/src/app/devices/page.tsx",
    ROOT / "marketing/src/app/telegram/page.tsx",
    ROOT / "marketing/src/app/offer/page.tsx",
    ROOT / "marketing/src/app/privacy/page.tsx",
    ROOT / "marketing/src/components/marketing-landing.tsx",
    ROOT / "marketing/src/lib/marketing-site.ts",
]

USER_FACING_COPY_FILES = [
    ROOT / "docs/user/portal-vpn-user-guide-ru.md",
]

BACKEND_PUBLIC_COPY_FILES = [
    ROOT / "portal_bot/api.py",
    ROOT / "portal_bot/bot.py",
    ROOT / "portal_bot/helpbot.py",
    ROOT / "portal_bot/feedbackbot.py",
    ROOT / "portal_bot/worker.py",
]

CURRENT_COPY_CONTRACT_FILES = PUBLIC_COPY_FILES + FRONTEND_COPY_FILES + WEBAPP_PUBLIC_COPY_FILES + WEBAPP_ADMIN_COPY_FILES

FIRST_LAYER_APP_CATALOG_PREFIXES = (
    "app.nav.",
    "app.route_mode.",
    "app.connection.",
    "app.trial.",
)

BANNED_PATTERNS = [
    re.compile(r"\b100%\b", re.IGNORECASE),
    re.compile(r"РіР°СЂР°РЅС‚РёСЂРѕРІР°РЅ\w*", re.IGNORECASE),
    re.compile(r"Р±РµР·\s+РѕРіСЂР°РЅРёС‡РµРЅРёР№", re.IGNORECASE),
]

PUBLIC_FORBIDDEN_PATTERNS = [
    re.compile(r"safe checkout flow", re.IGNORECASE),
    re.compile(r"tg_id=", re.IGNORECASE),
    re.compile(r"Telegram\s+Stars", re.IGNORECASE),
    re.compile(r"\bStars\b", re.IGNORECASE),
    re.compile(r"\bPORTAL\b"),
    re.compile(r"@portal_service_bot", re.IGNORECASE),
    re.compile(r"@portal_privacy_helpbot", re.IGNORECASE),
    re.compile(r"portalfeedbackbot", re.IGNORECASE),
    re.compile(r"\bPORTAL VPN\b", re.IGNORECASE),
]

MOJIBAKE_MARKERS = ["Р РЋ", "Р Сџ", "РЎРѓ", "РІР‚", "СЂСџ", "РІС™", "РІСљ", "�"]

PUBLIC_HUMAN_COPY_FORBIDDEN_PATTERNS = [
    re.compile(r"\bVPN\b", re.IGNORECASE),
    re.compile(r"\bcheckout\b", re.IGNORECASE),
    re.compile(r"\bfallback\b", re.IGNORECASE),
    re.compile(r"\bmanaged premium\b", re.IGNORECASE),
    re.compile(r"\btrial\b", re.IGNORECASE),
    re.compile(r"\bscope\b", re.IGNORECASE),
    re.compile(r"\bSNI\b", re.IGNORECASE),
    re.compile(r"\bDNS\b", re.IGNORECASE),
    re.compile(r"\bузл\w*", re.IGNORECASE),
]

PUBLIC_MARKETING_FORBIDDEN_PATTERNS = [
    re.compile(r"\?{3,}"),
    re.compile(r"\bVPN\b", re.IGNORECASE),
    re.compile(r"\bcheckout\b", re.IGNORECASE),
    re.compile(r"\bfallback\b", re.IGNORECASE),
    re.compile(r"\bmanaged premium\b", re.IGNORECASE),
    re.compile(r"\btrial\b", re.IGNORECASE),
    re.compile(r"\bscope\b", re.IGNORECASE),
    re.compile(r"\bSNI\b", re.IGNORECASE),
    re.compile(r"\bDNS\b", re.IGNORECASE),
    re.compile(r"публичн\w+\s+каталог\w*", re.IGNORECASE),
    re.compile(r"raw\s+links?", re.IGNORECASE),
    re.compile(r"техническ\w+\s+ссыл", re.IGNORECASE),
    re.compile(r"техническ\w+\s+сценари", re.IGNORECASE),
    re.compile(r"ручн\w+\s+профил", re.IGNORECASE),
    re.compile(r"сыры\w+\s+персональн\w+\s+ссыл", re.IGNORECASE),
    re.compile(r"continuation", re.IGNORECASE),
    re.compile(r"trust-сценари", re.IGNORECASE),
    re.compile(r"checkout\s+покажет", re.IGNORECASE),
    re.compile(r"ускор\w*", re.IGNORECASE),
    re.compile(r"пинг\w*", re.IGNORECASE),
    re.compile(r"без\s+границ", re.IGNORECASE),
]

PUBLIC_MARKETING_SOURCE_FORBIDDEN_PATTERNS = [
    re.compile(r"\?{3,}"),
    re.compile(r"\bVPN\b", re.IGNORECASE),
    re.compile(r"\bmanaged premium\b", re.IGNORECASE),
    re.compile(r"публичн\w+\s+каталог\w*", re.IGNORECASE),
    re.compile(r"raw\s+links?", re.IGNORECASE),
    re.compile(r"техническ\w+\s+ссыл", re.IGNORECASE),
    re.compile(r"техническ\w+\s+сценари", re.IGNORECASE),
    re.compile(r"ручн\w+\s+профил", re.IGNORECASE),
    re.compile(r"сыры\w+\s+персональн\w+\s+ссыл", re.IGNORECASE),
    re.compile(r"continuation", re.IGNORECASE),
    re.compile(r"trust-сценари", re.IGNORECASE),
    re.compile(r"First-party promo slots", re.IGNORECASE),
    re.compile(r"checkout\s+покажет", re.IGNORECASE),
    re.compile(r"ускор\w*", re.IGNORECASE),
    re.compile(r"пинг\w*", re.IGNORECASE),
    re.compile(r"без\s+границ", re.IGNORECASE),
]
STALE_TRIAL_LENGTH_PATTERNS = [
    re.compile(r"\b7\s*days?\b", re.IGNORECASE),
    re.compile(r"\b7[-\s]?day\b", re.IGNORECASE),
    re.compile(r"\b14\s*days?\b", re.IGNORECASE),
    re.compile(r"\b14[-\s]?day\b", re.IGNORECASE),
    re.compile(r"\b7\s*РґРЅ", re.IGNORECASE),
    re.compile(r"\b7\s*дн", re.IGNORECASE),
]

OLD_SUBTITLE_PATTERNS = [
    re.compile(r"\bPOKROV\s+Network\b", re.IGNORECASE),
    re.compile(r"\bPREMIUM\s+VPN\b", re.IGNORECASE),
]

FIRST_LAYER_APP_TECH_PATTERNS = [
    re.compile(r"\bVPN\b", re.IGNORECASE),
    re.compile(r"\bSNI\b", re.IGNORECASE),
    re.compile(r"\bDNS\b", re.IGNORECASE),
    re.compile(r"\bVLESS\b", re.IGNORECASE),
    re.compile(r"\bVMess\b", re.IGNORECASE),
    re.compile(r"\bTrojan\b", re.IGNORECASE),
    re.compile(r"\bXHTTP\b", re.IGNORECASE),
    re.compile(r"\bxray\b", re.IGNORECASE),
    re.compile(r"\bsing-box\b", re.IGNORECASE),
    re.compile(r"\bsystem\s+proxy\b", re.IGNORECASE),
    re.compile(r"\bservice\s+mode\b", re.IGNORECASE),
    re.compile(r"\bsubscription_url\b", re.IGNORECASE),
    re.compile(r"\bhost:port\b", re.IGNORECASE),
    re.compile(r"raw\s+(?:profile|config)", re.IGNORECASE),
    re.compile(r"(?:profile|config)\s+editor", re.IGNORECASE),
]

FAKE_SUPPORT_PATTERNS = [
    re.compile(r"fake\s+live\s+chat", re.IGNORECASE),
    re.compile(r"imaginary\s+live\s+chat", re.IGNORECASE),
    re.compile(r"realtime\s+in-app\s+chat", re.IGNORECASE),
]

FINAL_POLISH_USER_FACING_FORBIDDEN_PATTERNS = [
    re.compile(r"\bPOKROV\s+VPN\b", re.IGNORECASE),
    re.compile(r"\bPOKROV\s+Network\b", re.IGNORECASE),
    re.compile(r"\bPREMIUM\s+VPN\b", re.IGNORECASE),
    re.compile(r"\bVPN\b", re.IGNORECASE),
    re.compile(r"dev-indicator", re.IGNORECASE),
    re.compile(r"api\.qrserver\.com", re.IGNORECASE),
    re.compile(r"\?format=plain", re.IGNORECASE),
    re.compile(r"\bsubscription_url\b", re.IGNORECASE),
    re.compile(r"\bhost:port\b", re.IGNORECASE),
    re.compile(r"\bpublic\s+IP\b", re.IGNORECASE),
    re.compile(r"\bvless://", re.IGNORECASE),
    re.compile(r"\bvmess://", re.IGNORECASE),
    re.compile(r"\btrojan://", re.IGNORECASE),
    re.compile(r"\braw\s+(?:profile|config|subscription|link)", re.IGNORECASE),
    re.compile(r"(?:profile|config|JSON/profile)\s+editor", re.IGNORECASE),
    *FAKE_SUPPORT_PATTERNS,
]

FINAL_POLISH_ADMIN_BACKEND_FORBIDDEN_PATTERNS = [
    re.compile(r"\bPOKROV\s+VPN\b", re.IGNORECASE),
    re.compile(r"\bPOKROV\s+Network\b", re.IGNORECASE),
    re.compile(r"\bPREMIUM\s+VPN\b", re.IGNORECASE),
    re.compile(r"dev-indicator", re.IGNORECASE),
    *FAKE_SUPPORT_PATTERNS,
]

FINAL_POLISH_CODE_CONTEXT_ALLOWLIST = (
    "android.permission.bind_vpn_service",
    "permissionrequirement.vpnprofile",
    "override_android_vpn",
    "vpn service",
    "pokrovruntimevpnservice",
)


def _resolve_client_app_root() -> Path:
    configured = os.getenv("POKROV_APP_ROOT")
    if configured:
        return Path(configured)

    sibling_worktree = ROOT.parent.parent / "POKROV-app" / ROOT.name
    if sibling_worktree.exists():
        return sibling_worktree

    return Path("C:/Users/kiwun/Documents/ai/POKROV-app")


def _existing(paths: tuple[Path, ...]) -> tuple[Path, ...]:
    return tuple(path for path in paths if path.exists())


def _final_polish_public_surface_groups() -> dict[str, tuple[Path, ...]]:
    client_root = _resolve_client_app_root()
    return {
        "marketing": _existing(tuple(WORKER3_MARKETING_COPY_FILES)),
        "cabinet": _existing(tuple(WEBAPP_PUBLIC_COPY_FILES)),
        "admin": _existing(tuple(WEBAPP_ADMIN_COPY_FILES)),
        "backend": _existing(tuple(BACKEND_PUBLIC_COPY_FILES)),
        "client_app": _existing(
            (
                client_root / "packages" / "app_shell" / "lib" / "app_shell.dart",
                client_root / "apps" / "android_shell" / "lib" / "main.dart",
                client_root / "apps" / "windows_shell" / "lib" / "main.dart",
            )
        ),
    }


def _line_has_final_polish_code_exception(line: str) -> bool:
    lowered = line.lower()
    return any(fragment in lowered for fragment in FINAL_POLISH_CODE_CONTEXT_ALLOWLIST)


def _public_text(path: Path) -> str:
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        items = payload.get("items") or {}
        return "\n".join(str((item or {}).get("ru") or "") for item in items.values())
    return path.read_text(encoding="utf-8")


def _frontend_text_without_legacy_catalog(path: Path) -> str:
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        items = payload.get("items") or {}
        if items:
            return "\n".join(str((item or {}).get("ru") or "") for item in items.values())
        return json.dumps(payload, ensure_ascii=False)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".ts":
        text = re.sub(r"export const LEGACY_PUBLIC_MARKERS = \[(?:.|\n)*?\] as const;\n?", "", text)
    return text


def _public_human_copy_text(path: Path) -> str:
    text = _frontend_text_without_legacy_catalog(path)
    text = re.sub(r"https?://\S+", "", text)
    if path.name == "portal-vpn-user-guide-ru.md":
        kept_lines = []
        for line in text.splitlines():
            lowered = line.lower()
            if (
                "legacy" in lowered
                or "историчес" in lowered
                or "portal-vpn-user-guide-ru.md" in lowered
                or "старых названиях" in lowered
            ):
                continue
            kept_lines.append(line)
        return "\n".join(kept_lines)
    return text


def _catalog_allowed_public_ru_text(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload.get("items") or {}
    return "\n".join(
        str((item or {}).get("ru") or "")
        for item in items.values()
        if (item or {}).get("allowed_public") is True
    )


def _catalog_items() -> dict[str, dict]:
    payload = json.loads((ROOT / "copy/catalog.ru.json").read_text(encoding="utf-8"))
    return payload.get("items") or {}


def _catalog_ru_values() -> list[tuple[str, str]]:
    return [(key, str((item or {}).get("ru") or "")) for key, item in _catalog_items().items()]


def _walk_json_strings(value: object, path: str = "$") -> list[tuple[str, str]]:
    if isinstance(value, str):
        return [(path, value)]
    if isinstance(value, list):
        strings: list[tuple[str, str]] = []
        for index, item in enumerate(value):
            strings.extend(_walk_json_strings(item, f"{path}[{index}]"))
        return strings
    if isinstance(value, dict):
        strings: list[tuple[str, str]] = []
        for key, item in value.items():
            strings.extend(_walk_json_strings(item, f"{path}.{key}"))
        return strings
    return []


def test_public_copy_has_no_banned_claims() -> None:
    violations: list[str] = []
    for path in PUBLIC_COPY_FILES:
        text = _public_text(path)
        for pattern in BANNED_PATTERNS:
            for match in pattern.finditer(text):
                snippet = text[max(0, match.start() - 30):match.end() + 30].replace("\n", " ")
                violations.append(f"{path.relative_to(ROOT)}: /{pattern.pattern}/ -> {snippet}")
    assert not violations, "\n".join(violations)


def test_public_copy_has_no_forbidden_public_terms() -> None:
    violations: list[str] = []
    for path in PUBLIC_COPY_FILES:
        text = _public_text(path)
        for pattern in PUBLIC_FORBIDDEN_PATTERNS:
            for match in pattern.finditer(text):
                snippet = text[max(0, match.start() - 30):match.end() + 30].replace("\n", " ")
                violations.append(f"{path.relative_to(ROOT)}: /{pattern.pattern}/ -> {snippet}")
    assert not violations, "\n".join(violations)


def test_public_copy_has_no_mojibake_markers() -> None:
    violations: list[str] = []
    for path in PUBLIC_COPY_FILES:
        text = _public_text(path)
        for marker in MOJIBAKE_MARKERS:
            if marker in text:
                violations.append(f"{path.relative_to(ROOT)}: found mojibake marker {marker!r}")
    assert not violations, "\n".join(violations)


def test_user_facing_copy_avoids_public_jargon_and_direct_vpn_wording() -> None:
    violations: list[str] = []
    for path in USER_FACING_COPY_FILES:
        text = _public_human_copy_text(path)
        for pattern in PUBLIC_HUMAN_COPY_FORBIDDEN_PATTERNS:
            for match in pattern.finditer(text):
                snippet = text[max(0, match.start() - 30):match.end() + 30].replace("\n", " ")
                violations.append(f"{path.relative_to(ROOT)}: /{pattern.pattern}/ -> {snippet}")
    assert not violations, "\n".join(violations)


def test_worker3_public_marketing_copy_stays_human_and_policy_safe() -> None:
    violations: list[str] = []
    catalog_text = _catalog_allowed_public_ru_text(ROOT / "copy/catalog.ru.json")

    for pattern in PUBLIC_MARKETING_FORBIDDEN_PATTERNS:
        for match in pattern.finditer(catalog_text):
            snippet = catalog_text[max(0, match.start() - 30):match.end() + 30].replace("\n", " ")
            violations.append(f"copy/catalog.ru.json: /{pattern.pattern}/ -> {snippet}")

    for path in WORKER3_MARKETING_COPY_FILES:
        text = path.read_text(encoding="utf-8")
        for pattern in PUBLIC_MARKETING_SOURCE_FORBIDDEN_PATTERNS:
            for match in pattern.finditer(text):
                snippet = text[max(0, match.start() - 30):match.end() + 30].replace("\n", " ")
                violations.append(f"{path.relative_to(ROOT)}: /{pattern.pattern}/ -> {snippet}")

    assert not violations, "\n".join(violations)


def test_frontend_public_copy_catalogs_stay_pokrov_only() -> None:
    violations: list[str] = []
    portal_config_required_snippets = (
        'from "./product-facts"',
        'from "./public-urls"',
        "CANONICAL_CLIENT_BRAND",
        "CANONICAL_API_BASE_URL",
        "CANONICAL_WEBAPP_URL",
        "CANONICAL_CONNECT_URL",
        "CANONICAL_CHECKOUT_URL",
        "CANONICAL_BOT_URL",
        "CANONICAL_SUPPORT_BOT_URL",
        "CANONICAL_FEEDBACK_BOT_URL",
        "CANONICAL_NEWS_CHANNEL_URL",
    )
    public_urls_required_snippets = (
        "https://api.pokrov.space",
        "https://app.pokrov.space",
        "https://connect.pokrov.space",
        "https://pay.pokrov.space",
        "https://t.me/pokrov_vpnbot",
        "https://t.me/pokrov_supportbot",
        "https://t.me/pokrov_feedbackbot",
        "https://t.me/pokrov_vpn",
    )
    product_facts_required_snippets = (
        '"platform": "POKROV"',
        '"client": "POKROV"',
    )
    forbidden_markers = (
        "portal-privacy.online",
        "kiwunaka.space",
        "portal_service_bot",
        "portal_privacy_helpbot",
        "portalfeedbackbot",
        "PORTAL ENTRY",
    )

    for path in FRONTEND_COPY_FILES:
        text = _frontend_text_without_legacy_catalog(path)
        for marker in MOJIBAKE_MARKERS:
            if marker in text:
                violations.append(f"{path.relative_to(ROOT)}: found mojibake marker {marker!r}")
        if path.name == "portal-config.ts":
            for snippet in portal_config_required_snippets:
                if snippet not in text:
                    violations.append(f"{path.relative_to(ROOT)}: missing required snippet {snippet}")
        elif path.name == "public-urls.json":
            for snippet in public_urls_required_snippets:
                if snippet not in text:
                    violations.append(f"{path.relative_to(ROOT)}: missing required snippet {snippet}")
        elif path.name == "product-facts.json":
            for snippet in product_facts_required_snippets:
                if snippet not in text:
                    violations.append(f"{path.relative_to(ROOT)}: missing required snippet {snippet}")
        if path.name != "product-facts.json":
            for marker in forbidden_markers:
                if marker in text:
                    violations.append(f"{path.relative_to(ROOT)}: found forbidden legacy marker {marker}")

    assert not violations, "\n".join(violations)


def test_governed_copy_has_no_old_subtitle_or_stale_seven_day_trial() -> None:
    violations: list[str] = []

    for path in CURRENT_COPY_CONTRACT_FILES:
        text = _frontend_text_without_legacy_catalog(path) if path in FRONTEND_COPY_FILES else _public_text(path)
        for pattern in STALE_TRIAL_LENGTH_PATTERNS:
            for match in pattern.finditer(text):
                snippet = text[max(0, match.start() - 30):match.end() + 30].replace("\n", " ")
                violations.append(f"{path.relative_to(ROOT)}: stale trial length /{pattern.pattern}/ -> {snippet}")

    for key, text in _catalog_ru_values():
        for pattern in OLD_SUBTITLE_PATTERNS:
            for match in pattern.finditer(text):
                snippet = text[max(0, match.start() - 30):match.end() + 30].replace("\n", " ")
                violations.append(f"copy/catalog.ru.json:{key}: old subtitle /{pattern.pattern}/ -> {snippet}")

    assert not violations, "\n".join(violations)


def test_webapp_and_admin_copy_avoid_fake_support_promises() -> None:
    violations: list[str] = []

    for path in WEBAPP_PUBLIC_COPY_FILES + WEBAPP_ADMIN_COPY_FILES + BACKEND_PUBLIC_COPY_FILES:
        text = path.read_text(encoding="utf-8")
        for pattern in FAKE_SUPPORT_PATTERNS:
            for match in pattern.finditer(text):
                snippet = text[max(0, match.start() - 30):match.end() + 30].replace("\n", " ")
                violations.append(f"{path.relative_to(ROOT)}: fake support promise /{pattern.pattern}/ -> {snippet}")

    assert not violations, "\n".join(violations)


def test_shared_manifests_have_no_workstation_paths_outside_temporary_logo_exception() -> None:
    violations: list[str] = []
    absolute_workstation_path = re.compile(r"\b[A-Za-z]:[\\/](?:Users|Documents)[\\/]", re.IGNORECASE)
    allowed_temporary_logo_keys = (
        "$.asset_policy.canonical_mark_source",
        "$.brand.canonical_mark.source_path",
        "$.brand.optimized.mark_svg.source_path",
        "$.brand.optimized.mark_png.source_path",
        "$.brand.optimized.mark_png_compact.source_path",
        "$.brand.optimized.favicon_png.source_path",
        "$.brand.optimized.favicon_svg.source_path",
        "$.brand.optimized.favicon_ico.source_path",
        "$.brand.optimized.apple_touch_icon.source_path",
        "$.brand.optimized.android_icon.source_path",
        "$.brand.optimized.windows_icon.source_path",
    )

    for path in SHARED_MANIFEST_FILES:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for key_path, value in _walk_json_strings(payload):
            if not absolute_workstation_path.search(value):
                continue
            if key_path in allowed_temporary_logo_keys and "logogo.png" in value.replace("\\", "/"):
                continue
            violations.append(f"{path.relative_to(ROOT)}:{key_path}: {value}")

    assert not violations, "\n".join(violations)


def test_public_catalog_items_have_no_direct_vpn_wording() -> None:
    violations: list[str] = []

    skipped_jargon_patterns = {
        r"\bcheckout\b",
        r"\bfallback\b",
        r"\bmanaged premium\b",
        r"\btrial\b",
        r"\bscope\b",
    }
    for key, item in _catalog_items().items():
        if not (item or {}).get("allowed_public"):
            continue
        text = str((item or {}).get("ru") or "")
        for pattern in PUBLIC_HUMAN_COPY_FORBIDDEN_PATTERNS:
            if pattern.pattern in skipped_jargon_patterns:
                continue
            for match in pattern.finditer(text):
                snippet = text[max(0, match.start() - 30):match.end() + 30].replace("\n", " ")
                violations.append(f"copy/catalog.ru.json:{key}: /{pattern.pattern}/ -> {snippet}")

    assert not violations, "\n".join(violations)


def test_backend_and_bot_public_copy_stays_pokrov_app_first() -> None:
    forbidden_literals = (
        "POKROV VPN",
        "TRIAL_10GB_7",
    )
    stale_public_trial_patterns = (
        re.compile(r"/gift\s+\[tg_id\]\s+trial.*7", re.IGNORECASE),
        re.compile(r'"trial"\s*:\s*\{\s*"days"\s*:\s*7', re.IGNORECASE),
    )
    violations: list[str] = []

    for path in BACKEND_PUBLIC_COPY_FILES:
        text = path.read_text(encoding="utf-8")
        for literal in forbidden_literals:
            if literal in text:
                violations.append(f"{path.relative_to(ROOT)}: found forbidden backend copy {literal!r}")
        for pattern in stale_public_trial_patterns:
            for match in pattern.finditer(text):
                snippet = text[max(0, match.start() - 30):match.end() + 30].replace("\n", " ")
                violations.append(f"{path.relative_to(ROOT)}: stale backend trial copy /{pattern.pattern}/ -> {snippet}")

    assert not violations, "\n".join(violations)


def test_backend_and_bot_first_layer_copy_hides_raw_networking_and_keeps_key_first_language() -> None:
    allowed_fragments = (
        "legacy",
        "compat",
        "manual",
        "recovery",
        "admin",
        "diagnostic",
        "operator",
        "advanced",
        "оплат",
        "привяз",
        "реферал",
        "подароч",
        "launch",
        "show_key",
        "copy_key",
        "восстанов",
        "сброс",
        "vless://uuid@host:port",
        "subscription_url",
    )
    direct_vpn = re.compile(r"\bVPN\b", re.IGNORECASE)
    raw_first_layer_patterns = (
        re.compile(r"raw\s+(?:profile|config)", re.IGNORECASE),
        re.compile(r"(?:profile|config)\s+editor", re.IGNORECASE),
        re.compile(r"JSON/profile\s+editor", re.IGNORECASE),
        re.compile(r"\bsystem\s+proxy\b", re.IGNORECASE),
        re.compile(r"\bservice\s+mode\b", re.IGNORECASE),
        re.compile(r"\braw\s+node\b", re.IGNORECASE),
        re.compile(r"ссылк[ауи] для подключения", re.IGNORECASE),
        re.compile(r"скопируйте ссылку", re.IGNORECASE),
        re.compile(r"личн\w+\s+ссылк\w+\s+доступ", re.IGNORECASE),
    )
    key_language = re.compile(r"ключ (?:доступа|активации)|activation[- ]key", re.IGNORECASE)
    violations: list[str] = []
    key_language_hits = 0

    for path in BACKEND_PUBLIC_COPY_FILES:
        lines = path.read_text(encoding="utf-8").splitlines()
        for line_no, line in enumerate(lines, start=1):
            lowered = line.lower()
            context = "\n".join(lines[max(0, line_no - 8):line_no + 1]).lower()
            is_allowed_context = any(fragment in lowered or fragment in context for fragment in allowed_fragments)
            if direct_vpn.search(line) and not is_allowed_context:
                violations.append(f"{path.relative_to(ROOT)}:{line_no}: direct VPN wording -> {line.strip()}")
            for pattern in raw_first_layer_patterns:
                if pattern.search(line) and not is_allowed_context:
                    violations.append(f"{path.relative_to(ROOT)}:{line_no}: raw first-layer copy /{pattern.pattern}/ -> {line.strip()}")
            if key_language.search(line):
                key_language_hits += 1

    assert key_language_hits >= 1
    assert not violations, "\n".join(violations)


def test_first_layer_app_catalog_copy_avoids_technical_terms() -> None:
    violations: list[str] = []

    for key, text in _catalog_ru_values():
        if not key.startswith(FIRST_LAYER_APP_CATALOG_PREFIXES):
            continue
        for pattern in FIRST_LAYER_APP_TECH_PATTERNS:
            for match in pattern.finditer(text):
                snippet = text[max(0, match.start() - 30):match.end() + 30].replace("\n", " ")
                violations.append(f"copy/catalog.ru.json:{key}: /{pattern.pattern}/ -> {snippet}")

    assert not violations, "\n".join(violations)


def test_redesign_spine_uses_one_current_contract_path() -> None:
    spine = json.loads((ROOT / "shared/redesign-spine.json").read_text(encoding="utf-8"))

    assert spine["version"] == "2026-04-23-full-redesign"
    assert spine["visual_direction"]["name"] == "white-mint premium utility"
    assert spine["brand"]["subtitle"] == ""
    assert "legacy_path" not in spine
    assert "dual_path" not in spine
    assert "old_redesign" not in spine


def test_public_copy_pack_is_present_on_canonical_docs() -> None:
    expected_substrings = {
        ROOT / "docs/product/portal-vpn-product.md": [
            "POKROV VPN",
            "@pokrov_feedbackbot",
            "mikh****",
            "key-first trial starts from the site, bot, or app",
            "hybrid paid flow",
            "temporary visible logo asset exception",
        ],
        ROOT / "docs/architecture/system-overview.md": [
            "GET /api/reviews",
            "visible nicknames are masked in a friendly format such as `mikh****`",
            "web-session-only admin",
            "no deploy is part of this polish wave",
        ],
        ROOT / "docs/architecture/app-first-and-bonus-flows.md": [
            "operator approves selected reviews for public display",
            "mikh****",
            "selected-app scan MVP",
            "hybrid paid flow",
        ],
        ROOT / "docs/developer/developer-guide.md": [
            "Final polish QA checklist",
            "web-session-only admin",
            "no deploy in this wave",
        ],
        ROOT / "docs/developer/repository-map.md": [
            "tests/test_redesign_spine.py",
            "tests/test_ui_visual_smoke.py",
            "final polish guardrail pack",
        ],
        ROOT / "docs/operations/deployment-and-access.md": [
            "@pokrov_feedbackbot",
            "public review feed loads with masked usernames",
        ],
        ROOT / "docs/user/portal-vpn-user-guide-ru.md": [
            "Публичные отзывы показываются с маскировкой ника, например `mikh****`",
        ],
    }

    missing: list[str] = []
    for path, snippets in expected_substrings.items():
        text = path.read_text(encoding="utf-8")
        for snippet in snippets:
            if snippet not in text:
                missing.append(f"{path.relative_to(ROOT)} missing: {snippet}")

    assert not missing, "\n".join(missing)


def test_final_polish_public_surfaces_have_guardrail_inventory() -> None:
    surface_groups = _final_polish_public_surface_groups()

    assert {"marketing", "cabinet", "admin", "backend", "client_app"} <= set(surface_groups)
    for group_name, paths in surface_groups.items():
        assert paths, f"{group_name} has no guardrail files"


def test_final_polish_public_surfaces_avoid_banned_user_facing_wording() -> None:
    violations: list[str] = []

    surface_groups = _final_polish_public_surface_groups()
    for group_name, paths in surface_groups.items():
        patterns = (
            FINAL_POLISH_ADMIN_BACKEND_FORBIDDEN_PATTERNS
            if group_name in {"admin", "backend"}
            else FINAL_POLISH_USER_FACING_FORBIDDEN_PATTERNS
        )
        for path in paths:
            for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
                if _line_has_final_polish_code_exception(line):
                    continue
                for pattern in patterns:
                    if pattern.search(line):
                        violations.append(
                            f"{group_name}:{path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}:{line_no}: "
                            f"/{pattern.pattern}/ -> {line.strip()}"
                        )

    assert not violations, "\n".join(violations)
