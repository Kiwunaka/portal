from __future__ import annotations

import argparse
import ast
import csv
import json
import posixpath
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _resolve_client_root(platform_checkout: Path) -> Path:
    common_dir = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=platform_checkout,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    client_repo = Path(common_dir).resolve().parent.parent / "POKROV-app"
    if not (client_repo / ".git").exists():
        return client_repo
    worktrees = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=client_repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    for block in worktrees.strip().split("\n\n"):
        fields = dict(line.split(" ", 1) for line in block.splitlines() if " " in line)
        if fields.get("branch") == "refs/heads/main" and fields.get("worktree"):
            return Path(fields["worktree"]).resolve()
    return client_repo


DEFAULT_CLIENT_ROOT = _resolve_client_root(REPO_ROOT)
DEFAULT_OUT = REPO_ROOT / "docs" / "developer" / "pokrov-code-function-inventory.csv"
DEFAULT_SYMBOL_COVERAGE_OUT = REPO_ROOT / "docs" / "developer" / "pokrov-symbol-coverage-audit.csv"
DEFAULT_TRACKER = REPO_ROOT / "docs" / "developer" / "pokrov-canonical-feature-tracker.csv"
DEFAULT_ENTRYPOINT_COVERAGE = REPO_ROOT / "docs" / "developer" / "pokrov-entrypoint-story-coverage.csv"
DEFAULT_SCRIPT_MANIFEST = REPO_ROOT / "scripts" / "manifest.yaml"
TODAY = "2026-07-21"

EXCLUDED_PARTS = {
    ".dart_tool",
    ".git",
    ".next",
    ".pytest_cache",
    ".tmp",
    "build",
    "coverage",
    "docs",
    "e2e",
    "ephemeral",
    "frameworks",
    "generated",
    "legacy",
    "node_modules",
    "out",
    "outputs",
    "runnertests",
    "test",
    "tests",
    "__pycache__",
}
ROOT_INCLUDED_DIRS = {"portal_bot", "scripts", "shared", "webapp", "marketing"}
CLIENT_INCLUDED_DIRS = {"apps", "packages", "lib", "scripts"}
SOURCE_SUFFIXES = {".py", ".ts", ".tsx", ".dart", ".kt", ".kts", ".java", ".swift", ".cpp", ".cc", ".cxx", ".h", ".hpp"}
TEST_FILE_PATTERNS = ("test_", ".spec.", ".test.")
NON_PRODUCT_COVERAGE_TEST_NAMES = {
    "test_code_function_inventory.py",
}
GENERATED_FILE_STEMS = {"generatedpluginregistrant", "buildconfig"}
TELEGRAM_BOT_FILE_NAMES = {"bot.py", "helpbot.py", "feedbackbot.py", "legacy_redirect_bot.py"}
TELEGRAM_HANDLER_DECORATOR_MARKERS = (
    "router.callback_query(",
    "router.message(",
    "router.pre_checkout_query(",
)
HTTP_ROUTE_DECORATOR_MARKERS = tuple(
    f"{prefix}.{method}("
    for prefix in ("app", "api", "router")
    for method in (
        "api_route",
        "delete",
        "get",
        "head",
        "options",
        "patch",
        "post",
        "put",
        "websocket",
    )
)


@dataclass(frozen=True)
class Symbol:
    root_label: str
    path: Path
    language: str
    subsystem: str
    symbol_kind: str
    qualified_name: str
    name: str
    parent: str
    visibility: str
    line: int
    end_line: int
    is_async: bool
    decorators_or_modifiers: str
    doc_or_signature: str
    entrypoint_hint: str
    parser_note: str


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def _single_line(value: object) -> str:
    text = "" if value is None else str(value)
    return re.sub(r"\s+", " ", text).strip()


def _dedupe_strings(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _skip_path(path: Path, root: Path, included_dirs: set[str]) -> bool:
    rel = path.relative_to(root)
    if rel.parts and rel.parts[0] not in included_dirs:
        return True
    lower_parts = {part.lower() for part in rel.parts}
    if lower_parts & EXCLUDED_PARTS:
        return True
    if path.stem.lower() in GENERATED_FILE_STEMS:
        return True
    if rel.parts and rel.parts[0] != "scripts" and any(pattern in path.name for pattern in TEST_FILE_PATTERNS):
        return True
    return path.suffix.lower() not in SOURCE_SUFFIXES


def _subsystem(path: Path) -> str:
    parts = path.as_posix().split("/")
    if "portal_bot" in parts:
        return "Backend and Telegram bots"
    if "scripts" in parts:
        return "Scripts and Ops"
    if "webapp" in parts:
        return "WebApp and Admin"
    if "marketing" in parts:
        return "Marketing site"
    if "shared" in parts:
        return "Shared constants"
    if "POKROV-app" in parts or "packages" in parts or "apps" in parts:
        return "POKROV client app"
    return "Other source"


def _visibility(name: str) -> str:
    if name.startswith("__") and name.endswith("__"):
        return "dunder"
    if name.startswith("_"):
        return "private"
    return "public"


def _decorators(node: ast.AST) -> str:
    decorators = getattr(node, "decorator_list", [])
    return _single_line("; ".join(ast.unparse(item) for item in decorators))


def _doc_or_signature(source_lines: list[str], node: ast.AST) -> str:
    doc = ast.get_docstring(node) if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) else None
    if doc:
        return _single_line(doc.strip().splitlines()[0])[:240]
    lineno = getattr(node, "lineno", 1)
    if 1 <= lineno <= len(source_lines):
        return _single_line(source_lines[lineno - 1])[:240]
    return ""


def _entrypoint_hint(path: Path, name: str, decorators: str) -> str:
    path_text = path.as_posix()
    if "portal_bot" in path.parts and path.name in TELEGRAM_BOT_FILE_NAMES:
        if any(marker in decorators for marker in TELEGRAM_HANDLER_DECORATOR_MARKERS):
            return "telegram_handler"
    if "app.middleware(" in decorators or "api.middleware(" in decorators or "router.middleware(" in decorators:
        return "fastapi_middleware"
    if any(marker in decorators for marker in HTTP_ROUTE_DECORATOR_MARKERS):
        return "fastapi_route_handler"
    if path_text.startswith("scripts/") and name == "main":
        return "script_cli_main"
    if path_text.endswith("/page.tsx") and name.lower() in {"page", "default"}:
        return "next_page_component"
    if path_text.endswith("/mainactivity.kt") and name == "MainActivity":
        return "android_activity"
    if path_text.endswith("/appdelegate.swift"):
        return "apple_app_delegate"
    if path_text.endswith("/main.cpp") and name.lower() in {"main", "winmain", "wwinmain"}:
        return "windows_entrypoint"
    if name == "build":
        return "framework_override"
    return ""


