from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = REPO_ROOT / "shared" / "marketing-governance.source.json"
CATALOG_PATH = REPO_ROOT / "copy" / "catalog.ru.json"
OUTPUT_PATH = (
    REPO_ROOT
    / "shared"
    / "contracts"
    / "marketing"
    / "marketing-governance.v1.json"
)
DOC_PATH = REPO_ROOT / "docs" / "generated" / "marketing-governance.md"
SOURCE_SCHEMA = "pokrov-marketing-governance-source-v1"
OUTPUT_SCHEMA = "pokrov-marketing-governance-v1"
ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
COPY_STATES = frozenset(
    {"repository_verified", "blocked_owner_legal_approval_required"}
)
LAUNCH_STATES = frozenset(
    {
        "blocked_owner_approval_required",
        "blocked_owner_legal_approval_required",
        "blocked_consent_and_owner_approval_required",
    }
)


class MarketingGovernanceError(ValueError):
    pass


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise MarketingGovernanceError(f"invalid_json:{path.relative_to(REPO_ROOT)}") from exc
    if not isinstance(value, dict):
        raise MarketingGovernanceError(f"object_required:{path.relative_to(REPO_ROOT)}")
    return value


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _file_digest(path: Path) -> str:
    # Keep generated text identities stable when Git checks LF files out as
    # CRLF on Windows.
    normalized = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(normalized).hexdigest()


