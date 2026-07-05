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


def test_runtime_python_sources_do_not_use_obvious_rce_primitives() -> None:
    findings: list[str] = []
    for path in _python_sources():
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = _call_name(node.func)
            if name in {"eval", "exec"}:
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
