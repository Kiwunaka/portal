import ast
from pathlib import Path


SOURCE_ROOTS = ("portal_bot", "scripts")


def _python_sources() -> list[Path]:
    root = Path(__file__).resolve().parents[1]
    out: list[Path] = []
    for rel in SOURCE_ROOTS:
        for path in (root / rel).rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            out.append(path)
    return out


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return ""


def _is_verified_repo_loader_exec(
    *,
    relative_path: str,
    node: ast.Call,
    parents: dict[ast.AST, ast.AST],
) -> bool:
    if relative_path != "scripts/release_1_2_candidate_rollback_rehearsal.py":
        return False
    if len(node.args) != 2 or node.keywords:
        return False
    code_arg, namespace_arg = node.args
    if not isinstance(code_arg, ast.Name) or code_arg.id != "code":
        return False
    if not (
        isinstance(namespace_arg, ast.Attribute)
        and namespace_arg.attr == "__dict__"
        and isinstance(namespace_arg.value, ast.Name)
        and namespace_arg.value.id == "module"
    ):
        return False

    scopes: list[str] = []
    current: ast.AST = node
    while current in parents:
        current = parents[current]
        if isinstance(current, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            scopes.append(current.name)
    return tuple(reversed(scopes)) == (
        "_VerifiedRepoSourceLoader",
        "exec_module",
    )


def _synthetic_call(source: str) -> tuple[ast.Call, dict[ast.AST, ast.AST]]:
    tree = ast.parse(source)
    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    call = next(node for node in ast.walk(tree) if isinstance(node, ast.Call))
    return call, parents


def test_verified_repo_loader_exec_exception_is_exact() -> None:
    call, parents = _synthetic_call(
        "class _VerifiedRepoSourceLoader:\n"
        "    def exec_module(self, module):\n"
        "        exec(code, module.__dict__)\n"
    )
    assert _is_verified_repo_loader_exec(
        relative_path="scripts/release_1_2_candidate_rollback_rehearsal.py",
        node=call,
        parents=parents,
    )


def test_verified_repo_loader_exec_exception_rejects_near_misses() -> None:
    wrong_scope, wrong_scope_parents = _synthetic_call(
        "def exec_module(module):\n"
        "    exec(code, module.__dict__)\n"
    )
    assert not _is_verified_repo_loader_exec(
        relative_path="scripts/release_1_2_candidate_rollback_rehearsal.py",
        node=wrong_scope,
        parents=wrong_scope_parents,
    )

    wrong_args, wrong_args_parents = _synthetic_call(
        "class _VerifiedRepoSourceLoader:\n"
        "    def exec_module(self, module):\n"
        "        exec(unverified, module.__dict__)\n"
    )
    assert not _is_verified_repo_loader_exec(
        relative_path="scripts/release_1_2_candidate_rollback_rehearsal.py",
        node=wrong_args,
        parents=wrong_args_parents,
    )


def test_runtime_python_sources_do_not_use_obvious_rce_primitives() -> None:
    root = Path(__file__).resolve().parents[1]
    findings: list[str] = []
    for path in _python_sources():
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        relative_path = path.relative_to(root).as_posix()
        parents = {
            child: parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = _call_name(node.func)
            if name in {"eval", "exec"}:
                if not (
                    name == "exec"
                    and _is_verified_repo_loader_exec(
                        relative_path=relative_path,
                        node=node,
                        parents=parents,
                    )
                ):
                    findings.append(f"{path}:{node.lineno}: forbidden {name}()")
            if name in {"pickle.load", "pickle.loads"}:
                findings.append(f"{path}:{node.lineno}: forbidden {name}()")
            if name == "yaml.load":
                findings.append(f"{path}:{node.lineno}: forbidden yaml.load()")
            if name.startswith("subprocess."):
                for kw in node.keywords:
                    if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        findings.append(f"{path}:{node.lineno}: forbidden subprocess shell=True")
    assert not findings, "\n".join(findings)


def test_ssh_clients_do_not_trust_unknown_host_keys_silently() -> None:
    forbidden = "Auto" + "AddPolicy"
    findings: list[str] = []
    for path in _python_sources():
        source = path.read_text(encoding="utf-8-sig")
        if forbidden in source:
            findings.append(f"{path}: forbidden silent Paramiko host-key trust")
    assert not findings, "\n".join(findings)


def test_ssh_host_key_helpers_default_to_reject_policy() -> None:
    root = Path(__file__).resolve().parents[1]
    for rel in ("scripts/ssh_host_keys.py", "portal_bot/ssh_host_keys.py"):
        source = (root / rel).read_text(encoding="utf-8")
        assert "RejectPolicy()" in source
        assert "POKROV_SSH_TRUST_ON_FIRST_USE" in source
        assert "POKROV_SSH_KNOWN_HOSTS" in source


def test_mini_canary_installer_redacts_bearer_links_by_default() -> None:
    root = Path(__file__).resolve().parents[1]
    source = (root / "scripts" / "remote_install_mini_canary_stack.py").read_text(encoding="utf-8")
    assert "--print-links" in source
    assert "--print-secrets" in source
    assert "xhttp_link=[redacted]" in source
    assert "hysteria2_link=[redacted]" in source
    assert "hy2_password=[redacted]" in source