def _closed_keys(value: Mapping[str, Any], allowed: set[str], *, field: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise MarketingGovernanceError(f"unknown_keys:{field}:{','.join(unknown)}")


def _text(value: object, *, field: str, limit: int = 256) -> str:
    normalized = str(value or "").strip()
    if not normalized or len(normalized) > limit:
        raise MarketingGovernanceError(f"invalid_text:{field}")
    return normalized


def _identifier(value: object, *, field: str) -> str:
    normalized = _text(value, field=field, limit=64).lower()
    if ID_RE.fullmatch(normalized) is None:
        raise MarketingGovernanceError(f"invalid_identifier:{field}")
    return normalized


def _json_pointer(value: Any, pointer: str) -> Any:
    if pointer == "":
        return value
    if not pointer.startswith("/"):
        raise MarketingGovernanceError("invalid_json_pointer")
    current = value
    for raw in pointer[1:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            if not token.isdigit() or int(token) >= len(current):
                raise MarketingGovernanceError(f"missing_json_pointer:{pointer}")
            current = current[int(token)]
        elif isinstance(current, dict) and token in current:
            current = current[token]
        else:
            raise MarketingGovernanceError(f"missing_json_pointer:{pointer}")
    return current


def _relative_repo_path(value: object, *, field: str) -> tuple[str, Path]:
    normalized = _text(value, field=field, limit=240).replace("\\", "/")
    relative = Path(normalized)
    if relative.is_absolute() or ".." in relative.parts:
        raise MarketingGovernanceError(f"unsafe_path:{field}")
    resolved = (REPO_ROOT / relative).resolve()
    if REPO_ROOT.resolve() not in resolved.parents:
        raise MarketingGovernanceError(f"unsafe_path:{field}")
    return normalized, resolved


def build_contract(source: Mapping[str, Any], catalog: Mapping[str, Any]) -> dict[str, Any]:
    _closed_keys(
        source,
        {
            "schema_version",
            "revision",
            "default_copy_profile",
            "default_campaign_launch_state",
            "profiles",
            "channels",
            "claims",
            "copy_bindings",
            "prohibited_claim_patterns",
            "trust_led_forbidden_markers",
            "trust_led_files",
        },
        field="source",
    )
    if source.get("schema_version") != SOURCE_SCHEMA:
        raise MarketingGovernanceError("source_schema_mismatch")
    revision = _text(source.get("revision"), field="revision", limit=32)

    profiles: list[dict[str, Any]] = []
    profile_ids: set[str] = set()
    for index, raw in enumerate(source.get("profiles") or []):
        if not isinstance(raw, Mapping):
            raise MarketingGovernanceError(f"object_required:profiles.{index}")
        _closed_keys(
            raw,
            {
                "profile_id",
                "copy_state",
                "campaign_launch_state",
                "allowed_channels",
                "service_led",
                "approval",
            },
            field=f"profiles.{index}",
        )
        profile_id = _identifier(raw.get("profile_id"), field=f"profiles.{index}.profile_id")
        if profile_id in profile_ids:
            raise MarketingGovernanceError("duplicate_profile_id")
        profile_ids.add(profile_id)
        copy_state = _text(raw.get("copy_state"), field=f"profiles.{index}.copy_state")
        launch_state = _text(
            raw.get("campaign_launch_state"),
            field=f"profiles.{index}.campaign_launch_state",
        )
        if copy_state not in COPY_STATES or launch_state not in LAUNCH_STATES:
            raise MarketingGovernanceError("invalid_profile_state")
        if raw.get("approval") is not None:
            raise MarketingGovernanceError("sample_legal_approval_forbidden")
        profiles.append(
            {
                "profile_id": profile_id,
                "copy_state": copy_state,
                "campaign_launch_state": launch_state,
                "allowed_channels": sorted(
                    {
                        _identifier(item, field=f"profiles.{index}.allowed_channels")
                        for item in list(raw.get("allowed_channels") or [])
                    }
                ),
                "service_led": raw.get("service_led") is True,
                "approval": None,
            }
        )
    if not profiles:
        raise MarketingGovernanceError("profiles_required")

    channels: list[dict[str, Any]] = []
    channel_ids: set[str] = set()
    for index, raw in enumerate(source.get("channels") or []):
        if not isinstance(raw, Mapping):
            raise MarketingGovernanceError(f"object_required:channels.{index}")
        _closed_keys(
            raw,
            {"channel_id", "requires_consent", "erid_policy", "launch_state"},
            field=f"channels.{index}",
        )
        channel_id = _identifier(raw.get("channel_id"), field=f"channels.{index}.channel_id")
        if channel_id in channel_ids:
            raise MarketingGovernanceError("duplicate_channel_id")
        channel_ids.add(channel_id)
        launch_state = _text(raw.get("launch_state"), field=f"channels.{index}.launch_state")
        if launch_state not in LAUNCH_STATES:
            raise MarketingGovernanceError("invalid_channel_launch_state")
        channels.append(
            {
                "channel_id": channel_id,
                "requires_consent": raw.get("requires_consent") is True,
                "erid_policy": _text(
                    raw.get("erid_policy"), field=f"channels.{index}.erid_policy"
                ),
                "launch_state": launch_state,
            }
        )
    if any(set(item["allowed_channels"]) - channel_ids for item in profiles):
        raise MarketingGovernanceError("profile_channel_unknown")

    evidence_payloads: dict[str, dict[str, Any]] = {}
    evidence_sha256: dict[str, str] = {}
    claims: list[dict[str, Any]] = []
    claim_ids: set[str] = set()
    for index, raw in enumerate(source.get("claims") or []):
        if not isinstance(raw, Mapping):
            raise MarketingGovernanceError(f"object_required:claims.{index}")
        _closed_keys(
            raw,
            {
                "claim_id",
                "canonical_ru",
                "status",
                "allowed_profiles",
                "allowed_surfaces",
                "evidence",
            },
            field=f"claims.{index}",
        )
        claim_id = _identifier(raw.get("claim_id"), field=f"claims.{index}.claim_id")
        if claim_id in claim_ids:
            raise MarketingGovernanceError("duplicate_claim_id")
        claim_ids.add(claim_id)
        status = _text(raw.get("status"), field=f"claims.{index}.status")
        if status != "repository_verified":
            raise MarketingGovernanceError("unsupported_claim_status")
        allowed_profiles = sorted(
            {
                _identifier(item, field=f"claims.{index}.allowed_profiles")
                for item in list(raw.get("allowed_profiles") or [])
            }
        )
        if not allowed_profiles or set(allowed_profiles) - profile_ids:
            raise MarketingGovernanceError("claim_profile_unknown")
        evidence: list[dict[str, Any]] = []
        for evidence_index, assertion in enumerate(raw.get("evidence") or []):
            if not isinstance(assertion, Mapping):
                raise MarketingGovernanceError("claim_evidence_object_required")
            _closed_keys(
                assertion,
                {"path", "pointer", "equals"},
                field=f"claims.{index}.evidence.{evidence_index}",
            )
            relative_path, path = _relative_repo_path(
                assertion.get("path"),
                field=f"claims.{index}.evidence.{evidence_index}.path",
            )
            pointer = _text(
                assertion.get("pointer"),
                field=f"claims.{index}.evidence.{evidence_index}.pointer",
            )
            payload = evidence_payloads.setdefault(relative_path, _read_object(path))
            actual = _json_pointer(payload, pointer)
            expected = assertion.get("equals")
            if type(actual) is not type(expected) or actual != expected:
                raise MarketingGovernanceError(
                    f"claim_evidence_mismatch:{claim_id}:{relative_path}:{pointer}"
                )
            evidence_sha256.setdefault(relative_path, _file_digest(path))
            evidence.append(
                {
                    "path": relative_path,
                    "pointer": pointer,
                    "equals": expected,
                    "source_sha256": evidence_sha256[relative_path],
                }
            )
        if not evidence:
            raise MarketingGovernanceError("claim_evidence_required")
        claims.append(
            {
                "claim_id": claim_id,
                "canonical_ru": _text(
                    raw.get("canonical_ru"), field=f"claims.{index}.canonical_ru"
                ),
                "status": status,
                "allowed_profiles": allowed_profiles,
                "allowed_surfaces": sorted(
                    {
                        _identifier(item, field=f"claims.{index}.allowed_surfaces")
                        for item in list(raw.get("allowed_surfaces") or [])
                    }
                ),
                "evidence": evidence,
            }
        )

    catalog_items = catalog.get("items")
    if not isinstance(catalog_items, Mapping):
        raise MarketingGovernanceError("copy_catalog_items_required")
    copy_bindings: list[dict[str, Any]] = []
    seen_copy_keys: set[str] = set()
    for index, raw in enumerate(source.get("copy_bindings") or []):
        if not isinstance(raw, Mapping):
            raise MarketingGovernanceError(f"object_required:copy_bindings.{index}")
        _closed_keys(
            raw,
            {"copy_key", "profile_id", "claim_ids"},
            field=f"copy_bindings.{index}",
        )
        copy_key = _text(raw.get("copy_key"), field=f"copy_bindings.{index}.copy_key")
        if copy_key in seen_copy_keys or copy_key not in catalog_items:
            raise MarketingGovernanceError(f"invalid_copy_key:{copy_key}")
        seen_copy_keys.add(copy_key)
        profile_id = _identifier(raw.get("profile_id"), field=f"copy_bindings.{index}.profile_id")
        bound_claim_ids = sorted(
            {
                _identifier(item, field=f"copy_bindings.{index}.claim_ids")
                for item in list(raw.get("claim_ids") or [])
            }
        )
        if profile_id not in profile_ids or not bound_claim_ids or set(bound_claim_ids) - claim_ids:
            raise MarketingGovernanceError("invalid_copy_binding")
        item = catalog_items[copy_key]
        if not isinstance(item, Mapping) or item.get("allowed_public") is not True:
            raise MarketingGovernanceError(f"copy_binding_not_public:{copy_key}")
        copy_bindings.append(
            {
                "copy_key": copy_key,
                "profile_id": profile_id,
                "claim_ids": bound_claim_ids,
                "copy_sha256": _digest(str(item.get("ru") or "")),
            }
        )

    patterns: list[str] = []
    for index, raw in enumerate(source.get("prohibited_claim_patterns") or []):
        pattern = _text(raw, field=f"prohibited_claim_patterns.{index}")
        try:
            re.compile(pattern)
        except re.error as exc:
            raise MarketingGovernanceError("invalid_prohibited_claim_pattern") from exc
        patterns.append(pattern)

    trust_led_files: list[str] = []
    for index, raw in enumerate(source.get("trust_led_files") or []):
        relative, path = _relative_repo_path(raw, field=f"trust_led_files.{index}")
        if not path.is_file():
            raise MarketingGovernanceError(f"missing_trust_led_file:{relative}")
        trust_led_files.append(relative)

    default_profile = _identifier(
        source.get("default_copy_profile"), field="default_copy_profile"
    )
    default_launch_state = _text(
        source.get("default_campaign_launch_state"),
        field="default_campaign_launch_state",
    )
    if default_profile not in profile_ids or default_launch_state not in LAUNCH_STATES:
        raise MarketingGovernanceError("invalid_defaults")

    contract: dict[str, Any] = {
        "schema_version": OUTPUT_SCHEMA,
        "revision": revision,
        "default_copy_profile": default_profile,
        "default_campaign_launch_state": default_launch_state,
        "profiles": sorted(profiles, key=lambda item: item["profile_id"]),
        "channels": sorted(channels, key=lambda item: item["channel_id"]),
        "claims": sorted(claims, key=lambda item: item["claim_id"]),
        "copy_bindings": sorted(copy_bindings, key=lambda item: item["copy_key"]),
        "prohibited_claim_patterns": patterns,
        "trust_led_forbidden_markers": sorted(
            {
                _text(item, field="trust_led_forbidden_markers", limit=80).lower()
                for item in list(source.get("trust_led_forbidden_markers") or [])
            }
        ),
        "trust_led_files": sorted(set(trust_led_files)),
        "source_contract": "shared/marketing-governance.source.json",
        "source_sha256": _file_digest(SOURCE_PATH),
        "copy_catalog_sha256": _file_digest(CATALOG_PATH),
        "evidence_source_sha256": dict(sorted(evidence_sha256.items())),
    }
    contract["contract_sha256"] = _digest(contract)
    return contract


def render_document(contract: Mapping[str, Any]) -> str:
    lines = [
        "# Generated marketing governance contract",
        "",
        "Generated by `scripts/generate_marketing_governance.py`. Do not edit by hand.",
        "",
        f"- revision: `{contract['revision']}`",
        f"- contract SHA-256: `{contract['contract_sha256']}`",
        f"- default copy profile: `{contract['default_copy_profile']}`",
        f"- campaign launch: `{contract['default_campaign_launch_state']}`",
        "",
        "## Claims",
        "",
        "| Claim | State | Canonical Russian copy |",
        "| --- | --- | --- |",
    ]
    for claim in contract["claims"]:
        lines.append(
            f"| `{claim['claim_id']}` | `{claim['status']}` | {claim['canonical_ru']} |"
        )
    lines.extend(
        [
            "",
            "Repository verification proves source consistency only. It is not legal approval, consent, ERID, deployment or campaign-launch evidence.",
            "The service-led profile and every campaign channel remain blocked until an exact owner approval record is supplied outside this generated contract.",
            "",
        ]
    )
    return "\n".join(lines)


def _write_or_check(path: Path, expected: str, *, check: bool) -> None:
    if check:
        try:
            actual = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise MarketingGovernanceError(f"missing_generated_output:{path}") from exc
        if actual != expected:
            raise MarketingGovernanceError(f"stale_generated_output:{path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(expected, encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate and validate the POKROV marketing-governance contract."
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        source = _read_object(SOURCE_PATH)
        catalog = _read_object(CATALOG_PATH)
        contract = build_contract(source, catalog)
        _write_or_check(
            OUTPUT_PATH,
            json.dumps(contract, ensure_ascii=False, indent=2) + "\n",
            check=bool(args.check),
        )
        _write_or_check(DOC_PATH, render_document(contract), check=bool(args.check))
    except MarketingGovernanceError as exc:
        print(f"FAIL marketing-governance {exc}")
        return 1
    print(
        "PASS marketing-governance "
        f"revision={contract['revision']} sha256={contract['contract_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