def parse_python(path: Path, rel_path: str, root_label: str, root: Path) -> list[Symbol]:
    text = _read_text(path)
    lines = text.splitlines()
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return [
            Symbol(
                root_label,
                path,
                "python",
                _subsystem(path),
                "parse_error",
                rel_path,
                path.name,
                "",
                "",
                int(getattr(exc, "lineno", 0) or 0),
                int(getattr(exc, "lineno", 0) or 0),
                False,
                "",
                str(exc),
                "",
                "python_ast_parse_error",
            )
        ]

    out: list[Symbol] = []

    def visit(node: ast.AST, parents: list[str]) -> None:
        if isinstance(node, ast.ClassDef):
            qn = ".".join([*parents, node.name]) if parents else node.name
            dec = _decorators(node)
            out.append(
                Symbol(
                    root_label,
                    path,
                    "python",
                    _subsystem(path),
                    "class",
                    qn,
                    node.name,
                    ".".join(parents),
                    _visibility(node.name),
                    node.lineno,
                    int(getattr(node, "end_lineno", node.lineno) or node.lineno),
                    False,
                    dec,
                    _doc_or_signature(lines, node),
                    _entrypoint_hint(Path(rel_path), node.name, dec),
                    "python_ast",
                )
            )
            for child in node.body:
                visit(child, [*parents, node.name])
            return
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            qn = ".".join([*parents, node.name]) if parents else node.name
            dec = _decorators(node)
            kind = "method" if parents else "function"
            out.append(
                Symbol(
                    root_label,
                    path,
                    "python",
                    _subsystem(path),
                    kind,
                    qn,
                    node.name,
                    ".".join(parents),
                    _visibility(node.name),
                    node.lineno,
                    int(getattr(node, "end_lineno", node.lineno) or node.lineno),
                    isinstance(node, ast.AsyncFunctionDef),
                    dec,
                    _doc_or_signature(lines, node),
                    _entrypoint_hint(Path(rel_path), node.name, dec),
                    "python_ast",
                )
            )
            for child in node.body:
                visit(child, [*parents, node.name])
            return
        for child in ast.iter_child_nodes(node):
            visit(child, parents)

    visit(tree, [])
    return out


