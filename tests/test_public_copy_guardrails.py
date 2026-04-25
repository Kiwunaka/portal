import json
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
]

BANNED_PATTERNS = [
    re.compile(r"\b100%\b", re.IGNORECASE),
    re.compile(r"гарантирован\w*", re.IGNORECASE),
    re.compile(r"без\s+ограничений", re.IGNORECASE),
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

PUBLIC_BETA_SURFACE_FILES = [
    ROOT / "marketing/src/components/marketing-landing.tsx",
    ROOT / "marketing/src/app/checkout/page.tsx",
    ROOT / "marketing/src/app/checkout/checkout-client.tsx",
    ROOT / "marketing/src/components/home/homepage.tsx",
    ROOT / "webapp/src/app/loading.tsx",
    ROOT / "webapp/src/components/cabinet/downloads-surface.tsx",
]

PUBLIC_BETA_SURFACE_FORBIDDEN_PATTERNS = [
    re.compile(r"Paid beta", re.IGNORECASE),
    re.compile(r"оплачиваемая\s+бета", re.IGNORECASE),
    re.compile(r"ограничен[а-яё\s]+приглаш", re.IGNORECASE),
    re.compile(r"до\s+25\s+активн", re.IGNORECASE),
    re.compile(r"00:12:34"),
    re.compile(r"Email signup\s+на\s+сайте\s+да[её]т", re.IGNORECASE),
]


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


def test_public_beta_surfaces_do_not_expose_stale_limited_beta_copy() -> None:
    violations: list[str] = []
    for path in PUBLIC_BETA_SURFACE_FILES:
        text = path.read_text(encoding="utf-8")
        for pattern in PUBLIC_BETA_SURFACE_FORBIDDEN_PATTERNS:
            for match in pattern.finditer(text):
                snippet = text[max(0, match.start() - 30):match.end() + 30].replace("\n", " ")
                violations.append(f"{path.relative_to(ROOT)}: /{pattern.pattern}/ -> {snippet}")

    checkout_page = (ROOT / "marketing/src/app/checkout/page.tsx").read_text(encoding="utf-8")
    if "noIndex: true" in checkout_page:
        violations.append("marketing/src/app/checkout/page.tsx: checkout route must not be noindexed for public beta")

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
        "POKROV Network",
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


def test_public_copy_pack_is_present_on_canonical_docs() -> None:
    expected_substrings = {
        ROOT / "docs/product/portal-vpn-product.md": [
            "POKROV VPN",
            "@pokrov_feedbackbot",
            "mikh****",
        ],
        ROOT / "docs/architecture/system-overview.md": [
            "GET /api/reviews",
            "visible nicknames are masked in a friendly format such as `mikh****`",
        ],
        ROOT / "docs/architecture/app-first-and-bonus-flows.md": [
            "operator approves selected reviews for public display",
            "mikh****",
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