TS_CLASS_RE = re.compile(r"^\s*(?:export\s+)?(?:default\s+)?class\s+([A-Za-z_$][\w$]*)")
TS_FUNCTION_RE = re.compile(
    r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\("
)
TS_ARROW_RE = re.compile(
    r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*[:=].*=>"
)
TS_METHOD_RE = re.compile(
    r"^\s*(?:public\s+|private\s+|protected\s+|static\s+|async\s+)*([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*[:\w<>,\s|]*\{?\s*$"
)


def _brace_delta(line: str) -> int:
    stripped = re.sub(r"(['\"]).*?\1", "", line)
    return stripped.count("{") - stripped.count("}")


def parse_typescript_like(path: Path, rel_path: str, root_label: str, root: Path) -> list[Symbol]:
    text = _read_text(path)
    lines = text.splitlines()
    language = "tsx" if path.suffix.lower() == ".tsx" else "typescript"
    out: list[Symbol] = []
    class_stack: list[tuple[str, int, str]] = []
    brace_depth = 0

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        while class_stack and brace_depth < class_stack[-1][1]:
            class_stack.pop()

        match = TS_CLASS_RE.match(line)
        if match:
            name = match.group(1)
            is_exported = bool(re.match(r"^\s*export\b", line))
            visibility = _visibility(name) if is_exported else "private"
            out.append(
                Symbol(
                    root_label,
                    path,
                    language,
                    _subsystem(path),
                    "class",
                    name,
                    name,
                    "",
                    visibility,
                    idx,
                    idx,
                    False,
                    "export" if is_exported else "",
                    _single_line(stripped)[:240],
                    "",
                    "typescript_regex",
                )
            )
            class_stack.append((name, brace_depth + max(_brace_delta(line), 1), visibility))
        else:
            match = TS_FUNCTION_RE.match(line) or TS_ARROW_RE.match(line)
            if match:
                name = match.group(1)
                parent = class_stack[-1][0] if class_stack else ""
                parent_visibility = class_stack[-1][2] if class_stack else ""
                is_exported = bool(re.match(r"^\s*export\b", line))
                kind = "method" if parent else "function"
                qn = f"{parent}.{name}" if parent else name
                if parent:
                    visibility = "private" if parent_visibility == "private" else _visibility(name)
                else:
                    visibility = _visibility(name) if is_exported else "private"
                out.append(
                    Symbol(
                        root_label,
                        path,
                        language,
                        _subsystem(path),
                        kind,
                        qn,
                        name,
                        parent,
                        visibility,
                        idx,
                        idx,
                        "async" in line,
                        "export" if is_exported else "",
                        _single_line(stripped)[:240],
                        _entrypoint_hint(Path(rel_path), name, ""),
                        "typescript_regex",
                    )
                )
            elif class_stack:
                match = TS_METHOD_RE.match(line)
                if match and not stripped.startswith(("if ", "for ", "while ", "switch ", "catch ", "function ")):
                    name = match.group(1)
                    if name not in {"constructor"}:
                        parent, _parent_depth, parent_visibility = class_stack[-1]
                        method_visibility = _visibility(name)
                        if parent_visibility == "private" or stripped.startswith(("private ", "protected ")):
                            method_visibility = "private"
                        out.append(
                            Symbol(
                                root_label,
                                path,
                                language,
                                _subsystem(path),
                                "method",
                                f"{parent}.{name}",
                                name,
                                parent,
                                method_visibility,
                                idx,
                                idx,
                                "async" in line,
                                "",
                                _single_line(stripped)[:240],
                                "",
                                "typescript_regex",
                            )
                        )
        brace_depth += _brace_delta(line)
    return out


DART_CLASS_RE = re.compile(r"^\s*(?:abstract\s+)?class\s+([A-Za-z_]\w*)")
DART_FUNCTION_RE = re.compile(
    r"^\s*(?:(?:static|external|factory|async)\s+)*(?:[A-Za-z_<>,?][\w<>,\s?]*\s+)?([A-Za-z_]\w*)\s*\([^;]*\)\s*(?:async\s*)?(?:\{|=>)"
)
DART_STATEMENT_PREFIXES = (
    "if ",
    "for ",
    "while ",
    "switch ",
    "catch ",
    "await ",
    "return ",
    "final ",
    "const ",
    "var ",
    "throw ",
)


def parse_dart(path: Path, rel_path: str, root_label: str, root: Path) -> list[Symbol]:
    lines = _read_text(path).splitlines()
    out: list[Symbol] = []
    class_stack: list[tuple[str, int, str]] = []
    pending_class: tuple[str, str] | None = None
    brace_depth = 0
    skip_function_parse_until = 0
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        while class_stack and brace_depth < class_stack[-1][1]:
            class_stack.pop()
        match = DART_CLASS_RE.match(line)
        if match:
            name = match.group(1)
            visibility = _visibility(name)
            out.append(
                Symbol(root_label, path, "dart", _subsystem(path), "class", name, name, "", visibility, idx, idx, False, "", _single_line(stripped)[:240], "", "dart_regex")
            )
            delta = _brace_delta(line)
            if delta > 0:
                class_stack.append((name, brace_depth + delta, visibility))
                pending_class = None
            else:
                pending_class = (name, visibility)
        else:
            if pending_class and "{" in line:
                pending_name, pending_visibility = pending_class
                class_stack.append((pending_name, brace_depth + max(_brace_delta(line), 1), pending_visibility))
                pending_class = None
            function_candidate = line
            function_signature_end = idx
            if idx > skip_function_parse_until and "(" in line and not stripped.startswith(DART_STATEMENT_PREFIXES):
                open_parens = line.count("(") - line.count(")")
                lookahead = idx
                while (
                    lookahead < len(lines)
                    and lookahead < idx + 12
                    and (open_parens > 0 or ("{" not in function_candidate and "=>" not in function_candidate))
                ):
                    next_line = lines[lookahead].strip()
                    function_candidate = f"{function_candidate} {next_line}"
                    open_parens += next_line.count("(") - next_line.count(")")
                    lookahead += 1
                    function_signature_end = lookahead
                    if open_parens <= 0 and ("{" in function_candidate or "=>" in function_candidate):
                        break
            match = DART_FUNCTION_RE.match(function_candidate) if idx > skip_function_parse_until else None
            if match and not stripped.startswith(DART_STATEMENT_PREFIXES):
                if function_signature_end > idx:
                    skip_function_parse_until = function_signature_end
                name = match.group(1)
                parent = class_stack[-1][0] if class_stack else ""
                parent_visibility = class_stack[-1][2] if class_stack else ""
                kind = "method" if parent else "function"
                visibility = "private" if parent_visibility == "private" else _visibility(name)
                out.append(
                    Symbol(
                        root_label,
                        path,
                        "dart",
                        _subsystem(path),
                        kind,
                        f"{parent}.{name}" if parent else name,
                        name,
                        parent,
                        visibility,
                        idx,
                        idx,
                        "async" in function_candidate,
                        "",
                        _single_line(function_candidate.strip())[:240],
                        _entrypoint_hint(Path(rel_path), name, ""),
                        "dart_regex",
                    )
                )
        brace_depth += _brace_delta(line)
    return out


KOTLIN_TYPE_RE = re.compile(r"^\s*(?:data\s+|sealed\s+|abstract\s+|open\s+)?(?:class|interface|object|enum\s+class)\s+([A-Za-z_]\w*)")
KOTLIN_FUNCTION_RE = re.compile(
    r"^\s*(?:override\s+|private\s+|public\s+|protected\s+|internal\s+|suspend\s+|inline\s+|operator\s+|tailrec\s+)*fun\s+(?:[A-Za-z_]\w*\.)?([A-Za-z_]\w*)\s*\("
)


def parse_kotlin(path: Path, rel_path: str, root_label: str, root: Path) -> list[Symbol]:
    lines = _read_text(path).splitlines()
    language = "kotlin" if path.suffix.lower() == ".kt" else "kotlin-script"
    out: list[Symbol] = []
    class_stack: list[tuple[str, int]] = []
    brace_depth = 0
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        while class_stack and brace_depth < class_stack[-1][1]:
            class_stack.pop()
        match = KOTLIN_TYPE_RE.match(line)
        if match:
            name = match.group(1)
            parent = class_stack[-1][0] if class_stack else ""
            qn = f"{parent}.{name}" if parent else name
            out.append(
                Symbol(root_label, path, language, _subsystem(path), "class", qn, name, parent, _visibility(name), idx, idx, False, "", _single_line(stripped)[:240], _entrypoint_hint(Path(rel_path), name, ""), "kotlin_regex")
            )
            class_stack.append((name, brace_depth + max(_brace_delta(line), 1)))
        else:
            match = KOTLIN_FUNCTION_RE.match(line)
            if match:
                name = match.group(1)
                parent = class_stack[-1][0] if class_stack else ""
                kind = "method" if parent else "function"
                out.append(
                    Symbol(
                        root_label,
                        path,
                        language,
                        _subsystem(path),
                        kind,
                        f"{parent}.{name}" if parent else name,
                        name,
                        parent,
                        _visibility(name),
                        idx,
                        idx,
                        "suspend " in line,
                        "",
                        _single_line(stripped)[:240],
                        _entrypoint_hint(Path(rel_path), name, ""),
                        "kotlin_regex",
                    )
                )
        brace_depth += _brace_delta(line)
    return out


SWIFT_TYPE_RE = re.compile(r"^\s*(?:final\s+|public\s+|private\s+|internal\s+|open\s+)?(?:class|struct|enum|actor|protocol)\s+([A-Za-z_]\w*)")
SWIFT_FUNCTION_RE = re.compile(
    r"^\s*(?:@\w+(?:\([^)]*\))?\s+)*(?:public\s+|private\s+|fileprivate\s+|internal\s+|open\s+|static\s+|class\s+|override\s+|mutating\s+|nonmutating\s+|final\s+)*func\s+([A-Za-z_]\w*)\s*\("
)
SWIFT_INIT_RE = re.compile(r"^\s*(?:public\s+|private\s+|fileprivate\s+|internal\s+|required\s+|convenience\s+|override\s+)*init\s*\(")


def parse_swift(path: Path, rel_path: str, root_label: str, root: Path) -> list[Symbol]:
    lines = _read_text(path).splitlines()
    out: list[Symbol] = []
    class_stack: list[tuple[str, int]] = []
    brace_depth = 0
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        while class_stack and brace_depth < class_stack[-1][1]:
            class_stack.pop()
        match = SWIFT_TYPE_RE.match(line)
        if match:
            name = match.group(1)
            parent = class_stack[-1][0] if class_stack else ""
            qn = f"{parent}.{name}" if parent else name
            out.append(
                Symbol(root_label, path, "swift", _subsystem(path), "class", qn, name, parent, _visibility(name), idx, idx, False, "", _single_line(stripped)[:240], _entrypoint_hint(Path(rel_path), name, ""), "swift_regex")
            )
            class_stack.append((name, brace_depth + max(_brace_delta(line), 1)))
        else:
            match = SWIFT_FUNCTION_RE.match(line)
            init_match = SWIFT_INIT_RE.match(line)
            if match or init_match:
                name = match.group(1) if match else "init"
                parent = class_stack[-1][0] if class_stack else ""
                kind = "method" if parent else "function"
                out.append(
                    Symbol(
                        root_label,
                        path,
                        "swift",
                        _subsystem(path),
                        kind,
                        f"{parent}.{name}" if parent else name,
                        name,
                        parent,
                        _visibility(name),
                        idx,
                        idx,
                        " async" in line,
                        "",
                        _single_line(stripped)[:240],
                        _entrypoint_hint(Path(rel_path), name, ""),
                        "swift_regex",
                    )
                )
        brace_depth += _brace_delta(line)
    return out


CPP_TYPE_RE = re.compile(r"^\s*(?:class|struct)\s+([A-Za-z_]\w*)")
CPP_FUNCTION_RE = re.compile(
    r"^\s*(?:template\s*<[^>]+>\s*)?(?:(?:[\w:<>,~*&]+\s+)+)([A-Za-z_]\w*(?:::[A-Za-z_~]\w*)?)\s*\([^;]*\)\s*(?:const\s*)?(?:override\s*)?(?:noexcept\s*)?(?:\{|:)"
)


def parse_cpp_like(path: Path, rel_path: str, root_label: str, root: Path) -> list[Symbol]:
    lines = _read_text(path).splitlines()
    language = {
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".h": "c-header",
        ".hpp": "cpp-header",
    }.get(path.suffix.lower(), "cpp")
    out: list[Symbol] = []
    class_stack: list[tuple[str, int]] = []
    brace_depth = 0
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        while class_stack and brace_depth < class_stack[-1][1]:
            class_stack.pop()
        match = CPP_TYPE_RE.match(line)
        if match:
            name = match.group(1)
            parent = class_stack[-1][0] if class_stack else ""
            qn = f"{parent}.{name}" if parent else name
            out.append(
                Symbol(root_label, path, language, _subsystem(path), "class", qn, name, parent, _visibility(name), idx, idx, False, "", _single_line(stripped)[:240], "", "cpp_regex")
            )
            class_stack.append((name, brace_depth + max(_brace_delta(line), 1)))
        else:
            match = CPP_FUNCTION_RE.match(line)
            if match and not stripped.startswith(("if ", "for ", "while ", "switch ", "catch ", "return ")):
                raw_name = match.group(1)
                parts = raw_name.split("::")
                name = parts[-1]
                parent = "::".join(parts[:-1]) or (class_stack[-1][0] if class_stack else "")
                kind = "method" if parent else "function"
                qn = ".".join([part for part in [parent.replace("::", "."), name] if part])
                out.append(
                    Symbol(
                        root_label,
                        path,
                        language,
                        _subsystem(path),
                        kind,
                        qn,
                        name,
                        parent.replace("::", "."),
                        _visibility(name),
                        idx,
                        idx,
                        False,
                        "",
                        _single_line(stripped)[:240],
                        _entrypoint_hint(Path(rel_path), name, ""),
                        "cpp_regex",
                    )
                )
        brace_depth += _brace_delta(line)
    return out


def collect_symbols(root: Path, root_label: str, included_dirs: set[str]) -> list[Symbol]:
    if not root.exists():
        return []
    symbols: list[Symbol] = []
    for top in sorted(included_dirs):
        base = root / top
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            if _skip_path(path, root, included_dirs):
                continue
            rel_path = _rel(path, root)
            suffix = path.suffix.lower()
            if suffix == ".py":
                symbols.extend(parse_python(path, rel_path, root_label, root))
            elif suffix in {".ts", ".tsx"}:
                symbols.extend(parse_typescript_like(path, rel_path, root_label, root))
            elif suffix == ".dart":
                symbols.extend(parse_dart(path, rel_path, root_label, root))
            elif suffix in {".kt", ".kts"}:
                symbols.extend(parse_kotlin(path, rel_path, root_label, root))
            elif suffix == ".swift":
                symbols.extend(parse_swift(path, rel_path, root_label, root))
            elif suffix in {".cpp", ".cc", ".cxx", ".h", ".hpp"}:
                symbols.extend(parse_cpp_like(path, rel_path, root_label, root))
    return symbols


def collect_test_texts(root: Path, client_root: Path | None) -> dict[str, str]:
    candidates: list[Path] = []
    test_roots = [
        root / "tests",
        root / "portal_bot" / "tests",
        root / "webapp" / "e2e",
    ]
    if client_root and client_root.exists():
        test_roots.extend(
            [
                client_root / "test",
                client_root / "tests",
                client_root / "packages",
                client_root / "apps",
            ]
        )
    for base in test_roots:
        if not base.exists():
            continue
        root_for_rel = root if root in base.parents or base == root else (client_root or base)
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in SOURCE_SUFFIXES:
                continue
            if path.name in NON_PRODUCT_COVERAGE_TEST_NAMES:
                continue
            rel = path.relative_to(root_for_rel)
            if any(part in EXCLUDED_PARTS - {"tests", "test", "e2e"} for part in rel.parts):
                continue
            if client_root and root_for_rel == client_root:
                rel_parts = set(rel.parts)
                if not (rel_parts & {"test", "tests"} or any(pattern in path.name for pattern in TEST_FILE_PATTERNS)):
                    continue
            candidates.append(path)
    out: dict[str, str] = {}
    for path in sorted(candidates):
        try:
            label = _rel(path, root) if path.is_relative_to(root) else f"POKROV-app/{_rel(path, client_root or path.parent)}"
        except AttributeError:
            label = path.as_posix()
        out[label] = _read_text(path)
    return out


def test_refs_for(symbol: Symbol, test_texts: dict[str, str]) -> list[str]:
    if symbol.symbol_kind == "class":
        pattern = re.compile(rf"\b{re.escape(symbol.name)}\b")
    else:
        pattern = re.compile(rf"\b{re.escape(symbol.name)}\b")
    refs = [label for label, text in test_texts.items() if pattern.search(text)]
    return refs[:30]


def build_test_token_index(test_texts: dict[str, str]) -> dict[str, list[str]]:
    token_index: dict[str, list[str]] = {}
    token_re = re.compile(r"\b[A-Za-z_]\w*\b")
    for label, text in test_texts.items():
        for token in set(token_re.findall(text)):
            token_index.setdefault(token, []).append(label)
    return {token: refs[:30] for token, refs in token_index.items()}


def _module_ref_patterns(symbol: Symbol, rel_path: str) -> list[str]:
    path_no_ext = re.sub(r"\.[^.]+$", "", rel_path)
    rel = Path(rel_path)
    generic_stems = {"error", "index", "layout", "main", "not-found", "page"}
    patterns = {rel_path, path_no_ext}
    if rel.stem not in generic_stems:
        patterns.update({rel.name, rel.stem})
    suffix = Path(rel_path).suffix.lower()
    if suffix == ".py":
        patterns.add(path_no_ext.replace("/", "."))
    elif suffix in {".ts", ".tsx"}:
        if "/src/" in path_no_ext:
            src_tail = path_no_ext.split("/src/", 1)[1]
            patterns.update({src_tail, f"@/{src_tail}"})
    elif suffix == ".dart":
        match = re.match(r"packages/([^/]+)/lib/(.+)$", path_no_ext)
        if match:
            package_name, package_path = match.groups()
            patterns.add(f"package:{package_name}/{package_path}.dart")
    if symbol.parent:
        patterns.add(symbol.parent)
    elif symbol.symbol_kind == "class":
        patterns.add(symbol.name)
    return [pattern for pattern in sorted(patterns, key=len, reverse=True) if len(pattern) >= 5]


def _module_refs_for_symbol(symbol: Symbol, rel_path: str, test_texts: dict[str, str]) -> list[str]:
    patterns = _module_ref_patterns(symbol, rel_path)
    if not patterns:
        return []
    refs: list[str] = []
    for label, text in test_texts.items():
        for pattern in patterns:
            if pattern in text:
                refs.append(label)
                break
    return _dedupe_strings(refs)[:30]


def _symbol_rel_path(symbol: Symbol, root: Path, client_root: Path | None) -> str:
    base = root if symbol.root_label == "root" else (client_root or root)
    return _rel(symbol.path, base)


SOURCE_REF_RE = re.compile(r"([A-Za-z0-9_./\\() -]+\.(?:py|tsx|ts|dart|kt|ps1|md))(?::(\d+))?")


def _source_refs_from_text(text: str) -> list[tuple[str, int | None]]:
    refs: list[tuple[str, int | None]] = []
    current_path: str | None = None
    for raw_part in re.split(r"[,;\s]+", text or ""):
        part = raw_part.strip().strip('"').strip("'")
        if not part:
            continue
        match = SOURCE_REF_RE.fullmatch(part)
        if match:
            current_path = _normalize_source_ref(match.group(1))
            line = int(match.group(2)) if match.group(2) else None
            refs.append((current_path, line))
            continue
        if current_path and part.isdigit():
            refs.append((current_path, int(part)))
    return _dedupe_source_refs(refs)


def _normalize_source_ref(ref: str) -> str:
    normalized = ref.replace("\\", "/")
    if normalized.startswith("POKROV-app/"):
        return normalized[len("POKROV-app/") :]
    return normalized


def _dedupe_source_refs(refs: list[tuple[str, int | None]]) -> list[tuple[str, int | None]]:
    seen: set[tuple[str, int | None]] = set()
    out: list[tuple[str, int | None]] = []
    for ref in refs:
        if ref not in seen:
            seen.add(ref)
            out.append(ref)
    return out


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _story_refs_by_path(tracker_path: Path) -> dict[str, list[str]]:
    refs: dict[str, list[str]] = {}
    for row in _read_csv_rows(tracker_path):
        canonical_id = row.get("canonical_id", "")
        for ref, _line in _source_refs_from_text(row.get("code_evidence", "")):
            refs.setdefault(ref, [])
            if canonical_id and canonical_id not in refs[ref]:
                refs[ref].append(canonical_id)
    return refs


TS_FROM_IMPORT_RE = re.compile(r"^\s*(?:import|export)\s+[\s\S]*?\s+from\s+['\"]([^'\"]+)['\"]", re.MULTILINE)
TS_SIDE_EFFECT_IMPORT_RE = re.compile(r"^\s*import\s+['\"]([^'\"]+)['\"]", re.MULTILINE)


def _normalize_rel_path(value: str) -> str:
    normalized = posixpath.normpath(value.replace("\\", "/"))
    return "" if normalized == "." else normalized


def _resolve_ts_import(current_rel: str, specifier: str, available_paths: set[str]) -> str:
    spec = specifier.strip()
    if spec.startswith("@/"):
        if current_rel.startswith("marketing/src/"):
            base = f"marketing/src/{spec[2:]}"
        else:
            base = f"webapp/src/{spec[2:]}"
    elif spec.startswith("."):
        base = _normalize_rel_path(f"{Path(current_rel).parent.as_posix()}/{spec}")
    else:
        return ""
    base = _normalize_rel_path(re.sub(r"/+", "/", base))
    candidates = [base]
    if not Path(base).suffix:
        candidates.extend(
            [
                f"{base}.ts",
                f"{base}.tsx",
                f"{base}/index.ts",
                f"{base}/index.tsx",
            ]
        )
    for candidate in candidates:
        normalized = _normalize_rel_path(candidate)
        if normalized in available_paths:
            return normalized
    return ""


def _ts_import_specifiers(text: str) -> list[str]:
    return _dedupe_strings(
        [
            *TS_FROM_IMPORT_RE.findall(text),
            *TS_SIDE_EFFECT_IMPORT_RE.findall(text),
        ]
    )


def _resolve_python_import(current_rel: str, module_name: str | None, level: int, available_paths: set[str]) -> str:
    if not module_name and level <= 0:
        return ""
    if level > 0:
        base = Path(current_rel).parent
        for _ in range(level - 1):
            base = base.parent
        module_base = _normalize_rel_path((base / (module_name or "").replace(".", "/")).as_posix())
    else:
        module_base = _normalize_rel_path((module_name or "").replace(".", "/"))
    candidates = [
        f"{module_base}.py",
        f"{module_base}/__init__.py",
    ]
    if level == 0 and "/" not in module_base:
        local_base = _normalize_rel_path((Path(current_rel).parent / module_base).as_posix())
        candidates.extend(
            [
                f"{local_base}.py",
                f"{local_base}/__init__.py",
            ]
        )
    for candidate in candidates:
        normalized = _normalize_rel_path(candidate)
        if normalized in available_paths:
            return normalized
    return ""


def _dependency_paths_for_source(rel_path: str, path: Path, available_paths: set[str]) -> list[str]:
    suffix = Path(rel_path).suffix.lower()
    if suffix in {".ts", ".tsx"}:
        text = _read_text(path)
        return _dedupe_strings(
            [
                resolved
                for specifier in _ts_import_specifiers(text)
                if (resolved := _resolve_ts_import(rel_path, specifier, available_paths))
            ]
        )
    if suffix == ".py":
        try:
            tree = ast.parse(_read_text(path))
        except SyntaxError:
            return []
        deps: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    resolved = _resolve_python_import(rel_path, alias.name, 0, available_paths)
                    if resolved:
                        deps.append(resolved)
            elif isinstance(node, ast.ImportFrom):
                resolved = _resolve_python_import(rel_path, node.module, node.level, available_paths)
                if resolved:
                    deps.append(resolved)
        return _dedupe_strings(deps)
    return []


def _source_path_map(root: Path, included_dirs: set[str]) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    if not root.exists():
        return paths
    for path in root.rglob("*"):
        if not path.is_file() or _skip_path(path, root, included_dirs):
            continue
        paths.setdefault(_rel(path, root), path)
    return paths


def _story_dependency_refs_by_path(
    symbols: list[Symbol],
    root: Path,
    client_root: Path | None,
    story_by_path: dict[str, list[str]],
) -> dict[str, list[str]]:
    path_by_rel = _source_path_map(root, ROOT_INCLUDED_DIRS)
    if client_root and client_root.exists():
        path_by_rel.update(_source_path_map(client_root, CLIENT_INCLUDED_DIRS))
    for symbol in symbols:
        rel_path = _symbol_rel_path(symbol, root, client_root)
        path_by_rel.setdefault(rel_path, symbol.path)
    available_paths = set(path_by_rel)
    deps_by_path: dict[str, list[str]] = {}
    for rel_path, path in path_by_rel.items():
        deps = _dependency_paths_for_source(rel_path, path, available_paths)
        if deps:
            deps_by_path[rel_path] = deps

    dependency_refs: dict[str, list[str]] = {}
    for source_path, story_refs in story_by_path.items():
        queue = list(deps_by_path.get(source_path, []))
        seen = {source_path}
        while queue:
            dep_path = queue.pop(0)
            if dep_path in seen:
                continue
            seen.add(dep_path)
            dependency_refs.setdefault(dep_path, [])
            for story_ref in story_refs:
                if story_ref not in dependency_refs[dep_path]:
                    dependency_refs[dep_path].append(story_ref)
            queue.extend(deps_by_path.get(dep_path, []))
    return dependency_refs


def _entrypoint_refs_for_symbol(
    symbol: Symbol,
    rel_path: str,
    entrypoint_rows: list[dict[str, str]],
) -> list[str]:
    refs: list[str] = []
    for row in entrypoint_rows:
        entry_id = row.get("entry_id", "")
        if not entry_id:
            continue
        trigger_path = _normalize_source_ref(row.get("trigger_or_path", ""))
        if trigger_path == rel_path:
            refs.append(entry_id)
            continue
        handler = row.get("handler_or_component", "")
        source_refs = _source_refs_from_text(row.get("code_evidence", ""))
        for ref_path, ref_line in source_refs:
            if ref_path != rel_path:
                continue
            if handler == symbol.name:
                refs.append(entry_id)
                break
            if handler == "main()/CLI" and symbol.name == "main":
                refs.append(entry_id)
                break
            if ref_line is None:
                refs.append(entry_id)
                break
            if symbol.line <= ref_line <= symbol.end_line or abs(symbol.line - ref_line) <= 3:
                refs.append(entry_id)
                break
    return _dedupe_strings(refs)


def _route_path_from_decorators(decorators: str) -> str:
    match = re.search(r"\.(?:api_route|delete|get|head|options|patch|post|put|websocket)\(['\"]([^'\"]+)['\"]", decorators)
    return match.group(1) if match else ""


def _route_refs_for_symbol(symbol: Symbol, test_texts: dict[str, str]) -> list[str]:
    if symbol.entrypoint_hint != "fastapi_route_handler":
        return []
    route_path = _route_path_from_decorators(symbol.decorators_or_modifiers)
    if not route_path:
        return []
    pattern_text = re.escape(route_path)
    pattern_text = re.sub(r"\\\{[^}]+\\\}", r"[^'\"\\s/?#]+", pattern_text)
    pattern = re.compile(pattern_text)
    return [label for label, text in test_texts.items() if pattern.search(text)][:30]


def _load_script_manifest(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8", errors="replace")
    data = json.loads(raw)
    statuses: dict[str, str] = {}
    for status in ("active", "deprecated", "archive_only", "denylist"):
        for script_path in data.get(status, []):
            statuses[str(script_path)] = status
    return statuses


USER_ENTRYPOINT_HINTS = {
    "android_activity",
    "apple_app_delegate",
    "fastapi_route_handler",
    "next_page_component",
    "script_cli_main",
    "telegram_handler",
    "windows_entrypoint",
}

CLIENT_PLATFORM_HOST_PREFIXES = (
    "apps/android_shell/android/",
    "apps/ios_shell/ios/",
    "apps/macos_shell/macos/",
    "apps/windows_shell/windows/",
)

NEXT_ROUTE_BOUNDARY_FILENAMES = {
    "error.tsx",
    "global-error.tsx",
    "layout.tsx",
    "loading.tsx",
    "not-found.tsx",
}

OPERATOR_TOOLING_PATHS = {
    "portal_bot/check_service.py",
    "portal_bot/get_logs.py",
    "portal_bot/sync_clients.py",
    "scripts/generate_private_helper_coverage.py",
}


def _is_client_platform_host_source(symbol: Symbol, rel_path: str) -> bool:
    return symbol.root_label == "POKROV-app" and rel_path.startswith(CLIENT_PLATFORM_HOST_PREFIXES)


def _is_next_route_boundary(rel_path: str) -> bool:
    return rel_path.startswith("webapp/src/app/") and Path(rel_path).name in NEXT_ROUTE_BOUNDARY_FILENAMES


def _is_webapp_qa_tooling(rel_path: str) -> bool:
    return rel_path in {
        "webapp/src/app/qa-overlay.tsx",
        "webapp/src/app/qa-overlay-host.tsx",
    }


def _is_telegram_webapp_bootstrap(rel_path: str) -> bool:
    return rel_path == "webapp/src/app/telegram-webapp-init.tsx"


def _is_operator_tooling_source(rel_path: str) -> bool:
    return rel_path.startswith("webapp/scripts/") or rel_path in OPERATOR_TOOLING_PATHS


def _is_client_desktop_tray_source(symbol: Symbol, rel_path: str) -> bool:
    return symbol.root_label == "POKROV-app" and rel_path == "apps/windows_shell/lib/main.dart"


def _is_client_package_public_api(symbol: Symbol, rel_path: str) -> bool:
    return symbol.root_label == "POKROV-app" and rel_path.startswith("packages/") and "/lib/" in rel_path


def _classify_symbol_coverage(
    symbol: Symbol,
    rel_path: str,
    story_refs: list[str],
    story_dependency_refs: list[str],
    entrypoint_refs: list[str],
    test_refs: list[str],
    route_refs: list[str],
    module_refs: list[str],
    script_manifest_status: str,
) -> tuple[str, list[str], str, str]:
    if symbol.parser_note.endswith("parse_error"):
        return (
            "parser_error",
            [],
            "Source parser reported an error for this symbol.",
            "Fix parser coverage or exclude generated/non-source content.",
        )
    if symbol.entrypoint_hint in USER_ENTRYPOINT_HINTS:
        if entrypoint_refs:
            return (
                "entrypoint_mapped",
                entrypoint_refs,
                "Externally reachable entrypoint maps to route/story/script coverage.",
                "Keep entrypoint coverage current when behavior changes.",
            )
        if symbol.entrypoint_hint == "script_cli_main":
            if script_manifest_status == "deprecated":
                return (
                    "script_cli_deprecated",
                    [],
                    "Script CLI is explicitly listed as deprecated in scripts/manifest.yaml.",
                    "Keep out of active workflow coverage unless the owner reopens this lane.",
                )
            if script_manifest_status == "archive_only":
                return (
                    "script_cli_archive_only",
                    [],
                    "Script CLI is explicitly listed as archive-only retained evidence.",
                    "Do not use for active operator workflows without a new manifest decision.",
                )
            if script_manifest_status == "denylist":
                return (
                    "script_cli_denylisted",
                    [],
                    "Script CLI is explicitly denylisted in scripts/manifest.yaml.",
                    "Remove active references and keep denylist coverage current.",
                )
            if script_manifest_status == "active":
                return (
                    "script_cli_active_without_workflow_mapping",
                    [],
                    "Script is active in scripts/manifest.yaml but has no script workflow coverage row.",
                    "Add script workflow coverage, canonical story row, and direct tests.",
                )
            return (
                "script_cli_manifest_review",
                [],
                "Script has a CLI main but no active script workflow coverage mapping.",
                "Add the script to active/deprecated/archive manifest status and map tests if active.",
            )
        if route_refs:
            return (
                "entrypoint_route_test_ref",
                route_refs,
                "FastAPI route path is referenced directly by automated tests.",
                "Promote to route/story coverage if this endpoint is user/provider-facing.",
            )
        if story_refs:
            return (
                "entrypoint_story_source_ref",
                story_refs[:30],
                "Entrypoint source file is referenced by canonical story evidence.",
                "Add route/handler-level mapping if this entrypoint is externally reachable.",
            )
        if test_refs:
            return (
                "entrypoint_token_test_ref",
                test_refs,
                "Entrypoint symbol name appears in automated test files.",
                "Prefer route/handler scenario coverage if behavior is user-visible.",
            )
        return (
            "entrypoint_needs_mapping_review",
            [],
            "Entrypoint hint exists but no entrypoint coverage row matched this symbol.",
            "Map this entrypoint to story/route/script evidence or update the matcher.",
        )
    if story_refs:
        return (
            "story_source_file",
            story_refs[:30],
            "Symbol lives in a source file referenced by canonical story code evidence.",
            "Prefer story-level behavior tests; add helper tests only for risky logic.",
        )
    if story_dependency_refs:
        return (
            "story_dependency_source_file",
            story_dependency_refs[:30],
            "Symbol lives in a local source dependency of a file referenced by canonical story evidence.",
            "Keep dependency mapping current when import structure changes; add direct tests for risky helpers.",
        )
    if test_refs:
        return (
            "direct_token_test_ref",
            test_refs,
            "Symbol name appears in automated test files.",
            "Keep token refs current; promote to story mapping if user-visible.",
        )
    if module_refs and symbol.visibility == "public":
        return (
            "module_test_ref",
            module_refs,
            "Source module, import path, or parent type is referenced by automated tests.",
            "Add direct symbol assertions if this public helper owns user-visible or high-risk behavior.",
        )
    if symbol.visibility == "public" and _is_client_platform_host_source(symbol, rel_path):
        return (
            "client_platform_host_manual_gate",
            [],
            "Public native client host symbol is inventoried separately from ordinary backend/web helpers.",
            "Verify through platform unit tests, simulator/device runs, or explicit manual owner evidence before stronger runtime claims.",
        )
    if symbol.visibility == "public" and _is_client_desktop_tray_source(symbol, rel_path):
        return (
            "client_desktop_tray_manual_gate",
            [],
            "Public Windows shell tray callback is inventoried as desktop host behavior.",
            "Verify through Windows shell tests, desktop smoke, or explicit manual owner evidence.",
        )
    if symbol.visibility == "public" and _is_next_route_boundary(rel_path):
        return (
            "next_route_boundary_inventory",
            [],
            "Next.js route boundary component is invoked by framework convention, not as an ordinary public helper.",
            "Cover through route/e2e behavior and update story evidence when route boundary UX changes.",
        )
    if symbol.visibility == "public" and _is_webapp_qa_tooling(rel_path):
        return (
            "qa_tooling_inventory",
            [],
            "QA overlay component is gated operator tooling, not a user-facing product story.",
            "Keep disabled by default; add direct tests if QA tooling becomes part of release acceptance.",
        )
    if symbol.visibility == "public" and _is_telegram_webapp_bootstrap(rel_path):
        return (
            "telegram_webapp_bootstrap_inventory",
            [],
            "Telegram WebApp bootstrap component is app-wide integration glue imported by the root layout.",
            "Cover with browser/Telegram WebApp integration smoke before stronger runtime claims.",
        )
    if symbol.visibility == "public" and _is_operator_tooling_source(rel_path):
        return (
            "operator_tooling_inventory",
            [],
            "Operator-only helper/tooling symbol is inventoried separately from user-facing product behavior.",
            "Add focused tests before using as active release, deploy, or incident-response workflow.",
        )
    if symbol.visibility == "public" and _is_client_package_public_api(symbol, rel_path):
        return (
            "client_package_public_api_review",
            [],
            "Public client package API has no direct story/test signal in the root audit.",
            "Add package-level Flutter tests or story mapping before claiming runtime behavior coverage.",
        )
    if symbol.entrypoint_hint == "framework_override":
        return (
            "framework_override_inventory",
            [],
            "Framework lifecycle/render override inventoried as implementation detail.",
            "Cover through surrounding widget/page behavior unless the override has risky logic.",
        )
    if symbol.visibility == "private":
        return (
            "private_inventory_only",
            [],
            "Private helper is inventoried but not promoted to a user-story contract.",
            "Add focused tests if this helper owns non-trivial business logic.",
        )
    return (
        "public_symbol_review",
        [],
        "Public symbol has no direct story, entrypoint, or test-token signal.",
        "Review whether this is public API, dead code, or low-risk implementation detail.",
    )


def _symbol_expected_behavior_from_code(
    symbol: Symbol,
    rel_path: str,
    coverage_tier: str,
    coverage_refs: list[str],
) -> str:
    symbol_label = f"{symbol.symbol_kind} `{symbol.qualified_name}`"
    ref_summary = ""
    if coverage_refs:
        sample = "; ".join(coverage_refs[:3])
        suffix = "" if len(coverage_refs) <= 3 else f"; plus {len(coverage_refs) - 3} more refs"
        ref_summary = f" Referenced coverage: {sample}{suffix}."

    if coverage_tier == "entrypoint_mapped":
        return (
            f"{symbol_label} must preserve the externally reachable route, handler, or CLI behavior "
            f"mapped for `{rel_path}`.{ref_summary}"
        )
    if coverage_tier == "entrypoint_route_test_ref":
        return (
            f"{symbol_label} must preserve the route behavior currently exercised by direct route-path tests; "
            "promote it to route/story coverage if the endpoint becomes a broader product contract."
            f"{ref_summary}"
        )
    if coverage_tier == "entrypoint_story_source_ref":
        return (
            f"{symbol_label} must preserve the story-referenced entrypoint behavior in `{rel_path}`; "
            "add narrower route or handler mapping when behavior changes."
            f"{ref_summary}"
        )
    if coverage_tier == "entrypoint_token_test_ref":
        return (
            f"{symbol_label} must preserve the entrypoint behavior indicated by direct test-token references; "
            "prefer scenario coverage for user-visible behavior."
            f"{ref_summary}"
        )
    if coverage_tier == "story_source_file":
        return (
            f"{symbol_label} must preserve the canonical user-story behavior implemented by `{rel_path}`."
            f"{ref_summary}"
        )
    if coverage_tier == "story_dependency_source_file":
        return (
            f"{symbol_label} must keep supporting the story-mapped source path `{rel_path}` without changing "
            "the referenced user-visible behavior."
            f"{ref_summary}"
        )
    if coverage_tier == "direct_token_test_ref":
        return (
            f"{symbol_label} must preserve the behavior implied by automated tests that reference its symbol name."
            f"{ref_summary}"
        )
    if coverage_tier == "module_test_ref":
        return (
            f"{symbol_label} must preserve the public module or parent-type behavior covered by automated tests; "
            "add direct assertions if it owns user-visible or high-risk logic."
            f"{ref_summary}"
        )
    if coverage_tier == "client_platform_host_manual_gate":
        return (
            f"{symbol_label} must preserve native client host integration behavior in `{rel_path}`; runtime claims "
            "require platform tests, simulator/device proof, or owner evidence."
        )
    if coverage_tier == "client_desktop_tray_manual_gate":
        return (
            f"{symbol_label} must preserve Windows desktop tray behavior in `{rel_path}`; runtime claims require "
            "Windows shell tests, desktop smoke, or owner evidence."
        )
    if coverage_tier == "next_route_boundary_inventory":
        return (
            f"{symbol_label} must preserve the framework-invoked Next.js route-boundary behavior for `{rel_path}` "
            "through surrounding route/e2e coverage."
        )
    if coverage_tier == "qa_tooling_inventory":
        return (
            f"{symbol_label} must remain gated QA/operator tooling and must not become user-visible release behavior "
            "without explicit tests and story updates."
        )
    if coverage_tier == "operator_tooling_inventory":
        return (
            f"{symbol_label} must preserve operator-tooling behavior in `{rel_path}` and needs focused tests before "
            "use in active release, deploy, or incident-response workflows."
        )
    if coverage_tier == "telegram_webapp_bootstrap_inventory":
        return (
            f"{symbol_label} must preserve Telegram WebApp bootstrap behavior imported by the root layout; stronger "
            "runtime claims require browser or Telegram WebApp smoke evidence."
        )
    if coverage_tier == "client_package_public_api_review":
        return (
            f"{symbol_label} must not be treated as covered runtime API until package-level Flutter tests or story "
            "mapping prove the public contract."
        )
    if coverage_tier == "script_cli_deprecated":
        return (
            f"{symbol_label} must remain out of active operator workflows while `{rel_path}` is deprecated in the "
            "script manifest."
        )
    if coverage_tier in {"script_cli_archive_only", "script_cli_denylisted"}:
        return (
            f"{symbol_label} must remain outside active workflow claims while `{rel_path}` has manifest status "
            f"`{coverage_tier.replace('script_cli_', '')}`."
        )
    if coverage_tier == "script_cli_active_without_workflow_mapping":
        return (
            f"{symbol_label} is active script code but lacks workflow mapping; expected behavior must be promoted "
            "into script workflow coverage before completion claims."
        )
    if coverage_tier == "script_cli_manifest_review":
        return (
            f"{symbol_label} has a CLI main without manifest classification; expected behavior is not complete "
            "until the script is classified and active paths get workflow tests."
        )
    if coverage_tier == "framework_override_inventory":
        return (
            f"{symbol_label} must preserve framework lifecycle or render behavior through the surrounding widget, "
            "page, or platform scenario."
        )
    if coverage_tier == "private_inventory_only":
        return (
            f"{symbol_label} is private implementation detail in `{rel_path}`; expected behavior stays coupled to "
            "its caller stories unless Q-001 requires dedicated helper tests."
        )
    if coverage_tier == "parser_error":
        return (
            f"{symbol_label} cannot have reliable expected behavior until source parsing for `{rel_path}` is fixed."
        )
    return (
        f"{symbol_label} has no accepted story, entrypoint, or test coverage tier yet; review public API status, "
        "dead-code status, or add evidence before completion claims."
    )


def _manual_gate_refs_for_symbol(symbol: Symbol, rel_path: str, coverage_tier: str) -> list[str]:
    if coverage_tier == "client_desktop_tray_manual_gate":
        return ["OWNER-GATE-WINDOWS-INSTALL-CONNECT"]
    if coverage_tier != "client_platform_host_manual_gate":
        return []
    normalized = rel_path.replace("\\", "/")
    if normalized.startswith("apps/android_shell/"):
        return ["OWNER-GATE-ANDROID-PHYSICAL-INSTALL-CONNECT"]
    if normalized.startswith("apps/windows_shell/"):
        return ["OWNER-GATE-WINDOWS-INSTALL-CONNECT"]
    if normalized.startswith("apps/ios_shell/") or normalized.startswith("apps/macos_shell/"):
        return ["NOT_CURRENT_PUBLIC_BETA_TARGET"]
    return ["OWNER-GATE-LIVE-DEPLOY-APP-SESSION"]


def write_symbol_coverage_audit(
    symbols: list[Symbol],
    out_path: Path,
    root: Path,
    client_root: Path | None,
    tracker_path: Path,
    entrypoint_coverage_path: Path,
    script_manifest_path: Path = DEFAULT_SCRIPT_MANIFEST,
) -> None:
    test_texts = collect_test_texts(root, client_root)
    token_index = build_test_token_index(test_texts)
    story_by_path = _story_refs_by_path(tracker_path)
    story_dependency_by_path = _story_dependency_refs_by_path(symbols, root, client_root, story_by_path)
    entrypoint_rows = _read_csv_rows(entrypoint_coverage_path)
    script_manifest_statuses = _load_script_manifest(script_manifest_path)
    fields = [
        "symbol_id",
        "root",
        "path",
        "line",
        "end_line",
        "language",
        "subsystem",
        "symbol_kind",
        "qualified_name",
        "name",
        "visibility",
        "entrypoint_hint",
        "coverage_tier",
        "coverage_ref_count",
        "coverage_refs",
        "test_ref_count",
        "test_refs",
        "expected_behavior_from_code",
        "manual_gate_refs",
        "evidence_basis",
        "next_action",
        "updated_at",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for index, symbol in enumerate(symbols, start=1):
            rel_path = _symbol_rel_path(symbol, root, client_root)
            test_refs = token_index.get(symbol.name, [])
            story_refs = story_by_path.get(rel_path, [])
            story_dependency_refs = story_dependency_by_path.get(rel_path, [])
            entrypoint_refs = _entrypoint_refs_for_symbol(symbol, rel_path, entrypoint_rows)
            route_refs = _route_refs_for_symbol(symbol, test_texts)
            module_refs = _module_refs_for_symbol(symbol, rel_path, test_texts)
            script_manifest_status = script_manifest_statuses.get(rel_path, "")
            tier, coverage_refs, basis, next_action = _classify_symbol_coverage(
                symbol,
                rel_path,
                story_refs,
                story_dependency_refs,
                entrypoint_refs,
                test_refs,
                route_refs,
                module_refs,
                script_manifest_status,
            )
            manual_gate_refs = _manual_gate_refs_for_symbol(symbol, rel_path, tier)
            writer.writerow(
                {
                    "symbol_id": f"CODE-SYMBOL-{index:05d}",
                    "root": _single_line(symbol.root_label),
                    "path": _single_line(rel_path),
                    "line": symbol.line,
                    "end_line": symbol.end_line,
                    "language": _single_line(symbol.language),
                    "subsystem": _single_line(symbol.subsystem),
                    "symbol_kind": _single_line(symbol.symbol_kind),
                    "qualified_name": _single_line(symbol.qualified_name),
                    "name": _single_line(symbol.name),
                    "visibility": _single_line(symbol.visibility),
                    "entrypoint_hint": _single_line(symbol.entrypoint_hint),
                    "coverage_tier": tier,
                    "coverage_ref_count": len(coverage_refs),
                    "coverage_refs": _single_line("; ".join(coverage_refs)),
                    "test_ref_count": len(test_refs),
                    "test_refs": _single_line("; ".join(test_refs)),
                    "expected_behavior_from_code": _single_line(
                        _symbol_expected_behavior_from_code(symbol, rel_path, tier, coverage_refs)
                    ),
                    "manual_gate_refs": _single_line("; ".join(manual_gate_refs)),
                    "evidence_basis": basis,
                    "next_action": next_action,
                    "updated_at": TODAY,
                }
            )


def write_csv(symbols: list[Symbol], out_path: Path, root: Path, client_root: Path | None) -> None:
    test_texts = collect_test_texts(root, client_root)
    token_index = build_test_token_index(test_texts)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "symbol_id",
        "root",
        "path",
        "language",
        "subsystem",
        "symbol_kind",
        "qualified_name",
        "name",
        "parent",
        "visibility",
        "line",
        "end_line",
        "is_async",
        "decorators_or_modifiers",
        "doc_or_signature",
        "entrypoint_hint",
        "parser_note",
        "test_ref_count",
        "test_refs",
        "inventory_status",
        "updated_at",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for index, symbol in enumerate(symbols, start=1):
            base = root if symbol.root_label == "root" else (client_root or root)
            refs = token_index.get(symbol.name, [])
            writer.writerow(
                {
                    "symbol_id": f"CODE-SYMBOL-{index:05d}",
                    "root": _single_line(symbol.root_label),
                    "path": _single_line(_rel(symbol.path, base)),
                    "language": _single_line(symbol.language),
                    "subsystem": _single_line(symbol.subsystem),
                    "symbol_kind": _single_line(symbol.symbol_kind),
                    "qualified_name": _single_line(symbol.qualified_name),
                    "name": _single_line(symbol.name),
                    "parent": _single_line(symbol.parent),
                    "visibility": _single_line(symbol.visibility),
                    "line": symbol.line,
                    "end_line": symbol.end_line,
                    "is_async": str(symbol.is_async).lower(),
                    "decorators_or_modifiers": _single_line(symbol.decorators_or_modifiers),
                    "doc_or_signature": _single_line(symbol.doc_or_signature),
                    "entrypoint_hint": _single_line(symbol.entrypoint_hint),
                    "parser_note": _single_line(symbol.parser_note),
                    "test_ref_count": len(refs),
                    "test_refs": _single_line("; ".join(refs)),
                    "inventory_status": "inventory_only",
                    "updated_at": TODAY,
                }
            )


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate low-level POKROV code symbol/function inventory.")
    ap.add_argument("--repo-root", default=str(REPO_ROOT))
    ap.add_argument("--client-root", default=str(DEFAULT_CLIENT_ROOT))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--symbol-coverage-out", default=str(DEFAULT_SYMBOL_COVERAGE_OUT))
    ap.add_argument("--tracker", default=str(DEFAULT_TRACKER))
    ap.add_argument("--entrypoint-coverage", default=str(DEFAULT_ENTRYPOINT_COVERAGE))
    ap.add_argument("--script-manifest", default=str(DEFAULT_SCRIPT_MANIFEST))
    ap.add_argument("--skip-symbol-coverage", action="store_true")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    client_root = Path(args.client_root).resolve() if args.client_root else None
    out_path = Path(args.out).resolve()

    symbols = collect_symbols(repo_root, "root", ROOT_INCLUDED_DIRS)
    if client_root and client_root.exists():
        symbols.extend(collect_symbols(client_root, "POKROV-app", CLIENT_INCLUDED_DIRS))
    symbols.sort(key=lambda item: (item.root_label, item.path.as_posix(), item.line, item.qualified_name))
    write_csv(symbols, out_path, repo_root, client_root)
    print(f"wrote {len(symbols)} symbols to {out_path}")
    if not args.skip_symbol_coverage:
        symbol_coverage_out = Path(args.symbol_coverage_out).resolve()
        write_symbol_coverage_audit(
            symbols,
            symbol_coverage_out,
            repo_root,
            client_root,
            Path(args.tracker).resolve(),
            Path(args.entrypoint_coverage).resolve(),
            Path(args.script_manifest).resolve(),
        )
        print(f"wrote {len(symbols)} symbol coverage rows to {symbol_coverage_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
